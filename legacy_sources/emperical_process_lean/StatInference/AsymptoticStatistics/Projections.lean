import StatInference.AsymptoticStatistics.LAN

/-!
# van der Vaart 1998 Chapter 11 projection interfaces

This module opens the Chapter 11 lane.  The first layer keeps L2 projections
source-shaped: squared-error optimality, orthogonality, a.s. uniqueness,
constant-space consequences, and the standardized asymptotic-equivalence
handoff from Theorem 11.2 are recorded as reusable certificates.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal ProbabilityTheory Topology

/--
The Chapter 11 L2 inner product display `E X Y`.
-/
def vaart1998_l2Inner
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (X Y : Ω -> ℝ) : ℝ :=
  ∫ ω, X ω * Y ω ∂P

/--
The residual `T - \hat S` used in the projection orthogonality condition.
-/
def vaart1998_l2Residual
    {Ω : Type*} (T projection : Ω -> ℝ) : Ω -> ℝ :=
  fun ω => T ω - projection ω

/--
The squared-error criterion minimized by an L2 projection.
-/
def vaart1998_projectionSquaredError
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (T S : Ω -> ℝ) : ℝ :=
  ∫ ω, (T ω - S ω) ^ 2 ∂P

/--
The expectation display used in the constant-containing projection
consequences.
-/
def vaart1998_projectionExpectation
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (X : Ω -> ℝ) : ℝ :=
  ∫ ω, X ω ∂P

/--
The covariance display used after the residual has zero mean.
-/
def vaart1998_projectionCovariance
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (X Y : Ω -> ℝ) : ℝ :=
  ∫ ω,
    (X ω - vaart1998_projectionExpectation P X) *
      (Y ω - vaart1998_projectionExpectation P Y) ∂P

/--
Orthogonality of the projection residual to every member of a candidate
space.
-/
def vaart1998_l2OrthogonalToSpace
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (T projection : Ω -> ℝ)
    (candidateSet : Set (Ω -> ℝ)) : Prop :=
  ∀ S ∈ candidateSet,
    vaart1998_l2Inner P
      (vaart1998_l2Residual T projection) S = 0

/--
The direct Chapter 11 definition: `projection` is in the candidate set and
minimizes squared error over that set.
-/
def vaart1998_isL2Projection
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (T : Ω -> ℝ)
    (candidateSet : Set (Ω -> ℝ)) (projection : Ω -> ℝ) : Prop :=
  projection ∈ candidateSet ∧
    ∀ S ∈ candidateSet,
      vaart1998_projectionSquaredError P T projection ≤
        vaart1998_projectionSquaredError P T S

/--
Source-shaped linear-space hypothesis for Chapter 11 projection candidates.
The `finiteSecondMoment` predicate records the textbook side condition without
forcing each downstream packet to commit to a particular integrability API.
-/
structure Vaart1998ProjectionLinearSpaceSource
    {Ω : Type*} (candidateSet : Set (Ω -> ℝ)) where
  /-- The zero variable belongs to the candidate space. -/
  zero_mem : (fun _ : Ω => 0) ∈ candidateSet
  /-- The candidate space is closed under addition. -/
  add_mem :
    ∀ {S U : Ω -> ℝ}, S ∈ candidateSet -> U ∈ candidateSet ->
      (fun ω => S ω + U ω) ∈ candidateSet
  /-- The candidate space is closed under real scalar multiplication. -/
  smul_mem :
    ∀ (a : ℝ) {S : Ω -> ℝ}, S ∈ candidateSet ->
      (fun ω => a * S ω) ∈ candidateSet
  /-- Predicate representing the finite-second-moment side condition. -/
  finiteSecondMoment : (Ω -> ℝ) -> Prop
  /-- Members of the candidate space satisfy the side condition. -/
  finiteSecondMoment_of_mem :
    ∀ {S : Ω -> ℝ}, S ∈ candidateSet -> finiteSecondMoment S

/--
Theorem 11.1 source: for a linear space of finite-second-moment variables,
projection optimality is equivalent to residual orthogonality.
-/
structure Vaart1998Theorem11_1ProjectionOrthogonalitySource
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (T projection : Ω -> ℝ)
    (candidateSet : Set (Ω -> ℝ)) where
  /-- The candidate set is the linear space from the theorem. -/
  linearSpace : Vaart1998ProjectionLinearSpaceSource candidateSet
  /-- The proposed projection belongs to the candidate space. -/
  projection_mem : projection ∈ candidateSet
  /-- The textbook equivalence between minimization and orthogonality. -/
  projection_iff_orthogonal :
    vaart1998_isL2Projection P T candidateSet projection ↔
      projection ∈ candidateSet ∧
        vaart1998_l2OrthogonalToSpace P T projection candidateSet

/--
Theorem 11.1 optimality/orthogonality equivalence.
-/
theorem Vaart1998Theorem11_1ProjectionOrthogonalitySource.projection_orthogonality_iff
    {Ω : Type*} [MeasurableSpace Ω]
    {P : Measure Ω} {T projection : Ω -> ℝ}
    {candidateSet : Set (Ω -> ℝ)}
    (S : Vaart1998Theorem11_1ProjectionOrthogonalitySource
      P T projection candidateSet) :
    vaart1998_isL2Projection P T candidateSet projection ↔
      projection ∈ candidateSet ∧
        vaart1998_l2OrthogonalToSpace P T projection candidateSet :=
  S.projection_iff_orthogonal

/--
An orthogonal residual certifies that the candidate is an L2 projection.
-/
theorem Vaart1998Theorem11_1ProjectionOrthogonalitySource.isL2Projection_of_orthogonal
    {Ω : Type*} [MeasurableSpace Ω]
    {P : Measure Ω} {T projection : Ω -> ℝ}
    {candidateSet : Set (Ω -> ℝ)}
    (S : Vaart1998Theorem11_1ProjectionOrthogonalitySource
      P T projection candidateSet)
    (hOrthogonal :
      vaart1998_l2OrthogonalToSpace P T projection candidateSet) :
    vaart1998_isL2Projection P T candidateSet projection :=
  S.projection_iff_orthogonal.2 ⟨S.projection_mem, hOrthogonal⟩

/--
Every L2 projection supplied by Theorem 11.1 has an orthogonal residual.
-/
theorem Vaart1998Theorem11_1ProjectionOrthogonalitySource.orthogonal_of_isL2Projection
    {Ω : Type*} [MeasurableSpace Ω]
    {P : Measure Ω} {T projection : Ω -> ℝ}
    {candidateSet : Set (Ω -> ℝ)}
    (S : Vaart1998Theorem11_1ProjectionOrthogonalitySource
      P T projection candidateSet)
    (hProjection :
      vaart1998_isL2Projection P T candidateSet projection) :
    vaart1998_l2OrthogonalToSpace P T projection candidateSet :=
  (S.projection_iff_orthogonal.1 hProjection).2

/--
Theorem 11.1 uniqueness source: any two projections onto the same linear
space are almost surely equal.
-/
structure Vaart1998Theorem11_1ProjectionUniquenessSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (T projection₁ projection₂ : Ω -> ℝ)
    (candidateSet : Set (Ω -> ℝ)) where
  /-- The first candidate is an L2 projection. -/
  first_isL2Projection :
    vaart1998_isL2Projection P T candidateSet projection₁
  /-- The second candidate is an L2 projection. -/
  second_isL2Projection :
    vaart1998_isL2Projection P T candidateSet projection₂
  /-- The theorem's a.s. uniqueness conclusion. -/
  projections_ae_eq : projection₁ =ᵐ[P] projection₂

/--
Any two L2 projections supplied by Theorem 11.1 are equal a.s.
-/
theorem Vaart1998Theorem11_1ProjectionUniquenessSource.projections_eq_ae
    {Ω : Type*} [MeasurableSpace Ω]
    {P : Measure Ω} {T projection₁ projection₂ : Ω -> ℝ}
    {candidateSet : Set (Ω -> ℝ)}
    (S : Vaart1998Theorem11_1ProjectionUniquenessSource
      P T projection₁ projection₂ candidateSet) :
    projection₁ =ᵐ[P] projection₂ :=
  S.projections_ae_eq

/--
The constant-containing consequences in Theorem 11.1: equal expectations and
zero covariance between the residual and every candidate-space member.
-/
structure Vaart1998Theorem11_1ProjectionConstantsSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (T projection : Ω -> ℝ)
    (candidateSet : Set (Ω -> ℝ)) where
  /-- The candidate set is the linear space from the theorem. -/
  linearSpace : Vaart1998ProjectionLinearSpaceSource candidateSet
  /-- The candidate space contains all constant variables. -/
  constants_mem : ∀ c : ℝ, (fun _ : Ω => c) ∈ candidateSet
  /-- The proposed projection is an L2 projection. -/
  projection_isL2Projection :
    vaart1998_isL2Projection P T candidateSet projection
  /-- Constants force equal expectations. -/
  expectation_eq :
    vaart1998_projectionExpectation P T =
      vaart1998_projectionExpectation P projection
  /-- The residual is uncorrelated with every candidate-space member. -/
  covariance_residual_eq_zero :
    ∀ S ∈ candidateSet,
      vaart1998_projectionCovariance P
        (vaart1998_l2Residual T projection) S = 0

/--
The expectation equality conclusion from the constant-containing part of
Theorem 11.1.
-/
theorem Vaart1998Theorem11_1ProjectionConstantsSource.expectation_eq_projection
    {Ω : Type*} [MeasurableSpace Ω]
    {P : Measure Ω} {T projection : Ω -> ℝ}
    {candidateSet : Set (Ω -> ℝ)}
    (S : Vaart1998Theorem11_1ProjectionConstantsSource
      P T projection candidateSet) :
    vaart1998_projectionExpectation P T =
      vaart1998_projectionExpectation P projection :=
  S.expectation_eq

/--
The covariance-zero conclusion from the constant-containing part of
Theorem 11.1.
-/
theorem Vaart1998Theorem11_1ProjectionConstantsSource.covariance_residual_zero
    {Ω : Type*} [MeasurableSpace Ω]
    {P : Measure Ω} {T projection : Ω -> ℝ}
    {candidateSet : Set (Ω -> ℝ)}
    (S : Vaart1998Theorem11_1ProjectionConstantsSource
      P T projection candidateSet)
    (U : Ω -> ℝ) (hU : U ∈ candidateSet) :
    vaart1998_projectionCovariance P
      (vaart1998_l2Residual T projection) U = 0 :=
  S.covariance_residual_eq_zero U hU

/--
Projection source for a sequence of statistics and spaces, as used in
Theorem 11.2.
-/
structure Vaart1998ProjectionSequenceSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P : ℕ -> Measure Ω) (statistic projection : ℕ -> Ω -> ℝ)
    (candidateSet : ℕ -> Set (Ω -> ℝ)) where
  /-- Each candidate set is a linear space. -/
  linearSpace :
    ∀ n, Vaart1998ProjectionLinearSpaceSource (candidateSet n)
  /-- Each candidate space contains the constants. -/
  constants_mem :
    ∀ n (c : ℝ), (fun _ : Ω => c) ∈ candidateSet n
  /-- Each `projection n` is the L2 projection of `statistic n`. -/
  projection_isL2Projection :
    ∀ n,
      vaart1998_isL2Projection (P n) (statistic n)
        (candidateSet n) (projection n)
  /-- The residual is orthogonal to the corresponding candidate space. -/
  residual_orthogonal :
    ∀ n,
      vaart1998_l2OrthogonalToSpace (P n) (statistic n)
        (projection n) (candidateSet n)

/--
Each member of a projection sequence is an L2 projection.
-/
theorem Vaart1998ProjectionSequenceSource.projection_isL2Projection_at
    {Ω : Type*} [MeasurableSpace Ω]
    {P : ℕ -> Measure Ω} {statistic projection : ℕ -> Ω -> ℝ}
    {candidateSet : ℕ -> Set (Ω -> ℝ)}
    (S : Vaart1998ProjectionSequenceSource
      P statistic projection candidateSet)
    (n : ℕ) :
    vaart1998_isL2Projection (P n) (statistic n)
      (candidateSet n) (projection n) :=
  S.projection_isL2Projection n

/--
Each projection residual in a projection sequence is orthogonal to its
candidate space.
-/
theorem Vaart1998ProjectionSequenceSource.residual_orthogonal_at
    {Ω : Type*} [MeasurableSpace Ω]
    {P : ℕ -> Measure Ω} {statistic projection : ℕ -> Ω -> ℝ}
    {candidateSet : ℕ -> Set (Ω -> ℝ)}
    (S : Vaart1998ProjectionSequenceSource
      P statistic projection candidateSet)
    (n : ℕ) :
    vaart1998_l2OrthogonalToSpace (P n) (statistic n)
      (projection n) (candidateSet n) :=
  S.residual_orthogonal n

/--
The centered-and-standardized statistic display from Theorem 11.2.
-/
def vaart1998_centeredStandardized
    {Ω : Type*} (X : ℕ -> Ω -> ℝ)
    (mean sd : ℕ -> ℝ) : ℕ -> Ω -> ℝ :=
  fun n ω => (X n ω - mean n) / sd n

/--
Theorem 11.2 source.  The analytic variance-ratio-to-second-mean argument is
kept as a certificate; downstream callers get the textbook conclusion that
the centered standardized statistic and its projection differ by `o_P(1)`,
plus Slutsky transfers in both directions.
-/
structure Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- The original statistics `T_n`. -/
  statistic : ℕ -> Ω -> ℝ
  /-- The projections `\hat S_n`. -/
  projection : ℕ -> Ω -> ℝ
  /-- The sequence of linear candidate spaces. -/
  candidateSet : ℕ -> Set (Ω -> ℝ)
  /-- Projection and orthogonality data for every `n`. -/
  projectionSequenceSource :
    Vaart1998ProjectionSequenceSource P statistic projection candidateSet
  /-- Means of the original statistics. -/
  meanStatistic : ℕ -> ℝ
  /-- Means of the projections. -/
  meanProjection : ℕ -> ℝ
  /-- Standard deviations of the original statistics. -/
  sdStatistic : ℕ -> ℝ
  /-- Standard deviations of the projections. -/
  sdProjection : ℕ -> ℝ
  /-- Variances of the original statistics. -/
  varianceStatistic : ℕ -> ℝ
  /-- Variances of the projections. -/
  varianceProjection : ℕ -> ℝ
  /-- The variance-ratio hypothesis from the theorem. -/
  varianceRatio_tendsto_one :
    Tendsto
      (fun n : ℕ => varianceStatistic n / varianceProjection n)
      atTop (𝓝 1)
  /-- The displayed standardized statistic. -/
  standardizedStatistic : ℕ -> Ω -> ℝ
  /-- The displayed standardized projection. -/
  standardizedProjection : ℕ -> Ω -> ℝ
  /-- The difference between the two displayed standardized variables. -/
  standardizedDifference : ℕ -> Ω -> ℝ
  /-- Identification of the standardized statistic display. -/
  standardizedStatistic_eq :
    standardizedStatistic =
      vaart1998_centeredStandardized statistic meanStatistic sdStatistic
  /-- Identification of the standardized projection display. -/
  standardizedProjection_eq :
    standardizedProjection =
      vaart1998_centeredStandardized projection meanProjection sdProjection
  /-- Identification of the difference display. -/
  standardizedDifference_eq :
    ∀ n ω,
      standardizedDifference n ω =
        standardizedStatistic n ω - standardizedProjection n ω
  /-- Theorem 11.2 conclusion: the standardized difference is `o_P(1)`. -/
  standardizedDifference_convergesInProbability :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      standardizedDifference
  /-- Candidate limit statistic for distributional transfers. -/
  limitStatistic : ΩLimit -> ℝ
  /-- Known limit law for the standardized projections. -/
  projection_tendstoInDistribution :
    TendstoInDistribution standardizedProjection atTop
      limitStatistic P LimitLaw
  /-- Slutsky transfer from projection limit to statistic limit. -/
  slutsky_projection_to_statistic :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      standardizedDifference ->
    TendstoInDistribution standardizedProjection atTop
      limitStatistic P LimitLaw ->
    TendstoInDistribution standardizedStatistic atTop
      limitStatistic P LimitLaw
  /-- Reverse Slutsky transfer, matching the textbook "and vice versa" use. -/
  slutsky_statistic_to_projection :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      standardizedDifference ->
    TendstoInDistribution standardizedStatistic atTop
      limitStatistic P LimitLaw ->
    TendstoInDistribution standardizedProjection atTop
      limitStatistic P LimitLaw

/--
The variance-ratio hypothesis carried by a Theorem 11.2 source.
-/
theorem Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.varianceRatio
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource
      P LimitLaw) :
    Tendsto
      (fun n : ℕ => S.varianceStatistic n / S.varianceProjection n)
      atTop (𝓝 1) :=
  S.varianceRatio_tendsto_one

/--
Theorem 11.2 standardized-difference conclusion.
-/
theorem Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.standardizedDifference_oP
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource
      P LimitLaw) :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      S.standardizedDifference :=
  S.standardizedDifference_convergesInProbability

/--
The standardized-difference display from Theorem 11.2.
-/
theorem Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.standardizedDifference_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource
      P LimitLaw)
    (n : ℕ) (ω : Ω) :
    S.standardizedDifference n ω =
      S.standardizedStatistic n ω - S.standardizedProjection n ω :=
  S.standardizedDifference_eq n ω

/--
If the standardized projections converge in distribution, then so do the
standardized statistics.
-/
theorem Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.statistic_tendstoInDistribution
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource
      P LimitLaw) :
    TendstoInDistribution S.standardizedStatistic atTop
      S.limitStatistic P LimitLaw :=
  S.slutsky_projection_to_statistic
    S.standardizedDifference_convergesInProbability
    S.projection_tendstoInDistribution

/--
If a caller has a limit theorem for the standardized statistic, the same
`o_P(1)` display transfers it back to the standardized projection.
-/
theorem Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.projection_tendstoInDistribution_of_statistic
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource
      P LimitLaw)
    (hStatistic :
      TendstoInDistribution S.standardizedStatistic atTop
        S.limitStatistic P LimitLaw) :
    TendstoInDistribution S.standardizedProjection atTop
      S.limitStatistic P LimitLaw :=
  S.slutsky_statistic_to_projection
    S.standardizedDifference_convergesInProbability hStatistic

/--
A function of the conditioning variable, the Chapter 11 display `g(Y)`.
-/
def vaart1998_functionOf
    {Ω 𝒴 : Type*} (Y : Ω -> 𝒴) (g : 𝒴 -> ℝ) : Ω -> ℝ :=
  fun ω => g (Y ω)

/--
The projection class generated by a conditioning variable: all variables of
the form `g(Y)`.
-/
def vaart1998_conditioningCandidateSet
    {Ω 𝒴 : Type*} (Y : Ω -> 𝒴) : Set (Ω -> ℝ) :=
  {S | ∃ g : 𝒴 -> ℝ, S = vaart1998_functionOf Y g}

/--
Each displayed function `g(Y)` belongs to the conditioning candidate set.
-/
theorem vaart1998_functionOf_mem_conditioningCandidateSet
    {Ω 𝒴 : Type*} (Y : Ω -> 𝒴) (g : 𝒴 -> ℝ) :
    vaart1998_functionOf Y g ∈
      vaart1998_conditioningCandidateSet Y :=
  ⟨g, rfl⟩

/--
The conditioning candidate set contains the zero variable.
-/
theorem vaart1998_conditioningCandidateSet_zero_mem
    {Ω 𝒴 : Type*} (Y : Ω -> 𝒴) :
    (fun _ : Ω => 0) ∈ vaart1998_conditioningCandidateSet Y :=
  ⟨fun _ : 𝒴 => 0, rfl⟩

/--
The conditioning candidate set is closed under addition.
-/
theorem vaart1998_conditioningCandidateSet_add_mem
    {Ω 𝒴 : Type*} {Y : Ω -> 𝒴} {S U : Ω -> ℝ}
    (hS : S ∈ vaart1998_conditioningCandidateSet Y)
    (hU : U ∈ vaart1998_conditioningCandidateSet Y) :
    (fun ω => S ω + U ω) ∈ vaart1998_conditioningCandidateSet Y := by
  rcases hS with ⟨g, rfl⟩
  rcases hU with ⟨h, rfl⟩
  refine ⟨fun y => g y + h y, ?_⟩
  ext ω
  simp [vaart1998_functionOf]

/--
The conditioning candidate set is closed under scalar multiplication.
-/
theorem vaart1998_conditioningCandidateSet_smul_mem
    {Ω 𝒴 : Type*} {Y : Ω -> 𝒴} (a : ℝ) {S : Ω -> ℝ}
    (hS : S ∈ vaart1998_conditioningCandidateSet Y) :
    (fun ω => a * S ω) ∈ vaart1998_conditioningCandidateSet Y := by
  rcases hS with ⟨g, rfl⟩
  refine ⟨fun y => a * g y, ?_⟩
  ext ω
  simp [vaart1998_functionOf]

/--
Chapter 11.2 source: conditional expectation as the L2 projection onto
functions of the conditioning variable.

The measurable/integrability side conditions are left as fields so callers can
instantiate them with the local conditional-expectation API they are using.
-/
structure Vaart1998ConditionalExpectationProjectionSource
    {Ω 𝒴 : Type*} [MeasurableSpace Ω] [MeasurableSpace 𝒴]
    (P : Measure Ω) (T : Ω -> ℝ) (Y : Ω -> 𝒴) where
  /-- The conditional expectation random variable. -/
  conditionalExpectation : Ω -> ℝ
  /-- A version of the conditional mean as a function of `Y`. -/
  conditionalMean : 𝒴 -> ℝ
  /-- The conditional expectation is represented as `g₀(Y)`. -/
  conditionalExpectation_eq_functionOf :
    conditionalExpectation = vaart1998_functionOf Y conditionalMean
  /-- The source candidate set, usually all square-integrable functions `g(Y)`. -/
  candidateSet : Set (Ω -> ℝ)
  /-- Identification with the displayed class of functions of `Y`. -/
  candidateSet_eq :
    candidateSet = vaart1998_conditioningCandidateSet Y
  /-- Linear-space data for the projection theorem. -/
  linearSpace : Vaart1998ProjectionLinearSpaceSource candidateSet
  /-- The conditional expectation is the L2 projection of `T`. -/
  projection_isL2Projection :
    vaart1998_isL2Projection P T candidateSet conditionalExpectation
  /-- The orthogonality characterization against every displayed `g(Y)`. -/
  orthogonal_to_functionOf :
    ∀ g : 𝒴 -> ℝ,
      vaart1998_l2Inner P
        (vaart1998_l2Residual T conditionalExpectation)
        (vaart1998_functionOf Y g) = 0
  /-- Uniqueness up to a.s. equality for any other version satisfying the same display. -/
  ae_eq_of_orthogonal :
    ∀ Z : Ω -> ℝ,
      Z ∈ candidateSet ->
      (∀ g : 𝒴 -> ℝ,
        vaart1998_l2Inner P
          (vaart1998_l2Residual T Z)
          (vaart1998_functionOf Y g) = 0) ->
      Z =ᵐ[P] conditionalExpectation

/--
The conditional expectation source supplies an L2 projection.
-/
theorem Vaart1998ConditionalExpectationProjectionSource.isL2Projection
    {Ω 𝒴 : Type*} [MeasurableSpace Ω] [MeasurableSpace 𝒴]
    {P : Measure Ω} {T : Ω -> ℝ} {Y : Ω -> 𝒴}
    (S : Vaart1998ConditionalExpectationProjectionSource P T Y) :
    vaart1998_isL2Projection P T S.candidateSet
      S.conditionalExpectation :=
  S.projection_isL2Projection

/--
The conditional expectation source supplies the orthogonality relation
`E (T - E(T | Y)) g(Y) = 0`.
-/
theorem Vaart1998ConditionalExpectationProjectionSource.orthogonal_to_functionOf'
    {Ω 𝒴 : Type*} [MeasurableSpace Ω] [MeasurableSpace 𝒴]
    {P : Measure Ω} {T : Ω -> ℝ} {Y : Ω -> 𝒴}
    (S : Vaart1998ConditionalExpectationProjectionSource P T Y)
    (g : 𝒴 -> ℝ) :
    vaart1998_l2Inner P
      (vaart1998_l2Residual T S.conditionalExpectation)
      (vaart1998_functionOf Y g) = 0 :=
  S.orthogonal_to_functionOf g

/--
The displayed `g₀(Y)` representation of a conditional expectation source.
-/
theorem Vaart1998ConditionalExpectationProjectionSource.functionOf_display
    {Ω 𝒴 : Type*} [MeasurableSpace Ω] [MeasurableSpace 𝒴]
    {P : Measure Ω} {T : Ω -> ℝ} {Y : Ω -> 𝒴}
    (S : Vaart1998ConditionalExpectationProjectionSource P T Y) :
    S.conditionalExpectation =
      vaart1998_functionOf Y S.conditionalMean :=
  S.conditionalExpectation_eq_functionOf

/--
Uniqueness of conditional expectation versions satisfying the same
orthogonality display.
-/
theorem Vaart1998ConditionalExpectationProjectionSource.ae_eq_of_orthogonal'
    {Ω 𝒴 : Type*} [MeasurableSpace Ω] [MeasurableSpace 𝒴]
    {P : Measure Ω} {T : Ω -> ℝ} {Y : Ω -> 𝒴}
    (S : Vaart1998ConditionalExpectationProjectionSource P T Y)
    {Z : Ω -> ℝ} (hZ : Z ∈ S.candidateSet)
    (hOrthogonal :
      ∀ g : 𝒴 -> ℝ,
        vaart1998_l2Inner P
          (vaart1998_l2Residual T Z)
          (vaart1998_functionOf Y g) = 0) :
    Z =ᵐ[P] S.conditionalExpectation :=
  S.ae_eq_of_orthogonal Z hZ hOrthogonal

/--
Chapter 11.2 basic conditional-expectation rules used by the examples after
Theorem 11.1.
-/
structure Vaart1998ConditionalExpectationRulesSource
    {Ω YSpace ZSpace : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) where
  /-- Conditional expectation given a `YSpace`-valued variable. -/
  conditionalExpectationY :
    (Ω -> ℝ) -> (Ω -> YSpace) -> Ω -> ℝ
  /-- Conditional expectation given the pair `(Y, Z)`. -/
  conditionalExpectationYZ :
    (Ω -> ℝ) -> (Ω -> YSpace × ZSpace) -> Ω -> ℝ
  /-- `E E(X | Y) = E X`. -/
  expectation_conditionalExpectation :
    ∀ (T : Ω -> ℝ) (Y : Ω -> YSpace),
      vaart1998_projectionExpectation P
        (conditionalExpectationY T Y) =
      vaart1998_projectionExpectation P T
  /-- If `T = f(Y)`, then `E(T | Y) = T` a.s. -/
  functionOf_self :
    ∀ (Y : Ω -> YSpace) (f : YSpace -> ℝ),
      conditionalExpectationY (vaart1998_functionOf Y f) Y
        =ᵐ[P] vaart1998_functionOf Y f
  /-- Independent conditioning variables collapse to the unconditional mean. -/
  independent_eq_constant :
    ∀ (T : Ω -> ℝ) (Y : Ω -> YSpace),
      (independentDisplay : Prop) ->
      independentDisplay ->
      conditionalExpectationY T Y
        =ᵐ[P] fun _ : Ω => vaart1998_projectionExpectation P T
  /-- Pull out a factor that is a function of the conditioning variable. -/
  pullout_functionOf :
    ∀ (T : Ω -> ℝ) (Y : Ω -> YSpace) (f : YSpace -> ℝ),
      conditionalExpectationY
          (fun ω => vaart1998_functionOf Y f ω * T ω) Y
        =ᵐ[P]
          fun ω =>
            vaart1998_functionOf Y f ω *
              conditionalExpectationY T Y ω
  /-- Projection can be carried out in stages. -/
  tower_property :
    ∀ (T : Ω -> ℝ) (Y : Ω -> YSpace) (Z : Ω -> ZSpace),
      conditionalExpectationY
          (conditionalExpectationYZ T (fun ω => (Y ω, Z ω))) Y
        =ᵐ[P] conditionalExpectationY T Y

/--
The expectation-of-conditional-expectation rule.
-/
theorem Vaart1998ConditionalExpectationRulesSource.expectation_conditional
    {Ω YSpace ZSpace : Type*} [MeasurableSpace Ω]
    {P : Measure Ω}
    (S : Vaart1998ConditionalExpectationRulesSource
      (Ω := Ω) (YSpace := YSpace) (ZSpace := ZSpace) P)
    (T : Ω -> ℝ) (Y : Ω -> YSpace) :
    vaart1998_projectionExpectation P
        (S.conditionalExpectationY T Y) =
      vaart1998_projectionExpectation P T :=
  S.expectation_conditionalExpectation T Y

/--
The `T = f(Y)` conditional-expectation rule.
-/
theorem Vaart1998ConditionalExpectationRulesSource.functionOf_self_ae
    {Ω YSpace ZSpace : Type*} [MeasurableSpace Ω]
    {P : Measure Ω}
    (S : Vaart1998ConditionalExpectationRulesSource
      (Ω := Ω) (YSpace := YSpace) (ZSpace := ZSpace) P)
    (Y : Ω -> YSpace) (f : YSpace -> ℝ) :
    S.conditionalExpectationY (vaart1998_functionOf Y f) Y
      =ᵐ[P] vaart1998_functionOf Y f :=
  S.functionOf_self Y f

/--
The tower-property rule from Example 11.9.
-/
theorem Vaart1998ConditionalExpectationRulesSource.tower_property_ae
    {Ω YSpace ZSpace : Type*} [MeasurableSpace Ω]
    {P : Measure Ω}
    (S : Vaart1998ConditionalExpectationRulesSource
      (Ω := Ω) (YSpace := YSpace) (ZSpace := ZSpace) P)
    (T : Ω -> ℝ) (Y : Ω -> YSpace) (Z : Ω -> ZSpace) :
    S.conditionalExpectationY
        (S.conditionalExpectationYZ T (fun ω => (Y ω, Z ω))) Y
      =ᵐ[P] S.conditionalExpectationY T Y :=
  S.tower_property T Y Z

/--
A finite sum of one-coordinate functions, the class used in the Hájek
projection lemma.
-/
def vaart1998_sumCoordinateFunction
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [Fintype ι] [DecidableEq ι]
    (X : (i : ι) -> Ω -> 𝒳 i)
    (g : (i : ι) -> 𝒳 i -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ i, g i (X i ω)

/--
The class of finite sums `∑ᵢ gᵢ(Xᵢ)`.
-/
def vaart1998_projectionOntoSumsCandidateSet
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [Fintype ι] [DecidableEq ι]
    (X : (i : ι) -> Ω -> 𝒳 i) : Set (Ω -> ℝ) :=
  {S | ∃ g : (i : ι) -> 𝒳 i -> ℝ,
    S = vaart1998_sumCoordinateFunction X g}

/--
Each displayed coordinate sum belongs to the projection-onto-sums candidate
set.
-/
theorem vaart1998_sumCoordinateFunction_mem_projectionOntoSumsCandidateSet
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [Fintype ι] [DecidableEq ι]
    (X : (i : ι) -> Ω -> 𝒳 i)
    (g : (i : ι) -> 𝒳 i -> ℝ) :
    vaart1998_sumCoordinateFunction X g ∈
      vaart1998_projectionOntoSumsCandidateSet X :=
  ⟨g, rfl⟩

/--
The Hájek projection display from Lemma 11.10:
`∑ᵢ E(T | Xᵢ) - (n - 1) E T`.
-/
def vaart1998_hajekProjection
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (conditionalOne : ι -> Ω -> ℝ) (meanT : ℝ) : Ω -> ℝ :=
  fun ω =>
    (∑ i, conditionalOne i ω) -
      ((Fintype.card ι : ℝ) - 1) * meanT

/--
The symmetric iid reduced class `∑ᵢ g(Xᵢ)` appearing after Lemma 11.10.
-/
def vaart1998_commonProjectionOntoSumsCandidateSet
    {Ω ι 𝒳 : Type*} [Fintype ι] [DecidableEq ι]
    (X : ι -> Ω -> 𝒳) : Set (Ω -> ℝ) :=
  {S | ∃ g : 𝒳 -> ℝ,
    S = fun ω => ∑ i, g (X i ω)}

/--
Lemma 11.10 source: the projection of `T` onto sums of one-coordinate
functions is the Hájek projection.
-/
structure Vaart1998Lemma11_10HajekProjectionSource
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    (P : Measure Ω) where
  /-- The target random variable `T`. -/
  statistic : Ω -> ℝ
  /-- Independent coordinate variables `Xᵢ`. -/
  coordinate : (i : ι) -> Ω -> 𝒳 i
  /-- The expectation `E T`. -/
  meanStatistic : ℝ
  /-- The one-coordinate conditional expectations `E(T | Xᵢ)`. -/
  conditionalOne : ι -> Ω -> ℝ
  /-- Versions of the one-coordinate conditional means as functions of `Xᵢ`. -/
  conditionalOneFunction : (i : ι) -> 𝒳 i -> ℝ
  /-- Each conditional expectation is represented as a function of `Xᵢ`. -/
  conditionalOne_eq_functionOf :
    ∀ i,
      conditionalOne i =
        vaart1998_functionOf (coordinate i) (conditionalOneFunction i)
  /-- The class of sums `∑ᵢ gᵢ(Xᵢ)`. -/
  candidateSet : Set (Ω -> ℝ)
  /-- Identification of the candidate set with the displayed class. -/
  candidateSet_eq :
    candidateSet = vaart1998_projectionOntoSumsCandidateSet coordinate
  /-- The displayed Hájek projection. -/
  hajekProjection : Ω -> ℝ
  /-- Formula for the Hájek projection. -/
  hajekProjection_eq :
    hajekProjection =
      vaart1998_hajekProjection conditionalOne meanStatistic
  /-- The displayed projection belongs to the candidate class. -/
  hajekProjection_mem : hajekProjection ∈ candidateSet
  /-- Orthogonality of the residual to the sums class. -/
  residual_orthogonal :
    vaart1998_l2OrthogonalToSpace P
      statistic hajekProjection candidateSet
  /-- Lemma 11.10 conclusion: the Hájek display is the L2 projection. -/
  hajekProjection_isL2Projection :
    vaart1998_isL2Projection P
      statistic candidateSet hajekProjection

/--
The formula for the Hájek projection in Lemma 11.10.
-/
theorem Vaart1998Lemma11_10HajekProjectionSource.hajekProjection_display
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_10HajekProjectionSource
      (Ω := Ω) (ι := ι) (𝒳 := 𝒳) P) :
    S.hajekProjection =
      vaart1998_hajekProjection
        (Ω := Ω) (ι := ι) S.conditionalOne S.meanStatistic :=
  S.hajekProjection_eq

/--
The Hájek projection is in the coordinate-sums candidate class.
-/
theorem Vaart1998Lemma11_10HajekProjectionSource.hajekProjection_mem_candidateSet
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_10HajekProjectionSource
      (Ω := Ω) (ι := ι) (𝒳 := 𝒳) P) :
    S.hajekProjection ∈ S.candidateSet :=
  S.hajekProjection_mem

/--
The Hájek residual is orthogonal to all finite sums `∑ᵢ gᵢ(Xᵢ)`.
-/
theorem Vaart1998Lemma11_10HajekProjectionSource.residual_orthogonal_candidateSet
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_10HajekProjectionSource
      (Ω := Ω) (ι := ι) (𝒳 := 𝒳) P) :
    vaart1998_l2OrthogonalToSpace P
      S.statistic S.hajekProjection S.candidateSet :=
  S.residual_orthogonal

/--
The L2-projection conclusion of Lemma 11.10.
-/
theorem Vaart1998Lemma11_10HajekProjectionSource.isL2Projection
    {Ω ι : Type*} {𝒳 : ι -> Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_10HajekProjectionSource
      (Ω := Ω) (ι := ι) (𝒳 := 𝒳) P) :
    vaart1998_isL2Projection P
      S.statistic S.candidateSet S.hajekProjection :=
  S.hajekProjection_isL2Projection

/--
Symmetric iid version after Lemma 11.10: the same Hájek display projects onto
the smaller common-kernel class `∑ᵢ g(Xᵢ)`.
-/
structure Vaart1998Lemma11_10SymmetricHajekProjectionSource
    {Ω ι 𝒳 : Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    (P : Measure Ω) where
  /-- The target permutation-symmetric statistic. -/
  statistic : Ω -> ℝ
  /-- Iid coordinate variables. -/
  coordinate : ι -> Ω -> 𝒳
  /-- The common one-coordinate conditional mean. -/
  commonConditionalMean : 𝒳 -> ℝ
  /-- The expectation `E T`. -/
  meanStatistic : ℝ
  /-- The displayed Hájek projection in the symmetric case. -/
  hajekProjection : Ω -> ℝ
  /-- Formula using the common conditional mean. -/
  hajekProjection_eq :
    hajekProjection =
      vaart1998_hajekProjection
        (Ω := Ω) (ι := ι)
        (fun i => vaart1998_functionOf (coordinate i) commonConditionalMean)
        meanStatistic
  /-- The reduced class `∑ᵢ g(Xᵢ)`. -/
  reducedCandidateSet : Set (Ω -> ℝ)
  /-- Identification with the displayed common-kernel class. -/
  reducedCandidateSet_eq :
    reducedCandidateSet =
      vaart1998_commonProjectionOntoSumsCandidateSet coordinate
  /-- The symmetric Hájek projection belongs to the reduced class. -/
  hajekProjection_mem : hajekProjection ∈ reducedCandidateSet
  /-- The residual is orthogonal to the reduced class. -/
  residual_orthogonal :
    vaart1998_l2OrthogonalToSpace P
      statistic hajekProjection reducedCandidateSet
  /-- Projection onto the reduced common-kernel class. -/
  hajekProjection_isL2Projection :
    vaart1998_isL2Projection P
      statistic reducedCandidateSet hajekProjection

/--
The symmetric iid Hájek projection formula.
-/
theorem Vaart1998Lemma11_10SymmetricHajekProjectionSource.hajekProjection_display
    {Ω ι 𝒳 : Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_10SymmetricHajekProjectionSource
      (Ω := Ω) (ι := ι) (𝒳 := 𝒳) P) :
    S.hajekProjection =
      vaart1998_hajekProjection
        (Ω := Ω) (ι := ι)
        (fun i =>
          vaart1998_functionOf (S.coordinate i) S.commonConditionalMean)
        S.meanStatistic :=
  S.hajekProjection_eq

/--
The symmetric iid projection conclusion onto `∑ᵢ g(Xᵢ)`.
-/
theorem Vaart1998Lemma11_10SymmetricHajekProjectionSource.isL2Projection
    {Ω ι 𝒳 : Type*}
    [MeasurableSpace Ω] [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_10SymmetricHajekProjectionSource
      (Ω := Ω) (ι := ι) (𝒳 := 𝒳) P) :
    vaart1998_isL2Projection P
      S.statistic S.reducedCandidateSet S.hajekProjection :=
  S.hajekProjection_isL2Projection

/--
Orthogonality of a single function to every member of a candidate space.
-/
def vaart1998_l2FunctionOrthogonalToSpace
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (T : Ω -> ℝ)
    (candidateSet : Set (Ω -> ℝ)) : Prop :=
  ∀ S ∈ candidateSet, vaart1998_l2Inner P T S = 0

/--
Pairwise orthogonality of a family of candidate spaces.
-/
def vaart1998_l2PairwiseOrthogonalSpaces
    {Ω ι : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) (space : Finset ι -> Set (Ω -> ℝ)) : Prop :=
  ∀ {A B : Finset ι}, A ≠ B ->
    ∀ U ∈ space A, ∀ V ∈ space B,
      vaart1998_l2Inner P U V = 0

/--
The alternating conditional-expectation formula in Lemma 11.11:
`P_A T = sum_{B subset A} (-1)^(|A|-|B|) E(T | B)`.
-/
def vaart1998_hoeffdingProjectionTerm
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (conditionalOn : Finset ι -> Ω -> ℝ)
    (A : Finset ι) : Ω -> ℝ :=
  fun ω =>
    A.powerset.sum fun B =>
      ((-1 : ℝ) ^ (A.card - B.card)) * conditionalOn B ω

/--
The zero-order Hoeffding term, represented by the unconditional mean.
-/
def vaart1998_hoeffdingZeroOrderTerm
    {Ω : Type*} (meanT : ℝ) : Ω -> ℝ :=
  fun _ => meanT

/--
The first-order Hoeffding display `E(T | X_i) - E T`.
-/
def vaart1998_hoeffdingFirstOrderTerm
    {Ω ι : Type*} [DecidableEq ι]
    (conditionalOn : Finset ι -> Ω -> ℝ) (meanT : ℝ)
    (i : ι) : Ω -> ℝ :=
  fun ω => conditionalOn ({i} : Finset ι) ω - meanT

/--
The second-order Hoeffding display
`E(T | X_i, X_j) - E(T | X_i) - E(T | X_j) + E T`.
-/
def vaart1998_hoeffdingSecondOrderTerm
    {Ω ι : Type*} [DecidableEq ι]
    (conditionalOn : Finset ι -> Ω -> ℝ) (meanT : ℝ)
    (i j : ι) : Ω -> ℝ :=
  fun ω =>
    conditionalOn (insert j ({i} : Finset ι)) ω -
      conditionalOn ({i} : Finset ι) ω -
      conditionalOn ({j} : Finset ι) ω + meanT

/--
Projection onto the sum of Hoeffding spaces up to order `r`.
-/
def vaart1998_hoeffdingProjectionUpToOrder
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (projectionTerm : Finset ι -> Ω -> ℝ) (r : ℕ) :
    Ω -> ℝ :=
  fun ω =>
    ∑ A : Finset ι,
      if A.card ≤ r then projectionTerm A ω else 0

/--
The full finite Hoeffding expansion display.
-/
def vaart1998_hoeffdingFullExpansion
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (projectionTerm : Finset ι -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ A : Finset ι, projectionTerm A ω

/--
The symmetric-order inner sum.  In the iid symmetric case this is the
`U`-statistic of order `r` mentioned at the end of Chapter 11.
-/
def vaart1998_symmetricHoeffdingOrderSum
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (orderTerm : ℕ -> Finset ι -> Ω -> ℝ) (r : ℕ) :
    Ω -> ℝ :=
  fun ω =>
    ∑ A : Finset ι,
      if A.card = r then orderTerm r A ω else 0

/--
The symmetric Hoeffding decomposition display
`T = sum_r sum_{|A|=r} g_r(X_i : i in A)`.
-/
def vaart1998_symmetricHoeffdingExpansion
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (orderTerm : ℕ -> Finset ι -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω =>
    (Finset.range (Fintype.card ι + 1)).sum fun r =>
      vaart1998_symmetricHoeffdingOrderSum orderTerm r ω

/--
Lemma 11.11 source: the Hoeffding projection onto `H_A` is the alternating
sum of conditional expectations over subsets of `A`.
-/
structure Vaart1998Lemma11_11HoeffdingProjectionSource
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    (P : Measure Ω) where
  /-- The target random variable `T`. -/
  statistic : Ω -> ℝ
  /-- Conditional expectation displays `E(T | X_i : i in A)`. -/
  conditionalOn : Finset ι -> Ω -> ℝ
  /-- Hoeffding spaces `H_A`. -/
  hoeffdingSpace : Finset ι -> Set (Ω -> ℝ)
  /-- Projection terms `P_A T`. -/
  projectionTerm : Finset ι -> Ω -> ℝ
  /-- The alternating formula from Lemma 11.11. -/
  projectionTerm_eq_alternating :
    ∀ A,
      projectionTerm A =
        vaart1998_hoeffdingProjectionTerm conditionalOn A
  /-- The projection term belongs to `H_A`. -/
  projectionTerm_mem :
    ∀ A, projectionTerm A ∈ hoeffdingSpace A
  /-- The spaces `H_A` are pairwise orthogonal. -/
  pairwise_orthogonal_spaces :
    vaart1998_l2PairwiseOrthogonalSpaces P hoeffdingSpace
  /-- Each `P_A T` is the L2 projection of `T` onto `H_A`. -/
  projectionTerm_isL2Projection :
    ∀ A,
      vaart1998_isL2Projection P
        statistic (hoeffdingSpace A) (projectionTerm A)
  /-- Predicate for the tower/intersection rule
      `E(E(T | A) | B) = E(T | A ∩ B)`. -/
  conditionalIntersectionRule : Finset ι -> Finset ι -> Prop
  /-- Tower/intersection rule used in the proof. -/
  conditional_intersection_rule :
    ∀ A B, conditionalIntersectionRule A B
  /-- Predicate for the proof's binomial cancellation step. -/
  lowerConditionalZero : Finset ι -> Finset ι -> Prop
  /-- The proof's binomial cancellation step for strict lower conditionings. -/
  lower_conditional_zero :
    ∀ (A C : Finset ι),
      C ⊆ A ->
      C.card < A.card ->
      lowerConditionalZero A C
  /-- Orthogonality of `T` to all `H_B`, `B ⊆ A`, forces `E(T | A)=0`. -/
  conditional_zero_of_orthogonal_subspaces :
    ∀ (A : Finset ι),
      (∀ B, B ⊆ A ->
        vaart1998_l2FunctionOrthogonalToSpace P
          statistic (hoeffdingSpace B)) ->
      conditionalOn A =ᵐ[P] 0
  /-- Predicate saying the sum of `H_B`, `B ⊆ A`, contains all
      square-integrable functions of the coordinate block indexed by `A`. -/
  blockFunctionsContained : Finset ι -> Prop
  /-- The final containment assertion of Lemma 11.11. -/
  subsetSpacesContainBlockFunctions :
    ∀ A, blockFunctionsContained A

/--
The alternating formula for `P_A T` in Lemma 11.11.
-/
theorem Vaart1998Lemma11_11HoeffdingProjectionSource.projectionTerm_display
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_11HoeffdingProjectionSource
      P)
    (A : Finset ι) :
    S.projectionTerm A =
      vaart1998_hoeffdingProjectionTerm
        (Ω := Ω) (ι := ι) S.conditionalOn A :=
  S.projectionTerm_eq_alternating A

/--
The projection term `P_A T` belongs to `H_A`.
-/
theorem Vaart1998Lemma11_11HoeffdingProjectionSource.projectionTerm_mem_space
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_11HoeffdingProjectionSource
      P)
    (A : Finset ι) :
    S.projectionTerm A ∈ S.hoeffdingSpace A :=
  S.projectionTerm_mem A

/--
The L2-projection conclusion of Lemma 11.11.
-/
theorem Vaart1998Lemma11_11HoeffdingProjectionSource.isL2Projection
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_11HoeffdingProjectionSource
      P)
    (A : Finset ι) :
    vaart1998_isL2Projection P
      S.statistic (S.hoeffdingSpace A) (S.projectionTerm A) :=
  S.projectionTerm_isL2Projection A

/--
The pairwise orthogonality of the Hoeffding spaces `H_A`.
-/
theorem Vaart1998Lemma11_11HoeffdingProjectionSource.pairwise_orthogonal
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_11HoeffdingProjectionSource
      (Ω := Ω) (ι := ι) P) :
    vaart1998_l2PairwiseOrthogonalSpaces
      (Ω := Ω) (ι := ι) P S.hoeffdingSpace :=
  S.pairwise_orthogonal_spaces

/--
The second assertion of Lemma 11.11: orthogonality to all lower Hoeffding
spaces under `A` forces the conditional expectation on `A` to vanish.
-/
theorem Vaart1998Lemma11_11HoeffdingProjectionSource.conditional_zero
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_11HoeffdingProjectionSource
      (Ω := Ω) (ι := ι) P)
    (A : Finset ι)
    (hOrthogonal :
      ∀ B, B ⊆ A ->
        vaart1998_l2FunctionOrthogonalToSpace P
          S.statistic (S.hoeffdingSpace B)) :
    S.conditionalOn A =ᵐ[P] 0 :=
  S.conditional_zero_of_orthogonal_subspaces A hOrthogonal

/--
The final containment assertion in Lemma 11.11.
-/
theorem Vaart1998Lemma11_11HoeffdingProjectionSource.contains_block_functions
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998Lemma11_11HoeffdingProjectionSource
      (Ω := Ω) (ι := ι) P)
    (A : Finset ι) :
    S.blockFunctionsContained A :=
  S.subsetSpacesContainBlockFunctions A

/--
Source for the projection onto the sum of all Hoeffding spaces up to order
`r`, using pairwise orthogonality to sum the individual projections.
-/
structure Vaart1998HoeffdingOrderProjectionSource
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    (P : Measure Ω) where
  /-- Lemma 11.11 projection data. -/
  lemma11_11Source :
    Vaart1998Lemma11_11HoeffdingProjectionSource
      (Ω := Ω) (ι := ι) P
  /-- The projection onto the sum of spaces of order at most `r`. -/
  orderProjection : ℕ -> Ω -> ℝ
  /-- Formula as a sum of individual Hoeffding projections. -/
  orderProjection_eq :
    ∀ r,
      orderProjection r =
        vaart1998_hoeffdingProjectionUpToOrder
          (Ω := Ω) (ι := ι)
          lemma11_11Source.projectionTerm r
  /-- Candidate space for all terms of order at most `r`. -/
  orderSpace : ℕ -> Set (Ω -> ℝ)
  /-- The order-`r` display is the L2 projection onto that summed space. -/
  orderProjection_isL2Projection :
    ∀ r,
      vaart1998_isL2Projection P
        lemma11_11Source.statistic (orderSpace r) (orderProjection r)
  /-- Predicate identifying the order-one Hoeffding projection with Hájek's display. -/
  firstOrderHajekBridge : (Ω -> ℝ) -> Prop
  /-- The projection onto constants plus first-order terms is the Hájek projection. -/
  firstOrder_eq_hajek :
    ∀ hajekProjection : Ω -> ℝ, firstOrderHajekBridge hajekProjection

/--
Display of the projection onto Hoeffding spaces up to order `r`.
-/
theorem Vaart1998HoeffdingOrderProjectionSource.orderProjection_display
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998HoeffdingOrderProjectionSource
      (Ω := Ω) (ι := ι) P)
    (r : ℕ) :
    S.orderProjection r =
      vaart1998_hoeffdingProjectionUpToOrder
        (Ω := Ω) (ι := ι)
        S.lemma11_11Source.projectionTerm r :=
  S.orderProjection_eq r

/--
Projection onto the sum of Hoeffding spaces up to order `r`.
-/
theorem Vaart1998HoeffdingOrderProjectionSource.orderProjection_isL2Projection_at
    {Ω ι : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι]
    {P : Measure Ω}
    (S : Vaart1998HoeffdingOrderProjectionSource
      (Ω := Ω) (ι := ι) P)
    (r : ℕ) :
    vaart1998_isL2Projection P
      S.lemma11_11Source.statistic (S.orderSpace r)
      (S.orderProjection r) :=
  S.orderProjection_isL2Projection r

/--
Symmetric iid Hoeffding decomposition source and bridge to Chapter 12
`U`-statistics.
-/
structure Vaart1998SymmetricHoeffdingUStatisticBridgeSource
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    (statistic : Ω -> ℝ) where
  /-- Symmetric order kernels displayed over subsets of a fixed order. -/
  orderTerm : ℕ -> Finset ι -> Ω -> ℝ
  /-- The order-`r` inner sum. -/
  orderStatistic : ℕ -> Ω -> ℝ
  /-- Identification with the finite subset sum of cardinality `r`. -/
  orderStatistic_eq :
    ∀ r,
      orderStatistic r =
        vaart1998_symmetricHoeffdingOrderSum
          (Ω := Ω) (ι := ι) orderTerm r
  /-- The full Hoeffding expansion. -/
  fullExpansion_eq :
    statistic =
      vaart1998_symmetricHoeffdingExpansion
        (Ω := Ω) (ι := ι) orderTerm
  /-- Predicate supplied by the Chapter 12 lane: `U`-statistic of order `r`. -/
  uStatisticOfOrder : ℕ -> (Ω -> ℝ) -> Prop
  /-- Each inner Hoeffding sum is a `U`-statistic of its order. -/
  orderStatistic_uStatistic :
    ∀ r, uStatisticOfOrder r (orderStatistic r)
  /-- Predicate for a degenerate kernel of order `r`. -/
  degenerateKernelOfOrder : ℕ -> (Finset ι -> Ω -> ℝ) -> Prop
  /-- The kernels in the Hoeffding decomposition are degenerate. -/
  orderKernel_degenerate :
    ∀ r, degenerateKernelOfOrder r (orderTerm r)
  /-- Orthogonality yields the variance decomposition in the textbook display. -/
  varianceDecomposition :
    Prop

/--
The symmetric iid Hoeffding expansion display.
-/
theorem Vaart1998SymmetricHoeffdingUStatisticBridgeSource.fullExpansion
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    {statistic : Ω -> ℝ}
    (S : Vaart1998SymmetricHoeffdingUStatisticBridgeSource
      (Ω := Ω) (ι := ι) statistic) :
    statistic =
      vaart1998_symmetricHoeffdingExpansion
        (Ω := Ω) (ι := ι) S.orderTerm :=
  S.fullExpansion_eq

/--
Each symmetric Hoeffding order term is a Chapter 12 `U`-statistic.
-/
theorem Vaart1998SymmetricHoeffdingUStatisticBridgeSource.order_uStatistic
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    {statistic : Ω -> ℝ}
    (S : Vaart1998SymmetricHoeffdingUStatisticBridgeSource
      (Ω := Ω) (ι := ι) statistic)
    (r : ℕ) :
    S.uStatisticOfOrder r (S.orderStatistic r) :=
  S.orderStatistic_uStatistic r

/--
The degeneracy handoff for the Hoeffding kernels.
-/
theorem Vaart1998SymmetricHoeffdingUStatisticBridgeSource.kernel_degenerate
    {Ω ι : Type*} [Fintype ι] [DecidableEq ι]
    {statistic : Ω -> ℝ}
    (S : Vaart1998SymmetricHoeffdingUStatisticBridgeSource
      (Ω := Ω) (ι := ι) statistic)
    (r : ℕ) :
    S.degenerateKernelOfOrder r (S.orderTerm r) :=
  S.orderKernel_degenerate r

end AsymptoticStatistics
end StatInference
