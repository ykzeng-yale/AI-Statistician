/-
================================================================================
  ProbabilityFoundations.lean —— Mathlib 概率论入门 (面试 cheat-sheet 版)
================================================================================

  目标: 5 分钟之内能在白板上说出 Mathlib 概率论的「骨架」 ——
        什么类型, 什么 namespace, 哪些 lemma 可以拿来直接用, 哪些是缺的.

  Mathlib 把概率论搭在 measure theory 上面 (跟 Rudin / Billingsley 的路线一样).
  四层骨架:

    ┌─────────────────────────────────────────────────────────────────┐
    │ Layer 1: MeasurableSpace α   ←  "α 上能 measure 的 σ-代数"        │
    │ Layer 2: Measure α           ←  "一个具体测度 (可能是无穷)"       │
    │ Layer 3: IsProbabilityMeasure μ  ←  "μ univ = 1, 即概率测度"     │
    │ Layer 4: Random variable: X : α → β  measurable                  │
    │           Expectation:  ∫ x, X x ∂μ                              │
    │           Variance:     ∫ x, (X x − E[X])^2 ∂μ                   │
    └─────────────────────────────────────────────────────────────────┘

  这份文件按这 4 层走, 每层给:
    (a) Mathlib 里的 name + import path
    (b) 最小可运行 example
    (c) 跟统计学家说人话的 "对应" (E[X], Var[X], P(X ≥ a))
-/

import Mathlib

namespace AIStat.Prob

open MeasureTheory ProbabilityTheory

/-! ## §1. Mathlib 概率论 cheat sheet (背下来 8 个 name)

  ┌──────────────────────────┬───────────────────────────────────────────┐
  │ 数学概念                  │ Mathlib 里叫什么                          │
  ├──────────────────────────┼───────────────────────────────────────────┤
  │ σ-algebra                │ `MeasurableSpace α`                       │
  │ measure μ                │ `MeasureTheory.Measure α`                 │
  │ probability measure      │ `IsProbabilityMeasure μ`                  │
  │ Borel σ-algebra on ℝ     │ `borel ℝ` / `MeasurableSpace.borel`       │
  │ measurable function      │ `Measurable f`                            │
  │ random variable          │ 没专门 type, 就是 `Measurable (X : Ω → ℝ)`│
  │ expectation E[X]         │ `∫ x, X x ∂μ`   (`MeasureTheory.integral`)│
  │ variance Var[X]          │ `ProbabilityTheory.variance X μ`          │
  │ indicator function 1_A   │ `Set.indicator A 1`                       │
  │ a.s. equal               │ `=ᵐ[μ]`   (Filter.EventuallyEq)           │
  │ independent              │ `ProbabilityTheory.IndepFun X Y μ`        │
  │ i.i.d.                   │ `IdentDistrib X Y μ μ' + Indep...`        │
  │ converges a.s.           │ `Filter.Tendsto _ _ (𝓝 ...)` a.s.        │
  │ converges in probability │ `Filter.Tendsto _ _ (...)` in MeasureP    │
  │ converges in distribution│ NOT YET in Mathlib ← 这是 pitch 的 gap!  │
  │ characteristic function  │ NOT YET fully formalized ← gap!           │
  │ moment-generating fun.   │ partial, 在 `Probability.Moments`         │
  └──────────────────────────┴───────────────────────────────────────────┘
-/


/-! ## §2. 最小 example —— "扔硬币" 概率空间

  把「扔一次公平硬币」formalize. 这是所有 stats 课的 hello world. -/

namespace CoinFlip

/-- 样本空间: `Bool` (true = heads, false = tails). -/
abbrev Ω : Type := Bool

/-- `Bool` 已经有 measurable space instance (自动是 discrete σ-algebra). -/
example : MeasurableSpace Ω := inferInstance

/-- 「均匀」概率测度: 每个 outcome 都是 1/2. Mathlib 提供 `PMF.uniformOfFinset`. -/
noncomputable def fairCoin : MeasureTheory.Measure Ω :=
  PMF.uniformOfFinset (Finset.univ : Finset Bool) (by decide) |>.toMeasure

example : IsProbabilityMeasure fairCoin := by
  unfold fairCoin
  infer_instance

end CoinFlip


/-! ## §3. 随机变量 = measurable function

  "random variable X" 在 Mathlib 里就是 `(X : Ω → ℝ) (hX : Measurable X)`.
  没有专门的 `RandomVariable` type —— Mathlib 哲学是「概念越少越好」.

  我们扔骰子, 定义 `X(ω) = ω + 1`. -/

namespace DiceRoll

abbrev Ω : Type := Fin 6   -- 6 个 outcome

noncomputable def fairDie : MeasureTheory.Measure Ω :=
  PMF.uniformOfFinset (Finset.univ : Finset (Fin 6)) (by decide) |>.toMeasure

/-- 随机变量 X = (掷出的点数). -/
def X : Ω → ℝ := fun ω => (ω.val : ℝ) + 1

/-- 任何从 `Fin 6` 出发的函数都是 measurable (因为 Fin 6 离散). -/
lemma X_measurable : Measurable X := measurable_of_finite _

end DiceRoll


/-! ## §4. Expectation E[X]

  Mathlib 用 `MeasureTheory.integral`. 写法:
      ∫ ω, X ω ∂μ
  对于 nonneg 的, 用 `lintegral` (ENNReal 版本):
      ∫⁻ ω, X ω ∂μ

  ⚠️ Gotcha 1: 必须保证 X 是 `Integrable` 才能用线性性等性质.
  ⚠️ Gotcha 2: a.e. equal 的两个函数 expectation 相同 —— 但要显式写
              `integral_congr_ae`, 不像纸笔上 "显然".
-/

namespace Expectation

open MeasureTheory

/-! 抽象 setup: 一个概率空间. (注意 `variable` 是命令, 不接 `/-- -/` 文档字符串, 必须用 `/-! -/`.) -/

variable {Ω : Type*} {m : MeasurableSpace Ω} (μ : Measure Ω) [IsProbabilityMeasure μ]
variable (X Y : Ω → ℝ)

/-- E[c] = c 对于常数 c. (常数随机变量的期望是它自己.) -/
example (c : ℝ) : ∫ _, c ∂μ = c := by
  simp [integral_const]

/-- E[X + Y] = E[X] + E[Y]  (期望线性性).
    Mathlib 名字: `integral_add`. 需要 X, Y 都 integrable. -/
example (hX : Integrable X μ) (hY : Integrable Y μ) :
    ∫ ω, (X ω + Y ω) ∂μ = (∫ ω, X ω ∂μ) + (∫ ω, Y ω ∂μ) :=
  integral_add hX hY

/-- E[c * X] = c * E[X]  (期望齐次性). -/
example (c : ℝ) :
    ∫ ω, c * X ω ∂μ = c * ∫ ω, X ω ∂μ :=
  integral_const_mul c X

end Expectation


/-! ## §5. Variance —— Mathlib 已经有

  `ProbabilityTheory.variance X μ` = E[(X − E[X])²].
  常用 lemma:
    • `variance_def'`     : variance X μ = E[X²] − (E[X])²
    • `variance_const`    : variance (fun _ => c) μ = 0
    • `variance_smul`     : variance (c • X) μ = c² * variance X μ
    • `IndepFun.variance_add` : Var[X + Y] = Var[X] + Var[Y] for independent X, Y
-/

namespace VarianceDemo

open MeasureTheory ProbabilityTheory

variable {Ω : Type*} {m : MeasurableSpace Ω} (μ : Measure Ω) [IsProbabilityMeasure μ]

/-- 常数的方差是 0.
    面试小知识: Mathlib 里 `variance` 是通过 `evariance` (ENNReal 版本) 定义的:
        variance X μ := (∫⁻ ω, ‖X ω - μ[X]‖ₑ ^ 2 ∂μ).toReal
    所以 unfold 后看到 ENNReal 的 norm 别慌, simp 会处理. -/
example (c : ℝ) : variance (fun _ : Ω => c) μ = 0 := by
  simp [variance, evariance]

end VarianceDemo


/-! ## §6. 概率 = 事件的测度

  "P(X ≥ a)" 在 Mathlib 里就是 `μ {ω | a ≤ X ω}`, 类型是 `ENNReal`.
  对于概率测度 μ, 这个值 ≤ 1.

  常用 measure 操作:
    • `μ univ = 1`  (since IsProbabilityMeasure)
    • `μ A + μ Aᶜ = 1`  (Finitely additive)
    • `μ (A ∪ B) ≤ μ A + μ B`  (Subadditivity)
-/

namespace EventProb

open MeasureTheory

variable {Ω : Type*} {m : MeasurableSpace Ω} (μ : Measure Ω) [IsProbabilityMeasure μ]

/-- 整个样本空间的概率是 1. -/
example : μ Set.univ = 1 := measure_univ

/-- 互补事件: μ A + μ Aᶜ = 1.  (这里用 `prob_compl_eq_one_sub` 等 Mathlib lemma.) -/
example (A : Set Ω) (hA : MeasurableSet A) : μ Aᶜ = 1 - μ A := by
  rw [prob_compl_eq_one_sub hA]

end EventProb


/-! ## §7. 独立性 (Independence)

  Mathlib 有 4 个 independence 概念, 都在 `ProbabilityTheory`:

    • `IndepSets`       : 两个 σ-代数 (作为 Set Set) 独立
    • `Indep`           : 两个 σ-代数 (作为 MeasurableSpace) 独立
    • `IndepFun X Y μ`  : 两个随机变量独立
    • `iIndepFun X μ`   : 一族随机变量两两独立

  CLT 和 SLLN 都需要 i.i.d.:  `iIndepFun X μ` + `IdentDistrib (X i) (X j) μ μ`.
-/

namespace IndepDemo

open MeasureTheory ProbabilityTheory

variable {Ω : Type*} {m : MeasurableSpace Ω} (μ : Measure Ω)
variable (X Y : Ω → ℝ)

/-- 独立性的标准定义: 任何 measurable 事件 A, B 都有 P(X ∈ A ∧ Y ∈ B) = P(X ∈ A) * P(Y ∈ B). -/
example (_hXY : IndepFun X Y μ) : True := trivial
-- 用法: `hXY.symm` (对称), `hXY.comp` (函数 composed 后仍独立), `hXY.variance_add` (方差可加)

end IndepDemo


/-! ## §8. 收敛模式 —— 这里有大 gap

  统计推断的核心是「估计量 → 真值」的各种收敛.

  四种收敛 (强到弱):

    a.s.  ──→  in L^p (p≥1)  ──→  in probability  ──→  in distribution
    ✓ Mathlib     ✓ Mathlib       ✓ Mathlib         ✗ NOT YET!

  Mathlib 已有:
    • `MeasureTheory.Tendsto.ae`           ─ a.s. 收敛
    • `MeasureTheory.MemLp`                ─ L^p 空间
    • `Filter.Tendsto _ _ (ae_le ...)`    ─ in probability (有些工具)

  **缺失** (Axiom Math 应该填):
    • `convergesInDistribution` 没有干净的 type
    • Lévy continuity theorem (CLT 的关键工具) 没有
    • `Helly–Bray` theorem 没有
    • Slutsky's theorem 没有
    • Delta method 没有

  这些缺失就是 *AI Statistician* 产品的核心 selling point.
-/


/-! ## §9. 一句话总结 (面试时可以这样说)

  "Mathlib 已经把测度论、Markov / Chebyshev、SLLN、条件期望 都建好了。
   缺的是 *统计推断* 那一层 —— 收敛模式 (in distribution)、CLT 完整版、
   characteristic function、estimator theory、hypothesis testing.
   这些是 Axiom Math 的产品空间, 因为它们恰好是 LLM hallucinate 最严重的地方."
-/

end AIStat.Prob
