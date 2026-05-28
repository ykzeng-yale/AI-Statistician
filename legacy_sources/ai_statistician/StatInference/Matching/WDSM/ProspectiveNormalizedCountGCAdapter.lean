import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter
import StatInference.Matching.WDSM.FiniteCellMassConvergence
import StatInference.Matching.WDSM.ProspectiveNormalizedCountIndicatorInterfaceBridge

/-!
# GC adapters for prospective normalized counts

This module routes the ordinary prospective normalized-count LLN layer through
the finite score-cell GC/bracketing interface.  It deliberately leaves scaled
cell-count differences and CLT/rate inputs as explicit assumptions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators Function

variable {Unit Cell : Type*} [DecidableEq Cell]

/--
Cellwise score-cell mass LLNs plus eventual fixed-partition coverage imply the
constant-one weighted total indicator LLN.  This is the total-count side needed
by prospective normalized-count ratio bridges.
-/
theorem tendsto_weightedSampleSum_one_of_cellwise_mass_lln_eventually_cover
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (hcover :
      ∀ᶠ sampleSize in atTop,
        ∀ unit, unit ∈ sample sampleSize -> score sampleSize unit ∈ cells)
    (hmass :
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        massLimit) :
    Tendsto
      (fun sampleSize =>
        weightedSampleSum (sample sampleSize) (weight sampleSize)
          (fun _unit => (1 : Real)))
      atTop (nhds (∑ cell ∈ cells, massLimit cell)) := by
  have hsum :
      Tendsto
        (fun sampleSize =>
          ∑ cell ∈ cells,
            scoreCellMass (sample sampleSize) (weight sampleSize)
              (score sampleSize) cell)
        atTop (nhds (∑ cell ∈ cells, massLimit cell)) :=
    tendsto_sum_cell_values cells
      (fun sampleSize cell =>
        scoreCellMass (sample sampleSize) (weight sampleSize)
          (score sampleSize) cell)
      massLimit hmass
  have heq :
      (fun sampleSize =>
        weightedSampleSum (sample sampleSize) (weight sampleSize)
          (fun _unit => (1 : Real))) =ᶠ[atTop]
      (fun sampleSize =>
        ∑ cell ∈ cells,
          scoreCellMass (sample sampleSize) (weight sampleSize)
            (score sampleSize) cell) := by
    filter_upwards [hcover] with sampleSize hcoverSize
    calc
      weightedSampleSum (sample sampleSize) (weight sampleSize)
          (fun _unit => (1 : Real)) =
          weightedSampleTotal (sample sampleSize) (weight sampleSize) := by
            rw [weightedSampleSum_one_eq_weightedSampleTotal]
      _ =
          ∑ cell ∈ cells,
            scoreCellMass (sample sampleSize) (weight sampleSize)
              (score sampleSize) cell := by
            exact
              (sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
                (sample sampleSize) cells (weight sampleSize)
                (score sampleSize) hcoverSize).symm
  exact hsum.congr' heq.symm

/--
A finite score-cell GC certificate supplies both the cellwise indicator LLN and
the total constant-one indicator LLN for prospective normalized counts.
-/
theorem prospective_normalized_count_indicator_llns_of_glivenkoCantelli
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (normalizer : ℕ -> Real)
    (cellLimit : Cell -> Real)
    (hcover :
      ∀ᶠ sampleSize in atTop,
        ∀ unit, unit ∈ sample sampleSize -> score sampleSize unit ∈ cells)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells cellLimit sample (fun sampleSize _unit => normalizer sampleSize)
        score).weighted_indicator_array_lln) :
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize)
            (fun _unit => normalizer sampleSize)
            (scoreCellIndicator (score sampleSize) cell))
        atTop (nhds (cellLimit cell))) ∧
    Tendsto
      (fun sampleSize =>
        weightedSampleSum (sample sampleSize)
          (fun _unit => normalizer sampleSize) (fun _unit => (1 : Real)))
      atTop (nhds (∑ cell ∈ cells, cellLimit cell)) := by
  have hboth :=
    cellwise_weighted_indicator_sum_and_mass_lln_of_glivenkoCantelli_bridge
      cells cellLimit sample (fun sampleSize _unit => normalizer sampleSize)
      score hgc
  exact
    ⟨hboth.1,
      tendsto_weightedSampleSum_one_of_cellwise_mass_lln_eventually_cover
        cells sample (fun sampleSize _unit => normalizer sampleSize) score
        cellLimit hcover hboth.2⟩

/--
VdV&W outer-a.s. GC supplies the prospective normalized-count indicator LLNs
pathwise, once the observation-level class is identified with the WDSM
constant-normalizer score-cell indicators.
-/
theorem prospective_normalized_count_indicator_llns_ae_of_vdvw_outerAlmostSure
    {Ω Observation : Type*} [MeasurableSpace Ω] [MeasurableSpace Observation]
    {μ : Measure Ω} {P : Measure Observation}
    (cells : Finset Cell)
    (classFun : Cell -> Observation -> ℝ)
    (X : ℕ -> Ω -> Observation)
    (sample : Ω -> ℕ -> Finset Unit)
    (score : Ω -> ℕ -> Unit -> Cell)
    (normalizer : Ω -> ℕ -> Real)
    (cellLimit : Cell -> Real)
    (hgc :
      VdVWOuterAlmostSurePGlivenkoCantelliClass μ P
        {cell : Cell | cell ∈ cells} classFun X)
    (hpopulation :
      ∀ cell, cell ∈ cells ->
        populationRiskOfFunction P (classFun cell) = cellLimit cell)
    (hempirical :
      ∀ ω sampleSize cell, cell ∈ cells ->
        empiricalAverage (samplePath X ω sampleSize) (classFun cell) =
          weightedSampleSum (sample ω sampleSize)
            (fun _unit => normalizer ω sampleSize)
            (scoreCellIndicator (score ω sampleSize) cell))
    (hcover :
      ∀ᵐ ω ∂μ,
        ∀ᶠ sampleSize in atTop,
          ∀ unit, unit ∈ sample ω sampleSize ->
            score ω sampleSize unit ∈ cells) :
    ∀ᵐ ω ∂μ,
      ((∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            weightedSampleSum (sample ω sampleSize)
              (fun _unit => normalizer ω sampleSize)
              (scoreCellIndicator (score ω sampleSize) cell))
          atTop (nhds (cellLimit cell))) ∧
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample ω sampleSize)
            (fun _unit => normalizer ω sampleSize) (fun _unit => (1 : Real)))
        atTop (nhds (∑ cell ∈ cells, cellLimit cell))) := by
  have hscore :
      ∀ᵐ ω ∂μ,
        ((∀ cell, cell ∈ cells ->
          Tendsto
            (fun sampleSize =>
              weightedSampleSum (sample ω sampleSize)
                (fun _unit => normalizer ω sampleSize)
                (scoreCellIndicator (score ω sampleSize) cell))
            atTop (nhds (cellLimit cell))) ∧
          cellwiseScoreCellMassLLN (l := atTop) cells (sample ω)
            (fun sampleSize _unit => normalizer ω sampleSize) (score ω)
            cellLimit) :=
    cellwise_weighted_indicator_sum_and_mass_lln_ae_of_vdvw_outerAlmostSure
      cells cellLimit classFun X sample
      (fun ω sampleSize _unit => normalizer ω sampleSize) score hgc
      hpopulation hempirical
  filter_upwards [hscore, hcover] with ω hscoreω hcoverω
  exact
    ⟨hscoreω.1,
      tendsto_weightedSampleSum_one_of_cellwise_mass_lln_eventually_cover
        cells (sample ω) (fun sampleSize _unit => normalizer ω sampleSize)
        (score ω) cellLimit hcoverω hscoreω.2⟩

/--
Iid observations plus primitive finite `L1(P)` bracketing numbers at every
positive radius supply the prospective normalized-count indicator LLNs
pathwise, including the total constant-one count.  This is the concrete
iid/bracketing version of
`prospective_normalized_count_indicator_llns_ae_of_vdvw_outerAlmostSure`.
-/
theorem prospective_normalized_count_indicator_llns_ae_of_iid_l1BracketingNumber
    {Ω Observation : Type*} [MeasurableSpace Ω] [MeasurableSpace Observation]
    {μ : Measure Ω} {P : Measure Observation}
    (cells : Finset Cell)
    (classFun : Cell -> Observation -> ℝ)
    (X : ℕ -> Ω -> Observation)
    (sample : Ω -> ℕ -> Finset Unit)
    (score : Ω -> ℕ -> Unit -> Cell)
    (normalizer : Ω -> ℕ -> Real)
    (cellLimit : Cell -> Real)
    (hLaw : ∀ i, HasLaw (X i) P μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (h_bracketing :
      ∀ epsilon, 0 < epsilon ->
        l1BracketingNumber P {cell : Cell | cell ∈ cells}
          classFun epsilon < ⊤)
    (hpopulation :
      ∀ cell, cell ∈ cells ->
        populationRiskOfFunction P (classFun cell) = cellLimit cell)
    (hempirical :
      ∀ ω sampleSize cell, cell ∈ cells ->
        empiricalAverage (samplePath X ω sampleSize) (classFun cell) =
          weightedSampleSum (sample ω sampleSize)
            (fun _unit => normalizer ω sampleSize)
            (scoreCellIndicator (score ω sampleSize) cell))
    (hcover :
      ∀ᵐ ω ∂μ,
        ∀ᶠ sampleSize in atTop,
          ∀ unit, unit ∈ sample ω sampleSize ->
            score ω sampleSize unit ∈ cells) :
    ∀ᵐ ω ∂μ,
      ((∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            weightedSampleSum (sample ω sampleSize)
              (fun _unit => normalizer ω sampleSize)
              (scoreCellIndicator (score ω sampleSize) cell))
          atTop (nhds (cellLimit cell))) ∧
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample ω sampleSize)
            (fun _unit => normalizer ω sampleSize) (fun _unit => (1 : Real)))
        atTop (nhds (∑ cell ∈ cells, cellLimit cell))) :=
  prospective_normalized_count_indicator_llns_ae_of_vdvw_outerAlmostSure
    cells classFun X sample score normalizer cellLimit
    (vdVW_theorem_2_4_1_outerAlmostSureGlivenkoCantelli
      X hLaw hindep h_bracketing)
    hpopulation hempirical hcover

/--
Finite `L1(P)` bracketing obligations supply the ordinary indicator LLNs
needed by the prospective normalized-count interface under constant weights.
-/
theorem prospective_normalized_count_indicator_llns_of_l1BracketingNumber
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (normalizer : ℕ -> Real)
    (cellLimit : Cell -> Real)
    (hcover :
      ∀ᶠ sampleSize in atTop,
        ∀ unit, unit ∈ sample sampleSize -> score sampleSize unit ∈ cells)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} cellLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            (fun _unit => normalizer sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize)
            (fun _unit => normalizer sampleSize)
            (scoreCellIndicator (score sampleSize) cell))
        atTop (nhds (cellLimit cell))) ∧
    Tendsto
      (fun sampleSize =>
        weightedSampleSum (sample sampleSize)
          (fun _unit => normalizer sampleSize) (fun _unit => (1 : Real)))
      atTop (nhds (∑ cell ∈ cells, cellLimit cell)) :=
  prospective_normalized_count_indicator_llns_of_glivenkoCantelli
    cells sample score normalizer cellLimit hcover
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells cellLimit sample (fun sampleSize _unit => normalizer sampleSize)
      score obligations)

/--
VdV&W endpoint assemblies supply the ordinary indicator LLNs needed by the
prospective normalized-count interface under constant weights.
-/
theorem prospective_normalized_count_indicator_llns_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (normalizer : ℕ -> Real)
    (cellLimit : Cell -> Real)
    (hcover :
      ∀ᶠ sampleSize in atTop,
        ∀ unit, unit ∈ sample sampleSize -> score sampleSize unit ∈ cells)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} cellLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            (fun _unit => normalizer sampleSize)
            (scoreCellIndicator (score sampleSize) cell))) :
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun sampleSize =>
          weightedSampleSum (sample sampleSize)
            (fun _unit => normalizer sampleSize)
            (scoreCellIndicator (score sampleSize) cell))
        atTop (nhds (cellLimit cell))) ∧
    Tendsto
      (fun sampleSize =>
        weightedSampleSum (sample sampleSize)
          (fun _unit => normalizer sampleSize) (fun _unit => (1 : Real)))
      atTop (nhds (∑ cell ∈ cells, cellLimit cell)) :=
  prospective_normalized_count_indicator_llns_of_glivenkoCantelli
    cells sample score normalizer cellLimit hcover
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells cellLimit sample (fun sampleSize _unit => normalizer sampleSize)
      score assembly)

/--
L1-bracketing obligations discharge the ordinary prospective normalized-count
ratio bridge under constant weights.  Only the nonzero denominator condition
and deterministic normalized-count-to-ratio map remain explicit.
-/
theorem cellwise_count_ratio_convergence_of_l1BracketingNumber_constant_weight
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (normalizer : ℕ -> Real)
    (cellLimit : Cell -> Real)
    (nonzeroTotalLimit cellwiseCountRatioConvergence : Prop)
    (hcover :
      ∀ᶠ sampleSize in atTop,
        ∀ unit, unit ∈ sample sampleSize -> score sampleSize unit ∈ cells)
    (normalized_to_ratio :
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            normalizer sampleSize *
              (((sample sampleSize).filter
                (fun unit => score sampleSize unit = cell)).card : Real))
          atTop (nhds (cellLimit cell))) ->
      Tendsto
        (fun sampleSize =>
          normalizer sampleSize * ((sample sampleSize).card : Real))
        atTop (nhds (∑ cell ∈ cells, cellLimit cell)) ->
      nonzeroTotalLimit ->
      cellwiseCountRatioConvergence)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} cellLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            (fun _unit => normalizer sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hnonzero : nonzeroTotalLimit) :
    cellwiseCountRatioConvergence := by
  have hlln :=
    prospective_normalized_count_indicator_llns_of_l1BracketingNumber
      cells sample score normalizer cellLimit hcover obligations
  exact
    cellwise_count_ratio_convergence_of_indicator_tendsto_constant_weight
      cells sample score normalizer cellLimit
      (∑ cell ∈ cells, cellLimit cell)
      nonzeroTotalLimit cellwiseCountRatioConvergence normalized_to_ratio
      hlln.1 hlln.2 hnonzero

/--
VdV&W endpoint assemblies discharge the ordinary prospective normalized-count
ratio bridge under constant weights.  Only the nonzero denominator condition
and deterministic normalized-count-to-ratio map remain explicit.
-/
theorem cellwise_count_ratio_convergence_of_vdvw241_endpoint_assembly_constant_weight
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (sample : ℕ -> Finset Unit)
    (score : ℕ -> Unit -> Cell)
    (normalizer : ℕ -> Real)
    (cellLimit : Cell -> Real)
    (nonzeroTotalLimit cellwiseCountRatioConvergence : Prop)
    (hcover :
      ∀ᶠ sampleSize in atTop,
        ∀ unit, unit ∈ sample sampleSize -> score sampleSize unit ∈ cells)
    (normalized_to_ratio :
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun sampleSize =>
            normalizer sampleSize *
              (((sample sampleSize).filter
                (fun unit => score sampleSize unit = cell)).card : Real))
          atTop (nhds (cellLimit cell))) ->
      Tendsto
        (fun sampleSize =>
          normalizer sampleSize * ((sample sampleSize).card : Real))
        atTop (nhds (∑ cell ∈ cells, cellLimit cell)) ->
      nonzeroTotalLimit ->
      cellwiseCountRatioConvergence)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} cellLimit
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize)
            (fun _unit => normalizer sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    (hnonzero : nonzeroTotalLimit) :
    cellwiseCountRatioConvergence := by
  have hlln :=
    prospective_normalized_count_indicator_llns_of_vdvw241_endpoint_assembly
      cells sample score normalizer cellLimit hcover assembly
  exact
    cellwise_count_ratio_convergence_of_indicator_tendsto_constant_weight
      cells sample score normalizer cellLimit
      (∑ cell ∈ cells, cellLimit cell)
      nonzeroTotalLimit cellwiseCountRatioConvergence normalized_to_ratio
      hlln.1 hlln.2 hnonzero

end WDSM
end Matching
end StatInference
