import StatInference.Matching.WDSM.RatioLinearization

/-!
# Multiplier bootstrap algebra for WDSM

The WDSM bootstrap linearization keeps the original matching structure and
reweights the already-linearized contributions by multiplier weights.  This
file proves the finite algebra that a replicated weighted sum equals the
original sum plus the multiplier perturbation.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Original finite linearized sum. -/
noncomputable def baseLinearizedSum (sample : Finset Unit)
    (contribution : Unit -> Real) : Real :=
  ∑ unit ∈ sample, contribution unit

/-- Replicated finite linearized sum under multiplier weights. -/
noncomputable def replicatedLinearizedSum (sample : Finset Unit)
    (multiplier contribution : Unit -> Real) : Real :=
  ∑ unit ∈ sample, multiplier unit * contribution unit

/-- Multiplier perturbation around the original finite sum. -/
noncomputable def multiplierPerturbation (sample : Finset Unit)
    (multiplier contribution : Unit -> Real) : Real :=
  ∑ unit ∈ sample, (multiplier unit - 1) * contribution unit

/-- Sum of squared centered bootstrap linear contributions. -/
noncomputable def centeredSquareSum (sample : Finset Unit)
    (contribution weight : Unit -> Real) (target : Real) : Real :=
  ∑ unit ∈ sample, (contribution unit - target * weight unit) ^ 2

/--
Finite bootstrap variance target after Hájek centering, with arbitrary real
denominator and sample-size normalizer.
-/
noncomputable def bootstrapCenteredVarianceTarget (sample : Finset Unit)
    (contribution weight : Unit -> Real) (target denominator normalizer : Real) :
    Real :=
  (1 / denominator ^ 2) * (1 / normalizer) *
    centeredSquareSum sample contribution weight target

/--
Replicated sum equals original sum plus the multiplier perturbation.  This is
the finite identity behind bootstrap linearizations using `(m_i^* - 1)`.
-/
theorem replicatedLinearizedSum_eq_base_add_multiplierPerturbation
    (sample : Finset Unit) (multiplier contribution : Unit -> Real) :
    replicatedLinearizedSum sample multiplier contribution =
      baseLinearizedSum sample contribution +
        multiplierPerturbation sample multiplier contribution := by
  unfold replicatedLinearizedSum baseLinearizedSum multiplierPerturbation
  calc
    (∑ unit ∈ sample, multiplier unit * contribution unit) =
        ∑ unit ∈ sample,
          (contribution unit + (multiplier unit - 1) * contribution unit) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by ring)
    _ =
        (∑ unit ∈ sample, contribution unit) +
          (∑ unit ∈ sample, (multiplier unit - 1) * contribution unit) := by
          rw [Finset.sum_add_distrib]

/-- The perturbation is the replicated sum minus the original sum. -/
theorem multiplierPerturbation_eq_replicated_sub_base
    (sample : Finset Unit) (multiplier contribution : Unit -> Real) :
    multiplierPerturbation sample multiplier contribution =
      replicatedLinearizedSum sample multiplier contribution -
        baseLinearizedSum sample contribution := by
  rw [replicatedLinearizedSum_eq_base_add_multiplierPerturbation]
  ring

/-- Unit multipliers produce zero perturbation. -/
theorem multiplierPerturbation_const_one_eq_zero
    (sample : Finset Unit) (contribution : Unit -> Real) :
    multiplierPerturbation sample (fun _unit => (1 : Real)) contribution = 0 := by
  unfold multiplierPerturbation
  exact Finset.sum_eq_zero
    (fun unit _hunit => by ring)

/--
Centering a bootstrap contribution by `target * weight` is the same as
subtracting `target` times the denominator perturbation from the numerator
perturbation.
-/
theorem multiplierPerturbation_centered_eq_sub
    (sample : Finset Unit) (multiplier contribution weight : Unit -> Real)
    (target : Real) :
    multiplierPerturbation sample multiplier
        (fun unit => contribution unit - target * weight unit) =
      multiplierPerturbation sample multiplier contribution -
        target * multiplierPerturbation sample multiplier weight := by
  unfold multiplierPerturbation
  calc
    (∑ unit ∈ sample,
        (multiplier unit - 1) *
          (contribution unit - target * weight unit)) =
        ∑ unit ∈ sample,
          ((multiplier unit - 1) * contribution unit -
            target * ((multiplier unit - 1) * weight unit)) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by ring)
    _ =
        (∑ unit ∈ sample, (multiplier unit - 1) * contribution unit) -
          ∑ unit ∈ sample,
            target * ((multiplier unit - 1) * weight unit) := by
          rw [Finset.sum_sub_distrib]
    _ =
        (∑ unit ∈ sample, (multiplier unit - 1) * contribution unit) -
          target *
            ∑ unit ∈ sample, (multiplier unit - 1) * weight unit := by
          rw [Finset.mul_sum]

/--
Exact replicated Hájek-ratio perturbation in numerator/denominator multiplier
perturbation form.
-/
theorem replicatedRatio_sub_baseRatio_eq
    (sample : Finset Unit) (multiplier contribution weight : Unit -> Real)
    (hden : baseLinearizedSum sample weight ≠ 0)
    (hrep_den : replicatedLinearizedSum sample multiplier weight ≠ 0) :
    replicatedLinearizedSum sample multiplier contribution /
        replicatedLinearizedSum sample multiplier weight -
        baseLinearizedSum sample contribution / baseLinearizedSum sample weight =
      (baseLinearizedSum sample weight *
          multiplierPerturbation sample multiplier contribution -
        baseLinearizedSum sample contribution *
          multiplierPerturbation sample multiplier weight) /
        (baseLinearizedSum sample weight *
          replicatedLinearizedSum sample multiplier weight) := by
  have hnum :=
    replicatedLinearizedSum_eq_base_add_multiplierPerturbation
      sample multiplier contribution
  have hden_rep_eq :=
    replicatedLinearizedSum_eq_base_add_multiplierPerturbation
      sample multiplier weight
  have hden_perturbed :
      baseLinearizedSum sample weight +
          multiplierPerturbation sample multiplier weight ≠ 0 := by
    rw [← hden_rep_eq]
    exact hrep_den
  have hratio :=
    ratio_sub_ratio_eq
      (baseLinearizedSum sample contribution)
      (baseLinearizedSum sample weight)
      (multiplierPerturbation sample multiplier contribution)
      (multiplierPerturbation sample multiplier weight)
      hden hden_perturbed
  rw [← hnum, ← hden_rep_eq] at hratio
  exact hratio

/--
Exact bootstrap Hájek-centering rewrite.  If the base ratio equals `target`,
then the replicated ratio minus `target` is the replicated denominator inverse
times the centered multiplier perturbation with contribution
`contribution - target * weight`.
-/
theorem replicatedRatio_sub_target_eq_centeredPerturbation_div
    (sample : Finset Unit) (multiplier contribution weight : Unit -> Real)
    (target : Real)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight)
    (hrep_den : replicatedLinearizedSum sample multiplier weight ≠ 0) :
    replicatedLinearizedSum sample multiplier contribution /
        replicatedLinearizedSum sample multiplier weight - target =
      multiplierPerturbation sample multiplier
        (fun unit => contribution unit - target * weight unit) /
        replicatedLinearizedSum sample multiplier weight := by
  have hnum :=
    replicatedLinearizedSum_eq_base_add_multiplierPerturbation
      sample multiplier contribution
  have hden_rep_eq :=
    replicatedLinearizedSum_eq_base_add_multiplierPerturbation
      sample multiplier weight
  have hden_perturbed :
      baseLinearizedSum sample weight +
          multiplierPerturbation sample multiplier weight ≠ 0 := by
    rw [← hden_rep_eq]
    exact hrep_den
  have hratio :=
    ratio_sub_ratio_eq_with_base_ratio
      target (baseLinearizedSum sample weight)
      (multiplierPerturbation sample multiplier contribution)
      (multiplierPerturbation sample multiplier weight)
      hden_perturbed
  have hrep_num_eq :
      replicatedLinearizedSum sample multiplier contribution =
        target * baseLinearizedSum sample weight +
          multiplierPerturbation sample multiplier contribution := by
    rw [hnum, hbase]
  have hcentered :=
    multiplierPerturbation_centered_eq_sub
      sample multiplier contribution weight target
  rw [← hden_rep_eq, ← hrep_num_eq, ← hcentered] at hratio
  exact hratio

/--
Expanded finite-sum form of the centered-square bootstrap variance target's
numerator.
-/
theorem centeredSquareSum_eq_expanded
    (sample : Finset Unit) (contribution weight : Unit -> Real)
    (target : Real) :
    centeredSquareSum sample contribution weight target =
      (∑ unit ∈ sample, contribution unit ^ 2) -
        2 * target * (∑ unit ∈ sample, contribution unit * weight unit) +
          target ^ 2 * (∑ unit ∈ sample, weight unit ^ 2) := by
  unfold centeredSquareSum
  calc
    (∑ unit ∈ sample, (contribution unit - target * weight unit) ^ 2) =
        ∑ unit ∈ sample,
          (contribution unit ^ 2 -
            2 * target * (contribution unit * weight unit) +
              target ^ 2 * weight unit ^ 2) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by ring)
    _ =
        (∑ unit ∈ sample, contribution unit ^ 2) -
          (∑ unit ∈ sample,
            2 * target * (contribution unit * weight unit)) +
          (∑ unit ∈ sample, target ^ 2 * weight unit ^ 2) := by
          rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
    _ =
        (∑ unit ∈ sample, contribution unit ^ 2) -
          2 * target * (∑ unit ∈ sample, contribution unit * weight unit) +
          target ^ 2 * (∑ unit ∈ sample, weight unit ^ 2) := by
          rw [← Finset.mul_sum, ← Finset.mul_sum]

/--
Expanded form of the normalized centered-square bootstrap variance target.
-/
theorem bootstrapCenteredVarianceTarget_eq_expanded
    (sample : Finset Unit) (contribution weight : Unit -> Real)
    (target denominator normalizer : Real) :
    bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer =
      (1 / denominator ^ 2) * (1 / normalizer) *
        ((∑ unit ∈ sample, contribution unit ^ 2) -
          2 * target * (∑ unit ∈ sample, contribution unit * weight unit) +
            target ^ 2 * (∑ unit ∈ sample, weight unit ^ 2)) := by
  unfold bootstrapCenteredVarianceTarget
  rw [centeredSquareSum_eq_expanded]

end WDSM
end Matching
end StatInference
