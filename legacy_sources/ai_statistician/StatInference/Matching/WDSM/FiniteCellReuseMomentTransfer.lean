import StatInference.Matching.WDSM.FiniteCellGeometryMomentBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorLLNFromMass

/-!
# Finite-cell reuse-moment transfer

This module isolates the remaining finite-cell step in the Chen-Han geometry
route.  Once weighted score-cell masses converge, a separate nearest-neighbor
geometry theorem still has to transfer those limits to exact weighted
reuse-moment limits.  The bridge below names that obligation and composes it
with the existing weighted geometry interface.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Concrete bridge from finite weighted score-cell mass convergence to exact
weighted reuse-moment limits and the corresponding limiting variance formula.

The field `cell_mass_to_reuse_moments` is the remaining stochastic-geometry
input: in a full proof it should be supplied by a nearest-neighbor/Palm
catchment theorem, not assumed inside the variance algebra.
-/
structure FiniteCellReuseMomentTransferBridge
    (Index Unit Cell : Type*) [DecidableEq Cell] (l : Filter Index) where
  cells : Finset Cell
  sample : Index -> Finset Unit
  weight : Index -> Unit -> Real
  score : Index -> Unit -> Cell
  massLimit : Cell -> Real
  score_space_regularity : Prop
  chen_han_catchment_input : Prop
  survey_design_regularity : Prop
  bounded_score_cell_indicators : Prop
  weighted_indicator_array_lln : Prop
  exact_weighted_reuse_moment_limits : Prop
  limiting_variance_formula : Prop
  regularity_to_design :
    score_space_regularity -> survey_design_regularity
  catchment_to_bounded :
    chen_han_catchment_input -> bounded_score_cell_indicators
  catchment_to_array_lln :
    chen_han_catchment_input -> weighted_indicator_array_lln
  array_lln_to_mass :
    survey_design_regularity ->
    bounded_score_cell_indicators ->
    weighted_indicator_array_lln ->
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit
  cell_mass_to_reuse_moments :
    cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit ->
      exact_weighted_reuse_moment_limits
  reuse_moments_to_variance :
    exact_weighted_reuse_moment_limits -> limiting_variance_formula

/--
The finite-cell reuse-transfer bridge supplies the concrete finite score-cell
LLN interface by using weighted score-cell mass convergence.
-/
def finiteScoreCellIndicatorLLNBridgeOfReuseMomentTransfer
    (b : FiniteCellReuseMomentTransferBridge Index Unit Cell l) :
    FiniteScoreCellIndicatorLLNBridge Cell :=
  finiteScoreCellIndicatorLLNBridgeOfMassConvergence b.cells b.sample
    b.weight b.score b.massLimit b.survey_design_regularity
    b.bounded_score_cell_indicators b.weighted_indicator_array_lln
    b.array_lln_to_mass

/--
The finite-cell reuse-transfer bridge supplies the generic weighted geometry
moment bridge used by the Chen-Han audit layer.
-/
def weightedGeometryMomentBridgeOfFiniteCellReuseMomentTransfer
    (b : FiniteCellReuseMomentTransferBridge Index Unit Cell l) :
    WeightedGeometryMomentBridge :=
  weightedGeometryMomentBridgeOfFiniteCellIndicatorLLN
    (finiteScoreCellIndicatorLLNBridgeOfReuseMomentTransfer b)
    b.score_space_regularity b.chen_han_catchment_input
    b.exact_weighted_reuse_moment_limits
    b.regularity_to_design
    b.catchment_to_bounded
    b.catchment_to_array_lln
    (by
      intro hindicator
      exact b.cell_mass_to_reuse_moments
        (cellwiseScoreCellMassLLN_of_indicator b.cells b.sample b.weight
          b.score b.massLimit hindicator))

/--
Under the bridge's regularity and catchment inputs, the concrete score-cell
mass convergence follows.
-/
theorem cell_mass_convergence_of_finite_cell_reuse_moment_transfer
    (b : FiniteCellReuseMomentTransferBridge Index Unit Cell l)
    (hregular : b.score_space_regularity)
    (hcatchment : b.chen_han_catchment_input) :
    cellwiseScoreCellMassLLN (l := l) b.cells b.sample b.weight b.score
      b.massLimit := by
  exact b.array_lln_to_mass
    (b.regularity_to_design hregular)
    (b.catchment_to_bounded hcatchment)
    (b.catchment_to_array_lln hcatchment)

/--
Score-cell mass convergence transfers to exact weighted reuse-moment limits
through the named finite-cell reuse theorem.
-/
theorem exact_weighted_reuse_moments_of_cell_mass_convergence
    (b : FiniteCellReuseMomentTransferBridge Index Unit Cell l)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) b.cells b.sample b.weight b.score
        b.massLimit) :
    b.exact_weighted_reuse_moment_limits :=
  b.cell_mass_to_reuse_moments hmass

/--
Regularity and catchment inputs imply exact weighted reuse-moment limits
through concrete score-cell mass convergence.
-/
theorem finite_cell_reuse_moments_of_mass_convergence_bridge
    (b : FiniteCellReuseMomentTransferBridge Index Unit Cell l)
    (hregular : b.score_space_regularity)
    (hcatchment : b.chen_han_catchment_input) :
    b.exact_weighted_reuse_moment_limits := by
  exact exact_weighted_reuse_moments_of_geometry
    (weightedGeometryMomentBridgeOfFiniteCellReuseMomentTransfer b)
    hregular hcatchment

/--
The finite-cell reuse-transfer bridge yields the Chen-Han-named reuse moment
and limiting-variance conclusions.
-/
theorem chen_han_reuse_and_variance_of_finite_cell_reuse_transfer
    (b : FiniteCellReuseMomentTransferBridge Index Unit Cell l)
    (hregular : b.score_space_regularity)
    (hcatchment : b.chen_han_catchment_input) :
    b.exact_weighted_reuse_moment_limits ∧ b.limiting_variance_formula := by
  exact chen_han_reuse_and_limiting_variance_of_weighted_geometry_bridge
    (weightedGeometryMomentBridgeOfFiniteCellReuseMomentTransfer b)
    b.limiting_variance_formula
    b.reuse_moments_to_variance
    hregular hcatchment

/--
Paired score-cell mass convergence from two finite-cell reuse-transfer
bridges.  This is the PATE/PATT shape of the finite-cell side of the
Chen-Han route.
-/
theorem paired_cell_mass_convergence_of_finite_cell_reuse_moment_transfer
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (left : FiniteCellReuseMomentTransferBridge Index Unit LeftCell l)
    (right : FiniteCellReuseMomentTransferBridge Index Unit RightCell l)
    (hleft_regular : left.score_space_regularity)
    (hleft_catchment : left.chen_han_catchment_input)
    (hright_regular : right.score_space_regularity)
    (hright_catchment : right.chen_han_catchment_input) :
    cellwiseScoreCellMassLLN (l := l) left.cells left.sample left.weight
        left.score left.massLimit ∧
      cellwiseScoreCellMassLLN (l := l) right.cells right.sample
        right.weight right.score right.massLimit :=
  ⟨cell_mass_convergence_of_finite_cell_reuse_moment_transfer
      left hleft_regular hleft_catchment,
    cell_mass_convergence_of_finite_cell_reuse_moment_transfer
      right hright_regular hright_catchment⟩

/--
Paired exact weighted reuse-moment limits from two finite-cell reuse-transfer
bridges.
-/
theorem paired_finite_cell_reuse_moments_of_mass_convergence_bridge
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (left : FiniteCellReuseMomentTransferBridge Index Unit LeftCell l)
    (right : FiniteCellReuseMomentTransferBridge Index Unit RightCell l)
    (hleft_regular : left.score_space_regularity)
    (hleft_catchment : left.chen_han_catchment_input)
    (hright_regular : right.score_space_regularity)
    (hright_catchment : right.chen_han_catchment_input) :
    left.exact_weighted_reuse_moment_limits ∧
      right.exact_weighted_reuse_moment_limits :=
  ⟨finite_cell_reuse_moments_of_mass_convergence_bridge
      left hleft_regular hleft_catchment,
    finite_cell_reuse_moments_of_mass_convergence_bridge
      right hright_regular hright_catchment⟩

/--
Paired Chen-Han reuse-moment and limiting-variance conclusions from two
finite-cell reuse-transfer bridges.
-/
theorem paired_chen_han_reuse_and_variance_of_finite_cell_reuse_transfer
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (left : FiniteCellReuseMomentTransferBridge Index Unit LeftCell l)
    (right : FiniteCellReuseMomentTransferBridge Index Unit RightCell l)
    (hleft_regular : left.score_space_regularity)
    (hleft_catchment : left.chen_han_catchment_input)
    (hright_regular : right.score_space_regularity)
    (hright_catchment : right.chen_han_catchment_input) :
    left.exact_weighted_reuse_moment_limits ∧
      left.limiting_variance_formula ∧
      right.exact_weighted_reuse_moment_limits ∧
      right.limiting_variance_formula := by
  have hleft :
      left.exact_weighted_reuse_moment_limits ∧
        left.limiting_variance_formula :=
    chen_han_reuse_and_variance_of_finite_cell_reuse_transfer
      left hleft_regular hleft_catchment
  have hright :
      right.exact_weighted_reuse_moment_limits ∧
        right.limiting_variance_formula :=
    chen_han_reuse_and_variance_of_finite_cell_reuse_transfer
      right hright_regular hright_catchment
  exact ⟨hleft.1, hleft.2, hright.1, hright.2⟩

end WDSM
end Matching
end StatInference
