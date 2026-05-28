"""
================================================================================
  run_eval.py — Multi-seed stability evaluation of the 3-agent system
  跑 N 个 random seed, 看 convergence / token / latency 多稳定
================================================================================

  Why this matters: any single LLM-driven demo is one sample from a stochastic
  process. To make defensible claims ("3-agent converges X% of time"), we need
  to run multiple trials.

  This script:
    1. Runs `stat_research_agent` (3-agent) on each demo question, N times
       (different MC seeds; LLM responses have inherent stochasticity too)
    2. Tracks: convergence, rounds, tokens, latency, final metrics
    3. Writes `EvaluationReport.md` with mean ± std across seeds

  Cost: ~$0.05 per seed × N seeds × 2 questions  ≈ $0.50 for 5 seeds.
  Time: ~30s per question × N × 2  ≈ 5 min for 5 seeds.

  Usage:
      python run_eval.py                  # default 3 seeds, ~3 min, ~$0.15
      python run_eval.py --seeds 5        # 5 seeds, ~5 min, ~$0.25
      python run_eval.py --seeds 1        # quick smoke test, 1 seed
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ARCHIVE_DIR = Path(__file__).resolve().parent
PARENT_DIR = ARCHIVE_DIR.parent
PROJECT_ROOT = ARCHIVE_DIR.parents[3]
sys.path.insert(0, str(PARENT_DIR))
load_dotenv(PROJECT_ROOT / ".env")

from axle import AxleClient  # noqa: E402

from stat_research_agent import (
    DEMO_QUESTIONS, MathematicianAgent, AlgorithmAgent, SimulatorAgent,
    research_one,
)


# ═════════════════════════════════════════════════════════════════════════════
# Data structures
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class TrialResult:
    seed: int
    question_name: str
    status: str
    n_outer_rounds: int
    n_total_llm_calls: int
    total_tokens: int
    wall_clock_s: float
    final_bias: float
    final_coverage: float


@dataclass
class StabilityStats:
    """Aggregate over multiple seeds for one question."""
    question_name: str
    n_trials: int
    converge_rate: float            # 0..1
    mean_rounds: float
    mean_tokens: float
    std_tokens: float
    mean_time_s: float
    std_time_s: float
    mean_coverage: float
    std_coverage: float


# ═════════════════════════════════════════════════════════════════════════════
# Trial runner
# ═════════════════════════════════════════════════════════════════════════════


async def run_one_trial(question, axle, seed: int) -> TrialResult:
    """Run 3-agent on `question` with the given Monte Carlo seed."""
    math = MathematicianAgent(axle, llm_mode="anthropic")
    algo = AlgorithmAgent(llm_mode="anthropic")
    sim = SimulatorAgent(seed=seed)

    t0 = time.monotonic()
    final = await research_one(question, math, algo, sim,
                                max_outer=2, max_inner=2)
    elapsed = time.monotonic() - t0

    n_outer = len(final.rounds)
    n_inner = sum(len(r.inner_attempts) for r in final.rounds)
    n_llm = n_outer + n_inner

    bias = cov = float("nan")
    if final.rounds:
        last = final.rounds[-1]
        if last.final_result and last.final_result.metrics:
            m = last.final_result.metrics
            bias, cov = m.bias, m.coverage_95

    return TrialResult(
        seed=seed,
        question_name=question.name,
        status=final.final_status,
        n_outer_rounds=n_outer,
        n_total_llm_calls=n_llm,
        total_tokens=(math.total_input_tokens + math.total_output_tokens
                       + algo.total_input_tokens + algo.total_output_tokens),
        wall_clock_s=elapsed,
        final_bias=bias, final_coverage=cov,
    )


def aggregate(trials: list[TrialResult]) -> StabilityStats:
    """Aggregate per-question across seeds."""
    name = trials[0].question_name
    n_conv = sum(1 for t in trials if t.status == "CONVERGED")
    cov_vals = [t.final_coverage for t in trials if not (t.final_coverage != t.final_coverage)]
    return StabilityStats(
        question_name=name,
        n_trials=len(trials),
        converge_rate=n_conv / len(trials),
        mean_rounds=statistics.mean(t.n_outer_rounds for t in trials),
        mean_tokens=statistics.mean(t.total_tokens for t in trials),
        std_tokens=statistics.stdev(t.total_tokens for t in trials) if len(trials) > 1 else 0.0,
        mean_time_s=statistics.mean(t.wall_clock_s for t in trials),
        std_time_s=statistics.stdev(t.wall_clock_s for t in trials) if len(trials) > 1 else 0.0,
        mean_coverage=statistics.mean(cov_vals) if cov_vals else float("nan"),
        std_coverage=statistics.stdev(cov_vals) if len(cov_vals) > 1 else 0.0,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Markdown report writer
# ═════════════════════════════════════════════════════════════════════════════


def write_report(all_trials: list[TrialResult], stats: list[StabilityStats],
                 path: Path) -> None:
    n_seeds = len(set(t.seed for t in all_trials))
    seeds_list = sorted(set(t.seed for t in all_trials))

    lines = [
        "# Multi-Seed Stability Evaluation (3-agent system)",
        "",
        f"_Generated by `archive/run_eval.py` — {n_seeds} seeds × "
        f"{len(stats)} questions = {len(all_trials)} trials._",
        f"_Seeds: {seeds_list}_",
        "_Model: Claude Haiku 4.5_",
        "",
        "## Per-question stability (mean ± std across seeds)",
        "",
        "| Question | Converge rate | Mean rounds | Mean tokens | Mean time | Mean coverage |",
        "|---|:-:|---:|---:|---:|---:|",
    ]
    for s in stats:
        cov_str = (f"{s.mean_coverage:.3f} ± {s.std_coverage:.3f}"
                   if s.std_coverage > 0 else f"{s.mean_coverage:.3f}")
        lines.append(
            f"| {s.question_name} | **{s.converge_rate:.0%}** "
            f"({int(s.converge_rate * s.n_trials)}/{s.n_trials}) | "
            f"{s.mean_rounds:.1f} | "
            f"{s.mean_tokens:,.0f} ± {s.std_tokens:,.0f} | "
            f"{s.mean_time_s:.1f}s ± {s.std_time_s:.1f}s | "
            f"{cov_str} |"
        )

    # Per-trial detail
    lines += ["", "## Per-trial detail", "",
              "| Seed | Question | Status | Rounds | LLM calls | Tokens | Time | Coverage |",
              "|---:|---|---|---:|---:|---:|---:|---:|"]
    for t in all_trials:
        badge = "✅" if t.status == "CONVERGED" else "⚠️ "
        lines.append(
            f"| {t.seed} | {t.question_name} | {badge} {t.status} | "
            f"{t.n_outer_rounds} | {t.n_total_llm_calls} | "
            f"{t.total_tokens:,} | {t.wall_clock_s:.1f}s | "
            f"{t.final_coverage:.3f} |"
        )

    # Aggregate / verdict
    total_conv = sum(1 for t in all_trials if t.status == "CONVERGED")
    total_tok = sum(t.total_tokens for t in all_trials)
    total_time = sum(t.wall_clock_s for t in all_trials)
    cost = total_tok * 3.0 / 1e6   # rough: avg ~$3/MTok blended Haiku 4.5

    lines += [
        "",
        "## Bottom line",
        "",
        f"- **Overall convergence**: {total_conv}/{len(all_trials)} trials "
        f"({total_conv/len(all_trials):.0%})",
        f"- **Total tokens**: {total_tok:,}",
        f"- **Total wall-clock**: {total_time:.1f}s ({total_time/60:.1f} min)",
        f"- **Estimated cost** (Haiku 4.5): ~${cost:.3f}",
        "",
        "### Stability assessment",
        "",
        _stability_verdict(stats),
        "",
        "### Caveats",
        "",
        "- LLM responses have inherent stochasticity; convergence rate could "
        "shift ±10% with more seeds.",
        "- Only 2 questions × N seeds; real benchmark needs 20+ questions.",
        "- Cost estimate uses blended ~$3/MTok rate; actual cost depends on "
        "input/output token ratio.",
    ]
    path.write_text("\n".join(lines))
    print(f"\n📝 Wrote eval report to {path}")


def _stability_verdict(stats: list[StabilityStats]) -> str:
    """Auto-generate a verdict about stability."""
    parts = []
    for s in stats:
        if s.converge_rate >= 0.8:
            parts.append(f"- `{s.question_name}`: **stable** ({s.converge_rate:.0%} converge), "
                         f"tokens vary ±{s.std_tokens/max(s.mean_tokens,1)*100:.0f}%, "
                         f"time varies ±{s.std_time_s/max(s.mean_time_s,1)*100:.0f}%.")
        elif s.converge_rate >= 0.5:
            parts.append(f"- `{s.question_name}`: **moderately stable** ({s.converge_rate:.0%} converge). "
                         f"This question is on the boundary of LLM capability.")
        else:
            parts.append(f"- `{s.question_name}`: **unstable** ({s.converge_rate:.0%} converge). "
                         f"Likely too hard for Haiku 4.5; needs Opus or specialized prompting.")
    return "\n".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════


async def main_async(seeds: list[int]) -> None:
    all_trials: list[TrialResult] = []
    async with AxleClient(api_key=os.environ["AXLE_API_KEY"]) as axle:
        for seed in seeds:
            for q in DEMO_QUESTIONS:
                print(f"\n▶ Seed {seed}, question {q.name} …")
                t = await run_one_trial(q, axle, seed)
                badge = "✅" if t.status == "CONVERGED" else "⚠️ "
                print(f"  {badge} {t.status}, "
                      f"rounds={t.n_outer_rounds}, tokens={t.total_tokens:,}, "
                      f"time={t.wall_clock_s:.1f}s, cov={t.final_coverage:.3f}")
                all_trials.append(t)

    # Aggregate by question
    by_q: dict[str, list[TrialResult]] = {}
    for t in all_trials:
        by_q.setdefault(t.question_name, []).append(t)
    stats = [aggregate(trs) for trs in by_q.values()]

    # Print summary
    print("\n" + "═" * 80)
    print("  STABILITY SUMMARY")
    print("═" * 80)
    for s in stats:
        print(f"  {s.question_name:24s}  "
              f"converge={s.converge_rate:.0%} ({int(s.converge_rate*s.n_trials)}/{s.n_trials})  "
              f"tokens={s.mean_tokens:,.0f}±{s.std_tokens:,.0f}  "
              f"time={s.mean_time_s:.1f}±{s.std_time_s:.1f}s")
    print("═" * 80)

    # Write report and raw JSON
    write_report(all_trials, stats, PARENT_DIR / "EvaluationReport.md")
    json_path = ARCHIVE_DIR / "eval_results.json"
    json_path.write_text(json.dumps(
        [t.__dict__ for t in all_trials], indent=2, default=str,
    ))
    print(f"📊 Raw trials → {json_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-seed stability eval of 3-agent system"
    )
    parser.add_argument("--seeds", type=int, default=3,
                        help="number of MC seeds to try (default 3)")
    parser.add_argument("--seed-list", type=str, default=None,
                        help="comma-separated list of seeds (overrides --seeds)")
    args = parser.parse_args()

    if args.seed_list:
        seeds = [int(s.strip()) for s in args.seed_list.split(",")]
    else:
        seeds = [42 + i * 17 for i in range(args.seeds)]   # 42, 59, 76, ...

    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    for noisy in ("httpx", "httpcore", "anthropic", "axle"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    asyncio.run(main_async(seeds))


if __name__ == "__main__":
    main()
