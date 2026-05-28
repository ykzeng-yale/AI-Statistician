/-
================================================================================
  StatisticsTheorems.lean —— 统计学定理形式化的「现状 + gap」清单
================================================================================

  这是 pitch 最关键的一个文件: 它把 Mathlib *已经有的* 统计定理 (直接调用)
  跟 *还没形式化的* (sorry + 注释 "this is the gap") 并排放出来.

  面试时打开这个文件, 一边滑一边讲, 自然就把「Axiom Math 应该 build 什么」
  这件事 communicate 清楚了.

  四个 section:
    §1. Markov inequality           ✓ Mathlib 完整支持
    §2. Chebyshev inequality        ✓ Mathlib 完整支持
    §3. Law of Large Numbers (LLN)  ✓ 强大数 (Etemadi proof) Mathlib 有
    §4. Central Limit Theorem (CLT) ✗ GAP —— pitch 弹药
    §5. MLE consistency             ✗ GAP —— pitch 弹药
    §6. Hypothesis testing           ✗ GAP —— pitch 弹药
-/

import Mathlib

namespace AIStat.Theorems

open MeasureTheory ProbabilityTheory


/-! ## §1. Markov's Inequality —— ✓ in Mathlib

  Statement (概率论本)
    若 X ≥ 0 a.s., 对任何 ε > 0:  P(X ≥ ε) ≤ E[X] / ε

  Mathlib 名字: `MeasureTheory.mul_meas_ge_le_lintegral₀` (用 lintegral / ENNReal)
                `MeasureTheory.meas_ge_le_lintegral_div`   (除法版本)

  ⚠️ Mathlib 的官方 form 用的是 `lintegral` (∫⁻, ENNReal-valued), 不是普通
     `integral`. 这是因为 ENNReal 允许 ∞, 不需要 integrability assumption.
     对统计学家来说习惯有点儿绕, 但好处是定理 *无 hypothesis*.
-/

section MarkovDemo

variable {α : Type*} [MeasurableSpace α] (μ : Measure α)
variable (f : α → ENNReal) (hf : Measurable f) (ε : ENNReal) (hε : ε ≠ 0) (hεt : ε ≠ ⊤)

/-- Markov's inequality, Mathlib form (除法形式):
      μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε

    这就是 P(X ≥ ε) ≤ E[X] / ε 在 measure 语言下的写法. -/
example : μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε :=
  meas_ge_le_lintegral_div hf.aemeasurable hε hεt

end MarkovDemo


/-! ## §2. Chebyshev's Inequality —— ✓ in Mathlib (via Lp seminorms)

  Statement (概率论本):
    若 E[X^2] < ∞ (即 X ∈ L²), 对任何 ε > 0:
        P(|X - μ| ≥ ε) ≤ Var[X] / ε²

  Mathlib 提供更 general 的 Lp 版本:
    `MeasureTheory.pow_mul_meas_ge_le_eLpNorm` : ε^p * μ{‖f‖ ≥ ε} ≤ ‖f‖_p^p

  令 p = 2, 把 f = X - E[X] 代入, 就是经典 Chebyshev.
-/

section ChebyshevDemo

variable {α : Type*} [MeasurableSpace α] (μ : Measure α)
variable {E : Type*} [NormedAddCommGroup E]
variable (f : α → E) (hf : AEStronglyMeasurable f μ) (p : ENNReal)
variable (hp1 : p ≠ 0) (hp2 : p ≠ ⊤) (ε : ENNReal)

/-- Chebyshev–Markov in Lp form. Mathlib 实际给的形式比想象的弯一点:
    `(ε * μ{‖f‖ ≥ ε^p}) ^ (1/p) ≤ ‖f‖_{L^p}`. 等价于教科书写法 but with
    一个 ENNReal-friendly 整形. -/
example : (ε * μ {x | ε ≤ ‖f x‖ₑ ^ p.toReal}) ^ (1 / p.toReal) ≤ eLpNorm f p μ :=
  pow_mul_meas_ge_le_eLpNorm μ hp1 hp2 hf ε

end ChebyshevDemo


/-! ## §3. Strong Law of Large Numbers (SLLN) —— ✓ in Mathlib (Etemadi)

  Statement:
    若 X_n 是 i.i.d. integrable random variables, 则
        (∑_{i<n} X_i) / n  →  E[X_0]  a.s.

  Mathlib 名字: `ProbabilityTheory.strong_law_ae`
    `ProbabilityTheory.strong_law_ae_real`  (实值版本)

  ⚠️ Mathlib 的 statement 假设的是 **pairwise independence** (Etemadi 1981
     的改进版), 比经典版本要弱. 这是 Mathlib 一向的「找最强 / 最少假设」style.
-/

section SLLNDemo

/-- 概略: Mathlib 的 strong law 长这样 (从 docs 摘的).
    用法: 给定一组 i.i.d. integrable 随机变量, 直接 invoke. -/
example : True := by trivial
-- 真用法 (不在这里展开, 太长, 见 `Mathlib.Probability.StrongLaw`):
--   ProbabilityTheory.strong_law_ae_real :
--     ∀ (X : ℕ → Ω → ℝ),
--       (∀ i, Integrable (X i) μ) →
--       Pairwise (fun i j => IndepFun (X i) (X j) μ) →
--       (∀ i, IdentDistrib (X i) (X 0) μ μ) →
--       ∀ᵐ ω ∂μ, Tendsto (fun n => (∑ i ∈ Finset.range n, X i ω) / n)
--                        atTop (𝓝 (∫ x, X 0 x ∂μ))

end SLLNDemo


/-! ## §4. Central Limit Theorem (CLT) —— ✗ GAP

  Statement (Lindeberg-Lévy):
    若 X_n 是 i.i.d. with E[X] = μ, Var[X] = σ² < ∞, 则
        (S_n - nμ) / (σ √n)  →_d  𝒩(0, 1)
    其中 →_d 是 convergence in distribution.

  ★ 这是 Mathlib 的真实 GAP. 形式化 CLT 需要:
    (1) `ConvergesInDistribution` 的干净 definition (Mathlib 还没有)
    (2) Characteristic functions (Mathlib 有 partial 实现)
    (3) Lévy continuity theorem (没有)
    (4) Standard normal distribution `gaussianReal` (Mathlib 有 `gaussianReal`)

  这就是 *"Axiom Math for AI Statistician"* 第一个具体的 deliverable.
-/

section CLTGap

/-- 我们想 *statement* 出 CLT, 但 `ConvergesInDistribution` 还没干净的定义.
    下面用 `sorry` 占位 —— 真实场景下, 这就是 Axiom Math 的 R&D backlog 一项. -/
example : True := by trivial
-- 真实想要的 statement (用 axiom 占位, 不是 theorem, 因为我们没法证):
-- axiom central_limit_theorem
--     {Ω : Type*} {m : MeasurableSpace Ω} (μ : Measure Ω) [IsProbabilityMeasure μ]
--     (X : ℕ → Ω → ℝ)
--     (h_indep : Pairwise (fun i j => IndepFun (X i) (X j) μ))
--     (h_iid   : ∀ i, IdentDistrib (X i) (X 0) μ μ)
--     (h_L2    : MemLp (X 0) 2 μ)
--     (σ : ℝ) (hσ : σ = Real.sqrt (variance (X 0) μ)) (hσpos : 0 < σ) :
--     -- 这里需要 `ConvergesInDistribution` —— GAP
--     True  -- TODO: replace with real statement once Mathlib has →_d

end CLTGap


/-! ## §5. MLE Consistency —— ✗ GAP

  Statement (van der Vaart Th. 5.7):
    若  • Θ 是 compact parameter space
        • f(x; θ) 是 dominated by integrable function
        • θ ↦ E[log f(X; θ)] 在 θ₀ 处唯一最大化 (identifiability)
        • log-likelihood 一致连续
    则 MLE  θ̂_n = argmax_θ ∑_i log f(X_i; θ)  →  θ₀  almost surely.

  ★ 这是 Mathlib 完全没有的方向. 需要:
    (1) Likelihood function 的 generic formulation
    (2) Argmax 的 measurable selection
    (3) Uniform convergence 的工具 (Mathlib 有但不够强)
    (4) Compactness-based argument

  → 形式化这一定理 ≈ 1 个 senior engineer 3-6 个月的工作.
-/

section MLEGap

/-- MLE consistency 的 stub: 给一个 *parameterized family of distributions*
    和 i.i.d. 样本, MLE 收敛到真参数.

    我们写一个最 minimal 的 statement, 留 sorry —— 这正是 Axiom Math 的
    实际工作流: 先定 statement, 后逐 piece 实现. -/

structure ParameterizedFamily (Θ : Type*) (X : Type*) where
  density : Θ → X → ℝ        -- f(x; θ)
  dominated : True            -- TODO: 真实形式化需要 dominated by integrable
  identifiable : True         -- TODO: θ ↦ ∫ log f(x;θ) dμ(x) 在 θ₀ 唯一最大

example : True := by trivial
-- 真实想要的 axiom (sorried 是合理的, 我们在告诉面试官 *what is missing*):
-- axiom mle_consistent
--   {Θ X : Type*} [TopologicalSpace Θ] [MeasurableSpace X]
--   (family : ParameterizedFamily Θ X)
--   (θ₀ : Θ) (μ : Measure X) [IsProbabilityMeasure μ]
--   (samples : ℕ → X)
--   (h_iid : True)        -- TODO: independence + identical dist
--   (h_compact : True)    -- TODO: Θ compact, family 的 4 个 regularity 条件
--   : ∀ᵐ ω, Filter.Tendsto
--     (fun n => mleOf family (samples |>.take n))
--     Filter.atTop (𝓝 θ₀)

end MLEGap


/-! ## §6. Hypothesis Testing Framework —— ✗ GAP (whole framework)

  Statement (frequentist hypothesis test):
    • H_0: θ ∈ Θ_0  (null hypothesis)
    • H_1: θ ∈ Θ_1  (alternative)
    • Test statistic T(X), rejection region R
    • Type I error rate α = sup_{θ∈Θ_0} P_θ(T(X) ∈ R)
    • Power π(θ) = P_θ(T(X) ∈ R) for θ ∈ Θ_1

  ★ Mathlib 完全没有 hypothesis testing framework. 需要:
    (1) `Hypothesis` / `Test` structure
    (2) Type I error 的 formal definition
    (3) Neyman-Pearson lemma (最优 test)
    (4) p-value calibration
    (5) 常见 test: t-test, chi-square, F-test, Wilcoxon, ...

  → 这是 Axiom Math 一个非常清晰的 product spec. 跟 FDA / 临床试验直接对接.
-/

section HypoTestGap

/-- 一个统计检验的最 minimal stub. -/
structure StatTest (Θ : Type*) (X : Type*) where
  -- 参数空间 Θ 划分: H_0 vs H_1
  H0 : Set Θ
  H1 : Set Θ
  -- Test statistic + rejection region
  testStat : X → ℝ
  rejectRegion : Set ℝ
  -- (省略 regularity conditions ...)

example : True := by trivial
-- 真实想要的 lemma:
-- axiom type_one_error_bound
--   {Θ X : Type*} (test : StatTest Θ X)
--   (μ : Θ → Measure X) (α : ℝ) (hα : 0 < α ∧ α < 1)
--   (h : ∀ θ ∈ test.H0,
--        (μ θ) {x | test.testStat x ∈ test.rejectRegion} ≤ ENNReal.ofReal α) :
--   "This test controls Type I error at level α"

end HypoTestGap


/-! ## §7. 整合 —— 一个 *可以现场展示* 的小定理

  把上面的 §1-3 (Mathlib 已有的) 串起来, 证一个有意思的 stat 结论.

  目标: "样本均值的方差 = σ²/n"  (用于 confidence interval 推导)

  这是 stat 入门第一周教的, 但形式化它需要:
    - 期望线性性 (✓)
    - 独立时方差可加 (✓ Mathlib `IndepFun.variance_add`)
    - 期望齐次性 (✓)
-/

section SampleMeanVariance

variable {Ω : Type*} {m : MeasurableSpace Ω} (μ : Measure Ω) [IsProbabilityMeasure μ]

/-- 用 i.i.d. 的设定计算样本均值的方差. 我们 *陈述* 这一结果, 实际 proof
    需要 `iIndepFun` 的 induction, 大约 30-50 行. 留 sorry 是因为我们想
    用这个 stub 演示 stat_agent.py 怎么调用 AXLE 验证它.

    (变量名用 `sigma_sq` 而非 `σ²` —— Lean 4 identifier 不能 *以* 上标结尾.) -/
example (X : ℕ → Ω → ℝ) (n : ℕ) (sigma_sq : ℝ)
    (_h_iid : ∀ i, IdentDistrib (X i) (X 0) μ μ)
    (_h_indep : iIndepFun X μ)
    (_h_var : variance (X 0) μ = sigma_sq) :
    variance (fun ω => (∑ i ∈ Finset.range n, X i ω) / n) μ = sigma_sq / n := by
  sorry  -- ★ AxiomProver 应该能填这个; 我们交给 stat_agent.py 演示

end SampleMeanVariance


end AIStat.Theorems


/-
================================================================================
  Cheat sheet —— 面试时打开这个文件, 按 §1→§6 顺序滑就是 5 分钟 pitch
================================================================================

  「Mathlib 给统计学家什么」(说 30 秒):
    Markov ✓, Chebyshev (via Lp) ✓, SLLN (Etemadi) ✓, conditional expectation ✓,
    martingales ✓, Borel-Cantelli ✓.

  「Mathlib 还缺什么 = Axiom Math 应该 build 什么」(说 90 秒):
    1. ConvergesInDistribution + characteristic function 完整 API → unlocks CLT
    2. Estimator theory: MLE / M-estimator consistency + asymp normality
    3. Hypothesis testing framework: tests, p-value, Type I/II error
    4. Regression: OLS asymptotics, GLM
    5. Bayesian: posterior consistency, Bernstein-von Mises

  「Why this is a *product*」(说 60 秒):
    - 客户: FDA, pharma trial design teams, regulators, peer reviewers
    - Value prop: 数学论文里一行 "by standard arguments, the estimator is
      consistent" → 我们形式化 + 暴露 hidden hypothesis
    - Moat: 需要 Lean + Mathlib + 统计学双背景, 全世界 < 50 人能做

  「Multi-agent 怎么用」(转入 stat_agent.py demo, 90 秒):
    见 `stat_agent.py`. 3 agent 协作:
      - prover (LLM ↔ AXLE)
      - Monte Carlo verifier (numpy)
      - counterexample finder (LLM 提议 distribution + numerical check)
-/
