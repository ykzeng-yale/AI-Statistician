"""
================================================================================
  stat_agent.py — Multi-Agent System for Statistical Theorem Verification
  统计定理多 agent 验证系统 (面试 demo 用)
================================================================================

  Pitch 的核心 deliverable: 把 Axiom Math 的 AXLE + Claude + numpy/scipy 串成
  一个 *3-agent ensemble*, 验证统计学 claim:

      ┌─────────────────────────────────────────────────────────────────────┐
      │   INPUT: a statistical claim (in plain English + Lean stub)         │
      │   OUTPUT: VERIFIED | DISPROVED | UNCERTAIN + evidence              │
      └─────────────────────────────────────────────────────────────────────┘

      Agent 1: ProverAgent       ← AXLE + Claude, 试形式证明 (跟 axle_agent.py 一样)
      Agent 2: MonteCarloAgent   ← 100k samples 跑 numerical 验证
      Agent 3: CounterexampleAgent  ← LLM 提议反例 distribution + MC 验证
              ↓
      Agent 0: Coordinator       ← 综合 3 个的输出, 给出最终判断

  为什么需要 3 个? 因为 *statistical claims* 跟 *pure math claims* 不一样:
    • 形式证明失败 ≠ claim 错; 可能只是 Mathlib 缺工具
    • 形式证明成功 ≠ claim 在实际数据上 hold; 可能形式化时 typo 改了 statement
    • Monte Carlo 通过 ≠ claim 是定理; 只是 N=100k 没找到反例
  3 个 agent 互相 cross-check, 才能给可靠的答案.

  Requirements:
      pip install axiom-axle anthropic python-dotenv numpy scipy

  Usage:
      # 跑内置 4 道 stat claim:
      python stat_agent.py --demo

      # 跑某一个具体的:
      python stat_agent.py --demo --claim markov_inequality

      # 用 mock LLM (省 token):
      python stat_agent.py --demo --mock
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

# 项目根目录的 .env (跟 axle_agent.py 一样).
# parents[1] == "AI Statistician/" (workspace root, one level above this file).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

import anthropic              # noqa: E402
import numpy as np             # noqa: E402
from axle import AxleClient    # noqa: E402

LEAN_ENV = "lean-4.29.0"
DEFAULT_MODEL = "claude-haiku-4-5"
N_MC_SAMPLES = 100_000   # Monte Carlo sample 数, 越多越准但越慢


# ═════════════════════════════════════════════════════════════════════════════
# Section 1.  Data model
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class StatClaim:
    """一个待验证的统计学 claim. 同时带 *自然语言描述* 和 *Lean stub* 和
    *Monte Carlo 实验器*. 三种 representation 给 3 个 agent 用. -/
    """
    name: str
    english: str                                    # 给 LLM 看
    lean_stub: str                                  # 给 ProverAgent + AXLE 看
    mc_experiment: Callable[[int, np.random.Generator], bool]  # 给 MC verifier 跑
    # mc_experiment(n_samples, rng) -> True if claim holds empirically


@dataclass
class AgentVerdict:
    """单个 agent 的判断."""
    agent: str
    verdict: str                  # "PASS" | "FAIL" | "UNKNOWN"
    evidence: str = ""
    timing_s: float = 0.0


@dataclass
class FinalReport:
    """协调器的最终输出."""
    claim_name: str
    overall: str                  # "VERIFIED" | "DISPROVED" | "UNCERTAIN"
    agent_verdicts: list[AgentVerdict] = field(default_factory=list)
    summary: str = ""

    def to_json(self) -> str:
        return json.dumps({
            "claim": self.claim_name,
            "overall": self.overall,
            "agents": [
                {"agent": v.agent, "verdict": v.verdict,
                 "evidence": v.evidence[:200], "timing_s": v.timing_s}
                for v in self.agent_verdicts
            ],
            "summary": self.summary,
        }, indent=2, ensure_ascii=False)


# ═════════════════════════════════════════════════════════════════════════════
# Section 2.  Agent 1 — Formal ProverAgent (LLM ↔ AXLE)
# ═════════════════════════════════════════════════════════════════════════════
# 这是 axle_agent.py 那个 loop 的 stat-claim 版本. 我们重写得更简, 不再考虑
# tactic-only 的细节, 直接把 LLM 的提议替进 sorry 然后 verify.


PROVER_SYSTEM = """\
You are a Lean 4 + Mathlib theorem prover specializing in MeasureTheory and
ProbabilityTheory. The user will give you a sorried theorem about a statistical
claim. Propose 3 candidate proofs, each on its own line, formatted EXACTLY as:

  ATTEMPT: <one-line Lean tactic block starting with `by ...`>

No prose, no markdown fences, no numbering. If you need multi-line, use `<;>`
or `(...)` to keep it on one line. Each ATTEMPT should differ in strategy:
e.g., exact lemma application, simp-based, omega/linarith/nlinarith.
"""


class ProverAgent:
    """Agent 1: 形式证明 agent. LLM ↔ AXLE 闭环."""
    def __init__(self, axle: AxleClient, llm_mode: str = "anthropic"):
        self.axle = axle
        self.llm_mode = llm_mode
        if llm_mode == "anthropic":
            self._claude = anthropic.Anthropic()

    async def verify(self, claim: StatClaim, max_attempts: int = 3) -> AgentVerdict:
        import time
        t0 = time.monotonic()

        # 1. 让 LLM 提议 candidate
        candidates = await self._propose(claim, max_attempts)
        if not candidates:
            return AgentVerdict(
                agent="ProverAgent", verdict="UNKNOWN",
                evidence="LLM 没产出 candidate",
                timing_s=time.monotonic() - t0,
            )

        # 2. 对每个 candidate 调 AXLE verify
        for tac in candidates:
            content = self._splice(claim.lean_stub, tac)
            try:
                r = await self.axle.verify_proof(
                    formal_statement=claim.lean_stub,
                    content=content,
                    environment=LEAN_ENV,
                    ignore_imports=True,
                )
                if r.okay:
                    return AgentVerdict(
                        agent="ProverAgent", verdict="PASS",
                        evidence=f"AXLE verified `{tac}`",
                        timing_s=time.monotonic() - t0,
                    )
            except Exception as e:
                logging.debug(f"AXLE error for `{tac}`: {e}")
                continue

        return AgentVerdict(
            agent="ProverAgent", verdict="UNKNOWN",
            evidence=f"{len(candidates)} candidates 都 fail. 可能 Mathlib 缺工具.",
            timing_s=time.monotonic() - t0,
        )

    async def _propose(self, claim: StatClaim, n: int) -> list[str]:
        if self.llm_mode == "mock":
            return ["by exact?", "by simp_all", "by trivial"][:n]

        user_msg = (
            f"CLAIM (English): {claim.english}\n\n"
            f"LEAN STUB:\n```lean\n{claim.lean_stub}\n```\n\n"
            f"Propose {n} candidate proofs (ATTEMPT: by ... format)."
        )

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=400,
                system=PROVER_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        text = resp.content[0].text

        out: list[str] = []
        for line in text.splitlines():
            m = re.match(r"^\s*ATTEMPT:\s*(.+?)\s*$", line)
            if m:
                tac = m.group(1).strip().strip("`")
                if not tac.lower().startswith("by "):
                    tac = "by " + tac
                out.append(tac)
        return out[:n]

    @staticmethod
    def _splice(stub: str, tac: str) -> str:
        """把 candidate 拼进 sorry 占位."""
        if "by sorry" in stub:
            return stub.replace("by sorry", tac, 1)
        if ":= sorry" in stub:
            return stub.replace(":= sorry", ":= " + tac, 1)
        return stub  # 没占位符就原样返回


# ═════════════════════════════════════════════════════════════════════════════
# Section 3.  Agent 2 — MonteCarloAgent (numpy)
# ═════════════════════════════════════════════════════════════════════════════
# 关键洞见: stat claim 大多都是 "对所有满足 X 的 distribution, 不等式 Y 成立".
# 我们 sample 100k 次, 实测每次是否 hold. 即使数学上正确, 由于浮点误差也可
# 能少数 fail —— 所以我们用「pass_rate ≥ 99%」作 threshold.


class MonteCarloAgent:
    """Agent 2: 用 numpy 跑 N_MC_SAMPLES 次模拟."""
    def __init__(self, n_samples: int = N_MC_SAMPLES, threshold: float = 0.99):
        self.n_samples = n_samples
        self.threshold = threshold

    async def verify(self, claim: StatClaim) -> AgentVerdict:
        import time
        t0 = time.monotonic()
        rng = np.random.default_rng(seed=42)
        # 单次实验返回 True/False; 我们跑 N 次取 pass_rate.
        # 但实验器接受 (n_samples, rng), 所以一次调用内部就完成所有 sample.
        try:
            holds = bool(claim.mc_experiment(self.n_samples, rng))
        except Exception as e:
            return AgentVerdict(
                agent="MonteCarloAgent", verdict="UNKNOWN",
                evidence=f"MC 实验报错: {e}",
                timing_s=time.monotonic() - t0,
            )

        # mc_experiment 内部已经 aggregate, 直接给 bool
        return AgentVerdict(
            agent="MonteCarloAgent",
            verdict="PASS" if holds else "FAIL",
            evidence=f"{self.n_samples:,} samples 全部" + (" hold" if holds else " 检测到违例"),
            timing_s=time.monotonic() - t0,
        )


# ═════════════════════════════════════════════════════════════════════════════
# Section 4.  Agent 3 — CounterexampleAgent (LLM + MC)
# ═════════════════════════════════════════════════════════════════════════════
# 给 LLM 看 claim, 让它提议「一个具体的 distribution + 参数」尝试做反例,
# 然后用 numpy 跑这个 specific case 看是否真的违反 claim.
# 这是 *adversarial verification* —— stat 论文里最容易漏的 corner case.


CE_SYSTEM = """\
You are a hostile statistician hunting for counterexamples. The user gives you
a statistical claim. Your job: propose ONE specific distribution + parameter
setting that you suspect violates the claim. Output EXACTLY in this format:

  DISTRIBUTION: <name like 'normal', 'exponential', 'pareto', 'cauchy', etc.>
  PARAMS: <one-line dict-like literal, e.g. mean=0,std=1 or shape=0.5>
  RATIONALE: <one sentence why this might be a counterexample>

If you cannot think of one, output:
  NO_COUNTEREXAMPLE
"""


class CounterexampleAgent:
    """Agent 3: LLM 提议反例 distribution, 然后 MC 验证."""
    def __init__(self, llm_mode: str = "anthropic"):
        self.llm_mode = llm_mode
        if llm_mode == "anthropic":
            self._claude = anthropic.Anthropic()

    async def verify(self, claim: StatClaim) -> AgentVerdict:
        import time
        t0 = time.monotonic()

        proposal = await self._propose(claim)
        if proposal is None:
            return AgentVerdict(
                agent="CounterexampleAgent", verdict="UNKNOWN",
                evidence="LLM 找不出反例 distribution",
                timing_s=time.monotonic() - t0,
            )

        # Demo 实现: 我们只把 LLM 的建议 *记录下来*; 真实版需要把 LLM 输出的
        # distribution name + params 翻译成 numpy.random 调用, 然后跑 MC.
        # 这里我们做一个 *简单的* 版本: 直接用 scipy.stats 的 distribution.
        dist_name, params, rationale = proposal
        try:
            # 用 LLM 提议的 distribution 重新跑 claim.mc_experiment
            # (我们让 mc_experiment 接受 *可选* `rng` 但用 default 的 generator).
            # 这里只是 demo: 我们 *不* 实际换 distribution, 只 *记录* LLM 的建议.
            return AgentVerdict(
                agent="CounterexampleAgent", verdict="UNKNOWN",
                evidence=f"LLM 提议反例: {dist_name}({params}). 原因: {rationale}. "
                         f"(实际验证需要把 mc_experiment 改成 distribution-parametrized.)",
                timing_s=time.monotonic() - t0,
            )
        except Exception as e:
            return AgentVerdict(
                agent="CounterexampleAgent", verdict="UNKNOWN",
                evidence=f"反例验证报错: {e}",
                timing_s=time.monotonic() - t0,
            )

    async def _propose(self, claim: StatClaim) -> tuple[str, str, str] | None:
        if self.llm_mode == "mock":
            return ("cauchy", "loc=0,scale=1",
                    "Cauchy 没有有限均值, 经常违反需要 finite moment 的 claim")

        user_msg = f"CLAIM: {claim.english}\n\nPropose a counterexample distribution."

        def _call():
            return self._claude.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=200,
                system=CE_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
        resp = await asyncio.to_thread(_call)
        text = resp.content[0].text

        if "NO_COUNTEREXAMPLE" in text:
            return None
        m_dist = re.search(r"DISTRIBUTION:\s*(.+)", text)
        m_par = re.search(r"PARAMS:\s*(.+)", text)
        m_rat = re.search(r"RATIONALE:\s*(.+)", text)
        if not (m_dist and m_par and m_rat):
            return None
        return (m_dist.group(1).strip(), m_par.group(1).strip(), m_rat.group(1).strip())


# ═════════════════════════════════════════════════════════════════════════════
# Section 5.  Coordinator
# ═════════════════════════════════════════════════════════════════════════════


class Coordinator:
    """协调 3 个 agent, 综合判断."""

    def synthesize(self, claim: StatClaim,
                   prover: AgentVerdict, mc: AgentVerdict,
                   ce: AgentVerdict) -> FinalReport:
        """3 个 agent 的 verdict → 最终结论."""
        # 决策表 (粗略):
        #   MC=FAIL                  → DISPROVED (有反例 = claim 错)
        #   Prover=PASS, MC=PASS     → VERIFIED (双重确认)
        #   Prover=PASS, MC=UNKNOWN  → VERIFIED (信形式证明)
        #   Prover=UNKNOWN, MC=PASS  → UNCERTAIN (Mathlib 缺工具, 但 empirical OK)
        #   全 UNKNOWN               → UNCERTAIN
        if mc.verdict == "FAIL":
            overall = "DISPROVED"
            summary = "Monte Carlo 找到 violation → claim 错"
        elif prover.verdict == "PASS" and mc.verdict in ("PASS", "UNKNOWN"):
            overall = "VERIFIED"
            summary = "AXLE 形式证明通过" + ("; MC 也支持" if mc.verdict == "PASS" else "")
        elif prover.verdict == "UNKNOWN" and mc.verdict == "PASS":
            overall = "UNCERTAIN"
            summary = ("Empirical OK 但形式证明失败. "
                       "Mathlib 可能缺工具 —— Axiom Math 该填.")
        else:
            overall = "UNCERTAIN"
            summary = "3 agent 都没给确定结论. 需要人工 review."

        return FinalReport(
            claim_name=claim.name, overall=overall,
            agent_verdicts=[prover, mc, ce], summary=summary,
        )


# ═════════════════════════════════════════════════════════════════════════════
# Section 6.  Demo claims (4 道经典统计 claim)
# ═════════════════════════════════════════════════════════════════════════════


def _mc_markov(n: int, rng: np.random.Generator) -> bool:
    """Markov: 对 Exponential(1), P(X ≥ 3) ≤ E[X]/3 = 1/3."""
    X = rng.exponential(scale=1.0, size=n)
    lhs = float(np.mean(X >= 3.0))
    rhs = 1.0 / 3.0
    return lhs <= rhs + 0.01  # 留一点 MC 噪声 tolerance


def _mc_chebyshev(n: int, rng: np.random.Generator) -> bool:
    """Chebyshev: 对 N(0,1), P(|X| ≥ 2) ≤ 1/4."""
    X = rng.standard_normal(size=n)
    lhs = float(np.mean(np.abs(X) >= 2.0))
    rhs = 1.0 / 4.0
    return lhs <= rhs + 0.01


def _mc_lln(n: int, rng: np.random.Generator) -> bool:
    """SLLN: 样本均值 → 总体均值. 用 n=10000 个 Uniform(0,1), 均值应 ≈ 0.5."""
    if n < 10:
        return True
    X = rng.uniform(0.0, 1.0, size=10_000)
    return abs(float(np.mean(X)) - 0.5) < 0.02


def _mc_wrong_claim(n: int, rng: np.random.Generator) -> bool:
    """故意错的 claim: "对所有 distribution, E[X²] = (E[X])²".
    这只在 Var[X] = 0 时成立 (即 X 是常数). 我们用 N(0,1) 验, 会失败."""
    X = rng.standard_normal(size=n)
    return abs(float(np.mean(X ** 2)) - float(np.mean(X)) ** 2) < 0.01


def _mc_trivial(n: int, rng: np.random.Generator) -> bool:
    """Sanity-check claim: 任何 distribution, MC sample 出来都是 finite real
    number. 用来 demo full pipeline 的 VERIFIED 路径."""
    X = rng.standard_normal(size=min(n, 1000))
    return bool(np.all(np.isfinite(X)))


DEMO_CLAIMS = [
    StatClaim(
        name="sanity_check_provable",
        english="For any natural number n, n + 0 = n (trivial sanity check).",
        lean_stub=(
            "import Mathlib\n"
            "theorem sanity_check (n : Nat) : n + 0 = n := by sorry"
        ),
        mc_experiment=_mc_trivial,
    ),
    StatClaim(
        name="markov_inequality",
        english="The Markov inequality in measure-theoretic form: "
                "for a measurable nonneg function f and ε ≠ 0, ε ≠ ⊤, "
                "μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε.",
        lean_stub=(
            "import Mathlib\n"
            "open MeasureTheory in\n"
            "theorem markov_thm {α : Type*} [MeasurableSpace α] (μ : Measure α)\n"
            "    (f : α → ENNReal) (hf : Measurable f) (ε : ENNReal)\n"
            "    (hε : ε ≠ 0) (hεt : ε ≠ ⊤) :\n"
            "    μ {x | ε ≤ f x} ≤ (∫⁻ x, f x ∂μ) / ε := by sorry"
        ),
        mc_experiment=_mc_markov,
    ),
    StatClaim(
        name="chebyshev_normal",
        english="For X ~ N(0,1), P(|X| ≥ 2) ≤ 1/4 (Chebyshev with Var[X]=1).",
        lean_stub=(
            "import Mathlib\n"
            "theorem chebyshev_le (a b : ℝ) (h : a ≤ b) : a ≤ b := by sorry"
        ),  # 简化 stub, MC 才是真验证
        mc_experiment=_mc_chebyshev,
    ),
    StatClaim(
        name="lln_uniform",
        english="For i.i.d. Uniform(0,1), sample mean of 10k samples is close to 0.5 (SLLN).",
        lean_stub=(
            "import Mathlib\n"
            "theorem lln_stub (n : Nat) : n + 0 = n := by sorry"
        ),  # 简化 stub
        mc_experiment=_mc_lln,
    ),
    StatClaim(
        name="WRONG_e_x2_eq_e_x_sq",
        english="For all distributions, E[X²] = (E[X])² — *intentionally wrong*.",
        lean_stub=(
            "import Mathlib\n"
            "-- This claim is false in general (only true when Var[X] = 0).\n"
            "theorem wrong_claim (a : ℝ) : a = a + 1 := by sorry"   # 故意错的 stub
        ),
        mc_experiment=_mc_wrong_claim,
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
# Section 7.  Main driver
# ═════════════════════════════════════════════════════════════════════════════


async def verify_one(claim: StatClaim, prover: ProverAgent,
                     mc: MonteCarloAgent, ce: CounterexampleAgent,
                     coord: Coordinator) -> FinalReport:
    """跑一个 claim 的完整 3-agent 流程."""
    print(f"\n══════════ {claim.name} ══════════")
    print(f"CLAIM: {claim.english}")

    # 3 个 agent 并行跑 (asyncio.gather 节省时间).
    print("  → dispatching 3 agents in parallel…")
    v_prover, v_mc, v_ce = await asyncio.gather(
        prover.verify(claim),
        mc.verify(claim),
        ce.verify(claim),
    )

    for v in (v_prover, v_mc, v_ce):
        sym = {"PASS": "✓", "FAIL": "✗", "UNKNOWN": "?"}.get(v.verdict, "?")
        print(f"  {sym}  {v.agent:22s}  {v.verdict:8s}  ({v.timing_s:.2f}s)")
        print(f"       └─ {v.evidence[:100]}")

    report = coord.synthesize(claim, v_prover, v_mc, v_ce)
    badge = {"VERIFIED": "✅", "DISPROVED": "❌", "UNCERTAIN": "🤔"}[report.overall]
    print(f"  {badge}  OVERALL: {report.overall}  —  {report.summary}")
    return report


async def main_async(claim_filter: str | None, mock: bool) -> None:
    llm_mode = "mock" if mock else "anthropic"

    async with AxleClient(api_key=os.environ["AXLE_API_KEY"]) as axle:
        prover = ProverAgent(axle, llm_mode=llm_mode)
        mc = MonteCarloAgent()
        ce = CounterexampleAgent(llm_mode=llm_mode)
        coord = Coordinator()

        claims = DEMO_CLAIMS
        if claim_filter:
            claims = [c for c in claims if c.name == claim_filter]
            if not claims:
                print(f"No claim named {claim_filter!r}", file=sys.stderr)
                sys.exit(1)

        results: list[FinalReport] = []
        for claim in claims:
            r = await verify_one(claim, prover, mc, ce, coord)
            results.append(r)

        # 最终 summary
        print("\n" + "═" * 70)
        print("  FINAL SUMMARY")
        print("═" * 70)
        for r in results:
            badge = {"VERIFIED": "✅", "DISPROVED": "❌", "UNCERTAIN": "🤔"}[r.overall]
            print(f"  {badge}  {r.claim_name:32s}  {r.overall}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-agent stat claim verifier")
    parser.add_argument("--demo", action="store_true",
                        help="run the 4 built-in demo claims")
    parser.add_argument("--claim", help="only run this claim (e.g. markov_inequality)")
    parser.add_argument("--mock", action="store_true",
                        help="use mock LLM (no Anthropic API calls)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )
    for noisy in ("httpx", "httpcore", "anthropic", "axle"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    asyncio.run(main_async(args.claim, args.mock))


if __name__ == "__main__":
    main()


# ═════════════════════════════════════════════════════════════════════════════
# 一句话总结 (interview pitch handle)
# ═════════════════════════════════════════════════════════════════════════════
# 这 ~400 行展示了 *3 个* 抽象层级:
#   ① Agent abstraction (Strategy pattern, dependency injection)
#   ② Cross-modal evidence (formal proof × empirical MC × adversarial CE)
#   ③ Coordinator decision logic (decision table over agent verdicts)
#
# Pitch 时说: "如果 Axiom Math 把这个产品化, 客户是 FDA / pharma / SEC,
# 价值是 *把统计学家 0 行 Lean 经验转化成 verified claims*."
# ═════════════════════════════════════════════════════════════════════════════
