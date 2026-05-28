import StatInference.AsymptoticStatistics.Basic
import StatInference.ProbabilityMeasure.StrongLaw
import Mathlib.Analysis.Calculus.InverseFunctionTheorem.FDeriv
import Mathlib.Analysis.InnerProductSpace.PiL2
import Mathlib.MeasureTheory.Measure.LevyConvergence
import Mathlib.MeasureTheory.SpecificCodomains.Pi
import Mathlib.Probability.CentralLimitTheorem
import Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Basic
import Mathlib.Probability.Independence.InfinitePi
import Mathlib.Probability.Moments.CovarianceBilinDual

/-!
# van der Vaart 1998 Chapter 4 moment-estimator interfaces

This module starts the source-shaped Chapter 4 lane for A. W. van der Vaart,
*Asymptotic Statistics* (1998), Section 4.1.  The first layer packages the
method-of-moments asymptotic-normality proof as the handoff used in the text:
an empirical-moment CLT followed by the Chapter 3 delta method applied to the
local inverse of the theoretical moment map.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal Real Topology

universe u v w x

/-- The textbook rate `sqrt n` tends to infinity. -/
theorem vaart1998_sqrt_nat_tendsto_atTop :
    Tendsto (fun n : ℕ => √(n : ℝ)) atTop atTop :=
  Real.tendsto_sqrt_atTop.comp tendsto_natCast_atTop_atTop

/--
Local inverse data for van der Vaart Theorem 4.1.

The textbook obtains these fields from the inverse function theorem.  Keeping
them as a certificate lets the Chapter 4 asymptotic-normality proof compile
while later work fills in the inverse-function and existence-with-probability
layers separately.
-/
structure Vaart1998MomentLocalInverseCertificate (M Θ : Type*)
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [MeasurableSpace Θ] where
  /-- The theoretical moment map `e(theta) = P_theta f`. -/
  e : Θ -> M
  /-- A local inverse of the theoretical moment map near `eta0`. -/
  eInv : M -> Θ
  /-- The true theoretical moment, `e theta0`. -/
  eta0 : M
  /-- The true parameter. -/
  theta0 : Θ
  /-- The derivative of the local inverse at `eta0`. -/
  Dinv : M →L[ℝ] Θ
  /-- The source identity `eta0 = e theta0`, oriented for rewriting moments. -/
  eta0_eq : e theta0 = eta0
  /-- The local inverse sends the true moment back to the true parameter. -/
  inverse_at_eta0 : eInv eta0 = theta0
  /-- Differentiability of the local inverse, supplied by the inverse function theorem. -/
  inverse_deriv : HasFDerivAt eInv Dinv eta0
  /-- Measurability needed to discharge the Chapter 3 delta-method remainder. -/
  inverse_measurable : Measurable eInv

/--
Inverse-function-theorem bridge into the Vaart Theorem 4.1 local inverse
certificate.

Mathlib constructs a local inverse and proves its derivative from a strict
derivative with continuous-linear equivalence derivative.  Global measurability
of this chosen local inverse is kept as an explicit field because the inverse
function theorem supplies local continuity at the true moment.
-/
def vaart1998_momentLocalInverseCertificate_of_hasStrictFDerivAt
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0)) :
    Vaart1998MomentLocalInverseCertificate M Θ where
  e := e
  eInv := he.localInverse e De theta0
  eta0 := e theta0
  theta0 := theta0
  Dinv := (De.symm : M →L[ℝ] Θ)
  eta0_eq := rfl
  inverse_at_eta0 := he.localInverse_apply_image
  inverse_deriv := he.to_localInverse.hasFDerivAt
  inverse_measurable := hInv_meas

/--
Local range data for the moment equations in van der Vaart Theorem 4.1.

The source proof obtains a neighborhood `V` of the true moment such that the
local inverse is defined on `V`.  This certificate records only the deterministic
equation-solving facts that later probability/localization work needs.
-/
structure Vaart1998MomentLocalRangeCertificate (M Θ : Type*) where
  /-- The theoretical moment map `e(theta) = P_theta f`. -/
  e : Θ -> M
  /-- The local inverse on the moment range. -/
  eInv : M -> Θ
  /-- Local range of empirical moments where the estimator exists. -/
  momentRange : Set M
  /-- Local parameter domain where uniqueness is asserted. -/
  parameterDomain : Set Θ
  /-- The inverse candidate maps local moments into the local parameter domain. -/
  eInv_mem_parameterDomain : ∀ {m : M}, m ∈ momentRange -> eInv m ∈ parameterDomain
  /-- Right inverse property: the local-inverse estimator solves the moment equation. -/
  right_inverse_on_momentRange : ∀ {m : M}, m ∈ momentRange -> e (eInv m) = m
  /-- Left inverse property on the local parameter domain, used for uniqueness. -/
  left_inverse_on_parameterDomain :
    ∀ {theta : Θ}, theta ∈ parameterDomain -> eInv (e theta) = theta

/--
Canonical local-range certificate generated by mathlib's local inverse.

The range/domain sets are chosen to be exactly the points where the right and
left inverse identities hold.  Later packets can replace these tautological
sets with open neighborhoods from the inverse function theorem.
-/
def vaart1998_momentLocalRangeCertificate_of_hasStrictFDerivAt
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0) :
    Vaart1998MomentLocalRangeCertificate M Θ where
  e := e
  eInv := he.localInverse e De theta0
  momentRange := {m : M | e (he.localInverse e De theta0 m) = m}
  parameterDomain := {theta : Θ | he.localInverse e De theta0 (e theta) = theta}
  eInv_mem_parameterDomain := by
    intro m hmem
    change he.localInverse e De theta0
        (e (he.localInverse e De theta0 m)) =
      he.localInverse e De theta0 m
    rw [hmem]
  right_inverse_on_momentRange := by
    intro m hmem
    exact hmem
  left_inverse_on_parameterDomain := by
    intro theta htheta
    exact htheta

/--
The inverse-function-theorem source neighborhood for the true parameter is open.

This records the exact local parameter domain supplied by mathlib's
`OpenPartialHomeomorph`, matching the open neighborhood `U` in van der Vaart's
proof of Theorem 4.1.
-/
theorem vaart1998_hasStrictFDerivAt_open_local_parameterDomain
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0) :
    IsOpen (he.toOpenPartialHomeomorph e).source :=
  (he.toOpenPartialHomeomorph e).open_source

/--
The inverse-function-theorem target neighborhood for the true moment is open.

This records the exact local moment range supplied by mathlib's
`OpenPartialHomeomorph`, matching the open neighborhood `V` in van der Vaart's
proof of Theorem 4.1.
-/
theorem vaart1998_hasStrictFDerivAt_open_local_momentRange
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0) :
    IsOpen (he.toOpenPartialHomeomorph e).target :=
  (he.toOpenPartialHomeomorph e).open_target

/--
The true parameter belongs to the inverse-function-theorem local source
neighborhood.
-/
theorem vaart1998_hasStrictFDerivAt_theta0_mem_local_parameterDomain
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0) :
    theta0 ∈ (he.toOpenPartialHomeomorph e).source :=
  he.mem_toOpenPartialHomeomorph_source

/--
The true theoretical moment belongs to the inverse-function-theorem local
target neighborhood.
-/
theorem vaart1998_hasStrictFDerivAt_eta0_mem_local_momentRange
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0) :
    e theta0 ∈ (he.toOpenPartialHomeomorph e).target :=
  he.image_mem_toOpenPartialHomeomorph_target

/--
An open partial homeomorphism has an a.e.-measurable inverse on its open
target.  This is the robust measurability form for local inverses: outside the
target the global partial-equivalence inverse is irrelevant.
-/
theorem vaart1998_openPartialHomeomorph_symm_aemeasurable_on_target
    {M Θ : Type*} [TopologicalSpace M] [MeasurableSpace M]
    [OpensMeasurableSpace M] [TopologicalSpace Θ] [MeasurableSpace Θ]
    [BorelSpace Θ] (φ : OpenPartialHomeomorph Θ M) (μ : Measure M) :
    AEMeasurable φ.symm (μ.restrict φ.target) :=
  φ.continuousOn_symm.aemeasurable φ.open_target.measurableSet

/--
The inverse-function-theorem local inverse is a.e.-measurable on the local
moment range produced by `HasStrictFDerivAt.toOpenPartialHomeomorph`.
-/
theorem vaart1998_localInverse_aemeasurable_on_open_momentRange
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (μ : Measure M) :
    AEMeasurable (he.localInverse e De theta0)
      (μ.restrict (he.toOpenPartialHomeomorph e).target) := by
  simpa [HasStrictFDerivAt.localInverse_def] using
    vaart1998_openPartialHomeomorph_symm_aemeasurable_on_target
      (he.toOpenPartialHomeomorph e) μ

/--
If a measure is concentrated on the inverse-function-theorem local moment
range, then the local inverse is a.e.-measurable for that measure.
-/
theorem vaart1998_localInverse_aemeasurable_of_ae_mem_open_momentRange
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    {μ : Measure M}
    (hμ_target : ∀ᵐ m ∂μ, m ∈ (he.toOpenPartialHomeomorph e).target) :
    AEMeasurable (he.localInverse e De theta0) μ := by
  rw [← Measure.restrict_eq_self_of_ae_mem hμ_target]
  exact vaart1998_localInverse_aemeasurable_on_open_momentRange e De he μ

/--
If the empirical moment is a.e. in the inverse-function-theorem local target,
then the composed local-inverse estimator is a.e.-measurable.
-/
theorem vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    {empiricalMoment : Ω -> M}
    (hEmpiricalMoment : AEMeasurable empiricalMoment P)
    (hTarget :
      ∀ᵐ ω ∂P, empiricalMoment ω ∈ (he.toOpenPartialHomeomorph e).target) :
    AEMeasurable
      (fun ω => he.localInverse e De theta0 (empiricalMoment ω)) P := by
  have hMapTarget :
      ∀ᵐ m ∂P.map empiricalMoment,
        m ∈ (he.toOpenPartialHomeomorph e).target := by
    exact (ae_map_iff hEmpiricalMoment
      (he.toOpenPartialHomeomorph e).open_target.measurableSet).2 hTarget
  have hInvMap :
      AEMeasurable (he.localInverse e De theta0) (P.map empiricalMoment) :=
    vaart1998_localInverse_aemeasurable_of_ae_mem_open_momentRange
      e De he hMapTarget
  simpa [Function.comp_def] using
    hInvMap.comp_aemeasurable hEmpiricalMoment

/--
If the inverse-function-theorem local inverse is globally measurable, then its
composition with any a.e.-measurable empirical moment is a.e.-measurable.
-/
theorem vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_measurable
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [MeasurableSpace M] [MeasurableSpace Θ]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    {empiricalMoment : Ω -> M}
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (hEmpiricalMoment : AEMeasurable empiricalMoment P) :
    AEMeasurable
      (fun ω => he.localInverse e De theta0 (empiricalMoment ω)) P :=
  hInv_meas.comp_aemeasurable hEmpiricalMoment

/--
Open-neighborhood local-range certificate generated by mathlib's inverse
function theorem.

Unlike the tautological identity-validity constructor above, this version uses
the actual open source and target of `he.toOpenPartialHomeomorph e` as the
local parameter domain and local moment range.  This is the deterministic
`U`/`V` bridge in van der Vaart's proof of Theorem 4.1.
-/
def vaart1998_momentLocalRangeCertificate_of_hasStrictFDerivAt_openPartialHomeomorph
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0) :
    Vaart1998MomentLocalRangeCertificate M Θ where
  e := e
  eInv := (he.toOpenPartialHomeomorph e).symm
  momentRange := (he.toOpenPartialHomeomorph e).target
  parameterDomain := (he.toOpenPartialHomeomorph e).source
  eInv_mem_parameterDomain := by
    intro m hmem
    exact (he.toOpenPartialHomeomorph e).map_target hmem
  right_inverse_on_momentRange := by
    intro m hmem
    simpa using (he.toOpenPartialHomeomorph e).right_inv hmem
  left_inverse_on_parameterDomain := by
    intro theta htheta
    simpa using (he.toOpenPartialHomeomorph e).left_inv htheta

/--
Supplied probability-localization certificate for Theorem 4.1's existence
sentence.  The vector LLN should eventually discharge `localRange_probability`;
for now it is kept as an explicit field.
-/
structure Vaart1998MomentEstimatorLocalRangeProbabilityCertificate
    (Ω M : Type*) [MeasurableSpace Ω] (P : Measure Ω) where
  empiricalMoment : ℕ -> Ω -> M
  momentRange : Set M
  localRange_probability :
    Tendsto (fun n : ℕ => P.real {ω : Ω | empiricalMoment n ω ∈ momentRange})
      atTop (𝓝 1)

/--
Open-neighborhood localization from convergence in probability.

If empirical moments converge in probability to the true moment and the local
moment range is an open neighborhood of that true moment, then the empirical
moments lie in the local range with probability tending to one.  This is the
probability skeleton of the existence sentence in van der Vaart Theorem 4.1;
the vector LLN is the intended downstream source of `hconv`.
-/
theorem vaart1998_local_range_probability_of_tendstoInMeasure_const
    {Ω M : Type*} [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [PseudoMetricSpace M] [MeasurableSpace M] [OpensMeasurableSpace M]
    {empiricalMoment : ℕ -> Ω -> M} {eta0 : M} {momentRange : Set M}
    (hOpen : IsOpen momentRange) (heta0 : eta0 ∈ momentRange)
    (hconv : TendstoInMeasure P empiricalMoment atTop (fun _ : Ω => eta0))
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n)) :
    Tendsto (fun n : ℕ =>
      P.real {ω : Ω | empiricalMoment n ω ∈ momentRange}) atTop (𝓝 1) := by
  rcases Metric.mem_nhds_iff.mp (hOpen.mem_nhds heta0) with
    ⟨ε, hε, hball_subset⟩
  have htail :
      Tendsto (fun n : ℕ =>
        P.real {ω : Ω | ε ≤ dist (empiricalMoment n ω) eta0}) atTop
          (𝓝 0) := by
    simpa using
      (MeasureTheory.tendstoInMeasure_iff_measureReal_dist.mp hconv ε hε)
  have hlower_tendsto :
      Tendsto (fun n : ℕ =>
        (1 : ℝ) - P.real {ω : Ω | ε ≤ dist (empiricalMoment n ω) eta0})
          atTop (𝓝 1) := by
    simpa using (tendsto_const_nhds.sub htail)
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    hlower_tendsto tendsto_const_nhds ?_ ?_
  · intro n
    let event : Set Ω := {ω : Ω | empiricalMoment n ω ∈ momentRange}
    let tail : Set Ω := {ω : Ω | ε ≤ dist (empiricalMoment n ω) eta0}
    have hevent_meas : MeasurableSet event := by
      dsimp [event]
      exact (hmeas n) hOpen.measurableSet
    have hcompl_subset_tail : eventᶜ ⊆ tail := by
      intro ω hω
      dsimp [event, tail] at hω ⊢
      by_contra hdist
      have hdist_lt : dist (empiricalMoment n ω) eta0 < ε :=
        lt_of_not_ge hdist
      have hball_mem : empiricalMoment n ω ∈ Metric.ball eta0 ε := by
        rw [Metric.mem_ball]
        simpa [dist_comm] using hdist_lt
      exact hω (hball_subset hball_mem)
    have hcompl_le : P.real eventᶜ ≤ P.real tail :=
      measureReal_mono hcompl_subset_tail
    have hsum : P.real event + P.real eventᶜ = 1 :=
      probReal_add_probReal_compl (μ := P) hevent_meas
    have hsub_eq : 1 - P.real eventᶜ = P.real event := by
      linarith
    calc
      (1 : ℝ) - P.real tail ≤ 1 - P.real eventᶜ := sub_le_sub_left hcompl_le 1
      _ = P.real event := hsub_eq
  · intro n
    have hle :
        P.real {ω : Ω | empiricalMoment n ω ∈ momentRange} ≤
          P.real Set.univ :=
      measureReal_mono (μ := P) (Set.subset_univ _)
    simpa using hle

/--
Certificate constructor for the Theorem 4.1 local-range probability field from
convergence in probability to the true moment and an open local range.
-/
def vaart1998_momentEstimatorLocalRangeProbabilityCertificate_of_tendstoInMeasure
    {Ω M : Type*} [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [PseudoMetricSpace M] [MeasurableSpace M] [OpensMeasurableSpace M]
    (empiricalMoment : ℕ -> Ω -> M) {eta0 : M} (momentRange : Set M)
    (hOpen : IsOpen momentRange) (heta0 : eta0 ∈ momentRange)
    (hconv : TendstoInMeasure P empiricalMoment atTop (fun _ : Ω => eta0))
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n)) :
    Vaart1998MomentEstimatorLocalRangeProbabilityCertificate Ω M P where
  empiricalMoment := empiricalMoment
  momentRange := momentRange
  localRange_probability :=
    vaart1998_local_range_probability_of_tendstoInMeasure_const
      hOpen heta0 hconv hmeas

/--
Almost-sure empirical-moment convergence implies convergence in probability.

This is the method-of-moments LLN handoff: any strong-law theorem that proves
almost-sure convergence of the empirical moment vector to the true moment can
now feed the Chapter 4 local existence machinery.
-/
theorem vaart1998_empiricalMoment_tendstoInMeasure_of_ae_tendsto_const
    {Ω M : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [PseudoEMetricSpace M]
    {empiricalMoment : ℕ -> Ω -> M} {eta0 : M}
    (hstrong : ∀ n : ℕ, AEStronglyMeasurable (empiricalMoment n) P)
    (hAE : ∀ᵐ ω ∂P,
      Tendsto (fun n : ℕ => empiricalMoment n ω) atTop (𝓝 eta0)) :
    TendstoInMeasure P empiricalMoment atTop (fun _ : Ω => eta0) :=
  vaart1998_tendstoInMeasure_of_tendsto_ae hstrong hAE

/--
Finite-coordinate empirical-moment strong-law handoff.

For finitely many real moment coordinates, the local real-valued strong law
implies almost-sure convergence of the vector of empirical moments to the
vector of population moments.
-/
theorem vaart1998_finiteCoordinate_empiricalMoment_tendsto_ae_real
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω}
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n)
        atTop
        (𝓝 fun coordinate : Coordinate => ∫ ω, X coordinate 0 ω ∂P) := by
  have hcenter :=
    StatInference.ProbabilityMeasure.finite_centeredStrongLaw_ae_real
      X hX_integrable hX_indep hX_ident
  filter_upwards [hcenter] with ω hω
  rw [tendsto_pi_nhds]
  intro coordinate
  have hcoord := hω coordinate
  have hconst :
      Tendsto
        (fun _n : ℕ => ∫ sample, X coordinate 0 sample ∂P)
        atTop (𝓝 (∫ sample, X coordinate 0 sample ∂P)) :=
    tendsto_const_nhds
  simpa using hcoord.add hconst

/--
Finite-coordinate empirical-moment convergence in probability.

The only extra input beyond the finite-coordinate strong law is the standard
strong measurability of the vector empirical moment sequence.
-/
theorem vaart1998_finiteCoordinate_empiricalMoment_tendstoInMeasure_real
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hstrong : ∀ n : ℕ,
      AEStronglyMeasurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) P) :
    TendstoInMeasure P
      (fun n : ℕ => fun ω : Ω => fun coordinate : Coordinate =>
        (∑ i ∈ Finset.range n, X coordinate i ω) / n)
      atTop
      (fun _ : Ω => fun coordinate : Coordinate =>
        ∫ sample, X coordinate 0 sample ∂P) :=
  vaart1998_empiricalMoment_tendstoInMeasure_of_ae_tendsto_const
    hstrong
    (vaart1998_finiteCoordinate_empiricalMoment_tendsto_ae_real
      X hX_integrable hX_indep hX_ident)

/--
Finite-coordinate empirical-moment measurability from coordinate measurability.
-/
theorem vaart1998_finiteCoordinate_empiricalMoment_measurable_real
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    ∀ n : ℕ,
      Measurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) := by
  intro n
  exact measurable_pi_lambda _ fun coordinate =>
    ((Finset.range n).measurable_fun_sum
      (fun i _hi => hX_meas coordinate i)).div_const (n : ℝ)

/--
Finite-coordinate empirical-moment a.e.-strong measurability from coordinate
measurability.
-/
theorem vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω}
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    ∀ n : ℕ,
      AEStronglyMeasurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) P :=
  fun n =>
    (vaart1998_finiteCoordinate_empiricalMoment_measurable_real X hX_meas n).aestronglyMeasurable

/--
Finite-coordinate empirical moment vector used in van der Vaart Theorem 4.1.
-/
noncomputable def vaart1998_finiteCoordinateEmpiricalMoment
    {Coordinate Ω : Type*} [Fintype Coordinate]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) :
    Coordinate -> ℝ :=
  fun coordinate : Coordinate =>
    (∑ i ∈ Finset.range n, X coordinate i ω) / n

/--
Source-shaped certificate that finite-coordinate empirical moments enter the
inverse-function-theorem target with probability tending to one.
-/
structure Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
    (Coordinate Ω Θ : Type*) [Fintype Coordinate] [MeasurableSpace Ω]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (P : Measure Ω)
    (e : Θ -> Coordinate -> ℝ) (theta0 : Θ)
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) where
  empiricalMoment_mem_target_probability :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
            (he.toOpenPartialHomeomorph e).target})
      atTop (𝓝 1)

/--
Turn the finite-coordinate target-probability certificate into the generic
moment-local-range probability certificate.
-/
def Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate.to_momentEstimatorLocalRangeProbabilityCertificate
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    {P : Measure Ω}
    {e : Θ -> Coordinate -> ℝ} {theta0 : Θ}
    {De : Θ ≃L[ℝ] (Coordinate -> ℝ)}
    {he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0}
    {X : Coordinate -> ℕ -> Ω -> ℝ}
    (C :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X) :
    Vaart1998MomentEstimatorLocalRangeProbabilityCertificate
      Ω (Coordinate -> ℝ) P where
  empiricalMoment := fun n => vaart1998_finiteCoordinateEmpiricalMoment X n
  momentRange := (he.toOpenPartialHomeomorph e).target
  localRange_probability := C.empiricalMoment_mem_target_probability

/--
Finite-coordinate population moment vector for the empirical moment sequence.
-/
noncomputable def vaart1998_finiteCoordinatePopulationMoment
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    (P : Measure Ω) (X : Coordinate -> ℕ -> Ω -> ℝ) :
    Coordinate -> ℝ :=
  fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P

/--
Scaled centered finite-coordinate empirical moment vector.
-/
noncomputable def vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    (P : Measure Ω) (X : Coordinate -> ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) :
    Coordinate -> ℝ :=
  √(n : ℝ) •
    (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
      vaart1998_finiteCoordinatePopulationMoment P X)

/--
Measurability of the scaled centered finite-coordinate empirical moment vector.
-/
theorem vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_measurable_real
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    (P : Measure Ω) (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    ∀ n : ℕ,
      Measurable
        (vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n) := by
  intro n
  exact measurable_pi_lambda _ fun coordinate => by
    simpa [vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment,
      vaart1998_finiteCoordinateEmpiricalMoment,
      vaart1998_finiteCoordinatePopulationMoment, Pi.sub_apply,
      Pi.smul_apply, smul_eq_mul] using
      (measurable_const.mul
        ((((Finset.range n).measurable_fun_sum
          (fun i _hi => hX_meas coordinate i)).div_const (n : ℝ)).sub
          measurable_const))

/--
A.e.-measurability of the scaled centered finite-coordinate empirical moment
vector.
-/
theorem vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aemeasurable_real
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    ∀ n : ℕ,
      AEMeasurable
        (vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n) P :=
  fun n =>
    (vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_measurable_real
      P X hX_meas n).aemeasurable

/--
A.e.-strong measurability of the scaled centered finite-coordinate empirical
moment vector.
-/
theorem vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aestronglyMeasurable_real
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    ∀ n : ℕ,
      AEStronglyMeasurable
        (vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n) P :=
  fun n =>
    (vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_measurable_real
      P X hX_meas n).aestronglyMeasurable

/--
Finite-coordinate empirical local-inverse a.e.-measurability from global
measurability of the inverse-function-theorem local inverse and coordinatewise
measurability of the empirical summands.
-/
theorem vaart1998_finiteCoordinate_localInverse_comp_empiricalMoment_aemeasurable_of_measurable_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ]
    {P : Measure Ω}
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) P := by
  intro n
  have hEmpiricalMoment :
      AEMeasurable (vaart1998_finiteCoordinateEmpiricalMoment X n) P := by
    simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
      (vaart1998_finiteCoordinate_empiricalMoment_measurable_real X hX_meas n).aemeasurable
  exact
    vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_measurable
      (P := P) (e := e) (theta0 := theta0) (De := De) (he := he)
      (hInv_meas := hInv_meas) hEmpiricalMoment

/--
Finite-coordinate empirical local-inverse a.e.-measurability from
coordinatewise sample measurability and a.e. localization in the
inverse-function-theorem local target.
-/
theorem vaart1998_finiteCoordinate_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    {P : Measure Ω}
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) P := by
  intro n
  have hEmpiricalMoment :
      AEMeasurable (vaart1998_finiteCoordinateEmpiricalMoment X n) P := by
    simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
      (vaart1998_finiteCoordinate_empiricalMoment_measurable_real X hX_meas n).aemeasurable
  exact
    vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange
      (P := P) (e := e) (theta0 := theta0) (De := De) (he := he)
      (hEmpiricalMoment := hEmpiricalMoment) (hTarget := hTarget n)

/--
Source-shaped certificate that the finite-coordinate empirical moments lie
a.e. in the inverse-function-theorem local target.
-/
structure Vaart1998FiniteCoordinateEmpiricalTargetLocalizationCertificate
    (Coordinate Ω Θ : Type*) [Fintype Coordinate] [MeasurableSpace Ω]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (P : Measure Ω)
    (e : Θ -> Coordinate -> ℝ) (theta0 : Θ)
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) where
  empiricalMoment_mem_target : ∀ n : ℕ,
    ∀ᵐ ω ∂P,
      vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
        (he.toOpenPartialHomeomorph e).target

/--
Source-shaped certificate for the empirical local-inverse measurability field
used by the finite-coordinate Vaart Theorem 4.1 endpoints.
-/
structure Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate
    (Coordinate Ω Θ : Type*) [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ]
    (P : Measure Ω)
    (e : Θ -> Coordinate -> ℝ) (theta0 : Θ)
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) where
  empiricalLocalInverse_aemeasurable : ∀ n : ℕ,
    AEMeasurable
      (fun ω : Ω =>
        he.localInverse e De theta0
          (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) P

/--
Build the empirical local-inverse measurability certificate from global
measurability of the inverse-function-theorem local inverse.
-/
theorem Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate.of_measurableLocalInverse_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ]
    {P : Measure Ω}
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate
      Coordinate Ω Θ P e theta0 De he X where
  empiricalLocalInverse_aemeasurable :=
    vaart1998_finiteCoordinate_localInverse_comp_empiricalMoment_aemeasurable_of_measurable_real
      (P := P) (e := e) (theta0 := theta0) (De := De) (he := he)
      (hInv_meas := hInv_meas) (X := X) (hX_meas := hX_meas)

/--
Build the empirical local-inverse measurability certificate from a.e.
localization in the inverse-function-theorem local target.
-/
theorem Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate.of_ae_mem_open_momentRange_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    {P : Measure Ω}
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate
      Coordinate Ω Θ P e theta0 De he X where
  empiricalLocalInverse_aemeasurable :=
    vaart1998_finiteCoordinate_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange_real
      (P := P) (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := X) (hX_meas := hX_meas) (hTarget := hTarget)

/--
Build the empirical local-inverse measurability certificate from the named
empirical target-localization certificate.
-/
theorem Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate.of_targetLocalization_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    {P : Measure Ω}
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetLocalization :
      Vaart1998FiniteCoordinateEmpiricalTargetLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X) :
    Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate
      Coordinate Ω Θ P e theta0 De he X :=
  Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate.of_ae_mem_open_momentRange_real
    (P := P) (e := e) (theta0 := theta0) (De := De) (he := he)
    (X := X) (hX_meas := hX_meas)
    (hTarget := targetLocalization.empiricalMoment_mem_target)

/--
Law of the scaled centered finite-coordinate empirical moment vector.
-/
noncomputable def vaart1998_finiteCoordinateScaledCenteredEmpiricalMomentLaw
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) (n : ℕ) :
    ProbabilityMeasure (Coordinate -> ℝ) :=
  ⟨P.map (vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n),
    Measure.isProbabilityMeasure_map
      (vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aemeasurable_real
        (P := P) X hX_meas n)⟩

/--
Law of the finite-coordinate vector limit.
-/
noncomputable def vaart1998_finiteCoordinateVectorLimitLaw
    {Coordinate Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω']
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (Z : Ω' -> Coordinate -> ℝ) (hZ_aemeas : AEMeasurable Z Q) :
    ProbabilityMeasure (Coordinate -> ℝ) :=
  ⟨Q.map Z, Measure.isProbabilityMeasure_map hZ_aemeas⟩

/--
Pure law-level projected convergence for finite-coordinate vector laws.
-/
def vaart1998_finiteCoordinateProjectedLawConvergence
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    (μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ))
    (μ : ProbabilityMeasure (Coordinate -> ℝ)) : Prop :=
  ∀ L : StrongDual ℝ (Coordinate -> ℝ),
    Tendsto (β := ProbabilityMeasure ℝ)
      (fun n => (μs n).map L.continuous.measurable.aemeasurable)
      atTop (𝓝 (μ.map L.continuous.measurable.aemeasurable))

/--
Projected law convergence implies pointwise convergence of the Banach-space
characteristic functions.

This is the characteristic-function half of the finite-dimensional
Cramér-Wold route: testing all one-dimensional projections gives convergence
of `charFunDual` at every continuous linear functional.
-/
theorem vaart1998_finiteCoordinateProjectedLawConvergence_charFunDual
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ)}
    {μ : ProbabilityMeasure (Coordinate -> ℝ)}
    (hproj : vaart1998_finiteCoordinateProjectedLawConvergence μs μ) :
    ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Tendsto
        (fun n : ℕ =>
          MeasureTheory.charFunDual
            ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
              Measure (Coordinate -> ℝ)) L)
        atTop
        (𝓝 (MeasureTheory.charFunDual
          ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
            Measure (Coordinate -> ℝ)) L)) := by
  intro L
  have hchar :=
    (ProbabilityMeasure.tendsto_iff_tendsto_charFun.mp (hproj L)) 1
  simpa [MeasureTheory.charFunDual_eq_charFun_map_one] using hchar

/--
Projected law convergence gives weak convergence after identifying finite real
vectors with the Hilbert-space `EuclideanSpace`.

The proof uses the previous `charFunDual` bridge and Lévy's characteristic
function theorem on `EuclideanSpace`.
-/
theorem vaart1998_finiteCoordinateProjectedLawConvergence_euclideanLaw
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ)}
    {μ : ProbabilityMeasure (Coordinate -> ℝ)}
    (hproj : vaart1998_finiteCoordinateProjectedLawConvergence μs μ) :
    Tendsto
      (fun n : ℕ =>
        (μs n).map
          ((EuclideanSpace.equiv Coordinate ℝ).symm.continuous.measurable.aemeasurable))
      atTop
      (𝓝 (μ.map
        ((EuclideanSpace.equiv Coordinate ℝ).symm.continuous.measurable.aemeasurable))) := by
  refine ProbabilityMeasure.tendsto_iff_tendsto_charFun.mpr ?_
  intro t
  let e : (Coordinate -> ℝ) ≃L[ℝ] EuclideanSpace ℝ Coordinate :=
    (EuclideanSpace.equiv Coordinate ℝ).symm
  let L : StrongDual ℝ (Coordinate -> ℝ) :=
    (InnerProductSpace.toDualMap ℝ (EuclideanSpace ℝ Coordinate) t).comp
      e.toContinuousLinearMap
  have hdual :=
    vaart1998_finiteCoordinateProjectedLawConvergence_charFunDual
      (μs := μs) (μ := μ) hproj L
  change Tendsto
    (fun n : ℕ =>
      MeasureTheory.charFun
        (Measure.map (⇑e.toContinuousLinearMap)
          ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
            Measure (Coordinate -> ℝ))) t)
    atTop
    (𝓝 (MeasureTheory.charFun
      (Measure.map (⇑e.toContinuousLinearMap)
        ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
          Measure (Coordinate -> ℝ))) t))
  simp_rw [MeasureTheory.charFun_eq_charFunDual_toDualMap]
  simp_rw [MeasureTheory.charFunDual_map]
  simpa [L, e] using hdual

/--
Finite-dimensional Cramér-Wold law theorem for the finite-coordinate real
vector model.

Convergence of all one-dimensional continuous-linear projections implies weak
convergence of the vector laws.  Internally this transfers the laws to
`EuclideanSpace`, applies Lévy's theorem there, and transfers back.
-/
theorem vaart1998_finiteCoordinateProjectedLawConvergence_lawTendsto
    {Coordinate : Type*} [Fintype Coordinate]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {μs : ℕ -> ProbabilityMeasure (Coordinate -> ℝ)}
    {μ : ProbabilityMeasure (Coordinate -> ℝ)}
    (hproj : vaart1998_finiteCoordinateProjectedLawConvergence μs μ) :
    Tendsto μs atTop (𝓝 μ) := by
  let e : (Coordinate -> ℝ) ≃L[ℝ] EuclideanSpace ℝ Coordinate :=
    (EuclideanSpace.equiv Coordinate ℝ).symm
  have hto :=
    vaart1998_finiteCoordinateProjectedLawConvergence_euclideanLaw
      (μs := μs) (μ := μ) hproj
  have hback :=
    ProbabilityMeasure.tendsto_map_of_tendsto_of_continuous
      (νs := fun n : ℕ =>
        (μs n).map e.continuous.measurable.aemeasurable)
      (ν := μ.map e.continuous.measurable.aemeasurable)
      hto
      (f_cont := (EuclideanSpace.equiv Coordinate ℝ).continuous)
  have hseq :
      (fun n : ℕ =>
        ((μs n).map e.continuous.measurable.aemeasurable).map
          (EuclideanSpace.equiv Coordinate ℝ).continuous.measurable.aemeasurable) = μs := by
    funext n
    apply ProbabilityMeasure.toMeasure_injective
    change Measure.map (⇑(EuclideanSpace.equiv Coordinate ℝ))
        (Measure.map (⇑e)
          ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
            Measure (Coordinate -> ℝ))) =
      ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
        Measure (Coordinate -> ℝ))
    rw [Measure.map_map]
    · change Measure.map (fun x : Coordinate -> ℝ => x)
        ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
          Measure (Coordinate -> ℝ)) =
        ((μs n : ProbabilityMeasure (Coordinate -> ℝ)) :
          Measure (Coordinate -> ℝ))
      exact Measure.map_id
    · exact (EuclideanSpace.equiv Coordinate ℝ).continuous.measurable
    · exact e.continuous.measurable
  have hlim :
      (μ.map e.continuous.measurable.aemeasurable).map
          (EuclideanSpace.equiv Coordinate ℝ).continuous.measurable.aemeasurable = μ := by
    apply ProbabilityMeasure.toMeasure_injective
    change Measure.map (⇑(EuclideanSpace.equiv Coordinate ℝ))
        (Measure.map (⇑e)
          ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
            Measure (Coordinate -> ℝ))) =
      ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
        Measure (Coordinate -> ℝ))
    rw [Measure.map_map]
    · change Measure.map (fun x : Coordinate -> ℝ => x)
        ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
          Measure (Coordinate -> ℝ)) =
        ((μ : ProbabilityMeasure (Coordinate -> ℝ)) :
          Measure (Coordinate -> ℝ))
      exact Measure.map_id
    · exact (EuclideanSpace.equiv Coordinate ℝ).continuous.measurable
    · exact e.continuous.measurable
  simpa [hseq, hlim] using hback

/--
Source-shaped interface for the multivariate empirical-moment CLT in van der
Vaart 1998, Example 2.18, as used by Theorem 4.1.

The current lane keeps the actual Cramér-Wold/vector CLT proof supplied as this
certificate. Later work can replace this interface by a theorem from scalar
CLTs, linear projections, and Gaussian covariance identification.
-/
structure Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
    (Coordinate Ω Ω' : Type*) [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (Q : Measure Ω') [IsProbabilityMeasure Q] where
  /-- The coordinate functions whose empirical averages form the moment vector. -/
  X : Coordinate -> ℕ -> Ω -> ℝ
  /-- The supplied Gaussian vector limit. -/
  Z : Ω' -> Coordinate -> ℝ
  /-- The supplied multivariate empirical-moment CLT. -/
  empiricalMoment_clt :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q
  /-- The supplied vector limit is Gaussian. -/
  gaussian_limit : HasGaussianLaw Z Q
  /-- Square-integrability of the supplied vector limit law. -/
  limit_memLp : MemLp id 2 (Q.map Z)

/--
The projected scalar CLT family appearing in the Cramér-Wold proof of Vaart
1998, Example 2.18.
-/
def vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (Z : Ω' -> Coordinate -> ℝ) : Prop :=
  ∀ L : StrongDual ℝ (Coordinate -> ℝ),
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        L (√(n : ℝ) •
          (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            vaart1998_finiteCoordinatePopulationMoment P X)))
      atTop (fun ω => L (Z ω)) (fun _ => P) Q

/--
A Cramér-Wold bridge from projected scalar CLTs to the vector empirical-moment
CLT in Vaart 1998, Example 2.18.

The bridge records exactly the missing weak-convergence ingredient: once every
continuous linear projection has the scalar CLT, the full finite-coordinate
vector has the supplied vector CLT.
-/
structure Vaart1998FiniteCoordinateCramerWoldCLTBridge
    (Coordinate Ω Ω' : Type*) [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (Q : Measure Ω') [IsProbabilityMeasure Q] where
  /-- The coordinate functions whose empirical averages form the moment vector. -/
  X : Coordinate -> ℕ -> Ω -> ℝ
  /-- The supplied vector limit. -/
  Z : Ω' -> Coordinate -> ℝ
  /-- Scalar CLTs for every continuous linear projection. -/
  projected_clt :
    vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT (P := P) (Q := Q) X Z
  /-- The Cramér-Wold implication from projected CLTs to vector convergence. -/
  cramerWold_vector_clt :
    vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT (P := P) (Q := Q) X Z ->
      TendstoInDistribution
        (fun (n : ℕ) ω =>
          √(n : ℝ) •
            (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
              vaart1998_finiteCoordinatePopulationMoment P X))
        atTop Z (fun _ => P) Q

/--
Scalar empirical average obtained by testing the finite-coordinate empirical
moment with a continuous linear functional.
-/
noncomputable def vaart1998_finiteCoordinateProjectedEmpiricalAverage
    {Coordinate Ω : Type*} [Fintype Coordinate]
    (L : StrongDual ℝ (Coordinate -> ℝ))
    (X : Coordinate -> ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  L (vaart1998_finiteCoordinateEmpiricalMoment X n ω)

/--
Scalar population moment obtained by testing the finite-coordinate population
moment with a continuous linear functional.
-/
noncomputable def vaart1998_finiteCoordinateProjectedPopulationMoment
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    (L : StrongDual ℝ (Coordinate -> ℝ)) (P : Measure Ω)
    (X : Coordinate -> ℕ -> Ω -> ℝ) : ℝ :=
  L (vaart1998_finiteCoordinatePopulationMoment P X)

/--
The finite-coordinate sample vector at a single observation index.
-/
noncomputable def vaart1998_finiteCoordinateSampleVector
    {Coordinate Ω : Type*}
    (X : Coordinate -> ℕ -> Ω -> ℝ) (i : ℕ) (ω : Ω) :
    Coordinate -> ℝ :=
  fun coordinate => X coordinate i ω

/--
The finite-coordinate sample vector is `MemLp` when each coordinate is.
-/
theorem vaart1998_finiteCoordinateSampleVector_memLp_of_coordinate_memLp
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    {p : ℝ≥0∞} (i : ℕ)
    (hX_memLp : ∀ coordinate, MemLp (X coordinate i) p P) :
    MemLp (vaart1998_finiteCoordinateSampleVector X i) p P := by
  simpa [vaart1998_finiteCoordinateSampleVector] using
    (MemLp.of_eval (f := fun ω : Ω => fun coordinate : Coordinate =>
      X coordinate i ω) hX_memLp)

/--
Finite-coordinate sample vectors are independent when their full sequence has
the infinite product law of its marginal vector laws.
-/
theorem vaart1998_finiteCoordinateSampleVector_iIndepFun_of_hasLaw_infinitePi
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {X : Coordinate -> ℕ -> Ω -> ℝ}
    {ν : ℕ -> Measure (Coordinate -> ℝ)}
    (hX_law : ∀ i,
      HasLaw (vaart1998_finiteCoordinateSampleVector X i) (ν i) P)
    (hX_joint_law :
      HasLaw (fun ω i => vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi ν) P) :
    iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P := by
  exact
    (ProbabilityTheory.iIndepFun_iff_hasLaw_Pi_infinitePi
      (X := fun i => vaart1998_finiteCoordinateSampleVector X i)
      (μ := ν) hX_law hX_joint_law.aemeasurable).2 hX_joint_law

/--
Finite-coordinate sample vectors are identically distributed when they share a
common vector law.
-/
theorem vaart1998_finiteCoordinateSampleVector_identDistrib_of_common_hasLaw
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_law : ∀ i,
      HasLaw (vaart1998_finiteCoordinateSampleVector X i) ν P) :
    ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P := by
  intro i
  exact (hX_law i).identDistrib (hX_law 0)

/--
Coordinate projections of independent finite-coordinate sample vectors are
independent scalar samples.
-/
theorem vaart1998_finiteCoordinateCoordinate_iIndepFun_of_vector_iIndepFun
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    (coordinate : Coordinate)
    (hcoordinate_meas :
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hX_indep : iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P) :
    iIndepFun (fun i => X coordinate i) P := by
  have h :=
    hX_indep.comp
      (fun _ => fun sampleVector : Coordinate -> ℝ => sampleVector coordinate)
      (fun _ => hcoordinate_meas)
  simpa [vaart1998_finiteCoordinateSampleVector, Function.comp_def] using h

/--
Coordinate projections of independent finite-coordinate sample vectors are
pairwise independent scalar samples.
-/
theorem vaart1998_finiteCoordinateCoordinate_pairwise_indepFun_of_vector_iIndepFun
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hX_indep : iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P) :
    ∀ coordinate, Pairwise fun i j =>
      _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P := by
  intro coordinate i j hij
  exact
    (vaart1998_finiteCoordinateCoordinate_iIndepFun_of_vector_iIndepFun
      (P := P) (X := X) coordinate (hcoordinate_meas coordinate) hX_indep).indepFun hij

/--
Coordinate projections of identically distributed finite-coordinate sample
vectors are identically distributed scalar samples.
-/
theorem vaart1998_finiteCoordinateCoordinate_identDistrib_of_vector_identDistrib
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hX_ident : ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P) :
    ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P := by
  intro coordinate i
  simpa [vaart1998_finiteCoordinateSampleVector, Function.comp_def] using
    (hX_ident i).comp (hcoordinate_meas coordinate)

/--
A common finite-coordinate vector law plus the infinite-product law of the
sample-vector sequence supplies the coordinate LLN independence and identical
distribution source fields.
-/
theorem vaart1998_finiteCoordinateCoordinateLLNSource_of_commonVectorLaw
    {Coordinate Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {ν : Measure (Coordinate -> ℝ)}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hX_vector_law : ∀ i : ℕ,
      HasLaw (vaart1998_finiteCoordinateSampleVector X i) ν P)
    (hX_sequence_law :
      HasLaw (fun ω i => vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    (∀ coordinate, Pairwise fun i j =>
      _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P) ∧
    (∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P) := by
  have hX_vector_indep :
      iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P :=
    vaart1998_finiteCoordinateSampleVector_iIndepFun_of_hasLaw_infinitePi
      (P := P) (X := X) (ν := fun _ : ℕ => ν) hX_vector_law hX_sequence_law
  have hX_vector_ident : ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P :=
    vaart1998_finiteCoordinateSampleVector_identDistrib_of_common_hasLaw
      (P := P) (X := X) hX_vector_law
  exact
    ⟨vaart1998_finiteCoordinateCoordinate_pairwise_indepFun_of_vector_iIndepFun
        (P := P) (X := X) hcoordinate_meas hX_vector_indep,
      vaart1998_finiteCoordinateCoordinate_identDistrib_of_vector_identDistrib
        (P := P) (X := X) hcoordinate_meas hX_vector_ident⟩

/--
Canonical iid finite-coordinate samples on the infinite-product space have the
common vector law.
-/
theorem vaart1998_finiteCoordinateCanonicalSampleVector_hasLaw
    {Coordinate : Type*} [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν] (i : ℕ) :
    HasLaw
      (vaart1998_finiteCoordinateSampleVector
        (fun coordinate i sample => sample i coordinate) i)
      ν (Measure.infinitePi (fun _ : ℕ => ν)) := by
  simpa [vaart1998_finiteCoordinateSampleVector] using
    (measurePreserving_eval_infinitePi (μ := fun _ : ℕ => ν) i).hasLaw

/--
The canonical iid finite-coordinate sample-vector sequence on the
infinite-product space has the infinite product law.
-/
theorem vaart1998_finiteCoordinateCanonicalSampleVector_sequence_hasLaw
    {Coordinate : Type*} [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} :
    HasLaw
      (fun sample i =>
        vaart1998_finiteCoordinateSampleVector
          (fun coordinate i sample => sample i coordinate) i sample)
      (Measure.infinitePi (fun _ : ℕ => ν))
      (Measure.infinitePi (fun _ : ℕ => ν)) := by
  simpa [vaart1998_finiteCoordinateSampleVector] using
    (HasLaw.id :
      HasLaw
        (id : (ℕ -> Coordinate -> ℝ) -> ℕ -> Coordinate -> ℝ)
        (Measure.infinitePi (fun _ : ℕ => ν))
        (Measure.infinitePi (fun _ : ℕ => ν)))

/--
Canonical iid finite-coordinate samples provide the common-vector-law source
package used by the Theorem 4.1 endpoint wrappers.
-/
theorem vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
    {Coordinate : Type*} [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν] :
    (∀ i : ℕ,
      HasLaw
        (vaart1998_finiteCoordinateSampleVector
          (fun coordinate i sample => sample i coordinate) i)
        ν (Measure.infinitePi (fun _ : ℕ => ν))) ∧
    HasLaw
      (fun sample i =>
        vaart1998_finiteCoordinateSampleVector
          (fun coordinate i sample => sample i coordinate) i sample)
      (Measure.infinitePi (fun _ : ℕ => ν))
      (Measure.infinitePi (fun _ : ℕ => ν)) :=
  ⟨fun i => vaart1998_finiteCoordinateCanonicalSampleVector_hasLaw (ν := ν) i,
    vaart1998_finiteCoordinateCanonicalSampleVector_sequence_hasLaw (ν := ν)⟩

/--
Canonical iid finite-coordinate samples are coordinatewise measurable when
coordinate evaluation on the vector state space is measurable.
-/
theorem vaart1998_finiteCoordinateCanonicalSample_coordinate_measurable
    {Coordinate : Type*} [MeasurableSpace (Coordinate -> ℝ)]
    (coordinate : Coordinate) (i : ℕ)
    (hcoordinate_meas :
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate)) :
    Measurable
      ((fun coordinate i sample => sample i coordinate) coordinate i :
        (ℕ -> Coordinate -> ℝ) -> ℝ) := by
  simpa using hcoordinate_meas.comp (measurable_pi_apply i)

/--
Canonical iid finite-coordinate samples are coordinatewise `MemLp` when the
coordinate projection is `MemLp` under the common vector law.
-/
theorem vaart1998_finiteCoordinateCanonicalSample_coordinate_memLp
    {Coordinate : Type*} [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (coordinate : Coordinate) (i : ℕ)
    (hν_coordinate_memLp :
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν) :
    MemLp
      ((fun coordinate i sample => sample i coordinate) coordinate i :
        (ℕ -> Coordinate -> ℝ) -> ℝ)
      2 (Measure.infinitePi (fun _ : ℕ => ν)) := by
  simpa [Function.comp_def] using
    hν_coordinate_memLp.comp_measurePreserving
      (measurePreserving_eval_infinitePi (μ := fun _ : ℕ => ν) i)

/--
Canonical iid finite-coordinate samples provide the coordinate `MemLp` and
plain coordinate measurability source fields needed by Theorem 4.1 endpoints.
-/
theorem vaart1998_finiteCoordinateCanonicalSample_coordinateSource
    {Coordinate : Type*} [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν) :
    (∀ coordinate,
      MemLp
        ((fun coordinate i sample => sample i coordinate) coordinate 0 :
          (ℕ -> Coordinate -> ℝ) -> ℝ)
        2 (Measure.infinitePi (fun _ : ℕ => ν))) ∧
    (∀ coordinate i,
      Measurable
        ((fun coordinate i sample => sample i coordinate) coordinate i :
          (ℕ -> Coordinate -> ℝ) -> ℝ)) :=
  ⟨fun coordinate =>
      vaart1998_finiteCoordinateCanonicalSample_coordinate_memLp
        (ν := ν) coordinate 0 (hν_coordinate_memLp coordinate),
    fun coordinate i =>
      vaart1998_finiteCoordinateCanonicalSample_coordinate_measurable
        coordinate i (hcoordinate_meas coordinate)⟩

/--
Reusable source certificate for a finite-coordinate observation law: every
coordinate projection is measurable and square-integrable.
-/
structure Vaart1998FiniteCoordinateVectorLawSource
    (Coordinate : Type*) [MeasurableSpace (Coordinate -> ℝ)]
    (ν : Measure (Coordinate -> ℝ)) where
  /-- Coordinate evaluation is measurable under the vector state space. -/
  coordinate_meas : ∀ coordinate,
    Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate)
  /-- Every coordinate projection is square-integrable under the vector law. -/
  coordinate_memLp : ∀ coordinate,
    MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν

/--
A finite-coordinate vector-law source certificate gives square-integrability of
the identity vector under the common vector law.
-/
theorem Vaart1998FiniteCoordinateVectorLawSource.memLp_id
    {Coordinate : Type*} [Fintype Coordinate]
    [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)}
    (S : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν) :
    MemLp id 2 ν := by
  simpa using
    (MemLp.of_eval (f := fun sampleVector : Coordinate -> ℝ => sampleVector)
      S.coordinate_memLp)

/--
A finite-coordinate vector-law source certificate provides the canonical
product-sample coordinate source fields.
-/
theorem Vaart1998FiniteCoordinateVectorLawSource.canonicalCoordinateSource
    {Coordinate : Type*} [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (S : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν) :
    (∀ coordinate,
      MemLp
        ((fun coordinate i sample => sample i coordinate) coordinate 0 :
          (ℕ -> Coordinate -> ℝ) -> ℝ)
        2 (Measure.infinitePi (fun _ : ℕ => ν))) ∧
    (∀ coordinate i,
      Measurable
        ((fun coordinate i sample => sample i coordinate) coordinate i :
          (ℕ -> Coordinate -> ℝ) -> ℝ)) :=
  vaart1998_finiteCoordinateCanonicalSample_coordinateSource
    (ν := ν) S.coordinate_meas S.coordinate_memLp

/--
The canonical iid product-sample population moment is the coordinatewise mean
under the common vector law.
-/
theorem vaart1998_finiteCoordinateCanonicalSample_populationMoment_eq_integral
    {Coordinate : Type*} [Fintype Coordinate] [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate)) :
    vaart1998_finiteCoordinatePopulationMoment
        (Measure.infinitePi (fun _ : ℕ => ν))
        (fun coordinate i sample => sample i coordinate) =
      fun coordinate : Coordinate =>
        ∫ sampleVector, sampleVector coordinate ∂ν := by
  ext coordinate
  have hlaw :
      HasLaw
        (fun sample : ℕ -> Coordinate -> ℝ => sample 0)
        ν (Measure.infinitePi (fun _ : ℕ => ν)) :=
    (measurePreserving_eval_infinitePi (μ := fun _ : ℕ => ν) 0).hasLaw
  simpa [vaart1998_finiteCoordinatePopulationMoment, Function.comp_def] using
    (hlaw.integral_comp (f := fun sampleVector : Coordinate -> ℝ =>
      sampleVector coordinate) (hcoordinate_meas coordinate).aestronglyMeasurable)

/--
Scalar summand obtained by testing one finite-coordinate sample vector with a
continuous linear functional.
-/
noncomputable def vaart1998_finiteCoordinateProjectedSample
    {Coordinate Ω : Type*} [Fintype Coordinate]
    (L : StrongDual ℝ (Coordinate -> ℝ))
    (X : Coordinate -> ℕ -> Ω -> ℝ) (i : ℕ) (ω : Ω) : ℝ :=
  L (vaart1998_finiteCoordinateSampleVector X i ω)

/--
The canonical iid product-sample projected summand has the same variance as the
corresponding projection under the common vector law.
-/
theorem vaart1998_finiteCoordinateCanonicalProjectedSample_variance_eq
    {Coordinate : Type*} [Fintype Coordinate]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (L : StrongDual ℝ (Coordinate -> ℝ)) :
    Var[vaart1998_finiteCoordinateProjectedSample L
        (fun coordinate i sample => sample i coordinate) 0;
      Measure.infinitePi (fun _ : ℕ => ν)] =
      Var[L; ν] := by
  simpa [vaart1998_finiteCoordinateProjectedSample,
    vaart1998_finiteCoordinateSampleVector, Function.comp_def] using
    (measurePreserving_eval_infinitePi (μ := fun _ : ℕ => ν) 0).variance_fun_comp
      (f := L) L.continuous.measurable.aemeasurable

/--
A vector-law moment identity at the true parameter gives the exact
product-space population-moment source field for the canonical iid sample.
-/
theorem vaart1998_finiteCoordinateCanonicalSample_trueMoment_eq_populationMoment
    {Coordinate Θ : Type*} [Fintype Coordinate]
    [MeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν) :
    e theta0 =
      vaart1998_finiteCoordinatePopulationMoment
        (Measure.infinitePi (fun _ : ℕ => ν))
        (fun coordinate i sample => sample i coordinate) :=
  heta0ν.trans
    (vaart1998_finiteCoordinateCanonicalSample_populationMoment_eq_integral
      (ν := ν) hcoordinate_meas).symm

/--
A covariance identity against the common vector law gives the product-space
projected variance source field for the canonical iid sample.
-/
theorem vaart1998_finiteCoordinateCanonicalSample_covariance_eq_projectedVariance
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'}
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν]) :
    ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L
          (fun coordinate i sample => sample i coordinate) 0;
          Measure.infinitePi (fun _ : ℕ => ν)] := fun L =>
  (hZ_covarianceν L).trans
    (vaart1998_finiteCoordinateCanonicalProjectedSample_variance_eq
      (ν := ν) L).symm

/--
Two symmetric real continuous bilinear forms are equal when their diagonal
quadratic forms agree.
-/
theorem vaart1998_continuousBilinearMap_eq_of_diagonal
    {V : Type*} [NormedAddCommGroup V] [NormedSpace ℝ V]
    (B C : V →L[ℝ] V →L[ℝ] ℝ)
    (hBsymm : ∀ x y : V, B x y = B y x)
    (hCsymm : ∀ x y : V, C x y = C y x)
    (hdiag : ∀ x : V, B x x = C x x) :
    ∀ x y : V, B x y = C x y := by
  intro x y
  have hBsum :
      B (x + y) (x + y) = B x x + B x y + B y x + B y y := by
    simp [map_add, add_left_comm, add_comm]
  have hCsum :
      C (x + y) (x + y) = C x x + C x y + C y x + C y y := by
    simp [map_add, add_left_comm, add_comm]
  calc
    B x y =
        (B (x + y) (x + y) - B x x - B y y) / 2 := by
          rw [hBsum, hBsymm y x]
          ring
    _ = (C (x + y) (x + y) - C x x - C y y) / 2 := by
          rw [hdiag (x + y), hdiag x, hdiag y]
    _ = C x y := by
          rw [hCsum, hCsymm y x]
          ring

/--
For covariance bilinear forms, equality of all projected variances determines
all off-diagonal covariance entries by polarization.
-/
theorem vaart1998_covarianceBilinDual_eq_of_diagonal_variance
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E]
    [OpensMeasurableSpace E] [CompleteSpace E]
    {μ ν : Measure E} [IsFiniteMeasure ν]
    (hν_memLp : MemLp id 2 ν)
    (hdiag : ∀ L : StrongDual ℝ E,
      ProbabilityTheory.covarianceBilinDual μ L L = Var[L; ν]) :
    ∀ L K : StrongDual ℝ E,
      ProbabilityTheory.covarianceBilinDual μ L K =
        ProbabilityTheory.covarianceBilinDual ν L K :=
  vaart1998_continuousBilinearMap_eq_of_diagonal
    (B := ProbabilityTheory.covarianceBilinDual μ)
    (C := ProbabilityTheory.covarianceBilinDual ν)
    (fun L K => ProbabilityTheory.covarianceBilinDual_comm L K)
    (fun L K => ProbabilityTheory.covarianceBilinDual_comm L K)
    (fun L => by
      calc
        ProbabilityTheory.covarianceBilinDual μ L L = Var[L; ν] := hdiag L
        _ = ProbabilityTheory.covarianceBilinDual ν L L :=
              (ProbabilityTheory.covarianceBilinDual_self_eq_variance hν_memLp L).symm)

/--
The probability-notation mean-zero field is exactly the explicit Bochner
integral mean-zero field used by the finite-dimensional sample-mean endpoint.
-/
theorem vaart1998_finiteCoordinateIntegralMapMean_eq_zero_of_map_mean_zero
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace (Coordinate -> ℝ)]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_mean_zero : (Q.map Z)[id] = 0) :
    (∫ z, z ∂(Q.map Z)) = 0 := by
  simpa using hZ_mean_zero

/--
Mean zero of the vector law gives zero mean for every continuous linear
projection.
-/
theorem vaart1998_finiteCoordinateProjectedMean_eq_zero_of_map_mean_zero
    {Coordinate Ω' : Type*} [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0) :
    ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0 := by
  intro L
  haveI : IsProbabilityMeasure (Q.map Z) :=
    Measure.isProbabilityMeasure_map hZ_aemeas
  have hZ_integrable : Integrable id (Q.map Z) :=
    hZ_memLp.integrable (by norm_num)
  calc
    Q[fun ω => L (Z ω)] = ∫ x, L x ∂Q.map Z :=
      (integral_map hZ_aemeas (by fun_prop : AEStronglyMeasurable L (Q.map Z))).symm
    _ = L ((Q.map Z)[id]) := L.integral_comp_comm hZ_integrable
    _ = 0 := by rw [hZ_mean_zero, map_zero]

/--
Projected samples inherit `MemLp` from the finite-coordinate sample vector.
-/
theorem vaart1998_finiteCoordinateProjectedSample_memLp_of_vectorMemLp
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    (L : StrongDual ℝ (Coordinate -> ℝ))
    (hX_memLp : MemLp (vaart1998_finiteCoordinateSampleVector X 0) 2 P) :
    MemLp (vaart1998_finiteCoordinateProjectedSample L X 0) 2 P := by
  simpa [vaart1998_finiteCoordinateProjectedSample, Function.comp_def] using
    (hX_memLp.continuousLinearMap_comp L)

/--
Projected samples inherit independence from the finite-coordinate sample-vector
sequence.
-/
theorem vaart1998_finiteCoordinateProjectedSample_iIndepFun_of_vector_iIndepFun
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    (L : StrongDual ℝ (Coordinate -> ℝ))
    (hX_indep : iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P) :
    iIndepFun (vaart1998_finiteCoordinateProjectedSample L X) P := by
  simpa [vaart1998_finiteCoordinateProjectedSample, Function.comp_def] using
    hX_indep.comp (fun _ => L) (fun _ => L.continuous.measurable)

/--
Projected samples inherit identical distribution from the finite-coordinate
sample vectors.
-/
theorem vaart1998_finiteCoordinateProjectedSample_identDistrib_of_vector_identDistrib
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    (L : StrongDual ℝ (Coordinate -> ℝ)) (i : ℕ)
    (hX_ident :
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P) :
    IdentDistrib
      (vaart1998_finiteCoordinateProjectedSample L X i)
      (vaart1998_finiteCoordinateProjectedSample L X 0) P P := by
  simpa [vaart1998_finiteCoordinateProjectedSample, Function.comp_def] using
    hX_ident.comp L.continuous.measurable

/--
Testing the finite-coordinate population moment agrees with the integral of the
tested first summand.
-/
theorem vaart1998_finiteCoordinateProjectedSample_integral_eq_populationMoment
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} {X : Coordinate -> ℕ -> Ω -> ℝ}
    (L : StrongDual ℝ (Coordinate -> ℝ))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P) :
    P[vaart1998_finiteCoordinateProjectedSample L X 0] =
      vaart1998_finiteCoordinateProjectedPopulationMoment L P X := by
  let Y : Ω -> Coordinate -> ℝ := fun ω coordinate => X coordinate 0 ω
  have hY : Integrable Y P := Integrable.of_eval (f := Y) hX_integrable
  have hcomp : ∫ ω, L (Y ω) ∂P = L (∫ ω, Y ω ∂P) :=
    L.integral_comp_comm hY
  have hpop : ∫ ω, Y ω ∂P = vaart1998_finiteCoordinatePopulationMoment P X := by
    ext coordinate
    exact MeasureTheory.eval_integral (f := Y) hX_integrable coordinate
  calc
    P[vaart1998_finiteCoordinateProjectedSample L X 0] =
        ∫ ω, L (Y ω) ∂P := by
          rfl
    _ = L (∫ ω, Y ω ∂P) := hcomp
    _ = vaart1998_finiteCoordinateProjectedPopulationMoment L P X := by
          rw [hpop]
          rfl

/--
The projected empirical average is the ordinary scalar average of the projected
sample summands.
-/
theorem vaart1998_finiteCoordinateProjectedEmpiricalAverage_eq_inv_mul_sum_sample
    {Coordinate Ω : Type*} [Fintype Coordinate]
    (L : StrongDual ℝ (Coordinate -> ℝ))
    (X : Coordinate -> ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_finiteCoordinateProjectedEmpiricalAverage L X n ω =
      (n : ℝ)⁻¹ *
        ∑ i ∈ Finset.range n,
          vaart1998_finiteCoordinateProjectedSample L X i ω := by
  let v : ℕ -> Coordinate -> ℝ := fun i coordinate => X coordinate i ω
  have hemp :
      vaart1998_finiteCoordinateEmpiricalMoment X n ω =
        (n : ℝ)⁻¹ • ∑ i ∈ Finset.range n, v i := by
    ext coordinate
    simp [vaart1998_finiteCoordinateEmpiricalMoment, v, div_eq_inv_mul,
      smul_eq_mul, Finset.sum_apply]
  calc
    vaart1998_finiteCoordinateProjectedEmpiricalAverage L X n ω
        = L ((n : ℝ)⁻¹ • ∑ i ∈ Finset.range n, v i) := by
          simp [vaart1998_finiteCoordinateProjectedEmpiricalAverage, hemp]
    _ = (n : ℝ)⁻¹ *
        ∑ i ∈ Finset.range n, L (v i) := by
          simp
    _ = (n : ℝ)⁻¹ *
        ∑ i ∈ Finset.range n,
          vaart1998_finiteCoordinateProjectedSample L X i ω := by
          congr 1

/--
Projected centered empirical averages can be written in the usual scalar
CLT sum-centered normalization.
-/
theorem vaart1998_finiteCoordinateProjectedScalarCLT_expression_eq_sum
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    (L : StrongDual ℝ (Coordinate -> ℝ)) (P : Measure Ω)
    (X : Coordinate -> ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) :
    √(n : ℝ) *
        (vaart1998_finiteCoordinateProjectedEmpiricalAverage L X n ω -
          vaart1998_finiteCoordinateProjectedPopulationMoment L P X) =
      (√(n : ℝ))⁻¹ *
        ((∑ i ∈ Finset.range n,
            vaart1998_finiteCoordinateProjectedSample L X i ω) -
          (n : ℝ) *
            vaart1998_finiteCoordinateProjectedPopulationMoment L P X) := by
  rw [vaart1998_finiteCoordinateProjectedEmpiricalAverage_eq_inv_mul_sum_sample]
  by_cases hn : n = 0
  · subst n
    simp
  · have hnpos_nat : 0 < n := Nat.pos_of_ne_zero hn
    have hnpos : 0 < (n : ℝ) := Nat.cast_pos.mpr hnpos_nat
    have hsqrt_pos : 0 < √(n : ℝ) := Real.sqrt_pos_of_pos hnpos
    have hsqrt_ne : √(n : ℝ) ≠ 0 := ne_of_gt hsqrt_pos
    have hn_ne : (n : ℝ) ≠ 0 := ne_of_gt hnpos
    have hsqrt_sq : (√(n : ℝ)) ^ 2 = (n : ℝ) :=
      Real.sq_sqrt hnpos.le
    field_simp [hsqrt_ne, hn_ne]
    rw [hsqrt_sq]

/--
Linearity identity for projected centered empirical moments.
-/
theorem vaart1998_finiteCoordinateProjected_scaled_centered_empiricalMoment_eq
    {Coordinate Ω : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    (L : StrongDual ℝ (Coordinate -> ℝ)) (P : Measure Ω)
    (X : Coordinate -> ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) :
    L (√(n : ℝ) •
        (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
          vaart1998_finiteCoordinatePopulationMoment P X)) =
      √(n : ℝ) *
        (vaart1998_finiteCoordinateProjectedEmpiricalAverage L X n ω -
          vaart1998_finiteCoordinateProjectedPopulationMoment L P X) := by
  simp [vaart1998_finiteCoordinateProjectedEmpiricalAverage,
    vaart1998_finiteCoordinateProjectedPopulationMoment, smul_eq_mul]

/--
Scalar projected empirical-moment CLT family in the usual real-valued
centered-average form.
-/
def vaart1998_finiteCoordinateProjectedScalarCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (Z : Ω' -> Coordinate -> ℝ) : Prop :=
  ∀ L : StrongDual ℝ (Coordinate -> ℝ),
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) *
          (vaart1998_finiteCoordinateProjectedEmpiricalAverage L X n ω -
            vaart1998_finiteCoordinateProjectedPopulationMoment L P X))
      atTop (fun ω => L (Z ω)) (fun _ => P) Q

/--
Source-shaped scalar CLT for the projected finite-coordinate summands.
-/
def vaart1998_finiteCoordinateProjectedSummandCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (Z : Ω' -> Coordinate -> ℝ) : Prop :=
  ∀ L : StrongDual ℝ (Coordinate -> ℝ),
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        (√(n : ℝ))⁻¹ *
          ((∑ i ∈ Finset.range n,
              vaart1998_finiteCoordinateProjectedSample L X i ω) -
            (n : ℝ) *
              vaart1998_finiteCoordinateProjectedPopulationMoment L P X))
      atTop (fun ω => L (Z ω)) (fun _ => P) Q

/--
Projected summand scalar CLTs feed the projected scalar empirical-moment CLT
family by the finite-average algebra used in Cramér-Wold.
-/
theorem vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hsummand :
      vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z) :
    vaart1998_finiteCoordinateProjectedScalarCLT (P := P) (Q := Q) X Z := by
  intro L
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl (hsummand L)
  intro n
  exact Filter.Eventually.of_forall fun ω =>
    (vaart1998_finiteCoordinateProjectedScalarCLT_expression_eq_sum
      L P X n ω).symm

/--
Mathlib's one-dimensional central limit theorem instantiates the projected
summand CLT family once each tested summand sequence has the usual source
fields.
-/
theorem vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hMean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      P[vaart1998_finiteCoordinateProjectedSample L X 0] =
        vaart1998_finiteCoordinateProjectedPopulationMoment L P X)
    (hLimitLaw : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      HasLaw (fun ω => L (Z ω))
        (gaussianReal 0
          (Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]).toNNReal) Q)
    (hMemLp : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      MemLp (vaart1998_finiteCoordinateProjectedSample L X 0) 2 P)
    (hIndep : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      iIndepFun (vaart1998_finiteCoordinateProjectedSample L X) P)
    (hIdent : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ∀ i : ℕ,
        IdentDistrib
          (vaart1998_finiteCoordinateProjectedSample L X i)
          (vaart1998_finiteCoordinateProjectedSample L X 0) P P) :
    vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z := by
  intro L
  have hclt :
      TendstoInDistribution
        (fun (n : ℕ) ω =>
          (√(n : ℝ))⁻¹ *
            ((∑ k ∈ Finset.range n,
                vaart1998_finiteCoordinateProjectedSample L X k ω) -
              (n : ℝ) *
                P[vaart1998_finiteCoordinateProjectedSample L X 0]))
        atTop (fun ω => L (Z ω)) (fun _ => P) Q :=
    ProbabilityTheory.tendstoInDistribution_inv_sqrt_mul_sum_sub
      (P := P) (P' := Q)
      (X := vaart1998_finiteCoordinateProjectedSample L X)
      (Y := fun ω => L (Z ω))
      (hY := hLimitLaw L) (hX := hMemLp L)
      (hindep := hIndep L) (hident := hIdent L)
  refine TendstoInDistribution.congr ?_ Filter.EventuallyEq.rfl hclt
  intro n
  exact Filter.Eventually.of_forall fun ω => by
    rw [hMean L]

/--
Mathlib's one-dimensional central limit theorem instantiates the projected
summand CLT family, with the projected mean field discharged from
finite-coordinate integrability.
-/
theorem vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_integrableMean
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hLimitLaw : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      HasLaw (fun ω => L (Z ω))
        (gaussianReal 0
          (Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]).toNNReal) Q)
    (hMemLp : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      MemLp (vaart1998_finiteCoordinateProjectedSample L X 0) 2 P)
    (hIndep : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      iIndepFun (vaart1998_finiteCoordinateProjectedSample L X) P)
    (hIdent : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ∀ i : ℕ,
        IdentDistrib
          (vaart1998_finiteCoordinateProjectedSample L X i)
          (vaart1998_finiteCoordinateProjectedSample L X 0) P P) :
    vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z :=
  vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hMean := fun L =>
      vaart1998_finiteCoordinateProjectedSample_integral_eq_populationMoment
        (P := P) (X := X) L hX_integrable)
    (hLimitLaw := hLimitLaw) (hMemLp := hMemLp)
    (hIndep := hIndep) (hIdent := hIdent)

/--
Vector-valued finite-coordinate source fields feed the projected summand CLT
through continuous linear projections and mathlib's one-dimensional CLT.
-/
theorem vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_vectorSource
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hLimitLaw : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      HasLaw (fun ω => L (Z ω))
        (gaussianReal 0
          (Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]).toNNReal) Q)
    (hX_memLp : MemLp (vaart1998_finiteCoordinateSampleVector X 0) 2 P)
    (hX_indep : iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P)
    (hX_ident : ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P) :
    vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z :=
  vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_integrableMean
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_integrable := hX_integrable)
    (hLimitLaw := hLimitLaw)
    (hMemLp := fun L =>
      vaart1998_finiteCoordinateProjectedSample_memLp_of_vectorMemLp
        (P := P) (X := X) L hX_memLp)
    (hIndep := fun L =>
      vaart1998_finiteCoordinateProjectedSample_iIndepFun_of_vector_iIndepFun
        (P := P) (X := X) L hX_indep)
    (hIdent := fun L i =>
      vaart1998_finiteCoordinateProjectedSample_identDistrib_of_vector_identDistrib
        (P := P) (X := X) L i (hX_ident i))

/--
A finite-coordinate Gaussian limit gives the scalar Gaussian laws needed by the
projected one-dimensional CLT once its projected mean and variance are
identified.
-/
theorem vaart1998_finiteCoordinateProjectedGaussianLimitLaw_of_zeroMean_variance
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} {Q : Measure Ω'}
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_variance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Var[fun ω => L (Z ω); Q] =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]) :
    ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      HasLaw (fun ω => L (Z ω))
        (gaussianReal 0
          (Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]).toNNReal) Q := by
  intro L
  let Y : Ω' -> ℝ := fun ω => L (Z ω)
  have hY_gaussian : HasGaussianLaw Y Q := hZ_gaussian.map_fun L
  refine ⟨hY_gaussian.aemeasurable, ?_⟩
  have hmap :
      Q.map Y =
        gaussianReal (Q.map Y)[id] (Var[id; Q.map Y]).toNNReal :=
    ProbabilityTheory.IsGaussian.eq_gaussianReal (Q.map Y) hY_gaussian.isGaussian_map
  calc
    Q.map (fun ω => L (Z ω)) = Q.map Y := rfl
    _ = gaussianReal (Q.map Y)[id] (Var[id; Q.map Y]).toNNReal := hmap
    _ = gaussianReal (Q[Y]) (Var[Y; Q]).toNNReal := by
          rw [integral_map hY_gaussian.aemeasurable (by fun_prop),
            variance_map (by fun_prop) hY_gaussian.aemeasurable]
          rfl
    _ = gaussianReal 0
        (Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]).toNNReal := by
          rw [hZ_mean L, hZ_variance L]

/--
Covariance-bilinear identification of the finite-coordinate Gaussian limit
supplies the scalar Gaussian laws needed by projected one-dimensional CLTs.
-/
theorem vaart1998_finiteCoordinateProjectedGaussianLimitLaw_of_covarianceBilinDual
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} {Q : Measure Ω'}
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]) :
    ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      HasLaw (fun ω => L (Z ω))
        (gaussianReal 0
          (Var[vaart1998_finiteCoordinateProjectedSample L X 0; P]).toNNReal) Q :=
  vaart1998_finiteCoordinateProjectedGaussianLimitLaw_of_zeroMean_variance
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hZ_gaussian := hZ_gaussian) (hZ_mean := hZ_mean)
    (hZ_variance := fun L => by
      letI : IsGaussian (Q.map Z) := hZ_gaussian.isGaussian_map
      have hmap :
          Var[L; Q.map Z] = Var[fun ω => L (Z ω); Q] := by
        simpa [Function.comp_def] using
          (variance_map (X := L) (Y := Z) (μ := Q) (by fun_prop)
            hZ_gaussian.aemeasurable)
      calc
        Var[fun ω => L (Z ω); Q] = Var[L; Q.map Z] := hmap.symm
        _ = ProbabilityTheory.covarianceBilinDual (Q.map Z) L L :=
              (ProbabilityTheory.covarianceBilinDual_self_eq_variance hZ_memLp L).symm
        _ = Var[vaart1998_finiteCoordinateProjectedSample L X 0; P] :=
              hZ_covariance L)

/--
Vector-valued finite-coordinate source fields, a finite-coordinate Gaussian
limit, zero projected mean, and covariance identification feed the projected
summand CLT through mathlib's one-dimensional CLT.
-/
theorem vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_vectorGaussianSource
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P])
    (hX_memLp : MemLp (vaart1998_finiteCoordinateSampleVector X 0) 2 P)
    (hX_indep : iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P)
    (hX_ident : ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P) :
    vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z :=
  vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_vectorSource
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_integrable := hX_integrable)
    (hLimitLaw :=
      vaart1998_finiteCoordinateProjectedGaussianLimitLaw_of_covarianceBilinDual
        (P := P) (Q := Q) (X := X) (Z := Z)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance))
    (hX_memLp := hX_memLp) (hX_indep := hX_indep)
    (hX_ident := hX_ident)

/--
Coordinatewise `MemLp 2` supplies both integrability and vector `MemLp` for the
vector-Gaussian projected summand CLT source wrapper.
-/
theorem vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P])
    (hX_indep : iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P)
    (hX_ident : ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P) :
    vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z :=
  vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_vectorGaussianSource
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_integrable := fun coordinate =>
      (hX_coordinate_memLp coordinate).integrable (by norm_num))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
    (hX_memLp :=
      vaart1998_finiteCoordinateSampleVector_memLp_of_coordinate_memLp
        (P := P) (X := X) 0 hX_coordinate_memLp)
    (hX_indep := hX_indep) (hX_ident := hX_ident)

/--
Coordinatewise `MemLp 2`, a common finite-coordinate vector law, the infinite
product law of the sample-vector sequence, and a finite-coordinate Gaussian
limit feed the projected summand CLT.
-/
theorem vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P])
    (hX_vector_law : ∀ i : ℕ,
      HasLaw (vaart1998_finiteCoordinateSampleVector X i) ν P)
    (hX_sequence_law :
      HasLaw (fun ω i => vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P) :
    vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z :=
  vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
    (P := P) (Q := Q) (X := X) (Z := Z)
    (hX_coordinate_memLp := hX_coordinate_memLp)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
    (hX_indep :=
      vaart1998_finiteCoordinateSampleVector_iIndepFun_of_hasLaw_infinitePi
        (P := P) (X := X) (ν := fun _ : ℕ => ν)
        hX_vector_law hX_sequence_law)
    (hX_ident :=
      vaart1998_finiteCoordinateSampleVector_identDistrib_of_common_hasLaw
        (P := P) (X := X) hX_vector_law)

/--
The scalar projected CLT family feeds the projected vector CLT family by
continuous-linear algebra.
-/
theorem vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT_of_projectedScalarCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hscalar : vaart1998_finiteCoordinateProjectedScalarCLT (P := P) (Q := Q) X Z) :
    vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT (P := P) (Q := Q) X Z := by
  intro L
  exact TendstoInDistribution.congr
    (fun n => Filter.Eventually.of_forall fun ω =>
      (vaart1998_finiteCoordinateProjected_scaled_centered_empiricalMoment_eq
        L P X n ω).symm)
    (Filter.EventuallyEq.rfl)
    (hscalar L)

/--
Build the Cramér-Wold bridge from scalar projected CLTs plus the remaining
Cramér-Wold implication.
-/
def vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (Z : Ω' -> Coordinate -> ℝ)
    (hscalar : vaart1998_finiteCoordinateProjectedScalarCLT (P := P) (Q := Q) X Z)
    (hCramerWold :
      vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT (P := P) (Q := Q) X Z ->
        TendstoInDistribution
          (fun (n : ℕ) ω =>
            √(n : ℝ) •
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
                vaart1998_finiteCoordinatePopulationMoment P X))
          atTop Z (fun _ => P) Q) :
    Vaart1998FiniteCoordinateCramerWoldCLTBridge Coordinate Ω Ω' P Q where
  X := X
  Z := Z
  projected_clt :=
    vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT_of_projectedScalarCLT
      (P := P) (Q := Q) hscalar
  cramerWold_vector_clt := hCramerWold

/--
Build the finite-coordinate empirical-moment CLT from law-level weak
convergence of the scaled centered vector.
-/
theorem vaart1998_finiteCoordinateEmpiricalMomentCLT_of_law_tendsto
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hlaw :
      Tendsto (β := ProbabilityMeasure (Coordinate -> ℝ))
        (fun n : ℕ =>
          (⟨P.map
              (vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n),
            Measure.isProbabilityMeasure_map
              (vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aemeasurable_real
                (P := P) X hX_meas n)⟩ :
            ProbabilityMeasure (Coordinate -> ℝ)))
        atTop
        (𝓝 (⟨Q.map Z, Measure.isProbabilityMeasure_map hZ_aemeas⟩ :
          ProbabilityMeasure (Coordinate -> ℝ)))) :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
            vaart1998_finiteCoordinatePopulationMoment P X))
      atTop Z (fun _ => P) Q := by
  simpa [vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment] using
    ({ forall_aemeasurable :=
        vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aemeasurable_real
          (P := P) X hX_meas
       aemeasurable_limit := hZ_aemeas
       tendsto := hlaw } :
      TendstoInDistribution
        (fun n => vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n)
        atTop Z (fun _ => P) Q)

/--
Build the Cramér-Wold bridge from real-valued projected scalar CLTs once the
remaining Cramér-Wold step has been proved at the law-convergence level.
-/
def vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_lawTendsto
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (Z : Ω' -> Coordinate -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hscalar : vaart1998_finiteCoordinateProjectedScalarCLT (P := P) (Q := Q) X Z)
    (hCramerWoldLaw :
      vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT (P := P) (Q := Q) X Z ->
        Tendsto (β := ProbabilityMeasure (Coordinate -> ℝ))
          (fun n : ℕ =>
            (⟨P.map
                (vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n),
              Measure.isProbabilityMeasure_map
                (vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aemeasurable_real
                  (P := P) X hX_meas n)⟩ :
              ProbabilityMeasure (Coordinate -> ℝ)))
          atTop
          (𝓝 (⟨Q.map Z, Measure.isProbabilityMeasure_map hZ_aemeas⟩ :
            ProbabilityMeasure (Coordinate -> ℝ)))) :
    Vaart1998FiniteCoordinateCramerWoldCLTBridge Coordinate Ω Ω' P Q where
  X := X
  Z := Z
  projected_clt :=
    vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT_of_projectedScalarCLT
      (P := P) (Q := Q) hscalar
  cramerWold_vector_clt := fun hprojected =>
    vaart1998_finiteCoordinateEmpiricalMomentCLT_of_law_tendsto
      (P := P) (Q := Q) hX_meas hZ_aemeas (hCramerWoldLaw hprojected)

/--
Projected random-variable CLTs imply projected convergence of the corresponding
vector laws.
-/
theorem vaart1998_finiteCoordinateProjectedLawConvergence_of_projectedCLT
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : Coordinate -> ℕ -> Ω -> ℝ} {Z : Ω' -> Coordinate -> ℝ}
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hprojected :
      vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT (P := P) (Q := Q) X Z) :
    vaart1998_finiteCoordinateProjectedLawConvergence
      (fun n =>
        vaart1998_finiteCoordinateScaledCenteredEmpiricalMomentLaw
          (P := P) X hX_meas n)
      (vaart1998_finiteCoordinateVectorLimitLaw (Q := Q) Z hZ_aemeas) := by
  intro L
  have h := (hprojected L).tendsto
  have hseq_eq :
      (fun n =>
        (vaart1998_finiteCoordinateScaledCenteredEmpiricalMomentLaw
          (P := P) X hX_meas n).map L.continuous.measurable.aemeasurable) =
        (fun n : ℕ =>
          (⟨P.map
            (fun ω =>
              L (√(n : ℝ) •
                (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
                  vaart1998_finiteCoordinatePopulationMoment P X))),
            Measure.isProbabilityMeasure_map ((hprojected L).forall_aemeasurable n)⟩ :
            ProbabilityMeasure ℝ)) := by
    funext n
    ext s
    change
      ((P.map
          (vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment P X n)).map L) s =
        (P.map
          (fun ω =>
            L (√(n : ℝ) •
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω -
                vaart1998_finiteCoordinatePopulationMoment P X)))) s
    rw [AEMeasurable.map_map_of_aemeasurable
      L.continuous.measurable.aemeasurable
      (vaart1998_finiteCoordinate_scaledCenteredEmpiricalMoment_aemeasurable_real
        (P := P) X hX_meas n)]
    simp [Function.comp_def, vaart1998_finiteCoordinateScaledCenteredEmpiricalMoment]
  have hlim_eq :
      (vaart1998_finiteCoordinateVectorLimitLaw (Q := Q) Z hZ_aemeas).map
          L.continuous.measurable.aemeasurable =
        (⟨Q.map (fun ω => L (Z ω)),
          Measure.isProbabilityMeasure_map ((hprojected L).aemeasurable_limit)⟩ :
          ProbabilityMeasure ℝ) := by
    ext s
    change ((Q.map Z).map L) s = (Q.map (fun ω => L (Z ω))) s
    rw [AEMeasurable.map_map_of_aemeasurable
      L.continuous.measurable.aemeasurable hZ_aemeas]
    rfl
  simpa [hseq_eq, hlim_eq] using h

/--
Build the Cramér-Wold bridge from projected scalar CLTs and a pure law-level
Cramér-Wold theorem.
-/
def vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_projectedLaw
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (Z : Ω' -> Coordinate -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hscalar : vaart1998_finiteCoordinateProjectedScalarCLT (P := P) (Q := Q) X Z)
    (hCramerWoldLaw :
      vaart1998_finiteCoordinateProjectedLawConvergence
          (fun n =>
            vaart1998_finiteCoordinateScaledCenteredEmpiricalMomentLaw
              (P := P) X hX_meas n)
          (vaart1998_finiteCoordinateVectorLimitLaw (Q := Q) Z hZ_aemeas) ->
        Tendsto (β := ProbabilityMeasure (Coordinate -> ℝ))
          (fun n =>
            vaart1998_finiteCoordinateScaledCenteredEmpiricalMomentLaw
              (P := P) X hX_meas n)
          atTop
          (𝓝 (vaart1998_finiteCoordinateVectorLimitLaw (Q := Q) Z hZ_aemeas))) :
    Vaart1998FiniteCoordinateCramerWoldCLTBridge Coordinate Ω Ω' P Q :=
  vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_lawTendsto
    (P := P) (Q := Q) X Z hX_meas hZ_aemeas hscalar
    (fun hprojected => by
      simpa [vaart1998_finiteCoordinateScaledCenteredEmpiricalMomentLaw,
        vaart1998_finiteCoordinateVectorLimitLaw] using
        hCramerWoldLaw
          (vaart1998_finiteCoordinateProjectedLawConvergence_of_projectedCLT
            (P := P) (Q := Q) hX_meas hZ_aemeas hprojected))

/--
Build the Cramér-Wold bridge from projected scalar CLTs using the compiled
finite-dimensional law-level Cramér-Wold theorem.
-/
def vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_finiteDimensional
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (X : Coordinate -> ℕ -> Ω -> ℝ) (Z : Ω' -> Coordinate -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hZ_aemeas : AEMeasurable Z Q)
    (hscalar : vaart1998_finiteCoordinateProjectedScalarCLT (P := P) (Q := Q) X Z) :
    Vaart1998FiniteCoordinateCramerWoldCLTBridge Coordinate Ω Ω' P Q :=
  vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_projectedLaw
    (P := P) (Q := Q) X Z hX_meas hZ_aemeas hscalar
    (fun hprojected =>
      vaart1998_finiteCoordinateProjectedLawConvergence_lawTendsto hprojected)

/--
The vector CLT certificate implies every projected scalar CLT by the continuous
mapping theorem.
-/
theorem vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT_of_cltCertificate
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (CLT :
      Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
        Coordinate Ω Ω' P Q) :
    vaart1998_finiteCoordinateProjectedEmpiricalMomentCLT
      (P := P) (Q := Q) CLT.X CLT.Z := by
  intro L
  simpa [Function.comp_def] using
    (TendstoInDistribution.continuous_comp (g := fun x : Coordinate -> ℝ => L x)
      L.continuous CLT.empiricalMoment_clt)

/--
Build the vector CLT certificate from a Cramér-Wold bridge plus Gaussian and
square-integrability facts for the supplied vector limit.
-/
def vaart1998_finiteCoordinateEmpiricalMomentCLTCertificate_of_cramerWoldBridge
    {Coordinate Ω Ω' : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [MeasurableSpace Ω'] [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    (B : Vaart1998FiniteCoordinateCramerWoldCLTBridge Coordinate Ω Ω' P Q)
    (hZ_gaussian : HasGaussianLaw B.Z Q)
    (hZ_memLp : MemLp id 2 (Q.map B.Z)) :
    Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
      Coordinate Ω Ω' P Q where
  X := B.X
  Z := B.Z
  empiricalMoment_clt := B.cramerWold_vector_clt B.projected_clt
  gaussian_limit := hZ_gaussian
  limit_memLp := hZ_memLp

/--
Local-range probability certificate from almost-sure empirical-moment
convergence to the true moment.
-/
def vaart1998_momentEstimatorLocalRangeProbabilityCertificate_of_ae_tendsto
    {Ω M : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [PseudoMetricSpace M] [MeasurableSpace M] [OpensMeasurableSpace M]
    (empiricalMoment : ℕ -> Ω -> M) {eta0 : M} (momentRange : Set M)
    (hOpen : IsOpen momentRange) (heta0 : eta0 ∈ momentRange)
    (hstrong : ∀ n : ℕ, AEStronglyMeasurable (empiricalMoment n) P)
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n))
    (hAE : ∀ᵐ ω ∂P,
      Tendsto (fun n : ℕ => empiricalMoment n ω) atTop (𝓝 eta0)) :
    Vaart1998MomentEstimatorLocalRangeProbabilityCertificate Ω M P :=
  vaart1998_momentEstimatorLocalRangeProbabilityCertificate_of_tendstoInMeasure
    empiricalMoment momentRange hOpen heta0
    (vaart1998_empiricalMoment_tendstoInMeasure_of_ae_tendsto_const
      hstrong hAE)
    hmeas

/--
Open inverse-function-theorem local-range probability.

This specializes the open-neighborhood localization lemma to the target
neighborhood produced by `HasStrictFDerivAt.toOpenPartialHomeomorph`.
-/
theorem vaart1998_theorem_4_1_open_local_range_probability_of_hasStrictFDerivAt
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    {empiricalMoment : ℕ -> Ω -> M}
    (hconv : TendstoInMeasure P empiricalMoment atTop (fun _ : Ω => e theta0))
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n)) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          empiricalMoment n ω ∈ (he.toOpenPartialHomeomorph e).target})
        atTop (𝓝 1) :=
  vaart1998_local_range_probability_of_tendstoInMeasure_const
    (hOpen := (he.toOpenPartialHomeomorph e).open_target)
    (heta0 := he.image_mem_toOpenPartialHomeomorph_target)
    hconv hmeas

/--
Local-range probability certificate generated from the inverse function theorem
and convergence in probability of empirical moments to the true moment.
-/
def vaart1998_momentEstimatorLocalRangeProbabilityCertificate_of_hasStrictFDerivAt_tendstoInMeasure
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (empiricalMoment : ℕ -> Ω -> M)
    (hconv : TendstoInMeasure P empiricalMoment atTop (fun _ : Ω => e theta0))
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n)) :
    Vaart1998MomentEstimatorLocalRangeProbabilityCertificate Ω M P where
  empiricalMoment := empiricalMoment
  momentRange := (he.toOpenPartialHomeomorph e).target
  localRange_probability :=
    vaart1998_theorem_4_1_open_local_range_probability_of_hasStrictFDerivAt
      e De he hconv hmeas

/--
Finite-coordinate target-probability localization certificate from convergence
in probability of empirical moments to the true moment.
-/
def Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate.of_tendstoInMeasure_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hconv : TendstoInMeasure P
      (fun n : ℕ => vaart1998_finiteCoordinateEmpiricalMoment X n)
      atTop (fun _ : Ω => e theta0))
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
      Coordinate Ω Θ P e theta0 De he X where
  empiricalMoment_mem_target_probability :=
    vaart1998_theorem_4_1_open_local_range_probability_of_hasStrictFDerivAt
      (P := P) e De he hconv
      (fun n => by
        simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
          vaart1998_finiteCoordinate_empiricalMoment_measurable_real X hX_meas n)

/--
Finite-coordinate target-probability localization certificate from the
coordinatewise strong law.
-/
def Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate.of_finiteCoordinateStrongLaw_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i)) :
    Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
      Coordinate Ω Θ P e theta0 De he X :=
  Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate.of_tendstoInMeasure_real
    (P := P) (e := e) (theta0 := theta0) (De := De) (he := he)
    (X := X)
    (hconv := by
      simpa [vaart1998_finiteCoordinateEmpiricalMoment,
        vaart1998_finiteCoordinatePopulationMoment, heta0] using
        vaart1998_finiteCoordinate_empiricalMoment_tendstoInMeasure_real
          X hX_integrable hX_indep hX_ident
          (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
            X hX_meas))
    (hX_meas := hX_meas)

/--
Open inverse-function-theorem local-range probability from almost-sure
empirical-moment convergence.
-/
theorem vaart1998_theorem_4_1_open_local_range_probability_of_hasStrictFDerivAt_ae_tendsto
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    {empiricalMoment : ℕ -> Ω -> M}
    (hstrong : ∀ n : ℕ, AEStronglyMeasurable (empiricalMoment n) P)
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n))
    (hAE : ∀ᵐ ω ∂P,
      Tendsto (fun n : ℕ => empiricalMoment n ω) atTop (𝓝 (e theta0))) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          empiricalMoment n ω ∈ (he.toOpenPartialHomeomorph e).target})
        atTop (𝓝 1) :=
  vaart1998_theorem_4_1_open_local_range_probability_of_hasStrictFDerivAt
    e De he
    (vaart1998_empiricalMoment_tendstoInMeasure_of_ae_tendsto_const
      hstrong hAE)
    hmeas

/--
Local-range probability certificate from strict differentiability and
almost-sure empirical-moment convergence.
-/
def vaart1998_momentEstimatorLocalRangeProbabilityCertificate_of_hasStrictFDerivAt_ae_tendsto
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (empiricalMoment : ℕ -> Ω -> M)
    (hstrong : ∀ n : ℕ, AEStronglyMeasurable (empiricalMoment n) P)
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n))
    (hAE : ∀ᵐ ω ∂P,
      Tendsto (fun n : ℕ => empiricalMoment n ω) atTop (𝓝 (e theta0))) :
    Vaart1998MomentEstimatorLocalRangeProbabilityCertificate Ω M P :=
  vaart1998_momentEstimatorLocalRangeProbabilityCertificate_of_hasStrictFDerivAt_tendstoInMeasure
    e De he empiricalMoment
    (vaart1998_empiricalMoment_tendstoInMeasure_of_ae_tendsto_const
      hstrong hAE)
    hmeas

/--
If the empirical moment lies in the local range, the inverse candidate solves
the moment equation.
-/
theorem vaart1998_theorem_4_1_moment_estimator_solves_on_local_range
    {Ω M Θ : Type*} (C : Vaart1998MomentLocalRangeCertificate M Θ)
    {empiricalMoment : ℕ -> Ω -> M} {n : ℕ} {ω : Ω}
    (hmem : empiricalMoment n ω ∈ C.momentRange) :
    C.e (C.eInv (empiricalMoment n ω)) = empiricalMoment n ω :=
  C.right_inverse_on_momentRange hmem

/--
Pointwise version for a named estimator that is definitionally or propositionally
equal to the local-inverse candidate on the given sample point.
-/
theorem vaart1998_theorem_4_1_moment_estimator_thetaHat_solves_on_local_range
    {Ω M Θ : Type*} (C : Vaart1998MomentLocalRangeCertificate M Θ)
    {empiricalMoment : ℕ -> Ω -> M} {thetaHat : ℕ -> Ω -> Θ}
    {n : ℕ} {ω : Ω}
    (hhat : thetaHat n ω = C.eInv (empiricalMoment n ω))
    (hmem : empiricalMoment n ω ∈ C.momentRange) :
    C.e (thetaHat n ω) = empiricalMoment n ω := by
  rw [hhat]
  exact vaart1998_theorem_4_1_moment_estimator_solves_on_local_range C hmem

/--
Uniqueness of the local moment-equation solution inside the supplied local
parameter domain.
-/
theorem vaart1998_theorem_4_1_moment_estimator_unique_on_parameterDomain
    {M Θ : Type*} (C : Vaart1998MomentLocalRangeCertificate M Θ)
    {m : M} {theta : Θ}
    (htheta : theta ∈ C.parameterDomain) (hsolve : C.e theta = m) :
    theta = C.eInv m := by
  have hleft := C.left_inverse_on_parameterDomain htheta
  rw [hsolve] at hleft
  exact hleft.symm

/--
The local-inverse candidate itself lies in the local parameter domain whenever
the empirical moment lies in the local range.
-/
theorem vaart1998_theorem_4_1_moment_estimator_mem_parameterDomain_on_local_range
    {Ω M Θ : Type*} (C : Vaart1998MomentLocalRangeCertificate M Θ)
    {empiricalMoment : ℕ -> Ω -> M} {n : ℕ} {ω : Ω}
    (hmem : empiricalMoment n ω ∈ C.momentRange) :
    C.eInv (empiricalMoment n ω) ∈ C.parameterDomain :=
  C.eInv_mem_parameterDomain hmem

/--
If empirical moments enter the local range with probability tending to one, then
the local-inverse candidate lies in the local parameter domain with probability
tending to one.
-/
theorem vaart1998_theorem_4_1_moment_estimator_mem_parameterDomain_with_probability_tending_to_one
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (C : Vaart1998MomentLocalRangeCertificate M Θ)
    {empiricalMoment : ℕ -> Ω -> M}
    (hprob : Tendsto (fun n : ℕ =>
      P.real {ω : Ω | empiricalMoment n ω ∈ C.momentRange}) atTop (𝓝 1)) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          C.eInv (empiricalMoment n ω) ∈ C.parameterDomain})
        atTop (𝓝 1) := by
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    hprob tendsto_const_nhds ?_ ?_
  · intro n
    refine measureReal_mono ?_
    intro ω hmem
    exact C.eInv_mem_parameterDomain hmem
  · intro n
    have hle :
        P.real
            {ω : Ω |
              C.eInv (empiricalMoment n ω) ∈ C.parameterDomain} ≤
          P.real Set.univ :=
      measureReal_mono (μ := P) (Set.subset_univ _)
    simpa using hle

/--
Certificate form of the Theorem 4.1 existence-localization sentence: empirical
moments fall in the local range with probability tending to one.
-/
theorem vaart1998_theorem_4_1_local_range_probability_of_certificate
    {Ω M : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    (C : Vaart1998MomentEstimatorLocalRangeProbabilityCertificate Ω M P) :
    Tendsto (fun n : ℕ =>
      P.real {ω : Ω | C.empiricalMoment n ω ∈ C.momentRange}) atTop (𝓝 1) :=
  C.localRange_probability

/--
If the local-range event has probability tending to one, then the local-inverse
candidate solves the moment equation with probability tending to one.
-/
theorem vaart1998_theorem_4_1_moment_equation_solved_with_probability_tending_to_one
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (C : Vaart1998MomentLocalRangeCertificate M Θ)
    {empiricalMoment : ℕ -> Ω -> M}
    (hprob : Tendsto (fun n : ℕ =>
      P.real {ω : Ω | empiricalMoment n ω ∈ C.momentRange}) atTop (𝓝 1)) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          C.e (C.eInv (empiricalMoment n ω)) = empiricalMoment n ω})
        atTop (𝓝 1) := by
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    hprob tendsto_const_nhds ?_ ?_
  · intro n
    refine measureReal_mono ?_
    intro ω hmem
    exact C.right_inverse_on_momentRange hmem
  · intro n
    have hle :
        P.real
            {ω : Ω |
              C.e (C.eInv (empiricalMoment n ω)) = empiricalMoment n ω} ≤
          P.real Set.univ :=
      measureReal_mono (μ := P) (Set.subset_univ _)
    simpa using hle

/--
Certificate form of the moment-equation solved-with-probability statement.
-/
theorem vaart1998_theorem_4_1_moment_equation_solved_with_probability_tending_to_one_of_certificate
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    (C : Vaart1998MomentLocalRangeCertificate M Θ)
    (Pcert : Vaart1998MomentEstimatorLocalRangeProbabilityCertificate Ω M P)
    (hRange : Pcert.momentRange = C.momentRange) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          C.e (C.eInv (Pcert.empiricalMoment n ω)) =
            Pcert.empiricalMoment n ω})
        atTop (𝓝 1) :=
  vaart1998_theorem_4_1_moment_equation_solved_with_probability_tending_to_one
    (C := C) (empiricalMoment := Pcert.empiricalMoment) <| by
      simpa [hRange] using Pcert.localRange_probability

/--
Finite-coordinate target-probability localization implies that the
inverse-function-theorem local-inverse candidate lies in the source
neighborhood with probability tending to one.
-/
theorem vaart1998_theorem_4_1_local_inverse_mem_parameterDomain_of_targetProbabilityLocalization_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) ∈
            (he.toOpenPartialHomeomorph e).source})
        atTop (𝓝 1) := by
  simpa [vaart1998_momentLocalRangeCertificate_of_hasStrictFDerivAt_openPartialHomeomorph,
    HasStrictFDerivAt.localInverse_def] using
    (vaart1998_theorem_4_1_moment_estimator_mem_parameterDomain_with_probability_tending_to_one
      (P := P)
      (C :=
        vaart1998_momentLocalRangeCertificate_of_hasStrictFDerivAt_openPartialHomeomorph
          e De he)
      (empiricalMoment := fun n : ℕ =>
        vaart1998_finiteCoordinateEmpiricalMoment X n)
      targetProbability.empiricalMoment_mem_target_probability)

/--
Finite-coordinate target-probability localization implies that the
inverse-function-theorem local-inverse candidate solves the empirical moment
equation with probability tending to one.
-/
theorem vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_targetProbabilityLocalization_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1) := by
  simpa [vaart1998_momentLocalRangeCertificate_of_hasStrictFDerivAt_openPartialHomeomorph,
    HasStrictFDerivAt.localInverse_def] using
    (vaart1998_theorem_4_1_moment_equation_solved_with_probability_tending_to_one
      (P := P)
      (C :=
        vaart1998_momentLocalRangeCertificate_of_hasStrictFDerivAt_openPartialHomeomorph
          e De he)
      (empiricalMoment := fun n : ℕ =>
        vaart1998_finiteCoordinateEmpiricalMoment X n)
      targetProbability.empiricalMoment_mem_target_probability)

/--
The inverse-function theorem plus convergence in probability of empirical
moments yields a moment-equation solution with probability tending to one.
-/
theorem vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_hasStrictFDerivAt_tendstoInMeasure
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    {empiricalMoment : ℕ -> Ω -> M}
    (hconv : TendstoInMeasure P empiricalMoment atTop (fun _ : Ω => e theta0))
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n)) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm (empiricalMoment n ω)) =
            empiricalMoment n ω})
        atTop (𝓝 1) := by
  let C :=
    vaart1998_momentLocalRangeCertificate_of_hasStrictFDerivAt_openPartialHomeomorph
      e De he
  have hprob :
      Tendsto (fun n : ℕ =>
        P.real {ω : Ω | empiricalMoment n ω ∈ C.momentRange}) atTop
          (𝓝 1) := by
    simpa [C] using
      vaart1998_theorem_4_1_open_local_range_probability_of_hasStrictFDerivAt
        e De he hconv hmeas
  simpa [C] using
    vaart1998_theorem_4_1_moment_equation_solved_with_probability_tending_to_one
      (C := C) (empiricalMoment := empiricalMoment) hprob

/--
The inverse-function theorem plus almost-sure empirical-moment convergence
yields a moment-equation solution with probability tending to one.
-/
theorem vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_hasStrictFDerivAt_ae_tendsto
    {Ω M Θ : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    {empiricalMoment : ℕ -> Ω -> M}
    (hstrong : ∀ n : ℕ, AEStronglyMeasurable (empiricalMoment n) P)
    (hmeas : ∀ n : ℕ, Measurable (empiricalMoment n))
    (hAE : ∀ᵐ ω ∂P,
      Tendsto (fun n : ℕ => empiricalMoment n ω) atTop (𝓝 (e theta0))) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm (empiricalMoment n ω)) =
            empiricalMoment n ω})
        atTop (𝓝 1) :=
  vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_hasStrictFDerivAt_tendstoInMeasure
    e De he
    (vaart1998_empiricalMoment_tendstoInMeasure_of_ae_tendsto_const
      hstrong hAE)
    hmeas

/--
Finite-coordinate strong-law version of the Theorem 4.1 local existence step.

For a finite real moment vector, coordinatewise iid strong laws feed the
inverse-function-theorem local range and imply that the local inverse candidate
solves the moment equation with probability tending to one.
-/
theorem vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_hasStrictFDerivAt_finiteCoordinateStrongLaw_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hstrong : ∀ n : ℕ,
      AEStronglyMeasurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) P)
    (hmeas : ∀ n : ℕ,
      Measurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n)) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1) :=
  vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_hasStrictFDerivAt_tendstoInMeasure
    e De he
    (by
      simpa [heta0] using
        vaart1998_finiteCoordinate_empiricalMoment_tendstoInMeasure_real
          X hX_integrable hX_indep hX_ident hstrong)
    hmeas

/--
van der Vaart 1998, Theorem 4.1, method-of-moments delta handoff.

This theorem is the compiled Chapter 4 proof spine: once the empirical moments
have a scaled distributional limit and the local inverse of the theoretical
moment map is differentiable and measurable, the moment estimator inherits the
linear image limit by Theorem 3.1.
-/
theorem vaart1998_theorem_4_1_moment_estimator_delta_method
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M}
    {eInv : M -> Θ} {eta0 : M} {theta0 : Θ} {r : ℕ -> ℝ}
    (Dinv : M →L[ℝ] Θ)
    (hInv_deriv : HasFDerivAt eInv Dinv eta0)
    (hInv_meas : Measurable eInv)
    (heta0 : eInv eta0 = theta0)
    (hr : Tendsto r atTop atTop)
    (hCLT : TendstoInDistribution
      (fun n ω => r n • (empiricalMoment n ω - eta0)) atTop Z (fun _ => P) Q)
    (hEmpiricalMoment : ∀ n, AEMeasurable (empiricalMoment n) P) :
    TendstoInDistribution
      (fun n ω => r n • (eInv (empiricalMoment n ω) - theta0)) atTop
      (fun ω => Dinv (Z ω)) (fun _ => P) Q := by
  simpa [heta0] using
    vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution_measurable
      (Tn := empiricalMoment) (T := Z) (phi := eInv) (theta := eta0)
      (r := r) (L := Dinv) hInv_deriv hInv_meas hr hCLT
      hEmpiricalMoment

/--
van der Vaart 1998, Theorem 4.1, method-of-moments delta handoff with
a.e.-measurability of the composed local inverse.

This is the version that can consume local-inverse measurability after the
empirical moment sequence has been localized in the inverse-function-theorem
moment range.
-/
theorem vaart1998_theorem_4_1_moment_estimator_delta_method_aemeasurable
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M}
    {eInv : M -> Θ} {eta0 : M} {theta0 : Θ} {r : ℕ -> ℝ}
    (Dinv : M →L[ℝ] Θ)
    (hInv_deriv : HasFDerivAt eInv Dinv eta0)
    (heta0 : eInv eta0 = theta0)
    (hr : Tendsto r atTop atTop)
    (hCLT : TendstoInDistribution
      (fun n ω => r n • (empiricalMoment n ω - eta0)) atTop Z (fun _ => P) Q)
    (hEmpiricalMoment : ∀ n, AEMeasurable (empiricalMoment n) P)
    (hInvEmpirical : ∀ n, AEMeasurable (fun ω => eInv (empiricalMoment n ω)) P) :
    TendstoInDistribution
      (fun n ω => r n • (eInv (empiricalMoment n ω) - theta0)) atTop
      (fun ω => Dinv (Z ω)) (fun _ => P) Q := by
  simpa [heta0] using
    vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution_aemeasurable
      (Tn := empiricalMoment) (T := Z) (phi := eInv) (theta := eta0)
      (r := r) (L := Dinv) hInv_deriv hr hCLT hEmpiricalMoment
      hInvEmpirical

/--
van der Vaart 1998, Theorem 4.1, method-of-moments `sqrt n` form.

This is the same Chapter 4 handoff with the textbook rate fixed to `sqrt n`.
-/
theorem vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M}
    {eInv : M -> Θ} {eta0 : M} {theta0 : Θ}
    (Dinv : M →L[ℝ] Θ)
    (hInv_deriv : HasFDerivAt eInv Dinv eta0)
    (hInv_meas : Measurable eInv)
    (heta0 : eInv eta0 = theta0)
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (empiricalMoment n ω - eta0)) atTop Z
        (fun _ => P) Q)
    (hEmpiricalMoment : ∀ n, AEMeasurable (empiricalMoment n) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)) atTop
      (fun ω => Dinv (Z ω)) (fun _ => P) Q :=
  vaart1998_theorem_4_1_moment_estimator_delta_method
    (empiricalMoment := empiricalMoment) (Z := Z) (eInv := eInv)
    (eta0 := eta0) (theta0 := theta0)
    (r := fun n : ℕ => √(n : ℝ)) (Dinv := Dinv)
    hInv_deriv hInv_meas heta0 vaart1998_sqrt_nat_tendsto_atTop
    hCLT hEmpiricalMoment

/--
Textbook `sqrt n` form of the Chapter 4.1 delta handoff with a.e.-measurability
of the composed local inverse.
-/
theorem vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_aemeasurable
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M}
    {eInv : M -> Θ} {eta0 : M} {theta0 : Θ}
    (Dinv : M →L[ℝ] Θ)
    (hInv_deriv : HasFDerivAt eInv Dinv eta0)
    (heta0 : eInv eta0 = theta0)
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (empiricalMoment n ω - eta0)) atTop Z
        (fun _ => P) Q)
    (hEmpiricalMoment : ∀ n, AEMeasurable (empiricalMoment n) P)
    (hInvEmpirical : ∀ n, AEMeasurable (fun ω => eInv (empiricalMoment n ω)) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)) atTop
      (fun ω => Dinv (Z ω)) (fun _ => P) Q :=
  vaart1998_theorem_4_1_moment_estimator_delta_method_aemeasurable
    (empiricalMoment := empiricalMoment) (Z := Z) (eInv := eInv)
    (eta0 := eta0) (theta0 := theta0)
    (r := fun n : ℕ => √(n : ℝ)) (Dinv := Dinv)
    hInv_deriv heta0 vaart1998_sqrt_nat_tendsto_atTop hCLT
    hEmpiricalMoment hInvEmpirical

/--
Textbook `sqrt n` delta-method handoff for any estimator that agrees with the
local-inverse candidate with probability tending to one.

This packages the usual asymptotic-equivalence step after the local inverse has
been used as a theorem-facing candidate.
-/
theorem vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_of_eq_with_probability_tending_to_one
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M}
    {eInv : M -> Θ} {eta0 : M} {theta0 : Θ}
    {thetaHat : ℕ -> Ω -> Θ}
    (Dinv : M →L[ℝ] Θ)
    (hInv_deriv : HasFDerivAt eInv Dinv eta0)
    (heta0 : eInv eta0 = theta0)
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (empiricalMoment n ω - eta0)) atTop Z
        (fun _ => P) Q)
    (hEmpiricalMoment : ∀ n, AEMeasurable (empiricalMoment n) P)
    (hInvEmpirical : ∀ n, AEMeasurable (fun ω => eInv (empiricalMoment n ω)) P)
    (hThetaHat : ∀ n, AEMeasurable (thetaHat n) P)
    (hScaledEq_meas : ∀ n : ℕ,
      MeasurableSet
        {ω : Ω |
          √(n : ℝ) • (thetaHat n ω - theta0) =
            √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)})
    (hEq_prob : Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω | thetaHat n ω = eInv (empiricalMoment n ω)})
      atTop (𝓝 1)) :
    TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (thetaHat n ω - theta0)) atTop
      (fun ω => Dinv (Z ω)) (fun _ => P) Q := by
  have hCandidate :
      TendstoInDistribution
        (fun (n : ℕ) ω =>
          √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)) atTop
        (fun ω => Dinv (Z ω)) (fun _ => P) Q :=
    vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_aemeasurable
      (empiricalMoment := empiricalMoment) (Z := Z) (eInv := eInv)
      (eta0 := eta0) (theta0 := theta0) (Dinv := Dinv)
      hInv_deriv heta0 hCLT hEmpiricalMoment hInvEmpirical
  have hScaledEq_prob :
      Tendsto (fun n : ℕ =>
        P.real
          {ω : Ω |
            √(n : ℝ) • (thetaHat n ω - theta0) =
              √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)})
        atTop (𝓝 1) := by
    refine tendsto_of_tendsto_of_tendsto_of_le_of_le
      hEq_prob tendsto_const_nhds ?_ ?_
    · intro n
      refine measureReal_mono ?_
      intro ω hω
      have hEq : thetaHat n ω = eInv (empiricalMoment n ω) := hω
      simp [hEq]
    · intro n
      have hle :
          P.real
              {ω : Ω |
                √(n : ℝ) • (thetaHat n ω - theta0) =
                  √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)} ≤
            P.real Set.univ :=
        measureReal_mono (μ := P) (Set.subset_univ _)
      simpa using hle
  have hDiff_meas : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          √(n : ℝ) • (thetaHat n ω - theta0) -
            √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)) P := by
    intro n
    exact
      (((hThetaHat n).sub aemeasurable_const).const_smul (√(n : ℝ))).sub
        (((hInvEmpirical n).sub aemeasurable_const).const_smul (√(n : ℝ)))
  exact
    vaart1998_tendstoInDistribution_of_eq_with_probability_tending_to_one
      (P := P) (Q := Q)
      (X := fun (n : ℕ) ω => √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0))
      (Y := fun (n : ℕ) ω => √(n : ℝ) • (thetaHat n ω - theta0))
      (Z := fun ω => Dinv (Z ω))
      hCandidate hScaledEq_meas hScaledEq_prob hDiff_meas

/--
Textbook `sqrt n` delta-method handoff for an estimator that agrees with the
local-inverse candidate on a high-probability event.

This is the source-facing version of the asymptotic-equivalence wrapper: later
existence or measurable-selection work only has to produce a good event whose
probability tends to one and on which the selected estimator equals the local
inverse.
-/
theorem vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_of_eq_on_event_with_probability_tending_to_one
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M}
    {eInv : M -> Θ} {eta0 : M} {theta0 : Θ}
    {thetaHat : ℕ -> Ω -> Θ} {good : ℕ -> Set Ω}
    (Dinv : M →L[ℝ] Θ)
    (hInv_deriv : HasFDerivAt eInv Dinv eta0)
    (hInv_meas : Measurable eInv)
    (heta0 : eInv eta0 = theta0)
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (empiricalMoment n ω - eta0)) atTop Z
        (fun _ => P) Q)
    (hEmpiricalMoment_meas : ∀ n, Measurable (empiricalMoment n))
    (hThetaHat_meas : ∀ n, Measurable (thetaHat n))
    (hGood_prob : Tendsto (fun n : ℕ => P.real (good n)) atTop (𝓝 1))
    (hGood_subset : ∀ n : ℕ,
      good n ⊆ {ω : Ω | thetaHat n ω = eInv (empiricalMoment n ω)}) :
    TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (thetaHat n ω - theta0)) atTop
      (fun ω => Dinv (Z ω)) (fun _ => P) Q := by
  have hInvEmpirical : ∀ n : ℕ,
      AEMeasurable (fun ω : Ω => eInv (empiricalMoment n ω)) P := by
    intro n
    exact (hInv_meas.comp (hEmpiricalMoment_meas n)).aemeasurable
  have hScaledEq_meas : ∀ n : ℕ,
      MeasurableSet
        {ω : Ω |
          √(n : ℝ) • (thetaHat n ω - theta0) =
            √(n : ℝ) • (eInv (empiricalMoment n ω) - theta0)} := by
    intro n
    refine measurableSet_eq_fun ?_ ?_
    · exact
        (((hThetaHat_meas n).sub measurable_const).const_smul (√(n : ℝ)))
    · exact
        ((((hInv_meas.comp (hEmpiricalMoment_meas n)).sub measurable_const).const_smul
          (√(n : ℝ))))
  have hEq_prob :
      Tendsto (fun n : ℕ =>
        P.real {ω : Ω | thetaHat n ω = eInv (empiricalMoment n ω)})
        atTop (𝓝 1) :=
    vaart1998_probability_tending_to_one_of_subset hGood_prob hGood_subset
  exact
    vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_of_eq_with_probability_tending_to_one
      (P := P) (Q := Q) (empiricalMoment := empiricalMoment) (Z := Z)
      (eInv := eInv) (eta0 := eta0) (theta0 := theta0)
      (thetaHat := thetaHat) (Dinv := Dinv) hInv_deriv heta0 hCLT
      (fun n => (hEmpiricalMoment_meas n).aemeasurable) hInvEmpirical
      (fun n => (hThetaHat_meas n).aemeasurable) hScaledEq_meas hEq_prob

/--
Certificate form of van der Vaart Theorem 4.1's delta-method step.
-/
theorem vaart1998_theorem_4_1_moment_estimator_delta_method_of_certificate
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (C : Vaart1998MomentLocalInverseCertificate M Θ)
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M} {r : ℕ -> ℝ}
    (hr : Tendsto r atTop atTop)
    (hCLT : TendstoInDistribution
      (fun n ω => r n • (empiricalMoment n ω - C.eta0)) atTop Z
        (fun _ => P) Q)
    (hEmpiricalMoment : ∀ n, AEMeasurable (empiricalMoment n) P) :
    TendstoInDistribution
      (fun n ω => r n • (C.eInv (empiricalMoment n ω) - C.theta0)) atTop
      (fun ω => C.Dinv (Z ω)) (fun _ => P) Q :=
  vaart1998_theorem_4_1_moment_estimator_delta_method
    (empiricalMoment := empiricalMoment) (Z := Z) (eInv := C.eInv)
    (eta0 := C.eta0) (theta0 := C.theta0) (r := r) (Dinv := C.Dinv)
    C.inverse_deriv C.inverse_measurable C.inverse_at_eta0 hr hCLT
    hEmpiricalMoment

/--
Textbook `sqrt n` certificate form of Theorem 4.1's delta-method step.
-/
theorem vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_of_certificate
    {Ω : Type u} {Ω' : Type v} {M : Type w} {Θ : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [SecondCountableTopology M] [BorelSpace M]
    [OpensMeasurableSpace M] [CompleteSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (C : Vaart1998MomentLocalInverseCertificate M Θ)
    {empiricalMoment : ℕ -> Ω -> M} {Z : Ω' -> M}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (empiricalMoment n ω - C.eta0))
        atTop Z (fun _ => P) Q)
    (hEmpiricalMoment : ∀ n, AEMeasurable (empiricalMoment n) P) :
    TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (C.eInv (empiricalMoment n ω) - C.theta0))
        atTop (fun ω => C.Dinv (Z ω)) (fun _ => P) Q :=
  vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method
    (empiricalMoment := empiricalMoment) (Z := Z) (eInv := C.eInv)
    (eta0 := C.eta0) (theta0 := C.theta0) (Dinv := C.Dinv)
    C.inverse_deriv C.inverse_measurable C.inverse_at_eta0 hCLT
    hEmpiricalMoment

/--
Gaussian limits are preserved by the linear inverse-derivative map appearing
in van der Vaart Theorem 4.1.
-/
theorem vaart1998_theorem_4_1_gaussian_limit_of_linear_inverse_derivative
    {Ω' M Θ : Type*} [MeasurableSpace Ω'] {Q : Measure Ω'}
    [NormedAddCommGroup M] [NormedSpace ℝ M] [MeasurableSpace M]
    [BorelSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [MeasurableSpace Θ]
    [BorelSpace Θ]
    {Z : Ω' -> M} (Dinv : M →L[ℝ] Θ) (hZ : HasGaussianLaw Z Q) :
    HasGaussianLaw (fun ω => Dinv (Z ω)) Q :=
  hZ.map_fun Dinv

/--
Covariance functional of a vector-valued limit, tested against continuous
linear coordinates.

For finite-dimensional Euclidean coordinates this is the coordinate-free
version of the covariance matrix.
-/
noncomputable def vaart1998_limitCovarianceFunctional
    {Ω' E : Type*} [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Z : Ω' -> E) (Q : Measure Ω') :
    StrongDual ℝ E -> StrongDual ℝ E -> ℝ :=
  fun L K =>
    ProbabilityTheory.covariance (fun ω => L (Z ω)) (fun ω => K (Z ω)) Q

/--
The covariance functional obtained after applying the inverse derivative.

This is the coordinate-free form of the textbook covariance display
`Dinv * Sigma * Dinv^T`.
-/
noncomputable def vaart1998_inverseDerivativeCovarianceFunctional
    {M Θ : Type*} [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    (Dinv : M →L[ℝ] Θ)
    (Sigma : StrongDual ℝ M -> StrongDual ℝ M -> ℝ) :
    StrongDual ℝ Θ -> StrongDual ℝ Θ -> ℝ :=
  fun L K => Sigma (L.comp Dinv) (K.comp Dinv)

/--
Applying the inverse derivative pulls back covariance functionals by
precomposition of continuous linear coordinates.
-/
theorem vaart1998_limitCovarianceFunctional_inverseDerivative_apply
    {Ω' M Θ : Type*} [MeasurableSpace Ω']
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    (Z : Ω' -> M) (Q : Measure Ω') (Dinv : M →L[ℝ] Θ)
    (L K : StrongDual ℝ Θ) :
    vaart1998_limitCovarianceFunctional (fun ω => Dinv (Z ω)) Q L K =
      vaart1998_inverseDerivativeCovarianceFunctional Dinv
        (vaart1998_limitCovarianceFunctional Z Q) L K := by
  rfl

/--
When the limit has a square-integrable law, the coordinate covariance
functional is mathlib's covariance bilinear form of that law.
-/
theorem vaart1998_limitCovarianceFunctional_eq_covarianceBilinDual_map
    {Ω' E : Type*} [MeasurableSpace Ω'] [MeasurableSpace E]
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    [BorelSpace E] {Q : Measure Ω'} [IsFiniteMeasure Q]
    (Z : Ω' -> E) (hZ : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) (L K : StrongDual ℝ E) :
    vaart1998_limitCovarianceFunctional Z Q L K =
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L K := by
  rw [ProbabilityTheory.covarianceBilinDual_eq_covariance hZ_memLp L K,
    ProbabilityTheory.covariance_map_fun (by fun_prop) (by fun_prop) hZ]
  rfl

/--
The covariance bilinear form of the inverse-derivative pushed law is the
pullback of the covariance bilinear form of the original law.
-/
theorem vaart1998_covarianceBilinDual_inverseDerivative_map_apply
    {Ω' M Θ : Type*} [MeasurableSpace Ω']
    [MeasurableSpace M] [NormedAddCommGroup M] [NormedSpace ℝ M]
    [CompleteSpace M] [BorelSpace M]
    [MeasurableSpace Θ] [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [CompleteSpace Θ] [BorelSpace Θ]
    {Q : Measure Ω'} [IsFiniteMeasure Q]
    (Z : Ω' -> M) (Dinv : M →L[ℝ] Θ)
    (hZ : AEMeasurable Z Q)
    (hDinvZ : AEMeasurable (fun ω => Dinv (Z ω)) Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hDinvZ_memLp : MemLp id 2 (Q.map fun ω => Dinv (Z ω)))
    (L K : StrongDual ℝ Θ) :
    ProbabilityTheory.covarianceBilinDual (Q.map fun ω => Dinv (Z ω)) L K =
      vaart1998_inverseDerivativeCovarianceFunctional Dinv
        (fun L0 K0 => ProbabilityTheory.covarianceBilinDual (Q.map Z) L0 K0) L K := by
  rw [ProbabilityTheory.covarianceBilinDual_eq_covariance hDinvZ_memLp L K,
    ProbabilityTheory.covariance_map_fun (by fun_prop) (by fun_prop) hDinvZ]
  dsimp [vaart1998_inverseDerivativeCovarianceFunctional]
  rw [ProbabilityTheory.covarianceBilinDual_eq_covariance hZ_memLp (L.comp Dinv) (K.comp Dinv),
    ProbabilityTheory.covariance_map_fun (by fun_prop) (by fun_prop) hZ]
  rfl

/--
Continuous linear inverse derivatives preserve a.e. measurability of the
limit variable.
-/
theorem vaart1998_inverseDerivative_aemeasurable_of_aemeasurable
    {Ω' M Θ : Type*} [MeasurableSpace Ω']
    [MeasurableSpace M] [NormedAddCommGroup M] [NormedSpace ℝ M]
    [BorelSpace M]
    [MeasurableSpace Θ] [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [BorelSpace Θ]
    {Q : Measure Ω'} (Z : Ω' -> M) (Dinv : M →L[ℝ] Θ)
    (hZ : AEMeasurable Z Q) :
    AEMeasurable (fun ω => Dinv (Z ω)) Q :=
  Dinv.continuous.aemeasurable.comp_aemeasurable hZ

/--
Continuous linear inverse derivatives preserve square-integrability of the
limit law.
-/
theorem vaart1998_inverseDerivative_map_memLp_of_memLp
    {Ω' M Θ : Type*} [MeasurableSpace Ω']
    [MeasurableSpace M] [NormedAddCommGroup M] [NormedSpace ℝ M]
    [BorelSpace M]
    [MeasurableSpace Θ] [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [SecondCountableTopology Θ] [BorelSpace Θ]
    {Q : Measure Ω'} (Z : Ω' -> M) (Dinv : M →L[ℝ] Θ)
    (hZ : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) :
    MemLp id 2 (Q.map fun ω => Dinv (Z ω)) := by
  have hDinvZ : AEMeasurable (fun ω => Dinv (Z ω)) Q :=
    vaart1998_inverseDerivative_aemeasurable_of_aemeasurable Z Dinv hZ
  rw [MeasureTheory.memLp_map_measure_iff aestronglyMeasurable_id hDinvZ]
  have hZ_memLp_Q : MemLp Z 2 Q := by
    simpa [Function.comp_def] using hZ_memLp.comp_of_map hZ
  simpa [Function.comp_def] using hZ_memLp_Q.continuousLinearMap_comp Dinv

/--
The inverse-derivative covarianceBilinDual pullback using only the original
square-integrable law hypothesis.
-/
theorem vaart1998_covarianceBilinDual_inverseDerivative_map_apply_of_memLp
    {Ω' M Θ : Type*} [MeasurableSpace Ω']
    [MeasurableSpace M] [NormedAddCommGroup M] [NormedSpace ℝ M]
    [CompleteSpace M] [BorelSpace M]
    [MeasurableSpace Θ] [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [CompleteSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    {Q : Measure Ω'} [IsFiniteMeasure Q]
    (Z : Ω' -> M) (Dinv : M →L[ℝ] Θ)
    (hZ : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (L K : StrongDual ℝ Θ) :
    ProbabilityTheory.covarianceBilinDual (Q.map fun ω => Dinv (Z ω)) L K =
      vaart1998_inverseDerivativeCovarianceFunctional Dinv
        (fun L0 K0 => ProbabilityTheory.covarianceBilinDual (Q.map Z) L0 K0) L K := by
  exact vaart1998_covarianceBilinDual_inverseDerivative_map_apply Z Dinv hZ
    (vaart1998_inverseDerivative_aemeasurable_of_aemeasurable Z Dinv hZ)
    hZ_memLp
    (vaart1998_inverseDerivative_map_memLp_of_memLp Z Dinv hZ hZ_memLp)
    L K

/--
Finite-indexed covariance table obtained by testing a covariance functional
against a chosen finite family of continuous linear coordinates.
-/
noncomputable def vaart1998_covarianceTable
    {I E : Type*} [Fintype I]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (coordinates : I -> StrongDual ℝ E)
    (Sigma : StrongDual ℝ E -> StrongDual ℝ E -> ℝ) :
    I -> I -> ℝ :=
  fun i j => Sigma (coordinates i) (coordinates j)

/--
The inverse-derivative covariance table is obtained by precomposing each
chosen coordinate with the inverse derivative.
-/
theorem vaart1998_inverseDerivativeCovarianceTable_apply
    {I M Θ : Type*} [Fintype I]
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    (Dinv : M →L[ℝ] Θ)
    (Sigma : StrongDual ℝ M -> StrongDual ℝ M -> ℝ)
    (coordinates : I -> StrongDual ℝ Θ) (i j : I) :
    vaart1998_covarianceTable coordinates
        (vaart1998_inverseDerivativeCovarianceFunctional Dinv Sigma) i j =
      vaart1998_covarianceTable
        (fun k => (coordinates k).comp Dinv) Sigma i j := by
  rfl

/--
Finite-indexed covarianceBilinDual version of Vaart's covariance display
`Dinv * Sigma * Dinv^T`.
-/
theorem vaart1998_covarianceBilinDual_inverseDerivative_table_apply_of_memLp
    {I Ω' M Θ : Type*} [Fintype I] [MeasurableSpace Ω']
    [MeasurableSpace M] [NormedAddCommGroup M] [NormedSpace ℝ M]
    [CompleteSpace M] [BorelSpace M]
    [MeasurableSpace Θ] [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [CompleteSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    {Q : Measure Ω'} [IsFiniteMeasure Q]
    (Z : Ω' -> M) (Dinv : M →L[ℝ] Θ)
    (coordinates : I -> StrongDual ℝ Θ)
    (hZ : AEMeasurable Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) (i j : I) :
    vaart1998_covarianceTable coordinates
        (fun L K =>
          ProbabilityTheory.covarianceBilinDual
            (Q.map fun ω => Dinv (Z ω)) L K) i j =
      vaart1998_covarianceTable
        (fun k => (coordinates k).comp Dinv)
        (fun L K => ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j := by
  simpa [vaart1998_covarianceTable] using
    vaart1998_covarianceBilinDual_inverseDerivative_map_apply_of_memLp
      Z Dinv hZ hZ_memLp (coordinates i) (coordinates j)

/--
The continuous linear coordinate evaluation functional on a finite real vector.
-/
noncomputable def vaart1998_finiteCoordinateEvalCLM
    {Coordinate : Type*} (coordinate : Coordinate) :
    StrongDual ℝ (Coordinate -> ℝ) :=
  ContinuousLinearMap.proj coordinate

@[simp]
theorem vaart1998_finiteCoordinateEvalCLM_apply
    {Coordinate : Type*} (coordinate : Coordinate) (x : Coordinate -> ℝ) :
    vaart1998_finiteCoordinateEvalCLM coordinate x = x coordinate := by
  rfl

/--
Coordinate-indexed covariance table of a finite real vector law.
-/
noncomputable def vaart1998_finiteCoordinateCovarianceTable
    {Coordinate : Type*} [Fintype Coordinate]
    (Sigma :
      StrongDual ℝ (Coordinate -> ℝ) ->
        StrongDual ℝ (Coordinate -> ℝ) -> ℝ) :
    Coordinate -> Coordinate -> ℝ :=
  vaart1998_covarianceTable
    (fun coordinate => vaart1998_finiteCoordinateEvalCLM coordinate) Sigma

/--
Finite-coordinate source-shaped form of van der Vaart Theorem 4.1.

For finitely many real moment coordinates, coordinatewise iid strong laws give
the existence/local-solving statement, while a supplied empirical-moment CLT
and the inverse-function-theorem local inverse give the `sqrt n` asymptotic
distribution by the Chapter 3 delta method.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateStrongLaw_sqrt_exists_and_delta_method_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hstrong : ∀ n : ℕ,
      AEStronglyMeasurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) P)
    (hmeas : ∀ n : ℕ,
      Measurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n))
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q := by
  constructor
  · exact
      vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_hasStrictFDerivAt_finiteCoordinateStrongLaw_real
        e De he X heta0 hX_integrable hX_indep hX_ident hstrong hmeas
  · let C :=
      vaart1998_momentLocalInverseCertificate_of_hasStrictFDerivAt
        e De he hInv_meas
    simpa [C] using
      vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_of_certificate
        (C := C)
        (empiricalMoment := fun n : ℕ => fun ω : Ω =>
          fun coordinate : Coordinate =>
            (∑ i ∈ Finset.range n, X coordinate i ω) / n)
        (Z := Z) hCLT (fun n => (hstrong n).aemeasurable)

/--
Finite-coordinate source-shaped Theorem 4.1 wrapper using only
a.e.-measurability of the composed local inverse.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateStrongLaw_sqrt_exists_and_delta_method_aemeasurable_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hstrong : ∀ n : ℕ,
      AEStronglyMeasurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) P)
    (hmeas : ∀ n : ℕ,
      Measurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)) P)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q := by
  constructor
  · exact
      vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_hasStrictFDerivAt_finiteCoordinateStrongLaw_real
        e De he X heta0 hX_integrable hX_indep hX_ident hstrong hmeas
  · simpa using
      vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_aemeasurable
        (empiricalMoment := fun n : ℕ => fun ω : Ω =>
          fun coordinate : Coordinate =>
            (∑ i ∈ Finset.range n, X coordinate i ω) / n)
        (Z := Z) (eInv := he.localInverse e De theta0)
        (eta0 := e theta0) (theta0 := theta0)
        (Dinv := (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
        he.to_localInverse.hasFDerivAt he.localInverse_apply_image hCLT
        (fun n => (hstrong n).aemeasurable) hInvEmpirical

/--
Finite-coordinate source-shaped Theorem 4.1 wrapper deriving composed
local-inverse a.e.-measurability from a.e. localization in the open moment
range.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateStrongLaw_sqrt_exists_and_delta_method_of_ae_mem_open_momentRange_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hstrong : ∀ n : ℕ,
      AEStronglyMeasurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) P)
    (hmeas : ∀ n : ℕ,
      Measurable
        (fun ω : Ω => fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        (fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) ∈
            (he.toOpenPartialHomeomorph e).target)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q :=
  vaart1998_theorem_4_1_finiteCoordinateStrongLaw_sqrt_exists_and_delta_method_aemeasurable_real
    e De he X heta0 hX_integrable hX_indep hX_ident hstrong hmeas
    (fun n =>
      vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange
        e De he (hstrong n).aemeasurable (hTarget n))
    hCLT

/--
Finite-coordinate Theorem 4.1 wrapper with empirical-moment measurability
derived from coordinate measurability.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_delta_method_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q :=
  vaart1998_theorem_4_1_finiteCoordinateStrongLaw_sqrt_exists_and_delta_method_real
    e De he hInv_meas X heta0 hX_integrable hX_indep hX_ident
    (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
      X hX_meas)
    (vaart1998_finiteCoordinate_empiricalMoment_measurable_real X hX_meas)
    hCLT

/--
Measurable-coordinate Theorem 4.1 wrapper using only a.e.-measurability of the
composed local inverse.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_delta_method_aemeasurable_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)) P)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q :=
  vaart1998_theorem_4_1_finiteCoordinateStrongLaw_sqrt_exists_and_delta_method_aemeasurable_real
    e De he X heta0 hX_integrable hX_indep hX_ident
    (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
      X hX_meas)
    (vaart1998_finiteCoordinate_empiricalMoment_measurable_real X hX_meas)
    hInvEmpirical hCLT

/--
Finite-coordinate Theorem 4.1 wrapper for an explicit estimator that agrees
with the local-inverse candidate with probability tending to one.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_estimator_delta_method_of_eq_with_probability_tending_to_one_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)) P)
    {thetaHat : ℕ -> Ω -> Θ}
    (hThetaHat : ∀ n : ℕ, AEMeasurable (thetaHat n) P)
    (hScaledEq_meas : ∀ n : ℕ,
      MeasurableSet
        {ω : Ω |
          √(n : ℝ) • (thetaHat n ω - theta0) =
            √(n : ℝ) •
              (he.localInverse e De theta0
                (fun coordinate : Coordinate =>
                  (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0)})
    (hEq_prob : Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          thetaHat n ω =
            he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
      atTop (𝓝 1))
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (thetaHat n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_delta_method_aemeasurable_real
      e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
      hInvEmpirical hCLT
  refine ⟨hbase.1, ?_⟩
  exact
    vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_of_eq_with_probability_tending_to_one
      (P := P) (Q := Q)
      (empiricalMoment := fun n : ℕ =>
        vaart1998_finiteCoordinateEmpiricalMoment X n)
      (Z := Z) (eInv := he.localInverse e De theta0)
      (eta0 := e theta0) (theta0 := theta0) (thetaHat := thetaHat)
      (Dinv := (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
      he.to_localInverse.hasFDerivAt he.localInverse_apply_image
      (by
        simpa [vaart1998_finiteCoordinateEmpiricalMoment] using hCLT)
      (fun n =>
        (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
          X hX_meas n).aemeasurable)
      (fun n => by
        simpa [vaart1998_finiteCoordinateEmpiricalMoment] using hInvEmpirical n)
      hThetaHat
      (fun n => by
        simpa [vaart1998_finiteCoordinateEmpiricalMoment] using hScaledEq_meas n)
      (by
        simpa [vaart1998_finiteCoordinateEmpiricalMoment] using hEq_prob)

/--
Finite-coordinate Theorem 4.1 wrapper for a selected estimator that agrees with
the local-inverse candidate on the inverse-function-theorem target event.

The target-localization certificate is the source-shaped "existence with
probability tending to one" field from van der Vaart's proof.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_estimator_delta_method_of_targetProbabilityLocalization_eq_on_target_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X)
    {thetaHat : ℕ -> Ω -> Θ}
    (hThetaHat_meas : ∀ n : ℕ, Measurable (thetaHat n))
    (hThetaHat_eq_on_target : ∀ n : ℕ, ∀ ⦃ω : Ω⦄,
      vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target ->
        thetaHat n ω =
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment X n ω))
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω => √(n : ℝ) • (thetaHat n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q := by
  refine ⟨?_, ?_⟩
  · exact
      vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_targetProbabilityLocalization_real
        e De he X targetProbability
  · exact
      vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method_of_eq_on_event_with_probability_tending_to_one
        (P := P) (Q := Q)
        (empiricalMoment := fun n : ℕ =>
          vaart1998_finiteCoordinateEmpiricalMoment X n)
        (Z := Z) (eInv := he.localInverse e De theta0)
        (eta0 := e theta0) (theta0 := theta0) (thetaHat := thetaHat)
        (good := fun n : ℕ =>
          {ω : Ω |
            vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
              (he.toOpenPartialHomeomorph e).target})
        (Dinv := (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
        he.to_localInverse.hasFDerivAt hInv_meas he.localInverse_apply_image
        (by
          simpa [vaart1998_finiteCoordinateEmpiricalMoment] using hCLT)
        (fun n => vaart1998_finiteCoordinate_empiricalMoment_measurable_real
          X hX_meas n)
        hThetaHat_meas
        targetProbability.empiricalMoment_mem_target_probability
        (fun n => by
          intro ω hω
          exact hThetaHat_eq_on_target n hω)

/--
Moment-space fallback extension of the inverse-function-theorem local inverse:
use the local inverse on the target and a fixed fallback outside it.
-/
noncomputable def vaart1998_localInverseFallbackExtension
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (fallback : Θ) : M -> Θ :=
  by
    classical
    exact
      (he.toOpenPartialHomeomorph e).target.piecewise
        (he.localInverse e De theta0) (fun _ => fallback)

/--
The local-inverse fallback extension is measurable without assuming global
measurability of `he.localInverse e De theta0`.
-/
theorem vaart1998_localInverseFallbackExtension_measurable
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (fallback : Θ) :
    Measurable (vaart1998_localInverseFallbackExtension e De he fallback) := by
  classical
  have hlocal :
      ContinuousOn (he.localInverse e De theta0)
        (he.toOpenPartialHomeomorph e).target := by
    simpa [HasStrictFDerivAt.localInverse_def] using
      (he.toOpenPartialHomeomorph e).continuousOn_symm
  have hfallback :
      ContinuousOn (fun _ : M => fallback)
        ((he.toOpenPartialHomeomorph e).target)ᶜ :=
    continuous_const.continuousOn
  simpa [vaart1998_localInverseFallbackExtension] using
    hlocal.measurable_piecewise hfallback
      (he.toOpenPartialHomeomorph e).open_target.measurableSet

/--
Near the true moment, the fallback extension equals the local inverse, so it has
the same derivative.
-/
theorem vaart1998_localInverseFallbackExtension_hasFDerivAt
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [MeasurableSpace M] [OpensMeasurableSpace M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [BorelSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (fallback : Θ) :
    HasFDerivAt (vaart1998_localInverseFallbackExtension e De he fallback)
      (De.symm : M →L[ℝ] Θ) (e theta0) := by
  classical
  have hevent :
      vaart1998_localInverseFallbackExtension e De he fallback
        =ᶠ[𝓝 (e theta0)] he.localInverse e De theta0 := by
    filter_upwards
      [(he.toOpenPartialHomeomorph e).open_target.eventually_mem
        he.image_mem_toOpenPartialHomeomorph_target] with m hm
    simp [vaart1998_localInverseFallbackExtension, hm]
  exact he.to_localInverse.hasFDerivAt.congr_of_eventuallyEq hevent

/--
The fallback extension sends the true moment to the true parameter.
-/
theorem vaart1998_localInverseFallbackExtension_apply_true_moment
    {M Θ : Type*}
    [NormedAddCommGroup M] [NormedSpace ℝ M]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> M) {theta0 : Θ} (De : Θ ≃L[ℝ] M)
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] M) theta0)
    (fallback : Θ) :
    vaart1998_localInverseFallbackExtension e De he fallback (e theta0) =
      theta0 := by
  classical
  simp [vaart1998_localInverseFallbackExtension,
    he.image_mem_toOpenPartialHomeomorph_target]

/--
Selected finite-coordinate moment estimator: use the local inverse on the
inverse-function-theorem target event and a fixed fallback outside the event.
-/
noncomputable def vaart1998_finiteCoordinateLocalInverseSelectedEstimator
    {Coordinate Ω Θ : Type*} [Fintype Coordinate]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) (fallback : Θ) (n : ℕ) (ω : Ω) :
    Θ :=
  by
    classical
    exact
      if vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target then
        he.localInverse e De theta0 (vaart1998_finiteCoordinateEmpiricalMoment X n ω)
      else
        fallback

/--
The selected finite-coordinate local-inverse estimator is measurable whenever
the coordinates are measurable.  The local inverse is used through its
measurable fallback extension on moment space.
-/
theorem vaart1998_finiteCoordinateLocalInverseSelectedEstimator_measurable_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (fallback : Θ) :
    ∀ n : ℕ,
      Measurable
        (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
          e De he X fallback n) := by
  intro n
  classical
  simpa [vaart1998_finiteCoordinateLocalInverseSelectedEstimator,
    vaart1998_localInverseFallbackExtension] using
      (vaart1998_localInverseFallbackExtension_measurable e De he fallback).comp
        (vaart1998_finiteCoordinate_empiricalMoment_measurable_real
          X hX_meas n)

/--
On the target event, the selected finite-coordinate estimator is exactly the
local-inverse candidate.
-/
theorem vaart1998_finiteCoordinateLocalInverseSelectedEstimator_eq_on_target_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) (fallback : Θ) :
    ∀ n : ℕ, ∀ ⦃ω : Ω⦄,
      vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target ->
        vaart1998_finiteCoordinateLocalInverseSelectedEstimator
            e De he X fallback n ω =
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment X n ω) := by
  intro n ω htarget
  simp [vaart1998_finiteCoordinateLocalInverseSelectedEstimator, htarget]

/--
The canonical selected estimator lies in the inverse-function-theorem source
with probability tending to one.
-/
theorem vaart1998_finiteCoordinateLocalInverseSelectedEstimator_mem_source_of_targetProbabilityLocalization_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) (fallback : Θ)
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω ∈
            (he.toOpenPartialHomeomorph e).source})
        atTop (𝓝 1) :=
  vaart1998_probability_tending_to_one_of_subset
    targetProbability.empiricalMoment_mem_target_probability
    (fun n => by
      intro ω htarget
      have hEq :=
        vaart1998_finiteCoordinateLocalInverseSelectedEstimator_eq_on_target_real
          e De he X fallback n htarget
      have hmem :
          he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) ∈
            (he.toOpenPartialHomeomorph e).source := by
        simpa [HasStrictFDerivAt.localInverse_def] using
          (he.toOpenPartialHomeomorph e).map_target htarget
      simpa [hEq] using hmem)

/--
The canonical selected estimator solves the empirical moment equation with
probability tending to one.
-/
theorem vaart1998_finiteCoordinateLocalInverseSelectedEstimator_solves_momentEquation_with_probability_of_targetProbabilityLocalization_real
    {Coordinate Ω Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) (fallback : Θ)
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X) :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1) :=
  vaart1998_probability_tending_to_one_of_subset
    targetProbability.empiricalMoment_mem_target_probability
    (fun n => by
      intro ω htarget
      have hEq :=
        vaart1998_finiteCoordinateLocalInverseSelectedEstimator_eq_on_target_real
          e De he X fallback n htarget
      have hsolve :
          e (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω := by
        simpa [HasStrictFDerivAt.localInverse_def] using
          (he.toOpenPartialHomeomorph e).right_inv htarget
      simpa [hEq] using hsolve)

/--
Finite-coordinate Theorem 4.1 endpoint for the canonical selected estimator
with a fixed fallback outside the inverse-function-theorem target event.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_selectedEstimator_delta_method_of_targetProbabilityLocalization_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X)
    (fallback : Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q :=
  by
    refine ⟨?_, ?_⟩
    · exact
        vaart1998_theorem_4_1_moment_equation_solved_with_probability_of_targetProbabilityLocalization_real
          e De he X targetProbability
    · have hdist :
          TendstoInDistribution
            (fun (n : ℕ) ω =>
              √(n : ℝ) •
                (vaart1998_localInverseFallbackExtension e De he fallback
                    (vaart1998_finiteCoordinateEmpiricalMoment X n ω) -
                  theta0))
            atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
            (fun _ => P) Q :=
        vaart1998_theorem_4_1_moment_estimator_sqrt_delta_method
          (P := P) (Q := Q)
          (empiricalMoment := fun n : ℕ =>
            vaart1998_finiteCoordinateEmpiricalMoment X n)
          (Z := Z)
          (eInv := vaart1998_localInverseFallbackExtension e De he fallback)
          (eta0 := e theta0) (theta0 := theta0)
          (Dinv := (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (vaart1998_localInverseFallbackExtension_hasFDerivAt e De he fallback)
          (vaart1998_localInverseFallbackExtension_measurable e De he fallback)
          (vaart1998_localInverseFallbackExtension_apply_true_moment e De he fallback)
          (by
            simpa [vaart1998_finiteCoordinateEmpiricalMoment] using hCLT)
          (fun n =>
            (vaart1998_finiteCoordinate_empiricalMoment_measurable_real
              X hX_meas n).aemeasurable)
      simpa [vaart1998_finiteCoordinateLocalInverseSelectedEstimator,
        vaart1998_localInverseFallbackExtension] using hdist

/--
Finite-coordinate Theorem 4.1 Gaussian-limit endpoint for the canonical
selected estimator with fallback outside the inverse-function-theorem target.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_of_targetProbabilityLocalization_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X)
    (fallback : Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_selectedEstimator_delta_method_of_targetProbabilityLocalization_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := X) (hX_meas := hX_meas)
      (targetProbability := targetProbability) (fallback := fallback)
      (hCLT := hCLT)
  exact
    ⟨hbase.1, hbase.2,
      vaart1998_theorem_4_1_gaussian_limit_of_linear_inverse_derivative
        (Dinv := (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)) hZ_gaussian⟩

/--
Finite-coordinate covariance-functional display for the canonical selected
estimator with fallback outside the target event.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceDisplay_of_targetProbabilityLocalization_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X)
    (fallback : Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      vaart1998_limitCovarianceFunctional
          (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (vaart1998_limitCovarianceFunctional Z Q) L K) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_of_targetProbabilityLocalization_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := X) (hX_meas := hX_meas)
      (targetProbability := targetProbability) (fallback := fallback)
      (hCLT := hCLT) (hZ_gaussian := hZ_gaussian)
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2, fun L K =>
      vaart1998_limitCovarianceFunctional_inverseDerivative_apply
        Z Q (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) L K⟩

/--
Finite-coordinate covarianceBilinDual display for the canonical selected
estimator with fallback outside the target event.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceBilinDual_of_targetProbabilityLocalization_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X)
    (fallback : Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      ProbabilityTheory.covarianceBilinDual
          (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (fun L0 K0 =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L0 K0) L K) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_of_targetProbabilityLocalization_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := X) (hX_meas := hX_meas)
      (targetProbability := targetProbability) (fallback := fallback)
      (hCLT := hCLT) (hZ_gaussian := hZ_gaussian)
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2, fun L K =>
      vaart1998_covarianceBilinDual_inverseDerivative_map_apply_of_memLp
        Z (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
        hCLT.aemeasurable_limit hZ_memLp L K⟩

/--
CLT-certificate version of the canonical selected-estimator covarianceBilinDual
display.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceBilinDual_of_cltCertificate_targetProbabilityLocalization_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (CLT :
      Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
        Coordinate Ω Ω' P Q)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P CLT.X)
    (hX_meas : ∀ coordinate i, Measurable (CLT.X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he CLT.X)
    (fallback : Θ) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he CLT.X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      ProbabilityTheory.covarianceBilinDual
          (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (fun L0 K0 =>
            ProbabilityTheory.covarianceBilinDual (Q.map CLT.Z) L0 K0) L K) := by
  have hCLT :
      TendstoInDistribution
        (fun (n : ℕ) ω =>
          √(n : ℝ) •
            ((fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, CLT.X coordinate i ω) / n) -
              e theta0))
        atTop CLT.Z (fun _ => P) Q := by
    simpa [vaart1998_finiteCoordinateEmpiricalMoment,
      vaart1998_finiteCoordinatePopulationMoment, heta0] using
      CLT.empiricalMoment_clt
  simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceBilinDual_of_targetProbabilityLocalization_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := CLT.X) (hX_meas := hX_meas)
      (targetProbability := targetProbability) (fallback := fallback)
      (hCLT := hCLT) (hZ_gaussian := CLT.gaussian_limit)
      (hZ_memLp := CLT.limit_memLp)

/--
Finite covariance-table display for the canonical selected estimator with
fallback outside the target event.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_targetProbabilityLocalization_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X)
    (fallback : Θ) (coordinates : I -> StrongDual ℝ Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceBilinDual_of_targetProbabilityLocalization_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := X) (hX_meas := hX_meas)
      (targetProbability := targetProbability) (fallback := fallback)
      (hCLT := hCLT) (hZ_gaussian := hZ_gaussian)
      (hZ_memLp := hZ_memLp)
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2.1, fun i j => by
      simpa [vaart1998_covarianceTable,
        vaart1998_inverseDerivativeCovarianceFunctional] using
        hbase.2.2.2 (coordinates i) (coordinates j)⟩

/--
CLT-certificate version of the finite covariance-table display for the
canonical selected estimator with fallback outside the target event.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_cltCertificate_targetProbabilityLocalization_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (CLT :
      Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
        Coordinate Ω Ω' P Q)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P CLT.X)
    (hX_meas : ∀ coordinate i, Measurable (CLT.X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he CLT.X)
    (fallback : Θ) (coordinates : I -> StrongDual ℝ Θ) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he CLT.X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω =>
                (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map CLT.Z) L K) i j) := by
  have hCLT :
      TendstoInDistribution
        (fun (n : ℕ) ω =>
          √(n : ℝ) •
            ((fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, CLT.X coordinate i ω) / n) -
              e theta0))
        atTop CLT.Z (fun _ => P) Q := by
    simpa [vaart1998_finiteCoordinateEmpiricalMoment,
      vaart1998_finiteCoordinatePopulationMoment, heta0] using
      CLT.empiricalMoment_clt
  simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_targetProbabilityLocalization_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := CLT.X) (hX_meas := hX_meas)
      (targetProbability := targetProbability) (fallback := fallback)
      (coordinates := coordinates)
      (hCLT := hCLT) (hZ_gaussian := CLT.gaussian_limit)
      (hZ_memLp := CLT.limit_memLp)

/--
Bundled Chapter 4.1 conclusions for the canonical finite-coordinate selected
estimator with fallback outside the inverse-function-theorem target.
-/
structure Vaart1998FiniteCoordinateSelectedEstimatorTheorem41Conclusion
    (I Coordinate Ω Ω' Θ : Type*) [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] [MeasurableSpace Ω']
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (Q : Measure Ω') [IsProbabilityMeasure Q]
    (e : Θ -> Coordinate -> ℝ) (theta0 : Θ)
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ) (fallback : Θ)
    (coordinates : I -> StrongDual ℝ Θ) (Z : Ω' -> Coordinate -> ℝ)
    (Sigma :
      StrongDual ℝ (Coordinate -> ℝ) ->
        StrongDual ℝ (Coordinate -> ℝ) -> ℝ) where
  /-- The selected estimator is in the local parameter source with probability tending to one. -/
  source_probability :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω ∈
            (he.toOpenPartialHomeomorph e).source})
      atTop (𝓝 1)
  /-- The selected estimator solves the empirical moment equation with probability tending to one. -/
  moment_equation_probability :
    Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
      atTop (𝓝 1)
  /-- The selected estimator has the Theorem 4.1 `sqrt n` weak limit. -/
  delta_limit :
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he X fallback n ω - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q
  /-- The selected-estimator limit is Gaussian. -/
  gaussian_limit :
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q
  /-- The selected-estimator limit covariance table is the inverse-derivative pullback. -/
  covariance_table :
    ∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          Sigma i j

/--
Build the bundled selected-estimator Chapter 4.1 conclusion from target
probability localization and a supplied empirical-moment CLT.
-/
theorem vaart1998_finiteCoordinateSelectedEstimatorTheorem41Conclusion_of_targetProbabilityLocalization_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (targetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate Ω Θ P e theta0 De he X)
    (fallback : Θ) (coordinates : I -> StrongDual ℝ Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) :
    Vaart1998FiniteCoordinateSelectedEstimatorTheorem41Conclusion
      I Coordinate Ω Ω' Θ P Q e theta0 De he X fallback coordinates Z
      (fun L K => ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) where
  source_probability :=
    vaart1998_finiteCoordinateLocalInverseSelectedEstimator_mem_source_of_targetProbabilityLocalization_real
      (P := P) e De he X fallback targetProbability
  moment_equation_probability :=
    vaart1998_finiteCoordinateLocalInverseSelectedEstimator_solves_momentEquation_with_probability_of_targetProbabilityLocalization_real
      (P := P) e De he X fallback targetProbability
  delta_limit := by
    have hbase :=
      vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_targetProbabilityLocalization_real
        (e := e) (theta0 := theta0) (De := De) (he := he)
        (X := X) (hX_meas := hX_meas)
        (targetProbability := targetProbability) (fallback := fallback)
        (coordinates := coordinates)
        (hCLT := hCLT) (hZ_gaussian := hZ_gaussian)
        (hZ_memLp := hZ_memLp)
    exact hbase.2.1
  gaussian_limit := by
    have hbase :=
      vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_targetProbabilityLocalization_real
        (e := e) (theta0 := theta0) (De := De) (he := he)
        (X := X) (hX_meas := hX_meas)
        (targetProbability := targetProbability) (fallback := fallback)
        (coordinates := coordinates)
        (hCLT := hCLT) (hZ_gaussian := hZ_gaussian)
        (hZ_memLp := hZ_memLp)
    exact hbase.2.2.1
  covariance_table := by
    have hbase :=
      vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_targetProbabilityLocalization_real
        (e := e) (theta0 := theta0) (De := De) (he := he)
        (X := X) (hX_meas := hX_meas)
        (targetProbability := targetProbability) (fallback := fallback)
        (coordinates := coordinates)
        (hCLT := hCLT) (hZ_gaussian := hZ_gaussian)
        (hZ_memLp := hZ_memLp)
    exact hbase.2.2.2

/--
Canonical iid product-space covariance-table source endpoint for the actual
fallback-selected estimator.

This theorem builds the target-probability localization certificate from the
canonical product strong law, builds the finite-coordinate empirical-moment CLT
certificate from the vector-law Gaussian/covariance source fields, and displays
the final covariance table under the common vector law `ν`.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (source : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν)
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (fallback : Θ) (coordinates : I -> StrongDual ℝ Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (vaart1998_finiteCoordinateLocalInverseSelectedEstimator
              e De he
              (fun coordinate i sample => sample i coordinate)
              fallback n sample - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j) := by
  have hν_memLp : MemLp id 2 ν := source.memLp_id
  have hfullCovariance :
      ∀ L K : StrongDual ℝ (Coordinate -> ℝ),
        ProbabilityTheory.covarianceBilinDual (Q.map Z) L K =
          ProbabilityTheory.covarianceBilinDual ν L K :=
    vaart1998_covarianceBilinDual_eq_of_diagonal_variance
      (μ := Q.map Z) (ν := ν) hν_memLp hZ_covarianceν
  have hcanonicalCoordinateSource := source.canonicalCoordinateSource
  have hcanonicalVectorSource :=
    vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  have hcoordinateSource :=
    vaart1998_finiteCoordinateCoordinateLLNSource_of_commonVectorLaw
      (P := Measure.infinitePi (fun _ : ℕ => ν))
      (X := fun coordinate i sample => sample i coordinate)
      (ν := ν) source.coordinate_meas hcanonicalVectorSource.1
      hcanonicalVectorSource.2
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  let B :=
    vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_finiteDimensional
      (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q) X Z
      hcanonicalCoordinateSource.2 hZ_aemeas
      (vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
        (P := Measure.infinitePi (fun _ : ℕ => ν)) (Q := Q)
        (vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
          (P := Measure.infinitePi (fun _ : ℕ => ν))
          (Q := Q) (X := X) (Z := Z) (ν := ν)
          (hX_coordinate_memLp := hcanonicalCoordinateSource.1)
          (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
          (hZ_mean :=
            vaart1998_finiteCoordinateProjectedMean_eq_zero_of_map_mean_zero
              (Q := Q) (Z := Z) hZ_aemeas hZ_memLp hZ_mean_zero)
          (hZ_covariance :=
            vaart1998_finiteCoordinateCanonicalSample_covariance_eq_projectedVariance
              (Q := Q) (ν := ν) (Z := Z) hZ_covarianceν)
          (hX_vector_law := hcanonicalVectorSource.1)
          (hX_sequence_law := hcanonicalVectorSource.2)))
  let CLT :=
    vaart1998_finiteCoordinateEmpiricalMomentCLTCertificate_of_cramerWoldBridge
      B hZ_gaussian hZ_memLp
  have htargetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate (ℕ -> Coordinate -> ℝ) Θ
        (Measure.infinitePi (fun _ : ℕ => ν)) e theta0 De he X :=
    Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate.of_finiteCoordinateStrongLaw_real
      (P := Measure.infinitePi (fun _ : ℕ => ν))
      (e := e) (theta0 := theta0) (De := De) (he := he) (X := X)
      (heta0 :=
        vaart1998_finiteCoordinateCanonicalSample_trueMoment_eq_populationMoment
          (ν := ν) e source.coordinate_meas heta0ν)
      (hX_integrable := fun coordinate =>
        (hcanonicalCoordinateSource.1 coordinate).integrable (by norm_num))
      (hX_indep := hcoordinateSource.1)
      (hX_ident := hcoordinateSource.2)
      (hX_meas := hcanonicalCoordinateSource.2)
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_cltCertificate_targetProbabilityLocalization_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (CLT := CLT)
      (heta0 := by
        simpa [CLT, B, X,
          vaart1998_finiteCoordinatePopulationMoment] using
          vaart1998_finiteCoordinateCanonicalSample_trueMoment_eq_populationMoment
            (ν := ν) e source.coordinate_meas heta0ν)
      (hX_meas := by
        intro coordinate i
        simpa [CLT, B, X] using hcanonicalCoordinateSource.2 coordinate i)
      (targetProbability := by
        simpa [CLT, B, X] using htargetProbability)
      (fallback := fallback) (coordinates := coordinates)
  rcases hbase with ⟨hsolve, hdist, hgauss, htable⟩
  exact ⟨by simpa [CLT, B, X] using hsolve,
    by simpa [CLT, B, X] using hdist,
    by simpa [CLT, B, X] using hgauss,
    fun i j => by
      calc
        vaart1998_covarianceTable coordinates
            (fun L K =>
              ProbabilityTheory.covarianceBilinDual
                (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
                L K) i j =
          vaart1998_covarianceTable
            (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
            (fun L K =>
              ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j := by
            simpa [CLT, B, X] using htable i j
        _ = vaart1998_covarianceTable
            (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
            (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j := by
            simp [vaart1998_covarianceTable, hfullCovariance]⟩

/--
Bundled canonical vector-law source conclusion for the actual fallback-selected
estimator.
-/
theorem vaart1998_finiteCoordinateSelectedEstimatorTheorem41Conclusion_of_canonicalMeanVectorLawCovarianceSourceCertificate_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (source : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν)
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (fallback : Θ) (coordinates : I -> StrongDual ℝ Θ)
    {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν) :
    Vaart1998FiniteCoordinateSelectedEstimatorTheorem41Conclusion
      I Coordinate (ℕ -> Coordinate -> ℝ) Ω' Θ
      (Measure.infinitePi (fun _ : ℕ => ν)) Q e theta0 De he
      (fun coordinate i sample => sample i coordinate)
      fallback coordinates Z
      (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) := by
  have hcanonicalCoordinateSource := source.canonicalCoordinateSource
  have hcanonicalVectorSource :=
    vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  have hcoordinateSource :=
    vaart1998_finiteCoordinateCoordinateLLNSource_of_commonVectorLaw
      (P := Measure.infinitePi (fun _ : ℕ => ν))
      (X := fun coordinate i sample => sample i coordinate)
      (ν := ν) source.coordinate_meas hcanonicalVectorSource.1
      hcanonicalVectorSource.2
  let X : Coordinate -> ℕ -> (ℕ -> Coordinate -> ℝ) -> ℝ :=
    fun coordinate i sample => sample i coordinate
  have htargetProbability :
      Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate
        Coordinate (ℕ -> Coordinate -> ℝ) Θ
        (Measure.infinitePi (fun _ : ℕ => ν)) e theta0 De he X :=
    Vaart1998FiniteCoordinateEmpiricalTargetProbabilityLocalizationCertificate.of_finiteCoordinateStrongLaw_real
      (P := Measure.infinitePi (fun _ : ℕ => ν))
      (e := e) (theta0 := theta0) (De := De) (he := he) (X := X)
      (heta0 :=
        vaart1998_finiteCoordinateCanonicalSample_trueMoment_eq_populationMoment
          (ν := ν) e source.coordinate_meas heta0ν)
      (hX_integrable := fun coordinate =>
        (hcanonicalCoordinateSource.1 coordinate).integrable (by norm_num))
      (hX_indep := hcoordinateSource.1)
      (hX_ident := hcoordinateSource.2)
      (hX_meas := hcanonicalCoordinateSource.2)
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_selectedEstimator_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_real
      (source := source) (e := e) (theta0 := theta0) (De := De)
      (he := he) (fallback := fallback) (coordinates := coordinates)
      (Z := Z) (hZ_aemeas := hZ_aemeas)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean_zero := hZ_mean_zero) (hZ_covarianceν := hZ_covarianceν)
      (heta0ν := heta0ν)
  exact
    { source_probability := by
        simpa [X] using
          vaart1998_finiteCoordinateLocalInverseSelectedEstimator_mem_source_of_targetProbabilityLocalization_real
            (P := Measure.infinitePi (fun _ : ℕ => ν))
            e De he X fallback htargetProbability
      moment_equation_probability := by
        simpa [X] using
          vaart1998_finiteCoordinateLocalInverseSelectedEstimator_solves_momentEquation_with_probability_of_targetProbabilityLocalization_real
            (P := Measure.infinitePi (fun _ : ℕ => ν))
            e De he X fallback htargetProbability
      delta_limit := by
        simpa [X] using hbase.2.1
      gaussian_limit := by
        simpa [X] using hbase.2.2.1
      covariance_table := by
        intro i j
        simpa [X] using hbase.2.2.2 i j }

/--
Measurable-coordinate Theorem 4.1 wrapper deriving composed local-inverse
a.e.-measurability from a.e. localization in the open moment range.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_delta_method_of_ae_mem_open_momentRange_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        (fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) ∈
            (he.toOpenPartialHomeomorph e).target)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_delta_method_aemeasurable_real
    e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
    (fun n =>
      vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange
        e De he
        (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
          X hX_meas n).aemeasurable
        (hTarget n))
    hCLT

/--
Finite-coordinate Theorem 4.1 wrapper with a Gaussian supplied
empirical-moment limit.

The first two conclusions are the existence/local-solving and delta-method
limits.  The third conclusion records that the transformed estimator limit is
Gaussian, obtained by mapping the supplied Gaussian empirical-moment limit by
the inverse derivative.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_delta_method_real
      e De he hInv_meas X heta0 hX_integrable hX_indep hX_ident hX_meas
      hCLT
  exact
    ⟨hbase.1, hbase.2,
      vaart1998_theorem_4_1_gaussian_limit_of_linear_inverse_derivative
        (Dinv := (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)) hZ_gaussian⟩

/--
Finite-coordinate Theorem 4.1 Gaussian-limit wrapper using only
a.e.-measurability of the composed local inverse.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_aemeasurable_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)) P)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_and_delta_method_aemeasurable_real
      e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
      hInvEmpirical hCLT
  exact
    ⟨hbase.1, hbase.2,
      vaart1998_theorem_4_1_gaussian_limit_of_linear_inverse_derivative
        (Dinv := (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)) hZ_gaussian⟩

/--
Finite-coordinate Theorem 4.1 Gaussian-limit wrapper deriving composed
local-inverse a.e.-measurability from a.e. localization in the open moment
range.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_of_ae_mem_open_momentRange_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        (fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) ∈
            (he.toOpenPartialHomeomorph e).target)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_aemeasurable_real
    e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
    (fun n =>
      vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange
        e De he
        (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
          X hX_meas n).aemeasurable
        (hTarget n))
    hCLT hZ_gaussian

/--
Finite-coordinate Theorem 4.1 wrapper with the covariance display for the
Gaussian estimator limit.

The covariance statement is written as the pullback identity for all continuous
linear coordinates.  In Euclidean coordinates this is the textbook matrix
display `e'_theta0^{-1} Sigma (e'_theta0^{-1})^T`.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceDisplay_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      vaart1998_limitCovarianceFunctional
          (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (vaart1998_limitCovarianceFunctional Z Q) L K) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_real
      e De he hInv_meas X heta0 hX_integrable hX_indep hX_ident hX_meas
      hCLT hZ_gaussian
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2, fun L K =>
      vaart1998_limitCovarianceFunctional_inverseDerivative_apply
        Z Q (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) L K⟩

/--
Finite-coordinate covariance-display wrapper using only a.e.-measurability of
the composed local inverse.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceDisplay_aemeasurable_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)) P)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      vaart1998_limitCovarianceFunctional
          (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (vaart1998_limitCovarianceFunctional Z Q) L K) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_aemeasurable_real
      e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
      hInvEmpirical hCLT hZ_gaussian
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2, fun L K =>
      vaart1998_limitCovarianceFunctional_inverseDerivative_apply
        Z Q (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) L K⟩

/--
Finite-coordinate covariance-display wrapper deriving composed local-inverse
a.e.-measurability from a.e. localization in the open moment range.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceDisplay_of_ae_mem_open_momentRange_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        (fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) ∈
            (he.toOpenPartialHomeomorph e).target)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      vaart1998_limitCovarianceFunctional
          (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (vaart1998_limitCovarianceFunctional Z Q) L K) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceDisplay_aemeasurable_real
    e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
    (fun n =>
      vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange
        e De he
        (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
          X hX_meas n).aemeasurable
        (hTarget n))
    hCLT hZ_gaussian

/--
Finite-coordinate Theorem 4.1 wrapper with the canonical covarianceBilinDual
display for the Gaussian estimator limit.

The covariance conclusion is the mathlib bilinear-form version of Vaart's
matrix formula `e'_theta0^{-1} Sigma (e'_theta0^{-1})^T`.  The only additional
moment assumption is square-integrability of the supplied empirical-moment
limit law.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      ProbabilityTheory.covarianceBilinDual
          (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (fun L0 K0 =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L0 K0) L K) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_real
      e De he hInv_meas X heta0 hX_integrable hX_indep hX_ident hX_meas
      hCLT hZ_gaussian
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2, fun L K =>
      vaart1998_covarianceBilinDual_inverseDerivative_map_apply_of_memLp
        Z (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
        hCLT.aemeasurable_limit hZ_memLp L K⟩

/--
Finite-coordinate covarianceBilinDual wrapper using only a.e.-measurability of
the composed local inverse.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_aemeasurable_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)) P)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      ProbabilityTheory.covarianceBilinDual
          (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (fun L0 K0 =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L0 K0) L K) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_aemeasurable_real
      e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
      hInvEmpirical hCLT hZ_gaussian
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2, fun L K =>
      vaart1998_covarianceBilinDual_inverseDerivative_map_apply_of_memLp
        Z (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
        hCLT.aemeasurable_limit hZ_memLp L K⟩

/--
Finite-coordinate covarianceBilinDual wrapper deriving composed local-inverse
a.e.-measurability from a.e. localization in the open moment range.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_of_ae_mem_open_momentRange_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (X : Coordinate -> ℕ -> Ω -> ℝ)
    (heta0 :
      e theta0 =
        (fun coordinate : Coordinate => ∫ sample, X coordinate 0 sample ∂P))
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        (fun coordinate : Coordinate =>
          (∑ i ∈ Finset.range n, X coordinate i ω) / n) ∈
            (he.toOpenPartialHomeomorph e).target)
    {Z : Ω' -> Coordinate -> ℝ}
    (hCLT : TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          ((fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n) - e theta0))
      atTop Z (fun _ => P) Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z)) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n)) =
            (fun coordinate : Coordinate =>
              (∑ i ∈ Finset.range n, X coordinate i ω) / n)})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, X coordinate i ω) / n) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      ProbabilityTheory.covarianceBilinDual
          (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (fun L0 K0 =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L0 K0) L K) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_aemeasurable_real
    e De he X heta0 hX_integrable hX_indep hX_ident hX_meas
    (fun n =>
      vaart1998_localInverse_comp_empiricalMoment_aemeasurable_of_ae_mem_open_momentRange
        e De he
        (vaart1998_finiteCoordinate_empiricalMoment_aestronglyMeasurable_real
          X hX_meas n).aemeasurable
        (hTarget n))
    hCLT hZ_gaussian hZ_memLp

/--
Theorem 4.1 finite-coordinate source wrapper fed by the supplied
multivariate empirical-moment CLT certificate.

This is the current endpoint of the Chapter 4 route: strong-law local
existence, localized local-inverse measurability, the supplied multivariate
CLT/Gaussian/MemLp certificate, and the covarianceBilinDual pullback display
are assembled into one source-shaped statement.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_of_cltCertificate_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (CLT :
      Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
        Coordinate Ω Ω' P Q)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P CLT.X)
    (hX_integrable : ∀ coordinate, Integrable (CLT.X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (CLT.X coordinate i) (CLT.X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (CLT.X coordinate i) (CLT.X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (CLT.X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      ProbabilityTheory.covarianceBilinDual
          (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (fun L0 K0 =>
            ProbabilityTheory.covarianceBilinDual (Q.map CLT.Z) L0 K0) L K) := by
  have hCLT :
      TendstoInDistribution
        (fun (n : ℕ) ω =>
          √(n : ℝ) •
            ((fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, CLT.X coordinate i ω) / n) -
              e theta0))
        atTop CLT.Z (fun _ => P) Q := by
    simpa [vaart1998_finiteCoordinateEmpiricalMoment,
      vaart1998_finiteCoordinatePopulationMoment, heta0] using
      CLT.empiricalMoment_clt
  simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_of_ae_mem_open_momentRange_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := CLT.X) (heta0 := by
        simpa [vaart1998_finiteCoordinatePopulationMoment] using heta0)
      (hX_integrable := hX_integrable) (hX_indep := hX_indep)
      (hX_ident := hX_ident) (hX_meas := hX_meas)
      (hTarget := fun n => by
        simpa [vaart1998_finiteCoordinateEmpiricalMoment] using hTarget n)
      (hCLT := hCLT) (hZ_gaussian := CLT.gaussian_limit)
      (hZ_memLp := CLT.limit_memLp)

/--
Theorem 4.1 finite-coordinate CLT-certificate wrapper with the composed
local-inverse empirical estimator supplied directly as an a.e.-measurable map.

This is the certificate-level sibling of the open-target wrapper above.  It is
useful when localization has already been packaged at the estimator level, so
downstream source certificates do not need to restate a separate
target-membership hypothesis for every empirical moment.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_of_cltCertificate_aemeasurable_real
    {Coordinate Ω Ω' Θ : Type*} [Fintype Coordinate] [MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (CLT :
      Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
        Coordinate Ω Ω' P Q)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P CLT.X)
    (hX_integrable : ∀ coordinate, Integrable (CLT.X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (CLT.X coordinate i) (CLT.X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (CLT.X coordinate i) (CLT.X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (CLT.X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) P) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) Q ∧
    (∀ L K : StrongDual ℝ Θ,
      ProbabilityTheory.covarianceBilinDual
          (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) L K =
        vaart1998_inverseDerivativeCovarianceFunctional
          (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ)
          (fun L0 K0 =>
            ProbabilityTheory.covarianceBilinDual (Q.map CLT.Z) L0 K0) L K) := by
  have hCLT :
      TendstoInDistribution
        (fun (n : ℕ) ω =>
          √(n : ℝ) •
            ((fun coordinate : Coordinate =>
                (∑ i ∈ Finset.range n, CLT.X coordinate i ω) / n) -
              e theta0))
        atTop CLT.Z (fun _ => P) Q := by
    simpa [vaart1998_finiteCoordinateEmpiricalMoment,
      vaart1998_finiteCoordinatePopulationMoment, heta0] using
      CLT.empiricalMoment_clt
  simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_aemeasurable_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (X := CLT.X) (heta0 := by
        simpa [vaart1998_finiteCoordinatePopulationMoment] using heta0)
      (hX_integrable := hX_integrable) (hX_indep := hX_indep)
      (hX_ident := hX_ident) (hX_meas := hX_meas)
      (hInvEmpirical := fun n => by
        simpa [vaart1998_finiteCoordinateEmpiricalMoment] using
          hInvEmpirical n)
      (hCLT := hCLT) (hZ_gaussian := CLT.gaussian_limit)
      (hZ_memLp := CLT.limit_memLp)

/--
Theorem 4.1 finite-coordinate source wrapper with a finite covariance table,
fed by the supplied multivariate empirical-moment CLT certificate.

This is the table-valued version of the covarianceBilinDual source wrapper:
after choosing finitely many continuous linear coordinates on the parameter
space, Vaart's covariance display is available entry by entry.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_cltCertificate_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (CLT :
      Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
        Coordinate Ω Ω' P Q)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P CLT.X)
    (hX_integrable : ∀ coordinate, Integrable (CLT.X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (CLT.X coordinate i) (CLT.X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (CLT.X coordinate i) (CLT.X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (CLT.X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map CLT.Z) L K) i j) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_of_cltCertificate_real
      (e := e) (theta0 := theta0) (De := De) (he := he) (CLT := CLT)
      (heta0 := heta0) (hX_integrable := hX_integrable)
      (hX_indep := hX_indep) (hX_ident := hX_ident)
      (hX_meas := hX_meas) (hTarget := hTarget)
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2.1, fun i j => by
      simpa [vaart1998_covarianceTable,
        vaart1998_inverseDerivativeCovarianceFunctional] using
        hbase.2.2.2 (coordinates i) (coordinates j)⟩

/--
Finite covariance-table version of the CLT-certificate a.e.-measurable
local-inverse wrapper.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_cltCertificate_aemeasurable_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (CLT :
      Vaart1998FiniteCoordinateEmpiricalMomentCLTCertificate
        Coordinate Ω Ω' P Q)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P CLT.X)
    (hX_integrable : ∀ coordinate, Integrable (CLT.X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (CLT.X coordinate i) (CLT.X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (CLT.X coordinate i) (CLT.X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (CLT.X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) P) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (CLT.Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map CLT.Z) L K) i j) := by
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceBilinDual_of_cltCertificate_aemeasurable_real
      (e := e) (theta0 := theta0) (De := De) (he := he) (CLT := CLT)
      (heta0 := heta0) (hX_integrable := hX_integrable)
      (hX_indep := hX_indep) (hX_ident := hX_ident)
      (hX_meas := hX_meas) (hInvEmpirical := hInvEmpirical)
  exact
    ⟨hbase.1, hbase.2.1, hbase.2.2.1, fun i j => by
      simpa [vaart1998_covarianceTable,
        vaart1998_inverseDerivativeCovarianceFunctional] using
        hbase.2.2.2 (coordinates i) (coordinates j)⟩

/--
Theorem 4.1 finite-coordinate covariance-table endpoint fed by a Cramér-Wold
bridge.

This removes the caller-side step of manually converting the bridge into a
multivariate empirical-moment CLT certificate.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_cramerWoldBridge_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (B : Vaart1998FiniteCoordinateCramerWoldCLTBridge Coordinate Ω Ω' P Q)
    (hZ_gaussian : HasGaussianLaw B.Z Q)
    (hZ_memLp : MemLp id 2 (Q.map B.Z))
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P B.X)
    (hX_integrable : ∀ coordinate, Integrable (B.X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (B.X coordinate i) (B.X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (B.X coordinate i) (B.X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (B.X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment B.X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment B.X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment B.X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment B.X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (B.Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (B.Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (B.Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map B.Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_cltCertificate_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates)
    (CLT :=
      vaart1998_finiteCoordinateEmpiricalMomentCLTCertificate_of_cramerWoldBridge
        B hZ_gaussian hZ_memLp)
    (heta0 := heta0) (hX_integrable := hX_integrable)
    (hX_indep := hX_indep) (hX_ident := hX_ident)
    (hX_meas := hX_meas) (hTarget := hTarget)

/--
Theorem 4.1 finite-coordinate covariance-table endpoint fed directly by
projected scalar CLTs.

The finite-dimensional Cramér-Wold theorem constructs the bridge internally, so
the caller only supplies the projected scalar CLT family.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedScalarCLT_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (X : Coordinate -> ℕ -> Ω -> ℝ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hscalar : vaart1998_finiteCoordinateProjectedScalarCLT (P := P) (Q := Q) X Z)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_cramerWoldBridge_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates)
    (B :=
      vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_finiteDimensional
        (P := P) (Q := Q) X Z hX_meas hZ_aemeas hscalar)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (heta0 := heta0) (hX_integrable := hX_integrable)
    (hX_indep := hX_indep) (hX_ident := hX_ident)
    (hX_meas := hX_meas) (hTarget := hTarget)

/--
Theorem 4.1 finite-coordinate covariance-table endpoint fed by projected
summand scalar CLTs.

This is the handoff closest to the one-dimensional CLT infrastructure: once
every continuous linear projection has the scalar sum-centered CLT, the
finite-dimensional Cramér-Wold bridge and covariance-table endpoint are
assembled internally.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedSummandCLT_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (X : Coordinate -> ℕ -> Ω -> ℝ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hsummand :
      vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedScalarCLT_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (X := X) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hscalar :=
      vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
        (P := P) (Q := Q) hsummand)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (heta0 := heta0) (hX_integrable := hX_integrable)
    (hX_indep := hX_indep) (hX_ident := hX_ident)
    (hX_meas := hX_meas) (hTarget := hTarget)

/--
Theorem 4.1 finite-coordinate covariance-table endpoint fed by projected
summand scalar CLTs and direct a.e.-measurability of the localized empirical
estimator.

This is the reusable handoff for source wrappers that already construct the
composed local inverse as an a.e.-measurable statistic, avoiding a separate
per-`n` target-membership assumption at this layer.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedSummandCLT_aemeasurable_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (X : Coordinate -> ℕ -> Ω -> ℝ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hsummand :
      vaart1998_finiteCoordinateProjectedSummandCLT (P := P) (Q := Q) X Z)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) P) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) := by
  let B :=
    vaart1998_finiteCoordinateCramerWoldCLTBridge_of_projectedScalarCLT_finiteDimensional
      (P := P) (Q := Q) X Z hX_meas hZ_aemeas
      (vaart1998_finiteCoordinateProjectedScalarCLT_of_projectedSummandCLT
        (P := P) (Q := Q) hsummand)
  let CLT :=
    vaart1998_finiteCoordinateEmpiricalMomentCLTCertificate_of_cramerWoldBridge
      B hZ_gaussian hZ_memLp
  have hInvCLT : ∀ n : ℕ,
      AEMeasurable
        (fun ω : Ω =>
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment CLT.X n ω)) P := by
    intro n
    simpa [CLT, B] using hInvEmpirical n
  simpa [CLT, B] using
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_cltCertificate_aemeasurable_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (coordinates := coordinates) (CLT := CLT)
      (heta0 := by simpa [CLT, B] using heta0)
      (hX_integrable := by
        intro coordinate
        simpa [CLT, B] using hX_integrable coordinate)
      (hX_indep := by
        intro coordinate
        simpa [CLT, B] using hX_indep coordinate)
      (hX_ident := by
        intro coordinate i
        simpa [CLT, B] using hX_ident coordinate i)
      (hX_meas := by
        intro coordinate i
        simpa [CLT, B] using hX_meas coordinate i)
      (hInvEmpirical := hInvCLT)

/--
Theorem 4.1 finite-coordinate covariance-table endpoint fed by vector-valued
source fields plus the finite-coordinate Gaussian/covariance source fields.

This packages the full handoff from vector-valued source assumptions to the
projected one-dimensional CLTs, then into the existing finite-dimensional
Cramér-Wold and delta-method endpoint.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_vectorGaussianSource_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (X : Coordinate -> ℕ -> Ω -> ℝ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P])
    (hX_vector_memLp : MemLp (vaart1998_finiteCoordinateSampleVector X 0) 2 P)
    (hX_vector_indep :
      iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P)
    (hX_vector_ident : ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_integrable : ∀ coordinate, Integrable (X coordinate 0) P)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedSummandCLT_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (X := X) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hsummand :=
      vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_vectorGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z)
        (hX_integrable := hX_integrable)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_memLp := hX_vector_memLp) (hX_indep := hX_vector_indep)
        (hX_ident := hX_vector_ident))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (heta0 := heta0) (hX_integrable := hX_integrable)
    (hX_indep := hX_indep) (hX_ident := hX_ident)
    (hX_meas := hX_meas) (hTarget := hTarget)

/--
Theorem 4.1 covariance-table endpoint using coordinatewise `MemLp 2` to
discharge both the finite-coordinate integrability and vector `MemLp` source
fields.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_coordinateMemLp_vectorGaussianSource_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (X : Coordinate -> ℕ -> Ω -> ℝ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P])
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hX_vector_indep :
      iIndepFun (fun i => vaart1998_finiteCoordinateSampleVector X i) P)
    (hX_vector_ident : ∀ i : ℕ,
      IdentDistrib
        (vaart1998_finiteCoordinateSampleVector X i)
        (vaart1998_finiteCoordinateSampleVector X 0) P P)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedSummandCLT_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (X := X) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hsummand :=
      vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_vectorGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_indep := hX_vector_indep) (hX_ident := hX_vector_ident))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (heta0 := heta0)
    (hX_integrable := fun coordinate =>
      (hX_coordinate_memLp coordinate).integrable (by norm_num))
    (hX_indep := hX_indep) (hX_ident := hX_ident)
    (hX_meas := hX_meas) (hTarget := hTarget)

/--
Theorem 4.1 covariance-table endpoint using coordinatewise `MemLp 2`, a
common finite-coordinate vector law, and the infinite product law of the
sample-vector sequence to discharge the vector source fields.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_coordinateMemLp_commonVectorLawGaussianSource_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (X : Coordinate -> ℕ -> Ω -> ℝ) {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P])
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hX_vector_law : ∀ i : ℕ,
      HasLaw (vaart1998_finiteCoordinateSampleVector X i) ν P)
    (hX_sequence_law :
      HasLaw (fun ω i => vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_indep :
      ∀ coordinate, Pairwise fun i j =>
        _root_.ProbabilityTheory.IndepFun (X coordinate i) (X coordinate j) P)
    (hX_ident :
      ∀ coordinate i, IdentDistrib (X coordinate i) (X coordinate 0) P P)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedSummandCLT_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (X := X) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hsummand :=
      vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
        (P := P) (Q := Q) (X := X) (Z := Z) (ν := ν)
        (hX_coordinate_memLp := hX_coordinate_memLp)
        (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
        (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
        (hX_vector_law := hX_vector_law)
        (hX_sequence_law := hX_sequence_law))
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (heta0 := heta0)
    (hX_integrable := fun coordinate =>
      (hX_coordinate_memLp coordinate).integrable (by norm_num))
    (hX_indep := hX_indep) (hX_ident := hX_ident)
    (hX_meas := hX_meas) (hTarget := hTarget)

/--
Theorem 4.1 covariance-table endpoint using coordinatewise `MemLp 2`, a
common finite-coordinate vector law, the infinite product law of the
sample-vector sequence, and coordinate evaluation measurability to discharge
the vector and coordinate LLN source fields.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_coordinateMemLp_commonVectorLawCoordinateSource_real
    {I Coordinate Ω Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ)
    (X : Coordinate -> ℕ -> Ω -> ℝ) {Z : Ω' -> Coordinate -> ℝ}
    {ν : Measure (Coordinate -> ℝ)}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L X 0; P])
    (hX_coordinate_memLp : ∀ coordinate, MemLp (X coordinate 0) 2 P)
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hX_vector_law : ∀ i : ℕ,
      HasLaw (vaart1998_finiteCoordinateSampleVector X i) ν P)
    (hX_sequence_law :
      HasLaw (fun ω i => vaart1998_finiteCoordinateSampleVector X i ω)
        (Measure.infinitePi (fun _ : ℕ => ν)) P)
    (heta0 :
      e theta0 = vaart1998_finiteCoordinatePopulationMoment P X)
    (hX_meas : ∀ coordinate i, Measurable (X coordinate i))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ ω ∂P,
        vaart1998_finiteCoordinateEmpiricalMoment X n ω ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      P.real
        {ω : Ω |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω)) =
            vaart1998_finiteCoordinateEmpiricalMoment X n ω})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) ω =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment X n ω) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => P) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) := by
  have hcoordinateSource :=
    vaart1998_finiteCoordinateCoordinateLLNSource_of_commonVectorLaw
      (P := P) (X := X) (ν := ν) hcoordinate_meas hX_vector_law hX_sequence_law
  exact
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_coordinateMemLp_commonVectorLawGaussianSource_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (coordinates := coordinates) (X := X) (Z := Z) (ν := ν)
      (hZ_aemeas := hZ_aemeas)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_coordinate_memLp := hX_coordinate_memLp)
      (hX_vector_law := hX_vector_law)
      (hX_sequence_law := hX_sequence_law)
      (heta0 := heta0) (hX_indep := hcoordinateSource.1)
      (hX_ident := hcoordinateSource.2)
      (hX_meas := hX_meas) (hTarget := hTarget)

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint.  The
finite-coordinate sample source is `X coordinate i sample = sample i coordinate`;
the remaining source fields are the vector law, coordinate evaluation
measurability, and coordinate-projection `MemLp` under that vector law.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalProductSource_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covariance : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[vaart1998_finiteCoordinateProjectedSample L
          (fun coordinate i sample => sample i coordinate) 0;
          Measure.infinitePi (fun _ : ℕ => ν)])
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (heta0 :
      e theta0 =
        vaart1998_finiteCoordinatePopulationMoment
          (Measure.infinitePi (fun _ : ℕ => ν))
          (fun coordinate i sample => sample i coordinate))
    (hTarget : ∀ n : ℕ,
      ∀ᵐ sample ∂Measure.infinitePi (fun _ : ℕ => ν),
        vaart1998_finiteCoordinateEmpiricalMoment
            (fun coordinate i sample => sample i coordinate) n sample ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) := by
  have hcanonicalCoordinateSource :=
    vaart1998_finiteCoordinateCanonicalSample_coordinateSource
      (ν := ν) hcoordinate_meas hν_coordinate_memLp
  have hcanonicalVectorSource :=
    vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  exact
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_coordinateMemLp_commonVectorLawCoordinateSource_real
      (P := Measure.infinitePi (fun _ : ℕ => ν))
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (coordinates := coordinates)
      (X := fun coordinate i sample => sample i coordinate) (Z := Z) (ν := ν)
      (hZ_aemeas := hZ_aemeas)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean := hZ_mean) (hZ_covariance := hZ_covariance)
      (hX_coordinate_memLp := hcanonicalCoordinateSource.1)
      (hcoordinate_meas := hcoordinate_meas)
      (hX_vector_law := hcanonicalVectorSource.1)
      (hX_sequence_law := hcanonicalVectorSource.2)
      (heta0 := heta0) (hX_meas := hcanonicalCoordinateSource.2)
      (hTarget := hTarget)

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint with the
true moment and covariance hypotheses stated entirely under the common vector
law `ν`.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalVectorLawSource_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      Q[fun ω => L (Z ω)] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν)
    (hTarget : ∀ n : ℕ,
      ∀ᵐ sample ∂Measure.infinitePi (fun _ : ℕ => ν),
        vaart1998_finiteCoordinateEmpiricalMoment
            (fun coordinate i sample => sample i coordinate) n sample ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalProductSource_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean := hZ_mean)
    (hZ_covariance :=
      vaart1998_finiteCoordinateCanonicalSample_covariance_eq_projectedVariance
        (Q := Q) (ν := ν) (Z := Z) hZ_covarianceν)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (heta0 :=
      vaart1998_finiteCoordinateCanonicalSample_trueMoment_eq_populationMoment
        (ν := ν) e hcoordinate_meas heta0ν)
    (hTarget := hTarget)

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint with the
Gaussian limit mean-zero hypothesis stated as a vector-law mean-zero identity.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawSource_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν)
    (hTarget : ∀ n : ℕ,
      ∀ᵐ sample ∂Measure.infinitePi (fun _ : ℕ => ν),
        vaart1998_finiteCoordinateEmpiricalMoment
            (fun coordinate i sample => sample i coordinate) n sample ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalVectorLawSource_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean :=
      vaart1998_finiteCoordinateProjectedMean_eq_zero_of_map_mean_zero
        (Q := Q) (Z := Z) hZ_aemeas hZ_memLp hZ_mean_zero)
    (hZ_covarianceν := hZ_covarianceν)
    (hcoordinate_meas := hcoordinate_meas)
    (hν_coordinate_memLp := hν_coordinate_memLp)
    (heta0ν := heta0ν) (hTarget := hTarget)

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint whose final
covariance display is stated under the common vector law `ν`.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSource_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (hcoordinate_meas : ∀ coordinate,
      Measurable (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate))
    (hν_coordinate_memLp : ∀ coordinate,
      MemLp (fun sampleVector : Coordinate -> ℝ => sampleVector coordinate) 2 ν)
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν)
    (hTarget : ∀ n : ℕ,
      ∀ᵐ sample ∂Measure.infinitePi (fun _ : ℕ => ν),
        vaart1998_finiteCoordinateEmpiricalMoment
            (fun coordinate i sample => sample i coordinate) n sample ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j) := by
  have hν_memLp : MemLp id 2 ν := by
    simpa using
      (MemLp.of_eval (f := fun sampleVector : Coordinate -> ℝ => sampleVector)
        hν_coordinate_memLp)
  have hfullCovariance :
      ∀ L K : StrongDual ℝ (Coordinate -> ℝ),
        ProbabilityTheory.covarianceBilinDual (Q.map Z) L K =
          ProbabilityTheory.covarianceBilinDual ν L K :=
    vaart1998_covarianceBilinDual_eq_of_diagonal_variance
      (μ := Q.map Z) (ν := ν) hν_memLp hZ_covarianceν
  rcases
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawSource_real
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (coordinates := coordinates) (Z := Z)
      (hZ_aemeas := hZ_aemeas)
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (hZ_mean_zero := hZ_mean_zero)
      (hZ_covarianceν := hZ_covarianceν)
      (hcoordinate_meas := hcoordinate_meas)
      (hν_coordinate_memLp := hν_coordinate_memLp)
      (heta0ν := heta0ν) (hTarget := hTarget) with
    ⟨hsolve, hdist, hgauss, htable⟩
  exact ⟨hsolve, hdist, hgauss, fun i j => by
    calc
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j :=
          htable i j
      _ = vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j := by
          simp [vaart1998_covarianceTable, hfullCovariance]⟩

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint using the
finite-coordinate vector-law source certificate for coordinate measurability
and square-integrability.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (source : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν)
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν)
    (hTarget : ∀ n : ℕ,
      ∀ᵐ sample ∂Measure.infinitePi (fun _ : ℕ => ν),
        vaart1998_finiteCoordinateEmpiricalMoment
            (fun coordinate i sample => sample i coordinate) n sample ∈
          (he.toOpenPartialHomeomorph e).target) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSource_real
    (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean_zero := hZ_mean_zero)
    (hZ_covarianceν := hZ_covarianceν)
    (hcoordinate_meas := source.coordinate_meas)
    (hν_coordinate_memLp := source.coordinate_memLp)
    (heta0ν := heta0ν) (hTarget := hTarget)

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint using the
finite-coordinate vector-law source certificate and direct a.e.-measurability of
the empirical local-inverse statistic.

This is the source-certificate version of the canonical covariance endpoint for
callers that have already constructed
`he.localInverse e De theta0 (vaart1998_finiteCoordinateEmpiricalMoment X n ω)`
as an a.e.-measurable statistic.  It avoids restating a stronger
target-membership event for every empirical moment at this boundary.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_aemeasurable_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (source : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν)
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν)
    (hInvEmpirical : ∀ n : ℕ,
      AEMeasurable
        (fun sample : ℕ -> Coordinate -> ℝ =>
          he.localInverse e De theta0
            (vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample))
        (Measure.infinitePi (fun _ : ℕ => ν))) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j) := by
  have hν_memLp : MemLp id 2 ν := source.memLp_id
  have hfullCovariance :
      ∀ L K : StrongDual ℝ (Coordinate -> ℝ),
        ProbabilityTheory.covarianceBilinDual (Q.map Z) L K =
          ProbabilityTheory.covarianceBilinDual ν L K :=
    vaart1998_covarianceBilinDual_eq_of_diagonal_variance
      (μ := Q.map Z) (ν := ν) hν_memLp hZ_covarianceν
  have hcanonicalCoordinateSource := source.canonicalCoordinateSource
  have hcanonicalVectorSource :=
    vaart1998_finiteCoordinateCanonicalSampleVector_commonVectorLawSource
      (ν := ν)
  have hcoordinateSource :=
    vaart1998_finiteCoordinateCoordinateLLNSource_of_commonVectorLaw
      (P := Measure.infinitePi (fun _ : ℕ => ν))
      (X := fun coordinate i sample => sample i coordinate)
      (ν := ν) source.coordinate_meas hcanonicalVectorSource.1
      hcanonicalVectorSource.2
  have hbase :=
    vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_projectedSummandCLT_aemeasurable_real
      (P := Measure.infinitePi (fun _ : ℕ => ν))
      (e := e) (theta0 := theta0) (De := De) (he := he)
      (coordinates := coordinates)
      (X := fun coordinate i sample => sample i coordinate) (Z := Z)
      (hZ_aemeas := hZ_aemeas)
      (hsummand :=
        vaart1998_finiteCoordinateProjectedSummandCLT_of_mathlibCLT_coordinateMemLp_commonVectorLawGaussianSource
          (P := Measure.infinitePi (fun _ : ℕ => ν))
          (Q := Q) (X := fun coordinate i sample => sample i coordinate)
          (Z := Z) (ν := ν)
          (hX_coordinate_memLp := hcanonicalCoordinateSource.1)
          (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
          (hZ_mean :=
            vaart1998_finiteCoordinateProjectedMean_eq_zero_of_map_mean_zero
              (Q := Q) (Z := Z) hZ_aemeas hZ_memLp hZ_mean_zero)
          (hZ_covariance :=
            vaart1998_finiteCoordinateCanonicalSample_covariance_eq_projectedVariance
              (Q := Q) (ν := ν) (Z := Z) hZ_covarianceν)
          (hX_vector_law := hcanonicalVectorSource.1)
          (hX_sequence_law := hcanonicalVectorSource.2))
      (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
      (heta0 :=
        vaart1998_finiteCoordinateCanonicalSample_trueMoment_eq_populationMoment
          (ν := ν) e source.coordinate_meas heta0ν)
      (hX_integrable := fun coordinate =>
        (hcanonicalCoordinateSource.1 coordinate).integrable (by norm_num))
      (hX_indep := hcoordinateSource.1)
      (hX_ident := hcoordinateSource.2)
      (hX_meas := hcanonicalCoordinateSource.2)
      (hInvEmpirical := hInvEmpirical)
  rcases hbase with ⟨hsolve, hdist, hgauss, htable⟩
  exact ⟨hsolve, hdist, hgauss, fun i j => by
    calc
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual (Q.map Z) L K) i j :=
          htable i j
      _ = vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j := by
          simp [vaart1998_covarianceTable, hfullCovariance]⟩

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint using the
finite-coordinate vector-law source certificate and a named empirical
local-inverse measurability certificate.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_localInverseCertificate_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (source : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν)
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (localization :
      Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate
        Coordinate (ℕ -> Coordinate -> ℝ) Θ
        (Measure.infinitePi (fun _ : ℕ => ν)) e theta0 De he
        (fun coordinate i sample => sample i coordinate))
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_aemeasurable_real
    (source := source) (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean_zero := hZ_mean_zero)
    (hZ_covarianceν := hZ_covarianceν)
    (heta0ν := heta0ν)
    (hInvEmpirical := localization.empiricalLocalInverse_aemeasurable)

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint using the
finite-coordinate vector-law source certificate and a named empirical
target-localization certificate.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_targetLocalization_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (source : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν)
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (targetLocalization :
      Vaart1998FiniteCoordinateEmpiricalTargetLocalizationCertificate
        Coordinate (ℕ -> Coordinate -> ℝ) Θ
        (Measure.infinitePi (fun _ : ℕ => ν)) e theta0 De he
        (fun coordinate i sample => sample i coordinate))
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_localInverseCertificate_real
    (source := source) (e := e) (theta0 := theta0) (De := De) (he := he)
    (localization :=
      Vaart1998FiniteCoordinateEmpiricalLocalInverseMeasurabilityCertificate.of_targetLocalization_real
        (P := Measure.infinitePi (fun _ : ℕ => ν))
        (e := e) (theta0 := theta0) (De := De) (he := he)
        (X := fun coordinate i sample => sample i coordinate)
        (hX_meas := source.canonicalCoordinateSource.2)
        targetLocalization)
    (coordinates := coordinates) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean_zero := hZ_mean_zero)
    (hZ_covarianceν := hZ_covarianceν)
    (heta0ν := heta0ν)

/--
Canonical iid product-space Theorem 4.1 covariance-table endpoint using the
finite-coordinate vector-law source certificate and global measurability of the
inverse-function-theorem local inverse.

This discharges the direct empirical local-inverse `AEMeasurable` field in the
previous endpoint from ordinary measurability of `he.localInverse e De theta0`.
-/
theorem vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_measurableLocalInverse_real
    {I Coordinate Ω' Θ : Type*} [Fintype I] [Fintype Coordinate]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    [CompleteSpace (Coordinate -> ℝ)]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ] [CompleteSpace Θ]
    [MeasurableSpace Θ] [SecondCountableTopology Θ] [BorelSpace Θ]
    [OpensMeasurableSpace Θ]
    {ν : Measure (Coordinate -> ℝ)} [IsProbabilityMeasure ν]
    (source : Vaart1998FiniteCoordinateVectorLawSource Coordinate ν)
    (e : Θ -> Coordinate -> ℝ) {theta0 : Θ}
    (De : Θ ≃L[ℝ] (Coordinate -> ℝ))
    (he : HasStrictFDerivAt e (De : Θ →L[ℝ] (Coordinate -> ℝ)) theta0)
    (hInv_meas : Measurable (he.localInverse e De theta0))
    (coordinates : I -> StrongDual ℝ Θ) {Z : Ω' -> Coordinate -> ℝ}
    (hZ_aemeas : AEMeasurable Z Q)
    (hZ_gaussian : HasGaussianLaw Z Q)
    (hZ_memLp : MemLp id 2 (Q.map Z))
    (hZ_mean_zero : (Q.map Z)[id] = 0)
    (hZ_covarianceν : ∀ L : StrongDual ℝ (Coordinate -> ℝ),
      ProbabilityTheory.covarianceBilinDual (Q.map Z) L L =
        Var[L; ν])
    (heta0ν :
      e theta0 =
        fun coordinate : Coordinate =>
          ∫ sampleVector, sampleVector coordinate ∂ν) :
    (Tendsto (fun n : ℕ =>
      (Measure.infinitePi (fun _ : ℕ => ν)).real
        {sample : ℕ -> Coordinate -> ℝ |
          e ((he.toOpenPartialHomeomorph e).symm
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample)) =
            vaart1998_finiteCoordinateEmpiricalMoment
              (fun coordinate i sample => sample i coordinate) n sample})
        atTop (𝓝 1)) ∧
    TendstoInDistribution
      (fun (n : ℕ) sample =>
        √(n : ℝ) •
          (he.localInverse e De theta0
              (vaart1998_finiteCoordinateEmpiricalMoment
                (fun coordinate i sample => sample i coordinate) n sample) - theta0))
      atTop (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
      (fun _ => Measure.infinitePi (fun _ : ℕ => ν)) Q ∧
    HasGaussianLaw
      (fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω)) Q ∧
    (∀ i j : I,
      vaart1998_covarianceTable coordinates
          (fun L K =>
            ProbabilityTheory.covarianceBilinDual
              (Q.map fun ω => (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ) (Z ω))
              L K) i j =
        vaart1998_covarianceTable
          (fun k => (coordinates k).comp (De.symm : (Coordinate -> ℝ) →L[ℝ] Θ))
          (fun L K => ProbabilityTheory.covarianceBilinDual ν L K) i j) :=
  vaart1998_theorem_4_1_finiteCoordinateMeasurable_sqrt_exists_delta_gaussianLimit_covarianceTable_of_canonicalMeanVectorLawCovarianceSourceCertificate_aemeasurable_real
    (source := source) (e := e) (theta0 := theta0) (De := De) (he := he)
    (coordinates := coordinates) (Z := Z)
    (hZ_aemeas := hZ_aemeas)
    (hZ_gaussian := hZ_gaussian) (hZ_memLp := hZ_memLp)
    (hZ_mean_zero := hZ_mean_zero)
    (hZ_covarianceν := hZ_covarianceν)
    (heta0ν := heta0ν)
    (hInvEmpirical :=
      vaart1998_finiteCoordinate_localInverse_comp_empiricalMoment_aemeasurable_of_measurable_real
        (P := Measure.infinitePi (fun _ : ℕ => ν))
        (e := e) (theta0 := theta0) (De := De) (he := he)
        (hInv_meas := hInv_meas)
        (X := fun coordinate i sample => sample i coordinate)
        (hX_meas := source.canonicalCoordinateSource.2))

end AsymptoticStatistics
end StatInference
