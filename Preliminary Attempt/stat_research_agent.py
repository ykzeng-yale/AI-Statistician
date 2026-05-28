"""
================================================================================
  stat_research_agent.py — End-to-End Statistical Research Loop (3-agent ver.)
  端到端统计研究三 agent 系统 (面试 demo 重头戏 ★)
================================================================================

  完整 architecture (3 个 agent + 2 个嵌套 loop):

      ┌──────────────────────────────────────────────────────────────────┐
      │  INPUT: ResearchQuestion                                         │
      │   • DGP (data generating process)                                │
      │   • Target (要估计什么)                                          │
      │   • Guarantee wanted (asymptotic normality? unbiasedness?)       │
      └──────────────────────────────────────────────────────────────────┘
                                  ↓
   ╔═══════════════════════════════════════════════════════════════════════╗
   ║ OUTER LOOP  (Mathematician escalation, max 2 rounds)                  ║
   ║                                                                       ║
   ║   ┌──────────────────────────────────────────────────┐                ║
   ║   │ MATHEMATICIAN AGENT                              │                ║
   ║   │  • derive estimator from DGP + target            │                ║
   ║   │  • express asymptotic guarantee in Lean theorem  │                ║
   ║   │  • AXLE type-checks the Lean statement           │                ║
   ║   │  OUTPUT: math formula + Lean stmt (NO code)      │                ║
   ║   └────────────────────┬─────────────────────────────┘                ║
   ║                        │ formula                                      ║
   ║                        ▼                                              ║
   ║   ╔═══════════════════════════════════════════════════════════════╗   ║
   ║   ║ INNER LOOP  (Algorithm ↔ Simulator, max 2 retries)            ║   ║
   ║   ║                                                               ║   ║
   ║   ║   ┌──────────────────┐    code    ┌─────────────────────┐     ║   ║
   ║   ║   │ ALGORITHM AGENT  │ ─────────► │ SIMULATOR AGENT     │     ║   ║
   ║   ║   │ - implement(...)│            │ - build environment │     ║   ║
   ║   ║   │ - fix(... err) │            │ - run MC replicates │     ║   ║
   ║   ║   │                  │            │ - classify outcome  │     ║   ║
   ║   ║   └────────┬─────────┘            └─────────┬───────────┘     ║   ║
   ║   ║            ▲                                │                  ║   ║
   ║   ║            │   IMPL_ERROR (algo bug)        │                  ║   ║
   ║   ║            └──── (impl_feedback) ───────────┤                  ║   ║
   ║   ║                                             │                  ║   ║
   ║   ║   Outcomes the simulator classifies:        │                  ║   ║
   ║   ║     OK         → ✅ converged, exit         │                  ║   ║
   ║   ║     IMPL_ERROR → algo retries (inner)       │                  ║   ║
   ║   ║     MATH_ERROR → 🔺 escalate to outer       │                  ║   ║
   ║   ╚═══════════════════════════════════════════════════════════════╝   ║
   ║                        │                                              ║
   ║       MATH_ERROR ─── (math_feedback) ────► back to Mathematician     ║
   ╚═══════════════════════════════════════════════════════════════════════╝
                                  ↓
                Final report: best (math, algo, metrics) tuple

  关键设计原则:
    (1) Mathematician 只管 *数学*, 输出公式 + Lean stmt, *从不写 Python 代码*.
    (2) Algorithm 只管 *实现*, 把公式翻译成 numpy code. 如果数值崩了 (NaN,
        exception) 它自己 retry; 不向上抛.
    (3) Simulator 只管 *环境 + 度量*, 是 deterministic (无 LLM). 它 classify
        失败是 IMPL_ERROR 还是 MATH_ERROR —— 是整个系统的 "ground truth
        adjudicator".
    (4) Escalation 是显式的: 只有 IMPL_ERROR 在 inner loop 内修, MATH_ERROR
        必须升级到 outer loop 让 Mathematician 重 derive.

  Demo questions (2 道, 都展示不同的 escalation 路径):
    1. variance_estimation:  Round 1 (naive /n biased) → MATH_ERROR escalate
                            → Round 2 (Bessel /(n-1)) → OK
    2. bernoulli_ci:         Round 1 (Wald CI under-covers) → MATH_ERROR
                            → Round 2 (Wilson CI) → OK
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

# parents[1] == "AI Statistician/" (workspace root, one level above this file).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

import anthropic              # noqa: E402
import numpy as np             # noqa: E402
import scipy.stats             # noqa: E402
from axle import AxleClient    # noqa: E402

LEAN_ENV = "lean-4.29.0"
DEFAULT_MODEL = "claude-haiku-4-5"
N_MC_RUNS = 2_000
MAX_OUTER_ROUNDS = 2   # Mathematician escalation 层
MAX_INNER_ROUNDS = 2   # Algorithm-Simulator 修复 impl bug 层


# ═════════════════════════════════════════════════════════════════════════════
# Section 1.  Data classes
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class ResearchQuestion:
    """A statistical research question fed to the system."""
    name: str
    dgp_english: str
    target_english: str
    guarantee_english: str
    true_params: dict
    sampler: Callable[[np.random.Generator, int, dict], np.ndarray]
    n_obs: int


@dataclass
class MathDerivation:
    """MathematicianAgent 的输出 —— *只有数学*, 没有代码."""
    informal_derivation: str       # 自然语言推导
    estimator_formula: str         # math notation, 如 "σ̂² = (1/(n-1)) Σ (xᵢ - x̄)²"
    lean_stmt: str                  # Lean 4 theorem statement (no proof)
    asymp_theorem: str             # "Unbiased; √n(σ̂²−σ²) →_d N(0, 2σ⁴)"
    se_formula_hint: str           # "SE(σ̂²) ≈ σ̂² · √(2/n)" — 给 Algorithm 实现 SE 用


@dataclass
class AlgorithmImpl:
    """AlgorithmAgent 的输出 —— Python 代码, 实现 MathDerivation 的公式."""
    python_code: str               # 可 exec, 定义 estimate(data) → dict
    notes: str                     # "用 Welford 算法保证 numerical stability" 等
    inner_iteration: int           # 这是 inner loop 第几次产出


class ErrorType(Enum):
    """Simulator 把失败分两类, 驱动 escalation."""
    OK = "OK"
    IMPL_ERROR = "IMPL_ERROR"      # 算法实现 bug, Algorithm 该 fix
    MATH_ERROR = "MATH_ERROR"      # 估计量本身的 math 问题, Mathematician 该改


@dataclass
class SimulationMetrics:
    n_runs: int
    n_failed: int                  # 失败的 replicate 数 (NaN / exception)
    bias: float
    relative_bias: float
    rmse: float
    empirical_se: float
    mean_estimated_se: float
    coverage_95: float


@dataclass
class SimulationResult:
    metrics: SimulationMetrics | None
    error_type: ErrorType
    feedback_for_algorithm: str | None  # 只有 IMPL_ERROR 才填
    feedback_for_mathematician: str | None  # 只有 MATH_ERROR 才填
    raw_exception: str | None = None    # 如果是 IMPL_ERROR by exception


@dataclass
class RoundRecord:
    """一次 outer iteration 的完整记录."""
    outer_idx: int
    math: MathDerivation
    lean_typecheck_ok: bool
    inner_attempts: list[tuple[AlgorithmImpl, SimulationResult]] = field(default_factory=list)
    final_result: SimulationResult | None = None
    timing_s: float = 0.0


@dataclass
class FinalReport:
    question_name: str
    rounds: list[RoundRecord]
    final_status: str              # "CONVERGED" | "MAX_ROUNDS_REACHED" | "FAILED"


# ═════════════════════════════════════════════════════════════════════════════
# Section 2.  MathematicianAgent —— 只输出数学
# ═════════════════════════════════════════════════════════════════════════════


MATHEMATICIAN_SYS = """\
You are a mathematical statistician. Given a research question (DGP + target +
desired guarantee), derive an estimator and its asymptotic guarantee.

CRITICAL: You output MATH ONLY. Do NOT write Python code — that is done by a
separate Algorithm Agent. Your job is the *what*, not the *how*.

Output EXACTLY in this format (each block delimited by `---FIELD---` markers):

---INFORMAL---
<2-3 sentence informal derivation of why this estimator works>

---FORMULA---
<single-line math notation, e.g. σ̂² = (1/(n-1))·Σᵢ(xᵢ - x̄)²>

---SE_HINT---
<single-line formula for SE/CI construction, e.g. SE(σ̂²) ≈ σ̂²·√(2/n), CI = σ̂² ± 1.96·SE>

---LEAN_STMT---
<a Lean 4 + Mathlib theorem statement (ending `:= by sorry`)
 capturing the asymptotic guarantee. Keep types simple.>

---ASYMP_THM---
<one-line English statement of the guarantee, e.g.
 "E[σ̂²] = σ² (unbiased); √n(σ̂² - σ²) →_d N(0, 2σ⁴)">

---END---
"""


class MathematicianAgent:
    def __init__(self, axle: AxleClient, llm_mode: str = "anthropic"):
        self.axle = axle
        self.llm_mode = llm_mode
        # Token tracking (for architecture comparison harness).
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        if llm_mode == "anthropic":
            self._claude = anthropic.Anthropic()

    async def derive(
        self,
        question: ResearchQuestion,
        prev_math_feedback: str | None,
    ) -> MathDerivation:
        if self.llm_mode == "mock":
            return self._mock_derive(question, prev_math_feedback)

        user_msg = self._build_prompt(question, prev_math_feedback)

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=900,
                system=MATHEMATICIAN_SYS,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        self.total_input_tokens += resp.usage.input_tokens
        self.total_output_tokens += resp.usage.output_tokens
        return self._parse(resp.content[0].text)

    async def verify_lean_typecheck(self, lean_stmt: str) -> bool:
        try:
            content = lean_stmt if "import" in lean_stmt else "import Mathlib\n\n" + lean_stmt
            r = await self.axle.check(content=content, environment=LEAN_ENV,
                                       ignore_imports=True)
            errs = list(getattr(getattr(r, "lean_messages", None), "errors", []) or [])
            return len(errs) == 0
        except Exception:
            return False

    @staticmethod
    def _build_prompt(q: ResearchQuestion, fb: str | None) -> str:
        msg = (
            f"RESEARCH QUESTION:\n"
            f"  Name:      {q.name}\n"
            f"  DGP:       {q.dgp_english}\n"
            f"  Target:    {q.target_english}\n"
            f"  Guarantee: {q.guarantee_english}\n"
            f"  Sample size n = {q.n_obs}\n"
        )
        if fb:
            msg += (
                f"\nFEEDBACK FROM SIMULATION (your previous estimator had a math issue):\n"
                f"  {fb}\n"
                f"\nPropose a *refined* estimator that addresses this issue."
            )
        else:
            msg += "\nThis is round 1. Propose your initial estimator."
        return msg

    @staticmethod
    def _parse(text: str) -> MathDerivation:
        def grab(field: str) -> str:
            m = re.search(rf"---{field}---\s*(.+?)\s*---", text, re.DOTALL)
            return m.group(1).strip() if m else ""

        return MathDerivation(
            informal_derivation=grab("INFORMAL"),
            estimator_formula=grab("FORMULA"),
            se_formula_hint=grab("SE_HINT"),
            lean_stmt=grab("LEAN_STMT"),
            asymp_theorem=grab("ASYMP_THM"),
        )

    @staticmethod
    def _mock_derive(q: ResearchQuestion, fb: str | None) -> MathDerivation:
        if "variance" in q.name:
            unbiased = fb is not None
            denom = "n - 1" if unbiased else "n"
            return MathDerivation(
                informal_derivation=(
                    f"Sample variance with denominator {denom}. "
                    f"{'Bessel-corrected (unbiased).' if unbiased else 'Naive MLE form.'}"
                ),
                estimator_formula=f"σ̂² = (1/({denom})) · Σᵢ(xᵢ - x̄)²",
                se_formula_hint=f"SE(σ̂²) ≈ σ̂² · √(2/n); CI = σ̂² ± 1.96 · SE",
                lean_stmt="theorem mock_var_stmt : (1 : Nat) = 1 := by rfl",
                asymp_theorem=(
                    "E[σ̂²] = σ² (unbiased); √n(σ̂² - σ²) →_d N(0, 2σ⁴)"
                    if unbiased else
                    "E[σ̂²] = (n-1)/n · σ² (BIASED by factor (n-1)/n)"
                ),
            )
        else:  # bernoulli
            wilson = fb is not None
            method = "Wilson score" if wilson else "Wald"
            return MathDerivation(
                informal_derivation=(
                    f"{method} CI for Bernoulli p. "
                    f"{'Wilson handles small p / small n correctly.' if wilson else 'Asymptotic normal approximation.'}"
                ),
                estimator_formula=(
                    "p̂_W = (X̄ + z²/(2n)) / (1 + z²/n); CI = [p̂_W ± z·SE_W]"
                    if wilson else
                    "p̂ = X̄ = (1/n) Σᵢ Xᵢ; CI = p̂ ± 1.96·√(p̂(1-p̂)/n)"
                ),
                se_formula_hint=(
                    "SE_W = √(p̂(1-p̂)/n + z²/(4n²)) / (1 + z²/n)"
                    if wilson else
                    "SE = √(p̂(1-p̂)/n)"
                ),
                lean_stmt="theorem mock_bern_stmt : (1 : Nat) = 1 := by rfl",
                asymp_theorem=f"{method} CI nominally achieves 95% coverage",
            )


# ═════════════════════════════════════════════════════════════════════════════
# Section 3.  AlgorithmAgent —— 把数学公式翻译成 Python
# ═════════════════════════════════════════════════════════════════════════════


ALGORITHM_SYS = """\
You are a numerical algorithms engineer. The Mathematician Agent has derived a
statistical estimator (formula + SE + asymptotic guarantee). Your job: write a
Python function `estimate(data)` that computes the estimator on a 1-D numpy
array, returning {'estimate', 'se', 'ci_lo', 'ci_hi'} (all floats).

CRITICAL constraints:
  • Only use `np` (numpy) and `scipy.stats` — both are in scope.
  • No I/O, no prints, no imports.
  • Handle edge cases (e.g., p̂ = 0 or p̂ = 1 for Bernoulli).
  • Return floats, not arrays.

Output EXACTLY this format:
---CODE---
def estimate(data: np.ndarray) -> dict:
    # your implementation
    ...
    return {'estimate': ..., 'se': ..., 'ci_lo': ..., 'ci_hi': ...}
---NOTES---
<1-2 sentence note about implementation choices (e.g. "uses Welford for numerical
 stability", "clips p̂ to (1e-9, 1-1e-9) to avoid log(0)")>
---END---

If you are given prior IMPL_ERROR feedback, your new code MUST fix that specific
error.
"""


class AlgorithmAgent:
    def __init__(self, llm_mode: str = "anthropic"):
        self.llm_mode = llm_mode
        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        if llm_mode == "anthropic":
            self._claude = anthropic.Anthropic()

    async def implement(
        self,
        math: MathDerivation,
        prev_impl_feedback: str | None,
        iteration: int,
    ) -> AlgorithmImpl:
        if self.llm_mode == "mock":
            return self._mock_implement(math, iteration)

        user_msg = (
            f"MATHEMATICIAN'S ESTIMATOR:\n"
            f"  Formula: {math.estimator_formula}\n"
            f"  SE/CI:   {math.se_formula_hint}\n"
            f"  Guarantee: {math.asymp_theorem}\n"
            f"  Informal: {math.informal_derivation}\n"
        )
        if prev_impl_feedback:
            user_msg += (
                f"\nPRIOR IMPLEMENTATION ERROR (you must fix this):\n"
                f"  {prev_impl_feedback}\n"
            )

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=700,
                system=ALGORITHM_SYS,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        self.total_input_tokens += resp.usage.input_tokens
        self.total_output_tokens += resp.usage.output_tokens
        return self._parse(resp.content[0].text, iteration)

    @staticmethod
    def _parse(text: str, iteration: int) -> AlgorithmImpl:
        m_code = re.search(r"---CODE---\s*(.+?)\s*---NOTES---", text, re.DOTALL)
        m_notes = re.search(r"---NOTES---\s*(.+?)\s*---END---", text, re.DOTALL)
        code = m_code.group(1).strip() if m_code else ""
        notes = m_notes.group(1).strip() if m_notes else ""
        return AlgorithmImpl(python_code=code, notes=notes, inner_iteration=iteration)

    @staticmethod
    def _mock_implement(math: MathDerivation, iteration: int) -> AlgorithmImpl:
        """Mock: produces canonical Python for variance / Bernoulli based on formula text."""
        formula = math.estimator_formula
        if "σ̂²" in formula or "sigma" in formula.lower() or "variance" in formula.lower():
            unbiased = "n - 1" in formula or "(n-1)" in formula
            denom = "(n - 1)" if unbiased else "n"
            code = (
                "def estimate(data):\n"
                "    n = len(data); mean = float(np.mean(data))\n"
                f"    est = float(np.sum((data - mean)**2) / {denom})\n"
                "    se = est * np.sqrt(2.0 / n)\n"
                "    return {'estimate': est, 'se': se,\n"
                "            'ci_lo': est - 1.96*se, 'ci_hi': est + 1.96*se}"
            )
            return AlgorithmImpl(
                python_code=code,
                notes=f"Direct implementation of {denom}-denominator sample variance",
                inner_iteration=iteration,
            )
        else:  # bernoulli
            wilson = "Wilson" in formula or "z²" in formula
            if wilson:
                code = (
                    "def estimate(data):\n"
                    "    n = len(data); p = float(np.mean(data)); z = 1.96\n"
                    "    denom = 1 + z**2/n\n"
                    "    center = (p + z**2/(2*n)) / denom\n"
                    "    half = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom\n"
                    "    se = half / z\n"
                    "    return {'estimate': p, 'se': se,\n"
                    "            'ci_lo': center - half, 'ci_hi': center + half}"
                )
                notes = "Wilson score interval, robust for small p / small n"
            else:
                code = (
                    "def estimate(data):\n"
                    "    n = len(data); p = float(np.mean(data))\n"
                    "    se = float(np.sqrt(max(p*(1-p), 1e-12) / n))\n"
                    "    return {'estimate': p, 'se': se,\n"
                    "            'ci_lo': p - 1.96*se, 'ci_hi': p + 1.96*se}"
                )
                notes = "Naive Wald CI, fragile for small p"
            return AlgorithmImpl(python_code=code, notes=notes, inner_iteration=iteration)


# ═════════════════════════════════════════════════════════════════════════════
# Section 4.  SimulatorAgent —— deterministic 环境管理 + 度量 + 分类
# ═════════════════════════════════════════════════════════════════════════════
# 注意: 这一层 *没有 LLM*. 它是 ground-truth adjudicator, 必须 deterministic
# 才能信. 它的 IMPL_ERROR vs MATH_ERROR 分类驱动整个系统的 escalation.


class SimulatorAgent:
    def __init__(self, n_runs: int = N_MC_RUNS, seed: int = 42):
        self.n_runs = n_runs
        self.seed = seed

    def build_environment(self, q: ResearchQuestion) -> dict:
        """Configure DGP environment (rng + true target)."""
        return {
            "rng": np.random.default_rng(self.seed),
            "true_target": self._extract_true_target(q),
            "n_obs": q.n_obs,
            "sampler": q.sampler,
            "true_params": q.true_params,
        }

    async def run(self, env: dict, algo: AlgorithmImpl) -> SimulationResult:
        """Execute algorithm in environment, classify outcome."""
        # 1. Sandboxed exec
        ns: dict = {"np": np, "scipy": scipy}
        try:
            exec(algo.python_code, ns)
        except Exception as e:
            return SimulationResult(
                metrics=None, error_type=ErrorType.IMPL_ERROR,
                feedback_for_algorithm=f"Python compilation/exec error: {type(e).__name__}: {e}",
                feedback_for_mathematician=None,
                raw_exception=str(e),
            )
        if "estimate" not in ns:
            return SimulationResult(
                metrics=None, error_type=ErrorType.IMPL_ERROR,
                feedback_for_algorithm="Your code did not define `estimate(data)`. "
                                       "Make sure the function name is exactly `estimate`.",
                feedback_for_mathematician=None,
            )
        estimate_fn = ns["estimate"]

        # 2. Run MC replicates
        rng, sampler = env["rng"], env["sampler"]
        n_obs, params = env["n_obs"], env["true_params"]
        true_target = env["true_target"]

        ests: list[float] = []
        ses: list[float] = []
        cis_contain: list[bool] = []
        last_exc: str | None = None
        n_failed = 0

        for _ in range(self.n_runs):
            data = sampler(rng, n_obs, params)
            try:
                r = estimate_fn(data)
                est = float(r["estimate"]); se = float(r.get("se", float("nan")))
                ci_lo = float(r["ci_lo"]); ci_hi = float(r["ci_hi"])
                if not (np.isfinite(est) and np.isfinite(ci_lo) and np.isfinite(ci_hi)):
                    n_failed += 1; continue
                ests.append(est); ses.append(se)
                cis_contain.append(ci_lo <= true_target <= ci_hi)
            except Exception as e:
                last_exc = f"{type(e).__name__}: {e}"
                n_failed += 1

        # 3. Classify outcomes by failure rate
        if not ests:
            # 所有 replicate 都失败 —— 算法压根不能跑
            return SimulationResult(
                metrics=None, error_type=ErrorType.IMPL_ERROR,
                feedback_for_algorithm=(
                    f"All {self.n_runs} MC replicates failed. "
                    f"Sample error: {last_exc or 'NaN / extreme values returned'}"
                ),
                feedback_for_mathematician=None,
                raw_exception=last_exc,
            )
        fail_rate = n_failed / self.n_runs
        if fail_rate > 0.20:
            # > 20% 失败率 → impl 不稳定
            return SimulationResult(
                metrics=None, error_type=ErrorType.IMPL_ERROR,
                feedback_for_algorithm=(
                    f"{fail_rate * 100:.0f}% of MC replicates failed "
                    f"(likely numerical instability). Sample error: {last_exc}"
                ),
                feedback_for_mathematician=None,
                raw_exception=last_exc,
            )

        # 4. Compute metrics on successful replicates
        ests_arr = np.array(ests); ses_arr = np.array(ses)
        ses_valid = ses_arr[np.isfinite(ses_arr)]
        bias = float(np.mean(ests_arr) - true_target)
        relbias = bias / true_target if abs(true_target) > 1e-12 else float("nan")
        rmse = float(np.sqrt(np.mean((ests_arr - true_target) ** 2)))
        emp_se = float(np.std(ests_arr))
        mean_est_se = float(np.mean(ses_valid)) if len(ses_valid) > 0 else float("nan")
        coverage = float(np.mean(cis_contain))

        metrics = SimulationMetrics(
            n_runs=len(ests), n_failed=n_failed, bias=bias, relative_bias=relbias,
            rmse=rmse, empirical_se=emp_se, mean_estimated_se=mean_est_se,
            coverage_95=coverage,
        )

        # 5. Diagnose: math problem vs ok
        math_issues = self._diagnose_math(metrics)
        if not math_issues:
            return SimulationResult(
                metrics=metrics, error_type=ErrorType.OK,
                feedback_for_algorithm=None,
                feedback_for_mathematician=None,
            )
        return SimulationResult(
            metrics=metrics, error_type=ErrorType.MATH_ERROR,
            feedback_for_algorithm=None,
            feedback_for_mathematician=" ".join(math_issues),
        )

    @staticmethod
    def _extract_true_target(q: ResearchQuestion) -> float:
        if "variance" in q.name:
            return q.true_params["sigma_sq"]
        if "bernoulli" in q.name:
            return q.true_params["p"]
        return float(next(iter(q.true_params.values())))

    @staticmethod
    def _diagnose_math(m: SimulationMetrics) -> list[str]:
        issues: list[str] = []
        if not np.isnan(m.relative_bias) and abs(m.relative_bias) > 0.03:
            direction = "high" if m.relative_bias > 0 else "low"
            issues.append(
                f"BIAS detected: relative bias = {m.relative_bias:+.3f} "
                f"({direction} by {abs(m.relative_bias)*100:.1f}%). "
                f"The estimator's mathematical form has a systematic offset — "
                f"check normalization constants (e.g., denominator), centering."
            )
        if (not np.isnan(m.mean_estimated_se) and m.empirical_se > 0
                and abs(m.mean_estimated_se - m.empirical_se) / m.empirical_se > 0.10):
            issues.append(
                f"SE FORMULA WRONG: mean SE = {m.mean_estimated_se:.4f}, "
                f"empirical SE = {m.empirical_se:.4f} (>10% gap). "
                f"The asymptotic variance formula doesn't match reality — "
                f"derive a sharper variance expression or use exact distribution."
            )
        if m.coverage_95 < 0.91:
            issues.append(
                f"CI UNDER-COVERS: empirical coverage = {m.coverage_95:.3f} < 0.91. "
                f"The 95% interval is too narrow — try a different CI method "
                f"(Wilson score, profile likelihood, or exact)."
            )
        return issues


# ═════════════════════════════════════════════════════════════════════════════
# Section 5.  Coordinator —— nested loop driver
# ═════════════════════════════════════════════════════════════════════════════


async def research_one(
    question: ResearchQuestion,
    math_agent: MathematicianAgent,
    algo_agent: AlgorithmAgent,
    sim_agent: SimulatorAgent,
    max_outer: int = MAX_OUTER_ROUNDS,
    max_inner: int = MAX_INNER_ROUNDS,
) -> FinalReport:
    """The 3-agent nested loop."""
    print(f"\n{'═' * 78}")
    print(f"  RESEARCH QUESTION: {question.name}")
    print(f"  DGP:       {question.dgp_english}")
    print(f"  Target:    {question.target_english}")
    print(f"  Guarantee: {question.guarantee_english}")
    print(f"  n = {question.n_obs}, MC runs = {sim_agent.n_runs}")
    print('═' * 78)

    rounds: list[RoundRecord] = []
    math_feedback: str | None = None

    for outer_idx in range(1, max_outer + 1):
        print(f"\n┌── OUTER ROUND {outer_idx}/{max_outer} ─────────────────────────────────")
        round_t0 = time.monotonic()

        # ─── (1) Mathematician derives ───────────────────────────────────────
        print("│ [Mathematician] deriving estimator…")
        math = await math_agent.derive(question, math_feedback)
        print(f"│   formula:  {math.estimator_formula}")
        print(f"│   SE hint:  {math.se_formula_hint[:80]}")
        print(f"│   asymp:    {math.asymp_theorem[:80]}")

        # ─── (2) AXLE type-checks Lean stmt ──────────────────────────────────
        print("│ [AXLE check] type-checking Lean statement…")
        lean_ok = await math_agent.verify_lean_typecheck(math.lean_stmt)
        print(f"│   Lean stmt {'✓ type-checks' if lean_ok else '✗ ill-typed (continuing)'}")

        # ─── (3) Inner loop: Algorithm ↔ Simulator ───────────────────────────
        env = sim_agent.build_environment(question)
        round_record = RoundRecord(
            outer_idx=outer_idx, math=math, lean_typecheck_ok=lean_ok,
        )
        impl_feedback: str | None = None
        final_result: SimulationResult | None = None

        for inner_idx in range(1, max_inner + 1):
            print(f"│ ┌── INNER {inner_idx}/{max_inner} ─────────────────────────")
            print(f"│ │ [Algorithm] implementing formula in Python…")
            impl = await algo_agent.implement(math, impl_feedback, inner_idx)
            print(f"│ │   notes: {impl.notes[:80]}")

            print(f"│ │ [Simulator] running {sim_agent.n_runs:,} MC replicates…")
            result = await sim_agent.run(env, impl)
            round_record.inner_attempts.append((impl, result))

            if result.metrics is not None:
                m = result.metrics
                print(f"│ │   bias={m.bias:+.4f} (rel: {m.relative_bias:+.3f}), "
                      f"RMSE={m.rmse:.4f}")
                print(f"│ │   emp.SE={m.empirical_se:.4f}, est.SE={m.mean_estimated_se:.4f}, "
                      f"cov={m.coverage_95:.3f}")
                if m.n_failed > 0:
                    print(f"│ │   (n_failed = {m.n_failed}/{sim_agent.n_runs})")

            tag = {ErrorType.OK: "✓ OK",
                   ErrorType.IMPL_ERROR: "✗ IMPL_ERROR",
                   ErrorType.MATH_ERROR: "✗ MATH_ERROR"}[result.error_type]
            print(f"│ │ [Simulator] classified: {tag}")

            if result.error_type == ErrorType.OK:
                final_result = result
                print(f"│ └── inner done: algorithm + math both fine")
                break
            elif result.error_type == ErrorType.IMPL_ERROR:
                impl_feedback = result.feedback_for_algorithm
                print(f"│ │   → ALGO RETRY with feedback: "
                      f"{(impl_feedback or '')[:80]}")
                if inner_idx == max_inner:
                    print(f"│ └── inner max reached, impl still broken")
                    final_result = result
            else:  # MATH_ERROR
                final_result = result
                print(f"│ └── inner done: algo OK but MATH_ERROR — will escalate")
                break

        round_record.final_result = final_result
        round_record.timing_s = time.monotonic() - round_t0
        rounds.append(round_record)

        if final_result and final_result.error_type == ErrorType.OK:
            print(f"└── OUTER ROUND {outer_idx} ✅ CONVERGED ({round_record.timing_s:.1f}s)")
            return FinalReport(question_name=question.name, rounds=rounds,
                               final_status="CONVERGED")

        if final_result and final_result.error_type == ErrorType.MATH_ERROR:
            math_feedback = final_result.feedback_for_mathematician
            print(f"└── OUTER ROUND {outer_idx} 🔺 ESCALATING TO MATHEMATICIAN")
            print(f"     feedback: {(math_feedback or '')[:120]}")
        else:
            print(f"└── OUTER ROUND {outer_idx} ✗ FAILED (algorithm couldn't be fixed)")

    print(f"\n  ⚠️  Reached max_outer={max_outer} without convergence.")
    return FinalReport(question_name=question.name, rounds=rounds,
                       final_status="MAX_ROUNDS_REACHED")


# ═════════════════════════════════════════════════════════════════════════════
# Section 6.  Demo research questions
# ═════════════════════════════════════════════════════════════════════════════


def _sampler_normal(rng: np.random.Generator, n: int, p: dict) -> np.ndarray:
    return rng.normal(p["mu"], np.sqrt(p["sigma_sq"]), size=n)


def _sampler_bernoulli(rng: np.random.Generator, n: int, p: dict) -> np.ndarray:
    return rng.binomial(1, p["p"], size=n).astype(float)


DEMO_QUESTIONS = [
    ResearchQuestion(
        name="variance_estimation",
        dgp_english="X_1, …, X_n i.i.d. ~ N(μ=0, σ²=4),  with n=30",
        target_english="Estimate σ²",
        guarantee_english="Want UNBIASED + asymptotically normal estimator with valid 95% CI",
        true_params={"mu": 0.0, "sigma_sq": 4.0},
        sampler=_sampler_normal,
        n_obs=30,
    ),
    ResearchQuestion(
        name="bernoulli_ci",
        dgp_english="X_1, …, X_n i.i.d. ~ Bernoulli(p=0.05) (rare event, n=30)",
        target_english="Estimate p with 95% confidence interval",
        guarantee_english="Want CI with actual coverage ≥ 0.92 (close to nominal 95%)",
        true_params={"p": 0.05},
        sampler=_sampler_bernoulli,
        n_obs=30,
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
# Section 7.  CLI main
# ═════════════════════════════════════════════════════════════════════════════


async def main_async(question_filter: str | None, mock: bool,
                     max_outer: int, max_inner: int) -> None:
    llm_mode = "mock" if mock else "anthropic"
    async with AxleClient(api_key=os.environ["AXLE_API_KEY"]) as axle:
        math_agent = MathematicianAgent(axle, llm_mode=llm_mode)
        algo_agent = AlgorithmAgent(llm_mode=llm_mode)
        sim_agent = SimulatorAgent()

        questions = DEMO_QUESTIONS
        if question_filter:
            questions = [q for q in questions if question_filter in q.name]
            if not questions:
                print(f"No question matching {question_filter!r}", file=sys.stderr)
                sys.exit(1)

        reports: list[FinalReport] = []
        for q in questions:
            r = await research_one(q, math_agent, algo_agent, sim_agent,
                                    max_outer, max_inner)
            reports.append(r)

        print("\n" + "═" * 78)
        print("  FINAL SUMMARY")
        print("═" * 78)
        for r in reports:
            badge = {"CONVERGED": "✅", "MAX_ROUNDS_REACHED": "⚠️ ",
                     "FAILED": "❌"}.get(r.final_status, "?")
            n_outer = len(r.rounds)
            n_inner_total = sum(len(rd.inner_attempts) for rd in r.rounds)
            print(f"  {badge} {r.question_name:24s}  "
                  f"status={r.final_status:20s}  "
                  f"outer={n_outer}, inner_total={n_inner_total}")
            if r.rounds and r.rounds[-1].final_result and r.rounds[-1].final_result.metrics:
                m = r.rounds[-1].final_result.metrics
                print(f"      └─ final: bias={m.bias:+.3f}, RMSE={m.rmse:.3f}, "
                      f"coverage={m.coverage_95:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="3-agent statistical research loop (Math ↔ Algo ↔ Sim)"
    )
    parser.add_argument("--demo", action="store_true", help="run built-in 2 questions")
    parser.add_argument("--q", help="only run questions whose name contains this string")
    parser.add_argument("--mock", action="store_true",
                        help="use mock LLM (no Anthropic calls)")
    parser.add_argument("--max-outer", type=int, default=MAX_OUTER_ROUNDS)
    parser.add_argument("--max-inner", type=int, default=MAX_INNER_ROUNDS)
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    for noisy in ("httpx", "httpcore", "anthropic", "axle"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    asyncio.run(main_async(args.q, args.mock, args.max_outer, args.max_inner))


if __name__ == "__main__":
    main()


# ═════════════════════════════════════════════════════════════════════════════
# Pitch handle (interview 时背下来)
# ═════════════════════════════════════════════════════════════════════════════
#
#   "Three agents, two nested loops, clean separation of concerns:
#
#    MATHEMATICIAN     —  Math only. Formula + Lean stmt + asymptotic guarantee.
#                         Never writes code.
#    ALGORITHM         —  Code only. Translates math formula to numpy. Iterates
#                         with simulator to fix implementation bugs.
#    SIMULATOR         —  Deterministic. Builds DGP environment, runs algorithm,
#                         CLASSIFIES failure: IMPL_ERROR (algo bug) vs MATH_ERROR
#                         (estimator wrong). This classification is the *load-
#                         bearing* design — it decides escalation direction.
#
#    INNER LOOP  (Algorithm ↔ Simulator):  fixes implementation bugs locally.
#    OUTER LOOP  (Mathematician ↔ rest):   only triggered when simulator confirms
#                                          the issue is mathematical.
#
#    Pitch line: 'Production-grade AI statistician needs THIS separation —
#    otherwise a single LLM blames math for what's really an array indexing bug,
#    or rewrites code when the problem is the estimator is fundamentally biased.'"
#
# ═════════════════════════════════════════════════════════════════════════════
