from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_lab import (
    ProblemFormalizer,
    ResearchSimulator,
    TheoryPlanner,
    attach_research_algorithm_metadata,
    build_research_provenance,
    load_open_research_questions,
)
from .research_schema import OpenResearchQuestion, ResearchSimulation


ALGORITHM_SIMULATION_STRESS_AUDIT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmSimulationStressRow:
    question_id: str
    problem_class: str
    procedure_id: str
    algorithm: str
    seed: int
    passed: bool
    finite_metrics_ok: bool
    stress_ledger_ok: bool
    diagnosis_ok: bool
    n_metrics: int
    n_stress_tests: int
    n_stress_flags: int
    adaptive_mc_rerun_used: bool
    adaptive_mc_resolved: bool
    failed_diagnostics: tuple[str, ...]
    failed_stress_tests: tuple[str, ...]


def audit_algorithm_simulation_stress(
    out_dir: Path | None = None,
    *,
    question_file: Path = Path("examples/research_questions.json"),
    seeds: tuple[int, ...] = (101, 102, 103),
    n_runs: int = 25,
    max_questions: int | None = None,
    adaptive_mc_rerun: bool = True,
    adaptive_mc_multiplier: int = 5,
) -> dict[str, object]:
    """Run a targeted multi-seed simulation stress audit.

    This is intentionally simulator-only: it exercises the formalizer, theory
    planner, vetted algorithm metadata, and ResearchSimulator across multiple
    seeds without rerunning proof search. It checks finite metrics, per-problem
    stress-test ledgers, and simulator diagnoses. The evidence is empirical,
    not formal proof evidence.
    """

    questions = load_open_research_questions(question_file)
    if max_questions is not None:
        questions = questions[:max_questions]
    formalizer = ProblemFormalizer()
    planner = TheoryPlanner()
    rows: list[AlgorithmSimulationStressRow] = []
    for seed in seeds:
        simulator = ResearchSimulator(n_runs=n_runs, seed=seed)
        for question in questions:
            problem = formalizer.formalize(question)
            procedures, _ = planner.plan(problem)
            procedures = attach_research_algorithm_metadata(procedures)
            simulations = (
                simulator.run_with_adaptive_mc(problem, procedures, multiplier=adaptive_mc_multiplier)
                if adaptive_mc_rerun
                else simulator.run(problem, procedures)
            )
            for simulation in simulations:
                procedure = next((row for row in procedures if row.id == simulation.procedure_id), None)
                rows.append(
                    _row_from_simulation(
                        question=question,
                        problem_class=problem.problem_class,
                        algorithm=procedure.algorithm if procedure is not None else "",
                        seed=seed,
                        simulation=simulation,
                    )
                )

    by_algorithm: dict[str, dict[str, object]] = {}
    for algorithm in sorted({row.algorithm for row in rows}):
        alg_rows = [row for row in rows if row.algorithm == algorithm]
        by_algorithm[algorithm] = {
            "runs": len(alg_rows),
            "pass_rate": _rate(row.passed for row in alg_rows),
            "finite_metrics_rate": _rate(row.finite_metrics_ok for row in alg_rows),
            "stress_ledger_rate": _rate(row.stress_ledger_ok for row in alg_rows),
            "diagnosis_ok_rate": _rate(row.diagnosis_ok for row in alg_rows),
            "stress_flags": sum(row.n_stress_flags for row in alg_rows),
        }

    all_finite = all(row.finite_metrics_ok for row in rows)
    all_stress_ledgers = all(row.stress_ledger_ok for row in rows)
    all_diagnoses_ok = all(row.diagnosis_ok for row in rows)
    all_passed = all(row.passed for row in rows)
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_SIMULATION_STRESS_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_file": str(question_file),
        "seeds": list(seeds),
        "n_seeds": len(seeds),
        "n_runs": n_runs,
        "adaptive_mc_rerun": bool(adaptive_mc_rerun),
        "adaptive_mc_multiplier": int(adaptive_mc_multiplier),
        "adaptive_mc_rows": sum(1 for row in rows if row.adaptive_mc_rerun_used),
        "adaptive_mc_resolved": sum(1 for row in rows if row.adaptive_mc_resolved),
        "n_questions": len(questions),
        "n_seeded_simulations": len(rows),
        "n_algorithms": len(by_algorithm),
        "all_passed": all_passed,
        "all_finite_metrics": all_finite,
        "all_stress_ledgers_ok": all_stress_ledgers,
        "all_diagnoses_ok": all_diagnoses_ok,
        "multi_seed_stability_checked": len(seeds) >= 2 and bool(rows),
        "n_stress_flags": sum(row.n_stress_flags for row in rows),
        "n_failed_simulations": sum(1 for row in rows if not row.passed),
        "n_failed_diagnoses": sum(1 for row in rows if not row.diagnosis_ok),
        "by_algorithm": by_algorithm,
        "rows": [asdict(row) for row in rows],
        "all_ok": bool(rows)
        and len(seeds) >= 2
        and all_passed
        and all_finite
        and all_stress_ledgers
        and all_diagnoses_ok,
        "provenance": build_research_provenance(),
        "limitations": [
            "multi-seed simulation stress is empirical evidence, not a theorem proof",
            "stress-test metrics are simulator ledgers derived from registered DGP/procedure diagnostics",
            "passing this audit does not imply validity under arbitrary adversarial DGPs",
        ],
        "audit_fingerprint": stable_hash([asdict(row) for row in rows]),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "algorithm_simulation_stress_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "algorithm_simulation_stress.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _row_from_simulation(
    *,
    question: OpenResearchQuestion,
    problem_class: str,
    algorithm: str,
    seed: int,
    simulation: ResearchSimulation,
) -> AlgorithmSimulationStressRow:
    stress_values = [
        value
        for metrics in simulation.stress_test_metrics.values()
        for value in metrics.values()
        if isinstance(value, (int, float))
    ]
    finite_metrics_ok = all(_finite(value) for value in simulation.metrics.values()) and all(
        _finite(value) for value in stress_values
    )
    required_stress_keys = {"covered", "stress_flag", "primary_value", "threshold"}
    stress_ledger_ok = bool(simulation.stress_tests) and set(simulation.stress_tests) == set(
        simulation.stress_test_metrics
    ) and all(
        required_stress_keys <= set(metrics)
        and all(_finite(value) for value in metrics.values() if isinstance(value, (int, float)))
        for metrics in simulation.stress_test_metrics.values()
    )
    diagnosis = simulation.diagnosis
    diagnosis_ok = (
        diagnosis is not None
        and diagnosis.status == "OK"
        and diagnosis.escalate_to == "none"
        and not diagnosis.failed_diagnostics
        and not diagnosis.failed_stress_tests
    )
    return AlgorithmSimulationStressRow(
        question_id=question.id,
        problem_class=problem_class,
        procedure_id=simulation.procedure_id,
        algorithm=algorithm,
        seed=seed,
        passed=bool(simulation.passed),
        finite_metrics_ok=finite_metrics_ok,
        stress_ledger_ok=stress_ledger_ok,
        diagnosis_ok=diagnosis_ok,
        n_metrics=len(simulation.metrics),
        n_stress_tests=len(simulation.stress_tests),
        n_stress_flags=sum(
            1
            for metrics in simulation.stress_test_metrics.values()
            if float(metrics.get("stress_flag", 0.0)) > 0.0
        ),
        adaptive_mc_rerun_used=float(simulation.metrics.get("adaptive_mc_rerun_used", 0.0)) > 0.5,
        adaptive_mc_resolved=float(simulation.metrics.get("adaptive_mc_resolved", 0.0)) > 0.5,
        failed_diagnostics=tuple(diagnosis.failed_diagnostics if diagnosis is not None else ()),
        failed_stress_tests=tuple(diagnosis.failed_stress_tests if diagnosis is not None else ()),
    )


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _rate(values: Any) -> float:
    rows = [bool(value) for value in values]
    return sum(rows) / len(rows) if rows else 0.0


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Algorithm Simulation Stress Audit",
        "",
        f"- Questions: {payload.get('n_questions')}",
        f"- Seeds: {payload.get('n_seeds')} `{payload.get('seeds')}`",
        f"- Seeded simulations: {payload.get('n_seeded_simulations')}",
        f"- Algorithms: {payload.get('n_algorithms')}",
        f"- Adaptive MC rerun: `{payload.get('adaptive_mc_rerun')}`",
        f"- Adaptive MC rows/resolved: {payload.get('adaptive_mc_resolved')}/{payload.get('adaptive_mc_rows')}",
        f"- All passed: `{payload.get('all_passed')}`",
        f"- All finite metrics: `{payload.get('all_finite_metrics')}`",
        f"- All stress ledgers OK: `{payload.get('all_stress_ledgers_ok')}`",
        f"- All diagnoses OK: `{payload.get('all_diagnoses_ok')}`",
        f"- All OK: `{payload.get('all_ok')}`",
        "",
        "## By Algorithm",
        "",
        "| Algorithm | Runs | Pass rate | Finite rate | Stress-ledger rate | Diagnosis OK rate | Stress flags |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    by_algorithm = payload.get("by_algorithm", {})
    if isinstance(by_algorithm, dict):
        for algorithm, row in sorted(by_algorithm.items()):
            if not isinstance(row, dict):
                continue
            lines.append(
                f"| `{algorithm}` | {row.get('runs')} | {row.get('pass_rate')} | "
                f"{row.get('finite_metrics_rate')} | {row.get('stress_ledger_rate')} | "
                f"{row.get('diagnosis_ok_rate')} | {row.get('stress_flags')} |"
            )
    lines.extend(["", "## Honesty Boundary", ""])
    for limitation in payload.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)
