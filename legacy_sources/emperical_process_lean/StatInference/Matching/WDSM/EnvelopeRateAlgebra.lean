import StatInference.Matching.WDSM.ScaledSqueezeAlgebra

/-!
# Envelope-rate algebra for WDSM approximation bounds

Many deterministic WDSM bounds have the form `envelope * error`.  The
stochastic layer normally proves that the envelope converges to a finite limit
and that the error term vanishes.  This module records the real `Tendsto`
algebra that turns those two inputs into the product-rate hypotheses needed by
the approximate-balancing and double-score rate-transfer theorems.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index : Type*} {l : Filter Index}

theorem tendsto_envelope_mul_error_zero
    (envelope error : Index -> Real) (envelopeLimit : Real)
    (henvelope : Tendsto envelope l (nhds envelopeLimit))
    (herror : Tendsto error l (nhds 0)) :
    Tendsto (fun index => envelope index * error index) l (nhds 0) := by
  simpa using henvelope.mul herror

theorem tendsto_two_envelope_mul_errors_zero
    (envelopeA envelopeB errorA errorB : Index -> Real)
    (envelopeLimitA envelopeLimitB : Real)
    (henvelopeA : Tendsto envelopeA l (nhds envelopeLimitA))
    (henvelopeB : Tendsto envelopeB l (nhds envelopeLimitB))
    (herrorA : Tendsto errorA l (nhds 0))
    (herrorB : Tendsto errorB l (nhds 0)) :
    Tendsto
      (fun index =>
        envelopeA index * errorA index +
          envelopeB index * errorB index)
      l (nhds 0) := by
  simpa using
    (tendsto_envelope_mul_error_zero envelopeA errorA envelopeLimitA
      henvelopeA herrorA).add
    (tendsto_envelope_mul_error_zero envelopeB errorB envelopeLimitB
      henvelopeB herrorB)

theorem tendsto_scaled_envelope_mul_error_zero
    (scale envelope error : Index -> Real) (envelopeLimit : Real)
    (henvelope : Tendsto envelope l (nhds envelopeLimit))
    (hscaled_error :
      Tendsto (fun index => scale index * error index) l (nhds 0)) :
    Tendsto
      (fun index => scale index * (envelope index * error index))
      l (nhds 0) := by
  have hproduct :
      Tendsto (fun index => envelope index * (scale index * error index))
        l (nhds 0) := by
    simpa using henvelope.mul hscaled_error
  convert hproduct using 1
  ext index
  ring

theorem tendsto_scaled_two_envelope_mul_errors_zero
    (scale envelopeA envelopeB errorA errorB : Index -> Real)
    (envelopeLimitA envelopeLimitB : Real)
    (henvelopeA : Tendsto envelopeA l (nhds envelopeLimitA))
    (henvelopeB : Tendsto envelopeB l (nhds envelopeLimitB))
    (hscaled_errorA :
      Tendsto (fun index => scale index * errorA index) l (nhds 0))
    (hscaled_errorB :
      Tendsto (fun index => scale index * errorB index) l (nhds 0)) :
    Tendsto
      (fun index =>
        scale index *
          (envelopeA index * errorA index +
            envelopeB index * errorB index))
      l (nhds 0) := by
  have hA :
      Tendsto (fun index => envelopeA index * (scale index * errorA index))
        l (nhds 0) :=
    tendsto_envelope_mul_error_zero envelopeA
      (fun index => scale index * errorA index) envelopeLimitA
      henvelopeA hscaled_errorA
  have hB :
      Tendsto (fun index => envelopeB index * (scale index * errorB index))
        l (nhds 0) :=
    tendsto_envelope_mul_error_zero envelopeB
      (fun index => scale index * errorB index) envelopeLimitB
      henvelopeB hscaled_errorB
  have hsum :
      Tendsto
        (fun index =>
          envelopeA index * (scale index * errorA index) +
            envelopeB index * (scale index * errorB index))
        l (nhds 0) :=
    by simpa using hA.add hB
  convert hsum using 1
  ext index
  ring

end WDSM
end Matching
end StatInference
