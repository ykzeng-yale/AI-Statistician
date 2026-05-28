import StatInference.Matching.WDSM.ProspectiveEstimatedScoreAudit
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScorePositiveVarianceStudentizedBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreComponentPositiveVarianceStudentizedBridge
import StatInference.Matching.WDSM.WaldStandardErrorPositivity

/-!
# Prospective PATE estimated-score positive-variance inference

This module upgrades the prospective PATE estimated-score studentization layer
from a nonzero standard-error premise to a positive limiting-variance premise.
Variance-estimator consistency remains explicit in
`EstimatedScorePositiveVarianceStudentizationInput`, and Wald coverage uses the
variance-based calibration inputs from `WaldStandardErrorPositivity`.
-/

namespace StatInference
namespace Matching
namespace WDSM

universe u v w x y z

open MeasureTheory
open Filter
open scoped Topology

/--
Prospective PATE estimated-score bridge plus positive-variance studentization
data.
-/
structure ProspectivePATEEstimatedScorePositiveVarianceBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  estimated_bridge : ProspectivePATEEstimatedScoreAuditBridge
  studentization_input :
    EstimatedScorePositiveVarianceStudentizationInput Index Sample
      LimitSample sampleLaw limitLaw l
  estimated_score_to_scaled_tendsto :
    estimated_bridge.estimated_score_asymptotic_normality ->
      TendstoInDistribution studentization_input.scaledStatistic l
        studentization_input.limit (fun _index => sampleLaw) limitLaw

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : Measure Sample} {limitLaw : Measure LimitSample}
variable [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
variable {l : Filter Index} [l.IsCountablyGenerated]

/--
Audited prospective PATE estimated-score studentized weak limit with
positivity stated at the limiting-variance level.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst : b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore : b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment : b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe : b.estimated_bridge.estimated_input.godambe_identity) :
    b.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  have hestimated_pair :=
    prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
      b.estimated_bridge
      hexact
      hbias_bound
      hgeometry_regular
      hcatchment
      hheterogeneity_moment
      hheterogeneity_variance
      hresidual_reg
      hquad
      hradius_regular
      hradius_geometry
      hfinite
      hden
      horthogonality
      hfirst hscore hfunctional hequicontinuity hadjustment hgodambe
  have hscaled :
      TendstoInDistribution b.studentization_input.scaledStatistic l
        b.studentization_input.limit (fun _index => sampleLaw) limitLaw :=
    b.estimated_score_to_scaled_tendsto hestimated_pair.1
  have hstudentized :=
    studentized_tendstoInDistribution_of_positiveVariance_input
      b.studentization_input hscaled
  exact ⟨hestimated_pair.1, hestimated_pair.2, hstudentized⟩

/--
Audited prospective PATE estimated-score positive-variance studentized weak
limit with the WDSM-specific local derivative, stochastic equicontinuity, and
Godambe obligations packaged as one compact core.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_core
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst : b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore : b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hadjustment : b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.estimated_bridge.estimated_input) :
    b.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  exact
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
Audited prospective PATE estimated-score studentized weak limit from
first-step Z-estimator component certificates, with positivity stated at the
limiting-variance level.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional :
      b.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment : b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe : b.estimated_bridge.estimated_input.godambe_identity) :
    b.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  have hestimated_pair :=
    prospective_pate_estimated_score_normality_and_variance_of_audited_z_components
      b.estimated_bridge firstStep propensity treated control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      hfunctional hequicontinuity hadjustment hgodambe
  have hscaled :
      TendstoInDistribution b.studentization_input.scaledStatistic l
        b.studentization_input.limit (fun _index => sampleLaw) limitLaw :=
    b.estimated_score_to_scaled_tendsto hestimated_pair.1
  have hstudentized :=
    studentized_tendstoInDistribution_of_positiveVariance_input
      b.studentization_input hscaled
  exact ⟨hestimated_pair.1, hestimated_pair.2, hstudentized⟩

/--
Audited prospective PATE estimated-score positive-variance studentized weak
limit from first-step Z-estimator component certificates, with the local
derivative, stochastic equicontinuity, and Godambe obligations packaged as one
compact core.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hadjustment : b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.estimated_bridge.estimated_input) :
    b.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  exact
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
Build the prospective PATE positive-variance bridge from changing-law
estimated-score variance components, using strict projection slack and
nonnegative target drift to prove positivity of the limiting variance.
-/
def prospectivePATEEstimatedScorePositiveVarianceBridge_of_projection_lt_limit
    (estimated_bridge : ProspectivePATEEstimatedScoreAuditBridge)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimated_score_to_scaled_tendsto :
      estimated_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
      LimitSample sampleLaw limitLaw l where
  estimated_bridge := estimated_bridge
  studentization_input :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
      projectionLimit targetDriftLimit horacle hprojection hdrift
      hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
  estimated_score_to_scaled_tendsto := estimated_score_to_scaled_tendsto

/--
Build the prospective PATE positive-variance bridge from changing-law
estimated-score variance components, using weak projection slack plus positive
target drift to prove positivity of the limiting variance.
-/
def
    prospectivePATEEstimatedScorePositiveVarianceBridge_of_projection_le_drift_pos_limit
    (estimated_bridge : ProspectivePATEEstimatedScoreAuditBridge)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimated_score_to_scaled_tendsto :
      estimated_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
      LimitSample sampleLaw limitLaw l where
  estimated_bridge := estimated_bridge
  studentization_input :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
      scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
      projectionLimit targetDriftLimit horacle hprojection hdrift
      hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
  estimated_score_to_scaled_tendsto := estimated_score_to_scaled_tendsto

/--
Build the prospective PATE positive-variance bridge from fixed-law
estimated-score variance components, using strict projection slack to prove
positivity of the limiting variance.
-/
def prospectivePATEEstimatedScorePositiveVarianceBridge_of_fixedLaw_projection_lt_limit
    (estimated_bridge : ProspectivePATEEstimatedScoreAuditBridge)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimated_score_to_scaled_tendsto :
      estimated_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
      LimitSample sampleLaw limitLaw l where
  estimated_bridge := estimated_bridge
  studentization_input :=
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      scaledStatistic oracle projectionReduction limit oracleLimit
      projectionLimit horacle hprojection hprojectionLimit_lt_oracle
      hinverse_meas
  estimated_score_to_scaled_tendsto := estimated_score_to_scaled_tendsto

/-- Prospective PATE positive-variance bridge plus absolute Wald data. -/
structure ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  positive_bridge :
    ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
      LimitSample sampleLaw limitLaw l
  coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l

/-- Prospective PATE positive-variance bridge plus two-sided Wald data. -/
structure ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  positive_bridge :
    ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
      LimitSample sampleLaw limitLaw l
  coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l

/--
Absolute variance-based Wald coverage for prospective PATE from audited
estimated-score positive-variance studentization.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
    (b :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
      b.positive_bridge
      hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity hadjustment hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Two-sided variance-based Wald coverage for prospective PATE from audited
estimated-score positive-variance studentization.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
    (b :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
      b.positive_bridge
      hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity hadjustment hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Absolute variance-based Wald coverage for prospective PATE from first-step
Z-estimator component certificates.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
      b.positive_bridge firstStep propensity treated control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      hfunctional hequicontinuity hadjustment hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Two-sided variance-based Wald coverage for prospective PATE from first-step
Z-estimator component certificates.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
      b.positive_bridge firstStep propensity treated control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      hfunctional hequicontinuity hadjustment hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Absolute Wald coverage for prospective PATE from audited estimated-score
positive-variance studentization, with the local derivative,
equicontinuity, and Godambe obligations packaged as one compact core.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_core
    (b :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  exact
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
Two-sided Wald coverage for prospective PATE from audited estimated-score
positive-variance studentization, with the local derivative,
equicontinuity, and Godambe obligations packaged as one compact core.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_core
    (b :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  exact
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
Absolute Wald coverage for prospective PATE from first-step Z-estimator
component certificates, with the local derivative, equicontinuity, and
Godambe obligations packaged as one compact core.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  exact
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
Two-sided Wald coverage for prospective PATE from first-step Z-estimator
component certificates, with the local derivative, equicontinuity, and
Godambe obligations packaged as one compact core.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hadjustment :
      b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.positive_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.positive_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.positive_bridge.studentization_input.limit limitSample *
              (standardError
                b.positive_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  exact
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

end WDSM
end Matching
end StatInference
