from __future__ import annotations

import importlib.util
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


ALGORITHM_REPAIR_SANDBOX_PATCH_EVAL_SCHEMA_VERSION = 1
PATCH_MODULE_NAME = "ai_statistician_isolated_algorithm_patch"


@dataclass(frozen=True)
class AlgorithmRepairSandboxPatchEvalResult:
    patch_eval_id: str
    application_id: str
    candidate_id: str
    algorithm_id: str
    target_procedure: str
    question_id: str
    problem_class: str
    patch_application_mode: str
    isolated_workspace: str
    patch_module: str
    patch_source_hash: str
    baseline_metrics: dict[str, float]
    patched_metrics: dict[str, float]
    metric_deltas: dict[str, float]
    nonfinite_baseline_metrics: tuple[str, ...]
    nonfinite_patched_metrics: tuple[str, ...]
    registry_audit_ok: bool
    baseline_rerun_completed: bool
    isolated_patch_executed: bool
    before_after_comparison_ready: bool
    production_patch_applied: bool
    promotion_ready: bool
    comparison_status: str
    required_next_gate: str
    ok: bool
    errors: tuple[str, ...] = ()


def evaluate_algorithm_repair_sandbox_patches(
    apply_dir: Path,
    out_dir: Path | None = None,
    *,
    question_file: Path = Path("examples/research_questions.json"),
    n_runs: int = 50,
    seed: int = 20260531,
) -> dict[str, object]:
    """Execute deterministic algorithm repair patches in an isolated workspace.

    This is the first executable patch lane, but it remains intentionally
    bounded: it never runs LLM-provided code and never mutates the production
    registry.  Instead it writes a deterministic finite-metric guard patch into
    an output workspace, imports that module, compares baseline simulator output
    against the isolated patched simulator, and records whether the comparison
    is ready for human-reviewed promotion.
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
    workspace = (out_dir or Path("runs/algorithm_repair_sandbox_patch_eval")) / "isolated_patch_workspace"
    patch_module = _write_patch_module(workspace)
    patched_simulator_cls = _load_patched_simulator(patch_module, errors)

    results = [
        _evaluate_application(
            row,
            procedure_index=procedure_index,
            patched_simulator_cls=patched_simulator_cls,
            patch_module=patch_module,
            registry_audit_ok=bool(registry_audit.get("all_ok")),
            n_runs=n_runs,
            seed=seed,
        )
        for row in applications
        if isinstance(row, dict)
    ]
    by_status = Counter(row.comparison_status for row in results)
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_SANDBOX_PATCH_EVAL_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "apply_dir": str(apply_dir),
        "apply_manifest": str(manifest_path),
        "apply_results_jsonl": str(results_path),
        "question_file": str(question_file),
        "n_runs": int(n_runs),
        "seed": int(seed),
        "isolated_workspace": str(workspace),
        "patch_module": str(patch_module),
        "patch_source_hash": stable_hash(patch_module.read_text(encoding="utf-8")) if patch_module.exists() else "",
        "algorithm_audit_all_ok": bool(registry_audit.get("all_ok")),
        "algorithm_registry_fingerprint": str(registry_audit.get("registry_fingerprint", "")),
        "n_candidates": len(results),
        "n_ok": sum(1 for row in results if row.ok),
        "n_isolated_patches_executed": sum(1 for row in results if row.isolated_patch_executed),
        "n_before_after_comparisons": sum(1 for row in results if row.before_after_comparison_ready),
        "n_production_patches_applied": sum(1 for row in results if row.production_patch_applied),
        "n_promotion_ready": sum(1 for row in results if row.promotion_ready),
        "all_ok": not errors and all(row.ok for row in results),
        "errors": errors,
        "by_comparison_status": dict(sorted(by_status.items())),
        "results": [asdict(row) for row in results],
        "dataset_fingerprint": stable_hash([asdict(row) for row in results]),
        "limitations": [
            "the executed patch is a deterministic finite-metric guard template, not arbitrary generated code",
            "production_patch_applied is always false in this audit lane",
            "promotion still requires reviewed source changes and a release commit after before/after evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / "algorithm_repair_sandbox_patch_eval_results.jsonl"
        _write_jsonl(result_path, [asdict(row) for row in results])
        payload["results_jsonl"] = str(result_path)
        (out_dir / "algorithm_repair_sandbox_patch_eval_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "algorithm_repair_sandbox_patch_eval.md").write_text(
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


def _write_patch_module(workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    module_path = workspace / "patched_research_simulator.py"
    module_path.write_text(_patch_module_source(), encoding="utf-8")
    return module_path


def _patch_module_source() -> str:
    return '''from __future__ import annotations

import math
from dataclasses import replace

from ai_statistician.research_lab import ResearchSimulator


class PatchedResearchSimulator(ResearchSimulator):
    """Deterministic finite-metric guard patch used only in isolated eval."""

    def run(self, problem, procedures):
        rows = super().run(problem, procedures)
        return [self._with_finite_metric_guard(row) for row in rows]

    def _with_finite_metric_guard(self, row):
        metrics = dict(row.metrics)
        nonfinite = tuple(
            sorted(
                key
                for key, value in metrics.items()
                if isinstance(value, (int, float)) and not math.isfinite(float(value))
            )
        )
        for key in nonfinite:
            metrics[key] = 0.0
        n_runs = float(metrics.get("n_runs", 0.0)) if isinstance(metrics.get("n_runs"), (int, float)) else 0.0
        n_failed = float(metrics.get("n_failed", 0.0)) if isinstance(metrics.get("n_failed"), (int, float)) else 0.0
        metrics["finite_guard_patch_applied"] = 1.0
        metrics["finite_guard_nonfinite_metrics_repaired"] = float(len(nonfinite))
        metrics["finite_guard_failed_fraction"] = n_failed / n_runs if n_runs > 0.0 else 1.0
        return replace(
            row,
            metrics=metrics,
            feedback=row.feedback + " | isolated finite-metric guard patch evaluated",
        )
'''


def _load_patched_simulator(module_path: Path, errors: list[str]):
    if not module_path.exists():
        errors.append(f"missing patch module: {module_path}")
        return None
    try:
        spec = importlib.util.spec_from_file_location(PATCH_MODULE_NAME, module_path)
        if spec is None or spec.loader is None:
            errors.append("failed to create import spec for isolated patch module")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "PatchedResearchSimulator")
    except Exception as exc:
        errors.append(f"failed to import isolated patch module: {type(exc).__name__}: {exc}")
        return None


def _evaluate_application(
    row: dict[str, Any],
    *,
    procedure_index: dict[tuple[str, str], tuple[str, ResearchProblemSpec, CandidateProcedure]],
    patched_simulator_cls: Any,
    patch_module: Path,
    registry_audit_ok: bool,
    n_runs: int,
    seed: int,
) -> AlgorithmRepairSandboxPatchEvalResult:
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
    if patched_simulator_cls is None:
        errors.append("isolated patch simulator class is unavailable")

    question_id = ""
    problem_class = ""
    baseline_metrics: dict[str, float] = {}
    patched_metrics: dict[str, float] = {}
    metric_deltas: dict[str, float] = {}
    nonfinite_baseline: tuple[str, ...] = ()
    nonfinite_patched: tuple[str, ...] = ()
    baseline_completed = False
    patch_executed = False
    found = procedure_index.get((target_procedure, algorithm_id))
    if found is None:
        errors.append("target procedure/algorithm pair not found in open-question registry")
    elif patched_simulator_cls is not None:
        question_id, problem, procedure = found
        problem_class = problem.problem_class
        baseline_rows = ResearchSimulator(n_runs=n_runs, seed=seed).run(problem, [procedure])
        patched_rows = patched_simulator_cls(n_runs=n_runs, seed=seed).run(problem, [procedure])
        if not baseline_rows:
            errors.append("baseline simulator returned no result for target procedure")
        else:
            baseline_completed = True
            baseline_metrics = _numeric_metrics(baseline_rows[0].metrics, include_nonfinite=True)
            nonfinite_baseline = _nonfinite_metric_names(baseline_rows[0].metrics)
        if not patched_rows:
            errors.append("isolated patched simulator returned no result for target procedure")
        else:
            patch_executed = True
            patched_metrics = _numeric_metrics(patched_rows[0].metrics, include_nonfinite=True)
            nonfinite_patched = _nonfinite_metric_names(patched_rows[0].metrics)
        if baseline_completed and patch_executed:
            metric_deltas = _metric_deltas(baseline_metrics, patched_metrics)
            if nonfinite_patched:
                errors.append("isolated patched metrics still contain non-finite values: " + ", ".join(nonfinite_patched))
            if float(patched_metrics.get("finite_guard_patch_applied", 0.0)) != 1.0:
                errors.append("isolated patch did not record finite_guard_patch_applied=1")

    comparison_ready = baseline_completed and patch_executed and not nonfinite_patched
    comparison_status = _comparison_status(
        errors=errors,
        nonfinite_baseline=nonfinite_baseline,
        nonfinite_patched=nonfinite_patched,
        metric_deltas=metric_deltas,
    )
    ok = not errors and comparison_ready
    return AlgorithmRepairSandboxPatchEvalResult(
        patch_eval_id="algorithm_repair_sandbox_patch_eval:"
        f"{stable_hash([application_id, target_procedure, n_runs, seed])[:16]}",
        application_id=application_id,
        candidate_id=candidate_id,
        algorithm_id=algorithm_id,
        target_procedure=target_procedure,
        question_id=question_id,
        problem_class=problem_class,
        patch_application_mode="isolated_workspace_deterministic_finite_guard",
        isolated_workspace=str(patch_module.parent),
        patch_module=str(patch_module),
        patch_source_hash=stable_hash(patch_module.read_text(encoding="utf-8")) if patch_module.exists() else "",
        baseline_metrics=baseline_metrics,
        patched_metrics=patched_metrics,
        metric_deltas=metric_deltas,
        nonfinite_baseline_metrics=nonfinite_baseline,
        nonfinite_patched_metrics=nonfinite_patched,
        registry_audit_ok=registry_audit_ok,
        baseline_rerun_completed=baseline_completed,
        isolated_patch_executed=patch_executed,
        before_after_comparison_ready=comparison_ready,
        production_patch_applied=False,
        promotion_ready=False,
        comparison_status=comparison_status,
        required_next_gate=(
            "review the isolated patch source, port it to production code in a normal commit, "
            "rerun algorithm audit and finite simulation before/after comparison, then promote"
        ),
        ok=ok,
        errors=tuple(errors),
    )


def _numeric_metrics(metrics: dict[str, float], *, include_nonfinite: bool) -> dict[str, float]:
    payload: dict[str, float] = {}
    for key, value in metrics.items():
        if not isinstance(value, (int, float)):
            continue
        number = float(value)
        if math.isfinite(number) or include_nonfinite:
            payload[key] = number
    return payload


def _nonfinite_metric_names(metrics: dict[str, float]) -> tuple[str, ...]:
    return tuple(
        sorted(
            key
            for key, value in metrics.items()
            if isinstance(value, (int, float)) and not math.isfinite(float(value))
        )
    )


def _metric_deltas(baseline: dict[str, float], patched: dict[str, float]) -> dict[str, float]:
    deltas: dict[str, float] = {}
    for key in sorted(set(baseline) & set(patched)):
        before = baseline[key]
        after = patched[key]
        if math.isfinite(before) and math.isfinite(after):
            deltas[key] = after - before
    return deltas


def _comparison_status(
    *,
    errors: list[str],
    nonfinite_baseline: tuple[str, ...],
    nonfinite_patched: tuple[str, ...],
    metric_deltas: dict[str, float],
) -> str:
    if errors:
        return "ISOLATED_PATCH_EVAL_BLOCKED"
    if nonfinite_baseline and not nonfinite_patched:
        return "ISOLATED_PATCH_REMOVED_NONFINITE_METRICS"
    changed = any(abs(value) > 1e-12 for value in metric_deltas.values())
    if changed:
        return "ISOLATED_PATCH_CHANGED_NUMERICAL_METRICS"
    return "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA"


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
        "# Algorithm Repair Sandbox Patch Evaluation",
        "",
        f"- Apply dir: `{payload.get('apply_dir')}`",
        f"- Isolated workspace: `{payload.get('isolated_workspace')}`",
        f"- Patch eval artifacts: {payload.get('n_ok')}/{payload.get('n_candidates')}",
        f"- Before/after comparisons: {payload.get('n_before_after_comparisons')}",
        f"- Production patches applied: {payload.get('n_production_patches_applied')}",
        "",
        "## Comparison Status",
        "",
    ]
    by_status = payload.get("by_comparison_status", {})
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
