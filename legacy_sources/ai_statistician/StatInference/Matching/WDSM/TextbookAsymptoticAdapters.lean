import StatInference.Matching.WDSM.SlutskyAlgebra

/-!
# Textbook asymptotic adapters for WDSM

The external empirical-process/textbook formalization uses the same
`StatInference` root namespace, so it cannot be imported as a Lake dependency
without a module-name conflict.  This file ports the small vdV-style adapters
that WDSM repeatedly needs: deterministic uniform bounds imply `o_P(1)`, and
asymptotically equivalent statistics have the same weak limit.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample LimitSample E : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable {l : Filter Index}

/--
vdV-style stochastic little-o adapter: if a random sequence is uniformly
bounded by a deterministic real sequence converging to zero, then it converges
to zero in measure.
-/
theorem tendstoInMeasure_zero_of_eventually_uniform_norm_bound
    [SeminormedAddCommGroup E]
    (random : Index -> Sample -> E)
    (bound : Index -> Real)
    (hbound_zero : Tendsto bound l (nhds 0))
    (hbound_eventual :
      ∀ᶠ index in l, ∀ sample, ‖random index sample‖ ≤ bound index) :
    TendstoInMeasure sampleLaw random l (fun _sample => (0 : E)) := by
  rw [tendstoInMeasure_iff_norm]
  intro ε hε
  refine (tendsto_congr' ?_).mpr tendsto_const_nhds
  filter_upwards [hbound_eventual, hbound_zero.eventually_lt_const hε]
    with index hbound_index hbound_lt
  have hempty :
      {sample | ε ≤ ‖random index sample - 0‖} = (∅ : Set Sample) := by
    ext sample
    simp only [Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false]
    have hnorm_lt : ‖random index sample‖ < ε :=
      lt_of_le_of_lt (hbound_index sample) hbound_lt
    simpa [sub_zero] using not_le_of_gt hnorm_lt
  rw [hempty]
  simp

/--
Real-valued absolute-bound specialization of the uniform norm-bound adapter.
-/
theorem tendstoInMeasure_zero_of_eventually_abs_le_bound
    (random : Index -> Sample -> Real)
    (bound : Index -> Real)
    (hbound_zero : Tendsto bound l (nhds 0))
    (hbound_eventual :
      ∀ᶠ index in l, ∀ sample, |random index sample| ≤ bound index) :
    TendstoInMeasure sampleLaw random l (fun _sample => (0 : Real)) :=
  tendstoInMeasure_zero_of_eventually_uniform_norm_bound
    (sampleLaw := sampleLaw) (l := l) random bound hbound_zero
    (by
      filter_upwards [hbound_eventual] with index hbound_index sample
      simpa [Real.norm_eq_abs] using hbound_index sample)

/--
Real-valued absolute-bound adapter with a fixed scale multiplying one
shrinking envelope.
-/
theorem tendstoInMeasure_zero_of_eventually_abs_le_const_mul_bound
    (random : Index -> Sample -> Real)
    (scale : Real)
    (envelope : Index -> Real)
    (henvelope_zero : Tendsto envelope l (nhds 0))
    (hbound_eventual :
      ∀ᶠ index in l, ∀ sample,
        |random index sample| ≤ scale * envelope index) :
    TendstoInMeasure sampleLaw random l (fun _sample => (0 : Real)) :=
  tendstoInMeasure_zero_of_eventually_abs_le_bound
    (sampleLaw := sampleLaw) (l := l) random
    (fun index => scale * envelope index)
    (by
      simpa using
        ((tendsto_const_nhds : Tendsto (fun _index : Index => scale) l
          (nhds scale)).mul henvelope_zero))
    hbound_eventual

/--
Paired real-valued absolute-bound adapter.  This is the PATE/PATT shape used
when both local remainders are controlled by deterministic rates.
-/
theorem paired_tendstoInMeasure_zero_of_eventually_abs_le_bound
    (left right : Index -> Sample -> Real)
    (leftBound rightBound : Index -> Real)
    (hleft_bound_zero : Tendsto leftBound l (nhds 0))
    (hright_bound_zero : Tendsto rightBound l (nhds 0))
    (hleft_bound_eventual :
      ∀ᶠ index in l, ∀ sample,
        |left index sample| ≤ leftBound index)
    (hright_bound_eventual :
      ∀ᶠ index in l, ∀ sample,
        |right index sample| ≤ rightBound index) :
    TendstoInMeasure sampleLaw left l (fun _sample => (0 : Real)) ∧
      TendstoInMeasure sampleLaw right l (fun _sample => (0 : Real)) :=
  ⟨tendstoInMeasure_zero_of_eventually_abs_le_bound
      (sampleLaw := sampleLaw) (l := l) left leftBound hleft_bound_zero
      hleft_bound_eventual,
    tendstoInMeasure_zero_of_eventually_abs_le_bound
      (sampleLaw := sampleLaw) (l := l) right rightBound hright_bound_zero
      hright_bound_eventual⟩

/--
Paired fixed-envelope version of the deterministic-bound-to-`o_P(1)` adapter.
-/
theorem paired_tendstoInMeasure_zero_of_eventually_abs_le_const_mul_bound
    (left right : Index -> Sample -> Real)
    (leftScale rightScale : Real)
    (envelope : Index -> Real)
    (henvelope_zero : Tendsto envelope l (nhds 0))
    (hleft_bound_eventual :
      ∀ᶠ index in l, ∀ sample,
        |left index sample| ≤ leftScale * envelope index)
    (hright_bound_eventual :
      ∀ᶠ index in l, ∀ sample,
        |right index sample| ≤ rightScale * envelope index) :
    TendstoInMeasure sampleLaw left l (fun _sample => (0 : Real)) ∧
      TendstoInMeasure sampleLaw right l (fun _sample => (0 : Real)) :=
  ⟨tendstoInMeasure_zero_of_eventually_abs_le_const_mul_bound
      (sampleLaw := sampleLaw) (l := l) left leftScale envelope
      henvelope_zero hleft_bound_eventual,
    tendstoInMeasure_zero_of_eventually_abs_le_const_mul_bound
      (sampleLaw := sampleLaw) (l := l) right rightScale envelope
      henvelope_zero hright_bound_eventual⟩

/--
Asymptotically equivalent real-valued statistics have the same weak limit.
This is the vdV Slutsky equivalence form specialized to WDSM's real-valued
statistics.
-/
theorem tendstoInDistribution_of_tendstoInMeasure_sub_zero
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (main equivalent : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hdiff :
      TendstoInMeasure sampleLaw
        (fun index sample => equivalent index sample - main index sample)
        l (fun _sample => (0 : Real)))
    (hdiff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => equivalent index sample - main index sample)
          sampleLaw) :
    TendstoInDistribution equivalent l limit
      (fun _index => sampleLaw) limitLaw := by
  have hsum :
      TendstoInDistribution
        (fun index sample =>
          main index sample + (equivalent index sample - main index sample))
        l limit (fun _index => sampleLaw) limitLaw :=
    tendstoInDistribution_add_negligible_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main
      (fun index sample => equivalent index sample - main index sample)
      limit hmain hdiff hdiff_meas
  refine hsum.congr (fun index => ?_) (ae_eq_refl _)
  exact ae_of_all _ fun sample => by ring

/--
Paired asymptotic-equivalence transfer from convergence in measure of
differences.
-/
theorem paired_tendstoInDistribution_of_tendstoInMeasure_sub_zero
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (leftMain leftEquivalent rightMain rightEquivalent :
      Index -> Sample -> Real)
    (leftLimit rightLimit : LimitSample -> Real)
    (hleft_main :
      TendstoInDistribution leftMain l leftLimit
        (fun _index => sampleLaw) limitLaw)
    (hright_main :
      TendstoInDistribution rightMain l rightLimit
        (fun _index => sampleLaw) limitLaw)
    (hleft_diff :
      TendstoInMeasure sampleLaw
        (fun index sample => leftEquivalent index sample -
          leftMain index sample)
        l (fun _sample => (0 : Real)))
    (hright_diff :
      TendstoInMeasure sampleLaw
        (fun index sample => rightEquivalent index sample -
          rightMain index sample)
        l (fun _sample => (0 : Real)))
    (hleft_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => leftEquivalent index sample -
            leftMain index sample)
          sampleLaw)
    (hright_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => rightEquivalent index sample -
            rightMain index sample)
          sampleLaw) :
    TendstoInDistribution leftEquivalent l leftLimit
        (fun _index => sampleLaw) limitLaw ∧
      TendstoInDistribution rightEquivalent l rightLimit
        (fun _index => sampleLaw) limitLaw :=
  ⟨tendstoInDistribution_of_tendstoInMeasure_sub_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      leftMain leftEquivalent leftLimit hleft_main hleft_diff
      hleft_diff_meas,
    tendstoInDistribution_of_tendstoInMeasure_sub_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      rightMain rightEquivalent rightLimit hright_main hright_diff
      hright_diff_meas⟩

/--
Absolute-difference version of asymptotic equivalence.  This is convenient
when the local expansion has already produced an absolute-error `o_P(1)`.
-/
theorem tendstoInDistribution_of_tendstoInMeasure_abs_sub_zero
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (main equivalent : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (habsolute :
      TendstoInMeasure sampleLaw
        (fun index sample => |equivalent index sample - main index sample|)
        l (fun _sample => (0 : Real)))
    (hdiff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => equivalent index sample - main index sample)
          sampleLaw) :
    TendstoInDistribution equivalent l limit
      (fun _index => sampleLaw) limitLaw := by
  have hdiff :
      TendstoInMeasure sampleLaw
        (fun index sample => equivalent index sample - main index sample)
        l (fun _sample => (0 : Real)) := by
    rw [tendstoInMeasure_iff_norm] at habsolute ⊢
    intro ε hε
    convert habsolute ε hε using 1
    funext index
    congr 1
    ext sample
    simp [Real.norm_eq_abs]
  exact
    tendstoInDistribution_of_tendstoInMeasure_sub_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main equivalent limit hmain hdiff hdiff_meas

/--
Paired absolute-difference version of asymptotic equivalence.
-/
theorem paired_tendstoInDistribution_of_tendstoInMeasure_abs_sub_zero
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (leftMain leftEquivalent rightMain rightEquivalent :
      Index -> Sample -> Real)
    (leftLimit rightLimit : LimitSample -> Real)
    (hleft_main :
      TendstoInDistribution leftMain l leftLimit
        (fun _index => sampleLaw) limitLaw)
    (hright_main :
      TendstoInDistribution rightMain l rightLimit
        (fun _index => sampleLaw) limitLaw)
    (hleft_absolute :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          |leftEquivalent index sample - leftMain index sample|)
        l (fun _sample => (0 : Real)))
    (hright_absolute :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          |rightEquivalent index sample - rightMain index sample|)
        l (fun _sample => (0 : Real)))
    (hleft_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => leftEquivalent index sample -
            leftMain index sample)
          sampleLaw)
    (hright_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => rightEquivalent index sample -
            rightMain index sample)
          sampleLaw) :
    TendstoInDistribution leftEquivalent l leftLimit
        (fun _index => sampleLaw) limitLaw ∧
      TendstoInDistribution rightEquivalent l rightLimit
        (fun _index => sampleLaw) limitLaw :=
  ⟨tendstoInDistribution_of_tendstoInMeasure_abs_sub_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      leftMain leftEquivalent leftLimit hleft_main hleft_absolute
      hleft_diff_meas,
    tendstoInDistribution_of_tendstoInMeasure_abs_sub_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      rightMain rightEquivalent rightLimit hright_main hright_absolute
      hright_diff_meas⟩

/--
Uniform deterministic absolute-error bound version of asymptotic equivalence.
This is the most common WDSM use case after deterministic remainder algebra:
an absolute difference is bounded by a scalar rate that tends to zero.
-/
theorem tendstoInDistribution_of_eventually_abs_sub_le_bound
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (main equivalent : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (bound : Index -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hbound_zero : Tendsto bound l (nhds 0))
    (hbound :
      ∀ᶠ index in l,
        ∀ sample, |equivalent index sample - main index sample| ≤
          bound index)
    (hdiff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => equivalent index sample - main index sample)
          sampleLaw) :
    TendstoInDistribution equivalent l limit
      (fun _index => sampleLaw) limitLaw := by
  have hdiff :
      TendstoInMeasure sampleLaw
        (fun index sample => equivalent index sample - main index sample)
        l (fun _sample => (0 : Real)) :=
    tendstoInMeasure_zero_of_eventually_uniform_norm_bound
      (sampleLaw := sampleLaw) (l := l)
      (fun index sample => equivalent index sample - main index sample)
      bound hbound_zero
      (by
        filter_upwards [hbound] with index hbound_index sample
        simpa [Real.norm_eq_abs] using hbound_index sample)
  exact
    tendstoInDistribution_of_tendstoInMeasure_sub_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main equivalent limit hmain hdiff hdiff_meas

/--
Uniform deterministic absolute-error bound version of asymptotic equivalence
with a fixed scale multiplying one shrinking envelope.
-/
theorem tendstoInDistribution_of_eventually_abs_sub_le_const_mul_bound
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (main equivalent : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (scale : Real)
    (envelope : Index -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (henvelope_zero : Tendsto envelope l (nhds 0))
    (hbound :
      ∀ᶠ index in l,
        ∀ sample, |equivalent index sample - main index sample| ≤
          scale * envelope index)
    (hdiff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => equivalent index sample - main index sample)
          sampleLaw) :
    TendstoInDistribution equivalent l limit
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_of_eventually_abs_sub_le_bound
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    main equivalent limit (fun index => scale * envelope index) hmain
    (by
      simpa using
        ((tendsto_const_nhds : Tendsto (fun _index : Index => scale) l
          (nhds scale)).mul henvelope_zero))
    hbound hdiff_meas

/--
Paired deterministic absolute-error bound transfer for PATE/PATT-style
estimated-score local remainders.
-/
theorem paired_tendstoInDistribution_of_eventually_abs_sub_le_bound
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (leftMain leftEquivalent rightMain rightEquivalent :
      Index -> Sample -> Real)
    (leftLimit rightLimit : LimitSample -> Real)
    (leftBound rightBound : Index -> Real)
    (hleft_main :
      TendstoInDistribution leftMain l leftLimit
        (fun _index => sampleLaw) limitLaw)
    (hright_main :
      TendstoInDistribution rightMain l rightLimit
        (fun _index => sampleLaw) limitLaw)
    (hleft_bound_zero : Tendsto leftBound l (nhds 0))
    (hright_bound_zero : Tendsto rightBound l (nhds 0))
    (hleft_bound :
      ∀ᶠ index in l,
        ∀ sample, |leftEquivalent index sample - leftMain index sample| ≤
          leftBound index)
    (hright_bound :
      ∀ᶠ index in l,
        ∀ sample, |rightEquivalent index sample - rightMain index sample| ≤
          rightBound index)
    (hleft_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => leftEquivalent index sample -
            leftMain index sample)
          sampleLaw)
    (hright_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => rightEquivalent index sample -
            rightMain index sample)
          sampleLaw) :
    TendstoInDistribution leftEquivalent l leftLimit
        (fun _index => sampleLaw) limitLaw ∧
      TendstoInDistribution rightEquivalent l rightLimit
        (fun _index => sampleLaw) limitLaw :=
  ⟨tendstoInDistribution_of_eventually_abs_sub_le_bound
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      leftMain leftEquivalent leftLimit leftBound hleft_main
      hleft_bound_zero hleft_bound hleft_diff_meas,
    tendstoInDistribution_of_eventually_abs_sub_le_bound
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      rightMain rightEquivalent rightLimit rightBound hright_main
      hright_bound_zero hright_bound hright_diff_meas⟩

/--
Paired fixed-envelope version of deterministic absolute-error transfer.
-/
theorem paired_tendstoInDistribution_of_eventually_abs_sub_le_const_mul_bound
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated]
    (leftMain leftEquivalent rightMain rightEquivalent :
      Index -> Sample -> Real)
    (leftLimit rightLimit : LimitSample -> Real)
    (leftScale rightScale : Real)
    (envelope : Index -> Real)
    (hleft_main :
      TendstoInDistribution leftMain l leftLimit
        (fun _index => sampleLaw) limitLaw)
    (hright_main :
      TendstoInDistribution rightMain l rightLimit
        (fun _index => sampleLaw) limitLaw)
    (henvelope_zero : Tendsto envelope l (nhds 0))
    (hleft_bound :
      ∀ᶠ index in l,
        ∀ sample, |leftEquivalent index sample - leftMain index sample| ≤
          leftScale * envelope index)
    (hright_bound :
      ∀ᶠ index in l,
        ∀ sample, |rightEquivalent index sample - rightMain index sample| ≤
          rightScale * envelope index)
    (hleft_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => leftEquivalent index sample -
            leftMain index sample)
          sampleLaw)
    (hright_diff_meas :
      ∀ index,
        AEMeasurable
          (fun sample => rightEquivalent index sample -
            rightMain index sample)
          sampleLaw) :
    TendstoInDistribution leftEquivalent l leftLimit
        (fun _index => sampleLaw) limitLaw ∧
      TendstoInDistribution rightEquivalent l rightLimit
        (fun _index => sampleLaw) limitLaw :=
  ⟨tendstoInDistribution_of_eventually_abs_sub_le_const_mul_bound
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      leftMain leftEquivalent leftLimit leftScale envelope hleft_main
      henvelope_zero hleft_bound hleft_diff_meas,
    tendstoInDistribution_of_eventually_abs_sub_le_const_mul_bound
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      rightMain rightEquivalent rightLimit rightScale envelope hright_main
      henvelope_zero hright_bound hright_diff_meas⟩

end WDSM
end Matching
end StatInference
