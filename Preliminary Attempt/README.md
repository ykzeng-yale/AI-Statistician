# 🎯 AI Statistician × Axiom Math — Interview Prep

> **你的 pitch**: "Apply Axiom Math's formal verification stack to AI statisticians — build a system that *proves* statistical claims correct (no hallucinated regularity conditions, no flipped Type I/II errors, no missing identifiability checks)."

---

## 🧭 面试准备 —— 只需要看 7 个文件 (按顺序)

| # | 文件 | 你怎么用它 | 时长 |
|---|---|---|---:|
| 1 | **`PitchDeck.md`** ★ | 5-min 脚本 + 10 个 Q&A + Slide 4c (★ formal verification) + frozen demo backup | 30 min |
| 2 | **`FormalVerificationReport.md`** ★ | ★ REAL `axle.verify_proof` 结果: COLD 2/5, HINTED 5/5 (pitch's credibility check) | 5 min |
| 3 | **`ArchitectureComparison.md`** ★ | 2 vs 3 vs 4 agent benchmark + 为什么选 3-agent | 10 min |
| 4 | **`EvaluationReport.md`** ★ | 多 seed stability eval (variance 100% / bernoulli 0%) | 5 min |
| 5 | **`stat_research_agent.py`** ★ | 3-agent research loop. **跑一次 `--demo` 看 output.** | 5 min |
| 6 | **`formal_proof_eval.py`** ★ | ★ NEW: REAL formal proof eval. **跑一次 `--both`.** | 5 min |
| 7 | **`StatisticsTheorems.lean`** | Mathlib gap analysis. Pitch Slide 2 用. | 10 min |

**配套但不必精读** (面试官可能扫一眼):
- `ProbabilityFoundations.lean` — Mathlib 概率论 cheat sheet
- `StatTactics.lean` — 自定义 stat-specific Lean tactics
- `frozen_demos/*.txt` — 万一 API 挂了, 用这些 hardcoded 输出 demo

**完全不用看** —— 都在 `archive/` 文件夹:
- 2-agent / 4-agent code variants
- benchmark harness (`compare_architectures.py`)
- multi-seed eval runner (`run_eval.py`)
- raw JSON 结果 (`comparison_results.json`, `eval_results.json`)

---

## 🎬 面试当天 demo 流程 (~9 min, 全程跑实际代码)

```bash
cd /Users/yukang/LeanProjects/LeanPractice
source .venv/bin/activate

# Step 1 (0:30): 滑 PitchDeck.md, 背 Slide 1 "what problem"
# Step 2 (1:00): 滑 StatisticsTheorems.lean §1-6, 讲 Mathlib gap
# Step 3 (1:00): 滑 StatTactics.lean, 跑 markov_apply example
# Step 4a (1:00): 跑 verifier demo (~10s)
python LeanPractice/AxiomMathTutorials/AIStatisticianPrep/stat_agent.py --demo

# Step 4b (1:30): 跑 3-agent research loop (~30s)
python LeanPractice/AxiomMathTutorials/AIStatisticianPrep/stat_research_agent.py --demo

# Step 4c (1:30): ★ NEW —— REAL formal verification eval (~30s)
python LeanPractice/AxiomMathTutorials/AIStatisticianPrep/formal_proof_eval.py --both
# 显示 COLD 2/5, HINTED 5/5 → "premise selection gap = product opportunity"

# Step 4d (0:30): 打开 ArchitectureComparison.md, 讲 "我用数据选的 3-agent"
# Step 5 (2:00): Q&A, 按 PitchDeck.md 末尾 11 个准备的回答 (★ 重点 Q7-honesty)
```

---

## 📂 完整文件清单

### 🔥 Final / pitch-ready (in this folder)

| 文件 | 行数 | 用途 |
|---|---:|---|
| `README.md` | — | 本文件 (navigation) |
| `PitchDeck.md` | 354 | 5-min pitch 脚本 + Q&A |
| `ArchitectureComparison.md` | 162 | 2 vs 3 vs 4 agent benchmark report |
| `ProbabilityFoundations.lean` | 256 | Mathlib 概率论 8 个 type cheat sheet |
| `StatisticsTheorems.lean` | 300 | Markov/Chebyshev/SLLN ✓ + CLT/MLE/hypo testing ✗ |
| `StatTactics.lean` | 151 | 4 个 stat-specific Lean tactics |
| `stat_agent.py` | 582 | Verifier (3-agent: Prover + MC + Counterexample) |
| `stat_research_agent.py` | **858** ★ | **End-to-end 3-agent research loop (production default)** |

### 📦 Archive / exploration (in `archive/`)

| 文件 | 用途 |
|---|---|
| `archive/stat_research_agent_2agent.py` | 2-agent baseline (Math+Code, Sim) —— *输给 3-agent 的 control* |
| `archive/stat_research_agent_4agent.py` | 4-agent variant (Theory, Formal, Algo, Sim) —— *premium tier* |
| `archive/compare_architectures.py` | 2-vs-3-vs-4 benchmark harness, 产生 `ArchitectureComparison.md` |
| `archive/comparison_results.json` | 原始 architecture comparison raw data |
| `archive/run_eval.py` | 多 seed stability eval runner, 产生 `EvaluationReport.md` |
| `archive/eval_results.json` | 原始 per-trial eval data (6 trials = 3 seeds × 2 questions) |

> ⚠️ **面试不需要看 archive/**. 它们的*结论*已经在 `ArchitectureComparison.md` 和 `EvaluationReport.md` 里. 只有面试官问 "show me your code" 才需要打开.

### 🧊 Frozen demo outputs (in `frozen_demos/`)

| 文件 | 用途 |
|---|---|
| `frozen_demos/stat_agent_demo.txt` | 真 Claude 一次 stat_agent --demo 的完整 stdout (~10s 输出) |
| `frozen_demos/stat_research_agent_demo.txt` | 真 Claude 一次 stat_research_agent --demo 的完整 stdout (~30s 输出) |

**面试当天 API 挂了**: `cat frozen_demos/<file>` 直接读这些输出, 边讲边滑.

---

## 🎯 The pitch in 2 sentences

> "Statistics is the highest-hallucination-cost domain for LLMs. We built a 3-agent system (Mathematician derives, Algorithm implements, Simulator-as-deterministic-adjudicator classifies failures into MATH_ERROR vs IMPL_ERROR for explicit escalation) on top of AXLE — verified empirically against 2-agent and 4-agent variants — and it's the cost-per-converged-question sweet spot for production AI statistician."

---

## ❓ 6 个必背的问答

详见 `PitchDeck.md` 末尾 Q1-Q7c. 一句话版本:

| Q | A 关键词 |
|---|---|
| Why statistics? | "Highest-hallucination-cost domain; FDA/SEC use case" |
| What's already in Mathlib? | "Markov ✓, Chebyshev ✓, SLLN ✓; CLT ✗, MLE ✗, hypo testing ✗" |
| How to formalize CLT? | "Lévy continuity theorem + characteristic functions; 3-6 month effort" |
| Multi-agent vs single LLM? | "Empirical feedback ≠ LLM-generatable; separation enables blame routing" |
| Why 3-agent vs 4-agent? | "Data: 3-agent 33% cheaper per converged question; 4-agent ships for FDA-rigor segment" |
| Your one-week deliverable? | "5 Mathlib PRs + 5 stat tactics + 1 Phase III case study + 1 cold email" |

---

## 🚀 重新生成 ArchitectureComparison.md (如果你想 fresh data)

```bash
cd /Users/yukang/LeanProjects/LeanPractice
source .venv/bin/activate
python LeanPractice/AxiomMathTutorials/AIStatisticianPrep/archive/compare_architectures.py
# → 跑 ~2 min, $0.07, 更新 ../ArchitectureComparison.md + archive/comparison_results.json
```

(注意脚本是从 `archive/` 跑的, 但输出写回 parent folder.)

---

**祝你拿到 offer.** 🎯
