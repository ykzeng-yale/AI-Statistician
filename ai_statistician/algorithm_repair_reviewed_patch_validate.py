from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


ALGORITHM_REPAIR_REVIEWED_PATCH_VALIDATE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmRepairReviewedPatchValidationResult:
    validation_id: str
    apply_id: str
    plan_id: str
    algorithm_id: str
    target_procedure: str
    source_file: str
    patch_kind: str
    isolated_workspace: str
    patched_package_file: str
    subprocess_returncode: int
    import_ok: bool
    algorithm_audit_ok: bool
    simulation_completed: bool
    patched_metric_present: bool
    finite_metrics_ok: bool
    metrics: dict[str, float]
    stdout_json: dict[str, object]
    stderr_tail: str
    production_patch_applied: bool
    promotion_ready: bool
    next_gate: str
    ok: bool
    errors: tuple[str, ...] = ()


def validate_reviewed_algorithm_repair_patches(
    apply_dir: Path,
    out_dir: Path,
    *,
    source_root: Path = Path("."),
    question_file: Path = Path("examples/research_questions.json"),
    n_runs: int = 10,
    seed: int = 20260601,
) -> dict[str, object]:
    """Validate isolated reviewed source patches by importing a copied package.

    The previous lane writes a patched source file and diff.  This lane copies
    the package into a validation workspace, overlays the patched file, imports
    that copied package in a subprocess, and reruns the affected procedure's
    deterministic simulator.  It still does not mutate production source.
    """

    errors: list[str] = []
    manifest_path = apply_dir / "algorithm_repair_reviewed_patch_apply_manifest.json"
    manifest = _load_json(manifest_path, errors)
    results_path = Path(str(manifest.get("results_jsonl", apply_dir / "algorithm_repair_reviewed_patch_apply_results.jsonl")))
    if not results_path.is_absolute() and not results_path.exists():
        results_path = apply_dir / results_path
    apply_results = _load_jsonl(results_path, errors)
    validation_root = out_dir / "isolated_validation_workspace"
    results = [
        _validate_apply_result(
            row,
            source_root=source_root,
            validation_root=validation_root,
            question_file=question_file,
            n_runs=n_runs,
            seed=seed,
        )
        for row in apply_results
        if isinstance(row, dict)
    ]
    by_kind = Counter(row.patch_kind for row in results)
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "algorithm_repair_reviewed_patch_validate_results.jsonl"
    _write_jsonl(result_path, [asdict(row) for row in results])
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_REVIEWED_PATCH_VALIDATE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "apply_dir": str(apply_dir),
        "apply_manifest": str(manifest_path),
        "apply_results_jsonl": str(results_path),
        "source_root": str(source_root),
        "question_file": str(question_file),
        "n_runs": int(n_runs),
        "seed": int(seed),
        "isolated_validation_workspace": str(validation_root),
        "n_candidates": len(results),
        "n_ok": sum(1 for row in results if row.ok),
        "n_import_ok": sum(1 for row in results if row.import_ok),
        "n_algorithm_audit_ok": sum(1 for row in results if row.algorithm_audit_ok),
        "n_simulation_completed": sum(1 for row in results if row.simulation_completed),
        "n_patched_metric_present": sum(1 for row in results if row.patched_metric_present),
        "n_finite_metrics_ok": sum(1 for row in results if row.finite_metrics_ok),
        "n_production_patches_applied": sum(1 for row in results if row.production_patch_applied),
        "n_promotion_ready": sum(1 for row in results if row.promotion_ready),
        "by_patch_kind": dict(sorted(by_kind.items())),
        "results_jsonl": str(result_path),
        "dataset_fingerprint": stable_hash([asdict(row) for row in results]),
        "all_ok": (
            not errors
            and bool(manifest.get("all_ok"))
            and all(row.ok for row in results)
            and not any(row.production_patch_applied for row in results)
            and not any(row.promotion_ready for row in results)
        ),
        "errors": errors,
        "limitations": [
            "validates the copied package in a subprocess; production source is not mutated",
            "runs a small affected-procedure simulation, not the full research-system audit",
            "promotion still requires applying the reviewed diff to production and rerunning full validation",
        ],
    }
    (out_dir / "algorithm_repair_reviewed_patch_validate_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "algorithm_repair_reviewed_patch_validate.md").write_text(
        _markdown_report(payload, results),
        encoding="utf-8",
    )
    return payload


def _validate_apply_result(
    row: dict[str, Any],
    *,
    source_root: Path,
    validation_root: Path,
    question_file: Path,
    n_runs: int,
    seed: int,
) -> AlgorithmRepairReviewedPatchValidationResult:
    errors: list[str] = []
    apply_id = str(row.get("apply_id", ""))
    plan_id = str(row.get("plan_id", ""))
    algorithm_id = str(row.get("algorithm_id", ""))
    target_procedure = str(row.get("target_procedure", ""))
    source_file = str(row.get("source_file", ""))
    patch_kind = str(row.get("patch_kind", ""))
    if row.get("ok") is not True:
        errors.append("reviewed patch apply result ok flag is false")
    if row.get("production_patch_applied") is True:
        errors.append("reviewed patch apply result must not mutate production")
    patched_source = Path(str(row.get("patched_source_file", "")))
    if not patched_source.exists():
        errors.append(f"patched source file missing: {patched_source}")

    workspace = validation_root / _safe_id(apply_id or plan_id or algorithm_id)
    package_root = workspace / "package_root"
    copied_package = package_root / "ai_statistician"
    patched_package_file = package_root / source_file if source_file else package_root / "missing.py"
    if copied_package.exists():
        shutil.rmtree(copied_package)
    package_root.mkdir(parents=True, exist_ok=True)
    source_package = source_root / "ai_statistician"
    if not source_package.exists():
        errors.append(f"source package missing: {source_package}")
    else:
        shutil.copytree(source_package, copied_package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if patched_source.exists() and source_file:
        patched_package_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(patched_source, patched_package_file)

    stdout_json: dict[str, object] = {}
    stderr_tail = ""
    returncode = -1
    if not errors:
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                _validation_script(),
                str(question_file.resolve()),
                target_procedure,
                algorithm_id,
                str(n_runs),
                str(seed),
            ],
            cwd=str(package_root),
            env=_subprocess_env(package_root),
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        returncode = int(proc.returncode)
        stderr_tail = proc.stderr[-2000:]
        try:
            stdout_json = json.loads(proc.stdout.strip() or "{}")
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse validation subprocess JSON: {exc}; stdout={proc.stdout[-500:]}")
        if returncode != 0:
            errors.append(f"validation subprocess failed with returncode={returncode}: {stderr_tail[-500:]}")

    metrics = {
        str(key): float(value)
        for key, value in (stdout_json.get("metrics", {}) if isinstance(stdout_json.get("metrics"), dict) else {}).items()
        if isinstance(value, (int, float))
    }
    import_ok = bool(stdout_json.get("import_ok"))
    algorithm_audit_ok = bool(stdout_json.get("algorithm_audit_ok"))
    simulation_completed = bool(stdout_json.get("simulation_completed"))
    patched_metric_present = bool(stdout_json.get("patched_metric_present"))
    finite_metrics_ok = bool(stdout_json.get("finite_metrics_ok"))
    if returncode == 0:
        for flag, message in (
            (import_ok, "copied package import failed"),
            (algorithm_audit_ok, "algorithm audit failed inside copied package"),
            (simulation_completed, "affected procedure simulation did not complete"),
            (patched_metric_present, "patched finite-guard metric is missing from simulation output"),
            (finite_metrics_ok, "simulation metrics contain non-finite values"),
        ):
            if not flag:
                errors.append(message)
    ok = not errors
    return AlgorithmRepairReviewedPatchValidationResult(
        validation_id="algorithm_repair_reviewed_patch_validate:"
        f"{stable_hash([apply_id, returncode, metrics])[:16]}",
        apply_id=apply_id,
        plan_id=plan_id,
        algorithm_id=algorithm_id,
        target_procedure=target_procedure,
        source_file=source_file,
        patch_kind=patch_kind,
        isolated_workspace=str(workspace),
        patched_package_file=str(patched_package_file),
        subprocess_returncode=returncode,
        import_ok=import_ok,
        algorithm_audit_ok=algorithm_audit_ok,
        simulation_completed=simulation_completed,
        patched_metric_present=patched_metric_present,
        finite_metrics_ok=finite_metrics_ok,
        metrics=metrics,
        stdout_json=stdout_json,
        stderr_tail=stderr_tail,
        production_patch_applied=False,
        promotion_ready=False,
        next_gate="apply reviewed diff to production source, rerun before/after simulation and full research-system audit",
        ok=ok,
        errors=tuple(errors),
    )


def _validation_script() -> str:
    return r'''
import json
import math
import sys
from pathlib import Path

payload = {
    "import_ok": False,
    "algorithm_audit_ok": False,
    "simulation_completed": False,
    "patched_metric_present": False,
    "finite_metrics_ok": False,
    "metrics": {},
    "errors": [],
}
try:
    from ai_statistician.research_lab import (
        ProblemFormalizer,
        ResearchSimulator,
        TheoryPlanner,
        attach_research_algorithm_metadata,
        audit_research_algorithm_registry,
        load_open_research_questions,
    )
    payload["import_ok"] = True
    question_file = Path(sys.argv[1])
    target_procedure = sys.argv[2]
    algorithm_id = sys.argv[3]
    n_runs = int(sys.argv[4])
    seed = int(sys.argv[5])
    audit = audit_research_algorithm_registry()
    payload["algorithm_audit_ok"] = bool(audit.get("all_ok"))
    formalizer = ProblemFormalizer()
    planner = TheoryPlanner()
    found = None
    for question in load_open_research_questions(question_file):
        problem = formalizer.formalize(question)
        procedures, _goals = planner.plan(problem)
        for procedure in attach_research_algorithm_metadata(procedures):
            if procedure.id == target_procedure and procedure.algorithm == algorithm_id:
                found = (problem, procedure)
                break
        if found is not None:
            break
    if found is None:
        payload["errors"].append("target procedure not found")
    else:
        problem, procedure = found
        rows = ResearchSimulator(n_runs=n_runs, seed=seed).run(problem, [procedure])
        if not rows:
            payload["errors"].append("simulator returned no rows")
        else:
            metrics = dict(rows[0].metrics)
            payload["metrics"] = {
                str(key): float(value)
                for key, value in metrics.items()
                if isinstance(value, (int, float))
            }
            payload["simulation_completed"] = True
            payload["patched_metric_present"] = float(metrics.get("finite_guard_patch_applied", 0.0)) == 1.0
            payload["finite_metrics_ok"] = all(
                math.isfinite(float(value))
                for value in metrics.values()
                if isinstance(value, (int, float))
            )
except Exception as exc:
    payload["errors"].append(f"{type(exc).__name__}: {exc}")

print(json.dumps(payload, sort_keys=True))
sys.exit(0 if payload["import_ok"] and payload["algorithm_audit_ok"] and payload["simulation_completed"] else 1)
'''


def _subprocess_env(package_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(package_root)
    return env


def _safe_id(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)[:80] or "patch_validation"


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


def _markdown_report(
    payload: dict[str, object],
    results: list[AlgorithmRepairReviewedPatchValidationResult],
) -> str:
    lines = [
        "# Algorithm Repair Reviewed Patch Validation",
        "",
        f"- Apply dir: `{payload.get('apply_dir')}`",
        f"- Validation workspace: `{payload.get('isolated_validation_workspace')}`",
        f"- Validated candidates: {payload.get('n_ok')}/{payload.get('n_candidates')}",
        f"- Imports OK: {payload.get('n_import_ok')}",
        f"- Simulations completed: {payload.get('n_simulation_completed')}",
        f"- Patched metric present: {payload.get('n_patched_metric_present')}",
        f"- Production patches applied: {payload.get('n_production_patches_applied')}",
        "",
        "## Candidates",
        "",
    ]
    if results:
        for row in results:
            lines.append(
                f"- `{row.validation_id}` procedure `{row.target_procedure}` "
                f"import={row.import_ok} simulation={row.simulation_completed}"
            )
    else:
        lines.append("- none")
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)
