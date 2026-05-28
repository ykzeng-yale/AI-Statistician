from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schema import StatisticalQuestion
from .system import AIStatisticianSystem, build_provenance, compact_summary, write_run_manifest, write_trace


@dataclass(frozen=True)
class EvalConfig:
    seeds: tuple[int, ...]
    n_runs: int
    use_axle: bool = False


async def run_seed_eval(
    questions: list[StatisticalQuestion],
    config: EvalConfig,
    out_dir: Path,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    trials: list[dict[str, object]] = []
    for seed in config.seeds:
        seed_dir = out_dir / f"seed_{seed}"
        system = (
            AIStatisticianSystem.with_axle(n_runs=config.n_runs, seed=seed)
            if config.use_axle
            else AIStatisticianSystem(n_runs=config.n_runs, seed=seed)
        )
        seed_reports = []
        for question in questions:
            report = await system.run(question)
            seed_reports.append(report)
            write_trace(report, seed_dir)
            trials.append({"seed": seed, **compact_summary(report)})
        write_run_manifest(seed_reports, seed_dir)

    by_question: dict[str, dict[str, object]] = {}
    for question in questions:
        rows = [row for row in trials if row["question"] == question.id]
        accepted = sum(1 for row in rows if row["status"] == "ACCEPTED")
        by_question[question.id] = {
            "trials": len(rows),
            "accepted": accepted,
            "acceptance_rate": accepted / len(rows) if rows else 0.0,
            "mean_coverage_95": sum(float(row["coverage_95"]) for row in rows) / len(rows) if rows else 0.0,
            "mean_rmse": sum(float(row["rmse"]) for row in rows) / len(rows) if rows else 0.0,
        }

    payload = {
        "config": {
            "seeds": list(config.seeds),
            "n_runs": config.n_runs,
            "use_axle": config.use_axle,
        },
        "provenance": build_provenance(),
        "summary": by_question,
        "trials": trials,
    }
    path = out_dir / "evaluation_manifest.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload
