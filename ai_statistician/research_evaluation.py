from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_lab import build_research_provenance, run_research_benchmark
from .research_schema import OpenResearchQuestion
from .research_trace_audit import audit_research_traces
from .verifier import AxleProofVerifier, MockProofVerifier, ProofVerifier


@dataclass(frozen=True)
class ResearchEvalConfig:
    seeds: tuple[int, ...]
    n_runs: int
    use_axle: bool = False


async def run_research_seed_eval(
    questions: list[OpenResearchQuestion],
    config: ResearchEvalConfig,
    out_dir: Path,
    *,
    proof_verifier: ProofVerifier | None = None,
) -> dict[str, object]:
    """Run the open-question research benchmark across multiple simulation seeds."""

    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = proof_verifier or (AxleProofVerifier() if config.use_axle else MockProofVerifier())
    trials: list[dict[str, Any]] = []
    artifacts: list[dict[str, str]] = []
    for seed in config.seeds:
        seed_dir = out_dir / f"seed_{seed}"
        manifest = await run_research_benchmark(
            questions,
            seed_dir,
            proof_verifier=verifier,
            n_runs=config.n_runs,
            seed=seed,
        )
        trace_audit = audit_research_traces(seed_dir, seed_dir / "research_trace_audit")
        artifacts.append(
            {
                "seed": str(seed),
                "benchmark_manifest": str(seed_dir / "research_benchmark_manifest.json"),
                "trace_audit_manifest": str(seed_dir / "research_trace_audit" / "research_trace_audit_manifest.json"),
            }
        )
        for row in manifest["questions"]:
            trial = {
                "seed": seed,
                "trace_audit_ok": bool(trace_audit["all_ok"]),
                **row,
            }
            trials.append(trial)

    summary = _aggregate_trials(questions, trials)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "seeds": list(config.seeds),
            "n_runs": config.n_runs,
            "use_axle": config.use_axle,
            "verifier": verifier.name,
        },
        "provenance": build_research_provenance(),
        "n_questions": len(questions),
        "n_seeds": len(config.seeds),
        "all_ready_with_gaps": all(row["ready_rate"] == 1.0 for row in summary.values()),
        "all_trace_audits_ok": all(row["trace_audit_ok_rate"] == 1.0 for row in summary.values()),
        "summary": summary,
        "trials": trials,
        "artifacts": artifacts,
    }
    (out_dir / "research_evaluation_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def _aggregate_trials(questions: list[OpenResearchQuestion], trials: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for question in questions:
        rows = [row for row in trials if row["question"] == question.id]
        ready = sum(1 for row in rows if row["status"] == "RESEARCH_TRACE_READY_WITH_FORMAL_GAPS")
        sim_flagged = sum(1 for row in rows if row["status"] == "SIMULATION_FLAGGED_WITH_FORMAL_GAPS")
        formal_blocked = sum(1 for row in rows if row["status"] == "FORMAL_BLOCKED")
        trace_ok = sum(1 for row in rows if row["trace_audit_ok"])
        procedure_metrics: dict[str, dict[str, list[float]]] = {}
        for row in rows:
            for sim in row.get("simulations", []):
                procedure_id = str(sim.get("procedure_id"))
                metrics = sim.get("metrics", {})
                if not isinstance(metrics, dict):
                    continue
                procedure_metrics.setdefault(procedure_id, {})
                for key, value in metrics.items():
                    if isinstance(value, (int, float)) and math.isfinite(float(value)):
                        procedure_metrics[procedure_id].setdefault(key, []).append(float(value))
        procedures = {
            procedure_id: {
                metric: {
                    "mean": _mean(values),
                    "sd": _sample_sd(values),
                    "min": min(values),
                    "max": max(values),
                }
                for metric, values in metrics.items()
                if values
            }
            for procedure_id, metrics in procedure_metrics.items()
        }
        out[question.id] = {
            "trials": len(rows),
            "ready_with_gaps": ready,
            "simulation_flagged": sim_flagged,
            "formal_blocked": formal_blocked,
            "ready_rate": ready / len(rows) if rows else 0.0,
            "trace_audit_ok": trace_ok,
            "trace_audit_ok_rate": trace_ok / len(rows) if rows else 0.0,
            "procedures": procedures,
        }
    return out


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sample_sd(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
