import Mathlib.Probability.Process.FiniteDimensionalLaws

/-!
# Finite-dimensional process-law wrappers

This module records a content-based finite-dimensional distribution foundation
for stochastic processes.  The proof authority is mathlib's
`Probability.Process.FiniteDimensionalLaws` API, with source-crosswalk value for
textbook process-law statements.
-/

namespace StatInference
namespace ProbabilityMeasure

open MeasureTheory ProbabilityTheory

variable {T Ω : Type*} {𝓧 : T -> Type*} {mΩ : MeasurableSpace Ω}
  {m𝓧 : ∀ t, MeasurableSpace (𝓧 t)}
  {X Y : (t : T) -> Ω -> 𝓧 t} {P : Measure Ω}

/--
The finite-dimensional distributions of a stochastic process form a projective
measure family.
-/
theorem finiteDimensionalDistributions_projective
    (hX : ∀ t, AEMeasurable (X t) P) :
    IsProjectiveMeasureFamily
      (fun I => P.map (fun ω => I.restrict (fun t => X t ω))) := by
  exact ProbabilityTheory.isProjectiveMeasureFamily_map_restrict hX

/--
The full process law is the projective limit of its finite-dimensional
distributions.
-/
theorem processLaw_isProjectiveLimit
    (hX : AEMeasurable (fun ω => fun t => X t ω) P) :
    IsProjectiveLimit
      (P.map (fun ω => fun t => X t ω))
      (fun I => P.map (fun ω => I.restrict (fun t => X t ω))) := by
  exact ProbabilityTheory.isProjectiveLimit_map hX

/--
Two process laws are equal iff all finite-dimensional distributions are equal.

This is the probability-measure wrapper for the finite-dimensional-distribution
uniqueness principle used before broader process-space weak convergence.
-/
theorem processLaw_eq_iff_forall_finiteDimensional_eq [IsFiniteMeasure P]
    (hX : AEMeasurable (fun ω => fun t => X t ω) P)
    (hY : AEMeasurable (fun ω => fun t => Y t ω) P) :
    P.map (fun ω => fun t => X t ω) = P.map (fun ω => fun t => Y t ω) ↔
      ∀ I : Finset T,
        P.map (fun ω => I.restrict (fun t => X t ω)) =
          P.map (fun ω => I.restrict (fun t => Y t ω)) := by
  exact ProbabilityTheory.map_eq_iff_forall_finset_map_restrict_eq hX hY

/--
Two processes are identically distributed iff all finite-dimensional
restrictions are identically distributed.
-/
theorem identDistrib_iff_forall_finiteDimensional_identDistrib [IsFiniteMeasure P]
    (hX : AEMeasurable (fun ω => fun t => X t ω) P)
    (hY : AEMeasurable (fun ω => fun t => Y t ω) P) :
    IdentDistrib (fun ω => fun t => X t ω) (fun ω => fun t => Y t ω) P P ↔
      ∀ I : Finset T,
        IdentDistrib
          (fun ω => I.restrict (fun t => X t ω))
          (fun ω => I.restrict (fun t => Y t ω)) P P := by
  exact ProbabilityTheory.identDistrib_iff_forall_finset_identDistrib hX hY

/--
Pointwise almost-sure equality of process coordinates gives equality of every
finite-dimensional distribution.
-/
theorem finiteDimensional_eq_of_forall_ae_eq
    (h : ∀ t, X t =ᵐ[P] Y t) (I : Finset T) :
    P.map (fun ω => I.restrict (fun t => X t ω)) =
      P.map (fun ω => I.restrict (fun t => Y t ω)) := by
  exact ProbabilityTheory.map_restrict_eq_of_forall_ae_eq h I

/--
Pointwise almost-sure equality of process coordinates gives equality of full
process laws.
-/
theorem processLaw_eq_of_forall_ae_eq [IsFiniteMeasure P]
    (hX : AEMeasurable (fun ω => fun t => X t ω) P)
    (hY : AEMeasurable (fun ω => fun t => Y t ω) P)
    (h : ∀ t, X t =ᵐ[P] Y t) :
    P.map (fun ω => fun t => X t ω) = P.map (fun ω => fun t => Y t ω) := by
  exact ProbabilityTheory.map_eq_of_forall_ae_eq hX hY h

end ProbabilityMeasure
end StatInference
