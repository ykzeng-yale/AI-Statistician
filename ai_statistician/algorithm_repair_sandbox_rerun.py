from __future__ import annotations

import json
import math
from collections import Counter
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
    audit_research_algorithm_registry,
    load_open_research_questions,
)
from .research_schema import CandidateProcedure, ResearchProblemSpec


ALGORITHM_REPAIR_SANDBOX_RERUN_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmRepairSandboxRerunResult:
    rerun_id: str
    application_id: str
    candidate_id: str
    algorithm_id: str
    target_procedure: str
    question_id: str
    problem_class: str
    evidence_kind: str
    baseline_metrics: dict[str, float]
    guarded_metrics: dict[str, float]
    nonfinite_baseline_metrics: tuple[str, ...]
    registry_rerun_completed: bool
    guard_plan_replayed: bool
    production_patch_applied: bool
    rerun_status: str
    required_next_gate: str
    ok: bool
    errors: tuple[str, ...] = ()


def rerun_algorithm_repair_sandbox_applications(
    apply_dir: Path,
    out_dir: Path | None = None,
    *,
    question_file: Path = Path("examples/research_questions.json"),
    n_runs: int = 50,
    seed: int = 20260530,
) -> dict[str, object]:
    """Replay sandbox-applied repair plans against current vetted simulators.

    This stage supplies rerun-style evidence without mutating production code or
    executing generated patches. It locates the target procedure in the open
    research-question registry, reruns the current vetted simulator, applies a
    ledger-level finite/numerical guard replay, and records the remaining gate
    required before any code promotion.
    """

    errors: list[str] = []
    manifest_path = apply_dir / "algorithm_repair_sandbox_apply_manifest.json"
    manifest = _load_json(manifest_path, errors)
    results_path = Path(
        str(manifest.get("results_jsonl", apply_dir / "algorithm_repair_sandbox_apply_results.jsonl"))
    )
    if not results_path.is_absolute() and not results_path.exists():
        results_path = apply_dir / results_path
    applications = _load_jsonl(results_path, errors)
    registry_audit = audit_research_algorithm_registry()
    procedure_index = _build_procedure_index(question_file)
    results = [
        _rerun_application(
            row,
            procedure_index=procedure_index,
            registry_audit_ok=bool(registry_audit.get("all_ok")),
            n_runs=n_runs,
            seed=seed,
        )
        for row in applications
        if isinstance(row, dict)
    ]
    by_status = Counter(row.rerun_status for row in results)
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_SANDBOX_RERUN_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "apply_dir": str(apply_dir),
        "apply_manifest": str(manifest_path),
        "apply_results_jsonl": str(results_path),
        "question_file": str(question_file),
        "n_runs": int(n_runs),
        "seed": int(seed),
        "algorithm_audit_all_ok": bool(registry_audit.get("all_ok")),
        "algorithm_registry_fingerprint": str(registry_audit.get("registry_fingerprint", "")),
        "n_candidates": len(results),
        "n_ok": sum(1 for row in results if row.ok),
        "all_ok": not errors and all(row.ok for row in results),
        "errors": errors,
        "by_rerun_status": dict(sorted(by_status.items())),
        "results": [asdict(row) for row in results],
        "dataset_fingerprint": stable_hash([asdict(row) for row in results]),
        "limitations": [
            "rerun uses the current vetted registry implementation, not arbitrary generated code",
            "guard replay is ledger-level evidence and is not a production code patch",
            "promotion still requires an isolated patched workspace and before/after simulation comparison",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / "algorithm_repair_sandbox_rerun_results.jsonl"
        _write_jsonl(result_path, [asdict(row) for row in results])
        payload["results_jsonl"] = str(result_path)
        (out_dir / "algorithm_repair_sandbox_rerun_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "algorithm_repair_sandbox_rerun.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _build_procedure_index(question_file: Path) -> dict[tuple[str, str], tuple[str, ResearchProblemSpec, CandidateProcedure]]:
    formalizer = ProblemFormalizer()
    planner = TheoryPlanner()
    index: dict[tuple[str, str], tuple[str, ResearchProblemSpec, CandidateProcedure]] = {}
    for question in load_open_research_questions(question_file):
        problem = formalizer.formalize(question)
        procedures, _goals = planner.plan(problem)
        for procedure in attach_research_algorithm_metadata(procedures):
            index[(procedure.id, procedure.algorithm)] = (question.id, problem, procedure)
    return index


def _rerun_application(
    row: dict[str, Any],
    *,
    procedure_index: dict[tuple[str, str], tuple[str, ResearchProblemSpec, CandidateProcedure]],
    registry_audit_ok: bool,
    n_runs: int,
    seed: int,
) -> AlgorithmRepairSandboxRerunResult:
    errors: list[str] = []
    application_id = str(row.get("application_id", ""))
    candidate_id = str(row.get("candidate_id", ""))
    algorithm_id = str(row.get("algorithm_id", ""))
    target_procedure = str(row.get("target_procedure", ""))
    if row.get("ok") is not True:
        errors.append("sandbox apply result ok flag is false")
    if row.get("sandbox_artifact_created") is not True:
        errors.append("sandbox apply artifact was not created")
    if row.get("patch_applied_to_production") is not False:
        errors.append("sandbox apply result must not mutate production")
    if not registry_audit_ok:
        errors.append("current algorithm registry audit is not OK")

    question_id = ""
    problem_class = ""
    baseline_metrics: dict[str, float] = {}
    guarded_metrics: dict[str, float] = {}
    nonfinite_metrics: tuple[str, ...] = ()
    rerun_completed = False
    found = procedure_index.get((target_procedure, algorithm_id))
    if found is None:
        errors.append("target procedure/algorithm pair not found in open-question registry")
    else:
        question_id, problem, procedure = found
        problem_class = problem.problem_class
        simulations = ResearchSimulator(n_runs=n_runs, seed=seed).run(problem, [procedure])
        if not simulations:
            errors.append("simulator returned no result for target procedure")
        else:
            rerun_completed = True
            baseline_metrics = _finite_metric_payload(simulations[0].metrics, include_nonfinite=True)
            nonfinite_metrics = tuple(
                sorted(
                    key
                    for key, value in simulations[0].metrics.items()
                    if isinstance(value, (int, float)) and not math.isfinite(float(value))
                )
            )
            guarded_metrics = _guarded_metric_payload(simulations[0].metrics, nonfinite_metrics)
            _validate_rerun_metrics(guarded_metrics, errors)

    ok = not errors
    return AlgorithmRepairSandboxRerunResult(
        rerun_id="algorithm_repair_sandbox_rerun:" f"{stable_hash([application_id, target_procedure, n_runs, seed])[:16]}",
        application_id=application_id,
        candidate_id=candidate_id,
        algorithm_id=algorithm_id,
        target_procedure=target_procedure,
        question_id=question_id,
        problem_class=problem_class,
        evidence_kind="current_registry_rerun_with_guard_replay",
        baseline_metrics=baseline_metrics,
        guarded_metrics=guarded_metrics,
        nonfinite_baseline_metrics=nonfinite_metrics,
        registry_rerun_completed=rerun_completed,
        guard_plan_replayed=rerun_completed,
        production_patch_applied=False,
        rerun_status="RERUN_EVIDENCE_READY" if ok else "RERUN_EVIDENCE_BLOCKED",
        required_next_gate=(
            "apply the bounded repair in an isolated code workspace, rerun algorithm audit, "
            "compare patched-vs-baseline finite simulation diagnostics, then promote only by reviewed commit"
        ),
        ok=ok,
        errors=tuple(errors),
    )


def _finite_metric_payload(metrics: dict[str, float], *, include_nonfinite: bool) -> dict[str, float]:
    payload: dict[str, float] = {}
    for key, value in metrics.items():
        if not isinstance(value, (int, float)):
            continue
        number = float(value)
        if math.isfinite(number) or include_nonfinite:
            payload[key] = number
    return payload


def _guarded_metric_payload(metrics: dict[str, float], nonfinite_metrics: tuple[str, ...]) -> dict[str, float]:
    payload = _finite_metric_payload(metrics, include_nonfinite=False)
    n_runs = float(metrics.get("n_runs", 0.0)) if isinstance(metrics.get("n_runs"), (int, float)) else 0.0
    n_failed = float(metrics.get("n_failed", 0.0)) if isinstance(metrics.get("n_failed"), (int, float)) else 0.0
    payload["guard_replay_completed"] = 1.0
    payload["guard_nonfinite_metrics"] = float(len(nonfinite_metrics))
    payload["guard_failed_fraction"] = n_failed / n_runs if n_runs > 0.0 else 1.0
    payload["production_patch_applied"] = 0.0
    return payload


def _validate_rerun_metrics(metrics: dict[str, float], errors: list[str]) -> None:
    nonfinite = sorted(key for key, value in metrics.items() if not math.isfinite(float(value)))
    if nonfinite:
        errors.append("guarded rerun metrics contain non-finite values: " + ", ".join(nonfinite))
    if float(metrics.get("guard_failed_fraction", 1.0)) > 0.05:
        errors.append("guarded rerun failed-replicate fraction exceeds 0.05")


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Algorithm Repair Sandbox Rerun Evaluation",
        "",
        f"- Apply dir: `{payload.get('apply_dir')}`",
        f"- Rerun artifacts: {payload.get('n_ok')}/{payload.get('n_candidates')}",
        f"- Algorithm audit OK: {payload.get('algorithm_audit_all_ok')}",
        f"- Runs per rerun: {payload.get('n_runs')}",
        "",
        "## Rerun Status",
        "",
    ]
    by_status = payload.get("by_rerun_status", {})
    if isinstance(by_status, dict) and by_status:
        for status, count in sorted(by_status.items()):
            lines.append(f"- `{status}`: {count}")
    else:
        lines.append("- none")
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)
