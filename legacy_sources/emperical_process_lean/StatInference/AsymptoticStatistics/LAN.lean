import StatInference.AsymptoticStatistics.Contiguity
import Mathlib.Probability.Distributions.Gaussian.HasGaussianLaw.Basic
import Mathlib.Probability.Notation

/-!
# van der Vaart 1998 Chapter 7 LAN interfaces

This module opens the Chapter 7 lane with the first source-shaped local
asymptotic normality handoff.  The initial packet keeps the analytic LAN
input deliberately small: an a.e. log-likelihood expansion with a
stochastically bounded central sequence and a stochastically bounded
remainder.  The next layer replaces the remainder boundedness field with the
textbook `o_{P_n}(1)` condition, then feeds the Chapter 6 Le Cam contiguity
API.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology

/--
Convergence in probability to zero for triangular arrays whose underlying
measure may vary with `n`.
-/
def Vaart1998MeasureSeqConvergesInProbabilityToZero
    {Ω E : Type*} [MeasurableSpace Ω] [SeminormedAddCommGroup E]
    (P : ℕ -> Measure Ω) (X : ℕ -> Ω -> E) : Prop :=
  ∀ ε : ℝ, 0 < ε ->
    Tendsto (fun n : ℕ => (P n).real {ω | ε ≤ ‖X n ω‖}) atTop (𝓝 0)

/--
An `o_{P_n}(1)` triangular array is `O_{P_n}(1)`.
-/
theorem vaart1998_measureSeqStochasticBounded_of_convergesInProbabilityToZero
    {Ω E : Type*} [MeasurableSpace Ω] [SeminormedAddCommGroup E]
    {P : ℕ -> Measure Ω} {X : ℕ -> Ω -> E}
    (hX : Vaart1998MeasureSeqConvergesInProbabilityToZero P X) :
    Vaart1998MeasureSeqStochasticBounded P X := by
  intro ε hε
  refine ⟨1, by norm_num, ?_⟩
  exact (tendsto_order.1 (hX 1 (by norm_num))).2 ε hε

/--
Convergence in distribution under varying measures implies stochastic
boundedness under those measures.

This is the Chapter 7 triangular-array analogue of the Chapter 2 fixed-measure
`vaart1998_stochasticBounded_of_tendstoInDistribution` bridge.
-/
theorem vaart1998_measureSeqStochasticBounded_of_tendstoInDistribution
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    {P : ℕ -> Measure Ω} {Q : Measure Ω'} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    [IsProbabilityMeasure Q]
    [MeasurableSpace E] [NormedAddCommGroup E]
    [OpensMeasurableSpace E] [BorelSpace E]
    [SecondCountableTopology E] [CompleteSpace E]
    {X : ℕ -> Ω -> E} {Z : Ω' -> E}
    (hX : TendstoInDistribution X atTop Z P Q) :
    Vaart1998MeasureSeqStochasticBounded P X := by
  let μ : ℕ -> ProbabilityMeasure E := fun n =>
    ⟨(P n).map (X n), Measure.isProbabilityMeasure_map (hX.forall_aemeasurable n)⟩
  let ν : ProbabilityMeasure E :=
    ⟨Q.map Z, Measure.isProbabilityMeasure_map hX.aemeasurable_limit⟩
  have hweak : VdVWWeakConvergenceProbabilityMeasures μ atTop ν := by
    simpa [VdVWWeakConvergenceProbabilityMeasures, μ, ν] using hX.tendsto
  intro ε hε
  rcases vaart1998_law_real_norm_tail_of_weak_convergence hweak ε hε with
    ⟨M, hMpos, htail⟩
  refine ⟨M, hMpos, ?_⟩
  filter_upwards [htail] with n hn
  have hset : MeasurableSet {x : E | M ≤ ‖x‖} :=
    (isClosed_le continuous_const continuous_norm).measurableSet
  have hmap :
      ((P n).map (X n)).real {x : E | M ≤ ‖x‖} =
        (P n).real {ω : Ω | M ≤ ‖X n ω‖} := by
    rw [measureReal_def, measureReal_def]
    rw [Measure.map_apply_of_aemeasurable (hX.forall_aemeasurable n) hset]
    rfl
  exact hmap ▸ (by simpa [μ] using hn)

/--
Stochastic boundedness is invariant under eventual a.e. equality for
triangular arrays with varying measures.
-/
theorem vaart1998_measureSeqStochasticBounded_congr_ae
    {Ω E : Type*} [MeasurableSpace Ω] [SeminormedAddCommGroup E]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsFiniteMeasure (P n)]
    {X Y : ℕ -> Ω -> E}
    (hX : Vaart1998MeasureSeqStochasticBounded P X)
    (hXY : ∀ᶠ n in atTop, X n =ᵐ[P n] Y n) :
    Vaart1998MeasureSeqStochasticBounded P Y := by
  intro ε hε
  rcases hX ε hε with ⟨M, hMpos, htail⟩
  refine ⟨M, hMpos, ?_⟩
  filter_upwards [htail, hXY] with n hn hEq
  have hset :
      {ω | M ≤ ‖Y n ω‖} =ᵐ[P n] {ω | M ≤ ‖X n ω‖} := by
    exact hEq.mono fun ω hω => by
      apply propext
      change M ≤ ‖Y n ω‖ ↔ M ≤ ‖X n ω‖
      rw [← hω]
  have hmeasure :
      (P n).real {ω | M ≤ ‖Y n ω‖} =
        (P n).real {ω | M ≤ ‖X n ω‖} :=
    measureReal_congr hset
  simpa [hmeasure] using hn

/--
A deterministic real constant is stochastically bounded under any sequence of
measures.
-/
theorem vaart1998_measureSeqStochasticBounded_const
    {Ω : Type*} [MeasurableSpace Ω]
    (P : ℕ -> Measure Ω) (c : ℝ) :
    Vaart1998MeasureSeqStochasticBounded P (fun _ (_ : Ω) => c) := by
  intro ε hε
  refine ⟨‖c‖ + 1, by positivity, ?_⟩
  refine Eventually.of_forall ?_
  intro n
  have hempty : {ω : Ω | ‖c‖ + 1 ≤ ‖(fun _ (_ : Ω) => c) n ω‖} = ∅ := by
    ext ω
    simp
  rw [hempty]
  simpa using hε

/--
The sum of two stochastically bounded triangular arrays is stochastically
bounded.
-/
theorem vaart1998_measureSeqStochasticBounded_add
    {Ω E : Type*} [MeasurableSpace Ω] [SeminormedAddCommGroup E]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsFiniteMeasure (P n)]
    {X Y : ℕ -> Ω -> E}
    (hX : Vaart1998MeasureSeqStochasticBounded P X)
    (hY : Vaart1998MeasureSeqStochasticBounded P Y) :
    Vaart1998MeasureSeqStochasticBounded P (fun n ω => X n ω + Y n ω) := by
  intro ε hε
  have hε2 : 0 < ε / 2 := half_pos hε
  rcases hX (ε / 2) hε2 with ⟨MX, hMXpos, hXtail⟩
  rcases hY (ε / 2) hε2 with ⟨MY, hMYpos, hYtail⟩
  refine ⟨MX + MY, add_pos hMXpos hMYpos, ?_⟩
  filter_upwards [hXtail, hYtail] with n hnX hnY
  let SX : Set Ω := {ω | MX ≤ ‖X n ω‖}
  let SY : Set Ω := {ω | MY ≤ ‖Y n ω‖}
  have hsubset :
      {ω | MX + MY ≤ ‖X n ω + Y n ω‖} ⊆ SX ∪ SY := by
    intro ω hω
    by_cases hx : MX ≤ ‖X n ω‖
    · exact Or.inl hx
    · by_cases hy : MY ≤ ‖Y n ω‖
      · exact Or.inr hy
      · have hxlt : ‖X n ω‖ < MX := lt_of_not_ge hx
        have hylt : ‖Y n ω‖ < MY := lt_of_not_ge hy
        have hnorm_lt : ‖X n ω + Y n ω‖ < MX + MY := by
          exact lt_of_le_of_lt (norm_add_le (X n ω) (Y n ω)) (add_lt_add hxlt hylt)
        exact False.elim ((not_lt_of_ge hω) hnorm_lt)
  have hmono :
      (P n).real {ω | MX + MY ≤ ‖X n ω + Y n ω‖} ≤ (P n).real (SX ∪ SY) :=
    measureReal_mono hsubset
  have hunion : (P n).real (SX ∪ SY) ≤ (P n).real SX + (P n).real SY :=
    measureReal_union_le SX SY
  calc
    (P n).real {ω | MX + MY ≤ ‖X n ω + Y n ω‖} ≤ (P n).real (SX ∪ SY) :=
      hmono
    _ ≤ (P n).real SX + (P n).real SY := hunion
    _ < ε := by linarith

/--
Chapter 7 LAN-style source for a log-likelihood-ratio expansion.

The textbook LAN display has the form
`log dP_n/dQ_n = central_n + informationShift + remainder_n`.  This first
source keeps the central sequence and the remainder abstract and records the
probabilistic inputs needed to derive the Chapter 6 Le Cam contiguity source.
-/
structure Vaart1998LANLogLikelihoodExpansionSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : ℕ -> Measure Ω) where
  /-- The stochastic linear/central-sequence term in the LAN expansion. -/
  centralSequence : ℕ -> Ω -> ℝ
  /-- The deterministic information shift, typically `-1/2 hᵀ I h`. -/
  informationShift : ℝ
  /-- The remainder term in the LAN expansion. -/
  remainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The LAN log-likelihood expansion, up to a.e. equality under `P_n`. -/
  expansion_ae : ∀ᶠ n in atTop,
    (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
      fun ω => centralSequence n ω + informationShift + remainder n ω
  /-- The central sequence is `O_{P_n}(1)`. -/
  centralSequence_stochasticallyBounded :
    Vaart1998MeasureSeqStochasticBounded P centralSequence
  /-- The LAN remainder is `O_{P_n}(1)`. -/
  remainder_stochasticallyBounded :
    Vaart1998MeasureSeqStochasticBounded P remainder

/--
A LAN log-likelihood expansion supplies stochastic boundedness of the
log-likelihood ratios.
-/
theorem Vaart1998LANLogLikelihoodExpansionSource.logLikelihoodRatio_stochasticallyBounded
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} [∀ n : ℕ, IsFiniteMeasure (P n)]
    (S : Vaart1998LANLogLikelihoodExpansionSource P Q) :
    Vaart1998MeasureSeqStochasticBounded P
      (fun n ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) := by
  have hcentral_const :
      Vaart1998MeasureSeqStochasticBounded P
        (fun n ω => S.centralSequence n ω + S.informationShift) :=
    vaart1998_measureSeqStochasticBounded_add
      (P := P) (X := S.centralSequence)
      (Y := fun _ (_ : Ω) => S.informationShift)
      S.centralSequence_stochasticallyBounded
      (vaart1998_measureSeqStochasticBounded_const P S.informationShift)
  have hsum :
      Vaart1998MeasureSeqStochasticBounded P
        (fun n ω => S.centralSequence n ω + S.informationShift + S.remainder n ω) :=
    vaart1998_measureSeqStochasticBounded_add
      (P := P) (X := fun n ω => S.centralSequence n ω + S.informationShift)
      (Y := S.remainder) hcentral_const S.remainder_stochasticallyBounded
  exact vaart1998_measureSeqStochasticBounded_congr_ae
    (P := P)
    (X := fun n ω => S.centralSequence n ω + S.informationShift + S.remainder n ω)
    (Y := fun n ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω)
    hsum (by
      filter_upwards [S.expansion_ae] with n hn
      exact hn.symm)

/--
A LAN log-likelihood expansion supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANLogLikelihoodExpansionSource.leCamStochasticBoundedSource
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} [∀ n : ℕ, IsFiniteMeasure (P n)]
    (S : Vaart1998LANLogLikelihoodExpansionSource P Q) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  { ac_eventually := S.ac_eventually
    logLikelihoodRatio_stochasticallyBounded :=
      S.logLikelihoodRatio_stochasticallyBounded }

/--
A LAN log-likelihood expansion yields one-sided contiguity.
-/
theorem Vaart1998LANLogLikelihoodExpansionSource.contiguitySource
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANLogLikelihoodExpansionSource P Q) :
    Vaart1998ContiguitySource P Q :=
  (S.leCamStochasticBoundedSource).contiguitySource

/--
Textbook-shaped LAN source with an `o_{P_n}(1)` remainder.

This is the usual LAN remainder condition.  The central sequence boundedness
is still kept as a source field; later packets can discharge it from a
Gaussian central-sequence or tightness theorem.
-/
structure Vaart1998LANLittleOExpansionSource
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : ℕ -> Measure Ω) where
  /-- The stochastic linear/central-sequence term in the LAN expansion. -/
  centralSequence : ℕ -> Ω -> ℝ
  /-- The deterministic information shift, typically `-1/2 hᵀ I h`. -/
  informationShift : ℝ
  /-- The LAN remainder term. -/
  remainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The LAN log-likelihood expansion, up to a.e. equality under `P_n`. -/
  expansion_ae : ∀ᶠ n in atTop,
    (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
      fun ω => centralSequence n ω + informationShift + remainder n ω
  /-- The central sequence is `O_{P_n}(1)`. -/
  centralSequence_stochasticallyBounded :
    Vaart1998MeasureSeqStochasticBounded P centralSequence
  /-- The LAN remainder is `o_{P_n}(1)`. -/
  remainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P remainder

/--
A LAN expansion with an `o_{P_n}(1)` remainder supplies the bounded-remainder
LAN source.
-/
def Vaart1998LANLittleOExpansionSource.logLikelihoodExpansionSource
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    (S : Vaart1998LANLittleOExpansionSource P Q) :
    Vaart1998LANLogLikelihoodExpansionSource P Q :=
  { centralSequence := S.centralSequence
    informationShift := S.informationShift
    remainder := S.remainder
    ac_eventually := S.ac_eventually
    expansion_ae := S.expansion_ae
    centralSequence_stochasticallyBounded := S.centralSequence_stochasticallyBounded
    remainder_stochasticallyBounded :=
      vaart1998_measureSeqStochasticBounded_of_convergesInProbabilityToZero
        S.remainder_convergesInProbabilityToZero }

/--
A textbook LAN `o_{P_n}(1)` expansion supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANLittleOExpansionSource.leCamStochasticBoundedSource
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} [∀ n : ℕ, IsFiniteMeasure (P n)]
    (S : Vaart1998LANLittleOExpansionSource P Q) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.logLikelihoodExpansionSource.leCamStochasticBoundedSource

/--
A textbook LAN `o_{P_n}(1)` expansion yields one-sided contiguity.
-/
theorem Vaart1998LANLittleOExpansionSource.contiguitySource
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANLittleOExpansionSource P Q) :
    Vaart1998ContiguitySource P Q :=
  S.logLikelihoodExpansionSource.contiguitySource

/--
LAN source with a Gaussian central-sequence limit.

This is closer to van der Vaart's textbook LAN formulation: the central
sequence is supplied by weak convergence to a Gaussian limit, while the
remainder is the usual `o_{P_n}(1)` term.
-/
structure Vaart1998LANGaussianCentralSequenceSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- The stochastic linear/central-sequence term in the LAN expansion. -/
  centralSequence : ℕ -> Ω -> ℝ
  /-- The Gaussian limit random variable for the central sequence. -/
  centralLimit : Ω' -> ℝ
  /-- The deterministic information shift, typically `-1/2 hᵀ I h`. -/
  informationShift : ℝ
  /-- The LAN remainder term. -/
  remainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The LAN log-likelihood expansion, up to a.e. equality under `P_n`. -/
  expansion_ae : ∀ᶠ n in atTop,
    (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
      fun ω => centralSequence n ω + informationShift + remainder n ω
  /-- The central sequence converges weakly to its Gaussian limit. -/
  centralSequence_tendstoInDistribution :
    TendstoInDistribution centralSequence atTop centralLimit P LimitLaw
  /-- The central-sequence limit is Gaussian. -/
  centralLimit_gaussian : HasGaussianLaw centralLimit LimitLaw
  /-- The LAN remainder is `o_{P_n}(1)`. -/
  remainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P remainder

/--
A Gaussian central-sequence LAN source supplies the textbook little-o LAN
source.
-/
def Vaart1998LANGaussianCentralSequenceSource.littleOExpansionSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANGaussianCentralSequenceSource P Q LimitLaw) :
    Vaart1998LANLittleOExpansionSource P Q :=
  { centralSequence := S.centralSequence
    informationShift := S.informationShift
    remainder := S.remainder
    ac_eventually := S.ac_eventually
    expansion_ae := S.expansion_ae
    centralSequence_stochasticallyBounded :=
      vaart1998_measureSeqStochasticBounded_of_tendstoInDistribution
        (P := P) (Q := LimitLaw) S.centralSequence_tendstoInDistribution
    remainder_convergesInProbabilityToZero := S.remainder_convergesInProbabilityToZero }

/--
A Gaussian central-sequence LAN source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANGaussianCentralSequenceSource.leCamStochasticBoundedSource
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANGaussianCentralSequenceSource P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.littleOExpansionSource.leCamStochasticBoundedSource

/--
A Gaussian central-sequence LAN source yields one-sided contiguity.
-/
theorem Vaart1998LANGaussianCentralSequenceSource.contiguitySource
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANGaussianCentralSequenceSource P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.littleOExpansionSource.contiguitySource

/--
Source-shaped LAN certificate whose central sequence is obtained by projecting
a vector score through a continuous linear score direction.

This is the first DQM/score-vector shaped interface: later packets can
discharge the vector weak convergence and likelihood expansion fields from
quadratic-mean differentiability hypotheses, while this packet handles the
continuous-mapping and Gaussian-pushforward bookkeeping.
-/
structure Vaart1998LANDQMScoreVectorSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- The vector-valued score or central derivative array. -/
  scoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the score array. -/
  scoreLimit : Ω' -> E
  /-- The local direction used to form the scalar LAN central sequence. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The deterministic information shift, typically `-1/2 hᵀ I h`. -/
  informationShift : ℝ
  /-- The LAN remainder term. -/
  remainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The scalar LAN log-likelihood expansion induced by the vector score. -/
  expansion_ae : ∀ᶠ n in atTop,
    (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
      fun ω => scoreDirection (scoreVector n ω) + informationShift + remainder n ω
  /-- The vector score converges weakly to its Gaussian vector limit. -/
  scoreVector_tendstoInDistribution :
    TendstoInDistribution scoreVector atTop scoreLimit P LimitLaw
  /-- The vector score limit is Gaussian. -/
  scoreLimit_gaussian : HasGaussianLaw scoreLimit LimitLaw
  /-- The LAN remainder is `o_{P_n}(1)`. -/
  remainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P remainder

/--
A DQM score-vector LAN source supplies the Gaussian central-sequence LAN source
by the continuous mapping theorem and Gaussian pushforward along the score
direction.
-/
def Vaart1998LANDQMScoreVectorSource.gaussianCentralSequenceSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANDQMScoreVectorSource (E := E) P Q LimitLaw) :
    Vaart1998LANGaussianCentralSequenceSource P Q LimitLaw :=
  { centralSequence := fun n ω => S.scoreDirection (S.scoreVector n ω)
    centralLimit := fun ω => S.scoreDirection (S.scoreLimit ω)
    informationShift := S.informationShift
    remainder := S.remainder
    ac_eventually := S.ac_eventually
    expansion_ae := S.expansion_ae
    centralSequence_tendstoInDistribution := by
      simpa [Function.comp_def] using
        (TendstoInDistribution.continuous_comp
          (g := fun x : E => S.scoreDirection x)
          S.scoreDirection.continuous S.scoreVector_tendstoInDistribution)
    centralLimit_gaussian := S.scoreLimit_gaussian.map_fun S.scoreDirection
    remainder_convergesInProbabilityToZero :=
      S.remainder_convergesInProbabilityToZero }

/--
A DQM score-vector LAN source supplies the textbook little-o LAN source.
-/
def Vaart1998LANDQMScoreVectorSource.littleOExpansionSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANDQMScoreVectorSource (E := E) P Q LimitLaw) :
    Vaart1998LANLittleOExpansionSource P Q :=
  S.gaussianCentralSequenceSource.littleOExpansionSource

/--
A DQM score-vector LAN source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANDQMScoreVectorSource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANDQMScoreVectorSource (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.gaussianCentralSequenceSource.leCamStochasticBoundedSource

/--
A DQM score-vector LAN source yields one-sided contiguity.
-/
theorem Vaart1998LANDQMScoreVectorSource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANDQMScoreVectorSource (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.gaussianCentralSequenceSource.contiguitySource

/--
Quadratic-mean differentiability shaped LAN source.

The source records the score-vector expansion with the textbook Fisher
information shift `-I(h, h) / 2`.  Later packets can discharge the expansion
and weak-convergence fields from concrete Hellinger or quadratic-mean
differentiability assumptions.  This packet turns that QMD-shaped certificate
into the reusable DQM score-vector LAN source.
-/
structure Vaart1998LANQuadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- The vector-valued score array supplied by the QMD expansion. -/
  qmdScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the QMD score array. -/
  qmdScoreLimit : Ω' -> E
  /-- The local direction `h` applied to the score vector. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN/QMD remainder term. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The QMD LAN expansion with Fisher shift `-I(h, h) / 2`. -/
  expansion_ae : ∀ᶠ n in atTop,
    (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
      fun ω =>
        scoreDirection (qmdScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The vector QMD score converges weakly to its Gaussian vector limit. -/
  qmdScoreVector_tendstoInDistribution :
    TendstoInDistribution qmdScoreVector atTop qmdScoreLimit P LimitLaw
  /-- The QMD score limit is Gaussian. -/
  qmdScoreLimit_gaussian : HasGaussianLaw qmdScoreLimit LimitLaw
  /-- The QMD remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P qmdRemainder

/--
The Fisher shift in a QMD LAN source is nonpositive.
-/
theorem Vaart1998LANQuadraticMeanDifferentiabilitySource.informationShift_nonpos
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw) :
    -(S.fisherInformationQuadratic / 2) ≤ 0 := by
  nlinarith [S.fisherInformationQuadratic_nonneg]

/--
A QMD-shaped LAN source supplies the DQM score-vector LAN source by identifying
the deterministic LAN shift as `-I(h, h) / 2`.
-/
def Vaart1998LANQuadraticMeanDifferentiabilitySource.dqmScoreVectorSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LANDQMScoreVectorSource (E := E) P Q LimitLaw :=
  { scoreVector := S.qmdScoreVector
    scoreLimit := S.qmdScoreLimit
    scoreDirection := S.scoreDirection
    informationShift := -(S.fisherInformationQuadratic / 2)
    remainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    expansion_ae := S.expansion_ae
    scoreVector_tendstoInDistribution :=
      S.qmdScoreVector_tendstoInDistribution
    scoreLimit_gaussian := S.qmdScoreLimit_gaussian
    remainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A QMD-shaped LAN source supplies the Gaussian central-sequence LAN source.
-/
def Vaart1998LANQuadraticMeanDifferentiabilitySource.gaussianCentralSequenceSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LANGaussianCentralSequenceSource P Q LimitLaw :=
  S.dqmScoreVectorSource.gaussianCentralSequenceSource

/--
A QMD-shaped LAN source supplies the textbook little-o LAN source.
-/
def Vaart1998LANQuadraticMeanDifferentiabilitySource.littleOExpansionSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LANLittleOExpansionSource P Q :=
  S.dqmScoreVectorSource.littleOExpansionSource

/--
A QMD-shaped LAN source supplies the Chapter 6 Le Cam stochastic-boundedness
source.
-/
theorem Vaart1998LANQuadraticMeanDifferentiabilitySource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.dqmScoreVectorSource.leCamStochasticBoundedSource

/--
A QMD-shaped LAN source yields one-sided contiguity.
-/
theorem Vaart1998LANQuadraticMeanDifferentiabilitySource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.dqmScoreVectorSource.contiguitySource

/--
Density-level Hellinger differentiability shaped LAN source.

The source records square-root density expansion data against a dominating
measure, together with the log-likelihood expansion and weak limit facts that
turn that density-level certificate into the QMD Fisher-shift LAN source.
Later packets can discharge the log-likelihood expansion from the square-root
density expansion and concrete Hellinger differentiability hypotheses.
-/
structure Vaart1998LANHellingerDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- A measure dominating the local square-root density display. -/
  dominatingMeasure : Measure Ω
  /-- The baseline square-root density. -/
  baseSqrtDensity : Ω -> ℝ
  /-- The local square-root densities. -/
  localSqrtDensity : ℕ -> Ω -> ℝ
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under `P_n`. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The LAN expansion derived from the square-root density expansion. -/
  logLikelihood_expansion_ae : ∀ᶠ n in atTop,
    (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit P LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P qmdRemainder

/--
The square-root density remainder in a Hellinger source is stochastically
bounded.
-/
theorem Vaart1998LANHellingerDifferentiabilitySource.sqrtDensityRemainder_stochasticallyBounded
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998MeasureSeqStochasticBounded P S.sqrtDensityRemainder :=
  vaart1998_measureSeqStochasticBounded_of_convergesInProbabilityToZero
    S.sqrtDensityRemainder_convergesInProbabilityToZero

/--
A density-level Hellinger differentiability source supplies the QMD
Fisher-shift LAN source.
-/
def Vaart1998LANHellingerDifferentiabilitySource.quadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw :=
  { qmdScoreVector := S.hellingerScoreVector
    qmdScoreLimit := S.hellingerScoreLimit
    scoreDirection := S.scoreDirection
    fisherInformationQuadratic := S.fisherInformationQuadratic
    fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
    qmdRemainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    expansion_ae := S.logLikelihood_expansion_ae
    qmdScoreVector_tendstoInDistribution :=
      S.hellingerScoreVector_tendstoInDistribution
    qmdScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
    qmdRemainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A density-level Hellinger differentiability source supplies the DQM
score-vector LAN source.
-/
def Vaart1998LANHellingerDifferentiabilitySource.dqmScoreVectorSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LANDQMScoreVectorSource (E := E) P Q LimitLaw :=
  S.quadraticMeanDifferentiabilitySource.dqmScoreVectorSource

/--
A density-level Hellinger differentiability source supplies the Gaussian
central-sequence LAN source.
-/
def Vaart1998LANHellingerDifferentiabilitySource.gaussianCentralSequenceSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LANGaussianCentralSequenceSource P Q LimitLaw :=
  S.quadraticMeanDifferentiabilitySource.gaussianCentralSequenceSource

/--
A density-level Hellinger differentiability source supplies the textbook
little-o LAN source.
-/
def Vaart1998LANHellingerDifferentiabilitySource.littleOExpansionSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LANLittleOExpansionSource P Q :=
  S.quadraticMeanDifferentiabilitySource.littleOExpansionSource

/--
A density-level Hellinger differentiability source supplies the Chapter 6
Le Cam stochastic-boundedness source.
-/
theorem Vaart1998LANHellingerDifferentiabilitySource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.quadraticMeanDifferentiabilitySource.leCamStochasticBoundedSource

/--
A density-level Hellinger differentiability source yields one-sided
contiguity.
-/
theorem Vaart1998LANHellingerDifferentiabilitySource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.quadraticMeanDifferentiabilitySource.contiguitySource

/--
The density-log display suggested by a square-root density ratio:
`log (p_n / p_0) = 2 log (sqrt p_n / sqrt p_0)`.
-/
noncomputable def vaart1998_sqrtDensityLogLikelihoodDisplay
    {Ω : Type*} (baseSqrtDensity : Ω -> ℝ) (localSqrtDensity : Ω -> ℝ) :
    Ω -> ℝ :=
  fun ω => 2 * Real.log (localSqrtDensity ω / baseSqrtDensity ω)

/--
If the likelihood ratio is the square of the square-root density ratio, then
the log likelihood ratio is the square-root density log display.
-/
theorem vaart1998_logLikelihoodRatio_ae_eq_sqrtDensityLog_of_likelihoodRatio_sq
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : Measure Ω} {baseSqrtDensity localSqrtDensity : Ω -> ℝ}
    (hRatio :
      (fun ω => (vaart1998_likelihoodRatio P Q ω).toReal) =ᵐ[P]
        fun ω => (localSqrtDensity ω / baseSqrtDensity ω) ^ 2) :
    (fun ω => vaart1998_logLikelihoodRatio P Q ω) =ᵐ[P]
      vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
        localSqrtDensity := by
  filter_upwards [hRatio] with ω hω
  simp [vaart1998_logLikelihoodRatio_eq_log_likelihoodRatio_toReal,
    vaart1998_sqrtDensityLogLikelihoodDisplay, hω, Real.log_pow]

/--
Triangular-array version of the square-root density log-likelihood handoff.
-/
theorem vaart1998_logLikelihoodRatio_eventually_ae_eq_sqrtDensityLog_of_likelihoodRatio_sq
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    (hRatio : ∀ᶠ n in atTop,
      (fun ω => (vaart1998_likelihoodRatio (P n) (Q n) ω).toReal) =ᵐ[P n]
        fun ω => (localSqrtDensity n ω / baseSqrtDensity ω) ^ 2) :
    ∀ᶠ n in atTop,
      (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
        vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
          (localSqrtDensity n) := by
  filter_upwards [hRatio] with n hn
  exact vaart1998_logLikelihoodRatio_ae_eq_sqrtDensityLog_of_likelihoodRatio_sq
    (P := P n) (Q := Q n)
    (baseSqrtDensity := baseSqrtDensity)
    (localSqrtDensity := localSqrtDensity n) hn

/--
The ratio of squared square-root densities is the square of their ratio.
-/
theorem vaart1998_likelihoodRatio_ae_eq_sqrtDensityRatioSq_of_sq_ratio
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : Measure Ω} {baseSqrtDensity localSqrtDensity : Ω -> ℝ}
    (hRatio :
      (fun ω => (vaart1998_likelihoodRatio P Q ω).toReal) =ᵐ[P]
        fun ω => localSqrtDensity ω ^ 2 / baseSqrtDensity ω ^ 2) :
    (fun ω => (vaart1998_likelihoodRatio P Q ω).toReal) =ᵐ[P]
      fun ω => (localSqrtDensity ω / baseSqrtDensity ω) ^ 2 := by
  filter_upwards [hRatio] with ω hω
  rw [hω]
  ring

/--
Triangular-array version of the squared-density-ratio algebra handoff.
-/
theorem vaart1998_likelihoodRatio_eventually_ae_eq_sqrtDensityRatioSq_of_sq_ratio
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    (hRatio : ∀ᶠ n in atTop,
      (fun ω => (vaart1998_likelihoodRatio (P n) (Q n) ω).toReal) =ᵐ[P n]
        fun ω => localSqrtDensity n ω ^ 2 / baseSqrtDensity ω ^ 2) :
    ∀ᶠ n in atTop,
      (fun ω => (vaart1998_likelihoodRatio (P n) (Q n) ω).toReal) =ᵐ[P n]
        fun ω => (localSqrtDensity n ω / baseSqrtDensity ω) ^ 2 := by
  filter_upwards [hRatio] with n hn
  exact vaart1998_likelihoodRatio_ae_eq_sqrtDensityRatioSq_of_sq_ratio
    (P := P n) (Q := Q n)
    (baseSqrtDensity := baseSqrtDensity)
    (localSqrtDensity := localSqrtDensity n) hn

/--
The measure represented by a square-root density relative to a dominating
measure.
-/
noncomputable def vaart1998_sqrtDensityMeasure
    {Ω : Type*} [MeasurableSpace Ω]
    (dominatingMeasure : Measure Ω) (sqrtDensity : Ω -> ℝ) :
    Measure Ω :=
  dominatingMeasure.withDensity
    fun ω => ENNReal.ofReal (sqrtDensity ω ^ 2)

/--
The local triangular-array measures represented by local square-root
densities.
-/
noncomputable def vaart1998_localSqrtDensityMeasureSeq
    {Ω : Type*} [MeasurableSpace Ω]
    (dominatingMeasure : Measure Ω) (localSqrtDensity : ℕ -> Ω -> ℝ) :
    ℕ -> Measure Ω :=
  fun n => vaart1998_sqrtDensityMeasure dominatingMeasure (localSqrtDensity n)

/--
The constant baseline triangular-array measure represented by a baseline
square-root density.
-/
noncomputable def vaart1998_baseSqrtDensityMeasureSeq
    {Ω : Type*} [MeasurableSpace Ω]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ) :
    ℕ -> Measure Ω :=
  fun _ => vaart1998_sqrtDensityMeasure dominatingMeasure baseSqrtDensity

/--
Real measurability of a square-root density gives measurability of its
`ENNReal.ofReal` squared density.
-/
theorem vaart1998_measurable_ennreal_ofReal_sq
    {Ω : Type*} [MeasurableSpace Ω] {sqrtDensity : Ω -> ℝ}
    (hMeas : Measurable sqrtDensity) :
    Measurable fun ω => ENNReal.ofReal (sqrtDensity ω ^ 2) :=
  ENNReal.continuous_ofReal.measurable.comp (hMeas.pow_const 2)

/--
The total mass of the measure represented by a square-root density is the
integral of the squared square-root density.
-/
theorem vaart1998_sqrtDensityMeasure_univ
    {Ω : Type*} [MeasurableSpace Ω]
    (dominatingMeasure : Measure Ω) (sqrtDensity : Ω -> ℝ) :
    vaart1998_sqrtDensityMeasure dominatingMeasure sqrtDensity Set.univ =
      ∫⁻ ω, ENNReal.ofReal (sqrtDensity ω ^ 2) ∂dominatingMeasure := by
  rw [vaart1998_sqrtDensityMeasure, withDensity_apply _ MeasurableSet.univ]
  simp

/--
A square-root density normalized in `L^2(μ)` defines a probability measure.
-/
theorem vaart1998_sqrtDensityMeasure_isProbabilityMeasure_of_lintegral_eq_one
    {Ω : Type*} [MeasurableSpace Ω]
    {dominatingMeasure : Measure Ω} {sqrtDensity : Ω -> ℝ}
    (hNorm :
      ∫⁻ ω, ENNReal.ofReal (sqrtDensity ω ^ 2) ∂dominatingMeasure = 1) :
    IsProbabilityMeasure
      (vaart1998_sqrtDensityMeasure dominatingMeasure sqrtDensity) :=
  ⟨by
    rw [vaart1998_sqrtDensityMeasure_univ]
    exact hNorm⟩

/--
Pointwise local square-root-density normalizations give probability local
laws.
-/
theorem vaart1998_localSqrtDensityMeasureSeq_isProbabilityMeasure_of_lintegral_eq_one
    {Ω : Type*} [MeasurableSpace Ω]
    {dominatingMeasure : Measure Ω} {localSqrtDensity : ℕ -> Ω -> ℝ}
    (hNorm : ∀ n : ℕ,
      ∫⁻ ω, ENNReal.ofReal (localSqrtDensity n ω ^ 2) ∂dominatingMeasure = 1) :
    ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
  fun n =>
    vaart1998_sqrtDensityMeasure_isProbabilityMeasure_of_lintegral_eq_one
      (dominatingMeasure := dominatingMeasure)
      (sqrtDensity := localSqrtDensity n) (hNorm n)

/--
A baseline square-root-density normalization gives probability baseline laws.
-/
theorem vaart1998_baseSqrtDensityMeasureSeq_isProbabilityMeasure_of_lintegral_eq_one
    {Ω : Type*} [MeasurableSpace Ω]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    (hNorm :
      ∫⁻ ω, ENNReal.ofReal (baseSqrtDensity ω ^ 2) ∂dominatingMeasure = 1) :
    ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
  fun _ =>
    vaart1998_sqrtDensityMeasure_isProbabilityMeasure_of_lintegral_eq_one
      (dominatingMeasure := dominatingMeasure)
      (sqrtDensity := baseSqrtDensity) hNorm

/--
A square-root-density measure is absolutely continuous with respect to its
dominating measure.
-/
theorem vaart1998_sqrtDensityMeasure_absolutelyContinuous_dominating
    {Ω : Type*} [MeasurableSpace Ω]
    (dominatingMeasure : Measure Ω) (sqrtDensity : Ω -> ℝ) :
    vaart1998_sqrtDensityMeasure dominatingMeasure sqrtDensity ≪
      dominatingMeasure := by
  simpa [vaart1998_sqrtDensityMeasure] using
    (withDensity_absolutelyContinuous dominatingMeasure
      (fun ω => ENNReal.ofReal (sqrtDensity ω ^ 2)))

/--
If the baseline square-root density is nonzero almost everywhere, then every
square-root-density law is absolutely continuous with respect to the baseline
law.
-/
theorem vaart1998_sqrtDensityMeasure_absolutelyContinuous_of_base_ae_ne_zero
    {Ω : Type*} [MeasurableSpace Ω]
    {dominatingMeasure : Measure Ω}
    {baseSqrtDensity localSqrtDensity : Ω -> ℝ}
    (hBaseMeas : Measurable baseSqrtDensity)
    (hBaseNonzero : ∀ᵐ ω ∂dominatingMeasure, baseSqrtDensity ω ≠ 0) :
    vaart1998_sqrtDensityMeasure dominatingMeasure localSqrtDensity ≪
      vaart1998_sqrtDensityMeasure dominatingMeasure baseSqrtDensity := by
  have hLocal_ac :
      vaart1998_sqrtDensityMeasure dominatingMeasure localSqrtDensity ≪
        dominatingMeasure :=
    vaart1998_sqrtDensityMeasure_absolutelyContinuous_dominating
      dominatingMeasure localSqrtDensity
  have hBaseSqNonzero :
      ∀ᵐ ω ∂dominatingMeasure,
        ENNReal.ofReal (baseSqrtDensity ω ^ 2) ≠ 0 := by
    filter_upwards [hBaseNonzero] with ω hω
    exact ENNReal.ofReal_ne_zero_iff.mpr (sq_pos_of_ne_zero hω)
  have hDominating_ac_base :
      dominatingMeasure ≪
        vaart1998_sqrtDensityMeasure dominatingMeasure baseSqrtDensity := by
    simpa [vaart1998_sqrtDensityMeasure] using
      (withDensity_absolutelyContinuous'
        (μ := dominatingMeasure)
        (f := fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2))
        (vaart1998_measurable_ennreal_ofReal_sq hBaseMeas).aemeasurable
        hBaseSqNonzero)
  exact hLocal_ac.trans hDominating_ac_base

/--
Triangular-array absolute continuity from a nonzero baseline square-root
density.
-/
theorem vaart1998_localSqrtDensityMeasureSeq_ac_eventually_of_base_ae_ne_zero
    {Ω : Type*} [MeasurableSpace Ω]
    {dominatingMeasure : Measure Ω}
    {baseSqrtDensity : Ω -> ℝ} {localSqrtDensity : ℕ -> Ω -> ℝ}
    (hBaseMeas : Measurable baseSqrtDensity)
    (hBaseNonzero : ∀ᵐ ω ∂dominatingMeasure, baseSqrtDensity ω ≠ 0) :
    ∀ᶠ n in atTop,
      vaart1998_localSqrtDensityMeasureSeq dominatingMeasure localSqrtDensity n ≪
        vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n :=
  Eventually.of_forall fun n => by
    simpa [vaart1998_localSqrtDensityMeasureSeq,
      vaart1998_baseSqrtDensityMeasureSeq] using
      (vaart1998_sqrtDensityMeasure_absolutelyContinuous_of_base_ae_ne_zero
        (dominatingMeasure := dominatingMeasure)
        (baseSqrtDensity := baseSqrtDensity)
        (localSqrtDensity := localSqrtDensity n)
        hBaseMeas hBaseNonzero)

/--
Probability-normalized concrete square-root-density arrays have the
Lebesgue-decomposition instances needed by the final contiguity handoff.
-/
theorem vaart1998_localSqrtDensityMeasureSeq_haveLebesgueDecomposition_of_lintegral_eq_one
    {Ω : Type*} [MeasurableSpace Ω]
    {dominatingMeasure : Measure Ω}
    {baseSqrtDensity : Ω -> ℝ} {localSqrtDensity : ℕ -> Ω -> ℝ}
    (hLocalNorm : ∀ n : ℕ,
      ∫⁻ ω, ENNReal.ofReal (localSqrtDensity n ω ^ 2) ∂dominatingMeasure = 1)
    (hBaseNorm :
      ∫⁻ ω, ENNReal.ofReal (baseSqrtDensity ω ^ 2) ∂dominatingMeasure = 1) :
    ∀ n : ℕ,
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n).HaveLebesgueDecomposition
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n) := by
  haveI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    vaart1998_localSqrtDensityMeasureSeq_isProbabilityMeasure_of_lintegral_eq_one
      (dominatingMeasure := dominatingMeasure)
      (localSqrtDensity := localSqrtDensity) hLocalNorm
  haveI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    vaart1998_baseSqrtDensityMeasureSeq_isProbabilityMeasure_of_lintegral_eq_one
      (dominatingMeasure := dominatingMeasure)
      (baseSqrtDensity := baseSqrtDensity) hBaseNorm
  intro n
  infer_instance

/--
If `P` and `Q` are represented by squared square-root densities with respect
to a common dominating measure, then the likelihood ratio has Vaart's
squared-density-ratio display.
-/
theorem vaart1998_likelihoodRatio_ae_eq_sqrtDensitySqRatio_of_withDensity
    {Ω : Type*} [MeasurableSpace Ω]
    {μ P Q : Measure Ω} [SigmaFinite μ] [SigmaFinite P] [SigmaFinite Q]
    {baseSqrtDensity localSqrtDensity : Ω -> ℝ}
    (hP : P =
      μ.withDensity (fun ω => ENNReal.ofReal (localSqrtDensity ω ^ 2)))
    (hQ : Q =
      μ.withDensity (fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2)))
    (hLocal_meas :
      Measurable fun ω => ENNReal.ofReal (localSqrtDensity ω ^ 2))
    (hBase_meas :
      Measurable fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2))
    (hAC : P ≪ Q) :
    (fun ω => (vaart1998_likelihoodRatio P Q ω).toReal) =ᵐ[P]
      fun ω => localSqrtDensity ω ^ 2 / baseSqrtDensity ω ^ 2 := by
  have hP_ac : P ≪ μ := by
    rw [hP]
    exact withDensity_absolutelyContinuous μ _
  have hQ_ac : Q ≪ μ := by
    rw [hQ]
    exact withDensity_absolutelyContinuous μ _
  have hRN_div :
      P.rnDeriv Q =ᵐ[Q] fun ω => P.rnDeriv μ ω / Q.rnDeriv μ ω :=
    Measure.rnDeriv_eq_div (μ := P) (ν := Q) (ξ := μ) hP_ac hQ_ac
  have hP_rn :
      P.rnDeriv μ =ᵐ[μ]
        fun ω => ENNReal.ofReal (localSqrtDensity ω ^ 2) := by
    rw [hP]
    exact Measure.rnDeriv_withDensity μ hLocal_meas
  have hQ_rn :
      Q.rnDeriv μ =ᵐ[μ]
        fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2) := by
    rw [hQ]
    exact Measure.rnDeriv_withDensity μ hBase_meas
  filter_upwards [hAC hRN_div, hAC (hQ_ac hP_rn),
    hAC (hQ_ac hQ_rn)] with ω hRN hPrn hQrn
  rw [vaart1998_likelihoodRatio, hRN, hPrn, hQrn]
  rw [ENNReal.toReal_div,
    ENNReal.toReal_ofReal (sq_nonneg (localSqrtDensity ω)),
    ENNReal.toReal_ofReal (sq_nonneg (baseSqrtDensity ω))]

/--
Triangular-array version of the common-dominating-measure
square-root-density likelihood-ratio identity.
-/
theorem vaart1998_likelihoodRatio_eventually_ae_eq_sqrtDensitySqRatio_of_withDensity
    {Ω : Type*} [MeasurableSpace Ω]
    {μ : Measure Ω} [SigmaFinite μ]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, SigmaFinite (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    {baseSqrtDensity : Ω -> ℝ} {localSqrtDensity : ℕ -> Ω -> ℝ}
    (hP : ∀ᶠ n in atTop,
      P n = μ.withDensity
        (fun ω => ENNReal.ofReal (localSqrtDensity n ω ^ 2)))
    (hQ : ∀ᶠ n in atTop,
      Q n = μ.withDensity
        (fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2)))
    (hLocal_meas : ∀ n : ℕ,
      Measurable fun ω => ENNReal.ofReal (localSqrtDensity n ω ^ 2))
    (hBase_meas :
      Measurable fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2))
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n) :
    ∀ᶠ n in atTop,
      (fun ω => (vaart1998_likelihoodRatio (P n) (Q n) ω).toReal) =ᵐ[P n]
        fun ω => localSqrtDensity n ω ^ 2 / baseSqrtDensity ω ^ 2 := by
  filter_upwards [hP, hQ, hAC] with n hPn hQn hACn
  exact vaart1998_likelihoodRatio_ae_eq_sqrtDensitySqRatio_of_withDensity
    (μ := μ) (P := P n) (Q := Q n)
    (baseSqrtDensity := baseSqrtDensity)
    (localSqrtDensity := localSqrtDensity n)
    hPn hQn (hLocal_meas n) hBase_meas hACn

/--
Eventual a.e. equality is transitive for triangular arrays with varying
measures.
-/
theorem vaart1998_eventually_ae_eq_trans_atTop
    {Ω α : Type*} [MeasurableSpace Ω]
    {P : ℕ -> Measure Ω} {X Y Z : ℕ -> Ω -> α}
    (hXY : ∀ᶠ n in atTop, X n =ᵐ[P n] Y n)
    (hYZ : ∀ᶠ n in atTop, Y n =ᵐ[P n] Z n) :
    ∀ᶠ n in atTop, X n =ᵐ[P n] Z n := by
  filter_upwards [hXY, hYZ] with n hnXY hnYZ
  exact hnXY.trans hnYZ

/--
Hellinger density-log source.

This source replaces the direct Hellinger log-likelihood expansion field by
two density-level facts: the log likelihood ratio agrees with the square-root
density log display, and that display has the LAN expansion.  The constructor
below discharges the `logLikelihood_expansion_ae` field of
`Vaart1998LANHellingerDifferentiabilitySource` by transitivity.
-/
structure Vaart1998LANHellingerDensityLogSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- A measure dominating the local square-root density display. -/
  dominatingMeasure : Measure Ω
  /-- The baseline square-root density. -/
  baseSqrtDensity : Ω -> ℝ
  /-- The local square-root densities. -/
  localSqrtDensity : ℕ -> Ω -> ℝ
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under `P_n`. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /--
  The log likelihood ratio agrees with the square-root density log display.
  This is the density/Radon-Nikodym handoff field.
  -/
  logLikelihood_eq_sqrtDensityLog_ae : ∀ᶠ n in atTop,
    (fun ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω) =ᵐ[P n]
      vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
        (localSqrtDensity n)
  /-- The square-root density log display has the LAN expansion. -/
  sqrtDensityLog_expansion_ae : ∀ᶠ n in atTop,
    vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
      (localSqrtDensity n) =ᵐ[P n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit P LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P qmdRemainder

/--
A Hellinger density-log source supplies the Hellinger differentiability source
by composing the density-log display equality with its LAN expansion.
-/
def Vaart1998LANHellingerDensityLogSource.hellingerDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw :=
  { dominatingMeasure := S.dominatingMeasure
    baseSqrtDensity := S.baseSqrtDensity
    localSqrtDensity := S.localSqrtDensity
    hellingerScoreVector := S.hellingerScoreVector
    hellingerScoreLimit := S.hellingerScoreLimit
    scoreDirection := S.scoreDirection
    sqrtDensityRemainder := S.sqrtDensityRemainder
    sqrtDensity_expansion_ae := S.sqrtDensity_expansion_ae
    sqrtDensityRemainder_convergesInProbabilityToZero :=
      S.sqrtDensityRemainder_convergesInProbabilityToZero
    fisherInformationQuadratic := S.fisherInformationQuadratic
    fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
    qmdRemainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    logLikelihood_expansion_ae :=
      vaart1998_eventually_ae_eq_trans_atTop
        S.logLikelihood_eq_sqrtDensityLog_ae S.sqrtDensityLog_expansion_ae
    hellingerScoreVector_tendstoInDistribution :=
      S.hellingerScoreVector_tendstoInDistribution
    hellingerScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
    qmdRemainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A Hellinger density-log source supplies the QMD Fisher-shift source.
-/
def Vaart1998LANHellingerDensityLogSource.quadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw) :
    Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.hellingerDifferentiabilitySource.quadraticMeanDifferentiabilitySource

/--
A Hellinger density-log source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANHellingerDensityLogSource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.hellingerDifferentiabilitySource.leCamStochasticBoundedSource

/--
A Hellinger density-log source yields one-sided contiguity.
-/
theorem Vaart1998LANHellingerDensityLogSource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.hellingerDifferentiabilitySource.contiguitySource

/--
Hellinger density-ratio source.

This source replaces the density-log equality field by the more concrete
Radon-Nikodym identity
`dP_n/dQ_n = (sqrt p_n / sqrt p_0)^2` under `P_n`.  The constructor proves
the density-log equality by taking real logarithms and using
`Real.log_pow`.
-/
structure Vaart1998LANHellingerDensityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- A measure dominating the local square-root density display. -/
  dominatingMeasure : Measure Ω
  /-- The baseline square-root density. -/
  baseSqrtDensity : Ω -> ℝ
  /-- The local square-root densities. -/
  localSqrtDensity : ℕ -> Ω -> ℝ
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under `P_n`. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /--
  Concrete Radon-Nikodym identity for the likelihood ratio in terms of the
  square-root density ratio.
  -/
  likelihoodRatio_toReal_eq_sqrtDensityRatioSq_ae : ∀ᶠ n in atTop,
    (fun ω => (vaart1998_likelihoodRatio (P n) (Q n) ω).toReal) =ᵐ[P n]
      fun ω => (localSqrtDensity n ω / baseSqrtDensity ω) ^ 2
  /-- The square-root density log display has the LAN expansion. -/
  sqrtDensityLog_expansion_ae : ∀ᶠ n in atTop,
    vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
      (localSqrtDensity n) =ᵐ[P n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit P LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P qmdRemainder

/--
A Hellinger density-ratio source supplies the density-log Hellinger source by
taking logarithms of the square-root density-ratio identity.
-/
def Vaart1998LANHellingerDensityRatioSource.densityLogSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw :=
  { dominatingMeasure := S.dominatingMeasure
    baseSqrtDensity := S.baseSqrtDensity
    localSqrtDensity := S.localSqrtDensity
    hellingerScoreVector := S.hellingerScoreVector
    hellingerScoreLimit := S.hellingerScoreLimit
    scoreDirection := S.scoreDirection
    sqrtDensityRemainder := S.sqrtDensityRemainder
    sqrtDensity_expansion_ae := S.sqrtDensity_expansion_ae
    sqrtDensityRemainder_convergesInProbabilityToZero :=
      S.sqrtDensityRemainder_convergesInProbabilityToZero
    fisherInformationQuadratic := S.fisherInformationQuadratic
    fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
    qmdRemainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    logLikelihood_eq_sqrtDensityLog_ae :=
      vaart1998_logLikelihoodRatio_eventually_ae_eq_sqrtDensityLog_of_likelihoodRatio_sq
        S.likelihoodRatio_toReal_eq_sqrtDensityRatioSq_ae
    sqrtDensityLog_expansion_ae := S.sqrtDensityLog_expansion_ae
    hellingerScoreVector_tendstoInDistribution :=
      S.hellingerScoreVector_tendstoInDistribution
    hellingerScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
    qmdRemainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A Hellinger density-ratio source supplies the Hellinger differentiability
source.
-/
def Vaart1998LANHellingerDensityRatioSource.hellingerDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.densityLogSource.hellingerDifferentiabilitySource

/--
A Hellinger density-ratio source supplies the QMD Fisher-shift source.
-/
def Vaart1998LANHellingerDensityRatioSource.quadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.densityLogSource.quadraticMeanDifferentiabilitySource

/--
A Hellinger density-ratio source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANHellingerDensityRatioSource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.densityLogSource.leCamStochasticBoundedSource

/--
A Hellinger density-ratio source yields one-sided contiguity.
-/
theorem Vaart1998LANHellingerDensityRatioSource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.densityLogSource.contiguitySource

/--
Hellinger squared-density-ratio source.

This source replaces the field
`dP_n/dQ_n = (sqrt p_n / sqrt p_0)^2` by the more direct squared-density
ratio display `dP_n/dQ_n = (sqrt p_n)^2 / (sqrt p_0)^2`.  The constructor
uses the algebra identity `a^2 / b^2 = (a/b)^2`.
-/
structure Vaart1998LANHellingerSquaredDensityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- A measure dominating the local square-root density display. -/
  dominatingMeasure : Measure Ω
  /-- The baseline square-root density. -/
  baseSqrtDensity : Ω -> ℝ
  /-- The local square-root densities. -/
  localSqrtDensity : ℕ -> Ω -> ℝ
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under `P_n`. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /--
  Concrete Radon-Nikodym identity for the likelihood ratio as the ratio of
  squared square-root densities.
  -/
  likelihoodRatio_toReal_eq_sqrtDensitySqRatio_ae : ∀ᶠ n in atTop,
    (fun ω => (vaart1998_likelihoodRatio (P n) (Q n) ω).toReal) =ᵐ[P n]
      fun ω => localSqrtDensity n ω ^ 2 / baseSqrtDensity ω ^ 2
  /-- The square-root density log display has the LAN expansion. -/
  sqrtDensityLog_expansion_ae : ∀ᶠ n in atTop,
    vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
      (localSqrtDensity n) =ᵐ[P n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit P LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P qmdRemainder

/--
A Hellinger squared-density-ratio source supplies the Hellinger density-ratio
source.
-/
def Vaart1998LANHellingerSquaredDensityRatioSource.densityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw :=
  { dominatingMeasure := S.dominatingMeasure
    baseSqrtDensity := S.baseSqrtDensity
    localSqrtDensity := S.localSqrtDensity
    hellingerScoreVector := S.hellingerScoreVector
    hellingerScoreLimit := S.hellingerScoreLimit
    scoreDirection := S.scoreDirection
    sqrtDensityRemainder := S.sqrtDensityRemainder
    sqrtDensity_expansion_ae := S.sqrtDensity_expansion_ae
    sqrtDensityRemainder_convergesInProbabilityToZero :=
      S.sqrtDensityRemainder_convergesInProbabilityToZero
    fisherInformationQuadratic := S.fisherInformationQuadratic
    fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
    qmdRemainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    likelihoodRatio_toReal_eq_sqrtDensityRatioSq_ae :=
      vaart1998_likelihoodRatio_eventually_ae_eq_sqrtDensityRatioSq_of_sq_ratio
        S.likelihoodRatio_toReal_eq_sqrtDensitySqRatio_ae
    sqrtDensityLog_expansion_ae := S.sqrtDensityLog_expansion_ae
    hellingerScoreVector_tendstoInDistribution :=
      S.hellingerScoreVector_tendstoInDistribution
    hellingerScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
    qmdRemainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A Hellinger squared-density-ratio source supplies the density-log Hellinger
source.
-/
def Vaart1998LANHellingerSquaredDensityRatioSource.densityLogSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw :=
  S.densityRatioSource.densityLogSource

/--
A Hellinger squared-density-ratio source supplies the Hellinger
differentiability source.
-/
def Vaart1998LANHellingerSquaredDensityRatioSource.hellingerDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.densityRatioSource.hellingerDifferentiabilitySource

/--
A Hellinger squared-density-ratio source supplies the QMD Fisher-shift source.
-/
def Vaart1998LANHellingerSquaredDensityRatioSource.quadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.densityRatioSource.quadraticMeanDifferentiabilitySource

/--
A Hellinger squared-density-ratio source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANHellingerSquaredDensityRatioSource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.densityRatioSource.leCamStochasticBoundedSource

/--
A Hellinger squared-density-ratio source yields one-sided contiguity.
-/
theorem Vaart1998LANHellingerSquaredDensityRatioSource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.densityRatioSource.contiguitySource

/--
Hellinger with-density source.

This source replaces the squared-density-ratio identity by concrete
`withDensity` representations over a common dominating measure:
`P_n = μ.withDensity ((sqrt p_n)^2)` and
`Q_n = μ.withDensity ((sqrt p_0)^2)`.  The constructor derives the
Radon-Nikodym likelihood-ratio display and then reuses the
squared-density-ratio pipeline.
-/
structure Vaart1998LANHellingerWithDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- A common measure dominating the local square-root density display. -/
  dominatingMeasure : Measure Ω
  /-- The dominating measure is sigma-finite, as required by RN ratio lemmas. -/
  dominatingMeasure_sigmaFinite : SigmaFinite dominatingMeasure
  /-- The baseline square-root density. -/
  baseSqrtDensity : Ω -> ℝ
  /-- The local square-root densities. -/
  localSqrtDensity : ℕ -> Ω -> ℝ
  /-- Measurability of the squared local density. -/
  localSqrtDensitySq_measurable : ∀ n : ℕ,
    Measurable fun ω => ENNReal.ofReal (localSqrtDensity n ω ^ 2)
  /-- Measurability of the squared baseline density. -/
  baseSqrtDensitySq_measurable :
    Measurable fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2)
  /-- Local alternatives represented as squared square-root densities. -/
  localMeasure_eq_withDensity : ∀ᶠ n in atTop,
    P n = dominatingMeasure.withDensity
      (fun ω => ENNReal.ofReal (localSqrtDensity n ω ^ 2))
  /-- Baseline measures represented as the squared baseline square-root density. -/
  baseMeasure_eq_withDensity : ∀ᶠ n in atTop,
    Q n = dominatingMeasure.withDensity
      (fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2))
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under `P_n`. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The square-root density log display has the LAN expansion. -/
  sqrtDensityLog_expansion_ae : ∀ᶠ n in atTop,
    vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
      (localSqrtDensity n) =ᵐ[P n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit P LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P qmdRemainder

/--
A Hellinger with-density source supplies the squared-density-ratio source.
-/
def Vaart1998LANHellingerWithDensitySource.squaredDensityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw :=
  letI : SigmaFinite S.dominatingMeasure := S.dominatingMeasure_sigmaFinite
  { dominatingMeasure := S.dominatingMeasure
    baseSqrtDensity := S.baseSqrtDensity
    localSqrtDensity := S.localSqrtDensity
    hellingerScoreVector := S.hellingerScoreVector
    hellingerScoreLimit := S.hellingerScoreLimit
    scoreDirection := S.scoreDirection
    sqrtDensityRemainder := S.sqrtDensityRemainder
    sqrtDensity_expansion_ae := S.sqrtDensity_expansion_ae
    sqrtDensityRemainder_convergesInProbabilityToZero :=
      S.sqrtDensityRemainder_convergesInProbabilityToZero
    fisherInformationQuadratic := S.fisherInformationQuadratic
    fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
    qmdRemainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    likelihoodRatio_toReal_eq_sqrtDensitySqRatio_ae :=
      vaart1998_likelihoodRatio_eventually_ae_eq_sqrtDensitySqRatio_of_withDensity
        (μ := S.dominatingMeasure)
        S.localMeasure_eq_withDensity S.baseMeasure_eq_withDensity
        S.localSqrtDensitySq_measurable S.baseSqrtDensitySq_measurable
        S.ac_eventually
    sqrtDensityLog_expansion_ae := S.sqrtDensityLog_expansion_ae
    hellingerScoreVector_tendstoInDistribution :=
      S.hellingerScoreVector_tendstoInDistribution
    hellingerScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
    qmdRemainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A Hellinger with-density source supplies the density-ratio Hellinger source.
-/
def Vaart1998LANHellingerWithDensitySource.densityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw :=
  S.squaredDensityRatioSource.densityRatioSource

/--
A Hellinger with-density source supplies the density-log Hellinger source.
-/
def Vaart1998LANHellingerWithDensitySource.densityLogSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw :=
  S.squaredDensityRatioSource.densityLogSource

/--
A Hellinger with-density source supplies the Hellinger differentiability
source.
-/
def Vaart1998LANHellingerWithDensitySource.hellingerDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.squaredDensityRatioSource.hellingerDifferentiabilitySource

/--
A Hellinger with-density source supplies the QMD Fisher-shift source.
-/
def Vaart1998LANHellingerWithDensitySource.quadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw) :
    Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.squaredDensityRatioSource.quadraticMeanDifferentiabilitySource

/--
A Hellinger with-density source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANHellingerWithDensitySource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.squaredDensityRatioSource.leCamStochasticBoundedSource

/--
A Hellinger with-density source yields one-sided contiguity.
-/
theorem Vaart1998LANHellingerWithDensitySource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.squaredDensityRatioSource.contiguitySource

/--
Hellinger measurable with-density source.

This source replaces the squared `ENNReal.ofReal` measurability fields by the
more model-facing assumption that the real square-root densities themselves
are measurable.  The constructor derives the squared-density measurability
fields and then reuses the common-`withDensity` source.
-/
structure Vaart1998LANHellingerMeasurableWithDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (P Q : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- A common measure dominating the local square-root density display. -/
  dominatingMeasure : Measure Ω
  /-- The dominating measure is sigma-finite, as required by RN ratio lemmas. -/
  dominatingMeasure_sigmaFinite : SigmaFinite dominatingMeasure
  /-- The baseline square-root density. -/
  baseSqrtDensity : Ω -> ℝ
  /-- The local square-root densities. -/
  localSqrtDensity : ℕ -> Ω -> ℝ
  /-- Measurability of the baseline square-root density. -/
  baseSqrtDensity_measurable : Measurable baseSqrtDensity
  /-- Measurability of the local square-root densities. -/
  localSqrtDensity_measurable : ∀ n : ℕ, Measurable (localSqrtDensity n)
  /-- Local alternatives represented as squared square-root densities. -/
  localMeasure_eq_withDensity : ∀ᶠ n in atTop,
    P n = dominatingMeasure.withDensity
      (fun ω => ENNReal.ofReal (localSqrtDensity n ω ^ 2))
  /-- Baseline measures represented as the squared baseline square-root density. -/
  baseMeasure_eq_withDensity : ∀ᶠ n in atTop,
    Q n = dominatingMeasure.withDensity
      (fun ω => ENNReal.ofReal (baseSqrtDensity ω ^ 2))
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under `P_n`. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The square-root density log display has the LAN expansion. -/
  sqrtDensityLog_expansion_ae : ∀ᶠ n in atTop,
    vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
      (localSqrtDensity n) =ᵐ[P n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit P LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P qmdRemainder

/--
A Hellinger measurable with-density source supplies the common-`withDensity`
source.
-/
def Vaart1998LANHellingerMeasurableWithDensitySource.withDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerWithDensitySource (E := E) P Q LimitLaw :=
  { dominatingMeasure := S.dominatingMeasure
    dominatingMeasure_sigmaFinite := S.dominatingMeasure_sigmaFinite
    baseSqrtDensity := S.baseSqrtDensity
    localSqrtDensity := S.localSqrtDensity
    localSqrtDensitySq_measurable := fun n =>
      vaart1998_measurable_ennreal_ofReal_sq
        (S.localSqrtDensity_measurable n)
    baseSqrtDensitySq_measurable :=
      vaart1998_measurable_ennreal_ofReal_sq
        S.baseSqrtDensity_measurable
    localMeasure_eq_withDensity := S.localMeasure_eq_withDensity
    baseMeasure_eq_withDensity := S.baseMeasure_eq_withDensity
    hellingerScoreVector := S.hellingerScoreVector
    hellingerScoreLimit := S.hellingerScoreLimit
    scoreDirection := S.scoreDirection
    sqrtDensityRemainder := S.sqrtDensityRemainder
    sqrtDensity_expansion_ae := S.sqrtDensity_expansion_ae
    sqrtDensityRemainder_convergesInProbabilityToZero :=
      S.sqrtDensityRemainder_convergesInProbabilityToZero
    fisherInformationQuadratic := S.fisherInformationQuadratic
    fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
    qmdRemainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    sqrtDensityLog_expansion_ae := S.sqrtDensityLog_expansion_ae
    hellingerScoreVector_tendstoInDistribution :=
      S.hellingerScoreVector_tendstoInDistribution
    hellingerScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
    qmdRemainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A Hellinger measurable with-density source supplies the squared-density-ratio
source.
-/
def Vaart1998LANHellingerMeasurableWithDensitySource.squaredDensityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerSquaredDensityRatioSource (E := E) P Q LimitLaw :=
  S.withDensitySource.squaredDensityRatioSource

/--
A Hellinger measurable with-density source supplies the density-ratio
Hellinger source.
-/
def Vaart1998LANHellingerMeasurableWithDensitySource.densityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDensityRatioSource (E := E) P Q LimitLaw :=
  S.withDensitySource.densityRatioSource

/--
A Hellinger measurable with-density source supplies the density-log Hellinger
source.
-/
def Vaart1998LANHellingerMeasurableWithDensitySource.densityLogSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDensityLogSource (E := E) P Q LimitLaw :=
  S.withDensitySource.densityLogSource

/--
A Hellinger measurable with-density source supplies the Hellinger
differentiability source.
-/
def Vaart1998LANHellingerMeasurableWithDensitySource.hellingerDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998LANHellingerDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.withDensitySource.hellingerDifferentiabilitySource

/--
A Hellinger measurable with-density source supplies the QMD Fisher-shift
source.
-/
def Vaart1998LANHellingerMeasurableWithDensitySource.quadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E) P Q LimitLaw :=
  S.withDensitySource.quadraticMeanDifferentiabilitySource

/--
A Hellinger measurable with-density source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANHellingerMeasurableWithDensitySource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q :=
  S.withDensitySource.leCamStochasticBoundedSource

/--
A Hellinger measurable with-density source yields one-sided contiguity.
-/
theorem Vaart1998LANHellingerMeasurableWithDensitySource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {P Q : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [∀ n : ℕ, SigmaFinite (Q n)]
    [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LANHellingerMeasurableWithDensitySource
      (E := E) P Q LimitLaw) :
    Vaart1998ContiguitySource P Q :=
  S.withDensitySource.contiguitySource

/--
Concrete square-root-density Hellinger LAN source.

This source is the model-facing specialization where the local alternatives
and the baseline law are defined directly as squared square-root densities
with respect to one dominating measure.  The representation fields needed by
`Vaart1998LANHellingerMeasurableWithDensitySource` are therefore definitional.
-/
structure Vaart1998LANHellingerConcreteSqrtDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw] where
  /-- The dominating measure is sigma-finite, as required by RN ratio lemmas. -/
  dominatingMeasure_sigmaFinite : SigmaFinite dominatingMeasure
  /-- Measurability of the baseline square-root density. -/
  baseSqrtDensity_measurable : Measurable baseSqrtDensity
  /-- Measurability of the local square-root densities. -/
  localSqrtDensity_measurable : ∀ n : ℕ, Measurable (localSqrtDensity n)
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under the local laws. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- Eventual absolute continuity of local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop,
    vaart1998_localSqrtDensityMeasureSeq dominatingMeasure localSqrtDensity n ≪
      vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure baseSqrtDensity n
  /-- The square-root density log display has the LAN expansion. -/
  sqrtDensityLog_expansion_ae : ∀ᶠ n in atTop,
    vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
      (localSqrtDensity n) =ᵐ[
        vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      qmdRemainder

/--
A concrete square-root-density source supplies the real-measurable
common-`withDensity` source.
-/
def Vaart1998LANHellingerConcreteSqrtDensitySource.measurableWithDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LANHellingerMeasurableWithDensitySource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw :=
  { dominatingMeasure := dominatingMeasure
    dominatingMeasure_sigmaFinite := S.dominatingMeasure_sigmaFinite
    baseSqrtDensity := baseSqrtDensity
    localSqrtDensity := localSqrtDensity
    baseSqrtDensity_measurable := S.baseSqrtDensity_measurable
    localSqrtDensity_measurable := S.localSqrtDensity_measurable
    localMeasure_eq_withDensity := Eventually.of_forall fun _ => rfl
    baseMeasure_eq_withDensity := Eventually.of_forall fun _ => rfl
    hellingerScoreVector := S.hellingerScoreVector
    hellingerScoreLimit := S.hellingerScoreLimit
    scoreDirection := S.scoreDirection
    sqrtDensityRemainder := S.sqrtDensityRemainder
    sqrtDensity_expansion_ae := S.sqrtDensity_expansion_ae
    sqrtDensityRemainder_convergesInProbabilityToZero :=
      S.sqrtDensityRemainder_convergesInProbabilityToZero
    fisherInformationQuadratic := S.fisherInformationQuadratic
    fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
    qmdRemainder := S.qmdRemainder
    ac_eventually := S.ac_eventually
    sqrtDensityLog_expansion_ae := S.sqrtDensityLog_expansion_ae
    hellingerScoreVector_tendstoInDistribution :=
      S.hellingerScoreVector_tendstoInDistribution
    hellingerScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
    qmdRemainder_convergesInProbabilityToZero :=
      S.qmdRemainder_convergesInProbabilityToZero }

/--
A concrete square-root-density source supplies the common-`withDensity`
source.
-/
def Vaart1998LANHellingerConcreteSqrtDensitySource.withDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LANHellingerWithDensitySource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw :=
  S.measurableWithDensitySource.withDensitySource

/--
A concrete square-root-density source supplies the squared-density-ratio
source.
-/
def Vaart1998LANHellingerConcreteSqrtDensitySource.squaredDensityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LANHellingerSquaredDensityRatioSource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw :=
  S.measurableWithDensitySource.squaredDensityRatioSource

/--
A concrete square-root-density source supplies the density-ratio Hellinger
source.
-/
def Vaart1998LANHellingerConcreteSqrtDensitySource.densityRatioSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LANHellingerDensityRatioSource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw :=
  S.measurableWithDensitySource.densityRatioSource

/--
A concrete square-root-density source supplies the density-log Hellinger
source.
-/
def Vaart1998LANHellingerConcreteSqrtDensitySource.densityLogSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LANHellingerDensityLogSource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw :=
  S.measurableWithDensitySource.densityLogSource

/--
A concrete square-root-density source supplies the Hellinger differentiability
source.
-/
def Vaart1998LANHellingerConcreteSqrtDensitySource.hellingerDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LANHellingerDifferentiabilitySource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw :=
  S.measurableWithDensitySource.hellingerDifferentiabilitySource

/--
A concrete square-root-density source supplies the QMD Fisher-shift source.
-/
def Vaart1998LANHellingerConcreteSqrtDensitySource.quadraticMeanDifferentiabilitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LANQuadraticMeanDifferentiabilitySource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw :=
  S.measurableWithDensitySource.quadraticMeanDifferentiabilitySource

/--
A concrete square-root-density source supplies the Chapter 6 Le Cam
stochastic-boundedness source.
-/
theorem Vaart1998LANHellingerConcreteSqrtDensitySource.leCamStochasticBoundedSource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998LogLikelihoodStochasticBoundedContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.measurableWithDensitySource.leCamStochasticBoundedSource

/--
A concrete square-root-density source yields one-sided contiguity.
-/
theorem Vaart1998LANHellingerConcreteSqrtDensitySource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n)]
    [∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n)]
    [IsProbabilityMeasure LimitLaw]
    [∀ n : ℕ,
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n).HaveLebesgueDecomposition
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n)]
    (S : Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.measurableWithDensitySource.contiguitySource

/--
Normalized concrete square-root-density Hellinger LAN source.

This source is the model-facing version of
`Vaart1998LANHellingerConcreteSqrtDensitySource`: callers provide
`L^2(μ)` normalizations for the local and baseline square-root densities and
baseline nonvanishing a.e.  The probability and absolute-continuity inputs
for the concrete source are then derived by the constructors below.
-/
structure Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ) (LimitLaw : Measure Ω')
    [IsProbabilityMeasure LimitLaw] where
  /-- The dominating measure is sigma-finite, as required by RN ratio lemmas. -/
  dominatingMeasure_sigmaFinite : SigmaFinite dominatingMeasure
  /-- Measurability of the baseline square-root density. -/
  baseSqrtDensity_measurable : Measurable baseSqrtDensity
  /-- Measurability of the local square-root densities. -/
  localSqrtDensity_measurable : ∀ n : ℕ, Measurable (localSqrtDensity n)
  /-- Local square-root densities are normalized in `L^2(μ)`. -/
  localSqrtDensity_normalized : ∀ n : ℕ,
    ∫⁻ ω, ENNReal.ofReal (localSqrtDensity n ω ^ 2) ∂dominatingMeasure = 1
  /-- The baseline square-root density is normalized in `L^2(μ)`. -/
  baseSqrtDensity_normalized :
    ∫⁻ ω, ENNReal.ofReal (baseSqrtDensity ω ^ 2) ∂dominatingMeasure = 1
  /-- The baseline square-root density is nonzero almost everywhere. -/
  baseSqrtDensity_nonzero_ae :
    ∀ᵐ ω ∂dominatingMeasure, baseSqrtDensity ω ≠ 0
  /-- Probability instances for the local laws, derived from normalization. -/
  localMeasure_isProbabilityMeasure : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    vaart1998_localSqrtDensityMeasureSeq_isProbabilityMeasure_of_lintegral_eq_one
      (dominatingMeasure := dominatingMeasure)
      (localSqrtDensity := localSqrtDensity)
      localSqrtDensity_normalized
  /-- Probability instances for the baseline laws, derived from normalization. -/
  baseMeasure_isProbabilityMeasure : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    vaart1998_baseSqrtDensityMeasureSeq_isProbabilityMeasure_of_lintegral_eq_one
      (dominatingMeasure := dominatingMeasure)
      (baseSqrtDensity := baseSqrtDensity)
      baseSqrtDensity_normalized
  /-- Eventual absolute continuity, derived from baseline nonvanishing. -/
  ac_eventually : ∀ᶠ n in atTop,
    vaart1998_localSqrtDensityMeasureSeq dominatingMeasure localSqrtDensity n ≪
      vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure baseSqrtDensity n :=
    vaart1998_localSqrtDensityMeasureSeq_ac_eventually_of_base_ae_ne_zero
      (dominatingMeasure := dominatingMeasure)
      (baseSqrtDensity := baseSqrtDensity)
      (localSqrtDensity := localSqrtDensity)
      baseSqrtDensity_measurable
      baseSqrtDensity_nonzero_ae
  /-- The vector-valued Hellinger score array. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The Gaussian vector limit of the Hellinger score array. -/
  hellingerScoreLimit : Ω' -> E
  /-- The local score direction. -/
  scoreDirection : E →L[ℝ] ℝ
  /-- The square-root density expansion remainder. -/
  sqrtDensityRemainder : ℕ -> Ω -> ℝ
  /-- The density-level Hellinger expansion of square-root densities. -/
  sqrtDensity_expansion_ae : ∀ᶠ n in atTop,
    localSqrtDensity n =ᵐ[dominatingMeasure]
      fun ω =>
        baseSqrtDensity ω +
          scoreDirection (hellingerScoreVector n ω) / 2 +
            sqrtDensityRemainder n ω
  /-- The square-root density remainder is negligible under the local laws. -/
  sqrtDensityRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      sqrtDensityRemainder
  /-- The quadratic Fisher-information term `I(h, h)`. -/
  fisherInformationQuadratic : ℝ
  /-- The quadratic Fisher-information term is nonnegative. -/
  fisherInformationQuadratic_nonneg : 0 ≤ fisherInformationQuadratic
  /-- The LAN log-likelihood remainder induced by the Hellinger expansion. -/
  qmdRemainder : ℕ -> Ω -> ℝ
  /-- The square-root density log display has the LAN expansion. -/
  sqrtDensityLog_expansion_ae : ∀ᶠ n in atTop,
    vaart1998_sqrtDensityLogLikelihoodDisplay baseSqrtDensity
      (localSqrtDensity n) =ᵐ[
        vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n]
      fun ω =>
        scoreDirection (hellingerScoreVector n ω) +
          (-(fisherInformationQuadratic / 2)) + qmdRemainder n ω
  /-- The Hellinger score array converges weakly to its Gaussian vector limit. -/
  hellingerScoreVector_tendstoInDistribution :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      localMeasure_isProbabilityMeasure
    TendstoInDistribution hellingerScoreVector atTop hellingerScoreLimit
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      LimitLaw
  /-- The Hellinger score limit is Gaussian. -/
  hellingerScoreLimit_gaussian : HasGaussianLaw hellingerScoreLimit LimitLaw
  /-- The LAN log-likelihood remainder is `o_{P_n}(1)`. -/
  qmdRemainder_convergesInProbabilityToZero :
    Vaart1998MeasureSeqConvergesInProbabilityToZero
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      qmdRemainder

/--
A normalized concrete square-root-density source supplies the concrete source.
-/
def Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource.concreteSqrtDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.localMeasure_isProbabilityMeasure
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n) :=
      S.baseMeasure_isProbabilityMeasure
    Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.localMeasure_isProbabilityMeasure
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    S.baseMeasure_isProbabilityMeasure
  exact
    { dominatingMeasure_sigmaFinite := S.dominatingMeasure_sigmaFinite
      baseSqrtDensity_measurable := S.baseSqrtDensity_measurable
      localSqrtDensity_measurable := S.localSqrtDensity_measurable
      hellingerScoreVector := S.hellingerScoreVector
      hellingerScoreLimit := S.hellingerScoreLimit
      scoreDirection := S.scoreDirection
      sqrtDensityRemainder := S.sqrtDensityRemainder
      sqrtDensity_expansion_ae := S.sqrtDensity_expansion_ae
      sqrtDensityRemainder_convergesInProbabilityToZero :=
        S.sqrtDensityRemainder_convergesInProbabilityToZero
      fisherInformationQuadratic := S.fisherInformationQuadratic
      fisherInformationQuadratic_nonneg := S.fisherInformationQuadratic_nonneg
      qmdRemainder := S.qmdRemainder
      ac_eventually := S.ac_eventually
      sqrtDensityLog_expansion_ae := S.sqrtDensityLog_expansion_ae
      hellingerScoreVector_tendstoInDistribution :=
        S.hellingerScoreVector_tendstoInDistribution
      hellingerScoreLimit_gaussian := S.hellingerScoreLimit_gaussian
      qmdRemainder_convergesInProbabilityToZero :=
        S.qmdRemainder_convergesInProbabilityToZero }

/--
A normalized concrete square-root-density source supplies the real-measurable
common-`withDensity` source.
-/
def Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource.measurableWithDensitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.localMeasure_isProbabilityMeasure
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n) :=
      S.baseMeasure_isProbabilityMeasure
    Vaart1998LANHellingerMeasurableWithDensitySource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      LimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.localMeasure_isProbabilityMeasure
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    S.baseMeasure_isProbabilityMeasure
  exact S.concreteSqrtDensitySource.measurableWithDensitySource

/--
A normalized concrete square-root-density source yields one-sided contiguity.
-/
theorem Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource.contiguitySource
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ} {LimitLaw : Measure Ω'}
    [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity LimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.localMeasure_isProbabilityMeasure
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    S.baseMeasure_isProbabilityMeasure
  haveI : ∀ n : ℕ,
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n).HaveLebesgueDecomposition
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n) :=
    vaart1998_localSqrtDensityMeasureSeq_haveLebesgueDecomposition_of_lintegral_eq_one
      (dominatingMeasure := dominatingMeasure)
      (baseSqrtDensity := baseSqrtDensity)
      (localSqrtDensity := localSqrtDensity)
      S.localSqrtDensity_normalized
      S.baseSqrtDensity_normalized
  exact S.concreteSqrtDensitySource.contiguitySource

end AsymptoticStatistics
end StatInference
