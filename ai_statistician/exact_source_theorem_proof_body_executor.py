from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    FORBIDDEN_ARTIFACT_TOKENS,
    _lean_command,
    _run_local_lean,
)


SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
ARTIFACT_KERNEL_NOT_SOURCE_STATUS = (
    "EXACT_SOURCE_THEOREM_PROOF_BODY_ARTIFACT_KERNEL_VERIFIED_NOT_SOURCE_THEOREM"
)
SOURCE_KERNEL_STATUS = "EXACT_SOURCE_THEOREM_PROOF_BODY_SOURCE_KERNEL_VERIFIED"
PROOF_EVIDENCE_BOUNDARY = (
    "Exact source-theorem proof-body executor rows materialize ProofEngineer "
    "candidate artifacts and run optional local Lean/AXLE checks. A compiled "
    "candidate is source-theorem proof evidence only when the exact declaration "
    "passes Lean/AXLE and the formal environment has no placeholder primitives "
    "or unresolved semantic repairs."
)


@dataclass(frozen=True)
class ExactSourceTheoremProofBodyExecutionResultRow:
    schema_version: int
    artifact_kind: str
    execution_result_id: str
    execution_queue_id: str
    source_work_order_id: str
    target_theorem_name: str
    target_lean_declaration: str
    expected_target_lean_declaration: str
    source_theorem_target_known: bool
    source_theorem_target_provenance: dict[str, object]
    semantic_alignment_constraints: tuple[str, ...]
    target_identity_status: str
    target_identity_errors: tuple[str, ...]
    source_candidate_artifact_path: str
    signature_probe_artifact_path: str
    candidate_artifact_path: str
    execution_transcript_path: str
    live_goal_location_ready: bool
    candidate_live_proof_state_request: dict[str, object]
    execution_status: str
    exact_declaration_present: bool
    forbidden_tokens_found: tuple[str, ...]
    formal_environment_placeholder_symbols: tuple[str, ...]
    formal_environment_typeclass_blockers: tuple[str, ...]
    formal_environment_semantically_closed: bool
    local_lean_requested: bool
    local_lean_checked: bool
    local_lean_compiled: bool
    artifact_kernel_verified: bool
    source_theorem_kernel_verified: bool
    verifier: str
    verification_strength: str
    lean_command: tuple[str, ...]
    lean_project: str
    lean_timeout: int
    returncode: int
    diagnostics: tuple[str, ...]
    failure_classification: str
    transcript_event_id: str
    transcript_event_written: bool
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_exact_source_theorem_proof_body_execution_results(
    exact_source_theorem_proof_body_execution_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    overwrite: bool = False,
    local_lean: bool = False,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Materialize and optionally Lean-check exact source theorem proof-body rows."""

    errors: list[str] = []
    queue_manifest_path = (
        exact_source_theorem_proof_body_execution_queue_dir
        / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    project_path = Path(lean_project) if lean_project else None
    command = lean_command or _lean_command(project_path)
    rows = [
        _execution_result_row(
            row,
            overwrite=overwrite,
            local_lean=local_lean,
            lean_project=project_path,
            lean_timeout=lean_timeout,
            lean_command=command,
        )
        for row in queue_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    by_status = Counter(row.execution_status for row in rows)
    by_failure = Counter(row.failure_classification for row in rows if row.failure_classification)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionResultManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "exact_source_theorem_proof_body_execution_queue_dir": str(
            exact_source_theorem_proof_body_execution_queue_dir
        ),
        "exact_source_theorem_proof_body_execution_queue_manifest": str(
            queue_manifest_path
        ),
        "overwrite": overwrite,
        "local_lean_requested": local_lean,
        "lean_project": str(project_path or ""),
        "lean_timeout": lean_timeout,
        "lean_command": list(command),
        "n_queue_rows": len(queue_payload.get("rows", []) or []),
        "n_execution_result_rows": len(rows),
        "n_materialized_candidate_artifacts": sum(
            1
            for row in rows
            if row.execution_status
            in {
                "EXACT_SOURCE_PROOF_BODY_CANDIDATE_MATERIALIZED",
                "EXACT_SOURCE_PROOF_BODY_CANDIDATE_REUSED",
                "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED",
                "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED",
                "EXACT_SOURCE_PROOF_BODY_ARTIFACT_KERNEL_VERIFIED_ENVIRONMENT_OPEN",
            }
        ),
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "n_artifact_kernel_verified": sum(1 for row in rows if row.artifact_kernel_verified),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_formal_environment_semantically_closed": sum(
            1 for row in rows if row.formal_environment_semantically_closed
        ),
        "n_placeholder_environment_blockers": sum(
            1
            for row in rows
            if row.formal_environment_placeholder_symbols
            or row.formal_environment_typeclass_blockers
        ),
        "n_source_theorem_target_known": sum(
            1 for row in rows if row.source_theorem_target_known
        ),
        "n_semantic_alignment_constraint_rows": sum(
            1 for row in rows if row.semantic_alignment_constraints
        ),
        "source_theorem_route_ids": list(
            dict.fromkeys(
                str(row.source_theorem_target_provenance.get("source_theorem_route_id", ""))
                for row in rows
                if str(row.source_theorem_target_provenance.get("source_theorem_route_id", ""))
            )
        ),
        "n_live_goal_location_ready": sum(1 for row in rows if row.live_goal_location_ready),
        "n_candidate_live_proof_state_requests": sum(
            1 for row in rows if row.candidate_live_proof_state_request
        ),
        "n_transcript_events_written": sum(1 for row in rows if row.transcript_event_written),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "all_source_theorems_kernel_verified": bool(rows)
        and all(row.source_theorem_kernel_verified for row in rows),
        "errors": errors,
        "by_execution_status": dict(sorted(by_status.items())),
        "by_failure_classification": dict(sorted(by_failure.items())),
        "rows": [asdict(row) for row in rows],
        "runtime_learning_export": {},
        "execution_result_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": (
            SOURCE_KERNEL_STATUS
            if any(row.source_theorem_kernel_verified for row in rows)
            else PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "candidate materialization is not proof evidence",
            "failed local Lean rows are feedback for ProofEngineer repair only",
            "compiled artifacts with placeholder primitives remain artifact evidence, not source-theorem evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        rows_path = out_dir / "exact_source_theorem_proof_body_execution_results.jsonl"
        manifest_path = out_dir / "exact_source_theorem_proof_body_execution_result_manifest.json"
        _write_jsonl(rows_path, [asdict(row) for row in rows])
        learning_payload = _export_runtime_learning_rows(rows=rows, out_dir=out_dir)
        payload["runtime_learning_export"] = learning_payload
        payload["execution_results_jsonl"] = str(rows_path)
        payload["execution_result_manifest"] = str(manifest_path)
        manifest_path.write_text(
            json.dumps(payload, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        (out_dir / "exact_source_theorem_proof_body_execution_result.md").write_text(
            _markdown_report(payload), encoding="utf-8"
        )
    return payload


def _execution_result_row(
    row: Mapping[str, Any],
    *,
    overwrite: bool,
    local_lean: bool,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
) -> ExactSourceTheoremProofBodyExecutionResultRow:
    errors: list[str] = []
    execution_queue_id = str(row.get("execution_queue_id", "") or "")
    source_work_order_id = str(row.get("source_work_order_id", "") or "")
    target_theorem_name = str(row.get("target_theorem_name", "") or "")
    target_lean_declaration = str(row.get("target_lean_declaration", "") or "")
    expected_target_lean_declaration = str(
        row.get("expected_target_lean_declaration", "") or target_lean_declaration
    )
    source_theorem_target_known = bool(row.get("source_theorem_target_known", False))
    source_target_provenance_raw = row.get("source_theorem_target_provenance", {})
    source_theorem_target_provenance = (
        dict(source_target_provenance_raw)
        if isinstance(source_target_provenance_raw, Mapping)
        else {}
    )
    semantic_alignment_constraints = _str_tuple(
        row.get("semantic_alignment_constraints", [])
    )
    target_identity_status = str(row.get("target_identity_status", "") or "")
    target_identity_errors = _str_tuple(row.get("target_identity_errors", []))
    source_candidate_artifact_path = str(
        row.get("source_candidate_artifact_path", "") or ""
    )
    signature_probe_artifact_path = str(row.get("signature_probe_artifact_path", "") or "")
    candidate_artifact_path = Path(str(row.get("candidate_artifact_path", "") or ""))
    execution_transcript_path = Path(str(row.get("execution_transcript_path", "") or ""))
    source_path = Path(signature_probe_artifact_path)
    already_repaired = row.get("already_repaired_environment", {})
    if not isinstance(already_repaired, Mapping):
        already_repaired = {}
    placeholder_symbols = _str_tuple(already_repaired.get("missing_formal_symbols", []))
    typeclass_blockers = _str_tuple(already_repaired.get("typeclass_blockers", []))
    live_goal_ready = bool(row.get("live_goal_location_ready"))
    candidate_live_request: dict[str, object] = {}
    status = "EXACT_SOURCE_PROOF_BODY_EXECUTION_BLOCKED"
    source = ""
    forbidden_tokens_found: tuple[str, ...] = ()
    exact_declaration_present = False
    if not execution_queue_id:
        errors.append("execution_queue_id missing")
    if row.get("execution_status") != "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER":
        errors.append("execution queue row is not ready for exact source proof-body work")
    if target_identity_errors:
        errors.append("execution queue row has target identity errors")
    if not source_path.exists():
        errors.append(f"signature probe artifact missing: {source_path}")
    if not str(candidate_artifact_path):
        errors.append("candidate_artifact_path missing")
    if not str(execution_transcript_path):
        errors.append("execution_transcript_path missing")
    if not errors:
        candidate_artifact_path.parent.mkdir(parents=True, exist_ok=True)
        execution_transcript_path.parent.mkdir(parents=True, exist_ok=True)
        if candidate_artifact_path.exists() and not overwrite:
            status = "EXACT_SOURCE_PROOF_BODY_CANDIDATE_REUSED"
        else:
            shutil.copyfile(source_path, candidate_artifact_path)
            status = "EXACT_SOURCE_PROOF_BODY_CANDIDATE_MATERIALIZED"
        try:
            source = candidate_artifact_path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"failed to read candidate artifact: {type(exc).__name__}: {exc}")
    if source:
        forbidden_tokens_found = tuple(
            token for token in FORBIDDEN_ARTIFACT_TOKENS if token in source
        )
        exact_declaration_present = _has_exact_declaration(source, target_lean_declaration)
        if forbidden_tokens_found:
            errors.append(
                "candidate artifact contains forbidden tokens: "
                + ", ".join(forbidden_tokens_found)
            )
        if target_lean_declaration and not exact_declaration_present:
            errors.append("candidate artifact does not contain the exact target declaration")
    candidate_live_request = _candidate_live_proof_state_request(
        row=row,
        candidate_artifact_path=candidate_artifact_path,
    )
    if candidate_live_request and not live_goal_ready:
        errors.append("execution queue did not provide a ready live goal location")

    checked = False
    compiled = False
    returncode = -1
    diagnostics: tuple[str, ...] = ()
    verifier = "local.exact_source_theorem_proof_body_executor"
    verification_strength = "exact_source_proof_body_static"
    if local_lean and not lean_command:
        errors.append("lean executable not found")
        diagnostics = ("lean executable not found",)
        status = "LOCAL_LEAN_UNAVAILABLE"
    elif local_lean and not errors:
        checked = True
        compiled, returncode, diagnostics = _run_local_lean(
            candidate_artifact_path,
            lean_command=lean_command,
            lean_project=lean_project,
            timeout_s=lean_timeout,
        )
        verification_strength = "local_lean_exact_source_proof_body_kernel"
        if compiled:
            status = (
                "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
                if not placeholder_symbols and not typeclass_blockers
                else "EXACT_SOURCE_PROOF_BODY_ARTIFACT_KERNEL_VERIFIED_ENVIRONMENT_OPEN"
            )
        else:
            status = "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
            errors.append("local Lean exact source proof-body candidate check failed")
    elif errors:
        status = "EXACT_SOURCE_PROOF_BODY_STATIC_CHECK_FAILED"

    formal_environment_closed = not placeholder_symbols and not typeclass_blockers
    artifact_kernel_verified = compiled and not forbidden_tokens_found and exact_declaration_present
    source_theorem_kernel_verified = artifact_kernel_verified and formal_environment_closed
    failure_classification = (
        ""
        if source_theorem_kernel_verified
        else _classify_failure(
            diagnostics,
            errors=errors,
            placeholder_symbols=placeholder_symbols,
            typeclass_blockers=typeclass_blockers,
        )
    )
    proof_status = (
        SOURCE_KERNEL_STATUS
        if source_theorem_kernel_verified
        else ARTIFACT_KERNEL_NOT_SOURCE_STATUS
        if artifact_kernel_verified
        else PROOF_EVIDENCE_STATUS
    )
    result_id = "exact_source_theorem_proof_body_execution_result:" + stable_hash(
        [execution_queue_id, candidate_artifact_path, status, proof_status]
    )[:20]
    transcript_event_id = "exact_source_theorem_proof_body_execution_event:" + stable_hash(
        [result_id, execution_transcript_path, status]
    )[:20]
    transcript_written = _append_transcript_event(
        execution_transcript_path,
        event_id=transcript_event_id,
        execution_result_id=result_id,
        execution_queue_id=execution_queue_id,
        target_theorem_name=target_theorem_name,
        target_lean_declaration=target_lean_declaration,
        expected_target_lean_declaration=expected_target_lean_declaration,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_provenance=source_theorem_target_provenance,
        semantic_alignment_constraints=semantic_alignment_constraints,
        target_identity_status=target_identity_status,
        target_identity_errors=target_identity_errors,
        source_candidate_artifact_path=source_candidate_artifact_path,
        candidate_artifact_path=candidate_artifact_path,
        status=status,
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        formal_environment_placeholder_symbols=placeholder_symbols,
        formal_environment_typeclass_blockers=typeclass_blockers,
        diagnostics=diagnostics,
        failure_classification=failure_classification,
        proof_evidence_status=proof_status,
    )
    return ExactSourceTheoremProofBodyExecutionResultRow(
        schema_version=SCHEMA_VERSION,
        artifact_kind="ExactSourceTheoremProofBodyExecutionResultRow",
        execution_result_id=result_id,
        execution_queue_id=execution_queue_id,
        source_work_order_id=source_work_order_id,
        target_theorem_name=target_theorem_name,
        target_lean_declaration=target_lean_declaration,
        expected_target_lean_declaration=expected_target_lean_declaration,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_provenance=source_theorem_target_provenance,
        semantic_alignment_constraints=semantic_alignment_constraints,
        target_identity_status=target_identity_status,
        target_identity_errors=target_identity_errors,
        source_candidate_artifact_path=source_candidate_artifact_path,
        signature_probe_artifact_path=signature_probe_artifact_path,
        candidate_artifact_path=str(candidate_artifact_path),
        execution_transcript_path=str(execution_transcript_path),
        live_goal_location_ready=live_goal_ready,
        candidate_live_proof_state_request=candidate_live_request,
        execution_status=status,
        exact_declaration_present=exact_declaration_present,
        forbidden_tokens_found=forbidden_tokens_found,
        formal_environment_placeholder_symbols=placeholder_symbols,
        formal_environment_typeclass_blockers=typeclass_blockers,
        formal_environment_semantically_closed=formal_environment_closed,
        local_lean_requested=local_lean,
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        verifier=verifier,
        verification_strength=verification_strength,
        lean_command=lean_command,
        lean_project=str(lean_project or ""),
        lean_timeout=lean_timeout,
        returncode=returncode,
        diagnostics=diagnostics,
        failure_classification=failure_classification,
        transcript_event_id=transcript_event_id,
        transcript_event_written=transcript_written,
        proof_evidence_status=proof_status,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _candidate_live_proof_state_request(
    *,
    row: Mapping[str, Any],
    candidate_artifact_path: Path,
) -> dict[str, object]:
    request = row.get("live_proof_state_request", {})
    if not isinstance(request, Mapping) or not request:
        return {}
    candidate_request = dict(request)
    candidate_request["request_id"] = (
        "exact_source_theorem_candidate_live_goal:"
        + stable_hash([row.get("execution_queue_id", ""), candidate_artifact_path])[:20]
    )
    candidate_request["target_lean_file"] = str(candidate_artifact_path)
    candidate_request["candidate_artifact_path"] = str(candidate_artifact_path)
    calls = []
    for call in request.get("mcp_tool_calls", []) or []:
        if not isinstance(call, Mapping):
            continue
        cloned = dict(call)
        args = dict(cloned.get("arguments", {}) or {})
        args["file"] = str(candidate_artifact_path)
        cloned["arguments"] = args
        calls.append(cloned)
    candidate_request["mcp_tool_calls"] = calls
    candidate_request["proof_evidence_status"] = "LIVE_PROOF_STATE_REQUEST_NOT_PROOF_EVIDENCE"
    return candidate_request


def _append_transcript_event(
    path: Path,
    *,
    event_id: str,
    execution_result_id: str,
    execution_queue_id: str,
    target_theorem_name: str,
    target_lean_declaration: str,
    expected_target_lean_declaration: str,
    source_theorem_target_known: bool,
    source_theorem_target_provenance: dict[str, object],
    semantic_alignment_constraints: tuple[str, ...],
    target_identity_status: str,
    target_identity_errors: tuple[str, ...],
    source_candidate_artifact_path: str,
    candidate_artifact_path: Path,
    status: str,
    local_lean_checked: bool,
    local_lean_compiled: bool,
    artifact_kernel_verified: bool,
    source_theorem_kernel_verified: bool,
    formal_environment_placeholder_symbols: tuple[str, ...],
    formal_environment_typeclass_blockers: tuple[str, ...],
    diagnostics: tuple[str, ...],
    failure_classification: str,
    proof_evidence_status: str,
) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict) and payload.get("event_id") == event_id:
                    return False
        event = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "event": "exact_source_theorem_proof_body_execution_result",
            "event_id": event_id,
            "execution_result_id": execution_result_id,
            "execution_queue_id": execution_queue_id,
            "target_theorem_name": target_theorem_name,
            "target_lean_declaration": target_lean_declaration,
            "expected_target_lean_declaration": expected_target_lean_declaration,
            "source_theorem_target_known": source_theorem_target_known,
            "source_theorem_target_provenance": source_theorem_target_provenance,
            "semantic_alignment_constraints": semantic_alignment_constraints,
            "target_identity_status": target_identity_status,
            "target_identity_errors": target_identity_errors,
            "source_candidate_artifact_path": source_candidate_artifact_path,
            "candidate_artifact_path": str(candidate_artifact_path),
            "execution_status": status,
            "local_lean_checked": local_lean_checked,
            "local_lean_compiled": local_lean_compiled,
            "artifact_kernel_verified": artifact_kernel_verified,
            "source_theorem_kernel_verified": source_theorem_kernel_verified,
            "formal_environment_placeholder_symbols": formal_environment_placeholder_symbols,
            "formal_environment_typeclass_blockers": formal_environment_typeclass_blockers,
            "diagnostics": diagnostics,
            "failure_classification": failure_classification,
            "proof_evidence_status": proof_evidence_status,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
        return True
    except OSError:
        return False


def _export_runtime_learning_rows(
    *,
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
    out_dir: Path,
) -> dict[str, object]:
    export_dir = out_dir / "runtime_learning_export"
    export_dir.mkdir(parents=True, exist_ok=True)
    learning_rows: list[dict[str, object]] = []
    for row in rows:
        trigger = (
            "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
            if row.source_theorem_kernel_verified
            else "EXACT_SOURCE_PROOF_BODY_ARTIFACT_KERNEL_ENVIRONMENT_OPEN"
            if row.artifact_kernel_verified
            else "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
            if row.local_lean_checked
            else "EXACT_SOURCE_PROOF_BODY_CANDIDATE_MATERIALIZED"
        )
        learning_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "learning_task": "exact_source_theorem_proof_body_execution_feedback",
                "target_theorem_name": row.target_theorem_name,
                "target_lean_declaration": row.target_lean_declaration,
                "expected_target_lean_declaration": row.expected_target_lean_declaration,
                "source_theorem_target_known": row.source_theorem_target_known,
                "source_theorem_target_provenance": row.source_theorem_target_provenance,
                "semantic_alignment_constraints": list(
                    row.semantic_alignment_constraints
                ),
                "target_identity_status": row.target_identity_status,
                "target_identity_errors": list(row.target_identity_errors),
                "source_work_order_id": row.source_work_order_id,
                "execution_queue_id": row.execution_queue_id,
                "execution_result_id": row.execution_result_id,
                "target_behavior": (
                    "Use this as ProofEngineer runtime feedback. Do not count it "
                    "as source-theorem proof unless source_theorem_kernel_verified=true."
                ),
                "input_summary": asdict(row),
                "kernel_verified_source_theorem_ids": (
                    [row.target_theorem_name] if row.source_theorem_kernel_verified else []
                ),
                "proof_evidence_status": row.proof_evidence_status,
                "trigger": trigger,
            }
        )
    rows_path = export_dir / "runtime_learning_rows.jsonl"
    _write_jsonl(rows_path, learning_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "ExactSourceTheoremProofBodyExecutionRuntimeLearningExport",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_learning_rows_jsonl": str(rows_path),
        "n_runtime_learning_rows": len(learning_rows),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_artifact_kernel_verified": sum(1 for row in rows if row.artifact_kernel_verified),
        "n_source_theorem_target_known": sum(
            1 for row in rows if row.source_theorem_target_known
        ),
        "n_semantic_alignment_constraint_rows": sum(
            1 for row in rows if row.semantic_alignment_constraints
        ),
        "source_theorem_route_ids": list(
            dict.fromkeys(
                str(row.source_theorem_target_provenance.get("source_theorem_route_id", ""))
                for row in rows
                if str(row.source_theorem_target_provenance.get("source_theorem_route_id", ""))
            )
        ),
        "proof_evidence_status": (
            SOURCE_KERNEL_STATUS
            if any(row.source_theorem_kernel_verified for row in rows)
            else PROOF_EVIDENCE_STATUS
        ),
        "boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    manifest_path = export_dir / "exact_source_theorem_proof_body_execution_learning_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "runtime_learning_rows_jsonl": str(rows_path),
        "runtime_learning_manifest": str(manifest_path),
        "n_runtime_learning_rows": len(learning_rows),
        "n_source_theorem_target_known": manifest["n_source_theorem_target_known"],
        "n_semantic_alignment_constraint_rows": manifest[
            "n_semantic_alignment_constraint_rows"
        ],
        "source_theorem_route_ids": manifest["source_theorem_route_ids"],
        "proof_evidence_status": manifest["proof_evidence_status"],
    }


def _classify_failure(
    diagnostics: tuple[str, ...],
    *,
    errors: list[str],
    placeholder_symbols: tuple[str, ...],
    typeclass_blockers: tuple[str, ...],
) -> str:
    if placeholder_symbols:
        return "formal_environment_placeholder_primitives"
    if typeclass_blockers:
        return "formal_environment_typeclass_blockers_unreviewed"
    text = "\n".join(diagnostics or tuple(errors)).lower()
    if "timed out" in text or "timeout" in text:
        return "local_lean_timeout"
    if "unknown module prefix" in text or "invalid 'import' command" in text:
        return "lean_import_environment_missing"
    if "unknown identifier" in text or "unknown constant" in text or "function expected" in text:
        return "formal_environment_symbol_missing"
    if "failed to synthesize" in text:
        return "formal_environment_instance_missing"
    if "unsolved goals" in text:
        return "proof_body_incomplete"
    if errors:
        return "static_execution_contract_failed"
    return ""


def _has_exact_declaration(source: str, declaration_name: str) -> bool:
    if not source or not declaration_name:
        return False
    pattern = r"\b(?:theorem|lemma)\s+" + re.escape(declaration_name) + r"\b"
    return re.search(pattern, source) is not None


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, default=str) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _str_tuple(values: Any) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(value) for value in values if str(value))


def _markdown_report(payload: Mapping[str, object]) -> str:
    lines = [
        "# Exact Source Theorem Proof-Body Executor",
        "",
        f"- Rows: {payload.get('n_ok')}/{payload.get('n_execution_result_rows')}",
        f"- Local Lean checked: {payload.get('n_local_lean_checked')}",
        f"- Artifact kernel verified: {payload.get('n_artifact_kernel_verified')}",
        f"- Source theorem kernel verified: {payload.get('n_source_theorem_kernel_verified')}",
        f"- Proof evidence status: `{payload.get('proof_evidence_status')}`",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('target_theorem_name')}`: "
            f"{row.get('execution_status')} "
            f"source_kernel={row.get('source_theorem_kernel_verified')}"
        )
        provenance = row.get("source_theorem_target_provenance", {})
        route_id = (
            provenance.get("source_theorem_route_id", "")
            if isinstance(provenance, Mapping)
            else ""
        )
        if route_id:
            lines.append(f"  source route: `{route_id}`")
        if row.get("semantic_alignment_constraints"):
            lines.append(
                "  semantic constraints: "
                + ", ".join(str(value) for value in row.get("semantic_alignment_constraints", []))
            )
        lines.append(f"  candidate: `{row.get('candidate_artifact_path')}`")
        lines.append(f"  failure: `{row.get('failure_classification')}`")
    return "\n".join(lines) + "\n"
