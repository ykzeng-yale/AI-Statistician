import StatInference.Asymptotics.Op

/-!
# Asymptotic normality interfaces

This file records the first high-value inference theorem as an explicit bundle:
asymptotic linearity plus a CLT plus a negligible remainder implies asymptotic
normality. The concrete theorem should later be implemented using mathlib's
`TendstoInDistribution`, CLT, and Slutsky-style lemmas.
-/

namespace StatInference

structure AsymptoticNormalityBridge where
  asymptotic_linear : Prop
  clt_for_linear_part : Prop
  negligible_remainder : Prop
  asymptotic_normality : Prop
  bridge :
    asymptotic_linear ->
    clt_for_linear_part ->
    negligible_remainder ->
    asymptotic_normality

theorem asymptotic_normality_of_bridge (b : AsymptoticNormalityBridge)
    (hal : b.asymptotic_linear)
    (hclt : b.clt_for_linear_part)
    (hrem : b.negligible_remainder) :
    b.asymptotic_normality :=
  b.bridge hal hclt hrem

end StatInference

