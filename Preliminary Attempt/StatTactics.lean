/-
================================================================================
  StatTactics.lean —— 给统计学家用的 custom tactics
================================================================================

  这些 tactic 是 "Axiom Math for AI Statistician" 产品里应该 ship 的 stat-specific
  自动化. 每一个都把「概率论里常用 lemma 的 invocation」打包成一行.

  类比:
    - omega        ←  Lean 内置, 处理 ℕ/ℤ 线性 ⟹  统计学家想要的「stat tactic」
    - linarith     ←  线性算术                  ⟹  prob_nonneg, indep_split
    - ring         ←  多项式恒等式               ⟹  expectation_linear
    - polyrith     ←  外部 solver                ⟹  markov_apply (auto premise)

  4 个 tactic, 每个都给:
    (a) 名字 + 用途
    (b) 实现思路
    (c) 用 example 演示
-/

import Mathlib

open Lean Elab Meta Tactic
open MeasureTheory ProbabilityTheory

namespace AIStat.Tactics


/-! ## §1. `prob_nonneg` —— 自动证 "0 ≤ P(A)" 这种琐碎事

  统计学家写 proof 时, 经常需要 "P(some event) ≥ 0". 这是 trivially true
  (因为 measure 取值在 [0, ∞]), 但 Lean 一定要 explicit prove. 我们提供
  `prob_nonneg` 一键 close. -/

elab "prob_nonneg" : tactic => do
  -- 任何 `μ A ≥ 0` 或 `0 ≤ μ A` 都用 `zero_le _` 关掉 (ENNReal 的非负性).
  evalTactic (← `(tactic| first | exact zero_le _ | exact bot_le | positivity))

section ProbNonnegDemo
variable {α : Type*} [MeasurableSpace α] (μ : Measure α) (A : Set α)

example : 0 ≤ μ A := by prob_nonneg
example : μ A ≥ 0 := by prob_nonneg
end ProbNonnegDemo


/-! ## §2. `expectation_linear` —— 自动展开期望线性性

  对 goal 形如 `∫ ω, (a * X ω + b * Y ω) ∂μ = ...`, 自动跑
    `integral_add`, `integral_const_mul`, `integral_sub`, ...
  连续展开, 直到剩下「单纯 expectation 的恒等式」.

  这一招在统计推断的「打开方差 / 协方差」证明里非常常用. -/

elab "expectation_linear" : tactic => do
  evalTactic (← `(tactic|
    repeat (
      first
        | rw [integral_add (by assumption) (by assumption)]
        | rw [integral_sub (by assumption) (by assumption)]
        | rw [integral_const_mul]
        | rw [integral_mul_const]
    )
  ))

section ExpLinDemo
-- 不强制运行 (需要具体 Integrable hypothesis), 只展示 elab 编译过.
end ExpLinDemo


/-! ## §3. `markov_apply` —— 自动应用 Markov inequality

  对 goal `μ {x | ε ≤ f x} ≤ ?`, 自动:
    1. 识别 f 的 measurability (尝试 `measurability`)
    2. invoke `meas_ge_le_lintegral_div`
    3. 留下「需要给 ε ≠ 0 + ε ≠ ⊤ 的证明」给用户

  这是真正 useful 的 stat tactic —— 教科书里 "by Markov inequality, we have ..."
  这种省事写法对应到 Lean 就是一行. -/

elab "markov_apply" : tactic => do
  evalTactic (← `(tactic|
    first
      | exact meas_ge_le_lintegral_div (by measurability) (by assumption) (by assumption)
      | exact meas_ge_le_lintegral_div (by measurability) (by norm_num) (by norm_num)
  ))

section MarkovApplyDemo
variable {α : Type*} [MeasurableSpace α] (μ : Measure α)

/-- 一行 Markov, *如果* 你有了 ε ≠ 0 和 ε ≠ ⊤ 的 hypothesis. -/
example (f : α → ENNReal) (_hf : Measurable f)
    (ε : ENNReal) (_hε : ε ≠ 0) (_hε' : ε ≠ ⊤) :
    μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε := by
  markov_apply

end MarkovApplyDemo


/-! ## §4. `var_indep_add` —— 独立时 Var[X+Y] = Var[X] + Var[Y]

  统计学家在 OLS / ANOVA / random effects 里反复用到的事.
  Mathlib 提供 `IndepFun.variance_add`, 我们把它包成 tactic. -/

elab "var_indep_add" : tactic => do
  evalTactic (← `(tactic|
    first
      | exact IndepFun.variance_add (by assumption) (by assumption) (by assumption)
      | rw [IndepFun.variance_add (by assumption) (by assumption) (by assumption)]
  ))

section VarIndepAddDemo
-- 同样, 需要具体 IndepFun + MemLp 2 hypothesis. 这里只测 elab 编译过.
end VarIndepAddDemo


/-! ## §5. 综合 demo —— 把 4 个 tactic 串起来证一个 stat fact

  目标: "若 X, Y 独立且都 L²-integrable, 则 Var[X + Y] = Var[X] + Var[Y]"
  这个 fact 是 Mathlib 现成的 `IndepFun.variance_add`, 但我们演示我们的
  `var_indep_add` tactic 一行完成. -/

section CombineDemo

variable {Ω : Type*} {m : MeasurableSpace Ω} (μ : Measure Ω) [IsProbabilityMeasure μ]

example (X Y : Ω → ℝ)
    (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ)
    (h_indep : IndepFun X Y μ) :
    variance (X + Y) μ = variance X μ + variance Y μ := by
  var_indep_add

end CombineDemo


/-! ## §6. 总结 —— 这 4 个 tactic 对面试 pitch 的意义

  ★ "我们能给统计学家造一组类似 `omega`/`ring` 的 stat-specific tactic.
     上面 4 个只是 demo, 真实产品会有 40-100 个,  覆盖:
       prob_nonneg, prob_sub_one, prob_union_bound, prob_inclusion_exclusion,
       expectation_linear, expectation_iter (E[E[X|Y]] = E[X]),
       markov_apply, chebyshev_apply, jensen_apply, holder_apply,
       var_indep_add, var_smul, var_compose,
       conv_in_prob_of_ae, conv_in_distr_of_in_prob, ..."

  每个 tactic 都把 "1 行论文证明" 翻译成 "1 行 Lean tactic". 这就是
  *productized math*: 让统计学家不用学 Mathlib 命名, 也能 formal verify
  自己的论文.
-/

end AIStat.Tactics
