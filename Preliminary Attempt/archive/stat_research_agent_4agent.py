"""
================================================================================
  stat_research_agent_4agent.py — 4-agent specialization
  把数学层进一步切成「informal theory」+「formal Lean verifier」
================================================================================

  Architecture (4 agents + 3 nested loops):

      ┌─────────────────────────────────────────────────────────────────────┐
      │ OUTER LOOP — Theory escalation (max 2 rounds)                       │
      │                                                                     │
      │   ┌────────────────────────────────────┐                            │
      │   │ 1. TheoryDeveloperAgent            │                            │
      │   │    • informal mathematical reasoning                            │
      │   │    • English formula + asymp claim │                            │
      │   │    NO Lean, NO Python              │                            │
      │   └─────────────────┬──────────────────┘                            │
      │                     │ informal math                                 │
      │                     ▼                                               │
      │   ╔══════════════════════════════════════════════════════════════╗  │
      │   ║ FORMALIZATION SUB-LOOP (max 2 attempts)                      ║  │
      │   ║   ┌────────────────────────────────┐                         ║  │
      │   ║   │ 2. FormalVerifierAgent         │                         ║  │
      │   ║   │    • English → Lean theorem    │                         ║  │
      │   ║   │    • AXLE type-checks          │                         ║  │
      │   ║   │    • Retries on ill-typed      │                         ║  │
      │   ║   └────────────────────────────────┘                         ║  │
      │   ╚══════════════════════════════════════════════════════════════╝  │
      │                     │ verified Lean stmt + math                    │
      │                     ▼                                               │
      │   ╔══════════════════════════════════════════════════════════════╗  │
      │   ║ INNER LOOP — Algorithm ↔ Simulator (max 2 retries)           ║  │
      │   ║   ┌─────────────────┐  code   ┌──────────────────┐           ║  │
      │   ║   │ 3. AlgorithmEng │ ──────► │ 4. SimulatorAgent│           ║  │
      │   ║   │    (Python)     │ ◄────── │   (det. judge)   │           ║  │
      │   ║   └─────────────────┘ feedback└──────────────────┘           ║  │
      │   ║   IMPL_ERROR → algo retries; MATH_ERROR → escalate to Theory ║  │
      │   ╚══════════════════════════════════════════════════════════════╝  │
      └─────────────────────────────────────────────────────────────────────┘

  跟 3-agent 的区别:
    • Theory ≠ Formal: 信息流是 "informal English → Lean syntax". 错的地方可
      以更精准定位 (theory 错? Lean translation 错?).
    • 可以 swap 模型: TheoryDeveloper 用大模型 (math reasoning),
      FormalVerifier 用小/微调过的 Lean 模型, AlgorithmEngineer 用 code 模型.
    • 失败回退路径更细: 3 个 retry 边界 (algo / formal / theory).

  代价:
    • LLM 调用数 ↑ (4 步 vs 3 步)
    • 协调复杂度 ↑
    • 信息可能在 informal→formal 翻译中漏失

  这个 file 就是给 `compare_architectures.py` 跑 head-to-head 用的.
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Archived file: parent dir contains the production 3-agent code we re-use.
ARCHIVE_DIR = Path(__file__).resolve().parent
PARENT_DIR = ARCHIVE_DIR.parent
PROJECT_ROOT = ARCHIVE_DIR.parents[3]
sys.path.insert(0, str(PARENT_DIR))
load_dotenv(PROJECT_ROOT / ".env")

import anthropic              # noqa: E402
import numpy as np             # noqa: E402
from axle import AxleClient    # noqa: E402

# Re-use everything from 3-agent: question types, simulator, error types.
from stat_research_agent import (
    ResearchQuestion, DEMO_QUESTIONS, ErrorType,
    SimulationResult, SimulatorAgent, AlgorithmAgent, AlgorithmImpl,
    LEAN_ENV, DEFAULT_MODEL, N_MC_RUNS,
    MAX_OUTER_ROUNDS, MAX_INNER_ROUNDS,
)

MAX_INNER_FORMAL = 1  # FormalVerifier 最多 retry 几次 (1 = 初始 + 1 retry = 2 attempts)


# ═════════════════════════════════════════════════════════════════════════════
# Section 1.  Data classes
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class TheoryOutput:
    """TheoryDeveloperAgent 的输出 —— 纯英文数学描述, 无 Lean, 无代码."""
    informal_derivation: str
    estimator_formula: str         # math notation (LaTeX-ish, English/symbols)
    se_formula_hint: str
    asymp_theorem: str             # English-only statement of guarantee


@dataclass
class FormalOutput:
    """FormalVerifierAgent 的输出 —— Lean 形式化 + AXLE 校验结果."""
    lean_stmt: str
    lean_typecheck_ok: bool
    formal_notes: str              # 解释 Lean stmt 如何 capture asymp claim
    inner_iteration: int           # 第几次尝试


@dataclass
class RoundRecord4:
    outer_idx: int
    theory: TheoryOutput
    formal: FormalOutput
    formal_attempts: int           # 总共 FormalVerifier 调用次数
    inner_attempts: list[tuple[AlgorithmImpl, SimulationResult]] = field(default_factory=list)
    final_result: SimulationResult | None = None
    timing_s: float = 0.0


@dataclass
class FinalReport4:
    question_name: str
    architecture: str = "4-agent"
    rounds: list[RoundRecord4] = field(default_factory=list)
    final_status: str = "UNKNOWN"


# ═════════════════════════════════════════════════════════════════════════════
# Section 2.  TheoryDeveloperAgent —— 纯 informal 数学
# ═════════════════════════════════════════════════════════════════════════════


THEORY_SYS = """\
You are a research statistician. Given a research question (DGP + estimation
target + desired guarantee), derive an estimator using pure informal mathematics.

CRITICAL: You output ENGLISH MATH ONLY. No Lean syntax, no Python code.
Your job is the *mathematical idea*: what estimator, why does it work, what's
the asymptotic guarantee.

Output EXACTLY in this format:

---INFORMAL---
<2-3 sentence informal derivation: what estimator, why does it solve the question>

---FORMULA---
<single-line math notation, e.g. σ̂² = (1/(n-1)) Σᵢ(xᵢ - x̄)²>

---SE_HINT---
<single-line SE/CI formula, e.g. SE(σ̂²) ≈ σ̂²·√(2/n); CI = σ̂² ± 1.96·SE>

---ASYMP_THM---
<one-line English asymptotic claim, e.g.
 "E[σ̂²] = σ² (unbiased); √n(σ̂² - σ²) →_d N(0, 2σ⁴)">

---END---

If feedback from prior round indicates a math issue (bias, wrong SE, low
coverage), revise your math — pick a different estimator or different SE
formula. Do NOT just rewrite the same answer.
"""


class TheoryDeveloperAgent:
    def __init__(self):
        self._claude = anthropic.Anthropic()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def derive(
        self, question: ResearchQuestion, prev_math_feedback: str | None,
    ) -> TheoryOutput:
        user_msg = self._build_prompt(question, prev_math_feedback)

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL, max_tokens=600,
                system=THEORY_SYS,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        self.total_input_tokens += resp.usage.input_tokens
        self.total_output_tokens += resp.usage.output_tokens
        return self._parse(resp.content[0].text)

    @staticmethod
    def _build_prompt(q: ResearchQuestion, fb: str | None) -> str:
        msg = (
            f"RESEARCH QUESTION:\n"
            f"  DGP:       {q.dgp_english}\n"
            f"  Target:    {q.target_english}\n"
            f"  Guarantee: {q.guarantee_english}\n"
            f"  n = {q.n_obs}\n"
        )
        if fb:
            msg += (
                f"\nFEEDBACK FROM LAST ROUND (mathematical issue detected):\n  {fb}\n"
                f"\nRevise your estimator (different formula or SE) to address this."
            )
        else:
            msg += "\nFirst round. Propose your initial estimator (informal math)."
        return msg

    @staticmethod
    def _parse(text: str) -> TheoryOutput:
        def grab(field: str) -> str:
            m = re.search(rf"---{field}---\s*(.+?)\s*---", text, re.DOTALL)
            return m.group(1).strip() if m else ""
        return TheoryOutput(
            informal_derivation=grab("INFORMAL"),
            estimator_formula=grab("FORMULA"),
            se_formula_hint=grab("SE_HINT"),
            asymp_theorem=grab("ASYMP_THM"),
        )


# ═════════════════════════════════════════════════════════════════════════════
# Section 3.  FormalVerifierAgent —— Theory → Lean → AXLE
# ═════════════════════════════════════════════════════════════════════════════


FORMAL_SYS = """\
You are a Lean 4 + Mathlib formalization specialist. The TheoryDeveloper agent
has given you an English asymptotic claim. Your job: translate it into a
*well-typed* Lean 4 theorem statement.

CRITICAL:
  • Output a single Lean theorem ending in `:= by sorry`.
  • Use Mathlib types: `MeasureTheory.Measure`, `ProbabilityTheory.variance`, etc.
  • Keep types simple. Stick to `ℝ`, `ℕ`, `Fin n`, `Measure`.
  • If you don't know the exact Mathlib name, use a reasonable approximation.
  • If you previously produced an ill-typed statement, FIX the specific type error.

Output EXACTLY in this format:

---LEAN_STMT---
<a single Lean 4 + Mathlib theorem statement, ending `:= by sorry`>

---FORMAL_NOTES---
<one sentence explaining how your Lean stmt captures the English claim>

---END---
"""


class FormalVerifierAgent:
    def __init__(self, axle: AxleClient):
        self.axle = axle
        self._claude = anthropic.Anthropic()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def formalize(
        self,
        theory: TheoryOutput,
        prev_ill_typed_attempt: str | None,
        iteration: int,
    ) -> FormalOutput:
        user_msg = (
            f"ENGLISH ASYMPTOTIC CLAIM (from TheoryDeveloper):\n"
            f"  Formula: {theory.estimator_formula}\n"
            f"  Asymp:   {theory.asymp_theorem}\n"
            f"  Informal: {theory.informal_derivation}\n"
        )
        if prev_ill_typed_attempt:
            user_msg += (
                f"\nPRIOR ATTEMPT (was ill-typed by AXLE — fix it):\n"
                f"```lean\n{prev_ill_typed_attempt}\n```\n"
            )

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL, max_tokens=500,
                system=FORMAL_SYS,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        self.total_input_tokens += resp.usage.input_tokens
        self.total_output_tokens += resp.usage.output_tokens
        text = resp.content[0].text

        m_stmt = re.search(r"---LEAN_STMT---\s*(.+?)\s*---FORMAL_NOTES---", text, re.DOTALL)
        m_notes = re.search(r"---FORMAL_NOTES---\s*(.+?)\s*---END---", text, re.DOTALL)
        lean_stmt = m_stmt.group(1).strip() if m_stmt else ""
        notes = m_notes.group(1).strip() if m_notes else ""

        # AXLE type-check
        ok = await self._typecheck(lean_stmt)

        return FormalOutput(
            lean_stmt=lean_stmt, lean_typecheck_ok=ok,
            formal_notes=notes, inner_iteration=iteration,
        )

    async def _typecheck(self, lean_stmt: str) -> bool:
        try:
            content = lean_stmt if "import" in lean_stmt else "import Mathlib\n\n" + lean_stmt
            r = await self.axle.check(content=content, environment=LEAN_ENV,
                                       ignore_imports=True)
            errs = list(getattr(getattr(r, "lean_messages", None), "errors", []) or [])
            return len(errs) == 0
        except Exception:
            return False


# ═════════════════════════════════════════════════════════════════════════════
# Section 4.  AlgorithmEngineerAgent (re-use AlgorithmAgent from 3-agent)
# ═════════════════════════════════════════════════════════════════════════════
# We use the exact same AlgorithmAgent as 3-agent, but feed it TheoryOutput
# instead of MathDerivation (they have the same relevant fields).


def _theory_to_math_adapter(theory: TheoryOutput):
    """Adapter so we can re-use AlgorithmAgent that expects MathDerivation."""
    from stat_research_agent import MathDerivation
    return MathDerivation(
        informal_derivation=theory.informal_derivation,
        estimator_formula=theory.estimator_formula,
        se_formula_hint=theory.se_formula_hint,
        lean_stmt="",   # Algorithm doesn't need this
        asymp_theorem=theory.asymp_theorem,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Section 5.  Coordinator —— 3 nested loops
# ═════════════════════════════════════════════════════════════════════════════


async def research_one_4agent(
    question: ResearchQuestion,
    theory_agent: TheoryDeveloperAgent,
    formal_agent: FormalVerifierAgent,
    algo_agent: AlgorithmAgent,
    sim_agent: SimulatorAgent,
    max_outer: int = MAX_OUTER_ROUNDS,
    max_inner_algo: int = MAX_INNER_ROUNDS,
    max_inner_formal: int = MAX_INNER_FORMAL,
) -> FinalReport4:
    """4-agent nested loop."""
    print(f"\n{'═' * 78}")
    print(f"  [4-AGENT] {question.name}")
    print('═' * 78)

    report = FinalReport4(question_name=question.name)
    math_feedback: str | None = None

    for outer_idx in range(1, max_outer + 1):
        print(f"\n┌── OUTER {outer_idx}/{max_outer} ────────────────────────")
        t0 = time.monotonic()

        # ─── (1) TheoryDeveloper ────────────────────────────────────────
        print(f"│ [1. TheoryDeveloper] deriving informal math…")
        theory = await theory_agent.derive(question, math_feedback)
        print(f"│   formula:  {theory.estimator_formula[:80]}")
        print(f"│   asymp:    {theory.asymp_theorem[:80]}")

        # ─── (2) FormalVerifier (with retry sub-loop) ───────────────────
        print(f"│ [2. FormalVerifier] translating to Lean…")
        formal_out: FormalOutput | None = None
        prev_attempt: str | None = None
        formal_attempts = 0
        for fi in range(1, max_inner_formal + 2):  # max_inner_formal=1 → 2 attempts
            formal_out = await formal_agent.formalize(theory, prev_attempt, fi)
            formal_attempts += 1
            if formal_out.lean_typecheck_ok:
                print(f"│   Lean stmt ✓ type-checks (attempt {fi})")
                break
            print(f"│   Lean stmt ✗ ill-typed (attempt {fi}), retrying…")
            prev_attempt = formal_out.lean_stmt
        else:
            print(f"│   Lean stmt ✗ still ill-typed after {formal_attempts} attempts (continuing)")

        # ─── (3) Inner loop: Algorithm ↔ Simulator ──────────────────────
        round_record = RoundRecord4(
            outer_idx=outer_idx, theory=theory, formal=formal_out,
            formal_attempts=formal_attempts,
        )
        math_adapter = _theory_to_math_adapter(theory)
        env = sim_agent.build_environment(question)
        impl_feedback: str | None = None
        final_result: SimulationResult | None = None

        for ai in range(1, max_inner_algo + 1):
            print(f"│ ┌── INNER {ai}/{max_inner_algo} (algo+sim)")
            print(f"│ │ [3. AlgorithmEngineer] writing Python…")
            impl = await algo_agent.implement(math_adapter, impl_feedback, ai)
            print(f"│ │   notes: {impl.notes[:80]}")

            print(f"│ │ [4. Simulator] running {sim_agent.n_runs} MC replicates…")
            result = await sim_agent.run(env, impl)
            round_record.inner_attempts.append((impl, result))

            if result.metrics is not None:
                m = result.metrics
                print(f"│ │   bias={m.bias:+.4f} (rel: {m.relative_bias:+.3f}), "
                      f"cov={m.coverage_95:.3f}")
            tag = {ErrorType.OK: "✓ OK",
                   ErrorType.IMPL_ERROR: "✗ IMPL_ERROR",
                   ErrorType.MATH_ERROR: "✗ MATH_ERROR"}[result.error_type]
            print(f"│ │ [Simulator] classified: {tag}")

            if result.error_type == ErrorType.OK:
                final_result = result
                print(f"│ └── inner done: OK")
                break
            elif result.error_type == ErrorType.IMPL_ERROR:
                impl_feedback = result.feedback_for_algorithm
                print(f"│ │   → ALGO retry")
                if ai == max_inner_algo:
                    final_result = result
            else:
                final_result = result
                print(f"│ └── MATH_ERROR — escalating")
                break

        round_record.final_result = final_result
        round_record.timing_s = time.monotonic() - t0
        report.rounds.append(round_record)

        if final_result and final_result.error_type == ErrorType.OK:
            print(f"└── OUTER {outer_idx} ✅ CONVERGED ({round_record.timing_s:.1f}s)")
            report.final_status = "CONVERGED"
            return report

        if final_result and final_result.error_type == ErrorType.MATH_ERROR:
            math_feedback = final_result.feedback_for_mathematician
            print(f"└── OUTER {outer_idx} 🔺 ESCALATING TO THEORY")
        else:
            print(f"└── OUTER {outer_idx} ✗ FAILED")

    report.final_status = "MAX_ROUNDS_REACHED"
    return report


# ═════════════════════════════════════════════════════════════════════════════
# Optional: standalone runner (for direct invocation)
# ═════════════════════════════════════════════════════════════════════════════


async def main_async() -> None:
    async with AxleClient(api_key=os.environ["AXLE_API_KEY"]) as axle:
        theory = TheoryDeveloperAgent()
        formal = FormalVerifierAgent(axle)
        algo = AlgorithmAgent(llm_mode="anthropic")
        sim = SimulatorAgent()

        for q in DEMO_QUESTIONS:
            await research_one_4agent(q, theory, formal, algo, sim)


def main() -> None:
    import argparse, logging
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    for noisy in ("httpx", "httpcore", "anthropic", "axle"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
