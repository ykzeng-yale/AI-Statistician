import StatInference.AsymptoticStatistics.UStatistics

/-!
# van der Vaart 1998 Chapter 13 rank, sign, and permutation interfaces

This module opens the Chapter 13 lane.  It records finite-rank displays,
simple linear rank statistics, the Wilcoxon/Mann-Whitney bridge to the
Chapter 12 two-sample `U`-statistic interface, signed-rank displays, and the
permutation-test source handoffs from Section 13.5.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal ProbabilityTheory Topology

/--
Finite average of a real family.  This is the display used for `\bar c_N` and
`\bar a_N` in Lemma 13.1.
-/
def vaart1998_finiteAverage
    {ι : Type*} [Fintype ι] (x : ι -> ℝ) : ℝ :=
  (Fintype.card ι : ℝ)⁻¹ * ∑ i : ι, x i

/--
The uprank display `R_i = sum_j 1{X_j <= X_i}`.  The indicator is supplied by
the caller so the interface can cover ordinary ranks, absolute ranks, and
pooled ranks without committing to a concrete order API.
-/
def vaart1998_rankFromLeIndicator
    {Ω ι κ : Type*} [Fintype κ]
    (leIndicator : κ -> ι -> Ω -> ℝ) (i : ι) : Ω -> ℝ :=
  fun ω => ∑ j : κ, leIndicator j i ω

/--
Simple linear rank statistic `sum_i c_i a_{R_i}`.
-/
def vaart1998_simpleLinearRankStatistic
    {Ω ι ρ : Type*} [Fintype ι]
    (coefficient : ι -> ℝ) (rankIndex : ι -> Ω -> ρ)
    (score : ρ -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ i : ι, coefficient i * score (rankIndex i ω)

/--
Lemma 13.1 expectation display for a simple linear rank statistic:
`N * \bar c_N * \bar a_N`.
-/
def vaart1998_simpleLinearRankExpectationDisplay
    {ι ρ : Type*} [Fintype ι] [Fintype ρ]
    (coefficient : ι -> ℝ) (score : ρ -> ℝ) : ℝ :=
  (Fintype.card ι : ℝ) *
    vaart1998_finiteAverage coefficient *
      vaart1998_finiteAverage score

/--
Lemma 13.1 variance display:
`(N - 1)^{-1} sum_i (c_i - \bar c)^2 sum_j (a_j - \bar a)^2`.
-/
def vaart1998_simpleLinearRankVarianceDisplay
    {ι ρ : Type*} [Fintype ι] [Fintype ρ]
    (coefficient : ι -> ℝ) (score : ρ -> ℝ) : ℝ :=
  ((Fintype.card ι : ℝ) - 1)⁻¹ *
    (∑ i : ι,
      (coefficient i - vaart1998_finiteAverage coefficient) ^ 2) *
    (∑ r : ρ,
      (score r - vaart1998_finiteAverage score) ^ 2)

/--
Finite-sample source for Lemma 13.1 rank-vector bookkeeping.
-/
structure Vaart1998RankVectorFiniteSource
    {Ω ι : Type*} [MeasurableSpace Ω] [Fintype ι]
    (P : Measure Ω) where
  /-- Rank display for each observation. -/
  rank : ι -> Ω -> ℝ
  /-- Indicator display used to compute the rank. -/
  leIndicator : ι -> ι -> Ω -> ℝ
  /-- Identification with the uprank display. -/
  rank_eq :
    rank =
      vaart1998_rankFromLeIndicator leIndicator
  /-- The continuous-null/no-ties side condition. -/
  noTiesContinuousNull : Prop
  /-- Independence of ranks and order statistics under the null. -/
  orderStatsIndependentUnderNull : Prop
  /-- Uniformity of the rank vector on permutations under the null. -/
  rankVectorUniformUnderNull : Prop
  /-- Distribution-free conclusion for rank statistics under the null. -/
  distributionFreeUnderNull : Prop
  /-- Source proof of the no-ties side condition. -/
  noTiesContinuousNull_proof :
    noTiesContinuousNull
  /-- Source proof of independence of order statistics and ranks. -/
  orderStatsIndependentUnderNull_proof :
    orderStatsIndependentUnderNull
  /-- Source proof of uniform rank-vector law. -/
  rankVectorUniformUnderNull_proof :
    rankVectorUniformUnderNull
  /-- Source proof of the distribution-free conclusion. -/
  distributionFreeUnderNull_proof :
    distributionFreeUnderNull

/--
The finite-rank display `R_i = sum_j 1{X_j <= X_i}`.
-/
theorem Vaart1998RankVectorFiniteSource.rank_display
    {Ω ι : Type*} [MeasurableSpace Ω] [Fintype ι]
    {P : Measure Ω}
    (S : Vaart1998RankVectorFiniteSource (Ω := Ω) (ι := ι) P) :
    S.rank =
      vaart1998_rankFromLeIndicator S.leIndicator :=
  S.rank_eq

/--
Lemma 13.1(iv): the rank vector is uniform on permutations under the null.
-/
theorem Vaart1998RankVectorFiniteSource.rank_vector_uniform
    {Ω ι : Type*} [MeasurableSpace Ω] [Fintype ι]
    {P : Measure Ω}
    (S : Vaart1998RankVectorFiniteSource (Ω := Ω) (ι := ι) P) :
    S.rankVectorUniformUnderNull :=
  S.rankVectorUniformUnderNull_proof

/--
Distribution-free conclusion for rank statistics under the null.
-/
theorem Vaart1998RankVectorFiniteSource.distribution_free
    {Ω ι : Type*} [MeasurableSpace Ω] [Fintype ι]
    {P : Measure Ω}
    (S : Vaart1998RankVectorFiniteSource (Ω := Ω) (ι := ι) P) :
    S.distributionFreeUnderNull :=
  S.distributionFreeUnderNull_proof

/--
Finite-sample source for Lemma 13.1(vi), the mean and variance of simple
linear rank statistics.
-/
structure Vaart1998SimpleLinearRankStatisticFiniteSource
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    (P : Measure Ω) where
  /-- Coefficients `c_i`. -/
  coefficient : ι -> ℝ
  /-- Rank index assigned to observation `i`. -/
  rankIndex : ι -> Ω -> ρ
  /-- Scores `a_j`. -/
  score : ρ -> ℝ
  /-- The rank statistic. -/
  statistic : Ω -> ℝ
  /-- Displayed mean. -/
  expectation : ℝ
  /-- Displayed variance. -/
  variance : ℝ
  /-- Identification of the simple linear rank statistic. -/
  statistic_eq :
    statistic =
      vaart1998_simpleLinearRankStatistic
        coefficient rankIndex score
  /-- Lemma 13.1 expectation display. -/
  expectation_eq :
    expectation =
      vaart1998_simpleLinearRankExpectationDisplay
        coefficient score
  /-- Lemma 13.1 variance display. -/
  variance_eq :
    variance =
      vaart1998_simpleLinearRankVarianceDisplay
        coefficient score
  /-- Distribution-free null law of the statistic. -/
  distributionFreeUnderNull : Prop
  /-- Source proof of distribution-freeness. -/
  distributionFreeUnderNull_proof :
    distributionFreeUnderNull

/--
The simple linear rank statistic display.
-/
theorem Vaart1998SimpleLinearRankStatisticFiniteSource.statistic_display
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    {P : Measure Ω}
    (S : Vaart1998SimpleLinearRankStatisticFiniteSource
      (Ω := Ω) (ι := ι) (ρ := ρ) P) :
    S.statistic =
      vaart1998_simpleLinearRankStatistic
        S.coefficient S.rankIndex S.score :=
  S.statistic_eq

/--
Lemma 13.1 mean display.
-/
theorem Vaart1998SimpleLinearRankStatisticFiniteSource.expectation_display
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    {P : Measure Ω}
    (S : Vaart1998SimpleLinearRankStatisticFiniteSource
      (Ω := Ω) (ι := ι) (ρ := ρ) P) :
    S.expectation =
      vaart1998_simpleLinearRankExpectationDisplay
        S.coefficient S.score :=
  S.expectation_eq

/--
Lemma 13.1 variance display.
-/
theorem Vaart1998SimpleLinearRankStatisticFiniteSource.variance_display
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    {P : Measure Ω}
    (S : Vaart1998SimpleLinearRankStatisticFiniteSource
      (Ω := Ω) (ι := ι) (ρ := ρ) P) :
    S.variance =
      vaart1998_simpleLinearRankVarianceDisplay
        S.coefficient S.score :=
  S.variance_eq

/--
Difference between a rank statistic and its independent-sum approximation in
Theorem 13.5.
-/
def vaart1998_rankAsymptoticDifference
    {Ω : Type*} (statistic linearizedStatistic : ℕ -> Ω -> ℝ) :
    ℕ -> Ω -> ℝ :=
  fun n ω => statistic n ω - linearizedStatistic n ω

/--
Theorem 13.5 source: a simple linear rank statistic is asymptotically
equivalent to its projected independent-sum approximation.
-/
structure Vaart1998Theorem13_5RankAsymptoticEquivalenceSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Score-generating function `phi`. -/
  scoreGenerator : ℝ -> ℝ
  /-- Rank statistics `T_N`. -/
  statistic : ℕ -> Ω -> ℝ
  /-- Independent-sum approximations `\tilde T_N`. -/
  linearizedStatistic : ℕ -> Ω -> ℝ
  /-- Difference `T_N - \tilde T_N`. -/
  difference : ℕ -> Ω -> ℝ
  /-- Scaled or standardized rank statistic. -/
  scaledStatistic : ℕ -> Ω -> ℝ
  /-- Scaled or standardized linearized statistic. -/
  scaledLinearizedStatistic : ℕ -> Ω -> ℝ
  /-- Limit statistic. -/
  limitStatistic : ΩLimit -> ℝ
  /-- Identification of the difference display. -/
  difference_eq :
    difference =
      vaart1998_rankAsymptoticDifference
        statistic linearizedStatistic
  /-- Equality of expectations `E T_N = E \tilde T_N`. -/
  expectations_align : Prop
  /-- Variance-negligibility display from Theorem 13.5. -/
  varianceRatio_tendsto_zero : Prop
  /-- The corresponding probabilistic-negligibility handoff. -/
  difference_oP :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P difference
  /-- Limit theorem for the independent-sum approximation. -/
  linearized_tendstoInDistribution :
    TendstoInDistribution scaledLinearizedStatistic atTop
      limitStatistic P LimitLaw
  /-- Slutsky/projection transfer to the rank statistic. -/
  statistic_tendstoInDistribution :
    TendstoInDistribution scaledStatistic atTop
      limitStatistic P LimitLaw
  /-- Source proof of expectation alignment. -/
  expectations_align_proof :
    expectations_align
  /-- Source proof of the variance-negligibility display. -/
  varianceRatio_tendsto_zero_proof :
    varianceRatio_tendsto_zero

/--
Theorem 13.5 negligible-difference handoff.
-/
theorem Vaart1998Theorem13_5RankAsymptoticEquivalenceSource.difference_convergesInProbabilityToZero
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem13_5RankAsymptoticEquivalenceSource
      P LimitLaw) :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      S.difference :=
  S.difference_oP

/--
Theorem 13.5/Corollary 13.8 weak limit inherited by the rank statistic.
-/
theorem Vaart1998Theorem13_5RankAsymptoticEquivalenceSource.statistic_limit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem13_5RankAsymptoticEquivalenceSource
      P LimitLaw) :
    TendstoInDistribution S.scaledStatistic atTop
      S.limitStatistic P LimitLaw :=
  S.statistic_tendstoInDistribution

/--
The two-sample coefficient vector `(0, ..., 0, 1, ..., 1)`.
-/
def vaart1998_twoSampleCoefficient
    {ι κ : Type*} : Sum ι κ -> ℝ
  | Sum.inl _ => 0
  | Sum.inr _ => 1

/--
Wilcoxon rank sum: the sum of ranks of the second sample in the pooled sample.
-/
def vaart1998_pooledSecondSampleRankSum
    {Ω ι κ : Type*} [Fintype κ]
    (pooledRank : Sum ι κ -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ j : κ, pooledRank (Sum.inr j) ω

/--
Mann-Whitney count `sum_i sum_j 1{X_i <= Y_j}`.
-/
def vaart1998_mannWhitneyCount
    {Ω ι κ : Type*} [Fintype ι] [Fintype κ]
    (leIndicator : ι -> κ -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ i : ι, ∑ j : κ, leIndicator i j ω

/--
Degree `(1, 1)` Mann-Whitney kernel packaged as a two-sample `U`-statistic
kernel.
-/
def vaart1998_mannWhitneyKernel
    {Ω ι κ : Type*}
    (leIndicator : ι -> κ -> Ω -> ℝ) :
    Finset ι -> Finset κ -> Ω -> ℝ :=
  fun α β ω => ∑ i ∈ α, ∑ j ∈ β, leIndicator i j ω

/--
Chapter 12 normalized two-sample `U`-statistic corresponding to the
Mann-Whitney kernel.
-/
def vaart1998_mannWhitneyUStatistic
    {Ω ι κ : Type*} [Fintype ι] [DecidableEq ι]
    [Fintype κ] [DecidableEq κ]
    (leIndicator : ι -> κ -> Ω -> ℝ) : Ω -> ℝ :=
  vaart1998_twoSampleUStatistic
    (vaart1998_mannWhitneyKernel leIndicator) 1 1

/--
Wilcoxon rank-sum display from the unnormalized Mann-Whitney count:
`W = U + n(n+1)/2`.
-/
def vaart1998_wilcoxonRankSumFromMannWhitneyCount
    {Ω κ : Type*} [Fintype κ]
    (mannWhitneyCount : Ω -> ℝ) : Ω -> ℝ :=
  fun ω =>
    mannWhitneyCount ω +
      ((Fintype.card κ : ℝ) * ((Fintype.card κ : ℝ) + 1)) / 2

/--
Wilcoxon rank-sum display from the Chapter 12 normalized Mann-Whitney
`U`-statistic: `W = m n U + n(n+1)/2`.
-/
def vaart1998_wilcoxonRankSumFromNormalizedMannWhitney
    {Ω ι κ : Type*} [Fintype ι] [Fintype κ]
    (mannWhitneyU : Ω -> ℝ) : Ω -> ℝ :=
  fun ω =>
    (Fintype.card ι : ℝ) * (Fintype.card κ : ℝ) *
        mannWhitneyU ω +
      ((Fintype.card κ : ℝ) * ((Fintype.card κ : ℝ) + 1)) / 2

/--
Chapter 13 Wilcoxon/Mann-Whitney finite bridge.  It connects the pooled-rank
identity to the Chapter 12 degree `(1, 1)` two-sample `U`-statistic source.
-/
structure Vaart1998WilcoxonMannWhitneyBridgeSource
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    (P : Measure Ω) where
  /-- Indicator `1{X_i <= Y_j}`. -/
  leIndicator : ι -> κ -> Ω -> ℝ
  /-- Pooled ranks of both samples. -/
  pooledRank : Sum ι κ -> Ω -> ℝ
  /-- Unnormalized Mann-Whitney statistic. -/
  mannWhitneyCount : Ω -> ℝ
  /-- Chapter 12 normalized `U`-statistic. -/
  mannWhitneyUStatistic : Ω -> ℝ
  /-- Wilcoxon rank-sum statistic. -/
  wilcoxonRankSum : Ω -> ℝ
  /-- Chapter 12 two-sample `U`-statistic source for the same kernel. -/
  twoSampleUSource :
    Vaart1998TwoSampleUStatisticFiniteSource
      (Ω := Ω) (ι := ι) (κ := κ) P
  /-- Mann-Whitney count display. -/
  mannWhitneyCount_eq :
    mannWhitneyCount =
      vaart1998_mannWhitneyCount leIndicator
  /-- Normalized Chapter 12 `U`-statistic display. -/
  mannWhitneyUStatistic_eq :
    mannWhitneyUStatistic =
      vaart1998_mannWhitneyUStatistic leIndicator
  /-- Alignment with the Chapter 12 source statistic. -/
  twoSampleUSource_statistic_eq :
    twoSampleUSource.statistic = mannWhitneyUStatistic
  /-- The Chapter 12 source has degree `(1, 1)`. -/
  twoSampleUSource_degrees :
    twoSampleUSource.degreeX = 1 ∧ twoSampleUSource.degreeY = 1
  /-- Wilcoxon rank-sum display as a pooled-rank sum. -/
  wilcoxonRankSum_pooledRank_eq :
    wilcoxonRankSum =
      vaart1998_pooledSecondSampleRankSum pooledRank
  /-- No-ties side condition for the pooled sample. -/
  noTies : Prop
  /-- Chapter 13 identity `W = U + n(n+1)/2` under no ties. -/
  pooledRank_mannWhitney_identity :
    noTies ->
      vaart1998_pooledSecondSampleRankSum pooledRank =
        vaart1998_wilcoxonRankSumFromMannWhitneyCount (κ := κ)
          mannWhitneyCount
  /-- Normalized version `W = m n U + n(n+1)/2`. -/
  wilcoxonRankSum_normalized_eq :
    wilcoxonRankSum =
      vaart1998_wilcoxonRankSumFromNormalizedMannWhitney
        (ι := ι) (κ := κ)
        mannWhitneyUStatistic

/--
Mann-Whitney as the Chapter 12 degree `(1, 1)` two-sample `U`-statistic.
-/
theorem Vaart1998WilcoxonMannWhitneyBridgeSource.mannWhitneyUStatistic_display
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    {P : Measure Ω}
    (S : Vaart1998WilcoxonMannWhitneyBridgeSource
      (Ω := Ω) (ι := ι) (κ := κ) P) :
    S.mannWhitneyUStatistic =
      vaart1998_mannWhitneyUStatistic S.leIndicator :=
  S.mannWhitneyUStatistic_eq

/--
The Chapter 13 no-ties identity between Wilcoxon rank sum and Mann-Whitney
count.
-/
theorem Vaart1998WilcoxonMannWhitneyBridgeSource.pooledRank_mannWhitney
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    {P : Measure Ω}
    (S : Vaart1998WilcoxonMannWhitneyBridgeSource
      (Ω := Ω) (ι := ι) (κ := κ) P)
    (hNoTies : S.noTies) :
    vaart1998_pooledSecondSampleRankSum S.pooledRank =
      vaart1998_wilcoxonRankSumFromMannWhitneyCount
        (κ := κ)
        S.mannWhitneyCount :=
  S.pooledRank_mannWhitney_identity hNoTies

/--
Wilcoxon rank sum as an affine transform of the normalized Chapter 12
Mann-Whitney `U`-statistic.
-/
theorem Vaart1998WilcoxonMannWhitneyBridgeSource.wilcoxonRankSum_normalized_display
    {Ω ι κ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [DecidableEq ι] [Fintype κ] [DecidableEq κ]
    {P : Measure Ω}
    (S : Vaart1998WilcoxonMannWhitneyBridgeSource
      (Ω := Ω) (ι := ι) (κ := κ) P) :
    S.wilcoxonRankSum =
      vaart1998_wilcoxonRankSumFromNormalizedMannWhitney
        (ι := ι) (κ := κ)
        S.mannWhitneyUStatistic :=
  S.wilcoxonRankSum_normalized_eq

/--
Asymptotic-normality bridge for the Wilcoxon statistic: after centering and
scaling, the affine Wilcoxon statistic inherits the Chapter 12 two-sample
`U`-statistic projection limit.
-/
structure Vaart1998WilcoxonAsymptoticNormalitySource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Chapter 12 two-sample projection-method source. -/
  mannWhitneyProjectionSource :
    Vaart1998Theorem12_6TwoSampleProjectionMethodSource
      P LimitLaw
  /-- Scaled centered Mann-Whitney statistic. -/
  scaledMannWhitneyStatistic : ℕ -> Ω -> ℝ
  /-- Scaled centered Wilcoxon statistic. -/
  scaledWilcoxonStatistic : ℕ -> Ω -> ℝ
  /-- Alignment with the Chapter 12 source statistic. -/
  mannWhitney_scaled_eq :
    mannWhitneyProjectionSource.scaledCenteredStatistic =
      scaledMannWhitneyStatistic
  /-- The Wilcoxon affine transform has the same centered/scaled limit. -/
  wilcoxon_scaled_eq :
    scaledWilcoxonStatistic =
      scaledMannWhitneyStatistic
  /-- Source predicate saying the limit is normal with the displayed variance. -/
  normalLimitWithVariance : ℝ -> Prop
  /-- The normal-limit display inherited from Theorem 12.6. -/
  normalLimit_display :
    normalLimitWithVariance
      mannWhitneyProjectionSource.asymptoticVariance

/--
The scaled Mann-Whitney statistic inherits the Chapter 12 two-sample
projection limit.
-/
theorem Vaart1998WilcoxonAsymptoticNormalitySource.mannWhitney_tendstoInDistribution
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998WilcoxonAsymptoticNormalitySource
      P LimitLaw) :
    TendstoInDistribution S.scaledMannWhitneyStatistic atTop
      S.mannWhitneyProjectionSource.projectionMethodSource.limitStatistic
      P LimitLaw := by
  have h :=
    Vaart1998Theorem12_6TwoSampleProjectionMethodSource.scaledCenteredStatistic_tendstoInDistribution
      S.mannWhitneyProjectionSource
  simpa [S.mannWhitney_scaled_eq] using h

/--
The scaled Wilcoxon statistic has the same limit as the Mann-Whitney
`U`-statistic.
-/
theorem Vaart1998WilcoxonAsymptoticNormalitySource.wilcoxon_tendstoInDistribution
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998WilcoxonAsymptoticNormalitySource
      P LimitLaw) :
    TendstoInDistribution S.scaledWilcoxonStatistic atTop
      S.mannWhitneyProjectionSource.projectionMethodSource.limitStatistic
      P LimitLaw := by
  have h := S.mannWhitney_tendstoInDistribution
  simpa [S.wilcoxon_scaled_eq] using h

/--
The normal-limit variance display inherited from Theorem 12.6.
-/
theorem Vaart1998WilcoxonAsymptoticNormalitySource.normalLimit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998WilcoxonAsymptoticNormalitySource
      P LimitLaw) :
    S.normalLimitWithVariance
      S.mannWhitneyProjectionSource.asymptoticVariance :=
  S.normalLimit_display

/--
Sign statistic `sum_i sign(X_i)`.
-/
def vaart1998_signStatistic
    {Ω ι : Type*} [Fintype ι]
    (sign : ι -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ i : ι, sign i ω

/--
Simple linear signed-rank statistic
`sum_i a_{R_i^+} sign(X_i)`.
-/
def vaart1998_signedRankStatistic
    {Ω ι ρ : Type*} [Fintype ι]
    (absoluteRank : ι -> Ω -> ρ) (score : ρ -> ℝ)
    (sign : ι -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ i : ι, score (absoluteRank i ω) * sign i ω

/--
Positive signed-rank statistic `sum_i R_i^+ 1{X_i > 0}`, used in the Chapter
12 signed-rank `U`-statistic example.
-/
def vaart1998_positiveSignedRankStatistic
    {Ω ι : Type*} [Fintype ι]
    (absoluteRank : ι -> Ω -> ℝ)
    (positiveIndicator : ι -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω => ∑ i : ι, absoluteRank i ω * positiveIndicator i ω

/--
Lemma 13.17/Theorem 13.18 signed-rank source.
-/
structure Vaart1998SignedRankStatisticSource
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    (P : Measure Ω) where
  /-- Absolute ranks `R_i^+`. -/
  absoluteRank : ι -> Ω -> ρ
  /-- Scores `a_j`. -/
  score : ρ -> ℝ
  /-- Signs of observations. -/
  sign : ι -> Ω -> ℝ
  /-- The signed-rank statistic. -/
  statistic : Ω -> ℝ
  /-- Displayed variance under the symmetric null. -/
  variance : ℝ
  /-- Identification of the signed-rank display. -/
  statistic_eq :
    statistic =
      vaart1998_signedRankStatistic absoluteRank score sign
  /-- Lemma 13.17 independence of signs and absolute ranks. -/
  signsIndependentOfAbsoluteRanks : Prop
  /-- Lemma 13.17 uniformity of absolute ranks. -/
  absoluteRanksUniform : Prop
  /-- Lemma 13.17 uniformity of sign vectors. -/
  signsUniform : Prop
  /-- Variance display `sum_i a_i^2`. -/
  variance_eq :
    variance = ∑ r : ρ, score r ^ 2
  /-- Theorem 13.18 asymptotic equivalence to the signed independent sum. -/
  asymptoticallyEquivalentToSignedSum : Prop
  /-- Source proof of independence. -/
  signsIndependentOfAbsoluteRanks_proof :
    signsIndependentOfAbsoluteRanks
  /-- Source proof of absolute-rank uniformity. -/
  absoluteRanksUniform_proof :
    absoluteRanksUniform
  /-- Source proof of sign uniformity. -/
  signsUniform_proof :
    signsUniform
  /-- Source proof of Theorem 13.18 equivalence. -/
  asymptoticallyEquivalentToSignedSum_proof :
    asymptoticallyEquivalentToSignedSum

/--
The signed-rank statistic display.
-/
theorem Vaart1998SignedRankStatisticSource.statistic_display
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    {P : Measure Ω}
    (S : Vaart1998SignedRankStatisticSource
      (Ω := Ω) (ι := ι) (ρ := ρ) P) :
    S.statistic =
      vaart1998_signedRankStatistic
        S.absoluteRank S.score S.sign :=
  S.statistic_eq

/--
Lemma 13.17 variance display for signed-rank statistics.
-/
theorem Vaart1998SignedRankStatisticSource.variance_display
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    {P : Measure Ω}
    (S : Vaart1998SignedRankStatisticSource
      (Ω := Ω) (ι := ι) (ρ := ρ) P) :
    S.variance = ∑ r : ρ, S.score r ^ 2 :=
  S.variance_eq

/--
Theorem 13.18 signed-rank asymptotic-equivalence handoff.
-/
theorem Vaart1998SignedRankStatisticSource.asymptotic_equivalent
    {Ω ι ρ : Type*} [MeasurableSpace Ω]
    [Fintype ι] [Fintype ρ]
    {P : Measure Ω}
    (S : Vaart1998SignedRankStatisticSource
      (Ω := Ω) (ι := ι) (ρ := ρ) P) :
    S.asymptoticallyEquivalentToSignedSum :=
  S.asymptoticallyEquivalentToSignedSum_proof

/--
Permutation action on a statistic.
-/
def vaart1998_permutedStatistic
    {Ω Perm : Type*}
    (permute : Perm -> Ω -> Ω) (statistic : Ω -> ℝ)
    (π : Perm) : Ω -> ℝ :=
  fun ω => statistic (permute π ω)

/--
Two-sample sum statistic from Section 13.5:
`m^{-1} sum_i f(X_i) - n^{-1} sum_j f(Y_j)`.
-/
def vaart1998_twoSamplePermutationMeanDifference
    {Ω ι κ : Type*} [Fintype ι] [Fintype κ]
    (xValue : ι -> Ω -> ℝ) (yValue : κ -> Ω -> ℝ) : Ω -> ℝ :=
  fun ω =>
    (Fintype.card ι : ℝ)⁻¹ * (∑ i : ι, xValue i ω) -
      (Fintype.card κ : ℝ)⁻¹ * (∑ j : κ, yValue j ω)

/--
Finite permutation-test source: under the null, all pooled-sample
permutations are conditionally equally likely, yielding a conditional and
unconditional level statement.
-/
structure Vaart1998PermutationTestFiniteSource
    {Ω Perm : Type*} [MeasurableSpace Ω] [Fintype Perm]
    (P : Measure Ω) where
  /-- Observed statistic. -/
  statistic : Ω -> ℝ
  /-- Permutation action on the observation state. -/
  permute : Perm -> Ω -> Ω
  /-- Statistic after applying a permutation. -/
  permutedStatistic : Perm -> Ω -> ℝ
  /-- Identification of the permuted-statistic display. -/
  permutedStatistic_eq :
    ∀ π,
      permutedStatistic π =
        vaart1998_permutedStatistic permute statistic π
  /-- Conditional null law is uniform over permutations. -/
  conditionalNullUniform : Prop
  /-- Conditional level statement for the permutation test. -/
  conditionalLevel : Prop
  /-- Unconditional level statement for the permutation test. -/
  unconditionalLevel : Prop
  /-- Source proof of conditional uniformity. -/
  conditionalNullUniform_proof :
    conditionalNullUniform
  /-- Source proof of conditional level. -/
  conditionalLevel_proof :
    conditionalLevel
  /-- Source proof of unconditional level. -/
  unconditionalLevel_proof :
    unconditionalLevel

/--
Permuted-statistic display.
-/
theorem Vaart1998PermutationTestFiniteSource.permutedStatistic_display
    {Ω Perm : Type*} [MeasurableSpace Ω] [Fintype Perm]
    {P : Measure Ω}
    (S : Vaart1998PermutationTestFiniteSource
      (Ω := Ω) (Perm := Perm) P)
    (π : Perm) :
    S.permutedStatistic π =
      vaart1998_permutedStatistic S.permute S.statistic π :=
  S.permutedStatistic_eq π

/--
Conditional level conclusion for the permutation test.
-/
theorem Vaart1998PermutationTestFiniteSource.conditional_level
    {Ω Perm : Type*} [MeasurableSpace Ω] [Fintype Perm]
    {P : Measure Ω}
    (S : Vaart1998PermutationTestFiniteSource
      (Ω := Ω) (Perm := Perm) P) :
    S.conditionalLevel :=
  S.conditionalLevel_proof

/--
Unconditional level conclusion for the permutation test.
-/
theorem Vaart1998PermutationTestFiniteSource.unconditional_level
    {Ω Perm : Type*} [MeasurableSpace Ω] [Fintype Perm]
    {P : Measure Ω}
    (S : Vaart1998PermutationTestFiniteSource
      (Ω := Ω) (Perm := Perm) P) :
    S.unconditionalLevel :=
  S.unconditionalLevel_proof

/--
Theorem 13.25 source: conditional permutation distribution of a two-sample
sum statistic is asymptotically normal, with the same null variance as the
ordinary normal approximation.
-/
structure Vaart1998Theorem13_25PermutationCLTSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Permuted and scaled statistic `sqrt N T_N(Z_pi)`. -/
  scaledPermutedStatistic : ℕ -> Ω -> ℝ
  /-- Ordinary scaled statistic under the null. -/
  scaledObservedStatistic : ℕ -> Ω -> ℝ
  /-- Limit statistic. -/
  limitStatistic : ΩLimit -> ℝ
  /-- Sample-share limit `lambda`. -/
  lambda : ℝ
  /-- Null variance `var f(X_1)/(lambda(1-lambda))`. -/
  nullVariance : ℝ
  /-- Finite-second-moment assumptions on both samples. -/
  finiteSecondMoments : Prop
  /-- Sample-share condition `m/N -> lambda`. -/
  sampleShare_tendsto_lambda : Prop
  /-- Side condition `0 < lambda < 1`. -/
  lambda_between_zero_and_one : 0 < lambda ∧ lambda < 1
  /-- Conditional asymptotic normality statement. -/
  conditionalAsymptoticNormal : Prop
  /-- The ordinary null CLT for the observed statistic. -/
  observed_tendstoInDistribution :
    TendstoInDistribution scaledObservedStatistic atTop
      limitStatistic P LimitLaw
  /-- Same limit for the permuted statistic. -/
  permuted_tendstoInDistribution :
    TendstoInDistribution scaledPermutedStatistic atTop
      limitStatistic P LimitLaw
  /-- Source predicate for the normal law with the displayed variance. -/
  normalLimitWithVariance : ℝ -> Prop
  /-- Normal-variance display. -/
  normalLimit_display :
    normalLimitWithVariance nullVariance
  /-- Source proof of finite-second-moment assumptions. -/
  finiteSecondMoments_proof :
    finiteSecondMoments
  /-- Source proof of sample-share convergence. -/
  sampleShare_tendsto_lambda_proof :
    sampleShare_tendsto_lambda
  /-- Source proof of conditional asymptotic normality. -/
  conditionalAsymptoticNormal_proof :
    conditionalAsymptoticNormal

/--
Theorem 13.25 conditional asymptotic-normality handoff.
-/
theorem Vaart1998Theorem13_25PermutationCLTSource.conditional_asymptotic_normal
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem13_25PermutationCLTSource
      P LimitLaw) :
    S.conditionalAsymptoticNormal :=
  S.conditionalAsymptoticNormal_proof

/--
Theorem 13.25 permuted statistic weak limit.
-/
theorem Vaart1998Theorem13_25PermutationCLTSource.permuted_limit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem13_25PermutationCLTSource
      P LimitLaw) :
    TendstoInDistribution S.scaledPermutedStatistic atTop
      S.limitStatistic P LimitLaw :=
  S.permuted_tendstoInDistribution

/--
Theorem 13.25 normal-limit variance display.
-/
theorem Vaart1998Theorem13_25PermutationCLTSource.normalLimit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem13_25PermutationCLTSource
      P LimitLaw) :
    S.normalLimitWithVariance S.nullVariance :=
  S.normalLimit_display

end AsymptoticStatistics
end StatInference
