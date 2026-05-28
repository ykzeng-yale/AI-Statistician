import StatInference.EmpiricalProcess.EndpointSamples
import StatInference.Matching.WDSM.AggregateDecomposition

/-!
# Chen-Han cover-ball sampling counts

This module isolates the fixed cover-ball sampling-count boundary used by the
Chen-Han/WDSM radius route.  It proves the deterministic conversion from
metric-ball indicator sums to normalized donor counts, and a narrow iid
strong-law statement for fixed metric balls.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators Topology Function

variable {Index Unit Score Cell : Type*}

/-- Real-valued indicator of a closed metric ball. -/
noncomputable def metricClosedBallIndicator [PseudoMetricSpace Score]
    (center : Score) (radius : Real) : Score -> Real :=
  Set.indicator {point : Score | dist center point ≤ radius}
    (fun _point => (1 : Real))

/-- Measurability of a metric-ball indicator from measurability of the ball. -/
theorem measurable_metricClosedBallIndicator
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    (center : Score) (radius : Real)
    (hball :
      MeasurableSet {point : Score | dist center point ≤ radius}) :
    Measurable (metricClosedBallIndicator center radius) := by
  simpa [metricClosedBallIndicator] using
    (measurable_indicator_const_iff (1 : Real)).2 hball

/-- Metric-ball indicators are integrable under finite measures. -/
theorem integrable_metricClosedBallIndicator
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    (μ : Measure Score) [IsFiniteMeasure μ]
    (center : Score) (radius : Real)
    (hball :
      MeasurableSet {point : Score | dist center point ≤ radius}) :
    Integrable (metricClosedBallIndicator center radius) μ := by
  simpa [metricClosedBallIndicator] using
    (integrable_const (1 : Real)).indicator hball

/--
The empirical average of a metric-ball indicator is the normalized finite
metric-ball count.
-/
theorem empiricalAverage_metricClosedBallIndicator_eq_count_div
    [PseudoMetricSpace Score]
    {sampleSize : Nat}
    (sample : SampleAt Score sampleSize)
    (center : Score) (radius : Real) :
    empiricalAverage sample (metricClosedBallIndicator center radius) =
      (((Finset.univ.filter
        (fun index : Fin sampleSize =>
          dist center (sample index) ≤ radius)).card : Real) /
        (sampleSize : Real)) := by
  classical
  unfold empiricalAverage metricClosedBallIndicator
  have hsum :
      (∑ index : Fin sampleSize,
        Set.indicator {point : Score | dist center point ≤ radius}
          (fun _point => (1 : Real)) (sample index)) =
        (((Finset.univ.filter
          (fun index : Fin sampleSize =>
            dist center (sample index) ≤ radius)).card : Real)) := by
    calc
      (∑ index : Fin sampleSize,
        Set.indicator {point : Score | dist center point ≤ radius}
          (fun _point => (1 : Real)) (sample index))
          =
            ∑ index ∈ (Finset.univ.filter
              (fun index : Fin sampleSize =>
                dist center (sample index) ≤ radius)), (1 : Real) := by
              rw [Finset.sum_filter]
              simp [Set.indicator]
      _ =
          (((Finset.univ.filter
            (fun index : Fin sampleSize =>
              dist center (sample index) ≤ radius)).card : Real)) := by
            simp
  simp [hsum]

/--
Iid donor observations satisfy the fixed closed-ball normalized-count strong
law, once the ball is measurable and its population mass is identified.
-/
theorem metricClosedBall_count_div_tendsto_ae_of_iid
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (center : Score) (radius cellMass : Real)
    (hball :
      MeasurableSet {point : Score | dist center point ≤ radius})
    (hmass :
      ∫ point, metricClosedBallIndicator center radius point ∂P =
        cellMass)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun sampleSize : Nat =>
          (((Finset.univ.filter
            (fun index : Fin sampleSize =>
              dist center (X index.val ω) ≤ radius)).card : Real) /
            (sampleSize : Real)))
        atTop (nhds cellMass) := by
  have hindicator :
      ∀ᵐ ω ∂μ,
        Tendsto
          (fun sampleSize : Nat =>
            empiricalAverage (samplePath X ω sampleSize)
              (metricClosedBallIndicator center radius) -
              ∫ point, metricClosedBallIndicator center radius point ∂P)
          atTop (nhds 0) :=
    endpoint_empiricalAverage_sub_population_tendsto_zero_ae_of_iid
      X (metricClosedBallIndicator center radius)
      ((measurable_metricClosedBallIndicator center radius hball).aemeasurable)
      (integrable_metricClosedBallIndicator P center radius hball)
      hLaw hindep
  filter_upwards [hindicator] with ω hω
  have haverage :
      Tendsto
        (fun sampleSize : Nat =>
          empiricalAverage (samplePath X ω sampleSize)
            (metricClosedBallIndicator center radius))
        atTop
        (nhds
          (∫ point, metricClosedBallIndicator center radius point ∂P)) := by
    simpa [sub_eq_add_neg, add_assoc] using
      hω.add
        (tendsto_const_nhds :
          Tendsto
            (fun _sampleSize : Nat =>
              ∫ point, metricClosedBallIndicator center radius point ∂P)
            atTop
            (nhds
              (∫ point,
                metricClosedBallIndicator center radius point ∂P)))
  have hcount :
      Tendsto
        (fun sampleSize : Nat =>
          (((Finset.univ.filter
            (fun index : Fin sampleSize =>
              dist center (X index.val ω) ≤ radius)).card : Real) /
            (sampleSize : Real)))
        atTop
        (nhds
          (∫ point, metricClosedBallIndicator center radius point ∂P)) := by
    convert haverage using 1
    ext sampleSize
    rw [empiricalAverage_metricClosedBallIndicator_eq_count_div]
    simp [samplePath]
  simpa [hmass] using hcount

/--
Finite-cover version of the iid fixed-ball normalized-count strong law.
This is the stochastic sublemma for fixed centers and fixed donor radii.
-/
theorem fixed_cover_metricClosedBall_count_div_tendsto_ae_of_iid
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (cover : Finset Cell)
    (center : Cell -> Score)
    (radius cellMass : Cell -> Real)
    (hball :
      ∀ cell, cell ∈ cover ->
        MeasurableSet {point : Score |
          dist (center cell) point ≤ radius cell})
    (hmass :
      ∀ cell, cell ∈ cover ->
        ∫ point,
          metricClosedBallIndicator (center cell) (radius cell) point ∂P =
          cellMass cell)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    ∀ᵐ ω ∂μ,
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun sampleSize : Nat =>
            (((Finset.univ.filter
              (fun index : Fin sampleSize =>
                dist (center cell) (X index.val ω) ≤
                  radius cell)).card : Real) /
              (sampleSize : Real)))
          atTop (nhds (cellMass cell)) :=
  (Filter.eventually_all_finset cover).mpr
    (fun cell hcell =>
      metricClosedBall_count_div_tendsto_ae_of_iid
        X (center cell) (radius cell) (cellMass cell)
        (hball cell hcell) (hmass cell hcell) hLaw hindep)

/--
A constant-weight metric-ball indicator sum is the constant weight times the
finite metric-ball count.
-/
theorem weightedSum_metricClosedBallIndicator_constant_weight_eq
    [PseudoMetricSpace Score]
    (donorSet : Finset Unit)
    (score : Unit -> Score)
    (center : Score) (radius normalizer : Real) :
    weightedSum donorSet (fun _donor => normalizer)
        (fun donor => metricClosedBallIndicator center radius (score donor)) =
      normalizer *
        (((donorSet.filter
          (fun donor => dist center (score donor) ≤ radius)).card : Real)) := by
  classical
  unfold weightedSum metricClosedBallIndicator
  calc
    (∑ donor ∈ donorSet,
      normalizer *
        Set.indicator {point : Score | dist center point ≤ radius}
          (fun _point => (1 : Real)) (score donor))
        =
          ∑ donor ∈ (donorSet.filter
            (fun donor => dist center (score donor) ≤ radius)), normalizer := by
          rw [Finset.sum_filter]
          simp [Set.indicator]
    _ =
        normalizer *
          (((donorSet.filter
            (fun donor => dist center (score donor) ≤ radius)).card :
            Real)) := by
          rw [Finset.sum_const, nsmul_eq_mul]
          ring

/--
Normalized metric-ball counts are constant-inverse-sample-size weighted sums of
metric-ball indicators.
-/
theorem normalized_metricClosedBall_count_eq_weightedSum_indicator_inv
    [PseudoMetricSpace Score]
    (donorSet : Finset Unit)
    (score : Unit -> Score)
    (center : Score) (radius sampleSize : Real) :
    (((donorSet.filter
      (fun donor => dist center (score donor) ≤ radius)).card : Real) /
        sampleSize) =
      weightedSum donorSet (fun _donor => sampleSize⁻¹)
        (fun donor => metricClosedBallIndicator center radius (score donor)) := by
  rw [weightedSum_metricClosedBallIndicator_constant_weight_eq]
  rw [div_eq_mul_inv, mul_comm]

/--
The iid fixed-cover count theorem also supplies the exact metric-ball
indicator-sum convergence premise used by the WDSM radius count bridge, for
finite donor sets indexed by `Fin sampleSize`.
-/
theorem fixed_cover_metricClosedBallIndicator_weightedSum_tendsto_ae_of_iid
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (cover : Finset Cell)
    (center : Cell -> Score)
    (radius cellMass : Cell -> Real)
    (hball :
      ∀ cell, cell ∈ cover ->
        MeasurableSet {point : Score |
          dist (center cell) point ≤ radius cell})
    (hmass :
      ∀ cell, cell ∈ cover ->
        ∫ point,
          metricClosedBallIndicator (center cell) (radius cell) point ∂P =
          cellMass cell)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X)) :
    ∀ᵐ ω ∂μ,
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun sampleSize : Nat =>
            weightedSum (Finset.univ : Finset (Fin sampleSize))
              (fun _donor => (sampleSize : Real)⁻¹)
              (fun donor =>
                metricClosedBallIndicator (center cell) (radius cell)
                  (X donor.val ω)))
          atTop (nhds (cellMass cell)) := by
  filter_upwards
    [fixed_cover_metricClosedBall_count_div_tendsto_ae_of_iid
      X cover center radius cellMass hball hmass hLaw hindep] with ω hcount
  intro cell hcell
  have hcell_count :
      Tendsto
        (fun sampleSize : Nat =>
          (((Finset.univ.filter
            (fun index : Fin sampleSize =>
              dist (center cell) (X index.val ω) ≤
                radius cell)).card : Real) /
            (sampleSize : Real)))
        atTop (nhds (cellMass cell)) :=
    hcount cell hcell
  convert hcell_count using 1
  ext sampleSize
  exact
    (normalized_metricClosedBall_count_eq_weightedSum_indicator_inv
      (Finset.univ : Finset (Fin sampleSize))
      (fun donor : Fin sampleSize => X donor.val ω)
      (center cell) (radius cell) (sampleSize : Real)).symm

/--
Metric-ball indicator-sum convergence gives the normalized cover-ball donor
count convergence used by the radius-count bridge.
-/
theorem tendsto_cover_ball_count_div_sampleSize_of_tendsto_metricClosedBallIndicator_weightedSum
    {l : Filter Index} [PseudoMetricSpace Score]
    (donorSet : Index -> Finset Unit)
    (score : Index -> Unit -> Score)
    (center : Index -> Cell -> Score)
    (donorRadius sampleSize : Index -> Real)
    (cell : Cell) (cellMass : Real)
    (hindicator :
      Tendsto
        (fun index =>
          weightedSum (donorSet index)
            (fun _donor => (sampleSize index)⁻¹)
            (fun donor =>
              metricClosedBallIndicator
                (center index cell) (donorRadius index)
                (score index donor)))
        l (nhds cellMass)) :
    Tendsto
      (fun index =>
        (((donorSet index).filter
          (fun donor =>
            dist (center index cell) (score index donor) ≤
              donorRadius index)).card : Real) /
          sampleSize index)
      l (nhds cellMass) := by
  convert hindicator using 1
  ext index
  exact
    normalized_metricClosedBall_count_eq_weightedSum_indicator_inv
      (donorSet index) (score index) (center index cell)
      (donorRadius index) (sampleSize index)

/--
Fixed finite-cover version: cellwise metric-ball indicator LLNs supply the
cellwise normalized donor-count convergences.
-/
theorem fixed_cover_normalized_count_tendsto_of_metricClosedBallIndicator_weightedSum_tendsto
    {l : Filter Index} [PseudoMetricSpace Score]
    (donorSet : Index -> Finset Unit)
    (cover : Finset Cell)
    (score : Index -> Unit -> Score)
    (center : Index -> Cell -> Score)
    (donorRadius sampleSize : Index -> Real)
    (cellMass : Cell -> Real)
    (hindicator :
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun index =>
            weightedSum (donorSet index)
              (fun _donor => (sampleSize index)⁻¹)
              (fun donor =>
                metricClosedBallIndicator
                  (center index cell) (donorRadius index)
                  (score index donor)))
          l (nhds (cellMass cell))) :
    ∀ cell, cell ∈ cover ->
      Tendsto
        (fun index =>
          (((donorSet index).filter
            (fun donor =>
              dist (center index cell) (score index donor) ≤
                donorRadius index)).card : Real) /
            sampleSize index)
        l (nhds (cellMass cell)) := by
  intro cell hcell
  exact
    tendsto_cover_ball_count_div_sampleSize_of_tendsto_metricClosedBallIndicator_weightedSum
      donorSet score center donorRadius sampleSize cell (cellMass cell)
      (hindicator cell hcell)

/--
Iid fixed-cover positive-mass metric balls give the eventual raw donor-count
lower bound, after a deterministic lower-mass and matching-count scaling
condition.  This is the fixed-ball binomial/LLN route before the WDSM-specific
moving-ball or survey-design extension.
-/
theorem eventually_cover_cell_count_lower_bound_ae_of_iid_fixed_metricClosedBalls
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (cover : Finset Cell)
    (center : Cell -> Score)
    (radius cellMass cellMassLower : Cell -> Real)
    (minDonors : Nat -> Nat)
    (hball :
      ∀ cell, cell ∈ cover ->
        MeasurableSet {point : Score |
          dist (center cell) point ≤ radius cell})
    (hmass :
      ∀ cell, cell ∈ cover ->
        ∫ point,
          metricClosedBallIndicator (center cell) (radius cell) point ∂P =
          cellMass cell)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (hlower_lt_mass :
      ∀ cell, cell ∈ cover -> cellMassLower cell < cellMass cell)
    (hminDonors_le :
      ∀ᶠ sampleSize in atTop,
        ∀ cell, cell ∈ cover ->
          (minDonors sampleSize : Real) ≤
            cellMassLower cell * (sampleSize : Real)) :
    ∀ᵐ ω ∂μ,
      ∀ᶠ sampleSize in atTop,
        ∀ cell, cell ∈ cover ->
          minDonors sampleSize ≤
            ((Finset.univ.filter
              (fun donor : Fin sampleSize =>
                dist (center cell) (X donor.val ω) ≤
                  radius cell)).card) := by
  have hsampleSize_pos :
      ∀ᶠ sampleSize : Nat in atTop, 0 < (sampleSize : Real) := by
    filter_upwards [eventually_ge_atTop 1] with sampleSize hsampleSize
    have hsampleSize_real : (1 : Real) ≤ sampleSize := by
      exact_mod_cast hsampleSize
    exact lt_of_lt_of_le zero_lt_one hsampleSize_real
  filter_upwards
    [fixed_cover_metricClosedBall_count_div_tendsto_ae_of_iid
      X cover center radius cellMass hball hmass hLaw hindep] with ω hcount
  have hnormalized_lower :
      ∀ᶠ sampleSize in atTop,
        ∀ cell, cell ∈ cover ->
          cellMassLower cell ≤
            (((Finset.univ.filter
              (fun donor : Fin sampleSize =>
                dist (center cell) (X donor.val ω) ≤
                  radius cell)).card : Real) /
              (sampleSize : Real)) :=
    (Filter.eventually_all_finset cover).mpr
      (fun cell hcell =>
        (hcount cell hcell).eventually
          (eventually_ge_nhds (hlower_lt_mass cell hcell)))
  filter_upwards [hsampleSize_pos, hminDonors_le, hnormalized_lower]
    with sampleSize hsampleSize_pos_index hminDonors_le_index
      hnormalized_lower_index
  intro cell hcell
  let count : Nat :=
    ((Finset.univ.filter
      (fun donor : Fin sampleSize =>
        dist (center cell) (X donor.val ω) ≤ radius cell)).card)
  have hmass_sample_le_count :
      cellMassLower cell * (sampleSize : Real) ≤ (count : Real) := by
    have hmul :
        cellMassLower cell * (sampleSize : Real) ≤
          ((((Finset.univ.filter
            (fun donor : Fin sampleSize =>
              dist (center cell) (X donor.val ω) ≤
                radius cell)).card : Real) /
            (sampleSize : Real)) * (sampleSize : Real)) :=
      mul_le_mul_of_nonneg_right
        (hnormalized_lower_index cell hcell) hsampleSize_pos_index.le
    calc
      cellMassLower cell * (sampleSize : Real)
          ≤
            ((((Finset.univ.filter
              (fun donor : Fin sampleSize =>
                dist (center cell) (X donor.val ω) ≤
                  radius cell)).card : Real) /
              (sampleSize : Real)) * (sampleSize : Real)) := hmul
      _ = (count : Real) := by
            dsimp [count]
            field_simp [hsampleSize_pos_index.ne']
  have hmin_le_count_real :
      (minDonors sampleSize : Real) ≤ (count : Real) :=
    le_trans (hminDonors_le_index cell hcell) hmass_sample_le_count
  change minDonors sampleSize ≤ count
  exact_mod_cast hmin_le_count_real

/--
A reusable coupling interface for finite-prefix donor-score arrays.  It
separates the deterministic fact that the finite sample is a prefix of an
infinite actual donor-score process from the probabilistic coupling of that
process to an iid reference score process.
-/
structure FinitePrefixScoreCoupling
    {Ω Score : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω)
    (iidScore : Nat -> Ω -> Score)
    (actualScore : (sampleSize : Nat) -> Fin sampleSize -> Ω -> Score) where
  actualProcess : Nat -> Ω -> Score
  prefix_eq :
    ∀ᵐ ω ∂μ,
      ∀ sampleSize (donor : Fin sampleSize),
        actualScore sampleSize donor ω = actualProcess donor.val ω
  process_eq_iid :
    ∀ᵐ ω ∂μ,
      ∀ index : Nat, actualProcess index ω = iidScore index ω

namespace FinitePrefixScoreCoupling

/--
A finite-prefix coupling structure implies the eventual pathwise coupling
premise used by the fixed-ball iid transport theorems.
-/
theorem eventually_actualScore_eq_iid
    {Ω Score : Type*} [MeasurableSpace Ω]
    {μ : Measure Ω}
    {iidScore : Nat -> Ω -> Score}
    {actualScore : (sampleSize : Nat) -> Fin sampleSize -> Ω -> Score}
    (coupling : FinitePrefixScoreCoupling μ iidScore actualScore) :
    ∀ᵐ ω ∂μ,
      ∀ᶠ sampleSize in atTop,
        ∀ donor : Fin sampleSize,
          actualScore sampleSize donor ω = iidScore donor.val ω := by
  filter_upwards [coupling.prefix_eq, coupling.process_eq_iid]
    with ω hprefix hprocess_eq_iid
  exact Eventually.of_forall
    (fun sampleSize donor => by
      rw [hprefix sampleSize donor, hprocess_eq_iid donor.val])

end FinitePrefixScoreCoupling

/--
Pathwise coupling transport from the fixed iid score process to an actual
finite-prefix donor-score array.  If the actual donor scores are eventually
equal to the iid process on every finite prefix, then the fixed-ball iid
indicator-sum LLN transfers to the actual donor-score array.
-/
theorem fixed_cover_metricClosedBallIndicator_weightedSum_tendsto_ae_of_iid_coupled_actual_scores
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (actualScore : (sampleSize : Nat) -> Fin sampleSize -> Ω -> Score)
    (cover : Finset Cell)
    (center : Cell -> Score)
    (radius cellMass : Cell -> Real)
    (hball :
      ∀ cell, cell ∈ cover ->
        MeasurableSet {point : Score |
          dist (center cell) point ≤ radius cell})
    (hmass :
      ∀ cell, cell ∈ cover ->
        ∫ point,
          metricClosedBallIndicator (center cell) (radius cell) point ∂P =
          cellMass cell)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (hactual_eq_iid :
      ∀ᵐ ω ∂μ,
        ∀ᶠ sampleSize in atTop,
          ∀ donor : Fin sampleSize,
            actualScore sampleSize donor ω = X donor.val ω) :
    ∀ᵐ ω ∂μ,
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun sampleSize : Nat =>
            weightedSum (Finset.univ : Finset (Fin sampleSize))
              (fun _donor => (sampleSize : Real)⁻¹)
              (fun donor =>
                metricClosedBallIndicator (center cell) (radius cell)
                  (actualScore sampleSize donor ω)))
          atTop (nhds (cellMass cell)) := by
  filter_upwards
    [fixed_cover_metricClosedBallIndicator_weightedSum_tendsto_ae_of_iid
      X cover center radius cellMass hball hmass hLaw hindep,
    hactual_eq_iid] with ω hiid hactual_eq_iid_ω
  intro cell hcell
  have heq :
      (fun sampleSize : Nat =>
        weightedSum (Finset.univ : Finset (Fin sampleSize))
          (fun _donor => (sampleSize : Real)⁻¹)
          (fun donor =>
            metricClosedBallIndicator (center cell) (radius cell)
              (actualScore sampleSize donor ω))) =ᶠ[atTop]
      (fun sampleSize : Nat =>
        weightedSum (Finset.univ : Finset (Fin sampleSize))
          (fun _donor => (sampleSize : Real)⁻¹)
          (fun donor =>
            metricClosedBallIndicator (center cell) (radius cell)
              (X donor.val ω))) := by
    filter_upwards [hactual_eq_iid_ω] with sampleSize hsampleSize_eq
    exact
      weightedSum_congr_on_sample
        (Finset.univ : Finset (Fin sampleSize))
        (fun _donor => (sampleSize : Real)⁻¹)
        (fun donor =>
          metricClosedBallIndicator (center cell) (radius cell)
            (actualScore sampleSize donor ω))
        (fun donor =>
          metricClosedBallIndicator (center cell) (radius cell)
            (X donor.val ω))
        (fun donor _hdonor => by simp [hsampleSize_eq donor])
  exact (hiid cell hcell).congr' heq.symm

/--
Pathwise coupling transport for the raw eventual cover-cell count lower bound.
This is the fixed-ball iid theorem lifted to an actual finite-prefix donor-score
array under eventual pathwise equality to the iid score process.
-/
theorem eventually_cover_cell_count_lower_bound_ae_of_iid_fixed_metricClosedBalls_coupled_actual_scores
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (actualScore : (sampleSize : Nat) -> Fin sampleSize -> Ω -> Score)
    (cover : Finset Cell)
    (center : Cell -> Score)
    (radius cellMass cellMassLower : Cell -> Real)
    (minDonors : Nat -> Nat)
    (hball :
      ∀ cell, cell ∈ cover ->
        MeasurableSet {point : Score |
          dist (center cell) point ≤ radius cell})
    (hmass :
      ∀ cell, cell ∈ cover ->
        ∫ point,
          metricClosedBallIndicator (center cell) (radius cell) point ∂P =
          cellMass cell)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (hlower_lt_mass :
      ∀ cell, cell ∈ cover -> cellMassLower cell < cellMass cell)
    (hminDonors_le :
      ∀ᶠ sampleSize in atTop,
        ∀ cell, cell ∈ cover ->
          (minDonors sampleSize : Real) ≤
            cellMassLower cell * (sampleSize : Real))
    (hactual_eq_iid :
      ∀ᵐ ω ∂μ,
        ∀ᶠ sampleSize in atTop,
          ∀ donor : Fin sampleSize,
            actualScore sampleSize donor ω = X donor.val ω) :
    ∀ᵐ ω ∂μ,
      ∀ᶠ sampleSize in atTop,
        ∀ cell, cell ∈ cover ->
          minDonors sampleSize ≤
            ((Finset.univ.filter
              (fun donor : Fin sampleSize =>
                dist (center cell) (actualScore sampleSize donor ω) ≤
                  radius cell)).card) := by
  filter_upwards
    [eventually_cover_cell_count_lower_bound_ae_of_iid_fixed_metricClosedBalls
      X cover center radius cellMass cellMassLower minDonors hball hmass
      hLaw hindep hlower_lt_mass hminDonors_le,
    hactual_eq_iid] with ω hiid hactual_eq_iid_ω
  filter_upwards [hiid, hactual_eq_iid_ω]
    with sampleSize hiid_sampleSize hactual_eq_iid_sampleSize
  intro cell hcell
  have hcard_eq :
      ((Finset.univ.filter
        (fun donor : Fin sampleSize =>
          dist (center cell) (actualScore sampleSize donor ω) ≤
            radius cell)).card) =
      ((Finset.univ.filter
        (fun donor : Fin sampleSize =>
          dist (center cell) (X donor.val ω) ≤ radius cell)).card) := by
    apply congrArg Finset.card
    ext donor
    simp [hactual_eq_iid_sampleSize donor]
  rw [hcard_eq]
  exact hiid_sampleSize cell hcell

/--
Finite-prefix coupling version of the fixed iid indicator-sum transport.  This
replaces the eventual finite-prefix equality premise by a reusable coupling
object.
-/
theorem fixed_cover_metricClosedBallIndicator_weightedSum_tendsto_ae_of_iid_finitePrefixScoreCoupling
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (actualScore : (sampleSize : Nat) -> Fin sampleSize -> Ω -> Score)
    (cover : Finset Cell)
    (center : Cell -> Score)
    (radius cellMass : Cell -> Real)
    (hball :
      ∀ cell, cell ∈ cover ->
        MeasurableSet {point : Score |
          dist (center cell) point ≤ radius cell})
    (hmass :
      ∀ cell, cell ∈ cover ->
        ∫ point,
          metricClosedBallIndicator (center cell) (radius cell) point ∂P =
          cellMass cell)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (coupling : FinitePrefixScoreCoupling μ X actualScore) :
    ∀ᵐ ω ∂μ,
      ∀ cell, cell ∈ cover ->
        Tendsto
          (fun sampleSize : Nat =>
            weightedSum (Finset.univ : Finset (Fin sampleSize))
              (fun _donor => (sampleSize : Real)⁻¹)
              (fun donor =>
                metricClosedBallIndicator (center cell) (radius cell)
                  (actualScore sampleSize donor ω)))
          atTop (nhds (cellMass cell)) :=
  fixed_cover_metricClosedBallIndicator_weightedSum_tendsto_ae_of_iid_coupled_actual_scores
    X actualScore cover center radius cellMass hball hmass hLaw hindep
    coupling.eventually_actualScore_eq_iid

/--
Finite-prefix coupling version of the fixed iid raw cover-cell count lower
bound.  The remaining probabilistic task is proving the coupling object from
the concrete WDSM donor sampling law.
-/
theorem eventually_cover_cell_count_lower_bound_ae_of_iid_fixed_metricClosedBalls_finitePrefixScoreCoupling
    {Ω : Type*} [MeasurableSpace Ω]
    [MeasurableSpace Score] [PseudoMetricSpace Score]
    {μ : Measure Ω} {P : Measure Score} [IsFiniteMeasure P]
    (X : Nat -> Ω -> Score)
    (actualScore : (sampleSize : Nat) -> Fin sampleSize -> Ω -> Score)
    (cover : Finset Cell)
    (center : Cell -> Score)
    (radius cellMass cellMassLower : Cell -> Real)
    (minDonors : Nat -> Nat)
    (hball :
      ∀ cell, cell ∈ cover ->
        MeasurableSet {point : Score |
          dist (center cell) point ≤ radius cell})
    (hmass :
      ∀ cell, cell ∈ cover ->
        ∫ point,
          metricClosedBallIndicator (center cell) (radius cell) point ∂P =
          cellMass cell)
    (hLaw : ∀ index, HasLaw (X index) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (hlower_lt_mass :
      ∀ cell, cell ∈ cover -> cellMassLower cell < cellMass cell)
    (hminDonors_le :
      ∀ᶠ sampleSize in atTop,
        ∀ cell, cell ∈ cover ->
          (minDonors sampleSize : Real) ≤
            cellMassLower cell * (sampleSize : Real))
    (coupling : FinitePrefixScoreCoupling μ X actualScore) :
    ∀ᵐ ω ∂μ,
      ∀ᶠ sampleSize in atTop,
        ∀ cell, cell ∈ cover ->
          minDonors sampleSize ≤
            ((Finset.univ.filter
              (fun donor : Fin sampleSize =>
                dist (center cell) (actualScore sampleSize donor ω) ≤
                  radius cell)).card) :=
  eventually_cover_cell_count_lower_bound_ae_of_iid_fixed_metricClosedBalls_coupled_actual_scores
    X actualScore cover center radius cellMass cellMassLower minDonors hball
    hmass hLaw hindep hlower_lt_mass hminDonors_le
    coupling.eventually_actualScore_eq_iid

end WDSM
end Matching
end StatInference
