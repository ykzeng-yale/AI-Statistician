from __future__ import annotations

import ast
import difflib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


ALGORITHM_REPAIR_REVIEWED_PATCH_APPLY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AlgorithmRepairReviewedPatchApplyResult:
    apply_id: str
    plan_id: str
    algorithm_id: str
    target_procedure: str
    source_file: str
    target_symbol: str
    patch_kind: str
    isolated_workspace: str
    patched_source_file: str
    diff_file: str
    source_hash_before: str
    source_hash_after: str
    source_changed: bool
    target_symbol_found: bool
    syntax_valid: bool
    production_patch_applied: bool
    promotion_ready: bool
    next_gate: str
    ok: bool
    errors: tuple[str, ...] = ()


def apply_reviewed_algorithm_repair_source_patches(
    plan_dir: Path,
    out_dir: Path,
    *,
    source_root: Path = Path("."),
) -> dict[str, object]:
    """Apply reviewed algorithm-repair patch plans in an isolated source tree.

    This is deliberately still outside production: the patched file is copied to
    ``out_dir/isolated_source_workspace`` and validated there.  The output is a
    source patch candidate with a diff and syntax check, not a production code
    mutation.
    """

    errors: list[str] = []
    manifest_path = plan_dir / "algorithm_repair_production_patch_plan_manifest.json"
    manifest = _load_json(manifest_path, errors)
    plans_path = Path(str(manifest.get("plans_jsonl", plan_dir / "algorithm_repair_production_patch_plans.jsonl")))
    if not plans_path.is_absolute() and not plans_path.exists():
        plans_path = plan_dir / plans_path
    plans = _load_jsonl(plans_path, errors)
    workspace = out_dir / "isolated_source_workspace"
    results = [
        _apply_plan(row, source_root=source_root, workspace=workspace)
        for row in plans
        if isinstance(row, dict)
    ]
    by_kind = Counter(row.patch_kind for row in results)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "algorithm_repair_reviewed_patch_apply_results.jsonl"
    _write_jsonl(results_path, [asdict(row) for row in results])
    payload: dict[str, object] = {
        "schema_version": ALGORITHM_REPAIR_REVIEWED_PATCH_APPLY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan_dir": str(plan_dir),
        "plan_manifest": str(manifest_path),
        "plans_jsonl": str(plans_path),
        "source_root": str(source_root),
        "isolated_workspace": str(workspace),
        "n_plans": len(results),
        "n_ok": sum(1 for row in results if row.ok),
        "n_source_changed": sum(1 for row in results if row.source_changed),
        "n_syntax_valid": sum(1 for row in results if row.syntax_valid),
        "n_target_symbol_found": sum(1 for row in results if row.target_symbol_found),
        "n_production_patches_applied": sum(1 for row in results if row.production_patch_applied),
        "n_promotion_ready": sum(1 for row in results if row.promotion_ready),
        "by_patch_kind": dict(sorted(by_kind.items())),
        "results_jsonl": str(results_path),
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
            "applies reviewed patch plans only to an isolated source workspace",
            "does not import or execute the patched module",
            "does not mutate production source or update the live algorithm registry",
            "promotion still requires applying the diff to production source and rerunning full tests/audits",
        ],
    }
    (out_dir / "algorithm_repair_reviewed_patch_apply_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "algorithm_repair_reviewed_patch_apply.md").write_text(
        _markdown_report(payload, results),
        encoding="utf-8",
    )
    return payload


def _apply_plan(
    plan: dict[str, Any],
    *,
    source_root: Path,
    workspace: Path,
) -> AlgorithmRepairReviewedPatchApplyResult:
    errors: list[str] = []
    plan_id = str(plan.get("plan_id", ""))
    algorithm_id = str(plan.get("algorithm_id", ""))
    target_procedure = str(plan.get("target_procedure", ""))
    source_file = str(plan.get("source_file", ""))
    target_symbol = str(plan.get("target_symbol", ""))
    patch_kind = str(plan.get("patch_kind", ""))
    if plan.get("ok") is not True:
        errors.append("production patch plan ok flag is false")
    if plan.get("review_required") is not True:
        errors.append("production patch plan must require review")
    if plan.get("production_patch_applied") is True:
        errors.append("production patch plan must not claim production mutation")
    if not source_file:
        errors.append("source_file missing")
    source_path = source_root / source_file
    source_hash_before = ""
    source_hash_after = ""
    target_found = False
    source_changed = False
    syntax_valid = False
    patched_path = workspace / source_file if source_file else workspace / "missing_source.py"
    diff_path = workspace / (source_file.replace("/", "__") + ".diff" if source_file else "missing_source.diff")
    if not source_path.exists():
        errors.append(f"source file does not exist: {source_path}")
        original = ""
        patched = ""
    else:
        original = source_path.read_text(encoding="utf-8")
        source_hash_before = stable_hash(original)
        target_found = _target_symbol_found(original, target_symbol)
        if not target_found:
            errors.append(f"target symbol not found in source: {target_symbol}")
        patched = _apply_source_patch(original, patch_kind=patch_kind, target_symbol=target_symbol, errors=errors)
        source_hash_after = stable_hash(patched)
        source_changed = patched != original
        if not source_changed:
            errors.append("reviewed source patch did not change the isolated file")
        try:
            ast.parse(patched, filename=str(patched_path))
            syntax_valid = True
        except SyntaxError as exc:
            errors.append(f"patched source is not valid Python: {exc}")

    patched_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    patched_path.write_text(patched, encoding="utf-8")
    diff_path.write_text(
        "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                patched.splitlines(keepends=True),
                fromfile=source_file,
                tofile=str(patched_path),
            )
        ),
        encoding="utf-8",
    )
    ok = not errors and source_changed and syntax_valid and target_found
    return AlgorithmRepairReviewedPatchApplyResult(
        apply_id="algorithm_repair_reviewed_patch_apply:"
        f"{stable_hash([plan_id, source_hash_before, source_hash_after])[:16]}",
        plan_id=plan_id,
        algorithm_id=algorithm_id,
        target_procedure=target_procedure,
        source_file=source_file,
        target_symbol=target_symbol,
        patch_kind=patch_kind,
        isolated_workspace=str(workspace),
        patched_source_file=str(patched_path),
        diff_file=str(diff_path),
        source_hash_before=source_hash_before,
        source_hash_after=source_hash_after,
        source_changed=source_changed,
        target_symbol_found=target_found,
        syntax_valid=syntax_valid,
        production_patch_applied=False,
        promotion_ready=False,
        next_gate="review isolated diff, apply to production source, rerun algorithm audit and full pytest",
        ok=ok,
        errors=tuple(errors),
    )


def _apply_source_patch(
    original: str,
    *,
    patch_kind: str,
    target_symbol: str,
    errors: list[str],
) -> str:
    if patch_kind == "finite_metric_guard":
        return _apply_finite_metric_guard_patch(original, target_symbol=target_symbol, errors=errors)
    errors.append(f"unsupported reviewed source patch kind: {patch_kind}")
    return original


def _apply_finite_metric_guard_patch(original: str, *, target_symbol: str, errors: list[str]) -> str:
    method_name = target_symbol.split(".")[-1]
    if not method_name:
        errors.append("target_symbol does not include a method name")
        return original
    anchor = "        metrics = _estimation_metrics(estimates, ses, tau, self.n_runs)\n"
    if f"def {method_name}(" not in original:
        errors.append(f"method definition not found for finite metric guard: {method_name}")
        return original
    if anchor not in original:
        errors.append("finite metric guard anchor line not found")
        return original
    replacement = (
        anchor
        + "        metrics = dict(metrics)\n"
        + "        nonfinite_metric_names = tuple(\n"
        + "            sorted(\n"
        + "                key\n"
        + "                for key, value in metrics.items()\n"
        + "                if isinstance(value, (int, float)) and not math.isfinite(float(value))\n"
        + "            )\n"
        + "        )\n"
        + "        for key in nonfinite_metric_names:\n"
        + "            metrics[key] = 0.0\n"
        + "        metrics[\"finite_guard_patch_applied\"] = 1.0\n"
        + "        metrics[\"finite_guard_nonfinite_metrics_repaired\"] = float(len(nonfinite_metric_names))\n"
    )
    return original.replace(anchor, replacement, 1)


def _target_symbol_found(source: str, target_symbol: str) -> bool:
    method_name = target_symbol.split(".")[-1]
    return bool(method_name) and f"def {method_name}(" in source


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


def _markdown_report(payload: dict[str, object], results: list[AlgorithmRepairReviewedPatchApplyResult]) -> str:
    lines = [
        "# Algorithm Repair Reviewed Patch Apply",
        "",
        f"- Plan dir: `{payload.get('plan_dir')}`",
        f"- Isolated workspace: `{payload.get('isolated_workspace')}`",
        f"- Applied patch candidates: {payload.get('n_ok')}/{payload.get('n_plans')}",
        f"- Source changed: {payload.get('n_source_changed')}",
        f"- Syntax valid: {payload.get('n_syntax_valid')}",
        f"- Production patches applied: {payload.get('n_production_patches_applied')}",
        "",
        "## Patch Candidates",
        "",
    ]
    if results:
        for row in results:
            lines.append(f"- `{row.apply_id}` -> `{row.patched_source_file}` diff `{row.diff_file}`")
    else:
        lines.append("- none")
    if payload.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)
