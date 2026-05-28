"""
================================================================================
  stat_research_agent_2agent.py  — 2-agent (baseline) version
  对比组: Mathematician (does math + code) ↔ Simulator
================================================================================

  This is the *baseline* architecture, written here as the control group for
  `compare_architectures.py`.  It collapses Mathematician + Algorithm into one
  agent, and the Simulator just runs + reports (no IMPL/MATH classification).

  Key differences vs `stat_research_agent.py` (3-agent):
    1. ONE prompt does math AND Python (larger context, more tokens per call)
    2. NO explicit IMPL_ERROR vs MATH_ERROR distinction
    3. NO inner loop — single round per outer iteration
    4. Same Simulator MC logic, same diagnostic thresholds
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

# Archived file: parent dir contains the production 3-agent code we re-use.
ARCHIVE_DIR = Path(__file__).resolve().parent
PARENT_DIR = ARCHIVE_DIR.parent
PROJECT_ROOT = ARCHIVE_DIR.parents[3]
sys.path.insert(0, str(PARENT_DIR))
load_dotenv(PROJECT_ROOT / ".env")

import anthropic              # noqa: E402
import numpy as np             # noqa: E402
import scipy.stats             # noqa: E402
from axle import AxleClient    # noqa: E402

# Re-use ResearchQuestion + DEMO_QUESTIONS from the 3-agent file for fair compare
from stat_research_agent import (
    ResearchQuestion, DEMO_QUESTIONS,
    LEAN_ENV, DEFAULT_MODEL, N_MC_RUNS,
)


# ═════════════════════════════════════════════════════════════════════════════
# Data classes (simpler than 3-agent: one combined output)
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class CombinedProposal:
    """Mathematician's single output: math + code (the 2-agent way)."""
    informal_derivation: str
    estimator_formula: str
    lean_stmt: str
    asymp_theorem: str
    impl_python: str           # ← code goes here, not in separate agent


@dataclass
class SimMetrics:
    n_runs: int
    bias: float
    relative_bias: float
    rmse: float
    empirical_se: float
    mean_estimated_se: float
    coverage_95: float
    diagnosis: str             # "OK" | "NEEDS_FIX" | "FAILED"
    feedback: str              # generic feedback (no IMPL/MATH distinction)


@dataclass
class RoundRecord2:
    round_idx: int
    proposal: CombinedProposal
    metrics: SimMetrics | None
    lean_typecheck_ok: bool
    timing_s: float
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0


@dataclass
class FinalReport2:
    question_name: str
    architecture: str = "2-agent"
    rounds: list[RoundRecord2] = field(default_factory=list)
    final_status: str = "UNKNOWN"


# ═════════════════════════════════════════════════════════════════════════════
# Mathematician-with-code agent
# ═════════════════════════════════════════════════════════════════════════════


MATH_WITH_CODE_SYS = """\
You are a mathematical statistician AND a numerical programmer (combined role).
Given (1) a research question with DGP + target + guarantee, and possibly (2)
feedback from prior simulation, output BOTH the math derivation AND the
Python implementation in a single response.

Output EXACTLY in this format (each block delimited by `---FIELD---` markers):

---INFORMAL---
<2-3 sentence informal derivation of why this estimator works>

---FORMULA---
<single-line math notation of the estimator>

---LEAN_STMT---
<a Lean 4 + Mathlib theorem statement, ending with `:= by sorry`>

---ASYMP_THM---
<one-line English statement of the asymptotic guarantee>

---PYTHON---
def estimate(data: np.ndarray) -> dict:
    # implementation. Return dict with keys: 'estimate' (float),
    # 'se' (float), 'ci_lo' (float), 'ci_hi' (float).
    # `np` and `scipy.stats` are in scope.
    ...
    return {'estimate': ..., 'se': ..., 'ci_lo': ..., 'ci_hi': ...}
---END---
"""


class MathematicianWithCodeAgent:
    def __init__(self, axle: AxleClient):
        self.axle = axle
        self._claude = anthropic.Anthropic()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def propose(
        self,
        question: ResearchQuestion,
        prev_feedback: str | None,
    ) -> tuple[CombinedProposal, int, int]:
        """Returns (proposal, input_tokens, output_tokens)."""
        user_msg = self._build_prompt(question, prev_feedback)

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1200,
                system=MATH_WITH_CODE_SYS,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        in_tok = resp.usage.input_tokens
        out_tok = resp.usage.output_tokens
        self.total_input_tokens += in_tok
        self.total_output_tokens += out_tok
        return self._parse(resp.content[0].text), in_tok, out_tok

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
                f"\nFEEDBACK FROM LAST ROUND:\n  {fb}\n"
                f"\nPropose a *refined* estimator (math + code together) that addresses this."
            )
        else:
            msg += "\nThis is round 1. Propose your initial estimator (math + code together)."
        return msg

    @staticmethod
    def _parse(text: str) -> CombinedProposal:
        def grab(field: str) -> str:
            m = re.search(rf"---{field}---\s*(.+?)\s*---", text, re.DOTALL)
            return m.group(1).strip() if m else ""
        return CombinedProposal(
            informal_derivation=grab("INFORMAL"),
            estimator_formula=grab("FORMULA"),
            lean_stmt=grab("LEAN_STMT"),
            asymp_theorem=grab("ASYMP_THM"),
            impl_python=grab("PYTHON"),
        )


# ═════════════════════════════════════════════════════════════════════════════
# Simple Simulator (no IMPL/MATH distinction — generic "NEEDS_FIX")
# ═════════════════════════════════════════════════════════════════════════════


class SimpleSimulatorAgent:
    def __init__(self, n_runs: int = N_MC_RUNS, seed: int = 42):
        self.n_runs = n_runs
        self.seed = seed

    async def simulate(
        self, question: ResearchQuestion, proposal: CombinedProposal,
    ) -> SimMetrics:
        ns: dict = {"np": np, "scipy": scipy}
        try:
            exec(proposal.impl_python, ns)
        except Exception as e:
            return self._fail(f"exec error: {e}")
        if "estimate" not in ns:
            return self._fail("Python code didn't define `estimate(data)`")

        estimate_fn = ns["estimate"]
        rng = np.random.default_rng(self.seed)
        true_target = self._extract_true(question)

        ests, ses, cis = [], [], []
        for _ in range(self.n_runs):
            data = question.sampler(rng, question.n_obs, question.true_params)
            try:
                r = estimate_fn(data)
                est = float(r["estimate"]); se = float(r.get("se", float("nan")))
                ci_lo = float(r["ci_lo"]); ci_hi = float(r["ci_hi"])
                if not (np.isfinite(est) and np.isfinite(ci_lo) and np.isfinite(ci_hi)):
                    continue
            except Exception:
                continue
            ests.append(est); ses.append(se); cis.append(ci_lo <= true_target <= ci_hi)

        if not ests:
            return self._fail("all replicates failed (NaN / exception)")

        ests_arr = np.array(ests)
        ses_arr = np.array([s for s in ses if not np.isnan(s)])
        bias = float(np.mean(ests_arr) - true_target)
        relbias = bias / true_target if abs(true_target) > 1e-12 else float("nan")
        rmse = float(np.sqrt(np.mean((ests_arr - true_target) ** 2)))
        emp_se = float(np.std(ests_arr))
        mean_est_se = float(np.mean(ses_arr)) if len(ses_arr) > 0 else float("nan")
        cov = float(np.mean(cis))

        issues = []
        if not np.isnan(relbias) and abs(relbias) > 0.03:
            issues.append(f"bias = {relbias:+.3f} ({abs(relbias)*100:.1f}% off)")
        if (not np.isnan(mean_est_se) and emp_se > 0
                and abs(mean_est_se - emp_se) / emp_se > 0.10):
            issues.append(f"SE mismatch: estimated {mean_est_se:.4f} vs empirical {emp_se:.4f}")
        if cov < 0.91:
            issues.append(f"low coverage = {cov:.3f}")

        diagnosis = "OK" if not issues else "NEEDS_FIX"
        # Note: the 2-agent version uses GENERIC feedback (no separation
        # between "your code is wrong" vs "your math is wrong").
        feedback = "Your estimator has issues: " + "; ".join(issues) if issues else "OK"

        return SimMetrics(
            n_runs=len(ests), bias=bias, relative_bias=relbias, rmse=rmse,
            empirical_se=emp_se, mean_estimated_se=mean_est_se,
            coverage_95=cov, diagnosis=diagnosis, feedback=feedback,
        )

    @staticmethod
    def _extract_true(q: ResearchQuestion) -> float:
        if "variance" in q.name:
            return q.true_params["sigma_sq"]
        if "bernoulli" in q.name:
            return q.true_params["p"]
        return float(next(iter(q.true_params.values())))

    @staticmethod
    def _fail(msg: str) -> SimMetrics:
        return SimMetrics(
            n_runs=0, bias=float("nan"), relative_bias=float("nan"),
            rmse=float("nan"), empirical_se=float("nan"),
            mean_estimated_se=float("nan"), coverage_95=float("nan"),
            diagnosis="FAILED", feedback=msg,
        )


# ═════════════════════════════════════════════════════════════════════════════
# Coordinator (simple linear loop, no nested inner)
# ═════════════════════════════════════════════════════════════════════════════


async def research_one_2agent(
    question: ResearchQuestion,
    math_agent: MathematicianWithCodeAgent,
    sim_agent: SimpleSimulatorAgent,
    max_rounds: int = 2,
) -> FinalReport2:
    """2-agent loop: just Math ↔ Sim, no inner."""
    report = FinalReport2(question_name=question.name)
    feedback: str | None = None

    for r_idx in range(1, max_rounds + 1):
        t0 = time.monotonic()
        proposal, in_tok, out_tok = await math_agent.propose(question, feedback)
        lean_ok = await math_agent.verify_lean_typecheck(proposal.lean_stmt)
        metrics = await sim_agent.simulate(question, proposal)
        elapsed = time.monotonic() - t0

        record = RoundRecord2(
            round_idx=r_idx, proposal=proposal, metrics=metrics,
            lean_typecheck_ok=lean_ok, timing_s=elapsed,
            llm_input_tokens=in_tok, llm_output_tokens=out_tok,
        )
        report.rounds.append(record)

        if metrics.diagnosis == "OK":
            report.final_status = "CONVERGED"
            return report
        feedback = metrics.feedback

    report.final_status = "MAX_ROUNDS_REACHED"
    return report
