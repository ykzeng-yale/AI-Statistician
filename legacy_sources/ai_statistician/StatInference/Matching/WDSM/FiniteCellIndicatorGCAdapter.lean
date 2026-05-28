import StatInference.EmpiricalProcess.GlivenkoCantelli
import StatInference.EmpiricalProcess.VdVW241
import StatInference.Matching.WDSM.FiniteCellIndicatorLLNFromMass
import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScorePositiveVarianceStudentizedBridge

/-!
# Glivenko-Cantelli adapter for finite score-cell indicator LLNs

This module connects the local empirical-process interface to the WDSM finite
score-cell layer.  A GC certificate for the finite score-cell indicator class
now gives the weighted `0/1` indicator-sum LLN shape consumed by the WDSM
deterministic approximation theorems.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory ProbabilityTheory
open scoped Topology Function

variable {Unit Cell : Type*} [DecidableEq Cell]

/--
A Glivenko-Cantelli certificate for weighted score-cell indicator sums gives
cellwise convergence of every fixed weighted `0/1` score-cell sum.
-/
theorem tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (referenceShare : Cell -> Real)
    (gc :
      GlivenkoCantelliClass {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))
        atTop (nhds (referenceShare cell)) := by
  intro cell hcell
  have habs :
      Tendsto
        (fun sampleSize =>
          |weightedSampleSum (sample sampleSize) (weight sampleSize)
              (scoreCellIndicator (score sampleSize) cell) -
            referenceShare cell|)
        atTop (nhds 0) := by
    exact
      tendsto_of_tendsto_of_tendsto_of_le_of_le tendsto_const_nhds
        gc.radius_tendsto_zero
        (fun sampleSize => abs_nonneg
          (weightedSampleSum (sample sampleSize) (weight sampleSize)
              (scoreCellIndicator (score sampleSize) cell) -
            referenceShare cell))
        (fun sampleSize => gc.deviation sampleSize hcell)
  have hdiff :
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
              (scoreCellIndicator (score sampleSize) cell) -
            referenceShare cell)
        atTop (nhds 0) :=
    (tendsto_zero_iff_abs_tendsto_zero _).2 habs
  have hsum :=
    hdiff.add
      (tendsto_const_nhds :
        Tendsto (fun _sampleSize : ℕ => referenceShare cell) atTop
          (nhds (referenceShare cell)))
  simpa using hsum

/--
The same GC certificate gives cellwise convergence of score-cell masses, using
the verified indicator representation of `scoreCellMass`.
-/
theorem tendsto_scoreCellMass_of_indicator_glivenkoCantelli
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (referenceShare : Cell -> Real)
    (gc :
      GlivenkoCantelliClass {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          scoreCellMass (sample sampleSize) (weight sampleSize)
            (score sampleSize) cell)
        atTop (nhds (referenceShare cell)) := by
  intro cell hcell
  exact tendsto_scoreCellMass_of_tendsto_weightedSampleSum_indicator
    sample weight score cell (referenceShare cell)
    (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
      cells sample weight score referenceShare gc cell hcell)

/--
Finite `L1(P)` bracketing constructor obligations give cellwise convergence of
fixed weighted score-cell indicator sums.
-/
theorem tendsto_weightedSampleSum_scoreCellIndicator_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (referenceShare : Cell -> Real)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))
        atTop (nhds (referenceShare cell)) :=
  tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
    cells sample weight score referenceShare
    obligations.toGlivenkoCantelliClass

/--
VdV&W endpoint assemblies give cellwise convergence of fixed weighted
score-cell indicator sums.
-/
theorem tendsto_weightedSampleSum_scoreCellIndicator_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (referenceShare : Cell -> Real)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))
        atTop (nhds (referenceShare cell)) :=
  tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
    cells sample weight score referenceShare
    assembly.toGlivenkoCantelliClass

/--
Finite `L1(P)` bracketing constructor obligations give cellwise convergence of
score-cell masses.
-/
theorem tendsto_scoreCellMass_of_indicator_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (referenceShare : Cell -> Real)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          scoreCellMass (sample sampleSize) (weight sampleSize)
            (score sampleSize) cell)
        atTop (nhds (referenceShare cell)) :=
  tendsto_scoreCellMass_of_indicator_glivenkoCantelli
    cells sample weight score referenceShare
    obligations.toGlivenkoCantelliClass

/--
VdV&W endpoint assemblies give cellwise convergence of score-cell masses.
-/
theorem tendsto_scoreCellMass_of_indicator_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (referenceShare : Cell -> Real)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          scoreCellMass (sample sampleSize) (weight sampleSize)
            (score sampleSize) cell)
        atTop (nhds (referenceShare cell)) :=
  tendsto_scoreCellMass_of_indicator_glivenkoCantelli
    cells sample weight score referenceShare
    assembly.toGlivenkoCantelliClass

/--
Package a finite score-cell indicator GC certificate as the WDSM finite
score-cell LLN bridge.  The stochastic content is the GC certificate; the
bounded-indicator side condition is the already proved `0/1` bound.
-/
def finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell) :
    FiniteScoreCellIndicatorLLNBridge Cell where
  cells := cells
  referenceShare := referenceShare
  survey_design_regularity :=
    Nonempty
      (GlivenkoCantelliClass {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
  bounded_score_cell_indicators :=
    ∀ sampleSize cell unit, |scoreCellIndicator (score sampleSize) cell unit| ≤ 1
  weighted_indicator_array_lln :=
    Nonempty
      (GlivenkoCantelliClass {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
  cellwise_weighted_indicator_sum_lln :=
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))
        atTop (nhds (referenceShare cell))
  bridge := by
    intro _hdesign _hbounded hgc
    rcases hgc with ⟨gc⟩
    exact tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
      cells sample weight score referenceShare gc

/--
Finite `L1(P)` bracketing constructor obligations supply the GC certificate
needed by the WDSM finite score-cell indicator LLN bridge.
-/
theorem weighted_indicator_array_lln_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score).weighted_indicator_array_lln :=
  ⟨obligations.toGlivenkoCantelliClass⟩

/--
The VdV&W 2.4.1 endpoint-assembly layer supplies the GC certificate needed by
the WDSM finite score-cell indicator LLN bridge.
-/
theorem weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score).weighted_indicator_array_lln :=
  ⟨assembly.toGlivenkoCantelliClass⟩

theorem bounded_score_cell_indicators_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell) :
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score).bounded_score_cell_indicators := by
  intro sampleSize cell unit
  exact abs_scoreCellIndicator_le_one (score sampleSize) cell unit

theorem cellwise_weighted_indicator_sum_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln) :
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln :=
  finite_score_cell_indicator_lln_of_bridge
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score)
    hgc
    (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score)
    hgc

/--
A GC-backed finite score-cell bridge yields both the weighted indicator-sum
LLN and the equivalent score-cell mass LLN.
-/
theorem cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln) :
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare := by
  have hindicator :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln :=
    cellwise_weighted_indicator_sum_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc
  exact
    ⟨hindicator,
      cellwiseScoreCellMassLLN_of_indicator cells sample weight score
        referenceShare hindicator⟩

/--
A GC-backed finite score-cell bridge yields the score-cell mass LLN directly.
This projection is useful once a downstream route has already consumed the
indicator-sum LLN but still needs to expose the verified score-cell mass
convergence.
-/
theorem cellwise_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln) :
    cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
      referenceShare :=
  (cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score hgc).2

/--
VdV&W outer-a.s. GC for a stochastic observation process gives pathwise WDSM
weighted indicator-sum and score-cell mass LLNs once the observation-level
class functions are identified with the WDSM weighted score-cell indicators.
-/
theorem cellwise_weighted_indicator_sum_and_mass_lln_ae_of_vdvw_outerAlmostSure
    {Ω Observation : Type*} [MeasurableSpace Ω] [MeasurableSpace Observation]
    {μ : Measure Ω} {P : Measure Observation}
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (classFun : Cell -> Observation -> ℝ)
    (X : ℕ -> Ω -> Observation)
    (sample : Ω -> ℕ -> Finset Unit)
    (weight : Ω -> ℕ -> Unit -> Real)
    (score : Ω -> ℕ -> Unit -> Cell)
    (hgc :
      VdVWOuterAlmostSurePGlivenkoCantelliClass μ P
        {cell : Cell | cell ∈ cells} classFun X)
    (hpopulation :
      ∀ cell, cell ∈ cells ->
        populationRiskOfFunction P (classFun cell) = referenceShare cell)
    (hempirical :
      ∀ ω sampleSize cell, cell ∈ cells ->
        empiricalAverage (samplePath X ω sampleSize) (classFun cell) =
          weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
            (scoreCellIndicator (score ω sampleSize) cell)) :
    ∀ᵐ ω ∂μ,
      ((∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
              (scoreCellIndicator (score ω sampleSize) cell))
          atTop (nhds (referenceShare cell))) ∧
        cellwiseScoreCellMassLLN (l := atTop) cells (sample ω)
          (weight ω) (score ω) referenceShare) := by
  have hpoint :
      ∀ cell, cell ∈ cells ->
        ∀ᵐ ω ∂μ,
          Tendsto
            (fun sampleSize =>
              empiricalAverage (samplePath X ω sampleSize) (classFun cell))
            atTop (nhds (populationRiskOfFunction P (classFun cell))) := by
    intro cell hcell
    exact
      VdVWOuterAlmostSurePGlivenkoCantelliClass.tendsto_at_ae
        hgc hcell
  have hweighted :
      ∀ cell, cell ∈ cells ->
        ∀ᵐ ω ∂μ,
          Tendsto
            (fun sampleSize =>
              weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
                (scoreCellIndicator (score ω sampleSize) cell))
            atTop (nhds (referenceShare cell)) := by
    intro cell hcell
    filter_upwards [hpoint cell hcell] with ω hω
    have hω_ref :
        Tendsto
          (fun sampleSize =>
            empiricalAverage (samplePath X ω sampleSize) (classFun cell))
          atTop (nhds (referenceShare cell)) := by
      simpa [hpopulation cell hcell] using hω
    have heq :
        (fun sampleSize =>
          weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
            (scoreCellIndicator (score ω sampleSize) cell)) =ᶠ[atTop]
        (fun sampleSize =>
          empiricalAverage (samplePath X ω sampleSize) (classFun cell)) := by
      exact Eventually.of_forall fun sampleSize =>
        (hempirical ω sampleSize cell hcell).symm
    exact hω_ref.congr' heq.symm
  have hall :
      ∀ᵐ ω ∂μ,
        ∀ cell : {cell : Cell // cell ∈ cells},
          Tendsto
            (fun sampleSize =>
              weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
                (scoreCellIndicator (score ω sampleSize) cell.1))
            atTop (nhds (referenceShare cell.1)) := by
    exact eventually_all.2 (fun cell => hweighted cell.1 cell.2)
  filter_upwards [hall] with ω hω
  have hindicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
              (scoreCellIndicator (score ω sampleSize) cell))
          atTop (nhds (referenceShare cell)) := by
    intro cell hcell
    exact hω ⟨cell, hcell⟩
  exact
    ⟨hindicator,
      cellwiseScoreCellMassLLN_of_indicator cells (sample ω) (weight ω)
        (score ω) referenceShare hindicator⟩

/--
Iid observations plus primitive finite `L1(P)` bracketing numbers at every
positive radius give pathwise WDSM weighted indicator-sum and score-cell mass
LLNs.  This removes the need to provide an abstract VdV&W outer-a.s. GC
certificate separately for this finite score-cell route.
-/
theorem cellwise_weighted_indicator_sum_and_mass_lln_ae_of_iid_l1BracketingNumber
    {Ω Observation : Type*} [MeasurableSpace Ω] [MeasurableSpace Observation]
    {μ : Measure Ω} {P : Measure Observation}
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (classFun : Cell -> Observation -> ℝ)
    (X : ℕ -> Ω -> Observation)
    (sample : Ω -> ℕ -> Finset Unit)
    (weight : Ω -> ℕ -> Unit -> Real)
    (score : Ω -> ℕ -> Unit -> Cell)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (h_bracketing :
      ∀ epsilon, 0 < epsilon ->
        l1BracketingNumber P {cell : Cell | cell ∈ cells}
          classFun epsilon < ⊤)
    (hpopulation :
      ∀ cell, cell ∈ cells ->
        populationRiskOfFunction P (classFun cell) = referenceShare cell)
    (hempirical :
      ∀ ω sampleSize cell, cell ∈ cells ->
        empiricalAverage (samplePath X ω sampleSize) (classFun cell) =
          weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
            (scoreCellIndicator (score ω sampleSize) cell)) :
    ∀ᵐ ω ∂μ,
      ((∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
              (scoreCellIndicator (score ω sampleSize) cell))
          atTop (nhds (referenceShare cell))) ∧
        cellwiseScoreCellMassLLN (l := atTop) cells (sample ω)
          (weight ω) (score ω) referenceShare) :=
  cellwise_weighted_indicator_sum_and_mass_lln_ae_of_vdvw_outerAlmostSure
    cells referenceShare classFun X sample weight score
    (vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
      X hLaw hindep h_bracketing)
    hpopulation hempirical

/--
Finite bracketing-number obligations give both the WDSM weighted indicator-sum
LLN and the equivalent score-cell mass LLN.
-/
theorem cellwise_weighted_indicator_sum_and_mass_lln_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)

/--
The VdV&W endpoint-assembly route gives both the WDSM weighted indicator-sum
LLN and the equivalent score-cell mass LLN.
-/
theorem cellwise_weighted_indicator_sum_and_mass_lln_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)

/--
Paired GC-backed finite score-cell bridges yield both weighted indicator-sum
LLNs and score-cell mass LLNs for two score partitions.
-/
theorem paired_cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (hleft_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        leftCells leftReferenceShare leftSample leftWeight
        leftScore).weighted_indicator_array_lln)
    (hright_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        rightCells rightReferenceShare rightSample rightWeight
        rightScore).weighted_indicator_array_lln) :
    ((finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        leftCells leftReferenceShare leftSample leftWeight
        leftScore).cellwise_weighted_indicator_sum_lln ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare) ∧
    ((finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        rightCells rightReferenceShare rightSample rightWeight
        rightScore).cellwise_weighted_indicator_sum_lln ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare) :=
  ⟨cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      leftCells leftReferenceShare leftSample leftWeight leftScore hleft_gc,
    cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      rightCells rightReferenceShare rightSample rightWeight rightScore
      hright_gc⟩

/--
Paired GC-backed finite score-cell bridges yield the mass-LLN conclusions
directly.  This projection is the form needed when downstream studentization
already consumed the indicator-sum LLNs but still needs to expose the verified
score-cell mass convergence.
-/
theorem paired_cellwise_mass_lln_of_glivenkoCantelli_bridge
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (hleft_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        leftCells leftReferenceShare leftSample leftWeight
        leftScore).weighted_indicator_array_lln)
    (hright_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        rightCells rightReferenceShare rightSample rightWeight
        rightScore).weighted_indicator_array_lln) :
    cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare := by
  have hmass :=
    paired_cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      leftCells rightCells leftReferenceShare rightReferenceShare leftSample
      rightSample leftWeight rightWeight leftScore rightScore hleft_gc hright_gc
  exact ⟨hmass.1.2, hmass.2.2⟩

/--
Attach a GC-backed score-cell mass LLN to any already derived single-arm
output.  This keeps coverage, bootstrap, and studentization routers from
needing bespoke `_and_mass_lln` variants for every conclusion shape.
-/
theorem output_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {output : Prop}
    (houtput : output) :
    output ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨houtput,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach a score-cell mass LLN to an already derived output when the finite-cell
GC certificate is supplied by finite `L1(P)` bracketing obligations.
-/
theorem output_and_mass_lln_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {output : Prop}
    (houtput : output) :
    output ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  output_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    houtput

/--
Attach a score-cell mass LLN to an already derived output when the finite-cell
GC certificate is supplied by the VdV&W endpoint-assembly route.
-/
theorem output_and_mass_lln_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {output : Prop}
    (houtput : output) :
    output ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  output_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    houtput

/--
Attach paired GC-backed score-cell mass LLNs to any already derived paired
output tuple.
-/
theorem paired_output_and_mass_lln_of_glivenkoCantelli_bridge
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (hleft_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        leftCells leftReferenceShare leftSample leftWeight
        leftScore).weighted_indicator_array_lln)
    (hright_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        rightCells rightReferenceShare rightSample rightWeight
        rightScore).weighted_indicator_array_lln)
    {output : Prop}
    (houtput : output) :
    output ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare := by
  have hmass :=
    paired_cellwise_mass_lln_of_glivenkoCantelli_bridge
      leftCells rightCells leftReferenceShare rightReferenceShare leftSample
      rightSample leftWeight rightWeight leftScore rightScore hleft_gc hright_gc
  exact ⟨houtput, hmass.1, hmass.2⟩

/--
Attach paired score-cell mass LLNs to an already derived output when both
finite-cell GC certificates are supplied by finite `L1(P)` bracketing
obligations.
-/
theorem paired_output_and_mass_lln_of_l1BracketingNumber_obligations
    {LeftCell RightCell LeftBracket RightBracket : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    [Fintype LeftBracket] [Fintype RightBracket]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (leftObligations :
      L1BracketingNumberConstructorObligations (Bracket := LeftBracket)
        {cell : LeftCell | cell ∈ leftCells} leftReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (leftSample sampleSize) (leftWeight sampleSize)
            (scoreCellIndicator (leftScore sampleSize) cell)))
    (rightObligations :
      L1BracketingNumberConstructorObligations (Bracket := RightBracket)
        {cell : RightCell | cell ∈ rightCells} rightReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (rightSample sampleSize) (rightWeight sampleSize)
            (scoreCellIndicator (rightScore sampleSize) cell)))
    {output : Prop}
    (houtput : output) :
    output ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare :=
  paired_output_and_mass_lln_of_glivenkoCantelli_bridge
    leftCells rightCells leftReferenceShare rightReferenceShare leftSample
    rightSample leftWeight rightWeight leftScore rightScore
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      leftCells leftReferenceShare leftSample leftWeight leftScore
      leftObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      rightCells rightReferenceShare rightSample rightWeight rightScore
      rightObligations)
    houtput

/--
Attach paired score-cell mass LLNs to an already derived output when both
finite-cell GC certificates are supplied by VdV&W endpoint assemblies.
-/
theorem paired_output_and_mass_lln_of_vdvw241_endpoint_assembly
    {LeftCell RightCell LeftBracket RightBracket : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    [Fintype LeftBracket] [Fintype RightBracket]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (leftAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := LeftBracket)
        {cell : LeftCell | cell ∈ leftCells} leftReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (leftSample sampleSize) (leftWeight sampleSize)
            (scoreCellIndicator (leftScore sampleSize) cell)))
    (rightAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := RightBracket)
        {cell : RightCell | cell ∈ rightCells} rightReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (rightSample sampleSize) (rightWeight sampleSize)
            (scoreCellIndicator (rightScore sampleSize) cell)))
    {output : Prop}
    (houtput : output) :
    output ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare :=
  paired_output_and_mass_lln_of_glivenkoCantelli_bridge
    leftCells rightCells leftReferenceShare rightReferenceShare leftSample
    rightSample leftWeight rightWeight leftScore rightScore
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      leftCells leftReferenceShare leftSample leftWeight leftScore
      leftAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      rightCells rightReferenceShare rightSample rightWeight rightScore
      rightAssembly)
    houtput

/--
Attach paired GC-backed score-cell mass LLNs to an already derived paired
studentized output tuple.  The ten abstract propositions cover both the
ordinary estimated-score studentized theorem and its positive-variance variant.
-/
theorem paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (hleft_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        leftCells leftReferenceShare leftSample leftWeight
        leftScore).weighted_indicator_array_lln)
    (hright_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        rightCells rightReferenceShare rightSample rightWeight
        rightScore).weighted_indicator_array_lln)
    {leftApprox leftScaled leftKnownNormal leftEstimatedNormal
      leftStudentized rightApprox rightScaled rightKnownNormal
      rightEstimatedNormal rightStudentized : Prop}
    (hstudentized :
      leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
        leftStudentized ∧ rightApprox ∧ rightScaled ∧ rightKnownNormal ∧
        rightEstimatedNormal ∧ rightStudentized) :
    leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
      leftStudentized ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      rightApprox ∧ rightScaled ∧ rightKnownNormal ∧ rightEstimatedNormal ∧
      rightStudentized ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare := by
  have hmass :=
    paired_cellwise_mass_lln_of_glivenkoCantelli_bridge
      leftCells rightCells leftReferenceShare rightReferenceShare leftSample
      rightSample leftWeight rightWeight leftScore rightScore hleft_gc hright_gc
  exact
    ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2.1,
      hstudentized.2.2.2.1, hstudentized.2.2.2.2.1, hmass.1,
      hstudentized.2.2.2.2.2.1, hstudentized.2.2.2.2.2.2.1,
      hstudentized.2.2.2.2.2.2.2.1,
      hstudentized.2.2.2.2.2.2.2.2.1,
      hstudentized.2.2.2.2.2.2.2.2.2, hmass.2⟩

/--
L1-bracketing backed version of
`paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge`.
-/
theorem paired_studentized_outputs_and_mass_lln_of_l1BracketingNumber_obligations
    {LeftCell RightCell LeftBracket RightBracket : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    [Fintype LeftBracket] [Fintype RightBracket]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (leftObligations :
      L1BracketingNumberConstructorObligations (Bracket := LeftBracket)
        {cell : LeftCell | cell ∈ leftCells} leftReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (leftSample sampleSize) (leftWeight sampleSize)
            (scoreCellIndicator (leftScore sampleSize) cell)))
    (rightObligations :
      L1BracketingNumberConstructorObligations (Bracket := RightBracket)
        {cell : RightCell | cell ∈ rightCells} rightReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (rightSample sampleSize) (rightWeight sampleSize)
            (scoreCellIndicator (rightScore sampleSize) cell)))
    {leftApprox leftScaled leftKnownNormal leftEstimatedNormal
      leftStudentized rightApprox rightScaled rightKnownNormal
      rightEstimatedNormal rightStudentized : Prop}
    (hstudentized :
      leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
        leftStudentized ∧ rightApprox ∧ rightScaled ∧ rightKnownNormal ∧
        rightEstimatedNormal ∧ rightStudentized) :
    leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
      leftStudentized ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      rightApprox ∧ rightScaled ∧ rightKnownNormal ∧ rightEstimatedNormal ∧
      rightStudentized ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare :=
  paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge
    leftCells rightCells leftReferenceShare rightReferenceShare leftSample
    rightSample leftWeight rightWeight leftScore rightScore
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      leftCells leftReferenceShare leftSample leftWeight leftScore
      leftObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      rightCells rightReferenceShare rightSample rightWeight rightScore
      rightObligations)
    hstudentized

/--
VdV&W endpoint-assembly backed version of
`paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge`.
-/
theorem paired_studentized_outputs_and_mass_lln_of_vdvw241_endpoint_assembly
    {LeftCell RightCell LeftBracket RightBracket : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    [Fintype LeftBracket] [Fintype RightBracket]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (leftAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := LeftBracket)
        {cell : LeftCell | cell ∈ leftCells} leftReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (leftSample sampleSize) (leftWeight sampleSize)
            (scoreCellIndicator (leftScore sampleSize) cell)))
    (rightAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := RightBracket)
        {cell : RightCell | cell ∈ rightCells} rightReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (rightSample sampleSize) (rightWeight sampleSize)
            (scoreCellIndicator (rightScore sampleSize) cell)))
    {leftApprox leftScaled leftKnownNormal leftEstimatedNormal
      leftStudentized rightApprox rightScaled rightKnownNormal
      rightEstimatedNormal rightStudentized : Prop}
    (hstudentized :
      leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
        leftStudentized ∧ rightApprox ∧ rightScaled ∧ rightKnownNormal ∧
        rightEstimatedNormal ∧ rightStudentized) :
    leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
      leftStudentized ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      rightApprox ∧ rightScaled ∧ rightKnownNormal ∧ rightEstimatedNormal ∧
      rightStudentized ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare :=
  paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge
    leftCells rightCells leftReferenceShare rightReferenceShare leftSample
    rightSample leftWeight rightWeight leftScore rightScore
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      leftCells leftReferenceShare leftSample leftWeight leftScore
      leftAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      rightCells rightReferenceShare rightSample rightWeight rightScore
      rightAssembly)
    hstudentized

/--
Attach paired GC-backed score-cell mass LLNs to an already derived paired
estimated-score asymptotic-normality output tuple.  This is the estimated-score
analogue of `paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge`.
-/
theorem paired_estimated_score_outputs_and_mass_lln_of_glivenkoCantelli_bridge
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (hleft_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        leftCells leftReferenceShare leftSample leftWeight
        leftScore).weighted_indicator_array_lln)
    (hright_gc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        rightCells rightReferenceShare rightSample rightWeight
        rightScore).weighted_indicator_array_lln)
    {leftApprox leftScaled leftKnownNormal leftEstimatedNormal
      rightApprox rightScaled rightKnownNormal rightEstimatedNormal : Prop}
    (hestimated :
      leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
        rightApprox ∧ rightScaled ∧ rightKnownNormal ∧
        rightEstimatedNormal) :
    leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      rightApprox ∧ rightScaled ∧ rightKnownNormal ∧ rightEstimatedNormal ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare := by
  have hmass :=
    paired_cellwise_mass_lln_of_glivenkoCantelli_bridge
      leftCells rightCells leftReferenceShare rightReferenceShare leftSample
      rightSample leftWeight rightWeight leftScore rightScore hleft_gc hright_gc
  exact
    ⟨hestimated.1, hestimated.2.1, hestimated.2.2.1,
      hestimated.2.2.2.1, hmass.1, hestimated.2.2.2.2.1,
      hestimated.2.2.2.2.2.1, hestimated.2.2.2.2.2.2.1,
      hestimated.2.2.2.2.2.2.2, hmass.2⟩

/--
L1-bracketing backed version of
`paired_estimated_score_outputs_and_mass_lln_of_glivenkoCantelli_bridge`.
-/
theorem paired_estimated_score_outputs_and_mass_lln_of_l1BracketingNumber_obligations
    {LeftCell RightCell LeftBracket RightBracket : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    [Fintype LeftBracket] [Fintype RightBracket]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (leftObligations :
      L1BracketingNumberConstructorObligations (Bracket := LeftBracket)
        {cell : LeftCell | cell ∈ leftCells} leftReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (leftSample sampleSize) (leftWeight sampleSize)
            (scoreCellIndicator (leftScore sampleSize) cell)))
    (rightObligations :
      L1BracketingNumberConstructorObligations (Bracket := RightBracket)
        {cell : RightCell | cell ∈ rightCells} rightReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (rightSample sampleSize) (rightWeight sampleSize)
            (scoreCellIndicator (rightScore sampleSize) cell)))
    {leftApprox leftScaled leftKnownNormal leftEstimatedNormal
      rightApprox rightScaled rightKnownNormal rightEstimatedNormal : Prop}
    (hestimated :
      leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
        rightApprox ∧ rightScaled ∧ rightKnownNormal ∧
        rightEstimatedNormal) :
    leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      rightApprox ∧ rightScaled ∧ rightKnownNormal ∧ rightEstimatedNormal ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare :=
  paired_estimated_score_outputs_and_mass_lln_of_glivenkoCantelli_bridge
    leftCells rightCells leftReferenceShare rightReferenceShare leftSample
    rightSample leftWeight rightWeight leftScore rightScore
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      leftCells leftReferenceShare leftSample leftWeight leftScore
      leftObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      rightCells rightReferenceShare rightSample rightWeight rightScore
      rightObligations)
    hestimated

/--
VdV&W endpoint-assembly backed version of
`paired_estimated_score_outputs_and_mass_lln_of_glivenkoCantelli_bridge`.
-/
theorem paired_estimated_score_outputs_and_mass_lln_of_vdvw241_endpoint_assembly
    {LeftCell RightCell LeftBracket RightBracket : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    [Fintype LeftBracket] [Fintype RightBracket]
    (leftCells : Finset LeftCell)
    (rightCells : Finset RightCell)
    (leftReferenceShare : LeftCell -> Real)
    (rightReferenceShare : RightCell -> Real)
    (leftSample rightSample : ℕ -> Finset Unit)
    (leftWeight rightWeight : ℕ -> Unit -> Real)
    (leftScore : ℕ -> Unit -> LeftCell)
    (rightScore : ℕ -> Unit -> RightCell)
    (leftAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := LeftBracket)
        {cell : LeftCell | cell ∈ leftCells} leftReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (leftSample sampleSize) (leftWeight sampleSize)
            (scoreCellIndicator (leftScore sampleSize) cell)))
    (rightAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := RightBracket)
        {cell : RightCell | cell ∈ rightCells} rightReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (rightSample sampleSize) (rightWeight sampleSize)
            (scoreCellIndicator (rightScore sampleSize) cell)))
    {leftApprox leftScaled leftKnownNormal leftEstimatedNormal
      rightApprox rightScaled rightKnownNormal rightEstimatedNormal : Prop}
    (hestimated :
      leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
        rightApprox ∧ rightScaled ∧ rightKnownNormal ∧
        rightEstimatedNormal) :
    leftApprox ∧ leftScaled ∧ leftKnownNormal ∧ leftEstimatedNormal ∧
      cellwiseScoreCellMassLLN (l := atTop) leftCells leftSample
        leftWeight leftScore leftReferenceShare ∧
      rightApprox ∧ rightScaled ∧ rightKnownNormal ∧ rightEstimatedNormal ∧
      cellwiseScoreCellMassLLN (l := atTop) rightCells rightSample
        rightWeight rightScore rightReferenceShare :=
  paired_estimated_score_outputs_and_mass_lln_of_glivenkoCantelli_bridge
    leftCells rightCells leftReferenceShare rightReferenceShare leftSample
    rightSample leftWeight rightWeight leftScore rightScore
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      leftCells leftReferenceShare leftSample leftWeight leftScore
      leftAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      rightCells rightReferenceShare rightSample rightWeight rightScore
      rightAssembly)
    hestimated

/--
Build a PATE finite score-cell LLN approximation bridge whose stochastic LLN
input is a GC certificate for weighted score-cell indicator sums.
-/
def pateFiniteScoreCellLLNApproximationBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln) :
    PATEFiniteScoreCellLLNApproximationBridge Cell where
  lln_bridge :=
    finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score
  indicator_bridge := indicator_bridge
  finite_lln_to_indicator_lln := finite_lln_to_indicator_lln

theorem pate_approximation_negligible_of_finite_score_cell_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.pate_double_score_approximation_negligible := by
  exact pate_approximation_negligible_of_finite_score_cell_lln
    (pateFiniteScoreCellLLNApproximationBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln)
    hgc
    (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score)
    hgc hfinite henvelope

/--
GC-backed PATE approximation negligibility together with the equivalent
score-cell mass LLN needed by finite-cell variance layers.
-/
theorem pate_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare := by
  have hmass :
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
    (cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc).2
  exact
    ⟨pate_approximation_negligible_of_finite_score_cell_glivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln hgc hfinite henvelope,
      hmass⟩

/--
PATE finite score-cell approximation and mass LLN from finite `L1(P)`
bracketing-number obligations.
-/
theorem
    pate_approximation_negligible_and_mass_lln_of_finite_score_cell_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hfinite henvelope

/--
PATE finite score-cell approximation and mass LLN from the VdV&W endpoint
assembly route.
-/
theorem
    pate_approximation_negligible_and_mass_lln_of_finite_score_cell_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hfinite henvelope

/--
Build a PATT finite score-cell LLN approximation bridge whose stochastic LLN
input is a GC certificate for weighted score-cell indicator sums.
-/
def pattFiniteScoreCellLLNApproximationBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln) :
    PATTFiniteScoreCellLLNApproximationBridge Cell where
  lln_bridge :=
    finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score
  indicator_bridge := indicator_bridge
  finite_lln_to_indicator_lln := finite_lln_to_indicator_lln

theorem patt_approximation_negligible_of_finite_score_cell_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.patt_double_score_approximation_negligible := by
  exact patt_approximation_negligible_of_finite_score_cell_lln
    (pattFiniteScoreCellLLNApproximationBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln)
    hgc
    (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score)
    hgc hfinite henvelope

/--
GC-backed PATT approximation negligibility together with the equivalent
score-cell mass LLN needed by finite-cell variance layers.
-/
theorem patt_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare := by
  have hmass :
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
    (cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc).2
  exact
    ⟨patt_approximation_negligible_of_finite_score_cell_glivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln hgc hfinite henvelope,
      hmass⟩

/--
PATT finite score-cell approximation and mass LLN from finite `L1(P)`
bracketing-number obligations.
-/
theorem
    patt_approximation_negligible_and_mass_lln_of_finite_score_cell_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hfinite henvelope

/--
PATT finite score-cell approximation and mass LLN from the VdV&W endpoint
assembly route.
-/
theorem
    patt_approximation_negligible_and_mass_lln_of_finite_score_cell_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hfinite henvelope

/--
Paired GC-backed PATE/PATT approximation negligibility together with the
equivalent score-cell mass LLNs for both finite score partitions.
-/
theorem pate_patt_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    {PATECell PATTCell : Type*}
    [DecidableEq PATECell] [DecidableEq PATTCell]
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence) :
    (pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare) ∧
    (pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare) :=
  ⟨pate_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN hpateGC hpateFinite
      hpateEnvelope,
    patt_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattIndicatorBridge pattFiniteLLNToIndicatorLLN hpattGC hpattFinite
      hpattEnvelope⟩

/--
Paired PATE/PATT finite score-cell approximation and mass LLNs from finite
`L1(P)` bracketing-number obligations on both score partitions.
-/
theorem
    pate_patt_approximation_negligible_and_mass_lln_of_finite_score_cell_l1BracketingNumber_obligations
    {PATECell PATTCell PATEBracket PATTBracket : Type*}
    [DecidableEq PATECell] [DecidableEq PATTCell]
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pateObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize) (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pattObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize) (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence) :
    (pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare) ∧
    (pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare) :=
  pate_patt_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore pateIndicatorBridge
    pattIndicatorBridge pateFiniteLLNToIndicatorLLN
    pattFiniteLLNToIndicatorLLN
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattObligations)
    hpateFinite hpattFinite hpateEnvelope hpattEnvelope

/--
Paired PATE/PATT finite score-cell approximation and mass LLNs from VdV&W
endpoint assemblies on both score partitions.
-/
theorem
    pate_patt_approximation_negligible_and_mass_lln_of_finite_score_cell_vdvw241_endpoint_assembly
    {PATECell PATTCell PATEBracket PATTBracket : Type*}
    [DecidableEq PATECell] [DecidableEq PATTCell]
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pateAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize) (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pattAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize) (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence) :
    (pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare) ∧
    (pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare) :=
  pate_patt_approximation_negligible_and_mass_lln_of_finite_score_cell_glivenkoCantelli
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore pateIndicatorBridge
    pattIndicatorBridge pateFiniteLLNToIndicatorLLN
    pattFiniteLLNToIndicatorLLN
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattAssembly)
    hpateFinite hpattFinite hpateEnvelope hpattEnvelope

/--
Build a PATE finite score-cell stochastic approximation bridge whose LLN side
is backed by a GC certificate and whose scaled side is supplied by the existing
finite vector-CLT bridge.
-/
def pateFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln) :
    PATEFiniteScoreCellStochasticApproximationBridge Cell where
  lln_bridge :=
    pateFiniteScoreCellLLNApproximationBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln
  clt_bridge := clt_bridge
  finite_conditions_to_scaled := finite_conditions_to_scaled
  envelope_to_scaled := envelope_to_scaled
  indicator_lln_to_scaled := indicator_lln_to_scaled

theorem
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible := by
  exact
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      (pateFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
        envelope_to_scaled indicator_lln_to_scaled)
      hgc
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        cells referenceShare sample weight score)
      hgc hfinite henvelope hsimplex hlinear hmatrix

/--
GC-backed PATE unscaled/scaled approximation negligibility from a packaged
finite score-cell vector CLT.
-/
theorem
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible := by
  exact
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_vector_clt
      (pateFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
        envelope_to_scaled indicator_lln_to_scaled)
      hgc
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        cells referenceShare sample weight score)
      hgc hfinite henvelope hvector

/--
GC-backed PATE unscaled/scaled approximation negligibility together with the
score-cell mass LLN needed by finite-cell variance layers.
-/
theorem
    pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare := by
  have happrox :=
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled hgc hfinite henvelope
      hsimplex hlinear hmatrix
  have hmass :
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
    (cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc).2
  exact ⟨happrox.1, happrox.2, hmass⟩

/--
GC-backed PATE unscaled/scaled approximation negligibility and mass LLN from a
packaged finite score-cell vector CLT.
-/
theorem
    pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare := by
  have happrox :=
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled hgc hfinite henvelope
      hvector
  have hmass :
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
    (cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc).2
  exact ⟨happrox.1, happrox.2, hmass⟩

/--
L1-bracketing-number obligations supply the GC side needed for the PATE
finite score-cell stochastic approximation bridge, including the mass LLN.
-/
theorem
    pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hfinite henvelope hsimplex hlinear hmatrix

/--
L1-bracketing-number obligations supply the GC side needed for the PATE
finite score-cell stochastic approximation bridge, while the scaled side uses
the packaged finite score-cell vector CLT directly.
-/
theorem
    pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_l1BracketingNumber_vector_clt
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hfinite henvelope hvector

/--
VdV-W endpoint assemblies supply the GC side needed for the PATE finite
score-cell stochastic approximation bridge, including the mass LLN.
-/
theorem
    pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hfinite henvelope hsimplex hlinear hmatrix

/--
VdV-W endpoint assemblies supply the GC side needed for the PATE finite
score-cell stochastic approximation bridge, while the scaled side uses the
packaged finite score-cell vector CLT directly.
-/
theorem
    pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_vdvw241_endpoint_vector_clt
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hfinite henvelope hvector

/--
Build a PATT finite score-cell stochastic approximation bridge whose LLN side
is backed by a GC certificate and whose scaled side is supplied by the existing
finite vector-CLT bridge.
-/
def pattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln) :
    PATTFiniteScoreCellStochasticApproximationBridge Cell where
  lln_bridge :=
    pattFiniteScoreCellLLNApproximationBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln
  clt_bridge := clt_bridge
  finite_conditions_to_scaled := finite_conditions_to_scaled
  envelope_to_scaled := envelope_to_scaled
  indicator_lln_to_scaled := indicator_lln_to_scaled

theorem
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  exact
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      (pattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
        envelope_to_scaled indicator_lln_to_scaled)
      hgc
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        cells referenceShare sample weight score)
      hgc hfinite henvelope hsimplex hlinear hmatrix

/--
GC-backed PATT unscaled/scaled approximation negligibility from a packaged
finite score-cell vector CLT.
-/
theorem
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  exact
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_vector_clt
      (pattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
        envelope_to_scaled indicator_lln_to_scaled)
      hgc
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        cells referenceShare sample weight score)
      hgc hfinite henvelope hvector

/--
GC-backed PATT unscaled/scaled approximation negligibility together with the
score-cell mass LLN needed by finite-cell variance layers.
-/
theorem
    patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare := by
  have happrox :=
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled hgc hfinite henvelope
      hsimplex hlinear hmatrix
  have hmass :
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
    (cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc).2
  exact ⟨happrox.1, happrox.2, hmass⟩

/--
GC-backed PATT unscaled/scaled approximation negligibility and mass LLN from a
packaged finite score-cell vector CLT.
-/
theorem
    patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare := by
  have happrox :=
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled hgc hfinite henvelope
      hvector
  have hmass :
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
    (cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc).2
  exact ⟨happrox.1, happrox.2, hmass⟩

/--
L1-bracketing-number obligations supply the GC side needed for the PATT
finite score-cell stochastic approximation bridge, including the mass LLN.
-/
theorem
    patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hfinite henvelope hsimplex hlinear hmatrix

/--
L1-bracketing-number obligations supply the GC side needed for the PATT
finite score-cell stochastic approximation bridge, while the scaled side uses
the packaged finite score-cell vector CLT directly.
-/
theorem
    patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_l1BracketingNumber_vector_clt
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hfinite henvelope hvector

/--
VdV-W endpoint assemblies supply the GC side needed for the PATT finite
score-cell stochastic approximation bridge, including the mass LLN.
-/
theorem
    patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hfinite henvelope hsimplex hlinear hmatrix

/--
VdV-W endpoint assemblies supply the GC side needed for the PATT finite
score-cell stochastic approximation bridge, while the scaled side uses the
packaged finite score-cell vector CLT directly.
-/
theorem
    patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_vdvw241_endpoint_vector_clt
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hvector :
      clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hfinite henvelope hvector

/--
Build a PATE known-score asymptotic bridge whose finite score-cell stochastic
layer is backed by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible) :
    PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell where
  stochastic_bridge :=
    pateFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled
  known_score_bridge := knownScoreBridge
  scaled_approximation_to_matching_discrepancy :=
    scaledApproximationToMatchingDiscrepancy

/--
Build a PATT known-score asymptotic bridge whose finite score-cell stochastic
layer is backed by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible) :
    PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell where
  stochastic_bridge :=
    pattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled
  known_score_bridge := knownScoreBridge
  scaled_approximation_to_matching_discrepancy :=
    scaledApproximationToMatchingDiscrepancy

/--
Build a PATE estimated-score asymptotic bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality) :
    PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell where
  known_score_finite_cell_bridge :=
    pateFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy
  estimated_score_bridge := estimatedScoreBridge
  known_score_to_estimated_score_input := knownScoreToEstimatedScoreInput

/--
Build a PATT estimated-score asymptotic bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality) :
    PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell where
  known_score_finite_cell_bridge :=
    pattFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy
  estimated_score_bridge := estimatedScoreBridge
  known_score_to_estimated_score_input := knownScoreToEstimatedScoreInput

/--
Build a PATE estimated-score studentized bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge :=
    pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput
  studentization_input := studentizationInput
  estimated_score_to_scaled_tendsto := estimatedScoreToScaledTendsto

/--
Build a PATT estimated-score studentized bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge :=
    pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput
  studentization_input := studentizationInput
  estimated_score_to_scaled_tendsto := estimatedScoreToScaledTendsto

/--
Build a PATE positive-variance estimated-score studentized bridge whose finite
score-cell layer is backed by a GC certificate on the LLN side.
-/
def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      Cell Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge :=
    pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput
  studentization_input := studentizationInput
  estimated_score_to_scaled_tendsto := estimatedScoreToScaledTendsto

/--
PATE positive-variance estimated-score studentization conclusion from a GC
finite score-cell LLN certificate.
-/
theorem
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization)
    (hlocal : estimatedScoreBridge.matching_functional_local_expansion)
    (hgodambe : estimatedScoreBridge.godambe_variance_identity) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      estimatedScoreBridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  exact
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance
      (pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
        envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput sampleLaw limitLaw l
        studentizationInput estimatedScoreToScaledTendsto)
      hgc
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        cells referenceShare sample weight score)
      hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
      hheterogeneity hresidual hfirst hlocal hgodambe

/--
PATE positive-variance estimated-score studentization from a GC finite
score-cell LLN certificate with the estimated-score local expansion and
Godambe obligations packaged as one compact core.
-/
theorem
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli_estimated_score_core
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (core : EstimatedScoreAsymptoticBridgeCore estimatedScoreBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization) :
    indicator_bridge.pate_double_score_approximation_negligible ∧
      estimatedScoreBridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw :=
  pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
    knownScoreToEstimatedScoreInput sampleLaw limitLaw l studentizationInput
    estimatedScoreToScaledTendsto hgc hfinite henvelope hsimplex hlinear
    hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
Build a PATT positive-variance estimated-score studentized bridge whose finite
score-cell layer is backed by a GC certificate on the LLN side.
-/
def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      Cell Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge :=
    pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicator_bridge
      finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
      envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput
  studentization_input := studentizationInput
  estimated_score_to_scaled_tendsto := estimatedScoreToScaledTendsto

/--
PATT positive-variance estimated-score studentization conclusion from a GC
finite score-cell LLN certificate.
-/
theorem
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization)
    (hlocal : estimatedScoreBridge.matching_functional_local_expansion)
    (hgodambe : estimatedScoreBridge.godambe_variance_identity) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      estimatedScoreBridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  exact
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance
      (pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicator_bridge
        finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
        envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput sampleLaw limitLaw l
        studentizationInput estimatedScoreToScaledTendsto)
      hgc
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        cells referenceShare sample weight score)
      hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
      hheterogeneity hresidual hfirst hlocal hgodambe

/--
PATT positive-variance estimated-score studentization from a GC finite
score-cell LLN certificate with the estimated-score local expansion and
Godambe obligations packaged as one compact core.
-/
theorem
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli_estimated_score_core
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finite_lln_to_indicator_lln :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicator_bridge.weighted_indicator_sum_lln)
    (clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finite_conditions_to_scaled :
      indicator_bridge.eventual_finite_conditions ->
        clt_bridge.indicator_bridge.eventual_finite_conditions)
    (envelope_to_scaled :
      indicator_bridge.envelope_convergence ->
        clt_bridge.indicator_bridge.envelope_convergence)
    (indicator_lln_to_scaled :
      indicator_bridge.weighted_indicator_sum_lln ->
        clt_bridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (core : EstimatedScoreAsymptoticBridgeCore estimatedScoreBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicator_bridge.eventual_finite_conditions)
    (henvelope : indicator_bridge.envelope_convergence)
    (hsimplex : clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization) :
    indicator_bridge.patt_double_score_approximation_negligible ∧
      estimatedScoreBridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw :=
  patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli
    cells referenceShare sample weight score indicator_bridge
    finite_lln_to_indicator_lln clt_bridge finite_conditions_to_scaled
    envelope_to_scaled indicator_lln_to_scaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
    knownScoreToEstimatedScoreInput sampleLaw limitLaw l studentizationInput
    estimatedScoreToScaledTendsto hgc hfinite henvelope hsimplex hlinear
    hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

variable {PATECell PATTCell : Type*}
  [DecidableEq PATECell] [DecidableEq PATTCell]

/--
Build a paired PATE/PATT finite score-cell stochastic approximation bridge whose
two LLN sides are backed by GC certificates and whose scaled sides are supplied
by the existing finite vector-CLT bridges.
-/
def patePattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln) :
    PATEPATTFiniteScoreCellStochasticApproximationBridge PATECell PATTCell where
  pate_bridge :=
    pateFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled
  patt_bridge :=
    pattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattIndicatorBridge pattFiniteLLNToIndicatorLLN pattCLTBridge
      pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled

theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  exact
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      (patePattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix

/--
Paired GC-backed PATE/PATT unscaled/scaled approximation negligibility from
packaged finite score-cell vector CLTs for both score partitions.
-/
theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateVector :
      pateCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattVector :
      pattCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  exact
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_vector_clt
      (patePattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateVector
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattVector

/--
Paired GC-backed PATE/PATT unscaled/scaled approximation negligibility together
with score-cell mass LLNs for both finite score partitions.
-/
theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have happrox :=
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled hpateGC hpateFinite hpateEnvelope
      hpateSimplex hpateLinear hpateMatrix hpattGC hpattFinite
      hpattEnvelope hpattSimplex hpattLinear hpattMatrix
  have hmass :=
    paired_cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare
      pateSample pattSample pateWeight pattWeight pateScore pattScore
      hpateGC hpattGC
  exact
    ⟨happrox.1, happrox.2.1, hmass.1.2, happrox.2.2.1,
      happrox.2.2.2, hmass.2.2⟩

/--
Paired GC-backed PATE/PATT unscaled/scaled approximation negligibility and
mass LLNs from packaged finite score-cell vector CLTs.
-/
theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateVector :
      pateCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattVector :
      pattCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have happrox :=
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled hpateGC hpateFinite hpateEnvelope hpateVector
      hpattGC hpattFinite hpattEnvelope hpattVector
  have hmass :=
    paired_cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare
      pateSample pattSample pateWeight pattWeight pateScore pattScore
      hpateGC hpattGC
  exact
    ⟨happrox.1, happrox.2.1, hmass.1.2, happrox.2.2.1,
      happrox.2.2.2, hmass.2.2⟩

/--
Paired PATE/PATT unscaled/scaled approximation negligibility and mass LLNs from
finite `L1(P)` bracketing obligations on both LLN sides and packaged finite
score-cell vector CLTs on both scaled sides.
-/
theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_l1BracketingNumber_vector_clt
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize)
            (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (pateEnvelope : pateIndicatorBridge.envelope_convergence)
    (pateVector :
      pateCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize)
            (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    (pattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (pattEnvelope : pattIndicatorBridge.envelope_convergence)
    (pattVector :
      pattCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    pateCells pateReferenceShare pateSample pateWeight pateScore
    pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
    pateFiniteConditionsToScaled pateEnvelopeToScaled
    pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
    pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
    pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
    pattIndicatorLLNToScaled
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateObligations)
    pateFinite pateEnvelope pateVector
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattObligations)
    pattFinite pattEnvelope pattVector

/--
Paired PATE/PATT unscaled/scaled approximation negligibility and mass LLNs from
VdV-W endpoint assemblies on both LLN sides and packaged finite score-cell
vector CLTs on both scaled sides.
-/
theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_vdvw241_endpoint_vector_clt
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize)
            (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (pateEnvelope : pateIndicatorBridge.envelope_convergence)
    (pateVector :
      pateCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize)
            (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    (pattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (pattEnvelope : pattIndicatorBridge.envelope_convergence)
    (pattVector :
      pattCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_vector_clt
    pateCells pateReferenceShare pateSample pateWeight pateScore
    pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
    pateFiniteConditionsToScaled pateEnvelopeToScaled
    pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
    pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
    pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
    pattIndicatorLLNToScaled
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateAssembly)
    pateFinite pateEnvelope pateVector
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattAssembly)
    pattFinite pattEnvelope pattVector

/--
Build a paired known-score asymptotic bridge whose finite score-cell stochastic
layer is backed by GC certificates on the LLN side.
-/
def patePattFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible) :
    PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell where
  stochastic_bridge :=
    patePattFiniteScoreCellStochasticApproximationBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled
  pate_known_score_bridge := pateKnownScoreBridge
  patt_known_score_bridge := pattKnownScoreBridge
  pate_scaled_approximation_to_matching_discrepancy :=
    pateScaledApproximationToMatchingDiscrepancy
  patt_scaled_approximation_to_matching_discrepancy :=
    pattScaledApproximationToMatchingDiscrepancy

theorem
    pate_patt_known_score_asymptotic_normality_of_finite_score_cell_stochastic_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality := by
  exact
    pate_patt_known_score_asymptotic_normality_of_paired_finite_score_cell_stochastic
      (patePattFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual

/--
Paired GC-backed known-score asymptotic normality together with score-cell
mass LLNs for both finite score partitions.
-/
theorem
    pate_patt_known_score_asymptotic_normality_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hnormal :=
    pate_patt_known_score_asymptotic_normality_of_finite_score_cell_stochastic_glivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy hpateGC hpateFinite
      hpateEnvelope hpateSimplex hpateLinear hpateMatrix hpattGC
      hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
  have hmass :=
    paired_cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare
      pateSample pattSample pateWeight pattWeight pateScore pattScore
      hpateGC hpattGC
  exact
    ⟨hnormal.1, hnormal.2.1, hnormal.2.2.1, hmass.1.2,
      hnormal.2.2.2.1, hnormal.2.2.2.2.1, hnormal.2.2.2.2.2,
      hmass.2.2⟩

/--
Paired known-score asymptotic normality and score-cell mass LLNs from finite
`L1(P)` bracketing obligations on both LLN sides and packaged finite
score-cell vector CLTs on both scaled sides.
-/
theorem
    pate_patt_known_score_asymptotic_normality_and_mass_lln_of_finite_score_cell_stochastic_l1BracketingNumber_vector_clt
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize)
            (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (pateEnvelope : pateIndicatorBridge.envelope_convergence)
    (pateVector :
      pateCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize)
            (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    (pattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (pattEnvelope : pattIndicatorBridge.envelope_convergence)
    (pattVector :
      pattCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have happrox :=
    pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_l1BracketingNumber_vector_clt
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pateObligations pateFinite pateEnvelope
      pateVector pattCells pattReferenceShare pattSample pattWeight pattScore
      pattIndicatorBridge pattFiniteLLNToIndicatorLLN pattCLTBridge
      pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pattObligations pattFinite pattEnvelope
      pattVector
  have hpateMatching :
      pateKnownScoreBridge.matching_discrepancy_negligible :=
    pateScaledApproximationToMatchingDiscrepancy happrox.2.1
  have hpattMatching :
      pattKnownScoreBridge.matching_discrepancy_negligible :=
    pattScaledApproximationToMatchingDiscrepancy happrox.2.2.2.2.1
  have hpateAsymptotic : pateKnownScoreBridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge
      pateKnownScoreBridge hpateDecomp hpateDenominator
      hpateHeterogeneity hpateResidual hpateMatching
  have hpattAsymptotic : pattKnownScoreBridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge
      pattKnownScoreBridge hpattDecomp hpattDenominator
      hpattHeterogeneity hpattResidual hpattMatching
  exact
    ⟨happrox.1, happrox.2.1, hpateAsymptotic, happrox.2.2.1,
      happrox.2.2.2.1, happrox.2.2.2.2.1, hpattAsymptotic,
      happrox.2.2.2.2.2⟩

/--
Paired known-score asymptotic normality and score-cell mass LLNs from VdV-W
endpoint assemblies on both LLN sides and packaged finite score-cell vector
CLTs on both scaled sides.
-/
theorem
    pate_patt_known_score_asymptotic_normality_and_mass_lln_of_finite_score_cell_stochastic_vdvw241_endpoint_vector_clt
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize)
            (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (pateEnvelope : pateIndicatorBridge.envelope_convergence)
    (pateVector :
      pateCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize)
            (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    (pattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (pattEnvelope : pattIndicatorBridge.envelope_convergence)
    (pattVector :
      pattCLTBridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have happrox :=
    pate_patt_unscaled_and_scaled_approximation_negligible_and_mass_lln_of_finite_score_cell_stochastic_vdvw241_endpoint_vector_clt
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pateAssembly pateFinite pateEnvelope
      pateVector pattCells pattReferenceShare pattSample pattWeight pattScore
      pattIndicatorBridge pattFiniteLLNToIndicatorLLN pattCLTBridge
      pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pattAssembly pattFinite pattEnvelope pattVector
  have hpateMatching :
      pateKnownScoreBridge.matching_discrepancy_negligible :=
    pateScaledApproximationToMatchingDiscrepancy happrox.2.1
  have hpattMatching :
      pattKnownScoreBridge.matching_discrepancy_negligible :=
    pattScaledApproximationToMatchingDiscrepancy happrox.2.2.2.2.1
  have hpateAsymptotic : pateKnownScoreBridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge
      pateKnownScoreBridge hpateDecomp hpateDenominator
      hpateHeterogeneity hpateResidual hpateMatching
  have hpattAsymptotic : pattKnownScoreBridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge
      pattKnownScoreBridge hpattDecomp hpattDenominator
      hpattHeterogeneity hpattResidual hpattMatching
  exact
    ⟨happrox.1, happrox.2.1, hpateAsymptotic, happrox.2.2.1,
      happrox.2.2.2.1, happrox.2.2.2.2.1, hpattAsymptotic,
      happrox.2.2.2.2.2⟩

/--
Build a paired estimated-score asymptotic bridge whose finite score-cell layer
is backed by GC certificates on the LLN side.
-/
def patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality) :
    PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell where
  known_score_finite_cell_bridge :=
    patePattFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy
  pate_estimated_score_bridge := pateEstimatedScoreBridge
  patt_estimated_score_bridge := pattEstimatedScoreBridge
  pate_known_score_to_estimated_score_input :=
    pateKnownScoreToEstimatedScoreInput
  patt_known_score_to_estimated_score_input :=
    pattKnownScoreToEstimatedScoreInput

theorem
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality := by
  exact
    pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic
      (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe



/--
Paired GC-backed estimated-score asymptotic normality from finite score-cell
GC inputs for both score partitions, with PATE/PATT local expansion and
Godambe obligations packaged into compact estimated-score cores.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality := by
  exact
    pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic
      (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst pateCore.matching_functional_local_expansion
      pateCore.godambe_variance_identity hpattFirst
      pattCore.matching_functional_local_expansion
      pattCore.godambe_variance_identity

/--
Paired GC-backed estimated-score asymptotic normality from explicit PATE/PATT
local experiments whose first-step and score-local inputs are assembled from
PATE/PATT component first-step evidence.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_first_step_components_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pateEstimated.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpate_prop_weight : pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop :
      pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated :
      pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control :
      pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpatt_prop_weight : pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop :
      pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control :
      pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpate_functional :
      pateEstimated.matching_functional_local_derivative)
    (hpate_equicontinuity :
      pateEstimated.local_stochastic_equicontinuity)
    (hpate_godambe : pateEstimated.godambe_variance_identity)
    (hpatt_functional :
      pattEstimated.matching_functional_local_derivative)
    (hpatt_equicontinuity :
      pattEstimated.local_stochastic_equicontinuity)
    (hpatt_godambe : pattEstimated.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality :=
  pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic_local_experiment_first_step_components
    (patePattFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy)
    pateEstimated pattEstimated pateFirstStep pattFirstStep
    pateKnownScoreToEstimatedScoreInput
    pattKnownScoreToEstimatedScoreInput hpate_first_transfer
    hpate_score_transfer hpatt_first_transfer hpatt_score_transfer
    hpateGC
    (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
      pateCells pateReferenceShare pateSample pateWeight pateScore)
    hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
    hpattGC
    (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
      pattCells pattReferenceShare pattSample pattWeight pattScore)
    hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
    hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
    hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
    hpate_prop_weight hpate_treated_weight hpate_control_weight hpate_prop
    hpate_treated hpate_control hpatt_prop_weight hpatt_control_weight
    hpatt_prop hpatt_control hpate_functional hpate_equicontinuity
    hpate_godambe hpatt_functional hpatt_equicontinuity hpatt_godambe


/--
Paired GC-backed estimated-score asymptotic normality from PATE/PATT
first-step component evidence, with the local derivative, stochastic
equicontinuity, and Godambe obligations packaged into compact cores.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_first_step_components_glivenkoCantelli_local_experiment_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateCore : EstimatedScoreLocalExperimentCore pateEstimated)
    (pattCore : EstimatedScoreLocalExperimentCore pattEstimated)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pateEstimated.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpate_prop_weight : pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop :
      pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated :
      pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control :
      pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpatt_prop_weight : pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop :
      pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control :
      pattFirstStep.control_prognostic_component_asymptotic_linearity)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality :=
  pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic_local_experiment_first_step_components
    (patePattFiniteScoreCellKnownScoreAsymptoticBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy)
    pateEstimated pattEstimated pateFirstStep pattFirstStep
    pateKnownScoreToEstimatedScoreInput
    pattKnownScoreToEstimatedScoreInput hpate_first_transfer
    hpate_score_transfer hpatt_first_transfer hpatt_score_transfer
    hpateGC
    (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
      pateCells pateReferenceShare pateSample pateWeight pateScore)
    hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
    hpattGC
    (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
      pattCells pattReferenceShare pattSample pattWeight pattScore)
    hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
    hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
    hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
    hpate_prop_weight hpate_treated_weight hpate_control_weight hpate_prop
    hpate_treated hpate_control hpatt_prop_weight hpatt_control_weight
    hpatt_prop hpatt_control
    pateCore.matching_functional_local_derivative
    pateCore.local_stochastic_equicontinuity
    pateCore.godambe_variance_identity
    pattCore.matching_functional_local_derivative
    pattCore.local_stochastic_equicontinuity
    pattCore.godambe_variance_identity

/--
Paired GC-backed estimated-score asymptotic normality from first-step
component evidence, with score-cell mass LLNs for both finite score
partitions attached for downstream bootstrap and Wald routers.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_and_mass_lln_of_finite_score_cell_stochastic_first_step_components_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pateEstimated.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpate_prop_weight : pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop :
      pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated :
      pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control :
      pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpatt_prop_weight : pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop :
      pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control :
      pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpate_functional :
      pateEstimated.matching_functional_local_derivative)
    (hpate_equicontinuity :
      pateEstimated.local_stochastic_equicontinuity)
    (hpate_godambe : pateEstimated.godambe_variance_identity)
    (hpatt_functional :
      pattEstimated.matching_functional_local_derivative)
    (hpatt_equicontinuity :
      pattEstimated.local_stochastic_equicontinuity)
    (hpatt_godambe : pattEstimated.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hestimated :=
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_first_step_components_glivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimated
      pattEstimated pateFirstStep pattFirstStep
      pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput hpate_first_transfer
      hpate_score_transfer hpatt_first_transfer hpatt_score_transfer
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpate_prop_weight hpate_treated_weight hpate_control_weight hpate_prop
      hpate_treated hpate_control hpatt_prop_weight hpatt_control_weight
      hpatt_prop hpatt_control hpate_functional hpate_equicontinuity
      hpate_godambe hpatt_functional hpatt_equicontinuity hpatt_godambe
  exact
    paired_estimated_score_outputs_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
      hestimated


/--
Paired GC-backed estimated-score asymptotic normality and score-cell mass LLNs
from PATE/PATT first-step component evidence, with local-experiment
obligations packaged into compact cores.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_and_mass_lln_of_finite_score_cell_stochastic_first_step_components_glivenkoCantelli_local_experiment_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateCore : EstimatedScoreLocalExperimentCore pateEstimated)
    (pattCore : EstimatedScoreLocalExperimentCore pattEstimated)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pateEstimated.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpate_prop_weight : pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop :
      pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated :
      pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control :
      pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpatt_prop_weight : pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop :
      pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control :
      pattFirstStep.control_prognostic_component_asymptotic_linearity)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hestimated :=
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_first_step_components_glivenkoCantelli_local_experiment_core
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimated
      pattEstimated pateCore pattCore pateFirstStep pattFirstStep
      pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput hpate_first_transfer
      hpate_score_transfer hpatt_first_transfer hpatt_score_transfer
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpate_prop_weight hpate_treated_weight hpate_control_weight hpate_prop
      hpate_treated hpate_control hpatt_prop_weight hpatt_control_weight
      hpatt_prop hpatt_control
  exact
    paired_estimated_score_outputs_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
      hestimated

/--
Paired GC-backed estimated-score asymptotic normality together with score-cell
mass LLNs for both finite score partitions.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hnormal :=
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_glivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput hpateGC hpateFinite hpateEnvelope
      hpateSimplex hpateLinear hpateMatrix hpattGC hpattFinite
      hpattEnvelope hpattSimplex hpattLinear hpattMatrix hpateDecomp
      hpateDenominator hpateHeterogeneity hpateResidual hpattDecomp
      hpattDenominator hpattHeterogeneity hpattResidual hpateFirst
      hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe
  have hmass :=
    paired_cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare
      pateSample pattSample pateWeight pattWeight pateScore pattScore
      hpateGC hpattGC
  exact
    ⟨hnormal.1, hnormal.2.1, hnormal.2.2.1, hnormal.2.2.2.1,
      hmass.1.2, hnormal.2.2.2.2.1, hnormal.2.2.2.2.2.1,
      hnormal.2.2.2.2.2.2.1, hnormal.2.2.2.2.2.2.2,
      hmass.2.2⟩


/--
Paired GC-backed estimated-score asymptotic normality together with score-cell
mass LLNs for both finite score partitions, with PATE/PATT local expansion
and Godambe obligations packaged into compact estimated-score cores.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_and_mass_lln_of_finite_score_cell_stochastic_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hnormal :=
    pate_patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_glivenkoCantelli_estimated_score_core
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateCore pattCore
      pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput hpateGC hpateFinite hpateEnvelope
      hpateSimplex hpateLinear hpateMatrix hpattGC hpattFinite
      hpattEnvelope hpattSimplex hpattLinear hpattMatrix hpateDecomp
      hpateDenominator hpateHeterogeneity hpateResidual hpattDecomp
      hpattDenominator hpattHeterogeneity hpattResidual hpateFirst hpattFirst
  have hmass :=
    paired_cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare
      pateSample pattSample pateWeight pattWeight pateScore pattScore
      hpateGC hpattGC
  exact
    ⟨hnormal.1, hnormal.2.1, hnormal.2.2.1, hnormal.2.2.2.1,
      hmass.1.2, hnormal.2.2.2.2.1, hnormal.2.2.2.2.2.1,
      hnormal.2.2.2.2.2.2.1, hnormal.2.2.2.2.2.2.2,
      hmass.2.2⟩

/--
Build a paired estimated-score studentized bridge whose finite score-cell layer
is backed by GC certificates on the LLN side.
-/
def patePattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScoreStudentizedBridge PATECell PATTCell
      Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput
  pate_studentization_input := pateStudentizationInput
  patt_studentization_input := pattStudentizationInput
  pate_estimated_score_to_scaled_tendsto :=
    pateEstimatedScoreToScaledTendsto
  patt_estimated_score_to_scaled_tendsto :=
    pattEstimatedScoreToScaledTendsto

theorem
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  exact
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score
      (patePattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
        pateStudentizationInput pattStudentizationInput
        pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe


/--
Paired GC-backed estimated-score studentized weak limits with the PATE/PATT
local expansion and Godambe obligations packaged into compact cores.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  exact
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score
      (patePattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
        pateStudentizationInput pattStudentizationInput
        pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst pateCore.matching_functional_local_expansion
      pateCore.godambe_variance_identity hpattFirst
      pattCore.matching_functional_local_expansion
      pattCore.godambe_variance_identity

/--
Paired GC-backed estimated-score studentized weak limits together with
score-cell mass LLNs for both finite score partitions.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_and_mass_lln_of_finite_score_cell_estimated_score_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hstudentized :=
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_glivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
      pateStudentizationInput pattStudentizationInput
      pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe
  exact
    paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
      hstudentized


/--
Paired GC-backed estimated-score studentized weak limits together with
score-cell mass LLNs, with PATE/PATT local expansion and Godambe obligations
packaged into compact estimated-score cores.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_and_mass_lln_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hstudentized :=
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateCore pattCore
      pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
      pateStudentizationInput pattStudentizationInput
      pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst hpattFirst
  exact
    paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
      hstudentized

/--
Build a paired positive-variance estimated-score studentized bridge whose
finite score-cell layer is backed by GC certificates on the LLN side.
-/
def
    patePattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput
  pate_studentization_input := pateStudentizationInput
  patt_studentization_input := pattStudentizationInput
  pate_estimated_score_to_scaled_tendsto :=
    pateEstimatedScoreToScaledTendsto
  patt_estimated_score_to_scaled_tendsto :=
    pattEstimatedScoreToScaledTendsto

theorem
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  exact
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance
      (patePattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
        pateStudentizationInput pattStudentizationInput
        pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe


/--
Paired GC-backed positive-variance estimated-score studentized weak limits
with the PATE/PATT local expansion and Godambe obligations packaged into
compact cores.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  exact
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance
      (patePattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
        pateStudentizationInput pattStudentizationInput
        pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto)
      hpateGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pateCells pateReferenceShare pateSample pateWeight pateScore)
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC
      (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
        pattCells pattReferenceShare pattSample pattWeight pattScore)
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst pateCore.matching_functional_local_expansion
      pateCore.godambe_variance_identity hpattFirst
      pattCore.matching_functional_local_expansion
      pattCore.godambe_variance_identity

/--
Paired GC-backed positive-variance estimated-score studentized weak limits
together with score-cell mass LLNs for both finite score partitions.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_and_mass_lln_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hstudentized :=
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
      pateStudentizationInput pattStudentizationInput
      pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe
  exact
    paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
      hstudentized


/--
Paired GC-backed positive-variance estimated-score studentized weak limits
together with score-cell mass LLNs, with PATE/PATT local expansion and
Godambe obligations packaged into compact estimated-score cores.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_and_mass_lln_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    {Index Sample LimitSample : Type*}
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample)
    (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    :
    pateIndicatorBridge.pate_double_score_approximation_negligible ∧
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      pateKnownScoreBridge.asymptotic_normality ∧
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      pattIndicatorBridge.patt_double_score_approximation_negligible ∧
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      pattKnownScoreBridge.asymptotic_normality ∧
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hstudentized :=
    pate_patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance_glivenkoCantelli_estimated_score_core
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateCore pattCore
      pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
      pateStudentizationInput pattStudentizationInput
      pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto
      hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
      hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
      hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
      hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
      hpateFirst hpattFirst
  exact
    paired_studentized_outputs_and_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
      hstudentized

variable {PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]


/--
PATE approximation convergence from GC certificates for the target, treated,
and control weighted joint-score indicator sums.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    (targetSample treatedSample controlSample : ℕ -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : ℕ -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (treatedPrognosticScore : ℕ -> Unit -> TreatedProgCell)
    (controlPrognosticScore : ℕ -> Unit -> ControlProgCell)
    (treatedValue : ℕ -> TreatedProgCell -> Real)
    (controlValue : ℕ -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : ℕ -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (gcTarget :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcTreated :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassTreated :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (treatedSample sampleSize) (treatedWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeT sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        treatedOutcome sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeC sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (htreated_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue sampleSize) cell| ≤
          treatedEnvelope sampleSize)
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (htreatedEnvelope :
      Tendsto treatedEnvelope atTop (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        weightedSampleMeanContrast (targetSample sampleSize)
          (targetWeight sampleSize) (targetOutcomeT sampleSize)
          (targetOutcomeC sampleSize) -
        twoArmWeightedMeanContrast (treatedSample sampleSize)
          (controlSample sampleSize) (treatedWeight sampleSize)
          (controlWeight sampleSize) (treatedOutcome sampleSize)
          (controlOutcome sampleSize))
      atTop (nhds 0) := by
  exact tendsto_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
      cells targetSample targetWeight
      (fun sampleSize =>
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize))
      massLimit gcTarget)
    (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
      cells treatedSample treatedWeight
      (fun sampleSize =>
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize))
      massLimit gcTreated)
    (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
      cells controlSample controlWeight
      (fun sampleSize =>
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize))
      massLimit gcControl)
    htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope

/--
PATE approximation convergence from finite `L1(P)` bracketing obligations for
the target, treated, and control weighted joint-score indicator sums.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_indicator_l1BracketingNumber_obligations
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket] [Fintype ControlBracket]
    (targetSample treatedSample controlSample : ℕ -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : ℕ -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (treatedPrognosticScore : ℕ -> Unit -> TreatedProgCell)
    (controlPrognosticScore : ℕ -> Unit -> ControlProgCell)
    (treatedValue : ℕ -> TreatedProgCell -> Real)
    (controlValue : ℕ -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : ℕ -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (targetObligations :
      L1BracketingNumberConstructorObligations (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedObligations :
      L1BracketingNumberConstructorObligations (Bracket := TreatedBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassTreated :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (treatedSample sampleSize) (treatedWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeT sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        treatedOutcome sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeC sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (htreated_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue sampleSize) cell| ≤
          treatedEnvelope sampleSize)
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (htreatedEnvelope :
      Tendsto treatedEnvelope atTop (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        weightedSampleMeanContrast (targetSample sampleSize)
          (targetWeight sampleSize) (targetOutcomeT sampleSize)
          (targetOutcomeC sampleSize) -
        twoArmWeightedMeanContrast (treatedSample sampleSize)
          (controlSample sampleSize) (treatedWeight sampleSize)
          (controlWeight sampleSize) (treatedOutcome sampleSize)
          (controlOutcome sampleSize))
      atTop (nhds 0) :=
  tendsto_pateDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetObligations.toGlivenkoCantelliClass
    treatedObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass hcoverTarget hcoverTreated
    hcoverControl hmassTarget hmassTreated hmassControl htotalLimit
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
    htreated_bound hcontrol_bound htreatedEnvelope hcontrolEnvelope

/--
PATE approximation convergence from VdV&W endpoint assemblies for the target,
treated, and control weighted joint-score indicator sums.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_indicator_vdvw241_endpoint_assembly
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket] [Fintype ControlBracket]
    (targetSample treatedSample controlSample : ℕ -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : ℕ -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (treatedPrognosticScore : ℕ -> Unit -> TreatedProgCell)
    (controlPrognosticScore : ℕ -> Unit -> ControlProgCell)
    (treatedValue : ℕ -> TreatedProgCell -> Real)
    (controlValue : ℕ -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : ℕ -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (targetAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TreatedBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassTreated :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (treatedSample sampleSize) (treatedWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeT sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        treatedOutcome sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeC sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (htreated_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue sampleSize) cell| ≤
          treatedEnvelope sampleSize)
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (htreatedEnvelope :
      Tendsto treatedEnvelope atTop (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        weightedSampleMeanContrast (targetSample sampleSize)
          (targetWeight sampleSize) (targetOutcomeT sampleSize)
          (targetOutcomeC sampleSize) -
        twoArmWeightedMeanContrast (treatedSample sampleSize)
          (controlSample sampleSize) (treatedWeight sampleSize)
          (controlWeight sampleSize) (treatedOutcome sampleSize)
          (controlOutcome sampleSize))
      atTop (nhds 0) :=
  tendsto_pateDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetAssembly.toGlivenkoCantelliClass
    treatedAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass hcoverTarget hcoverTreated
    hcoverControl hmassTarget hmassTreated hmassControl htotalLimit
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
    htreated_bound hcontrol_bound htreatedEnvelope hcontrolEnvelope

/--
PATT approximation convergence from GC certificates for the target and control
weighted joint-score indicator sums.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    (targetSample controlSample : ℕ -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : ℕ -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (controlPrognosticScore : ℕ -> Unit -> PATTProgCell)
    (controlValue : ℕ -> PATTProgCell -> Real)
    (controlEnvelope : ℕ -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (gcTarget :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetControlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        weightedSampleMeanContrast (targetSample sampleSize)
          (targetWeight sampleSize) (treatedTargetOutcome sampleSize)
          (targetControlOutcome sampleSize) -
        pattWeightedMeanContrast (targetSample sampleSize)
          (controlSample sampleSize) (targetWeight sampleSize)
          (controlWeight sampleSize) (treatedTargetOutcome sampleSize)
          (controlOutcome sampleSize))
      atTop (nhds 0) := by
  exact tendsto_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit hcoverTarget hcoverControl hmassTarget hmassControl
    (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
      cells targetSample targetWeight
      (fun sampleSize =>
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize))
      massLimit gcTarget)
    (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
      cells controlSample controlWeight
      (fun sampleSize =>
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize))
      massLimit gcControl)
    htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope

/--
PATT approximation convergence from finite `L1(P)` bracketing obligations for
the target and control weighted joint-score indicator sums.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_indicator_l1BracketingNumber_obligations
    {TargetBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype ControlBracket]
    (targetSample controlSample : ℕ -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : ℕ -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (controlPrognosticScore : ℕ -> Unit -> PATTProgCell)
    (controlValue : ℕ -> PATTProgCell -> Real)
    (controlEnvelope : ℕ -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (targetObligations :
      L1BracketingNumberConstructorObligations (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetControlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        weightedSampleMeanContrast (targetSample sampleSize)
          (targetWeight sampleSize) (treatedTargetOutcome sampleSize)
          (targetControlOutcome sampleSize) -
        pattWeightedMeanContrast (targetSample sampleSize)
          (controlSample sampleSize) (targetWeight sampleSize)
          (controlWeight sampleSize) (treatedTargetOutcome sampleSize)
          (controlOutcome sampleSize))
      atTop (nhds 0) :=
  tendsto_pattDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass hcoverTarget hcoverControl
    hmassTarget hmassControl htotalLimit hscoreMeasTargetC hscoreMeasControl
    hcontrol_bound hcontrolEnvelope

/--
PATT approximation convergence from VdV&W endpoint assemblies for the target
and control weighted joint-score indicator sums.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_indicator_vdvw241_endpoint_assembly
    {TargetBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype ControlBracket]
    (targetSample controlSample : ℕ -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : ℕ -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (controlPrognosticScore : ℕ -> Unit -> PATTProgCell)
    (controlValue : ℕ -> PATTProgCell -> Real)
    (controlEnvelope : ℕ -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (targetAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetControlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        weightedSampleMeanContrast (targetSample sampleSize)
          (targetWeight sampleSize) (treatedTargetOutcome sampleSize)
          (targetControlOutcome sampleSize) -
        pattWeightedMeanContrast (targetSample sampleSize)
          (controlSample sampleSize) (targetWeight sampleSize)
          (controlWeight sampleSize) (treatedTargetOutcome sampleSize)
          (controlOutcome sampleSize))
      atTop (nhds 0) :=
  tendsto_pattDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass hcoverTarget hcoverControl
    hmassTarget hmassControl htotalLimit hscoreMeasTargetC hscoreMeasControl
    hcontrol_bound hcontrolEnvelope

/--
Scaled PATE approximation convergence from GC certificates for the unscaled
weighted joint-score indicator sums plus explicit scaled target-arm indicator
difference convergence.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    (scale : ℕ -> Real)
    (targetSample treatedSample controlSample : ℕ -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : ℕ -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (treatedPrognosticScore : ℕ -> Unit -> TreatedProgCell)
    (controlPrognosticScore : ℕ -> Unit -> ControlProgCell)
    (treatedValue : ℕ -> TreatedProgCell -> Real)
    (controlValue : ℕ -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : ℕ -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (gcTarget :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcTreated :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hscale_nonneg : ∀ sampleSize, 0 ≤ scale sampleSize)
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassTreated :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (treatedSample sampleSize) (treatedWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hscaledIndicatorTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (treatedSample sampleSize)
                  (treatedWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (controlSample sampleSize)
                  (controlWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeT sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        treatedOutcome sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeC sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (htreated_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue sampleSize) cell| ≤
          treatedEnvelope sampleSize)
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (htreatedEnvelope :
      Tendsto treatedEnvelope atTop (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        scale sampleSize *
          (weightedSampleMeanContrast (targetSample sampleSize)
            (targetWeight sampleSize) (targetOutcomeT sampleSize)
            (targetOutcomeC sampleSize) -
          twoArmWeightedMeanContrast (treatedSample sampleSize)
            (controlSample sampleSize) (treatedWeight sampleSize)
            (controlWeight sampleSize) (treatedOutcome sampleSize)
            (controlOutcome sampleSize)))
      atTop (nhds 0) := by
  exact
    tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
      scale targetSample treatedSample controlSample cells targetWeight
      treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
      controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
      hscale_nonneg hcoverTarget hcoverTreated hcoverControl hmassTarget
      hmassTreated hmassControl
      (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells targetSample targetWeight
        (fun sampleSize =>
          pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcTarget)
      (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells treatedSample treatedWeight
        (fun sampleSize =>
          pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcTreated)
      (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells controlSample controlWeight
        (fun sampleSize =>
          pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcControl)
      hscaledIndicatorTreated hscaledIndicatorControl htotalLimit
      hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
      hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
      hcontrolEnvelope

/--
Scaled PATE approximation convergence from finite `L1(P)` bracketing
obligations for the unscaled weighted joint-score indicator sums, plus explicit
scaled target-arm indicator difference convergence.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_l1BracketingNumber_obligations
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket] [Fintype ControlBracket]
    (scale : ℕ -> Real)
    (targetSample treatedSample controlSample : ℕ -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : ℕ -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (treatedPrognosticScore : ℕ -> Unit -> TreatedProgCell)
    (controlPrognosticScore : ℕ -> Unit -> ControlProgCell)
    (treatedValue : ℕ -> TreatedProgCell -> Real)
    (controlValue : ℕ -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : ℕ -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (targetObligations :
      L1BracketingNumberConstructorObligations (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedObligations :
      L1BracketingNumberConstructorObligations (Bracket := TreatedBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hscale_nonneg : ∀ sampleSize, 0 ≤ scale sampleSize)
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassTreated :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (treatedSample sampleSize) (treatedWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hscaledIndicatorTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (treatedSample sampleSize)
                  (treatedWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (controlSample sampleSize)
                  (controlWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeT sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        treatedOutcome sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeC sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (htreated_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue sampleSize) cell| ≤
          treatedEnvelope sampleSize)
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (htreatedEnvelope :
      Tendsto treatedEnvelope atTop (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        scale sampleSize *
          (weightedSampleMeanContrast (targetSample sampleSize)
            (targetWeight sampleSize) (targetOutcomeT sampleSize)
            (targetOutcomeC sampleSize) -
          twoArmWeightedMeanContrast (treatedSample sampleSize)
            (controlSample sampleSize) (treatedWeight sampleSize)
            (controlWeight sampleSize) (treatedOutcome sampleSize)
            (controlOutcome sampleSize)))
      atTop (nhds 0) :=
  tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetObligations.toGlivenkoCantelliClass
    treatedObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass hscale_nonneg hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    hscaledIndicatorTreated hscaledIndicatorControl htotalLimit
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
    htreated_bound hcontrol_bound htreatedEnvelope hcontrolEnvelope

/--
Scaled PATE approximation convergence from VdV&W endpoint assemblies for the
unscaled weighted joint-score indicator sums, plus explicit scaled target-arm
indicator difference convergence.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_vdvw241_endpoint_assembly
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket] [Fintype ControlBracket]
    (scale : ℕ -> Real)
    (targetSample treatedSample controlSample : ℕ -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : ℕ -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (treatedPrognosticScore : ℕ -> Unit -> TreatedProgCell)
    (controlPrognosticScore : ℕ -> Unit -> ControlProgCell)
    (treatedValue : ℕ -> TreatedProgCell -> Real)
    (controlValue : ℕ -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : ℕ -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (targetAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TreatedBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hscale_nonneg : ∀ sampleSize, 0 ≤ scale sampleSize)
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pateDoubleScore (propensityScore sampleSize)
          (treatedPrognosticScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassTreated :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (treatedSample sampleSize) (treatedWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hscaledIndicatorTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (treatedSample sampleSize)
                  (treatedWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (controlSample sampleSize)
                  (controlWeight sampleSize)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore sampleSize)
                      (treatedPrognosticScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeT sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTreated :
      ∀ sampleSize unit, unit ∈ treatedSample sampleSize ->
        treatedOutcome sampleSize unit =
          treatedValue sampleSize (treatedPrognosticScore sampleSize unit))
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetOutcomeC sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (htreated_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue sampleSize) cell| ≤
          treatedEnvelope sampleSize)
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (htreatedEnvelope :
      Tendsto treatedEnvelope atTop (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        scale sampleSize *
          (weightedSampleMeanContrast (targetSample sampleSize)
            (targetWeight sampleSize) (targetOutcomeT sampleSize)
            (targetOutcomeC sampleSize) -
          twoArmWeightedMeanContrast (treatedSample sampleSize)
            (controlSample sampleSize) (treatedWeight sampleSize)
            (controlWeight sampleSize) (treatedOutcome sampleSize)
            (controlOutcome sampleSize)))
      atTop (nhds 0) :=
  tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetAssembly.toGlivenkoCantelliClass
    treatedAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass hscale_nonneg hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    hscaledIndicatorTreated hscaledIndicatorControl htotalLimit
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
    htreated_bound hcontrol_bound htreatedEnvelope hcontrolEnvelope

/--
Scaled PATT approximation convergence from GC certificates for the unscaled
weighted joint-score indicator sums plus explicit scaled target-control
indicator difference convergence.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    (scale : ℕ -> Real)
    (targetSample controlSample : ℕ -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : ℕ -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (controlPrognosticScore : ℕ -> Unit -> PATTProgCell)
    (controlValue : ℕ -> PATTProgCell -> Real)
    (controlEnvelope : ℕ -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (gcTarget :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hscale_nonneg : ∀ sampleSize, 0 ≤ scale sampleSize)
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (controlSample sampleSize)
                  (controlWeight sampleSize)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetControlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        scale sampleSize *
          (weightedSampleMeanContrast (targetSample sampleSize)
            (targetWeight sampleSize) (treatedTargetOutcome sampleSize)
            (targetControlOutcome sampleSize) -
          pattWeightedMeanContrast (targetSample sampleSize)
            (controlSample sampleSize) (targetWeight sampleSize)
            (controlWeight sampleSize) (treatedTargetOutcome sampleSize)
            (controlOutcome sampleSize)))
      atTop (nhds 0) := by
  exact
    tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
      scale targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
      controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
      massLimit hscale_nonneg hcoverTarget hcoverControl hmassTarget
      hmassControl
      (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells targetSample targetWeight
        (fun sampleSize =>
          pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcTarget)
      (tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells controlSample controlWeight
        (fun sampleSize =>
          pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcControl)
      hscaledIndicatorControl htotalLimit hscoreMeasTargetC hscoreMeasControl
      hcontrol_bound hcontrolEnvelope

/--
Scaled PATT approximation convergence from finite `L1(P)` bracketing
obligations for the unscaled target/control joint-score indicator sums, plus
explicit scaled target-control indicator difference convergence.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_l1BracketingNumber_obligations
    {TargetBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype ControlBracket]
    (scale : ℕ -> Real)
    (targetSample controlSample : ℕ -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : ℕ -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (controlPrognosticScore : ℕ -> Unit -> PATTProgCell)
    (controlValue : ℕ -> PATTProgCell -> Real)
    (controlEnvelope : ℕ -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (targetObligations :
      L1BracketingNumberConstructorObligations (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hscale_nonneg : ∀ sampleSize, 0 ≤ scale sampleSize)
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (controlSample sampleSize)
                  (controlWeight sampleSize)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetControlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        scale sampleSize *
          (weightedSampleMeanContrast (targetSample sampleSize)
            (targetWeight sampleSize) (treatedTargetOutcome sampleSize)
            (targetControlOutcome sampleSize) -
          pattWeightedMeanContrast (targetSample sampleSize)
            (controlSample sampleSize) (targetWeight sampleSize)
            (controlWeight sampleSize) (treatedTargetOutcome sampleSize)
            (controlOutcome sampleSize)))
      atTop (nhds 0) :=
  tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass hscale_nonneg hcoverTarget
    hcoverControl hmassTarget hmassControl hscaledIndicatorControl
    htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope

/--
Scaled PATT approximation convergence from VdV&W endpoint assemblies for the
unscaled target/control joint-score indicator sums, plus explicit scaled
target-control indicator difference convergence.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_vdvw241_endpoint_assembly
    {TargetBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype ControlBracket]
    (scale : ℕ -> Real)
    (targetSample controlSample : ℕ -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : ℕ -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      ℕ -> Unit -> Real)
    (propensityScore : ℕ -> Unit -> PropensityCell)
    (controlPrognosticScore : ℕ -> Unit -> PATTProgCell)
    (controlValue : ℕ -> PATTProgCell -> Real)
    (controlEnvelope : ℕ -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (targetAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TargetBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (hscale_nonneg : ∀ sampleSize, 0 ≤ scale sampleSize)
    (hcoverTarget :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hcoverControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        pattDoubleScore (propensityScore sampleSize)
          (controlPrognosticScore sampleSize) unit ∈ cells)
    (hmassTarget :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (targetSample sampleSize) (targetWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hmassControl :
      ∀ sampleSize cell, cell ∈ cells ->
        scoreCellMass (controlSample sampleSize) (controlWeight sampleSize)
          (pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize)) cell ≠ 0)
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            scale sampleSize *
              (weightedSampleSum (targetSample sampleSize)
                  (targetWeight sampleSize)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell) -
                weightedSampleSum (controlSample sampleSize)
                  (controlWeight sampleSize)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore sampleSize)
                      (controlPrognosticScore sampleSize)) cell)))
          atTop (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ sampleSize unit, unit ∈ targetSample sampleSize ->
        targetControlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hscoreMeasControl :
      ∀ sampleSize unit, unit ∈ controlSample sampleSize ->
        controlOutcome sampleSize unit =
          controlValue sampleSize (controlPrognosticScore sampleSize unit))
    (hcontrol_bound :
      ∀ sampleSize cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue sampleSize) cell| ≤
          controlEnvelope sampleSize)
    (hcontrolEnvelope :
      Tendsto controlEnvelope atTop (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun sampleSize =>
        scale sampleSize *
          (weightedSampleMeanContrast (targetSample sampleSize)
            (targetWeight sampleSize) (treatedTargetOutcome sampleSize)
            (targetControlOutcome sampleSize) -
          pattWeightedMeanContrast (targetSample sampleSize)
            (controlSample sampleSize) (targetWeight sampleSize)
            (controlWeight sampleSize) (treatedTargetOutcome sampleSize)
            (controlOutcome sampleSize)))
      atTop (nhds 0) :=
  tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_glivenkoCantelli
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass hscale_nonneg hcoverTarget
    hcoverControl hmassTarget hmassControl hscaledIndicatorControl
    htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope

end WDSM
end Matching
end StatInference
