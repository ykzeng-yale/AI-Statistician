from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .research_architect import KERNEL_PROOF_BOUNDARY


ARTIFACT_KIND = "SourceTheoremExactSemanticDefinitionLeanEnvironmentRepairExecutorManifest"
RESULT_ARTIFACT_KIND = "SourceTheoremExactSemanticDefinitionLeanEnvironmentRepairResult"
LEARNING_TASK = "source_theorem_exact_semantic_definition_lean_environment_repair_execution"
PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_EXECUTION_NOT_PROOF_EVIDENCE"
)
BOUNDARY = (
    "Exact semantic-definition Lean environment repair execution rows are Lake "
    "project/dependency/cache readiness diagnostics. They do not prove a semantic "
    "definition, source theorem, or proof candidate. Promotion still requires a "
    "later local Lean/AXLE verifier manifest for the repaired declaration and "
    "source theorem."
)


def run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    repair_executor_manifest: Path | None = None,
    environment_tasks_jsonl: Path | None = None,
) -> dict[str, Any]:
    task_path = resolve_source_theorem_exact_semantic_definition_environment_tasks_path(
        runtime_dir=runtime_dir,
        repair_executor_manifest=repair_executor_manifest,
        environment_tasks_jsonl=environment_tasks_jsonl,
    )
    tasks = _read_jsonl(task_path)
    rows = [
        _environment_repair_result(row)
        for row in tasks
        if isinstance(row, Mapping)
    ]
    learning_rows = [_learning_row(row) for row in rows]
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_lean_environment_repair_results.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(results_path, rows)
    _write_jsonl(learning_path, learning_rows)
    status_counts = Counter(str(row.get("environment_repair_status", "") or "") for row in rows)
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_runtime_dir": str(runtime_dir or ""),
        "source_repair_executor_manifest": str(repair_executor_manifest or ""),
        "source_environment_tasks_jsonl": str(task_path),
        "environment_repair_results_jsonl": str(results_path),
        "runtime_learning_rows_jsonl": str(learning_path),
        "n_tasks": len(tasks),
        "n_results": len(rows),
        "n_ready_to_rerun_lean_repair": sum(
            1 for row in rows if row.get("ready_to_rerun_lean_repair")
        ),
        "n_dependency_fetch_required": sum(
            1 for row in rows if row.get("dependency_fetch_required")
        ),
        "n_missing_lake_project": sum(
            1 for row in rows if row.get("environment_repair_status") == "LAKE_PROJECT_MISSING"
        ),
        "status_counts": dict(sorted(status_counts.items())),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_lean_environment_repair_executor_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def resolve_source_theorem_exact_semantic_definition_environment_tasks_path(
    *,
    runtime_dir: Path | None = None,
    repair_executor_manifest: Path | None = None,
    environment_tasks_jsonl: Path | None = None,
) -> Path:
    if environment_tasks_jsonl is not None:
        return environment_tasks_jsonl
    if repair_executor_manifest is not None:
        payload = json.loads(repair_executor_manifest.read_text(encoding="utf-8"))
        raw_path = str(payload.get("lean_environment_repair_tasks_jsonl", "") or "")
        if not raw_path:
            raise ValueError(
                "repair executor manifest does not list lean_environment_repair_tasks_jsonl"
            )
        return _resolve_relative_artifact_path(
            base_dir=repair_executor_manifest.parent,
            raw_path=raw_path,
        )
    if runtime_dir is None:
        raise ValueError(
            "runtime_dir, repair_executor_manifest, or environment_tasks_jsonl is required"
        )
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = payload.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    raw_path = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_lean_environment_repair_tasks_jsonl",
            "",
        )
        or ""
    )
    if raw_path:
        return _resolve_runtime_artifact_path(runtime_dir=runtime_dir, raw_path=raw_path)
    raw_manifest = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_lean_repair_executor_manifest",
            "",
        )
        or ""
    )
    if raw_manifest:
        repair_manifest = _resolve_runtime_artifact_path(
            runtime_dir=runtime_dir,
            raw_path=raw_manifest,
        )
        return resolve_source_theorem_exact_semantic_definition_environment_tasks_path(
            repair_executor_manifest=repair_manifest,
        )
    raise ValueError(
        "runtime manifest does not list exact semantic-definition Lean environment repair tasks"
    )


def _environment_repair_result(row: Mapping[str, Any]) -> dict[str, Any]:
    project = Path(str(row.get("candidate_lean_project_hint", "") or ""))
    candidate_file = Path(str(row.get("candidate_source_file", "") or ""))
    lakefile_lean = project / "lakefile.lean"
    lakefile_toml = project / "lakefile.toml"
    lean_toolchain = project / "lean-toolchain"
    lake_manifest = project / "lake-manifest.json"
    lake_packages = project / ".lake" / "packages"
    mathlib_package = lake_packages / "mathlib"
    project_exists = bool(str(project)) and project.exists()
    candidate_exists = bool(str(candidate_file)) and candidate_file.exists()
    lakefile_exists = project_exists and (lakefile_lean.exists() or lakefile_toml.exists())
    toolchain_exists = project_exists and lean_toolchain.exists()
    manifest_exists = project_exists and lake_manifest.exists()
    packages_dir_exists = project_exists and lake_packages.exists()
    mathlib_package_exists = project_exists and mathlib_package.exists()
    failure_classification = str(row.get("failure_classification", "") or "")
    if not project_exists:
        status = "LAKE_PROJECT_MISSING"
    elif not lakefile_exists:
        status = "LAKEFILE_MISSING"
    elif not toolchain_exists:
        status = "LEAN_TOOLCHAIN_MISSING"
    elif not manifest_exists:
        status = "LAKE_MANIFEST_MISSING_DEPENDENCY_UPDATE_REQUIRED"
    elif not packages_dir_exists or not mathlib_package_exists:
        status = "LAKE_PACKAGE_CACHE_MISSING"
    elif not candidate_exists:
        status = "CANDIDATE_SOURCE_FILE_MISSING"
    elif failure_classification == "lean_local_library_build_unresolved":
        status = "LOCAL_LIBRARY_BUILD_OR_IMPORT_UNRESOLVED"
    else:
        status = "DEPENDENCY_ENVIRONMENT_READY_TO_RERUN_LEAN_REPAIR"
    dependency_fetch_required = status in {
        "LAKE_MANIFEST_MISSING_DEPENDENCY_UPDATE_REQUIRED",
        "LAKE_PACKAGE_CACHE_MISSING",
    }
    result_id = (
        "source_theorem_exact_semantic_definition_lean_environment_repair:"
        + stable_hash(
            [
                row.get("environment_repair_task_id", ""),
                row.get("target_theorem_name", ""),
                row.get("placeholder_symbol", ""),
                str(project),
                str(candidate_file),
                status,
            ]
        )[:20]
    )
    return {
        "schema_version": 1,
        "artifact_kind": RESULT_ARTIFACT_KIND,
        "environment_repair_result_id": result_id,
        "source_environment_repair_task_id": str(
            row.get("environment_repair_task_id", "") or ""
        ),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "candidate_source_file": str(candidate_file) if str(candidate_file) else "",
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_source_file_exists": candidate_exists,
        "candidate_lean_project_hint": str(project) if str(project) else "",
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        "lake_project_exists": project_exists,
        "lakefile_exists": lakefile_exists,
        "lean_toolchain_exists": toolchain_exists,
        "lake_manifest_exists": manifest_exists,
        "lake_packages_dir_exists": packages_dir_exists,
        "mathlib_package_exists": mathlib_package_exists,
        "environment_repair_status": status,
        "dependency_fetch_required": dependency_fetch_required,
        "ready_to_rerun_lean_repair": status
        == "DEPENDENCY_ENVIRONMENT_READY_TO_RERUN_LEAN_REPAIR",
        "recommended_commands": _recommended_commands(
            status=status,
            project=project,
            candidate_file=candidate_file,
        ),
        "recommended_next_action": _recommended_next_action(status),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _recommended_commands(*, status: str, project: Path, candidate_file: Path) -> list[str]:
    commands: list[str] = []
    if status in {
        "LAKE_MANIFEST_MISSING_DEPENDENCY_UPDATE_REQUIRED",
        "LAKE_PACKAGE_CACHE_MISSING",
    }:
        commands.extend(["lake update", "lake exe cache get"])
    if status != "LAKE_PROJECT_MISSING" and str(candidate_file):
        commands.append(f"lake env lean {candidate_file}")
    return commands


def _recommended_next_action(status: str) -> str:
    if status == "DEPENDENCY_ENVIRONMENT_READY_TO_RERUN_LEAN_REPAIR":
        return "rerun exact semantic-definition Lean repair executor with local Lean"
    if status == "LOCAL_LIBRARY_BUILD_OR_IMPORT_UNRESOLVED":
        return (
            "build or repair the inferred local Lean library import cone before "
            "rerunning exact semantic-definition Lean repair; dependency fetch is "
            "not the current blocker"
        )
    if status in {
        "LAKE_MANIFEST_MISSING_DEPENDENCY_UPDATE_REQUIRED",
        "LAKE_PACKAGE_CACHE_MISSING",
    }:
        return (
            "prepare Lake dependencies/cache for the inferred project, then rerun "
            "the exact semantic-definition Lean repair executor"
        )
    if status == "CANDIDATE_SOURCE_FILE_MISSING":
        return "repair candidate source path or source-root mapping before local Lean"
    return "repair the inferred Lake project path before rerunning local Lean"


def _learning_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": RESULT_ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": str(row.get("target_theorem_name", "") or ""),
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "environment_repair_result_id": str(
            row.get("environment_repair_result_id", "") or ""
        ),
        "source_environment_repair_task_id": str(
            row.get("source_environment_repair_task_id", "") or ""
        ),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        "environment_repair_status": str(
            row.get("environment_repair_status", "") or ""
        ),
        "dependency_fetch_required": bool(
            row.get("dependency_fetch_required", False)
        ),
        "ready_to_rerun_lean_repair": bool(
            row.get("ready_to_rerun_lean_repair", False)
        ),
        "candidate_lean_project_hint": str(
            row.get("candidate_lean_project_hint", "") or ""
        ),
        "candidate_source_file": str(row.get("candidate_source_file", "") or ""),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_PREFLIGHT",
            "environment_repair_status": str(
                row.get("environment_repair_status", "") or ""
            ),
            "source_execution_status": str(
                row.get("source_execution_status", "") or ""
            ),
            "authoring_mode": str(row.get("authoring_mode", "") or ""),
            "dependency_fetch_required": bool(
                row.get("dependency_fetch_required", False)
            ),
            "ready_to_rerun_lean_repair": bool(
                row.get("ready_to_rerun_lean_repair", False)
            ),
            "candidate_lean_project_hint": str(
                row.get("candidate_lean_project_hint", "") or ""
            ),
            "candidate_source_file": str(row.get("candidate_source_file", "") or ""),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "recommended_commands": [
                str(command)
                for command in row.get("recommended_commands", []) or []
                if str(command).strip()
            ],
            "recommended_next_action": str(
                row.get("recommended_next_action", "") or ""
            ),
            "source_theorem_kernel_verified": False,
        },
        "target_behavior": (
            "prepare Lean dependency/cache environment for exact semantic-definition "
            "repair before proof-body search resumes"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _resolve_relative_artifact_path(*, base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidate = base_dir / path
    if candidate.exists():
        return candidate
    if path.parts and path.parts[0] == base_dir.name:
        candidate = base_dir.parent / path
        if candidate.exists():
            return candidate
    return base_dir / path


def _resolve_runtime_artifact_path(*, runtime_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates = [runtime_dir / path, runtime_dir.parent / path]
    parts = path.parts
    if parts and parts[0] == runtime_dir.name:
        candidates.append(runtime_dir.parent / path)
    if len(parts) >= 2 and parts[0] == runtime_dir.parent.name:
        candidates.append(runtime_dir.parent.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )
