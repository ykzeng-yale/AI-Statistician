import Mathlib.Topology.MetricSpace.Pseudo.Lemmas
import Mathlib.Topology.Algebra.Order.Field
import StatInference.Matching.WDSM.ProspectiveResidualQuadraticVariationAudit

/-!
# Prospective residual quadratic-variation stabilization

This module proves the deterministic continuous-mapping step from arm-level
finite quadratic-variation convergence to the prospective PATE/PATT residual
quadratic-variation displays used in the appendix.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Treated Control : Type*} {l : Filter Index}

/--
Arm-level finite quadratic-variation convergence implies convergence of the
prospective PATE residual quadratic variation.
-/
theorem tendsto_prospectivePATEResidualQuadraticVariation_of_tendsto
    (treatedSet : Index -> Finset Treated)
    (controlSet : Index -> Finset Control)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlCoefficient controlVariance : Index -> Control -> Real)
    (denominator normalizer : Index -> Real)
    (treatedQVLimit controlQVLimit denominatorLimit normalizerLimit : Real)
    (htreatedQV :
      Tendsto
        (fun index =>
          quadraticVariation (treatedSet index) (treatedCoefficient index)
            (treatedVariance index))
        l (nhds treatedQVLimit))
    (hcontrolQV :
      Tendsto
        (fun index =>
          quadraticVariation (controlSet index) (controlCoefficient index)
            (controlVariance index))
        l (nhds controlQVLimit))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hnormalizer : Tendsto normalizer l (nhds normalizerLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        prospectivePATEResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((treatedQVLimit + controlQVLimit) / denominatorLimit ^ 2))) := by
  unfold prospectivePATEResidualQuadraticVariation twoArmResidualVariance
  exact hnormalizer.mul
    ((htreatedQV.add hcontrolQV).div (hdenominator.pow 2)
      (pow_ne_zero 2 hdenominatorLimit))

/--
Arm-level finite quadratic-variation convergence implies convergence of the
prospective PATT residual quadratic variation.
-/
theorem tendsto_prospectivePATTResidualQuadraticVariation_of_tendsto
    (treatedSet : Index -> Finset Treated)
    (controlSet : Index -> Finset Control)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlReuseCoefficient controlVariance : Index -> Control -> Real)
    (denominator normalizer : Index -> Real)
    (treatedQVLimit controlQVLimit denominatorLimit normalizerLimit : Real)
    (htreatedQV :
      Tendsto
        (fun index =>
          quadraticVariation (treatedSet index) (treatedCoefficient index)
            (treatedVariance index))
        l (nhds treatedQVLimit))
    (hcontrolQV :
      Tendsto
        (fun index =>
          quadraticVariation (controlSet index)
            (controlReuseCoefficient index) (controlVariance index))
        l (nhds controlQVLimit))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hnormalizer : Tendsto normalizer l (nhds normalizerLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        prospectivePATTResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlReuseCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((treatedQVLimit + controlQVLimit) / denominatorLimit ^ 2))) := by
  unfold prospectivePATTResidualQuadraticVariation pattResidualVariance
  exact hnormalizer.mul
    ((htreatedQV.add hcontrolQV).div (hdenominator.pow 2)
      (pow_ne_zero 2 hdenominatorLimit))

/--
Paired prospective PATE/PATT residual quadratic-variation stabilization from
arm-level finite quadratic-variation convergence.
-/
theorem tendsto_prospectivePATE_PATTResidualQuadraticVariation_of_tendsto
    (treatedSet : Index -> Finset Treated)
    (controlSet : Index -> Finset Control)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlCoefficient controlReuseCoefficient controlVariance :
      Index -> Control -> Real)
    (denominator normalizer : Index -> Real)
    (treatedQVLimit controlQVLimit denominatorLimit normalizerLimit : Real)
    (htreatedQV :
      Tendsto
        (fun index =>
          quadraticVariation (treatedSet index) (treatedCoefficient index)
            (treatedVariance index))
        l (nhds treatedQVLimit))
    (hcontrolQV_PATE :
      Tendsto
        (fun index =>
          quadraticVariation (controlSet index) (controlCoefficient index)
            (controlVariance index))
        l (nhds controlQVLimit))
    (hcontrolQV_PATT :
      Tendsto
        (fun index =>
          quadraticVariation (controlSet index)
            (controlReuseCoefficient index) (controlVariance index))
        l (nhds controlQVLimit))
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hnormalizer : Tendsto normalizer l (nhds normalizerLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        prospectivePATEResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((treatedQVLimit + controlQVLimit) / denominatorLimit ^ 2))) ∧
    Tendsto
      (fun index =>
        prospectivePATTResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlReuseCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((treatedQVLimit + controlQVLimit) / denominatorLimit ^ 2))) := by
  constructor
  · exact tendsto_prospectivePATEResidualQuadraticVariation_of_tendsto
      treatedSet controlSet treatedCoefficient treatedVariance
      controlCoefficient controlVariance denominator normalizer
      treatedQVLimit controlQVLimit denominatorLimit normalizerLimit
      htreatedQV hcontrolQV_PATE hdenominator hnormalizer hdenominatorLimit
  · exact tendsto_prospectivePATTResidualQuadraticVariation_of_tendsto
      treatedSet controlSet treatedCoefficient treatedVariance
      controlReuseCoefficient controlVariance denominator normalizer
      treatedQVLimit controlQVLimit denominatorLimit normalizerLimit
      htreatedQV hcontrolQV_PATT hdenominator hnormalizer hdenominatorLimit

end WDSM
end Matching
end StatInference
