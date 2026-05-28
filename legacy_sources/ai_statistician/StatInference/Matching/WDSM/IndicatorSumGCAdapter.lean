import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter
import StatInference.Matching.WDSM.IndicatorSumConvergenceConstructors

/-!
# GC adapters for double-score indicator-sum bridges

This module supplies the ordinary weighted-indicator LLN fields of the
PATE/PATT indicator-sum convergence bridges from finite score-cell
Glivenko-Cantelli, L1-bracketing, or VdV&W endpoint certificates.  Scaled
indicator-difference CLT/rate fields remain explicit assumptions elsewhere.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
GC certificates for the target, treated, and control PATE samples supply the
ordinary weighted-indicator LLN field of the concrete indicator-sum bridge.
-/
theorem pate_weighted_indicator_sum_lln_of_glivenkoCantelli
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
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcTreated :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).weighted_indicator_sum_lln := by
  exact
    ⟨tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells targetSample targetWeight
        (fun sampleSize =>
          pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcTarget,
      tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells treatedSample treatedWeight
        (fun sampleSize =>
          pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcTreated,
      tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells controlSample controlWeight
        (fun sampleSize =>
          pateDoubleScore (propensityScore sampleSize)
            (treatedPrognosticScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcControl,
      htotalLimit⟩

/--
L1-bracketing obligations for the target, treated, and control PATE samples
supply the ordinary weighted-indicator LLN field.
-/
theorem pate_weighted_indicator_sum_lln_of_l1BracketingNumber_obligations
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket]
    [Fintype ControlBracket]
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedObligations :
      L1BracketingNumberConstructorObligations (Bracket := TreatedBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).weighted_indicator_sum_lln :=
  pate_weighted_indicator_sum_lln_of_glivenkoCantelli
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetObligations.toGlivenkoCantelliClass
    treatedObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass htotalLimit

/--
VdV&W endpoint assemblies for the target, treated, and control PATE samples
supply the ordinary weighted-indicator LLN field.
-/
theorem pate_weighted_indicator_sum_lln_of_vdvw241_endpoint_assemblies
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket]
    [Fintype ControlBracket]
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TreatedBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).weighted_indicator_sum_lln :=
  pate_weighted_indicator_sum_lln_of_glivenkoCantelli
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetAssembly.toGlivenkoCantelliClass
    treatedAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass htotalLimit

/--
GC certificates for the target and control PATT samples supply the ordinary
weighted-indicator LLN field of the concrete PATT indicator-sum bridge.
-/
theorem patt_weighted_indicator_sum_lln_of_glivenkoCantelli
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
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).weighted_indicator_sum_lln := by
  exact
    ⟨tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells targetSample targetWeight
        (fun sampleSize =>
          pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcTarget,
      tendsto_weightedSampleSum_scoreCellIndicator_of_glivenkoCantelli
        cells controlSample controlWeight
        (fun sampleSize =>
          pattDoubleScore (propensityScore sampleSize)
            (controlPrognosticScore sampleSize))
        massLimit gcControl,
      htotalLimit⟩

/--
L1-bracketing obligations for the target and control PATT samples supply the
ordinary weighted-indicator LLN field.
-/
theorem patt_weighted_indicator_sum_lln_of_l1BracketingNumber_obligations
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).weighted_indicator_sum_lln :=
  patt_weighted_indicator_sum_lln_of_glivenkoCantelli
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass htotalLimit

/--
VdV&W endpoint assemblies for the target and control PATT samples supply the
ordinary weighted-indicator LLN field.
-/
theorem patt_weighted_indicator_sum_lln_of_vdvw241_endpoint_assemblies
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).weighted_indicator_sum_lln :=
  patt_weighted_indicator_sum_lln_of_glivenkoCantelli
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass htotalLimit

/--
GC certificates plus finite/envelope side conditions directly discharge the
ordinary PATE double-score approximation-negligibility conclusion.
-/
theorem pate_double_score_approximation_negligible_of_glivenkoCantelli
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
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcTreated :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT
        targetOutcomeC treatedOutcome controlOutcome propensityScore
        treatedPrognosticScore controlPrognosticScore treatedValue
        controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT
        targetOutcomeC treatedOutcome controlOutcome propensityScore
        treatedPrognosticScore controlPrognosticScore treatedValue
        controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
        controlEnvelopeLimit massLimit).envelope_convergence) :
    (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).pate_double_score_approximation_negligible :=
  pate_double_score_approximation_negligible_of_indicator_bridge
    (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit)
    hfinite henvelope
    (pate_weighted_indicator_sum_lln_of_glivenkoCantelli
      targetSample treatedSample controlSample cells targetWeight
      treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
      gcTarget gcTreated gcControl htotalLimit)

/--
Finite L1-bracketing obligations directly discharge the ordinary PATE
double-score approximation-negligibility conclusion.
-/
theorem pate_double_score_approximation_negligible_of_l1BracketingNumber_obligations
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket]
    [Fintype ControlBracket]
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedObligations :
      L1BracketingNumberConstructorObligations (Bracket := TreatedBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT
        targetOutcomeC treatedOutcome controlOutcome propensityScore
        treatedPrognosticScore controlPrognosticScore treatedValue
        controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT
        targetOutcomeC treatedOutcome controlOutcome propensityScore
        treatedPrognosticScore controlPrognosticScore treatedValue
        controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
        controlEnvelopeLimit massLimit).envelope_convergence) :
    (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).pate_double_score_approximation_negligible :=
  pate_double_score_approximation_negligible_of_glivenkoCantelli
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetObligations.toGlivenkoCantelliClass
    treatedObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass htotalLimit hfinite henvelope

/--
VdV&W endpoint assemblies directly discharge the ordinary PATE double-score
approximation-negligibility conclusion.
-/
theorem pate_double_score_approximation_negligible_of_vdvw241_endpoint_assemblies
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket]
    [Fintype ControlBracket]
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TreatedBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT
        targetOutcomeC treatedOutcome controlOutcome propensityScore
        treatedPrognosticScore controlPrognosticScore treatedValue
        controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT
        targetOutcomeC treatedOutcome controlOutcome propensityScore
        treatedPrognosticScore controlPrognosticScore treatedValue
        controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
        controlEnvelopeLimit massLimit).envelope_convergence) :
    (pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).pate_double_score_approximation_negligible :=
  pate_double_score_approximation_negligible_of_glivenkoCantelli
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetAssembly.toGlivenkoCantelliClass
    treatedAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass htotalLimit hfinite henvelope

/--
GC certificates plus finite/envelope side conditions directly discharge the
ordinary PATT double-score approximation-negligibility conclusion.
-/
theorem patt_double_score_approximation_negligible_of_glivenkoCantelli
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
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).envelope_convergence) :
    (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).patt_double_score_approximation_negligible :=
  patt_double_score_approximation_negligible_of_indicator_bridge
    (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit)
    hfinite henvelope
    (patt_weighted_indicator_sum_lln_of_glivenkoCantelli
      targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
      controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
      massLimit gcTarget gcControl htotalLimit)

/--
Finite L1-bracketing obligations directly discharge the ordinary PATT
double-score approximation-negligibility conclusion.
-/
theorem patt_double_score_approximation_negligible_of_l1BracketingNumber_obligations
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).envelope_convergence) :
    (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).patt_double_score_approximation_negligible :=
  patt_double_score_approximation_negligible_of_glivenkoCantelli
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass htotalLimit hfinite henvelope

/--
VdV&W endpoint assemblies directly discharge the ordinary PATT double-score
approximation-negligibility conclusion.
-/
theorem patt_double_score_approximation_negligible_of_vdvw241_endpoint_assemblies
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).envelope_convergence) :
    (pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).patt_double_score_approximation_negligible :=
  patt_double_score_approximation_negligible_of_glivenkoCantelli
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass htotalLimit hfinite henvelope

/--
GC certificates plus the scaled indicator-difference input directly discharge
the scaled PATE double-score approximation-negligibility conclusion.
-/
theorem scaled_pate_double_score_approximation_negligible_of_glivenkoCantelli
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
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcTreated :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).eventual_finite_conditions)
    (henvelope :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).envelope_convergence)
    (hscaledCLT :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).scaled_weighted_indicator_sum_difference_clt) :
    (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) scale targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).scaled_pate_double_score_approximation_negligible :=
  scaled_pate_double_score_approximation_negligible_of_indicator_bridge
    (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) scale targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit)
    hfinite henvelope
    (pate_weighted_indicator_sum_lln_of_glivenkoCantelli
      targetSample treatedSample controlSample cells targetWeight
      treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
      gcTarget gcTreated gcControl htotalLimit)
    hscaledCLT

/--
Finite L1-bracketing obligations plus the scaled indicator-difference input
directly discharge the scaled PATE approximation-negligibility conclusion.
-/
theorem scaled_pate_double_score_approximation_negligible_of_l1BracketingNumber_obligations
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket]
    [Fintype ControlBracket]
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedObligations :
      L1BracketingNumberConstructorObligations (Bracket := TreatedBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).eventual_finite_conditions)
    (henvelope :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).envelope_convergence)
    (hscaledCLT :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).scaled_weighted_indicator_sum_difference_clt) :
    (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) scale targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).scaled_pate_double_score_approximation_negligible :=
  scaled_pate_double_score_approximation_negligible_of_glivenkoCantelli
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetObligations.toGlivenkoCantelliClass
    treatedObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass htotalLimit hfinite henvelope
    hscaledCLT

/--
VdV&W endpoint assemblies plus the scaled indicator-difference input directly
discharge the scaled PATE approximation-negligibility conclusion.
-/
theorem scaled_pate_double_score_approximation_negligible_of_vdvw241_endpoint_assemblies
    {TargetBracket TreatedBracket ControlBracket : Type*}
    [Fintype TargetBracket] [Fintype TreatedBracket]
    [Fintype ControlBracket]
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (treatedAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := TreatedBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (treatedSample sampleSize)
            (treatedWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore sampleSize)
                (treatedPrognosticScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).eventual_finite_conditions)
    (henvelope :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).envelope_convergence)
    (hscaledCLT :
      (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
        (l := atTop) scale targetSample treatedSample controlSample cells
        targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        massLimit).scaled_weighted_indicator_sum_difference_clt) :
    (scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
      (l := atTop) scale targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      massLimit).scaled_pate_double_score_approximation_negligible :=
  scaled_pate_double_score_approximation_negligible_of_glivenkoCantelli
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    targetAssembly.toGlivenkoCantelliClass
    treatedAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass htotalLimit hfinite henvelope
    hscaledCLT

/--
GC certificates plus the scaled indicator-difference input directly discharge
the scaled PATT double-score approximation-negligibility conclusion.
-/
theorem scaled_patt_double_score_approximation_negligible_of_glivenkoCantelli
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
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (gcControl :
      GlivenkoCantelliClass {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).envelope_convergence)
    (hscaledCLT :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).scaled_weighted_indicator_sum_difference_clt) :
    (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) scale targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).scaled_patt_double_score_approximation_negligible :=
  scaled_patt_double_score_approximation_negligible_of_indicator_bridge
    (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) scale targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit)
    hfinite henvelope
    (patt_weighted_indicator_sum_lln_of_glivenkoCantelli
      targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
      controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
      massLimit gcTarget gcControl htotalLimit)
    hscaledCLT

/--
Finite L1-bracketing obligations plus the scaled indicator-difference input
directly discharge the scaled PATT approximation-negligibility conclusion.
-/
theorem scaled_patt_double_score_approximation_negligible_of_l1BracketingNumber_obligations
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlObligations :
      L1BracketingNumberConstructorObligations (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).envelope_convergence)
    (hscaledCLT :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).scaled_weighted_indicator_sum_difference_clt) :
    (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) scale targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).scaled_patt_double_score_approximation_negligible :=
  scaled_patt_double_score_approximation_negligible_of_glivenkoCantelli
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetObligations.toGlivenkoCantelliClass
    controlObligations.toGlivenkoCantelliClass htotalLimit hfinite henvelope
    hscaledCLT

/--
VdV&W endpoint assemblies plus the scaled indicator-difference input directly
discharge the scaled PATT approximation-negligibility conclusion.
-/
theorem scaled_patt_double_score_approximation_negligible_of_vdvw241_endpoint_assemblies
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
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (targetSample sampleSize)
            (targetWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (controlAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := ControlBracket)
        {cell : _ | cell ∈ cells} massLimit
        (fun sampleSize cell =>
          weightedSampleSum (controlSample sampleSize)
            (controlWeight sampleSize)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore sampleSize)
                (controlPrognosticScore sampleSize)) cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hfinite :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).eventual_finite_conditions)
    (henvelope :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).envelope_convergence)
    (hscaledCLT :
      (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
        (l := atTop) scale targetSample controlSample cells targetWeight
        controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit).scaled_weighted_indicator_sum_difference_clt) :
    (scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
      (l := atTop) scale targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit).scaled_patt_double_score_approximation_negligible :=
  scaled_patt_double_score_approximation_negligible_of_glivenkoCantelli
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit targetAssembly.toGlivenkoCantelliClass
    controlAssembly.toGlivenkoCantelliClass htotalLimit hfinite henvelope
    hscaledCLT

end WDSM
end Matching
end StatInference
