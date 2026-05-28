import StatInference.EmpiricalProcess.EndpointStrongLaw
import StatInference.Matching.WDSM.FiniteCellIndicatorLLNInterfaces
import StatInference.Matching.WDSM.FiniteCellIndicatorMass

/-!
# Finite score-cell indicator LLNs from cell-mass convergence

This module makes the finite score-cell LLN interface more concrete.  The
bridge in `FiniteCellIndicatorLLNInterfaces` records the LLN as a proposition;
here we identify that proposition with actual `Tendsto` statements for
weighted score-cell indicator sums, equivalently weighted score-cell masses.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators Topology

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Concrete cellwise LLN for weighted score-cell indicator sums over a fixed
finite partition.
-/
def cellwiseWeightedIndicatorSumLLN
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real) : Prop :=
  ∀ cell, cell ∈ cells ->
    Tendsto
      (fun index =>
        weightedSampleSum (sample index) (weight index)
          (scoreCellIndicator (score index) cell))
      l (nhds (massLimit cell))

/--
Concrete cellwise LLN for weighted score-cell masses over a fixed finite
partition.
-/
def cellwiseScoreCellMassLLN
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real) : Prop :=
  ∀ cell, cell ∈ cells ->
    Tendsto
      (fun index =>
        scoreCellMass (sample index) (weight index) (score index) cell)
      l (nhds (massLimit cell))

/-- Cell-indicator LLNs imply the equivalent score-cell mass LLNs. -/
theorem cellwiseScoreCellMassLLN_of_indicator
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (hindicator :
      cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit) :
    cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit := by
  intro cell hcell
  exact tendsto_scoreCellMass_of_tendsto_weightedSampleSum_indicator
    sample weight score cell (massLimit cell) (hindicator cell hcell)

/-- Score-cell mass LLNs imply the equivalent cell-indicator sum LLNs. -/
theorem cellwiseWeightedIndicatorSumLLN_of_mass
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit := by
  intro cell hcell
  convert hmass cell hcell using 1
  ext index
  exact (scoreCellMass_eq_weightedSampleSum_scoreCellIndicator
    (sample index) (weight index) (score index) cell).symm

/--
Cell-indicator sum LLNs and score-cell mass LLNs are equivalent over a fixed
finite partition.
-/
theorem cellwiseWeightedIndicatorSumLLN_iff_scoreCellMassLLN
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit ↔
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit := by
  constructor
  · exact
      cellwiseScoreCellMassLLN_of_indicator cells sample weight score
        massLimit
  · exact
      cellwiseWeightedIndicatorSumLLN_of_mass cells sample weight score
        massLimit

/--
Finite endpoint strong laws give pathwise weighted score-cell indicator LLNs
and the equivalent score-cell mass LLNs.

This is an iid endpoint-level reducer: the stochastic assumptions are
integrability, pairwise independence, identical distribution, population
mean identification, and the pathwise equality between endpoint empirical
averages and the WDSM weighted score-cell indicator sums.
-/
theorem cellwise_weighted_indicator_sum_and_mass_lln_ae_of_finite_endpoint_strong_law
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (X : {cell : Cell // cell ∈ cells} -> ℕ -> Ω -> Real)
    (sample : Ω -> ℕ -> Finset Unit)
    (weight : Ω -> ℕ -> Unit -> Real)
    (score : Ω -> ℕ -> Unit -> Cell)
    (hint : ∀ endpoint, Integrable (X endpoint 0) μ)
    (hindep :
      ∀ endpoint,
        Pairwise (Function.onFun (fun x1 x2 => x1 ⟂ᵢ[μ] x2)
          (X endpoint)))
    (hident :
      ∀ endpoint i, IdentDistrib (X endpoint i) (X endpoint 0) μ μ)
    (hpopulation :
      ∀ cell hcell, ∫ ω, X ⟨cell, hcell⟩ 0 ω ∂μ =
        referenceShare cell)
    (hempirical :
      ∀ ω sampleSize cell hcell,
        weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
            (scoreCellIndicator (score ω sampleSize) cell) =
          (∑ i ∈ Finset.range sampleSize,
            X ⟨cell, hcell⟩ i ω) / sampleSize) :
    ∀ᵐ ω ∂μ,
      cellwiseWeightedIndicatorSumLLN (l := atTop) cells (sample ω)
          (weight ω) (score ω) referenceShare ∧
        cellwiseScoreCellMassLLN (l := atTop) cells (sample ω)
          (weight ω) (score ω) referenceShare := by
  have hstrong :
      ∀ᵐ ω ∂μ, ∀ endpoint : {cell : Cell // cell ∈ cells},
        Tendsto
          (fun n : ℕ =>
            (∑ i ∈ Finset.range n, X endpoint i ω) / n -
              ∫ x, X endpoint 0 x ∂μ)
          atTop (𝓝 0) :=
    finite_endpoint_strong_law_ae_real X hint hindep hident
  filter_upwards [hstrong] with ω hω
  have hindicator :
      cellwiseWeightedIndicatorSumLLN (l := atTop) cells (sample ω)
        (weight ω) (score ω) referenceShare := by
    intro cell hcell
    let endpoint : {cell : Cell // cell ∈ cells} := ⟨cell, hcell⟩
    have hdiff :
        Tendsto
          (fun n : ℕ =>
            (∑ i ∈ Finset.range n, X endpoint i ω) / n -
              ∫ x, X endpoint 0 x ∂μ)
          atTop (𝓝 0) :=
      hω endpoint
    have hquotIntegral :
        Tendsto
          (fun n : ℕ =>
            (∑ i ∈ Finset.range n, X endpoint i ω) / n)
          atTop (𝓝 (∫ x, X endpoint 0 x ∂μ)) := by
      have hconst :
          Tendsto
            (fun _n : ℕ => ∫ x, X endpoint 0 x ∂μ)
            atTop (𝓝 (∫ x, X endpoint 0 x ∂μ)) :=
        tendsto_const_nhds
      simpa [sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using
        hdiff.add hconst
    have hquotReference :
        Tendsto
          (fun n : ℕ =>
            (∑ i ∈ Finset.range n, X endpoint i ω) / n)
          atTop (𝓝 (referenceShare cell)) := by
      simpa [endpoint, hpopulation cell hcell] using hquotIntegral
    have heq :
        (fun sampleSize =>
          weightedSampleSum (sample ω sampleSize) (weight ω sampleSize)
            (scoreCellIndicator (score ω sampleSize) cell)) =ᶠ[atTop]
        (fun sampleSize =>
          (∑ i ∈ Finset.range sampleSize,
            X endpoint i ω) / sampleSize) :=
      Eventually.of_forall fun sampleSize =>
        hempirical ω sampleSize cell hcell
    exact hquotReference.congr' heq.symm
  exact
    ⟨hindicator,
      cellwiseScoreCellMassLLN_of_indicator cells (sample ω) (weight ω)
        (score ω) referenceShare hindicator⟩

/--
Build the generic finite score-cell indicator LLN bridge when the array-LLN
assumption directly supplies concrete weighted indicator-sum convergence.
-/
def finiteScoreCellIndicatorLLNBridgeOfIndicatorConvergence
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      weightedIndicatorArrayLLN : Prop)
    (array_lln_to_indicator :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      weightedIndicatorArrayLLN ->
        cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
          massLimit) :
    FiniteScoreCellIndicatorLLNBridge Cell where
  cells := cells
  referenceShare := massLimit
  survey_design_regularity := surveyDesignRegularity
  bounded_score_cell_indicators := boundedScoreCellIndicators
  weighted_indicator_array_lln := weightedIndicatorArrayLLN
  cellwise_weighted_indicator_sum_lln :=
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit
  bridge := array_lln_to_indicator

/--
Build the generic finite score-cell indicator LLN bridge when the array-LLN
assumption supplies score-cell mass convergence.
-/
def finiteScoreCellIndicatorLLNBridgeOfMassConvergence
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      weightedIndicatorArrayLLN : Prop)
    (array_lln_to_mass :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      weightedIndicatorArrayLLN ->
        cellwiseScoreCellMassLLN (l := l) cells sample weight score
          massLimit) :
    FiniteScoreCellIndicatorLLNBridge Cell where
  cells := cells
  referenceShare := massLimit
  survey_design_regularity := surveyDesignRegularity
  bounded_score_cell_indicators := boundedScoreCellIndicators
  weighted_indicator_array_lln := weightedIndicatorArrayLLN
  cellwise_weighted_indicator_sum_lln :=
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit
  bridge := by
    intro hdesign hbounded harray
    exact cellwiseWeightedIndicatorSumLLN_of_mass cells sample weight score
      massLimit (array_lln_to_mass hdesign hbounded harray)

/--
Applying the bridge built from cell-mass convergence gives the concrete
weighted indicator-sum LLN.
-/
theorem finite_score_cell_indicator_lln_of_cell_mass_convergence
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      weightedIndicatorArrayLLN : Prop)
    (array_lln_to_mass :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      weightedIndicatorArrayLLN ->
        cellwiseScoreCellMassLLN (l := l) cells sample weight score
          massLimit)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (harray : weightedIndicatorArrayLLN) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit :=
  finite_score_cell_indicator_lln_of_bridge
    (finiteScoreCellIndicatorLLNBridgeOfMassConvergence cells sample weight
      score massLimit surveyDesignRegularity boundedScoreCellIndicators
      weightedIndicatorArrayLLN array_lln_to_mass)
    hdesign hbounded harray

/--
Applying the bridge built from concrete indicator convergence gives the
weighted indicator-sum LLN.
-/
theorem finite_score_cell_indicator_lln_of_indicator_convergence
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      weightedIndicatorArrayLLN : Prop)
    (array_lln_to_indicator :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      weightedIndicatorArrayLLN ->
        cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
          massLimit)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (harray : weightedIndicatorArrayLLN) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit :=
  finite_score_cell_indicator_lln_of_bridge
    (finiteScoreCellIndicatorLLNBridgeOfIndicatorConvergence cells sample
      weight score massLimit surveyDesignRegularity
      boundedScoreCellIndicators weightedIndicatorArrayLLN
      array_lln_to_indicator)
    hdesign hbounded harray

/--
Concrete indicator convergence also yields the equivalent score-cell mass LLN.
-/
theorem finite_score_cell_indicator_and_mass_lln_of_indicator_convergence
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      weightedIndicatorArrayLLN : Prop)
    (array_lln_to_indicator :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      weightedIndicatorArrayLLN ->
        cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
          massLimit)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (harray : weightedIndicatorArrayLLN) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit ∧
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit := by
  have hindicator :
      cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit :=
    finite_score_cell_indicator_lln_of_indicator_convergence
      cells sample weight score massLimit surveyDesignRegularity
      boundedScoreCellIndicators weightedIndicatorArrayLLN
      array_lln_to_indicator hdesign hbounded harray
  exact
    ⟨hindicator,
      cellwiseScoreCellMassLLN_of_indicator cells sample weight score
        massLimit hindicator⟩

/--
Concrete score-cell mass convergence yields both the indicator-sum and mass
LLNs needed by downstream finite-cell interfaces.
-/
theorem finite_score_cell_indicator_and_mass_lln_of_cell_mass_convergence
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (surveyDesignRegularity boundedScoreCellIndicators
      weightedIndicatorArrayLLN : Prop)
    (array_lln_to_mass :
      surveyDesignRegularity ->
      boundedScoreCellIndicators ->
      weightedIndicatorArrayLLN ->
        cellwiseScoreCellMassLLN (l := l) cells sample weight score
          massLimit)
    (hdesign : surveyDesignRegularity)
    (hbounded : boundedScoreCellIndicators)
    (harray : weightedIndicatorArrayLLN) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
        massLimit ∧
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit := by
  have hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit :=
    array_lln_to_mass hdesign hbounded harray
  exact
    ⟨cellwiseWeightedIndicatorSumLLN_of_mass cells sample weight score
        massLimit hmass,
      hmass⟩

end WDSM
end Matching
end StatInference
