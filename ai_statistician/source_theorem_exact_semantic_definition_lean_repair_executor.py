from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .exact_semantic_definition_policy import (
    compact_exact_semantic_placeholder_key,
    exact_semantic_definition_import_policy_blocker,
    exact_semantic_definition_placeholder_policy,
)
from .fingerprint import stable_hash
from .research_architect import KERNEL_PROOF_BOUNDARY
from .source_theorem_formal_environment_proofengineer_bridge import (
    _lean_command,
    _run_local_lean,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS,
)


ARTIFACT_KIND = "SourceTheoremExactSemanticDefinitionLeanRepairExecutorManifest"
RESULT_ARTIFACT_KIND = "SourceTheoremExactSemanticDefinitionLeanRepairExecutionResult"
ENVIRONMENT_REPAIR_TASK_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionLeanEnvironmentRepairTask"
)
AUTHOR_DEFINITION_TASK_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionAuthoringTask"
)
TYPECHECKED_CANDIDATE_REVIEW_PACKET_ARTIFACT_KIND = (
    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
)
LEARNING_TASK = "source_theorem_exact_semantic_definition_lean_repair_execution"
ENVIRONMENT_REPAIR_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_lean_environment_repair"
)
AUTHOR_DEFINITION_LEARNING_TASK = (
    "source_theorem_exact_semantic_definition_author_definition"
)
PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
)
ENVIRONMENT_REPAIR_PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_TASK_NOT_PROOF_EVIDENCE"
)
AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS = (
    "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
)
TYPECHECKED_CANDIDATE_REVIEW_PROOF_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
)
TYPECHECKED_CANDIDATE_LOCAL_LEAN_EVIDENCE_STATUS = (
    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_LOCAL_LEAN_COMPILED_"
    "REVIEW_REQUIRED"
)
TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS = (
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
)
TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_QUEUE_STATUS = (
    "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_AUTHORING"
)
TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_TRIGGER = (
    "EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
)
TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_MODE = (
    "review_typechecked_semantic_definition_candidate"
)
BOUNDARY = (
    "Exact semantic-definition Lean repair execution rows are ProofEngineer "
    "environment feedback for reviewed definition/import repair tasks. A local "
    "Lean compile of a candidate source declaration is source-availability and "
    "environment evidence only; it is not source theorem proof, not semantic "
    "faithfulness proof, and not sufficient to resume exact proof-body promotion "
    "unless a later verifier manifest checks the repaired candidate declaration "
    "and source theorem under local Lean/AXLE."
)
AUTHOR_DEFINITION_REPAIR_STATUSES = {
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED",
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_PATH_MISSING",
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_FILE_MISSING",
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_FAILED",
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING",
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING",
    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_ENVIRONMENT_TIMEOUT",
}
AUTHOR_DEFINITION_MISSING_STATUS = (
    "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN"
)
LEAN_DIAGNOSTIC_LOCATION_RE = re.compile(
    r"^(?P<path>.*?):(?P<line>\d+):(?P<column>\d+):"
)


def _local_lean_diagnostic_source_excerpts(
    *,
    artifact_path: str,
    diagnostics: Sequence[str],
    context_lines: int = 4,
    max_excerpts: int = 3,
) -> list[dict[str, Any]]:
    """Return small source windows around local Lean diagnostics."""

    excerpts: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    fallback_path = str(artifact_path or "").strip()
    for diagnostic in diagnostics:
        diagnostic_text = str(diagnostic or "").strip()
        if not diagnostic_text:
            continue
        match = LEAN_DIAGNOSTIC_LOCATION_RE.match(diagnostic_text)
        if match is None:
            continue
        diagnostic_path = ""
        line_number = 0
        column_number = 0
        diagnostic_path = match.group("path") or ""
        line_number = int(match.group("line") or 0)
        column_number = int(match.group("column") or 0)
        path_candidates = [
            value
            for value in (diagnostic_path, fallback_path)
            if str(value or "").strip()
        ]
        if not path_candidates:
            continue
        for raw_path in path_candidates:
            path = Path(str(raw_path or "").strip()).expanduser()
            if not path.exists():
                continue
            key = (str(path), line_number, column_number)
            if key in seen:
                continue
            seen.add(key)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            if not lines:
                continue
            center = line_number if line_number > 0 else 1
            start = max(1, center - context_lines)
            end = min(len(lines), center + context_lines)
            numbered = [
                f"{idx}: {lines[idx - 1]}"
                for idx in range(start, end + 1)
            ]
            excerpts.append(
                {
                    "artifact_path": str(path),
                    "line": line_number,
                    "column": column_number,
                    "diagnostic": diagnostic_text,
                    "source_excerpt": numbered,
                    "proof_evidence_status": PROOF_EVIDENCE_STATUS,
                    "proof_evidence_boundary": BOUNDARY,
                }
            )
            break
        if len(excerpts) >= max_excerpts:
            break
    return excerpts


def run_source_theorem_exact_semantic_definition_lean_repair_executor(
    *,
    out_dir: Path,
    runtime_dir: Path | None = None,
    bridge_manifest: Path | None = None,
    materializer_manifest: Path | None = None,
    tasks_jsonl: Path | None = None,
    source_roots: Sequence[Path] = (),
    local_lean: bool = False,
    lean_project: Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Consume exact semantic-definition Lean repair tasks and emit feedback rows."""

    task_path = resolve_source_theorem_exact_semantic_definition_lean_repair_tasks_path(
        runtime_dir=runtime_dir,
        bridge_manifest=bridge_manifest,
        materializer_manifest=materializer_manifest,
        tasks_jsonl=tasks_jsonl,
    )
    tasks = _read_jsonl(task_path)
    roots = tuple(Path(root).expanduser() for root in source_roots)
    command = lean_command or _lean_command(lean_project)
    command_explicit = lean_command is not None
    results = [
        _execution_result(
            task,
            source_roots=roots,
            local_lean=local_lean,
            lean_project=lean_project,
            lean_timeout=lean_timeout,
            lean_command=command,
            lean_command_explicit=command_explicit,
        )
        for task in tasks
        if isinstance(task, Mapping)
    ]
    environment_repair_tasks = [
        _environment_repair_task(row)
        for row in results
        if row.get("failure_classification")
        in {
            "lean_import_environment_missing",
            "lean_dependency_fetch_failed",
            "lean_local_library_build_unresolved",
            "local_lean_timeout",
        }
    ]
    author_definition_tasks = [
        _author_definition_task(row)
        for row in results
        if _needs_author_definition_task(row)
    ]
    typechecked_candidate_review_packets = [
        _typechecked_candidate_review_packet(row)
        for row in results
        if row.get("execution_status") == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
    ]
    learning_rows = [_learning_row(row) for row in results]
    learning_rows.extend(
        _environment_repair_learning_row(row) for row in environment_repair_tasks
    )
    learning_rows.extend(
        _author_definition_learning_row(row) for row in author_definition_tasks
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_lean_repair_execution_results.jsonl"
    )
    learning_path = out_dir / "runtime_learning_rows.jsonl"
    environment_repair_tasks_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_lean_environment_repair_tasks.jsonl"
    )
    author_definition_tasks_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_authoring_tasks.jsonl"
    )
    typechecked_candidate_review_packets_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_typechecked_candidate_review_packets.jsonl"
    )
    _write_jsonl(results_path, results)
    _write_jsonl(environment_repair_tasks_path, environment_repair_tasks)
    _write_jsonl(author_definition_tasks_path, author_definition_tasks)
    _write_jsonl(
        typechecked_candidate_review_packets_path,
        typechecked_candidate_review_packets,
    )
    _write_jsonl(learning_path, learning_rows)
    status_counts = Counter(str(row.get("execution_status", "") or "") for row in results)
    failure_counts = Counter(
        str(row.get("failure_classification", "") or "")
        for row in results
        if str(row.get("failure_classification", "") or "").strip()
    )
    dominant_failure_classification = (
        failure_counts.most_common(1)[0][0] if failure_counts else ""
    )
    state, state_reason = _proofengineer_state_from_status_counts(status_counts)
    manifest = {
        "schema_version": 1,
        "artifact_kind": ARTIFACT_KIND,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_runtime_dir": str(runtime_dir or ""),
        "source_bridge_manifest": str(bridge_manifest or ""),
        "source_materializer_manifest": str(materializer_manifest or ""),
        "source_lean_repair_tasks_jsonl": str(task_path),
        "execution_results_jsonl": str(results_path),
        "lean_environment_repair_tasks_jsonl": str(environment_repair_tasks_path),
        "exact_semantic_definition_authoring_tasks_jsonl": str(
            author_definition_tasks_path
        ),
        "typechecked_candidate_review_packets_jsonl": str(
            typechecked_candidate_review_packets_path
        ),
        "runtime_learning_rows_jsonl": str(learning_path),
        "source_roots": [str(root) for root in roots],
        "local_lean_requested": bool(local_lean),
        "local_lean_project": str(lean_project or ""),
        "local_lean_timeout_seconds": int(lean_timeout),
        "lean_command": list(command),
        "n_tasks": len(tasks),
        "n_results": len(results),
        "n_tasks_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(tasks)
        ),
        "n_results_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(results)
        ),
        "n_exact_semantic_definition_authoring_tasks_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(author_definition_tasks)
        ),
        "n_typechecked_candidate_review_packets_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(typechecked_candidate_review_packets)
        ),
        "n_runtime_learning_rows_with_placeholder_policy_lineage": (
            _count_placeholder_policy_lineage(learning_rows)
        ),
        "placeholder_policy_lineage_complete": (
            _placeholder_policy_lineage_complete(
                results,
                author_definition_tasks,
                typechecked_candidate_review_packets,
                learning_rows,
            )
        ),
        "n_import_candidate_tasks": sum(
            1
            for row in results
            if row.get("lean_repair_action") == "review_import_source_declaration"
        ),
        "n_import_candidate_ready_for_semantic_review": int(
            status_counts.get(
                "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF",
                0,
            )
        ),
        "n_synthesize_definition_tasks": sum(
            1
            for row in results
            if row.get("lean_repair_action") == "synthesize_exact_definition"
        ),
        "n_author_definition_tasks": sum(
            1
            for row in results
            if row.get("lean_repair_action") == "author_exact_definition"
        ),
        "n_exact_semantic_definition_authoring_tasks": len(author_definition_tasks),
        "n_exact_semantic_definition_authoring_repair_tasks": sum(
            1
            for row in author_definition_tasks
            if row.get("runtime_queue_status")
            == "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
        ),
        "n_exact_semantic_definition_candidate_review_authoring_tasks": sum(
            1
            for row in author_definition_tasks
            if row.get("runtime_queue_status")
            == TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_QUEUE_STATUS
        ),
        "n_typechecked_candidate_review_ready": int(
            status_counts.get(TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS, 0)
        ),
        "n_typechecked_candidate_review_packets": len(
            typechecked_candidate_review_packets
        ),
        "n_typechecked_candidate_semantic_review_blocked": int(
            status_counts.get(
                "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED",
                0,
            )
        ),
        "n_exact_definition_authoring_required": int(
            status_counts.get("EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN", 0)
        ),
        "n_candidate_source_files_resolved": sum(
            1 for row in results if row.get("candidate_source_file_resolved")
        ),
        "n_local_lean_checked": sum(1 for row in results if row.get("local_lean_checked")),
        "n_local_lean_compiled": sum(
            1 for row in results if row.get("local_lean_compiled")
        ),
        "n_local_lean_tool_calls": sum(
            1
            for row in results
            if "local.lake_env_lean" in set(row.get("executed_tools", []) or [])
        ),
        "n_executed_tool_calls": sum(
            len(row.get("tool_call_trace", []) or []) for row in results
        ),
        "n_inferred_lean_project_hints": sum(
            1 for row in results if row.get("candidate_lean_project_hint")
        ),
        "n_lean_environment_repair_tasks": len(environment_repair_tasks),
        "n_tasks_from_pseudo_formal": sum(
            1
            for row in tasks
            if isinstance(row, Mapping)
            and str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        ),
        "n_results_from_pseudo_formal": sum(
            1
            for row in results
            if str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        ),
        "n_local_lean_checked_from_pseudo_formal": sum(
            1
            for row in results
            if row.get("local_lean_checked")
            and str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        ),
        "n_local_lean_compiled_from_pseudo_formal": sum(
            1
            for row in results
            if row.get("local_lean_compiled")
            and str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        ),
        "n_lean_environment_repair_tasks_from_pseudo_formal": sum(
            1
            for row in environment_repair_tasks
            if str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        ),
        "n_exact_semantic_definition_authoring_tasks_from_pseudo_formal": sum(
            1
            for row in author_definition_tasks
            if str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        ),
        "n_typechecked_candidate_review_packets_from_pseudo_formal": sum(
            1
            for row in typechecked_candidate_review_packets
            if str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
        ),
        "source_pseudo_formal_work_order_ids": list(
            dict.fromkeys(
                str(row.get("source_pseudo_formal_work_order_id", "") or "")
                for row in results
                if str(row.get("source_pseudo_formal_work_order_id", "") or "").strip()
            )
        ),
        "source_pseudo_formal_block_ids": list(
            dict.fromkeys(
                str(row.get("source_pseudo_formal_block_id", "") or "")
                for row in results
                if str(row.get("source_pseudo_formal_block_id", "") or "").strip()
            )
        ),
        "status_counts": dict(sorted(status_counts.items())),
        "by_failure_classification": dict(sorted(failure_counts.items())),
        "dominant_failure_classification": dominant_failure_classification,
        "proofengineer_state": state,
        "proofengineer_state_reason": state_reason,
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_lean_repair_executor_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def _proofengineer_state_from_status_counts(
    status_counts: Counter[str],
) -> tuple[str, str]:
    if not status_counts:
        return (
            "NO_EXACT_SEMANTIC_DEFINITION_REPAIR_TASKS",
            "no exact semantic-definition Lean repair tasks were executed",
        )
    if any(
        status_counts.get(status, 0)
        for status in {
            "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_IMPORT_ENVIRONMENT_MISSING",
            "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING",
            "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_ENVIRONMENT_TIMEOUT",
            "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LIBRARY_BUILD_UNRESOLVED",
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING",
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING",
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_ENVIRONMENT_TIMEOUT",
        }
    ):
        return (
            "LEAN_ENVIRONMENT_REPAIR_REQUIRED",
            "at least one exact semantic-definition candidate cannot be checked until the Lean environment is repaired",
        )
    if any(
        status_counts.get(status, 0)
        for status in {
            "IMPORT_CANDIDATE_SEMANTIC_REVIEW_BLOCKED",
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED",
        }
    ):
        return (
            "SEMANTIC_REVIEW_BLOCKED",
            "a compiled or source-located candidate still has semantic review blockers",
        )
    if status_counts.get(TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS, 0):
        return (
            "TYPECHECKED_CANDIDATE_SEMANTIC_REVIEW_REQUIRED",
            "a definition-only candidate typechecked, but source semantic faithfulness is still unreviewed",
        )
    if status_counts.get(
        "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF",
        0,
    ):
        return (
            "IMPORT_CANDIDATE_SEMANTIC_REVIEW_REQUIRED",
            "a candidate source declaration compiled locally and now needs source semantic review/import",
        )
    if status_counts.get("EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN", 0):
        return (
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_REQUIRED",
            "no executable exact semantic definition exists yet for at least one placeholder",
        )
    if status_counts.get("EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_NOT_REQUESTED", 0):
        return (
            "LOCAL_LEAN_CHECK_REQUIRED",
            "a definition-only candidate exists but local Lean has not checked it",
        )
    if any("LOCAL_LEAN_FAILED" in status for status in status_counts):
        return (
            "LOCAL_LEAN_REPAIR_REQUIRED",
            "a candidate was checked by Lean and failed before semantic review could proceed",
        )
    return (
        "EXACT_SEMANTIC_DEFINITION_REPAIR_REVIEW_REQUIRED",
        "exact semantic-definition repair produced non-proof feedback that still needs ProofEngineer review",
    )


def resolve_source_theorem_exact_semantic_definition_lean_repair_tasks_path(
    *,
    runtime_dir: Path | None = None,
    bridge_manifest: Path | None = None,
    materializer_manifest: Path | None = None,
    tasks_jsonl: Path | None = None,
) -> Path:
    if tasks_jsonl is not None:
        return tasks_jsonl
    if materializer_manifest is not None:
        payload = json.loads(materializer_manifest.read_text(encoding="utf-8"))
        raw_path = str(payload.get("materialized_lean_repair_tasks_jsonl", "") or "")
        if not raw_path:
            raise ValueError(
                "materializer manifest does not list materialized_lean_repair_tasks_jsonl"
            )
        return _resolve_relative_artifact_path(
            base_dir=materializer_manifest.parent,
            raw_path=raw_path,
        )
    if bridge_manifest is not None:
        payload = json.loads(bridge_manifest.read_text(encoding="utf-8"))
        raw_path = str(payload.get("lean_repair_tasks_jsonl", "") or "")
        if not raw_path:
            raise ValueError("bridge manifest does not list lean_repair_tasks_jsonl")
        return _resolve_relative_artifact_path(base_dir=bridge_manifest.parent, raw_path=raw_path)
    if runtime_dir is None:
        raise ValueError("runtime_dir, bridge_manifest, or tasks_jsonl is required")
    manifest_path = runtime_dir / "research_agent_runtime_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = payload.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        artifacts = {}
    raw_path = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_lean_repair_tasks_jsonl",
            "",
        )
        or ""
    )
    if raw_path:
        return _resolve_runtime_artifact_path(runtime_dir=runtime_dir, raw_path=raw_path)
    raw_bridge = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_proofengineer_bridge_manifest",
            "",
        )
        or ""
    )
    if raw_bridge:
        bridge_path = _resolve_runtime_artifact_path(runtime_dir=runtime_dir, raw_path=raw_bridge)
        return resolve_source_theorem_exact_semantic_definition_lean_repair_tasks_path(
            bridge_manifest=bridge_path,
        )
    raw_materializer = str(
        artifacts.get(
            "runtime_source_theorem_exact_semantic_definition_authoring_candidate_materializer_manifest",
            "",
        )
        or ""
    )
    if raw_materializer:
        materializer_path = _resolve_runtime_artifact_path(
            runtime_dir=runtime_dir,
            raw_path=raw_materializer,
        )
        return resolve_source_theorem_exact_semantic_definition_lean_repair_tasks_path(
            materializer_manifest=materializer_path,
        )
    raise ValueError(
        "runtime manifest does not list exact semantic-definition Lean repair tasks"
    )


def _execution_result(
    task: Mapping[str, Any],
    *,
    source_roots: Sequence[Path],
    local_lean: bool,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
    lean_command_explicit: bool,
) -> dict[str, Any]:
    action = str(task.get("lean_repair_action", "") or "")
    target_theorem_name = str(task.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        task,
        fallback_target=target_theorem_name,
    )
    placeholder_symbol = str(task.get("placeholder_symbol", "") or "")
    candidate_declarations = [
        dict(row)
        for row in task.get("candidate_import_declarations", []) or []
        if isinstance(row, Mapping)
    ]
    candidate_definition_request = dict(
        task.get("candidate_definition_request", {}) or {}
    )
    if candidate_definition_request:
        candidate_definition_request.setdefault("target_theorem_name", target_theorem_name)
        if placeholder_symbol and not candidate_definition_request.get(
            "placeholder_symbol"
        ):
            candidate_definition_request["placeholder_symbol"] = placeholder_symbol
        if target_ids and not candidate_definition_request.get("target_ids"):
            candidate_definition_request["target_ids"] = list(target_ids)
    candidate_path = Path()
    candidate_raw_path = ""
    if candidate_declarations:
        candidate_raw_path = str(candidate_declarations[0].get("path", "") or "")
        candidate_path = _resolve_source_path(candidate_raw_path, source_roots)
    source_file_resolved = bool(candidate_raw_path and candidate_path.exists())
    typechecked_definition_candidate = dict(
        task.get(
            "source_theorem_exact_semantic_definition_typechecked_candidate",
            {},
        )
        or {}
    )
    definition_only_candidate_raw_path = str(
        task.get("definition_only_candidate_artifact_path", "")
        or typechecked_definition_candidate.get(
            "definition_only_candidate_artifact_path",
            "",
        )
        or ""
    )
    definition_only_candidate_path = (
        _resolve_source_path(definition_only_candidate_raw_path, source_roots)
        if definition_only_candidate_raw_path
        else Path()
    )
    definition_only_candidate_file_resolved = bool(
        definition_only_candidate_raw_path and definition_only_candidate_path.exists()
    )
    full_candidate_artifact_path = str(
        task.get("candidate_artifact_path", "")
        or typechecked_definition_candidate.get("candidate_artifact_path", "")
        or ""
    )
    prior_definition_checked = _boolish(
        task.get(
            "local_definition_lean_checked",
            typechecked_definition_candidate.get("local_definition_lean_checked", False),
        )
    )
    prior_definition_compiled = _boolish(
        task.get(
            "local_definition_lean_compiled",
            typechecked_definition_candidate.get(
                "local_definition_lean_compiled",
                False,
            ),
        )
    )
    semantic_typecheck_status = str(
        task.get("semantic_definition_typecheck_evidence_status", "")
        or typechecked_definition_candidate.get(
            "semantic_definition_typecheck_evidence_status",
            "",
        )
        or ""
    )
    semantic_alignment_blockers = [
        str(value)
        for value in task.get("semantic_alignment_blockers", []) or []
        if str(value).strip()
    ]
    semantic_alignment_blockers = list(dict.fromkeys(semantic_alignment_blockers))
    definition_contract = dict(task.get("definition_contract", {}) or {})
    semantic_review_decision = str(
        task.get("semantic_review_decision", "")
        or definition_contract.get("semantic_review_decision", "")
        or ""
    )
    semantic_review_status = str(
        task.get("semantic_review_status", "")
        or definition_contract.get("semantic_review_status", "")
        or ""
    )
    semantic_review_evidence = list(
        task.get("semantic_review_evidence", [])
        or definition_contract.get("semantic_review_evidence", [])
        or []
    )
    semantic_review_required_before_proof_body = bool(
        task.get("semantic_review_required_before_proof_body", False)
    )
    llm_claimed_source_theorem_ready_for_exact_proof_body = bool(
        task.get("llm_claimed_source_theorem_ready_for_exact_proof_body", False)
    )
    task_lean_project_hint_raw = str(
        task.get("candidate_lean_project_hint", "")
        or typechecked_definition_candidate.get("candidate_lean_project_hint", "")
        or ""
    )
    task_lean_project_hint = (
        Path(task_lean_project_hint_raw).expanduser()
        if task_lean_project_hint_raw
        else None
    )
    candidate_lean_project_hint = (
        _find_lake_project_root(candidate_path)
        if source_file_resolved
        else task_lean_project_hint
    )
    semantic_import_blocker = _semantic_import_candidate_blocker(
        placeholder_symbol=str(task.get("placeholder_symbol", "") or ""),
        candidate_declaration=candidate_declarations[0]
        if candidate_declarations
        else {},
    )
    effective_lean_project = lean_project
    effective_lean_command = lean_command
    if (
        local_lean
        and not lean_command_explicit
        and lean_project is None
        and candidate_lean_project_hint is not None
    ):
        effective_lean_project = candidate_lean_project_hint
        effective_lean_command = _lean_command(candidate_lean_project_hint)
    reported_candidate_lean_project_hint = (
        candidate_lean_project_hint or effective_lean_project
    )
    checked = False
    compiled = False
    returncode = -1
    diagnostics: tuple[str, ...] = ()
    errors: list[str] = []
    if action == "review_import_source_declaration":
        if semantic_import_blocker:
            status = "IMPORT_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
            errors.append(semantic_import_blocker)
        elif not candidate_raw_path:
            status = "IMPORT_CANDIDATE_PATH_MISSING"
            errors.append("candidate import declaration path missing")
        elif not source_file_resolved:
            status = "IMPORT_CANDIDATE_SOURCE_FILE_MISSING"
            errors.append(f"candidate source file missing: {candidate_raw_path}")
        elif not local_lean:
            status = "IMPORT_CANDIDATE_RESOLVED_LOCAL_LEAN_NOT_REQUESTED"
        elif not effective_lean_command:
            status = "LOCAL_LEAN_UNAVAILABLE"
            errors.append("lean executable not found")
            diagnostics = ("lean executable not found",)
        else:
            checked = True
            compiled, returncode, diagnostics = _run_local_lean(
                candidate_path,
                lean_command=effective_lean_command,
                lean_project=effective_lean_project,
                timeout_s=lean_timeout,
            )
            failure_classification = _classify_local_lean_failure(diagnostics)
            status = (
                "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF"
                if compiled
                else "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LIBRARY_BUILD_UNRESOLVED"
                if failure_classification == "lean_local_library_build_unresolved"
                else "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_IMPORT_ENVIRONMENT_MISSING"
                if failure_classification == "lean_import_environment_missing"
                else "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING"
                if failure_classification == "lean_dependency_fetch_failed"
                else "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_ENVIRONMENT_TIMEOUT"
                if failure_classification == "local_lean_timeout"
                else "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_FAILED"
            )
            if not compiled:
                errors.append("candidate source file local Lean check failed")
    elif action in {
        "synthesize_exact_definition",
        "author_exact_definition",
        "review_typechecked_exact_definition_candidate",
    }:
        if prior_definition_compiled or definition_only_candidate_raw_path:
            if not definition_only_candidate_raw_path:
                status = "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_PATH_MISSING"
                errors.append("definition-only candidate artifact path missing")
            elif not definition_only_candidate_file_resolved:
                status = "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_FILE_MISSING"
                errors.append(
                    "definition-only candidate artifact file missing: "
                    f"{definition_only_candidate_raw_path}"
                )
            elif not local_lean:
                status = (
                    TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
                    if prior_definition_compiled
                    else "EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_NOT_REQUESTED"
                )
            elif not effective_lean_command:
                status = "LOCAL_LEAN_UNAVAILABLE"
                errors.append("lean executable not found")
                diagnostics = ("lean executable not found",)
            elif (
                prior_definition_compiled
                and not lean_command_explicit
                and effective_lean_project is None
            ):
                status = TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
            else:
                checked = True
                compiled, returncode, diagnostics = _run_local_lean(
                    definition_only_candidate_path,
                    lean_command=effective_lean_command,
                    lean_project=effective_lean_project,
                    timeout_s=lean_timeout,
                )
                failure_classification = _classify_local_lean_failure(diagnostics)
                status = (
                    TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
                    if compiled
                    else "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING"
                    if failure_classification == "lean_import_environment_missing"
                    else "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING"
                    if failure_classification == "lean_dependency_fetch_failed"
                    else "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_ENVIRONMENT_TIMEOUT"
                    if failure_classification == "local_lean_timeout"
                    else "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_FAILED"
                )
                if not compiled:
                    errors.append("definition-only candidate local Lean check failed")
            if (
                status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
                and semantic_alignment_blockers
            ):
                status = (
                    "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
                )
                errors.append(
                    "typechecked definition-only candidate still has semantic "
                    "alignment blockers"
                )
        else:
            status = "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN"
    else:
        status = "UNKNOWN_LEAN_REPAIR_ACTION"
        errors.append(f"unknown lean_repair_action: {action}")
    failure_classification = (
        ""
        if status
        in {
            "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF",
            "IMPORT_CANDIDATE_RESOLVED_LOCAL_LEAN_NOT_REQUESTED",
            "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN",
            "EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_NOT_REQUESTED",
            TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS,
        }
        else "semantic_definition_review_blocked"
        if status == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
        else _classify_local_lean_failure(diagnostics)
        if diagnostics
        else status.lower()
    )
    semantic_typecheck_status = _semantic_typecheck_status_from_execution(
        existing_status=semantic_typecheck_status,
        execution_status=status,
        current_local_lean_checked=checked,
        current_local_lean_compiled=compiled,
    )
    executed_tools = ["local.lake_env_lean"] if checked else []
    local_lean_artifact_path = (
        str(definition_only_candidate_path)
        if checked
        and action
        in {
            "synthesize_exact_definition",
            "author_exact_definition",
            "review_typechecked_exact_definition_candidate",
        }
        and definition_only_candidate_raw_path
        else str(candidate_path)
        if checked and candidate_raw_path
        else ""
    )
    local_lean_diagnostic_source_excerpts = _local_lean_diagnostic_source_excerpts(
        artifact_path=local_lean_artifact_path,
        diagnostics=diagnostics,
    )
    tool_call_trace = _local_lean_tool_call_trace(
        checked=checked,
        compiled=compiled,
        returncode=returncode,
        diagnostics=diagnostics,
        diagnostic_source_excerpts=local_lean_diagnostic_source_excerpts,
        failure_classification=failure_classification,
        lean_command=effective_lean_command,
        lean_project=effective_lean_project,
        lean_timeout=lean_timeout,
        artifact_path=local_lean_artifact_path,
    )
    result_id = (
        "source_theorem_exact_semantic_definition_lean_repair_execution:"
        + stable_hash(
            [
                task.get("lean_repair_task_id", ""),
                task.get("source_repair_packet_id", ""),
                target_theorem_name,
                task.get("placeholder_symbol", ""),
                action,
                candidate_raw_path,
                definition_only_candidate_raw_path,
                str(candidate_lean_project_hint or ""),
                status,
            ]
        )[:20]
    )
    return {
        "schema_version": 1,
        "artifact_kind": RESULT_ARTIFACT_KIND,
        "execution_result_id": result_id,
        "source_lean_repair_task_id": str(task.get("lean_repair_task_id", "") or ""),
        "source_repair_packet_id": str(task.get("source_repair_packet_id", "") or ""),
        "source_review_packet_id": str(task.get("source_review_packet_id", "") or ""),
        "source_execution_status": str(task.get("source_execution_status", "") or ""),
        "authoring_trigger": str(task.get("authoring_trigger", "") or ""),
        "authoring_mode": str(task.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            task.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(task.get("source_repair_strategy", "") or ""),
        "source_definition_closure_work_order_id": str(
            task.get("source_definition_closure_work_order_id", "") or ""
        ),
        "question_id": str(task.get("question_id", "") or ""),
        "question_title": str(task.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": str(task.get("placeholder_symbol", "") or ""),
        "materialization_order_index": int(
            task.get("materialization_order_index", 0) or 0
        ),
        "lean_repair_action": action,
        "repair_strategy": str(task.get("repair_strategy", "") or ""),
        "candidate_import_declarations": candidate_declarations,
        "semantic_import_blocker": semantic_import_blocker,
        "candidate_source_file": str(candidate_path) if candidate_raw_path else "",
        "candidate_source_file_resolved": source_file_resolved,
        "candidate_lean_project_hint": str(reported_candidate_lean_project_hint or ""),
        "source_theorem_exact_semantic_definition_typechecked_candidate": (
            typechecked_definition_candidate
        ),
        "definition_only_candidate_artifact_path": definition_only_candidate_raw_path,
        "definition_only_candidate_file_resolved": (
            definition_only_candidate_file_resolved
        ),
        "candidate_artifact_path": full_candidate_artifact_path,
        "runtime_queue_status": _runtime_queue_status_from_execution(
            execution_status=status,
            local_lean_compiled=compiled,
            local_definition_lean_compiled=bool(
                prior_definition_compiled or compiled
            ),
        ),
        "local_definition_lean_checked": bool(prior_definition_checked or checked),
        "local_definition_lean_compiled": bool(prior_definition_compiled or compiled),
        "semantic_definition_typecheck_evidence_status": semantic_typecheck_status,
        "source_reference_hints": list(task.get("source_reference_hints", []) or []),
        "semantic_alignment_constraints": list(
            task.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "source_to_bridge_adapter_instantiation_group_id": str(
            task.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        ),
        "required_adapter_object_names": list(
            task.get("required_adapter_object_names", []) or []
        ),
        "available_adapter_object_names": list(
            task.get("available_adapter_object_names", []) or []
        ),
        "missing_required_adapter_object_names": list(
            task.get("missing_required_adapter_object_names", []) or []
        ),
        "candidate_definition_request": candidate_definition_request,
        **_exact_semantic_definition_context(task),
        "candidate_repair_feedback": dict(
            task.get("candidate_repair_feedback", {}) or {}
        ),
        "definition_contract": definition_contract,
        "semantic_review_decision": semantic_review_decision,
        "semantic_review_status": semantic_review_status,
        "semantic_review_evidence": semantic_review_evidence,
        "semantic_review_required_before_proof_body": (
            semantic_review_required_before_proof_body
        ),
        "llm_claimed_source_theorem_ready_for_exact_proof_body": (
            llm_claimed_source_theorem_ready_for_exact_proof_body
        ),
        "execution_status": status,
        "local_lean_requested": bool(local_lean),
        "local_lean_checked": checked,
        "local_lean_compiled": compiled,
        "local_lean_returncode": int(returncode),
        "local_lean_diagnostics": list(diagnostics[:40]),
        "local_lean_diagnostic_source_excerpts": (
            local_lean_diagnostic_source_excerpts
        ),
        "executed_tools": executed_tools,
        "tool_call_trace": tool_call_trace,
        "failure_classification": failure_classification,
        "lean_project": str(effective_lean_project or ""),
        "lean_project_inferred": bool(
            effective_lean_project is not None
            and lean_project is None
            and candidate_lean_project_hint is not None
        ),
        "lean_timeout": int(lean_timeout),
        "lean_command": list(effective_lean_command),
        "semantic_definition_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "recommended_next_action": _recommended_next_action(status, action),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
        "ok": not errors,
        "errors": errors,
    }


def _local_lean_tool_call_trace(
    *,
    checked: bool,
    compiled: bool,
    returncode: int,
    diagnostics: Sequence[str],
    diagnostic_source_excerpts: Sequence[Mapping[str, Any]],
    failure_classification: str,
    lean_command: Sequence[str],
    lean_project: Path | None,
    lean_timeout: int,
    artifact_path: str,
) -> list[dict[str, Any]]:
    if not checked:
        return []
    status = "local_lean_compiled" if compiled else failure_classification
    if not status:
        status = "local_lean_failed"
    command = [str(part) for part in lean_command]
    if artifact_path:
        command = [*command, artifact_path]
    return [
        {
            "tool": "local.lake_env_lean",
            "status": status,
            "command": command,
            "artifact_path": artifact_path,
            "lean_project": str(lean_project or ""),
            "returncode": int(returncode),
            "timeout_seconds": int(lean_timeout),
            "diagnostics_excerpt": list(diagnostics[:12]),
            "diagnostic_source_excerpts": [
                dict(row) for row in diagnostic_source_excerpts[:3]
            ],
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": BOUNDARY,
        }
    ]


def _recommended_next_action(status: str, action: str) -> str:
    if status == "IMPORT_CANDIDATE_SEMANTIC_REVIEW_BLOCKED":
        return (
            "treat the candidate declaration as source context only; synthesize or "
            "author a reviewed exact semantic definition before proof-body search"
        )
    if status == "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF":
        return (
            "review/import the compiled candidate declaration into the exact source "
            "theorem candidate, then run local Lean/AXLE on the repaired candidate"
        )
    if status == "IMPORT_CANDIDATE_RESOLVED_LOCAL_LEAN_NOT_REQUESTED":
        return "run the Lean repair executor with --local-lean before importing"
    if status == "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_IMPORT_ENVIRONMENT_MISSING":
        return (
            "rerun the Lean repair executor in a Lake project that can resolve the "
            "candidate source imports, or import the candidate declaration into the "
            "exact source-theorem project before proof-body search"
        )
    if status == "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LIBRARY_BUILD_UNRESOLVED":
        return (
            "build or repair the inferred local Lean library import cone before "
            "rerunning the exact semantic-definition Lean repair executor; this is "
            "not a dependency fetch problem"
        )
    if status == "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING":
        return (
            "prepare the inferred Lake project dependencies/cache, then rerun the "
            "Lean repair executor before importing this declaration into the exact "
            "source-theorem candidate"
        )
    if status == "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_ENVIRONMENT_TIMEOUT":
        return (
            "preflight the inferred Lake project dependencies/cache and rerun the "
            "Lean repair executor with a ready project or larger timeout before "
            "importing this declaration into the exact source-theorem candidate"
        )
    if status == "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN":
        return (
            "author a reviewed exact Lean definition from the source references and "
            "semantic contract before local Lean checking"
        )
    if status == "EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_NOT_REQUESTED":
        return (
            "run the exact semantic-definition Lean repair executor with local Lean "
            "on the definition-only candidate before semantic review or proof-body "
            "search resumes"
        )
    if status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS:
        return (
            "review the typechecked definition-only candidate for source semantic "
            "faithfulness before importing it into the exact source-theorem "
            "candidate; do not treat this as source theorem proof"
        )
    if status == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED":
        return (
            "repair the typechecked definition-only candidate against the listed "
            "semantic alignment blockers before importing it or resuming exact "
            "source-theorem proof-body search"
        )
    if status == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_FILE_MISSING":
        return (
            "restore or regenerate the definition-only candidate artifact before "
            "semantic review and source-theorem proof-body search"
        )
    if status == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_FAILED":
        return (
            "repair the definition-only candidate Lean errors before semantic "
            "review and source-theorem proof-body search"
        )
    if status == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING":
        return (
            "rerun the exact semantic-definition Lean repair executor in a Lake "
            "project that can resolve Mathlib/source imports before semantic "
            "review or proof-body search resumes"
        )
    if status == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING"
    ):
        return (
            "prepare the Lake project dependencies/cache for the definition-only "
            "candidate, then rerun local Lean before semantic review or proof-body "
            "search resumes"
        )
    if status == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_ENVIRONMENT_TIMEOUT":
        return (
            "preflight the Lake project dependencies/cache and rerun local Lean "
            "with a ready project or larger timeout before semantic review or "
            "proof-body search resumes"
        )
    if action == "review_import_source_declaration":
        return "repair source root/path resolution or candidate import declaration"
    return "review the Lean repair task and assign it to ProofEngineer"


def _semantic_typecheck_status_from_execution(
    *,
    existing_status: str,
    execution_status: str,
    current_local_lean_checked: bool,
    current_local_lean_compiled: bool,
) -> str:
    if (
        execution_status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
        and current_local_lean_checked
        and current_local_lean_compiled
    ):
        return TYPECHECKED_CANDIDATE_LOCAL_LEAN_EVIDENCE_STATUS
    return existing_status


def _runtime_queue_status_from_execution(
    *,
    execution_status: str,
    local_lean_compiled: bool,
    local_definition_lean_compiled: bool,
) -> str:
    import_candidate_ready = (
        execution_status == "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF"
        and local_lean_compiled
    )
    typechecked_candidate_review_ready = (
        execution_status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
        and local_definition_lean_compiled
    )
    definition_candidate_local_lean_pending = (
        execution_status == "EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_NOT_REQUESTED"
    )
    typechecked_candidate_semantic_review_blocked = (
        execution_status
        == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    definition_authoring_required = (
        execution_status == "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN"
    )
    return (
        "PENDING_REVIEWED_SEMANTIC_DEFINITION_IMPORT"
        if import_candidate_ready
        else "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
        if typechecked_candidate_review_ready
        else "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR"
        if typechecked_candidate_semantic_review_blocked
        else "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING"
        if definition_authoring_required
        else "PENDING_EXACT_SEMANTIC_DEFINITION_LOCAL_LEAN_CHECK"
        if definition_candidate_local_lean_pending
        else ""
    )


def _environment_repair_task(row: Mapping[str, Any]) -> dict[str, Any]:
    candidate_file = _environment_repair_candidate_file(row)
    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    placeholder_symbol = str(row.get("placeholder_symbol", "") or "")
    candidate_definition_request = dict(
        row.get("candidate_definition_request", {}) or {}
    )
    if not candidate_definition_request:
        candidate_definition_request = _candidate_definition_request(
            row,
            placeholder_symbol=placeholder_symbol,
        )
    else:
        candidate_definition_request.setdefault("target_theorem_name", target_theorem_name)
        if target_ids and not candidate_definition_request.get("target_ids"):
            candidate_definition_request["target_ids"] = list(target_ids)
        if placeholder_symbol and not candidate_definition_request.get(
            "placeholder_symbol"
        ):
            candidate_definition_request["placeholder_symbol"] = placeholder_symbol
    task_id = (
        "source_theorem_exact_semantic_definition_lean_environment_repair_task:"
        + stable_hash(
            [
                row.get("execution_result_id", ""),
                target_theorem_name,
                row.get("placeholder_symbol", ""),
                candidate_file,
                row.get("candidate_lean_project_hint", ""),
            ]
        )[:20]
    )
    project_hint = str(
        row.get("candidate_lean_project_hint", "")
        or row.get("lean_project", "")
        or ""
    )
    command_hint = (
        f"lake env lean {candidate_file}" if project_hint and candidate_file else ""
    )
    failure_classification = str(row.get("failure_classification", "") or "")
    runtime_queue_status = (
        "PENDING_LEAN_DEPENDENCY_ENVIRONMENT_REPAIR"
        if failure_classification in {"lean_dependency_fetch_failed", "local_lean_timeout"}
        else "PENDING_LEAN_LOCAL_LIBRARY_BUILD_REPAIR"
        if failure_classification == "lean_local_library_build_unresolved"
        else "PENDING_LEAN_IMPORT_ENVIRONMENT_REPAIR"
    )
    return {
        "schema_version": 1,
        "artifact_kind": ENVIRONMENT_REPAIR_TASK_ARTIFACT_KIND,
        "environment_repair_task_id": task_id,
        "source_execution_result_id": str(row.get("execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            row.get("source_lean_repair_task_id", "") or ""
        ),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": placeholder_symbol,
        "candidate_source_file": candidate_file,
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        **_exact_semantic_definition_context(row),
        "candidate_definition_request": candidate_definition_request,
        "candidate_lean_project_hint": project_hint,
        "recommended_command": command_hint,
        "failure_classification": failure_classification,
        "local_lean_diagnostics": list(row.get("local_lean_diagnostics", []) or [])[:12],
        "runtime_queue_status": runtime_queue_status,
        "next_owner": "ProofEngineer/LeanProver",
        "recommended_next_action": (
            "Run the candidate in its inferred Lake project or port the candidate "
            "declaration/import cone into the exact source-theorem project before "
            "resuming proof-body search."
        ),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "proof_evidence_status": ENVIRONMENT_REPAIR_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "This environment repair task is operational feedback only. It does "
            "not prove the semantic definition or the source theorem; promotion "
            "requires a later local Lean/AXLE verifier manifest."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _environment_repair_candidate_file(row: Mapping[str, Any]) -> str:
    candidate_source_file = str(row.get("candidate_source_file", "") or "")
    if candidate_source_file:
        return candidate_source_file
    return str(row.get("definition_only_candidate_artifact_path", "") or "")


def _candidate_definition_request(
    row: Mapping[str, Any],
    *,
    placeholder_symbol: str,
) -> dict[str, Any]:
    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    required_anchor_names = _required_anchor_names_for_placeholder(placeholder_symbol)
    available_anchor_names = [
        str(value).strip()
        for value in row.get("premise_semantic_anchor_binder_names", []) or []
        if str(value).strip()
    ]
    available_binders_by_name = _available_semantic_binders_by_name(row)
    required_binders = [
        dict(available_binders_by_name[name])
        for name in required_anchor_names
        if name in available_binders_by_name
    ]
    missing_required = [
        name for name in required_anchor_names if name not in available_anchor_names
    ]
    required_adapter_object_names = _required_adapter_object_names_for_placeholder(
        placeholder_symbol
    )
    available_adapter_object_names = [
        str(value).strip()
        for value in row.get(
            "source_to_bridge_adapter_object_names_requiring_source_instantiation",
            [],
        )
        or []
        if str(value).strip()
    ]
    missing_required_adapter_object_names = [
        name
        for name in required_adapter_object_names
        if name not in available_adapter_object_names
    ]
    placeholder_policy = exact_semantic_definition_placeholder_policy(
        placeholder_symbol
    )
    return {
        "schema_version": 1,
        "request_kind": "source_theorem_exact_semantic_definition_candidate",
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": placeholder_symbol,
        "placeholder_policy_id": placeholder_policy.policy_id,
        "placeholder_policy_scope": placeholder_policy.policy_scope,
        "semantic_goal": placeholder_policy.semantic_goal,
        "required_anchor_names": required_anchor_names,
        "available_anchor_names": available_anchor_names,
        "missing_required_anchor_names": missing_required,
        "required_binders": required_binders,
        "required_adapter_object_names": required_adapter_object_names,
        "available_adapter_object_names": available_adapter_object_names,
        "missing_required_adapter_object_names": (
            missing_required_adapter_object_names
        ),
        "source_to_bridge_adapter_instantiation_group_id": str(
            row.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        ),
        "required_bridge_premise_names_for_shared_instantiation": list(
            row.get("required_bridge_premise_names_for_shared_instantiation", [])
            or []
        ),
        "expected_outputs": {
            "definition_only_candidate_artifact_path": (
                "Lean file containing only exact semantic definitions and imports"
            ),
            "candidate_artifact_path": (
                "Lean file integrating the candidate definitions into the exact "
                "source-theorem proof environment"
            ),
            "local_definition_lean_checked": False,
            "local_definition_lean_compiled": False,
            "semantic_definition_typecheck_evidence_status": (
                "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
            ),
        },
        "forbidden_shortcuts": [
            "do not define the placeholder as True",
            "do not add axiom/sorry/admit/unsafe",
            "do not assume or restate the source theorem target",
            "do not introduce stronger assumptions than the source theorem binders",
            "do not import generic declarations found by lexical source lookup as the definition",
        ],
        "local_lean_gate": (
            "The definition-only candidate must compile under local Lean/AXLE "
            "before it can be used by proof-body execution; compilation is still "
            "semantic-definition evidence only, not theorem proof."
        ),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _required_anchor_names_for_placeholder(placeholder_symbol: str) -> list[str]:
    return list(
        exact_semantic_definition_placeholder_policy(
            placeholder_symbol
        ).required_anchor_names
    )


def _required_adapter_object_names_for_placeholder(
    placeholder_symbol: str,
) -> list[str]:
    return list(
        exact_semantic_definition_placeholder_policy(
            placeholder_symbol
        ).required_adapter_object_names
    )


def _available_semantic_binders_by_name(
    row: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    binders_by_name: dict[str, Mapping[str, Any]] = {}
    for binder in row.get("premise_semantic_anchor_binders", []) or []:
        if not isinstance(binder, Mapping):
            continue
        name = str(binder.get("name", "") or "")
        if name:
            binders_by_name[name] = binder
    for binder in row.get("exact_source_theorem_binders", []) or []:
        if not isinstance(binder, Mapping):
            continue
        name = str(binder.get("name", "") or "")
        if name:
            binders_by_name[name] = binder
    return binders_by_name


def _has_placeholder_policy_lineage(row: Mapping[str, Any]) -> bool:
    return bool(
        str(row.get("placeholder_policy_id", "") or "").strip()
        and str(row.get("placeholder_policy_scope", "") or "").strip()
    )


def _count_placeholder_policy_lineage(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if _has_placeholder_policy_lineage(row))


def _placeholder_policy_lineage_complete(
    *row_groups: Sequence[Mapping[str, Any]],
) -> bool:
    for rows in row_groups:
        for row in rows:
            if not _has_placeholder_policy_lineage(row):
                return False
    return True


def _typechecked_candidate_review_packet(row: Mapping[str, Any]) -> dict[str, Any]:
    """Create a semantic-review handoff for a typechecked definition candidate."""

    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    packet_id = (
        "source_theorem_exact_semantic_definition_typechecked_candidate_review:"
        + stable_hash(
            [
                row.get("execution_result_id", ""),
                row.get("source_lean_repair_task_id", ""),
                row.get("target_theorem_name", ""),
                row.get("placeholder_symbol", ""),
                row.get("definition_only_candidate_artifact_path", ""),
                row.get("materialization_order_index", 0),
            ]
        )[:24]
    )
    placeholder = str(row.get("placeholder_symbol", "") or "")
    candidate_definition_request = dict(
        row.get("candidate_definition_request", {}) or {}
    )
    if not candidate_definition_request:
        candidate_definition_request = _candidate_definition_request(
            row,
            placeholder_symbol=placeholder,
        )
    else:
        candidate_definition_request.setdefault(
            "target_theorem_name",
            target_theorem_name,
        )
        if placeholder and not candidate_definition_request.get("placeholder_symbol"):
            candidate_definition_request["placeholder_symbol"] = placeholder
        if target_ids and not candidate_definition_request.get("target_ids"):
            candidate_definition_request["target_ids"] = list(target_ids)
    return {
        "schema_version": 1,
        "artifact_kind": TYPECHECKED_CANDIDATE_REVIEW_PACKET_ARTIFACT_KIND,
        "review_packet_id": packet_id,
        "source_execution_result_id": str(row.get("execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            row.get("source_lean_repair_task_id", "") or ""
        ),
        "source_repair_packet_id": str(row.get("source_repair_packet_id", "") or ""),
        "source_review_packet_id": str(row.get("source_review_packet_id", "") or ""),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "source_definition_closure_work_order_id": str(
            row.get("source_definition_closure_work_order_id", "") or ""
        ),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": placeholder,
        "materialization_order_index": int(
            row.get("materialization_order_index", 0) or 0
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "definition_only_candidate_file_resolved": bool(
            row.get("definition_only_candidate_file_resolved", False)
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        "candidate_definition_request": candidate_definition_request,
        "definition_contract": dict(row.get("definition_contract", {}) or {}),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "semantic_review_decision": str(
            row.get("semantic_review_decision", "") or ""
        ),
        "semantic_review_status": str(row.get("semantic_review_status", "") or ""),
        "semantic_review_evidence": list(
            row.get("semantic_review_evidence", []) or []
        ),
        "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
            row.get("llm_claimed_source_theorem_ready_for_exact_proof_body", False)
        ),
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        "source_to_bridge_adapter_instantiation_group_id": str(
            row.get("source_to_bridge_adapter_instantiation_group_id", "") or ""
        ),
        "required_adapter_object_names": list(
            row.get("required_adapter_object_names", []) or []
        ),
        "available_adapter_object_names": list(
            row.get("available_adapter_object_names", []) or []
        ),
        "missing_required_adapter_object_names": list(
            row.get("missing_required_adapter_object_names", []) or []
        ),
        **_exact_semantic_definition_context(row),
        "semantic_review_required_before_proof_body": True,
        "source_theorem_ready_for_exact_proof_body": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "runtime_queue_status": (
            "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
        ),
        "review_policy": (
            "Compare the typechecked definition-only candidate against the source "
            "theorem binders, source references, and adapter-object dependencies "
            "before it can be imported into the exact source-theorem proof body."
        ),
        "proof_evidence_status": TYPECHECKED_CANDIDATE_REVIEW_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "This packet records a locally typechecked exact semantic-definition "
            "candidate that still requires semantic faithfulness review. It is "
            "not source theorem proof and must not resume proof-body promotion "
            "until a reviewed candidate is verified by a later local Lean/AXLE gate."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _needs_author_definition_task(row: Mapping[str, Any]) -> bool:
    execution_status = str(row.get("execution_status", "") or "")
    return (
        execution_status == AUTHOR_DEFINITION_MISSING_STATUS
        or execution_status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
        or execution_status in AUTHOR_DEFINITION_REPAIR_STATUSES
    )


def _author_definition_runtime_queue_status(row: Mapping[str, Any]) -> str:
    execution_status = str(row.get("execution_status", "") or "")
    if execution_status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS:
        return TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_QUEUE_STATUS
    if execution_status in AUTHOR_DEFINITION_REPAIR_STATUSES:
        return "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    return "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING"


def _author_definition_trigger(row: Mapping[str, Any]) -> str:
    execution_status = str(row.get("execution_status", "") or "")
    if execution_status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS:
        return TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_TRIGGER
    if execution_status in AUTHOR_DEFINITION_REPAIR_STATUSES:
        return "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
    return "EXACT_SEMANTIC_DEFINITION_AUTHORING_REQUIRED"


def _author_definition_mode(execution_status: str) -> str:
    if execution_status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS:
        return TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_MODE
    if (
        execution_status
        == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    ):
        return "repair_typechecked_semantic_definition_candidate"
    if execution_status in AUTHOR_DEFINITION_REPAIR_STATUSES:
        return "repair_failed_exact_semantic_definition_candidate"
    return "author_missing_exact_semantic_definition"


def _author_definition_policy(
    *,
    execution_status: str,
    authoring_mode: str,
    placeholder: str,
) -> str:
    if authoring_mode == TYPECHECKED_CANDIDATE_REVIEW_AUTHORING_MODE:
        lead = (
            "Review the locally typechecked definition-only exact Lean candidate "
            "against the source theorem binders, semantic anchors, source "
            "references, and adapter dependencies. If it is faithful, return a "
            "reviewed candidate that preserves local Lean typecheckability; if "
            "it is not faithful, repair it or report explicit known_gaps. Do not "
            "claim source theorem proof. "
        )
    elif authoring_mode == "repair_typechecked_semantic_definition_candidate":
        lead = (
            "Repair the typechecked exact Lean definition against the listed "
            "semantic alignment blockers and required anchors. The replacement "
            "must preserve local Lean typecheckability while eliminating the "
            "semantic blockers. "
        )
    elif authoring_mode == "repair_failed_exact_semantic_definition_candidate":
        lead = (
            "Repair the existing definition-only exact Lean candidate using the "
            "local Lean diagnostics, failure classification, source theorem "
            "binders, source references, and semantic contract. The replacement "
            "must be designed to compile in the configured Lake project before "
            "semantic review resumes. "
        )
        if "ENVIRONMENT" in execution_status:
            lead += (
                "If the blocker is an import or dependency environment issue, "
                "avoid broad speculative imports and keep any required environment "
                "work explicit in known_gaps. "
            )
    else:
        lead = (
            "Synthesize the exact Lean definition from source theorem binders "
            "and source reference snippets. "
        )
    return (
        lead
        + "Do not import generic declarations for "
        f"{placeholder or 'the placeholder'} and do not define the placeholder "
        "as True, a constant, or an assumption-strengthening shortcut."
    )


def _author_definition_task(row: Mapping[str, Any]) -> dict[str, Any]:
    """Create an executable handoff when source references require synthesis."""

    execution_status = str(row.get("execution_status", "") or "")
    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    authoring_trigger = _author_definition_trigger(row)
    authoring_mode = _author_definition_mode(execution_status)
    semantic_review_required_before_proof_body = True
    task_id = (
        "source_theorem_exact_semantic_definition_authoring_task:"
        + stable_hash(
            [
                row.get("execution_result_id", ""),
                row.get("source_lean_repair_task_id", ""),
                target_theorem_name,
                row.get("placeholder_symbol", ""),
                row.get("repair_strategy", ""),
                row.get("execution_status", ""),
                row.get("source_reference_hints", [])[:5]
                if isinstance(row.get("source_reference_hints", []), list)
                else [],
            ]
        )[:20]
    )
    placeholder = str(row.get("placeholder_symbol", "") or "")
    candidate_definition_request = _candidate_definition_request(
        row,
        placeholder_symbol=placeholder,
    )
    return {
        "schema_version": 1,
        "artifact_kind": AUTHOR_DEFINITION_TASK_ARTIFACT_KIND,
        "authoring_task_id": task_id,
        "source_execution_result_id": str(row.get("execution_result_id", "") or ""),
        "source_execution_status": execution_status,
        "prior_source_execution_status": str(
            row.get("source_execution_status", "") or ""
        ),
        "prior_authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "prior_authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "source_lean_repair_task_id": str(
            row.get("source_lean_repair_task_id", "") or ""
        ),
        "source_repair_packet_id": str(row.get("source_repair_packet_id", "") or ""),
        "source_review_packet_id": str(row.get("source_review_packet_id", "") or ""),
        "source_definition_closure_work_order_id": str(
            row.get("source_definition_closure_work_order_id", "") or ""
        ),
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": placeholder,
        "authoring_trigger": authoring_trigger,
        "authoring_mode": authoring_mode,
        "lean_repair_action": str(row.get("lean_repair_action", "") or ""),
        "repair_strategy": str(row.get("repair_strategy", "") or ""),
        "definition_contract": dict(row.get("definition_contract", {}) or {}),
        "source_reference_hints": list(row.get("source_reference_hints", []) or []),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "candidate_source_file": str(row.get("candidate_source_file", "") or ""),
        "candidate_lean_project_hint": str(
            row.get("candidate_lean_project_hint", "") or ""
        ),
        "local_definition_lean_checked": bool(
            row.get("local_definition_lean_checked", False)
        ),
        "local_definition_lean_compiled": bool(
            row.get("local_definition_lean_compiled", False)
        ),
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        "semantic_alignment_constraints": list(
            row.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            row.get("semantic_alignment_blockers", []) or []
        ),
        "semantic_review_required_before_proof_body": (
            semantic_review_required_before_proof_body
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "semantic_review_contract": _author_definition_semantic_review_contract(
            row,
            authoring_mode=authoring_mode,
            semantic_review_required_before_proof_body=(
                semantic_review_required_before_proof_body
            ),
        ),
        "local_lean_requested": bool(row.get("local_lean_requested", False)),
        "local_lean_checked": bool(row.get("local_lean_checked", False)),
        "local_lean_compiled": bool(row.get("local_lean_compiled", False)),
        "local_lean_returncode": int(row.get("local_lean_returncode", 0) or 0),
        "local_lean_diagnostics": list(row.get("local_lean_diagnostics", []) or [])[:12],
        "local_lean_diagnostic_source_excerpts": [
            dict(value)
            for value in row.get("local_lean_diagnostic_source_excerpts", []) or []
            if isinstance(value, Mapping)
        ][:3],
        "failure_classification": str(row.get("failure_classification", "") or ""),
        "recommended_next_action": str(row.get("recommended_next_action", "") or ""),
        "candidate_repair_feedback": _current_candidate_repair_feedback(row),
        **_exact_semantic_definition_context(row),
        "candidate_definition_request": candidate_definition_request,
        "required_output_artifacts": [
            "definition_only_candidate_artifact_path",
            "candidate_artifact_path",
            "local_definition_lean_checked",
            "local_definition_lean_compiled",
            "semantic_definition_typecheck_evidence_status",
        ],
        "authoring_policy": _author_definition_policy(
            execution_status=execution_status,
            authoring_mode=authoring_mode,
            placeholder=placeholder,
        ),
        "acceptance_gate": (
            "A definition-only candidate must local-Lean check before semantic "
            "review, and exact source-theorem proof-body execution must remain "
            "blocked until the repaired candidate is verified."
        ),
        "runtime_queue_status": _author_definition_runtime_queue_status(row),
        "next_owner": "Formalizer/ProofEngineer/LeanProver",
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "This authoring task is a work order for creating a Lean definition. "
            "It is not source theorem proof, not semantic-definition kernel "
            "evidence, and not proof-body evidence until a later local Lean/AXLE "
            "manifest checks the materialized candidate."
        ),
        "kernel_proof_boundary": KERNEL_PROOF_BOUNDARY,
    }


def _current_candidate_repair_feedback(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return feedback for the current local Lean result, preserving prior notes."""

    feedback = dict(row.get("candidate_repair_feedback", {}) or {})
    diagnostics = list(row.get("local_lean_diagnostics", []) or [])[:12]
    diagnostic_source_excerpts = [
        dict(value)
        for value in row.get("local_lean_diagnostic_source_excerpts", []) or []
        if isinstance(value, Mapping)
    ][:3]
    checked = bool(row.get("local_lean_checked", False))
    failure_classification = str(row.get("failure_classification", "") or "")
    recommended_next_action = str(row.get("recommended_next_action", "") or "")
    feedback.update(
        {
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "candidate_artifact_path": str(
                row.get("candidate_artifact_path", "") or ""
            ),
            "candidate_source_file": str(row.get("candidate_source_file", "") or ""),
            "candidate_lean_project_hint": str(
                row.get("candidate_lean_project_hint", "") or ""
            ),
            "local_definition_lean_checked": bool(
                row.get("local_definition_lean_checked", False)
            ),
            "local_definition_lean_compiled": bool(
                row.get("local_definition_lean_compiled", False)
            ),
            "local_lean_checked": checked,
            "local_lean_compiled": bool(row.get("local_lean_compiled", False)),
            "local_lean_returncode": int(row.get("local_lean_returncode", 0) or 0),
            "source_execution_status": str(row.get("execution_status", "") or ""),
            "source_execution_result_id": str(row.get("execution_result_id", "") or ""),
        }
    )
    if checked or diagnostics:
        feedback["local_lean_diagnostics"] = diagnostics
    if diagnostic_source_excerpts:
        feedback["local_lean_diagnostic_source_excerpts"] = diagnostic_source_excerpts
    if failure_classification:
        feedback["failure_classification"] = failure_classification
    if recommended_next_action:
        feedback["recommended_next_action"] = recommended_next_action
    return feedback


def _author_definition_semantic_review_contract(
    row: Mapping[str, Any],
    *,
    authoring_mode: str,
    semantic_review_required_before_proof_body: bool,
) -> dict[str, Any]:
    """Describe non-proof semantic review evidence expected from an authoring task."""

    return {
        "contract_kind": "exact_semantic_definition_authoring_semantic_review",
        "authoring_mode": authoring_mode,
        "semantic_review_required_before_proof_body": bool(
            semantic_review_required_before_proof_body
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "review_decision_values": [
            "approved_definition_candidate",
            "repair_required",
            "blocked_or_insufficient_context",
        ],
        "required_review_checks": [
            "compare the candidate against source theorem binders",
            "check required semantic anchors and adapter dependencies",
            "list known gaps instead of guessing missing source context",
            "preserve local Lean typecheckability constraints",
        ],
        "existing_definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "proof_body_promotion_gate": (
            "LLM semantic review evidence is not source theorem proof and must "
            "not set source_theorem_ready_for_exact_proof_body. A later local "
            "Lean/AXLE recheck queue must verify any reviewed candidate before "
            "exact proof-body work resumes."
        ),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
    }


def _semantic_import_candidate_blocker(
    *,
    placeholder_symbol: str,
    candidate_declaration: Mapping[str, Any],
) -> str:
    if not candidate_declaration:
        return ""
    explicit_allowed = candidate_declaration.get("semantic_import_candidate_allowed")
    if explicit_allowed is False:
        status = str(candidate_declaration.get("source_semantic_review_status", "") or "")
        reason = str(candidate_declaration.get("source_semantic_review_reason", "") or "")
        return (
            f"semantic import candidate blocked by source lookup review: {status}"
            + (f"; {reason}" if reason else "")
        )
    normalized_placeholder = _compact_identifier(placeholder_symbol)
    snippet = str(candidate_declaration.get("snippet", "") or "")
    policy_blocker = exact_semantic_definition_import_policy_blocker(
        normalized_placeholder,
        snippet=snippet,
    )
    if policy_blocker:
        status = str(policy_blocker.get("source_semantic_review_status", "") or "")
        reason = str(policy_blocker.get("source_semantic_review_reason", "") or "")
        return (
            f"semantic import candidate blocked by placeholder policy: {status}"
            + (f"; {reason}" if reason else "")
        )
    return ""


def _exact_semantic_definition_context(row: Mapping[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    placeholder_symbol = str(
        row.get("placeholder_symbol", "")
        or input_summary.get("placeholder_symbol", "")
        or ""
    ).strip()
    for key in EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS:
        value = row.get(key, None)
        if value in (None, "", [], {}):
            value = input_summary.get(key, None)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, Mapping):
            context[key] = dict(value)
        elif isinstance(value, list):
            context[key] = list(value)
        else:
            context[key] = value
    if placeholder_symbol:
        placeholder_policy = exact_semantic_definition_placeholder_policy(
            placeholder_symbol
        )
        context.setdefault("placeholder_policy_id", placeholder_policy.policy_id)
        context.setdefault("placeholder_policy_scope", placeholder_policy.policy_scope)
    candidate_request = context.get("candidate_definition_request", {})
    if isinstance(candidate_request, Mapping):
        target_theorem_name = str(row.get("target_theorem_name", "") or "")
        target_ids = _exact_semantic_definition_target_ids(
            row,
            fallback_target=target_theorem_name,
        )
        normalized_request = dict(candidate_request)
        normalized_request.setdefault("target_theorem_name", target_theorem_name)
        if placeholder_symbol and not normalized_request.get("placeholder_symbol"):
            normalized_request["placeholder_symbol"] = placeholder_symbol
        if placeholder_symbol:
            placeholder_policy = exact_semantic_definition_placeholder_policy(
                placeholder_symbol
            )
            normalized_request.setdefault(
                "placeholder_policy_id",
                placeholder_policy.policy_id,
            )
            normalized_request.setdefault(
                "placeholder_policy_scope",
                placeholder_policy.policy_scope,
            )
        if target_ids and not normalized_request.get("target_ids"):
            normalized_request["target_ids"] = list(target_ids)
        context["candidate_definition_request"] = normalized_request
    return context


def _exact_semantic_definition_target_ids(
    row: Mapping[str, Any],
    *,
    fallback_target: str = "",
) -> list[str]:
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    raw_values = (
        row.get("target_ids", [])
        or row.get("target_id", "")
        or row.get("target_theorem_goal_ids", [])
        or input_summary.get("target_ids", [])
        or input_summary.get("target_id", "")
        or input_summary.get("target_theorem_goal_ids", [])
        or []
    )
    if isinstance(raw_values, Mapping):
        values = [str(key).strip() for key in raw_values.keys()]
    elif isinstance(raw_values, str):
        values = [raw_values.strip()]
    elif isinstance(raw_values, Sequence):
        values = [str(value).strip() for value in raw_values]
    else:
        values = [str(raw_values).strip()]
    target_ids = [value for value in values if value]
    fallback = str(fallback_target or "").strip()
    if not target_ids and fallback:
        target_ids = [fallback]
    return list(dict.fromkeys(target_ids))


def _compact_identifier(value: str) -> str:
    return compact_exact_semantic_placeholder_key(value)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _environment_repair_learning_row(row: Mapping[str, Any]) -> dict[str, Any]:
    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    placeholder_symbol = str(row.get("placeholder_symbol", "") or "")
    candidate_definition_request = dict(
        row.get("candidate_definition_request", {}) or {}
    )
    if not candidate_definition_request:
        candidate_definition_request = _candidate_definition_request(
            row,
            placeholder_symbol=placeholder_symbol,
        )
    else:
        candidate_definition_request.setdefault("target_theorem_name", target_theorem_name)
        if target_ids and not candidate_definition_request.get("target_ids"):
            candidate_definition_request["target_ids"] = list(target_ids)
        if placeholder_symbol and not candidate_definition_request.get(
            "placeholder_symbol"
        ):
            candidate_definition_request["placeholder_symbol"] = placeholder_symbol
    return {
        "schema_version": 1,
        "artifact_kind": ENVIRONMENT_REPAIR_TASK_ARTIFACT_KIND,
        "learning_task": ENVIRONMENT_REPAIR_LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": placeholder_symbol,
        "environment_repair_task_id": str(
            row.get("environment_repair_task_id", "") or ""
        ),
        "candidate_definition_request": candidate_definition_request,
        **_exact_semantic_definition_context(row),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "input_summary": {
            "trigger": "EXACT_SEMANTIC_DEFINITION_LEAN_IMPORT_ENVIRONMENT_REPAIR",
            "target_theorem_name": target_theorem_name,
            "target_ids": target_ids,
            "placeholder_symbol": placeholder_symbol,
            "candidate_definition_request": candidate_definition_request,
            "candidate_source_file": str(row.get("candidate_source_file", "") or ""),
            "candidate_lean_project_hint": str(
                row.get("candidate_lean_project_hint", "") or ""
            ),
            "failure_classification": str(row.get("failure_classification", "") or ""),
            **_exact_semantic_definition_context(row),
            "source_theorem_kernel_verified": False,
            "semantic_definition_kernel_verified": False,
            "source_theorem_ready_for_exact_proof_body": False,
        },
        "target_behavior": (
            "repair Lean import environment so reviewed exact semantic definitions "
            "can be checked before source theorem proof-body search"
        ),
        "proof_evidence_status": ENVIRONMENT_REPAIR_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": str(row.get("proof_evidence_boundary", "") or ""),
    }


def _author_definition_learning_row(row: Mapping[str, Any]) -> dict[str, Any]:
    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    return {
        "schema_version": 1,
        "artifact_kind": AUTHOR_DEFINITION_TASK_ARTIFACT_KIND,
        "learning_task": AUTHOR_DEFINITION_LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "authoring_task_id": str(row.get("authoring_task_id", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "source_execution_result_id": str(
            row.get("source_execution_result_id", "") or ""
        ),
        "source_lean_repair_task_id": str(
            row.get("source_lean_repair_task_id", "") or ""
        ),
        "runtime_queue_status": str(row.get("runtime_queue_status", "") or ""),
        "local_lean_diagnostics": list(row.get("local_lean_diagnostics", []) or [])[:12],
        "local_lean_diagnostic_source_excerpts": [
            dict(value)
            for value in row.get("local_lean_diagnostic_source_excerpts", []) or []
            if isinstance(value, Mapping)
        ][:3],
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        **_exact_semantic_definition_context(row),
        "candidate_definition_request": dict(
            row.get("candidate_definition_request", {}) or {}
        ),
        "input_summary": {
            "trigger": str(row.get("authoring_trigger", "") or "")
            or "EXACT_SEMANTIC_DEFINITION_AUTHORING_REQUIRED",
            "target_theorem_name": target_theorem_name,
            "target_ids": target_ids,
            "authoring_mode": str(row.get("authoring_mode", "") or ""),
            "source_execution_status": str(row.get("source_execution_status", "") or ""),
            "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
            "source_reference_hint_count": len(
                row.get("source_reference_hints", []) or []
            ),
            "semantic_alignment_constraint_count": len(
                row.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                row.get("semantic_alignment_blockers", []) or []
            ),
            **_exact_semantic_definition_context(row),
            "candidate_definition_request": dict(
                row.get("candidate_definition_request", {}) or {}
            ),
            "required_output_artifacts": list(
                row.get("required_output_artifacts", []) or []
            ),
            "local_lean_diagnostics": list(
                row.get("local_lean_diagnostics", []) or []
            )[:12],
            "local_lean_diagnostic_source_excerpts": [
                dict(value)
                for value in row.get("local_lean_diagnostic_source_excerpts", []) or []
                if isinstance(value, Mapping)
            ][:3],
            "candidate_repair_feedback": dict(
                row.get("candidate_repair_feedback", {}) or {}
            ),
            "source_theorem_kernel_verified": False,
        },
        "target_behavior": (
            "materialize an exact semantic-definition candidate from source "
            "references so local Lean can check it before proof-body search resumes"
        ),
        "proof_evidence_status": AUTHOR_DEFINITION_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": str(row.get("proof_evidence_boundary", "") or ""),
    }


def _classify_local_lean_failure(diagnostics: Sequence[str]) -> str:
    text = "\n".join(str(value) for value in diagnostics)
    lowered = text.lower()
    if (
        "Could not resolve host" in text
        or "failed to clone" in lowered
        or "external command 'git' exited" in text
        or "no previous manifest, creating one from scratch" in text
        and "cloning https://" in text
    ):
        return "lean_dependency_fetch_failed"
    if "object file" in text and "does not exist" in text and ".olean" in text:
        if ".lake/build/lib/lean/" in text and ".lake/packages/" not in text:
            return "lean_local_library_build_unresolved"
        return "lean_import_environment_missing"
    if "unknown module prefix" in text or "No directory" in text and ".olean" in text:
        return "lean_import_environment_missing"
    if "timed out" in lowered:
        return "local_lean_timeout"
    if "failed to synthesize instance" in lowered or "synthinstancefailed" in lowered:
        return "local_lean_typeclass_synthesis_failed"
    if "invalid field" in lowered or "environment does not contain" in lowered:
        return "local_lean_invalid_field"
    if (
        "unknown constant" in lowered
        or "unknown identifier" in lowered
        or "unknown declaration" in lowered
        or "unknown namespace" in lowered
    ):
        return "local_lean_unknown_identifier"
    if "application type mismatch" in lowered or "type mismatch" in lowered:
        return "local_lean_type_mismatch"
    if "expected token" in lowered or "unexpected token" in lowered:
        return "local_lean_parse_error"
    if text.strip():
        return "local_lean_failed_unclassified"
    return ""


def _find_lake_project_root(path: Path) -> Path | None:
    start = path if path.is_dir() else path.parent
    for current in (start, *start.parents):
        if (
            (current / "lakefile.lean").exists()
            or (current / "lakefile.toml").exists()
            or (current / "lake-manifest.json").exists()
        ):
            return current
    return None


def _learning_row(row: Mapping[str, Any]) -> dict[str, Any]:
    execution_status = str(row.get("execution_status", "") or "")
    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_ids = _exact_semantic_definition_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    local_lean_compiled = bool(row.get("local_lean_compiled", False))
    local_definition_lean_compiled = bool(
        row.get("local_definition_lean_compiled", False)
    )
    local_definition_lean_checked = bool(row.get("local_definition_lean_checked", False))
    semantic_alignment_blockers = [
        str(value)
        for value in row.get("semantic_alignment_blockers", []) or []
        if str(value).strip()
    ]
    import_candidate_ready = (
        execution_status == "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF"
        and local_lean_compiled
    )
    typechecked_candidate_review_ready = (
        execution_status == TYPECHECKED_CANDIDATE_REVIEW_REQUIRED_STATUS
        and local_definition_lean_compiled
    )
    definition_candidate_local_lean_pending = (
        execution_status == "EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_NOT_REQUESTED"
    )
    typechecked_candidate_semantic_review_blocked = (
        execution_status
        == "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    definition_authoring_required = (
        execution_status == "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN"
    )
    runtime_queue_status = _runtime_queue_status_from_execution(
        execution_status=execution_status,
        local_lean_compiled=local_lean_compiled,
        local_definition_lean_compiled=local_definition_lean_compiled,
    )
    return {
        "schema_version": 1,
        "artifact_kind": RESULT_ARTIFACT_KIND,
        "learning_task": LEARNING_TASK,
        "question_id": str(row.get("question_id", "") or ""),
        "question_title": str(row.get("question_title", "") or ""),
        "target_theorem_name": target_theorem_name,
        "target_ids": target_ids,
        "placeholder_symbol": str(row.get("placeholder_symbol", "") or ""),
        "execution_result_id": str(row.get("execution_result_id", "") or ""),
        "source_lean_repair_task_id": str(
            row.get("source_lean_repair_task_id", "") or ""
        ),
        "source_repair_packet_id": str(row.get("source_repair_packet_id", "") or ""),
        "source_execution_status": str(row.get("source_execution_status", "") or ""),
        "authoring_trigger": str(row.get("authoring_trigger", "") or ""),
        "authoring_mode": str(row.get("authoring_mode", "") or ""),
        "source_lean_repair_action": str(
            row.get("source_lean_repair_action", "") or ""
        ),
        "source_repair_strategy": str(row.get("source_repair_strategy", "") or ""),
        "execution_status": execution_status,
        "candidate_source_file": str(row.get("candidate_source_file", "") or ""),
        "candidate_lean_project_hint": str(
            row.get("candidate_lean_project_hint", "") or ""
        ),
        "candidate_import_declarations": list(
            row.get("candidate_import_declarations", []) or []
        ),
        "definition_only_candidate_artifact_path": str(
            row.get("definition_only_candidate_artifact_path", "") or ""
        ),
        "definition_only_candidate_file_resolved": bool(
            row.get("definition_only_candidate_file_resolved", False)
        ),
        "candidate_artifact_path": str(row.get("candidate_artifact_path", "") or ""),
        "local_definition_lean_checked": local_definition_lean_checked,
        "local_definition_lean_compiled": local_definition_lean_compiled,
        "semantic_definition_typecheck_evidence_status": str(
            row.get("semantic_definition_typecheck_evidence_status", "") or ""
        ),
        "semantic_alignment_blockers": semantic_alignment_blockers,
        "semantic_review_decision": str(
            row.get("semantic_review_decision", "") or ""
        ),
        "semantic_review_status": str(row.get("semantic_review_status", "") or ""),
        "semantic_review_evidence": list(
            row.get("semantic_review_evidence", []) or []
        ),
        "semantic_review_required_before_proof_body": bool(
            row.get("semantic_review_required_before_proof_body", False)
        ),
        "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
            row.get("llm_claimed_source_theorem_ready_for_exact_proof_body", False)
        ),
        "semantic_import_blocker": str(row.get("semantic_import_blocker", "") or ""),
        "failure_classification": str(row.get("failure_classification", "") or ""),
        "executed_tools": list(row.get("executed_tools", []) or []),
        "tool_call_trace": list(row.get("tool_call_trace", []) or []),
        "local_lean_checked": bool(row.get("local_lean_checked", False)),
        "local_lean_compiled": local_lean_compiled,
        "local_lean_diagnostics": list(row.get("local_lean_diagnostics", []) or [])[:12],
        "local_lean_diagnostic_source_excerpts": [
            dict(value)
            for value in row.get("local_lean_diagnostic_source_excerpts", []) or []
            if isinstance(value, Mapping)
        ][:3],
        "semantic_definition_import_candidate_ready": import_candidate_ready,
        "semantic_definition_typechecked_candidate_review_ready": (
            typechecked_candidate_review_ready
        ),
        "semantic_definition_typechecked_candidate_semantic_review_blocked": (
            typechecked_candidate_semantic_review_blocked
        ),
        "semantic_definition_authoring_required": definition_authoring_required,
        "semantic_definition_local_lean_check_pending": (
            definition_candidate_local_lean_pending
        ),
        "runtime_queue_status": runtime_queue_status,
        **_exact_semantic_definition_context(row),
        "candidate_repair_feedback": dict(
            row.get("candidate_repair_feedback", {}) or {}
        ),
        "source_theorem_kernel_verified": False,
        "semantic_definition_kernel_verified": False,
        "source_theorem_ready_for_exact_proof_body": False,
        "input_summary": {
            "trigger": "EXACT_SOURCE_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION",
            "target_theorem_name": target_theorem_name,
            "target_ids": target_ids,
            "lean_repair_action": str(row.get("lean_repair_action", "") or ""),
            "source_execution_status": str(
                row.get("source_execution_status", "") or ""
            ),
            "authoring_mode": str(row.get("authoring_mode", "") or ""),
            "source_lean_repair_action": str(
                row.get("source_lean_repair_action", "") or ""
            ),
            "source_repair_strategy": str(
                row.get("source_repair_strategy", "") or ""
            ),
            "execution_status": execution_status,
            "candidate_source_file": str(row.get("candidate_source_file", "") or ""),
            "candidate_source_file_resolved": bool(
                row.get("candidate_source_file_resolved", False)
            ),
            "candidate_lean_project_hint": str(
                row.get("candidate_lean_project_hint", "") or ""
            ),
            "candidate_import_declarations": list(
                row.get("candidate_import_declarations", []) or []
            ),
            "definition_only_candidate_artifact_path": str(
                row.get("definition_only_candidate_artifact_path", "") or ""
            ),
            "definition_only_candidate_file_resolved": bool(
                row.get("definition_only_candidate_file_resolved", False)
            ),
            "local_definition_lean_checked": local_definition_lean_checked,
            "local_definition_lean_compiled": local_definition_lean_compiled,
            "semantic_definition_typecheck_evidence_status": str(
                row.get("semantic_definition_typecheck_evidence_status", "") or ""
            ),
            "semantic_alignment_blockers": semantic_alignment_blockers,
            "semantic_review_decision": str(
                row.get("semantic_review_decision", "") or ""
            ),
            "semantic_review_status": str(
                row.get("semantic_review_status", "") or ""
            ),
            "semantic_review_required_before_proof_body": bool(
                row.get("semantic_review_required_before_proof_body", False)
            ),
            "llm_claimed_source_theorem_ready_for_exact_proof_body": bool(
                row.get(
                    "llm_claimed_source_theorem_ready_for_exact_proof_body",
                    False,
                )
            ),
            "semantic_import_blocker": str(
                row.get("semantic_import_blocker", "") or ""
            ),
            "local_lean_requested": bool(row.get("local_lean_requested", False)),
            "local_lean_checked": bool(row.get("local_lean_checked", False)),
            "local_lean_compiled": local_lean_compiled,
            "local_lean_diagnostics": list(
                row.get("local_lean_diagnostics", []) or []
            )[:12],
            "local_lean_diagnostic_source_excerpts": [
                dict(value)
                for value in row.get("local_lean_diagnostic_source_excerpts", []) or []
                if isinstance(value, Mapping)
            ][:3],
            "executed_tools": list(row.get("executed_tools", []) or []),
            "tool_call_trace": list(row.get("tool_call_trace", []) or []),
            "failure_classification": str(row.get("failure_classification", "") or ""),
            "semantic_definition_import_candidate_ready": import_candidate_ready,
            "semantic_definition_typechecked_candidate_review_ready": (
                typechecked_candidate_review_ready
            ),
            "semantic_definition_typechecked_candidate_semantic_review_blocked": (
                typechecked_candidate_semantic_review_blocked
            ),
            "semantic_definition_authoring_required": definition_authoring_required,
            "semantic_definition_local_lean_check_pending": (
                definition_candidate_local_lean_pending
            ),
            "runtime_queue_status": runtime_queue_status,
            **_exact_semantic_definition_context(row),
            "semantic_definition_kernel_verified": False,
            "source_theorem_kernel_verified": False,
            "source_theorem_ready_for_exact_proof_body": False,
            "recommended_next_action": str(row.get("recommended_next_action", "") or ""),
        },
        "target_behavior": (
            "make reviewed exact semantic definitions executable before source "
            "theorem proof-body search resumes"
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": BOUNDARY,
    }


def _resolve_source_path(raw_path: str, source_roots: Sequence[Path]) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or path.exists():
        return path
    candidates: list[Path] = []
    parts = path.parts
    for root in source_roots:
        candidates.append(root / path)
        if parts and parts[0] == root.name:
            candidates.append(root.joinpath(*parts[1:]))
            candidates.append(root.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else path


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
