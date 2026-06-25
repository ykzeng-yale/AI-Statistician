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
DEFAULT_PROOF_BODY_TACTIC_ATTEMPTS = (
    "assumption",
    "trivial",
    "simp",
    "exact True.intro",
)


@dataclass(frozen=True)
class ExactSourceTheoremProofBodyExecutionResultRow:
    schema_version: int
    artifact_kind: str
    execution_result_id: str
    execution_queue_id: str
    source_work_order_id: str
    question_id: str
    question_title: str
    target_theorem_name: str
    target_lean_declaration: str
    expected_target_lean_declaration: str
    source_theorem_target_known: bool
    source_theorem_target_identity_status: str
    source_theorem_target_provenance: dict[str, object]
    semantic_alignment_constraints: tuple[str, ...]
    semantic_alignment_blockers: tuple[str, ...]
    source_theorem_proof_body_adapter_feedback_available: bool
    source_theorem_proof_body_adapter_kernel_verified: bool
    kernel_verified_source_theorem_proof_body_adapter_ids: tuple[str, ...]
    verified_source_theorem_proof_body_adapter_artifact_paths: tuple[str, ...]
    verified_source_theorem_proof_body_adapter_declarations: tuple[str, ...]
    source_theorem_proof_body_adapter_context_boundary: str
    kernel_verified_source_to_bridge_premise_derivation_ids: tuple[str, ...]
    verified_source_to_bridge_premise_derivation_artifact_paths: tuple[str, ...]
    verified_source_to_bridge_premise_derivation_declarations: tuple[str, ...]
    kernel_verified_theorem_reduction_closure_declarations: tuple[str, ...]
    verified_theorem_reduction_closure_artifact_paths: tuple[str, ...]
    kernel_verified_theorem_reduction_closure_target_ids: tuple[str, ...]
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
    proof_body_goal_reached: bool
    proof_body_goal_excerpt: tuple[str, ...]
    proof_body_gate_status: str
    local_lean_requested: bool
    local_lean_checked: bool
    local_lean_compiled: bool
    source_theorem_kernel_evidence_eligible: bool
    proof_body_attempted: bool
    proof_body_attempt_source: str
    proof_body_attempt_count: int
    proof_body_attempt_success: bool
    proof_body_attempt_strategy: str
    proof_body_attempt_summaries: tuple[str, ...]
    exact_goal_shape_obligation_ids: tuple[str, ...]
    exact_goal_shape_obligations: tuple[str, ...]
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
        "n_proof_body_attempted": sum(1 for row in rows if row.proof_body_attempted),
        "n_proof_body_attempt_success": sum(
            1 for row in rows if row.proof_body_attempt_success
        ),
        "n_artifact_kernel_verified": sum(1 for row in rows if row.artifact_kernel_verified),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_formal_environment_semantically_closed": sum(
            1 for row in rows if row.formal_environment_semantically_closed
        ),
        "n_proof_body_goal_reached": sum(1 for row in rows if row.proof_body_goal_reached),
        "n_proof_body_goal_excerpt_rows": sum(
            1 for row in rows if row.proof_body_goal_excerpt
        ),
        "first_proof_body_goal_excerpt": next(
            (list(row.proof_body_goal_excerpt) for row in rows if row.proof_body_goal_excerpt),
            [],
        ),
        "n_proof_body_goal_reached_with_semantic_blockers": sum(
            1 for row in rows if row.proof_body_goal_reached and row.semantic_alignment_blockers
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
        "n_source_theorem_target_unpromoted_rows": sum(
            1
            for row in rows
            if row.source_theorem_target_identity_status
            == "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
        ),
        "n_semantic_alignment_constraint_rows": sum(
            1 for row in rows if row.semantic_alignment_constraints
        ),
        "n_semantic_alignment_blocker_rows": sum(
            1 for row in rows if row.semantic_alignment_blockers
        ),
        "n_source_theorem_proof_body_adapter_context_rows": sum(
            1
            for row in rows
            if row.source_theorem_proof_body_adapter_feedback_available
            or row.source_theorem_proof_body_adapter_kernel_verified
            or row.kernel_verified_source_theorem_proof_body_adapter_ids
        ),
        "n_source_theorem_proof_body_adapter_kernel_verified_context_rows": sum(
            1 for row in rows if row.source_theorem_proof_body_adapter_kernel_verified
        ),
        "n_kernel_verified_source_to_bridge_premise_derivation_context_rows": sum(
            1
            for row in rows
            if row.kernel_verified_source_to_bridge_premise_derivation_ids
            or row.verified_source_to_bridge_premise_derivation_artifact_paths
            or row.verified_source_to_bridge_premise_derivation_declarations
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": list(
            dict.fromkeys(
                premise_id
                for row in rows
                for premise_id in row.kernel_verified_source_to_bridge_premise_derivation_ids
            )
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
        "dominant_failure_classification": _dominant_failure_classification(rows),
        "by_proof_body_gate_status": dict(
            sorted(Counter(row.proof_body_gate_status for row in rows).items())
        ),
        "rows": [asdict(row) for row in rows],
        "runtime_learning_export": {},
        "execution_result_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": (
            SOURCE_KERNEL_STATUS
            if any(row.source_theorem_kernel_verified for row in rows)
            else ARTIFACT_KERNEL_NOT_SOURCE_STATUS
            if any(row.artifact_kernel_verified for row in rows)
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
        payload["runtime_learning_rows_jsonl"] = str(
            learning_payload.get("runtime_learning_rows_jsonl", "") or ""
        )
        payload["runtime_learning_manifest"] = str(
            learning_payload.get("runtime_learning_manifest", "") or ""
        )
        payload["n_runtime_learning_rows"] = int(
            learning_payload.get("n_runtime_learning_rows", 0) or 0
        )
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
    question_id = str(
        row.get("question_id", "")
        or source_theorem_target_provenance.get("question_id", "")
        or source_theorem_target_provenance.get("source_theorem_question_id", "")
        or ""
    )
    question_title = str(row.get("question_title", "") or "")
    semantic_alignment_constraints = _str_tuple(
        row.get("semantic_alignment_constraints", [])
    )
    semantic_alignment_blockers = _semantic_alignment_constraints_block_source_kernel(
        semantic_alignment_constraints
    )
    kernel_verified_source_theorem_proof_body_adapter_ids = _str_tuple(
        row.get("kernel_verified_source_theorem_proof_body_adapter_ids", [])
    )
    verified_source_theorem_proof_body_adapter_artifact_paths = _str_tuple(
        row.get("verified_source_theorem_proof_body_adapter_artifact_paths", [])
    )
    verified_source_theorem_proof_body_adapter_declarations = _str_tuple(
        row.get("verified_source_theorem_proof_body_adapter_declarations", [])
    )
    source_theorem_proof_body_adapter_kernel_verified = bool(
        row.get("source_theorem_proof_body_adapter_kernel_verified", False)
        or kernel_verified_source_theorem_proof_body_adapter_ids
    )
    source_theorem_proof_body_adapter_feedback_available = bool(
        row.get("source_theorem_proof_body_adapter_feedback_available", False)
        or source_theorem_proof_body_adapter_kernel_verified
        or verified_source_theorem_proof_body_adapter_artifact_paths
    )
    source_theorem_proof_body_adapter_context_boundary = str(
        row.get("source_theorem_proof_body_adapter_context_boundary", "") or ""
    )
    kernel_verified_source_to_bridge_premise_derivation_ids = _str_tuple(
        row.get("kernel_verified_source_to_bridge_premise_derivation_ids", [])
    )
    verified_source_to_bridge_premise_derivation_artifact_paths = _str_tuple(
        row.get("verified_source_to_bridge_premise_derivation_artifact_paths", [])
    )
    verified_source_to_bridge_premise_derivation_declarations = _str_tuple(
        row.get("verified_source_to_bridge_premise_derivation_declarations", [])
    )
    kernel_verified_theorem_reduction_closure_declarations = _str_tuple(
        row.get("kernel_verified_theorem_reduction_closure_declarations", [])
    )
    verified_theorem_reduction_closure_artifact_paths = _str_tuple(
        row.get("verified_theorem_reduction_closure_artifact_paths", [])
    )
    kernel_verified_theorem_reduction_closure_target_ids = _str_tuple(
        row.get("kernel_verified_theorem_reduction_closure_target_ids", [])
    )
    source_theorem_kernel_evidence_eligible = bool(
        row.get(
            "source_theorem_kernel_evidence_eligible",
            source_theorem_target_known and not semantic_alignment_blockers,
        )
    ) and not semantic_alignment_blockers
    target_identity_status = str(row.get("target_identity_status", "") or "")
    target_identity_errors = _str_tuple(row.get("target_identity_errors", []))
    source_theorem_target_identity_status = str(
        row.get("source_theorem_target_identity_status", "") or ""
    ) or _source_theorem_target_identity_status(
        source_theorem_target_known=source_theorem_target_known,
        target_identity_status=target_identity_status,
        target_identity_errors=target_identity_errors,
        expected_target_lean_declaration=expected_target_lean_declaration,
        target_lean_declaration=target_lean_declaration,
    )
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
    signature_typecheck_reached_proof_body = bool(
        already_repaired.get("signature_typecheck_reached_proof_body", False)
    )
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
        source_and_candidate_same_file = (
            source_path.exists()
            and candidate_artifact_path.exists()
            and source_path.resolve() == candidate_artifact_path.resolve()
        )
        if source_and_candidate_same_file or candidate_artifact_path.exists() and not overwrite:
            status = "EXACT_SOURCE_PROOF_BODY_CANDIDATE_REUSED"
        else:
            shutil.copyfile(source_path, candidate_artifact_path)
            status = "EXACT_SOURCE_PROOF_BODY_CANDIDATE_MATERIALIZED"
        try:
            source = candidate_artifact_path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"failed to read candidate artifact: {type(exc).__name__}: {exc}")
        if source:
            source, dependency_errors = (
                _materialize_verified_theorem_reduction_closure_dependencies(
                    source,
                    dependency_artifact_paths=(
                        verified_theorem_reduction_closure_artifact_paths
                    ),
                    dependency_declarations=(
                        kernel_verified_theorem_reduction_closure_declarations
                    ),
                    target_declaration=target_lean_declaration,
                )
            )
            errors.extend(dependency_errors)
            source, adapter_dependency_errors = (
                _materialize_verified_source_theorem_proof_body_adapter_dependencies(
                    source,
                    dependency_artifact_paths=(
                        verified_source_theorem_proof_body_adapter_artifact_paths
                    ),
                    dependency_declarations=(
                        verified_source_theorem_proof_body_adapter_declarations
                    ),
                    target_declaration=target_lean_declaration,
                )
            )
            errors.extend(adapter_dependency_errors)
            source, premise_derivation_dependency_errors = (
                _materialize_verified_source_to_bridge_premise_derivation_dependencies(
                    source,
                    dependency_artifact_paths=(
                        verified_source_to_bridge_premise_derivation_artifact_paths
                    ),
                    dependency_declarations=(
                        verified_source_to_bridge_premise_derivation_declarations
                    ),
                    target_declaration=target_lean_declaration,
                )
            )
            errors.extend(premise_derivation_dependency_errors)
            try:
                candidate_artifact_path.write_text(source, encoding="utf-8")
            except Exception as exc:
                errors.append(
                    "failed to write candidate artifact with verified dependency "
                    f"context: {type(exc).__name__}: {exc}"
                )
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
        candidate_source=source,
        target_declaration=target_lean_declaration,
        placeholder_symbols=placeholder_symbols,
        typeclass_blockers=typeclass_blockers,
        semantic_alignment_blockers=semantic_alignment_blockers,
    )
    if candidate_live_request and not live_goal_ready:
        errors.append("execution queue did not provide a ready live goal location")

    checked = False
    compiled = False
    returncode = -1
    diagnostics: tuple[str, ...] = ()
    proof_body_attempted = False
    proof_body_attempt_success = False
    proof_body_attempt_strategy = ""
    proof_body_attempt_summaries: tuple[str, ...] = ()
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
        if not compiled and _proof_body_attempts_should_run(
            diagnostics,
            placeholder_symbols=placeholder_symbols,
            typeclass_blockers=typeclass_blockers,
            semantic_alignment_blockers=semantic_alignment_blockers,
        ):
            (
                proof_body_attempted,
                proof_body_attempt_success,
                proof_body_attempt_strategy,
                proof_body_attempt_summaries,
                compiled,
                returncode,
                diagnostics,
                source,
            ) = _run_bounded_proof_body_attempts(
                source=source,
                declaration_name=target_lean_declaration,
                candidate_artifact_path=candidate_artifact_path,
                row=row,
                lean_command=lean_command,
                lean_project=lean_project,
                lean_timeout=lean_timeout,
                fallback_compiled=compiled,
                fallback_returncode=returncode,
                fallback_diagnostics=diagnostics,
            )
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

    formal_environment_closed = (
        not placeholder_symbols
        and not typeclass_blockers
        and not semantic_alignment_blockers
    )
    proof_body_goal_reached = _proof_body_goal_reached(
        diagnostics,
        exact_declaration_present=exact_declaration_present,
        local_lean_checked=checked,
        signature_typecheck_reached_proof_body=signature_typecheck_reached_proof_body,
        placeholder_symbols=placeholder_symbols,
        typeclass_blockers=typeclass_blockers,
    )
    artifact_kernel_verified = compiled and not forbidden_tokens_found and exact_declaration_present
    source_theorem_kernel_verified = (
        artifact_kernel_verified
        and formal_environment_closed
        and source_theorem_target_known
        and source_theorem_kernel_evidence_eligible
        and target_identity_status == "TARGET_DECLARATION_MATCHED"
        and not target_identity_errors
    )
    failure_classification = (
        ""
        if source_theorem_kernel_verified
        else _classify_failure(
            diagnostics,
            errors=errors,
            proof_body_attempt_summaries=proof_body_attempt_summaries,
            placeholder_symbols=placeholder_symbols,
            typeclass_blockers=typeclass_blockers,
            semantic_alignment_blockers=semantic_alignment_blockers,
            proof_body_goal_reached=proof_body_goal_reached,
            theorem_reduction_closure_declarations=(
                kernel_verified_theorem_reduction_closure_declarations
            ),
            verified_adapter_declarations=(
                verified_source_theorem_proof_body_adapter_declarations
            ),
        )
    )
    exact_goal_shape_obligation_ids = _exact_goal_shape_obligation_ids(
        source=source,
        diagnostics=diagnostics,
        proof_body_attempt_summaries=proof_body_attempt_summaries,
        verified_adapter_declarations=verified_source_theorem_proof_body_adapter_declarations,
        failure_classification=failure_classification,
    )
    exact_goal_shape_obligations = tuple(
        _exact_goal_shape_obligation_description(obligation_id)
        for obligation_id in exact_goal_shape_obligation_ids
    )
    proof_body_gate_status = _proof_body_gate_status(
        local_lean_checked=checked,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        artifact_kernel_verified=artifact_kernel_verified,
        proof_body_goal_reached=proof_body_goal_reached,
        placeholder_symbols=placeholder_symbols,
        typeclass_blockers=typeclass_blockers,
        semantic_alignment_blockers=semantic_alignment_blockers,
    )
    proof_body_goal_excerpt = _proof_body_goal_excerpt(
        diagnostics,
        candidate_live_request=candidate_live_request,
        proof_body_attempt_summaries=proof_body_attempt_summaries,
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
        source_theorem_target_identity_status=source_theorem_target_identity_status,
        source_theorem_target_provenance=source_theorem_target_provenance,
        semantic_alignment_constraints=semantic_alignment_constraints,
        semantic_alignment_blockers=semantic_alignment_blockers,
        source_theorem_proof_body_adapter_feedback_available=(
            source_theorem_proof_body_adapter_feedback_available
        ),
        source_theorem_proof_body_adapter_kernel_verified=(
            source_theorem_proof_body_adapter_kernel_verified
        ),
        kernel_verified_source_theorem_proof_body_adapter_ids=(
            kernel_verified_source_theorem_proof_body_adapter_ids
        ),
        verified_source_theorem_proof_body_adapter_artifact_paths=(
            verified_source_theorem_proof_body_adapter_artifact_paths
        ),
        verified_source_theorem_proof_body_adapter_declarations=(
            verified_source_theorem_proof_body_adapter_declarations
        ),
        source_theorem_proof_body_adapter_context_boundary=(
            source_theorem_proof_body_adapter_context_boundary
        ),
        kernel_verified_source_to_bridge_premise_derivation_ids=(
            kernel_verified_source_to_bridge_premise_derivation_ids
        ),
        verified_source_to_bridge_premise_derivation_artifact_paths=(
            verified_source_to_bridge_premise_derivation_artifact_paths
        ),
        verified_source_to_bridge_premise_derivation_declarations=(
            verified_source_to_bridge_premise_derivation_declarations
        ),
        kernel_verified_theorem_reduction_closure_declarations=(
            kernel_verified_theorem_reduction_closure_declarations
        ),
        verified_theorem_reduction_closure_artifact_paths=(
            verified_theorem_reduction_closure_artifact_paths
        ),
        kernel_verified_theorem_reduction_closure_target_ids=(
            kernel_verified_theorem_reduction_closure_target_ids
        ),
        target_identity_status=target_identity_status,
        target_identity_errors=target_identity_errors,
        source_candidate_artifact_path=source_candidate_artifact_path,
        candidate_artifact_path=candidate_artifact_path,
        status=status,
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        proof_body_attempted=proof_body_attempted,
        proof_body_goal_reached=proof_body_goal_reached,
        proof_body_goal_excerpt=proof_body_goal_excerpt,
        proof_body_gate_status=proof_body_gate_status,
        source_theorem_kernel_evidence_eligible=(
            source_theorem_kernel_evidence_eligible
        ),
        proof_body_attempt_source=str(
            candidate_live_request.get("proof_body_attempt_source", "")
            or row.get("proof_body_attempt_source", "")
            or ""
        ),
        proof_body_attempt_count=len(proof_body_attempt_summaries),
        proof_body_attempt_success=proof_body_attempt_success,
        proof_body_attempt_strategy=proof_body_attempt_strategy,
        proof_body_attempt_summaries=proof_body_attempt_summaries,
        exact_goal_shape_obligation_ids=exact_goal_shape_obligation_ids,
        exact_goal_shape_obligations=exact_goal_shape_obligations,
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
        question_id=question_id,
        question_title=question_title,
        target_theorem_name=target_theorem_name,
        target_lean_declaration=target_lean_declaration,
        expected_target_lean_declaration=expected_target_lean_declaration,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_identity_status=source_theorem_target_identity_status,
        source_theorem_target_provenance=source_theorem_target_provenance,
        semantic_alignment_constraints=semantic_alignment_constraints,
        semantic_alignment_blockers=semantic_alignment_blockers,
        source_theorem_proof_body_adapter_feedback_available=(
            source_theorem_proof_body_adapter_feedback_available
        ),
        source_theorem_proof_body_adapter_kernel_verified=(
            source_theorem_proof_body_adapter_kernel_verified
        ),
        kernel_verified_source_theorem_proof_body_adapter_ids=(
            kernel_verified_source_theorem_proof_body_adapter_ids
        ),
        verified_source_theorem_proof_body_adapter_artifact_paths=(
            verified_source_theorem_proof_body_adapter_artifact_paths
        ),
        verified_source_theorem_proof_body_adapter_declarations=(
            verified_source_theorem_proof_body_adapter_declarations
        ),
        source_theorem_proof_body_adapter_context_boundary=(
            source_theorem_proof_body_adapter_context_boundary
        ),
        kernel_verified_source_to_bridge_premise_derivation_ids=(
            kernel_verified_source_to_bridge_premise_derivation_ids
        ),
        verified_source_to_bridge_premise_derivation_artifact_paths=(
            verified_source_to_bridge_premise_derivation_artifact_paths
        ),
        verified_source_to_bridge_premise_derivation_declarations=(
            verified_source_to_bridge_premise_derivation_declarations
        ),
        kernel_verified_theorem_reduction_closure_declarations=(
            kernel_verified_theorem_reduction_closure_declarations
        ),
        verified_theorem_reduction_closure_artifact_paths=(
            verified_theorem_reduction_closure_artifact_paths
        ),
        kernel_verified_theorem_reduction_closure_target_ids=(
            kernel_verified_theorem_reduction_closure_target_ids
        ),
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
        proof_body_goal_reached=proof_body_goal_reached,
        proof_body_goal_excerpt=proof_body_goal_excerpt,
        proof_body_gate_status=proof_body_gate_status,
        local_lean_requested=local_lean,
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        source_theorem_kernel_evidence_eligible=(
            source_theorem_kernel_evidence_eligible
        ),
        proof_body_attempted=proof_body_attempted,
        proof_body_attempt_source=str(
            candidate_live_request.get("proof_body_attempt_source", "")
            or row.get("proof_body_attempt_source", "")
            or ""
        ),
        proof_body_attempt_count=len(proof_body_attempt_summaries),
        proof_body_attempt_success=proof_body_attempt_success,
        proof_body_attempt_strategy=proof_body_attempt_strategy,
        proof_body_attempt_summaries=proof_body_attempt_summaries,
        exact_goal_shape_obligation_ids=exact_goal_shape_obligation_ids,
        exact_goal_shape_obligations=exact_goal_shape_obligations,
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


def _proof_body_goal_reached(
    diagnostics: tuple[str, ...],
    *,
    exact_declaration_present: bool,
    local_lean_checked: bool,
    signature_typecheck_reached_proof_body: bool,
    placeholder_symbols: tuple[str, ...],
    typeclass_blockers: tuple[str, ...],
) -> bool:
    if signature_typecheck_reached_proof_body:
        return True
    if not local_lean_checked or not exact_declaration_present:
        return False
    if placeholder_symbols or typeclass_blockers:
        return False
    text = "\n".join(diagnostics).lower()
    if "unknown identifier" in text or "unknown constant" in text:
        return False
    if "failed to synthesize" in text or "type mismatch" in text:
        return False
    return "unsolved goals" in text


def _proof_body_goal_excerpt(
    diagnostics: tuple[str, ...],
    *,
    candidate_live_request: Mapping[str, object],
    proof_body_attempt_summaries: tuple[str, ...],
    max_lines: int = 8,
    max_len: int = 320,
) -> tuple[str, ...]:
    explicit = candidate_live_request.get("proof_body_goal_excerpt", ())
    explicit_lines: list[str] = []
    if isinstance(explicit, str):
        explicit_lines = [explicit]
    elif isinstance(explicit, (list, tuple)):
        explicit_lines = [str(value) for value in explicit if str(value).strip()]
    explicit_excerpt = tuple(
        _compact_diagnostic_line(line, max_len=max_len)
        for line in explicit_lines[:max_lines]
    )
    source_lines = [str(value) for value in (*diagnostics, *proof_body_attempt_summaries)]
    interesting_indices: set[int] = set()
    goal_indices: list[int] = []
    unsolved_indices: list[int] = []
    for index, line in enumerate(source_lines):
        text = line.strip()
        lowered = text.lower()
        if "⊢" in text:
            goal_indices.append(index)
        if "unsolved goals" in lowered:
            unsolved_indices.append(index)
        if (
            "⊢" in text
            or lowered.startswith("case ")
            or "unsolved goals" in lowered
        ):
            interesting_indices.update(
                range(max(0, index - 2), min(len(source_lines), index + 5))
            )
    if not interesting_indices:
        return explicit_excerpt
    if goal_indices:
        ordered_indices: list[int] = []
        if unsolved_indices:
            ordered_indices.append(unsolved_indices[-1])
        for index in goal_indices:
            ordered_indices.extend(
                range(max(0, index - 5), min(len(source_lines), index + 3))
            )
        ordered_indices.extend(sorted(interesting_indices))
    else:
        ordered_indices = sorted(interesting_indices)
    excerpt: list[str] = []
    seen: set[str] = set()
    for index in ordered_indices:
        line = _compact_diagnostic_line(source_lines[index], max_len=max_len)
        if not line or line in seen:
            continue
        seen.add(line)
        excerpt.append(line)
        if len(excerpt) >= max_lines:
            break
    diagnostic_excerpt = tuple(excerpt)
    if explicit_excerpt and any("⊢" in line for line in explicit_excerpt):
        return explicit_excerpt
    if diagnostic_excerpt and any("⊢" in line for line in diagnostic_excerpt):
        return diagnostic_excerpt
    return explicit_excerpt or diagnostic_excerpt


def _proof_body_gate_status(
    *,
    local_lean_checked: bool,
    source_theorem_kernel_verified: bool,
    artifact_kernel_verified: bool,
    proof_body_goal_reached: bool,
    placeholder_symbols: tuple[str, ...],
    typeclass_blockers: tuple[str, ...],
    semantic_alignment_blockers: tuple[str, ...],
) -> str:
    if source_theorem_kernel_verified:
        return "SOURCE_THEOREM_KERNEL_VERIFIED"
    if artifact_kernel_verified:
        return "ARTIFACT_KERNEL_VERIFIED_SOURCE_THEOREM_INELIGIBLE"
    if placeholder_symbols or typeclass_blockers:
        return "FORMAL_ENVIRONMENT_OPEN_BEFORE_PROOF_BODY"
    if proof_body_goal_reached and semantic_alignment_blockers:
        return "PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED"
    if semantic_alignment_blockers:
        return "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY"
    if proof_body_goal_reached:
        return "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    if local_lean_checked:
        return "PROOF_BODY_NOT_REACHED_LOCAL_LEAN_FAILED"
    return "PROOF_BODY_NOT_CHECKED"


def _proof_body_attempts_should_run(
    diagnostics: tuple[str, ...],
    *,
    placeholder_symbols: tuple[str, ...],
    typeclass_blockers: tuple[str, ...],
    semantic_alignment_blockers: tuple[str, ...] = (),
) -> bool:
    if placeholder_symbols or typeclass_blockers or semantic_alignment_blockers:
        return False
    text = "\n".join(diagnostics).lower()
    return "unsolved goals" in text


def _proof_body_attempts(row: Mapping[str, Any]) -> tuple[str, ...]:
    attempts: list[str] = []
    for value in row.get("proof_body_attempts", []) or []:
        text = str(value).strip()
        if text:
            attempts.append(text)
    attempts.extend(DEFAULT_PROOF_BODY_TACTIC_ATTEMPTS)
    cleaned: list[str] = []
    for tactic in attempts:
        if any(token in tactic for token in FORBIDDEN_ARTIFACT_TOKENS):
            continue
        cleaned.append(tactic)
    return tuple(dict.fromkeys(cleaned))


def _run_bounded_proof_body_attempts(
    *,
    source: str,
    declaration_name: str,
    candidate_artifact_path: Path,
    row: Mapping[str, Any],
    lean_command: tuple[str, ...],
    lean_project: Path | None,
    lean_timeout: int,
    fallback_compiled: bool,
    fallback_returncode: int,
    fallback_diagnostics: tuple[str, ...],
) -> tuple[bool, bool, str, tuple[str, ...], bool, int, tuple[str, ...], str]:
    summaries: list[str] = []
    for index, tactic in enumerate(_proof_body_attempts(row), start=1):
        attempted_source = _replace_exact_theorem_proof_body(
            source,
            declaration_name=declaration_name,
            tactic=tactic,
        )
        if not attempted_source:
            summaries.append(f"{index}:{tactic}:not_applied")
            continue
        attempt_path = candidate_artifact_path.with_name(
            f"{candidate_artifact_path.stem}.proof_body_attempt_{index}"
            f"{candidate_artifact_path.suffix or '.lean'}"
        )
        attempt_path.write_text(attempted_source, encoding="utf-8")
        compiled, returncode, diagnostics = _run_local_lean(
            attempt_path,
            lean_command=lean_command,
            lean_project=lean_project,
            timeout_s=lean_timeout,
        )
        summary = f"{index}:{tactic}:returncode={returncode}:compiled={compiled}"
        if diagnostics:
            kind = _diagnostic_failure_kind(diagnostics)
            brief = _diagnostic_brief(diagnostics)
            if kind:
                summary += f":diagnostic_kind={kind}"
            if brief:
                summary += ":diagnostic=" + brief
        summaries.append(summary)
        if compiled:
            candidate_artifact_path.write_text(attempted_source, encoding="utf-8")
            return (
                True,
                True,
                tactic,
                tuple(summaries),
                compiled,
                returncode,
                diagnostics,
                attempted_source,
            )
    return (
        bool(summaries),
        False,
        "",
        tuple(summaries),
        fallback_compiled,
        fallback_returncode,
        fallback_diagnostics,
        source,
    )


def _diagnostic_failure_kind(diagnostics: tuple[str, ...]) -> str:
    text = "\n".join(diagnostics).lower()
    if "unknown identifier" in text:
        return "unknown_identifier"
    if "unknown constant" in text:
        return "unknown_constant"
    if "unknown module prefix" in text or "invalid 'import' command" in text:
        return "missing_import"
    if "failed to synthesize" in text:
        return "instance_missing"
    if "type mismatch" in text:
        return "type_mismatch"
    if "function expected" in text:
        return "function_expected"
    if "unsolved goals" in text:
        return "unsolved_goals"
    if "timed out" in text or "timeout" in text:
        return "timeout"
    return ""


def _diagnostic_brief(diagnostics: tuple[str, ...], *, max_len: int = 260) -> str:
    for needle in (
        "Unknown identifier",
        "unknown identifier",
        "Unknown constant",
        "unknown constant",
        "unknown module prefix",
        "invalid 'import' command",
        "failed to synthesize",
        "type mismatch",
        "function expected",
        "unsolved goals",
        "timed out",
        "timeout",
    ):
        for line in diagnostics:
            if needle.lower() in line.lower():
                return _compact_diagnostic_line(line, max_len=max_len)
    return _compact_diagnostic_line(diagnostics[0], max_len=max_len) if diagnostics else ""


def _compact_diagnostic_line(line: str, *, max_len: int) -> str:
    cleaned = " ".join(str(line).split())
    if len(cleaned) <= max_len:
        return cleaned
    keep_tail = max_len - 20
    if keep_tail <= 0:
        return cleaned[:max_len]
    return cleaned[:12] + "..." + cleaned[-keep_tail:]


def _replace_exact_theorem_proof_body(
    source: str,
    *,
    declaration_name: str,
    tactic: str,
) -> str:
    if not source or not declaration_name or not tactic.strip():
        return ""
    match = re.search(r"\btheorem\s+" + re.escape(declaration_name) + r"\b", source)
    if match is None:
        return ""
    theorem_start = match.start()
    proof_match = re.search(r":=\s*by\b", source[theorem_start:])
    if proof_match is None:
        return ""
    proof_start = theorem_start + proof_match.start()
    proof_body_start = theorem_start + proof_match.end()
    trailing = source[proof_body_start:]
    if re.search(r"\n(?:theorem|lemma|def|structure|class|inductive)\s+", trailing):
        return ""
    prefix = source[:proof_start]
    return prefix.rstrip() + " := by\n  " + tactic.strip() + "\n"


def _materialize_verified_theorem_reduction_closure_dependencies(
    source: str,
    *,
    dependency_artifact_paths: tuple[str, ...],
    dependency_declarations: tuple[str, ...],
    target_declaration: str,
) -> tuple[str, list[str]]:
    return _materialize_verified_dependency_declarations(
        source,
        dependency_artifact_paths=dependency_artifact_paths,
        dependency_declarations=dependency_declarations,
        target_declaration=target_declaration,
        dependency_label="theorem-reduction closure",
        block_comment=(
            "Materialized kernel-verified theorem-reduction closure dependency for\n"
            "exact source-theorem proof-body repair. This helper is context for the\n"
            "candidate proof only; the source theorem is proved only if the exact\n"
            "target declaration below passes local Lean/AXLE."
        ),
    )


def _materialize_verified_source_theorem_proof_body_adapter_dependencies(
    source: str,
    *,
    dependency_artifact_paths: tuple[str, ...],
    dependency_declarations: tuple[str, ...],
    target_declaration: str,
) -> tuple[str, list[str]]:
    return _materialize_verified_dependency_declarations(
        source,
        dependency_artifact_paths=dependency_artifact_paths,
        dependency_declarations=dependency_declarations,
        target_declaration=target_declaration,
        dependency_label="source-theorem proof-body adapter",
        block_comment=(
            "Materialized kernel-verified source-theorem proof-body adapter for\n"
            "exact source-theorem proof-body repair. This adapter is context for\n"
            "the candidate proof only; the source theorem is proved only if the\n"
            "exact target declaration below passes local Lean/AXLE."
        ),
    )


def _materialize_verified_source_to_bridge_premise_derivation_dependencies(
    source: str,
    *,
    dependency_artifact_paths: tuple[str, ...],
    dependency_declarations: tuple[str, ...],
    target_declaration: str,
) -> tuple[str, list[str]]:
    return _materialize_verified_dependency_declarations(
        source,
        dependency_artifact_paths=dependency_artifact_paths,
        dependency_declarations=dependency_declarations,
        target_declaration=target_declaration,
        dependency_label="source-to-bridge premise derivation",
        block_comment=(
            "Materialized kernel-verified source-to-bridge premise derivation for\n"
            "exact source-theorem proof-body repair. This premise derivation is\n"
            "context for the candidate proof only; the source theorem is proved\n"
            "only if the exact target declaration below passes local Lean/AXLE."
        ),
    )


def _materialize_verified_dependency_declarations(
    source: str,
    *,
    dependency_artifact_paths: tuple[str, ...],
    dependency_declarations: tuple[str, ...],
    target_declaration: str,
    dependency_label: str,
    block_comment: str,
) -> tuple[str, list[str]]:
    if not source or not dependency_artifact_paths or not dependency_declarations:
        return source, []
    imports: list[str] = []
    opens: list[str] = []
    blocks: list[str] = []
    errors: list[str] = []
    n_readable_artifacts = 0
    already_present = {
        declaration
        for declaration in dependency_declarations
        if _has_exact_declaration(source, declaration)
    }
    for artifact_path in dependency_artifact_paths:
        path = Path(artifact_path)
        try:
            artifact_source = path.read_text(encoding="utf-8")
        except Exception:
            continue
        n_readable_artifacts += 1
        imports.extend(_lean_import_lines(artifact_source))
        opens.extend(_lean_open_lines(artifact_source))
        for declaration in dependency_declarations:
            if declaration in already_present:
                continue
            block = _extract_lean_declaration_block(artifact_source, declaration)
            if not block:
                continue
            forbidden = [
                token for token in FORBIDDEN_ARTIFACT_TOKENS if token in block
            ]
            if forbidden:
                errors.append(
                    "verified "
                    + dependency_label
                    + " declaration contains "
                    "forbidden tokens and was not materialized: "
                    + declaration
                    + " ("
                    + ", ".join(forbidden)
                    + ")"
                )
                continue
            blocks.append(block)
            already_present.add(declaration)
    missing = [
        declaration
        for declaration in dependency_declarations
        if declaration not in already_present
    ]
    if missing and n_readable_artifacts:
        errors.append(
            "verified "
            + dependency_label
            + " declarations not found in "
            "provided artifacts: "
            + ", ".join(missing)
        )
    if not blocks:
        return _prepend_lean_imports(source, imports), errors
    dependency_block = (
        "\n\n/-\n"
        + block_comment.rstrip()
        + "\n"
        "-/\n"
        + "\n".join(dict.fromkeys(opens))
        + ("\n\n" if opens else "")
        + "\n\n".join(blocks).strip()
        + "\n"
    )
    source_with_imports = _prepend_lean_imports(source, imports)
    return (
        _insert_before_lean_declaration(
            source_with_imports,
            declaration_name=target_declaration,
            insertion=dependency_block,
        ),
        errors,
    )


def _lean_import_lines(source: str) -> list[str]:
    return [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith("import ")
    ]


def _lean_open_lines(source: str) -> list[str]:
    return [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith("open ")
    ]


def _prepend_lean_imports(source: str, imports: list[str]) -> str:
    if not imports:
        return source
    existing = {
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith("import ")
    }
    missing = [line for line in dict.fromkeys(imports) if line not in existing]
    if not missing:
        return source
    return "\n".join(missing) + "\n" + source


def _extract_lean_declaration_block(source: str, declaration_name: str) -> str:
    if not source or not declaration_name:
        return ""
    declaration_head = (
        r"(?m)^[ \t]*(?:noncomputable[ \t]+)?(?:private[ \t]+)?"
        r"(?:theorem|lemma|def|abbrev)\s+"
        + re.escape(declaration_name)
        + r"\b"
    )
    match = re.search(declaration_head, source)
    if match is None:
        return ""
    rest = source[match.start() :]
    next_decl = re.search(
        r"(?m)^[ \t]*(?:noncomputable[ \t]+)?(?:private[ \t]+)?"
        r"(?:theorem|lemma|def|abbrev|structure|class|inductive|namespace|end)\b",
        rest[1:],
    )
    end = match.start() + 1 + next_decl.start() if next_decl else len(source)
    return source[match.start() : end].strip()


def _insert_before_lean_declaration(
    source: str,
    *,
    declaration_name: str,
    insertion: str,
) -> str:
    if not source or not declaration_name or not insertion.strip():
        return source
    match = re.search(
        r"(?m)^[ \t]*(?:theorem|lemma)\s+" + re.escape(declaration_name) + r"\b",
        source,
    )
    if match is None:
        return source
    return source[: match.start()].rstrip() + insertion + "\n\n" + source[match.start() :]


def _candidate_live_proof_state_request(
    *,
    row: Mapping[str, Any],
    candidate_artifact_path: Path,
    candidate_source: str,
    target_declaration: str,
    placeholder_symbols: tuple[str, ...],
    typeclass_blockers: tuple[str, ...],
    semantic_alignment_blockers: tuple[str, ...] = (),
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
    target_location = _lean_declaration_proof_body_location(
        candidate_source,
        declaration_name=target_declaration,
        candidate_artifact_path=candidate_artifact_path,
    )
    if target_location:
        candidate_request.update(target_location)
    for key in (
        "kernel_verified_source_theorem_proof_body_adapter_ids",
        "verified_source_theorem_proof_body_adapter_artifact_paths",
        "verified_source_theorem_proof_body_adapter_declarations",
        "source_theorem_proof_body_adapter_context_boundary",
        "source_theorem_proof_body_adapter_feedback_available",
        "source_theorem_proof_body_adapter_kernel_verified",
        "kernel_verified_source_to_bridge_premise_derivation_ids",
        "verified_source_to_bridge_premise_derivation_artifact_paths",
        "verified_source_to_bridge_premise_derivation_declarations",
        "kernel_verified_theorem_reduction_closure_declarations",
        "verified_theorem_reduction_closure_artifact_paths",
        "kernel_verified_theorem_reduction_closure_target_ids",
    ):
        if key in row:
            candidate_request[key] = row.get(key)
    proof_body_attempts = list(_proof_body_attempts(row))
    formal_environment_open = bool(
        placeholder_symbols or typeclass_blockers or semantic_alignment_blockers
    )
    calls = []
    for call in request.get("mcp_tool_calls", []) or []:
        if not isinstance(call, Mapping):
            continue
        cloned = dict(call)
        if formal_environment_open and cloned.get("tool") == "lean_multi_attempt":
            continue
        args = dict(cloned.get("arguments", {}) or {})
        args["file"] = str(candidate_artifact_path)
        if target_location:
            args["line"] = target_location["target_lean_line"]
            args["column"] = target_location["target_lean_column"]
            args["declaration"] = target_location["target_lean_declaration"]
        if cloned.get("tool") == "lean_multi_attempt":
            args["snippets"] = proof_body_attempts
        cloned["arguments"] = args
        calls.append(cloned)
    candidate_request["mcp_tool_calls"] = calls
    if formal_environment_open:
        candidate_request["proof_body_attempts"] = []
        candidate_request["proof_body_attempt_source"] = (
            "formal_environment_open_skip_tactic_attempts"
            if not semantic_alignment_blockers
            else "semantic_alignment_open_skip_tactic_attempts"
        )
    else:
        candidate_request["proof_body_attempts"] = proof_body_attempts
        candidate_request["proof_body_attempt_source"] = str(
            row.get("proof_body_attempt_source", "")
            or candidate_request.get("proof_body_attempt_source", "")
            or "runtime_exact_source_proof_body_repair_work_order"
        )
    candidate_request["proof_evidence_status"] = "LIVE_PROOF_STATE_REQUEST_NOT_PROOF_EVIDENCE"
    return candidate_request


def _lean_declaration_proof_body_location(
    source: str,
    *,
    declaration_name: str,
    candidate_artifact_path: Path,
) -> dict[str, object]:
    if not source or not declaration_name:
        return {}
    declaration_head = (
        r"(?m)^[ \t]*(?:noncomputable[ \t]+)?(?:private[ \t]+)?"
        r"(?:theorem|lemma)\s+"
        + re.escape(declaration_name)
        + r"\b"
    )
    match = re.search(declaration_head, source)
    if match is None:
        return {}
    prefix_line = source[: match.start()].count("\n")
    rest = source[match.start() :]
    next_decl = re.search(
        r"(?m)^[ \t]*(?:noncomputable[ \t]+)?(?:private[ \t]+)?"
        r"(?:theorem|lemma|def|abbrev|structure|class|inductive|namespace|end)\b",
        rest[1:],
    )
    block = rest[: 1 + next_decl.start()] if next_decl else rest
    block_lines = block.splitlines()
    proof_line = 0
    for offset, line in enumerate(block_lines):
        if line.strip() != "-- AI_STAT_EVOLVE_BLOCK_START":
            continue
        for inner_offset, candidate in enumerate(block_lines[offset + 1 :], start=1):
            stripped = candidate.strip()
            if stripped and not stripped.startswith("--"):
                proof_line = prefix_line + offset + inner_offset + 1
                break
        if proof_line:
            break
    if not proof_line:
        for offset, line in enumerate(block_lines):
            if ":= by" in line:
                proof_line = prefix_line + offset + 2
                break
    if not proof_line:
        proof_line = prefix_line + 1
    return {
        "target_lean_file": str(candidate_artifact_path),
        "target_lean_line": proof_line,
        "target_lean_column": 3,
        "target_lean_declaration": declaration_name,
    }


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
    source_theorem_target_identity_status: str,
    source_theorem_target_provenance: dict[str, object],
    semantic_alignment_constraints: tuple[str, ...],
    semantic_alignment_blockers: tuple[str, ...],
    source_theorem_proof_body_adapter_feedback_available: bool,
    source_theorem_proof_body_adapter_kernel_verified: bool,
    kernel_verified_source_theorem_proof_body_adapter_ids: tuple[str, ...],
    verified_source_theorem_proof_body_adapter_artifact_paths: tuple[str, ...],
    verified_source_theorem_proof_body_adapter_declarations: tuple[str, ...],
    source_theorem_proof_body_adapter_context_boundary: str,
    kernel_verified_source_to_bridge_premise_derivation_ids: tuple[str, ...],
    verified_source_to_bridge_premise_derivation_artifact_paths: tuple[str, ...],
    verified_source_to_bridge_premise_derivation_declarations: tuple[str, ...],
    kernel_verified_theorem_reduction_closure_declarations: tuple[str, ...],
    verified_theorem_reduction_closure_artifact_paths: tuple[str, ...],
    kernel_verified_theorem_reduction_closure_target_ids: tuple[str, ...],
    target_identity_status: str,
    target_identity_errors: tuple[str, ...],
    source_candidate_artifact_path: str,
    candidate_artifact_path: Path,
    status: str,
    local_lean_checked: bool,
    local_lean_compiled: bool,
    artifact_kernel_verified: bool,
    source_theorem_kernel_verified: bool,
    proof_body_attempted: bool,
    proof_body_goal_reached: bool,
    proof_body_goal_excerpt: tuple[str, ...],
    proof_body_gate_status: str,
    source_theorem_kernel_evidence_eligible: bool,
    proof_body_attempt_source: str,
    proof_body_attempt_count: int,
    proof_body_attempt_success: bool,
    proof_body_attempt_strategy: str,
    proof_body_attempt_summaries: tuple[str, ...],
    exact_goal_shape_obligation_ids: tuple[str, ...],
    exact_goal_shape_obligations: tuple[str, ...],
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
            "source_theorem_target_identity_status": (
                source_theorem_target_identity_status
            ),
            "source_theorem_target_provenance": source_theorem_target_provenance,
            "semantic_alignment_constraints": semantic_alignment_constraints,
            "semantic_alignment_blockers": semantic_alignment_blockers,
            "source_theorem_proof_body_adapter_feedback_available": (
                source_theorem_proof_body_adapter_feedback_available
            ),
            "source_theorem_proof_body_adapter_kernel_verified": (
                source_theorem_proof_body_adapter_kernel_verified
            ),
            "kernel_verified_source_theorem_proof_body_adapter_ids": (
                kernel_verified_source_theorem_proof_body_adapter_ids
            ),
            "verified_source_theorem_proof_body_adapter_artifact_paths": (
                verified_source_theorem_proof_body_adapter_artifact_paths
            ),
            "verified_source_theorem_proof_body_adapter_declarations": (
                verified_source_theorem_proof_body_adapter_declarations
            ),
            "source_theorem_proof_body_adapter_context_boundary": (
                source_theorem_proof_body_adapter_context_boundary
            ),
            "kernel_verified_source_to_bridge_premise_derivation_ids": (
                kernel_verified_source_to_bridge_premise_derivation_ids
            ),
            "verified_source_to_bridge_premise_derivation_artifact_paths": (
                verified_source_to_bridge_premise_derivation_artifact_paths
            ),
            "verified_source_to_bridge_premise_derivation_declarations": (
                verified_source_to_bridge_premise_derivation_declarations
            ),
            "kernel_verified_theorem_reduction_closure_declarations": (
                kernel_verified_theorem_reduction_closure_declarations
            ),
            "verified_theorem_reduction_closure_artifact_paths": (
                verified_theorem_reduction_closure_artifact_paths
            ),
            "kernel_verified_theorem_reduction_closure_target_ids": (
                kernel_verified_theorem_reduction_closure_target_ids
            ),
            "target_identity_status": target_identity_status,
            "target_identity_errors": target_identity_errors,
            "source_candidate_artifact_path": source_candidate_artifact_path,
            "candidate_artifact_path": str(candidate_artifact_path),
            "execution_status": status,
            "local_lean_checked": local_lean_checked,
            "local_lean_compiled": local_lean_compiled,
            "artifact_kernel_verified": artifact_kernel_verified,
            "source_theorem_kernel_verified": source_theorem_kernel_verified,
            "proof_body_attempted": proof_body_attempted,
            "proof_body_goal_reached": proof_body_goal_reached,
            "proof_body_goal_excerpt": proof_body_goal_excerpt,
            "proof_body_gate_status": proof_body_gate_status,
            "source_theorem_kernel_evidence_eligible": (
                source_theorem_kernel_evidence_eligible
            ),
            "proof_body_attempt_source": proof_body_attempt_source,
            "proof_body_attempt_count": proof_body_attempt_count,
            "proof_body_attempt_success": proof_body_attempt_success,
            "proof_body_attempt_strategy": proof_body_attempt_strategy,
            "proof_body_attempt_summaries": proof_body_attempt_summaries,
            "exact_goal_shape_obligation_ids": exact_goal_shape_obligation_ids,
            "exact_goal_shape_obligations": exact_goal_shape_obligations,
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
        trigger = _runtime_learning_trigger(row)
        learning_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "question_id": row.question_id,
                "question_title": row.question_title,
                "learning_task": "exact_source_theorem_proof_body_execution_feedback",
                "target_theorem_name": row.target_theorem_name,
                "target_lean_declaration": row.target_lean_declaration,
                "expected_target_lean_declaration": row.expected_target_lean_declaration,
                "source_theorem_target_known": row.source_theorem_target_known,
                "source_theorem_target_identity_status": (
                    row.source_theorem_target_identity_status
                ),
                "source_theorem_target_provenance": row.source_theorem_target_provenance,
                "semantic_alignment_constraints": list(
                    row.semantic_alignment_constraints
                ),
                "semantic_alignment_blockers": list(row.semantic_alignment_blockers),
                "source_theorem_proof_body_adapter_feedback_available": (
                    row.source_theorem_proof_body_adapter_feedback_available
                ),
                "source_theorem_proof_body_adapter_kernel_verified": (
                    row.source_theorem_proof_body_adapter_kernel_verified
                ),
                "kernel_verified_source_theorem_proof_body_adapter_ids": list(
                    row.kernel_verified_source_theorem_proof_body_adapter_ids
                ),
                "verified_source_theorem_proof_body_adapter_artifact_paths": list(
                    row.verified_source_theorem_proof_body_adapter_artifact_paths
                ),
                "verified_source_theorem_proof_body_adapter_declarations": list(
                    row.verified_source_theorem_proof_body_adapter_declarations
                ),
                "source_theorem_proof_body_adapter_context_boundary": (
                    row.source_theorem_proof_body_adapter_context_boundary
                ),
                "kernel_verified_source_to_bridge_premise_derivation_ids": list(
                    row.kernel_verified_source_to_bridge_premise_derivation_ids
                ),
                "verified_source_to_bridge_premise_derivation_artifact_paths": list(
                    row.verified_source_to_bridge_premise_derivation_artifact_paths
                ),
                "verified_source_to_bridge_premise_derivation_declarations": list(
                    row.verified_source_to_bridge_premise_derivation_declarations
                ),
                "kernel_verified_theorem_reduction_closure_declarations": list(
                    row.kernel_verified_theorem_reduction_closure_declarations
                ),
                "verified_theorem_reduction_closure_artifact_paths": list(
                    row.verified_theorem_reduction_closure_artifact_paths
                ),
                "kernel_verified_theorem_reduction_closure_target_ids": list(
                    row.kernel_verified_theorem_reduction_closure_target_ids
                ),
                "target_identity_status": row.target_identity_status,
                "target_identity_errors": list(row.target_identity_errors),
                "source_work_order_id": row.source_work_order_id,
                "execution_queue_id": row.execution_queue_id,
                "execution_result_id": row.execution_result_id,
                "execution_status": row.execution_status,
                "failure_classification": row.failure_classification,
                "runtime_queue_status": _runtime_learning_queue_status(row),
                "source_theorem_kernel_evidence_eligible": (
                    row.source_theorem_kernel_evidence_eligible
                ),
                "artifact_kernel_verified": row.artifact_kernel_verified,
                "source_theorem_kernel_verified": row.source_theorem_kernel_verified,
                "local_lean_requested": row.local_lean_requested,
                "local_lean_checked": row.local_lean_checked,
                "local_lean_compiled": row.local_lean_compiled,
                "returncode": row.returncode,
                "proof_body_attempt_source": row.proof_body_attempt_source,
                "proof_body_attempted": row.proof_body_attempted,
                "proof_body_attempt_count": row.proof_body_attempt_count,
                "proof_body_attempt_strategy": row.proof_body_attempt_strategy,
                "proof_body_attempt_summaries": list(
                    row.proof_body_attempt_summaries
                ),
                "exact_goal_shape_obligation_ids": list(
                    row.exact_goal_shape_obligation_ids
                ),
                "exact_goal_shape_obligations": list(
                    row.exact_goal_shape_obligations
                ),
                "proof_body_goal_reached": row.proof_body_goal_reached,
                "proof_body_goal_excerpt": list(row.proof_body_goal_excerpt),
                "proof_body_gate_status": row.proof_body_gate_status,
                "proof_body_attempt_success": row.proof_body_attempt_success,
                "diagnostics": list(row.diagnostics),
                "recommended_next_action": _runtime_learning_recommended_next_action(
                    row
                ),
                "target_behavior": _runtime_learning_target_behavior(row),
                "acceptance_gate": _runtime_learning_acceptance_gate(row),
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
        "n_source_theorem_target_unpromoted_rows": sum(
            1
            for row in rows
            if row.source_theorem_target_identity_status
            == "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
        ),
        "n_semantic_alignment_constraint_rows": sum(
            1 for row in rows if row.semantic_alignment_constraints
        ),
        "n_semantic_alignment_blocker_rows": sum(
            1 for row in rows if row.semantic_alignment_blockers
        ),
        "n_source_theorem_proof_body_adapter_context_rows": sum(
            1
            for row in rows
            if row.source_theorem_proof_body_adapter_feedback_available
            or row.source_theorem_proof_body_adapter_kernel_verified
            or row.kernel_verified_source_theorem_proof_body_adapter_ids
        ),
        "n_source_theorem_proof_body_adapter_kernel_verified_context_rows": sum(
            1 for row in rows if row.source_theorem_proof_body_adapter_kernel_verified
        ),
        "n_kernel_verified_source_to_bridge_premise_derivation_context_rows": sum(
            1
            for row in rows
            if row.kernel_verified_source_to_bridge_premise_derivation_ids
            or row.verified_source_to_bridge_premise_derivation_artifact_paths
            or row.verified_source_to_bridge_premise_derivation_declarations
        ),
        "kernel_verified_source_to_bridge_premise_derivation_ids": list(
            dict.fromkeys(
                premise_id
                for row in rows
                for premise_id in row.kernel_verified_source_to_bridge_premise_derivation_ids
            )
        ),
        "n_proof_body_goal_reached": sum(1 for row in rows if row.proof_body_goal_reached),
        "n_proof_body_goal_excerpt_rows": sum(
            1 for row in rows if row.proof_body_goal_excerpt
        ),
        "first_proof_body_goal_excerpt": next(
            (list(row.proof_body_goal_excerpt) for row in rows if row.proof_body_goal_excerpt),
            [],
        ),
        "n_proof_body_goal_reached_with_semantic_blockers": sum(
            1 for row in rows if row.proof_body_goal_reached and row.semantic_alignment_blockers
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
        "n_source_theorem_target_unpromoted_rows": manifest[
            "n_source_theorem_target_unpromoted_rows"
        ],
        "n_semantic_alignment_constraint_rows": manifest[
            "n_semantic_alignment_constraint_rows"
        ],
        "n_semantic_alignment_blocker_rows": manifest[
            "n_semantic_alignment_blocker_rows"
        ],
        "n_source_theorem_proof_body_adapter_context_rows": manifest[
            "n_source_theorem_proof_body_adapter_context_rows"
        ],
        "n_source_theorem_proof_body_adapter_kernel_verified_context_rows": manifest[
            "n_source_theorem_proof_body_adapter_kernel_verified_context_rows"
        ],
        "n_proof_body_goal_reached": manifest["n_proof_body_goal_reached"],
        "n_proof_body_goal_excerpt_rows": manifest[
            "n_proof_body_goal_excerpt_rows"
        ],
        "first_proof_body_goal_excerpt": manifest[
            "first_proof_body_goal_excerpt"
        ],
        "n_proof_body_goal_reached_with_semantic_blockers": manifest[
            "n_proof_body_goal_reached_with_semantic_blockers"
        ],
        "source_theorem_route_ids": manifest["source_theorem_route_ids"],
        "proof_evidence_status": manifest["proof_evidence_status"],
    }


def _runtime_learning_queue_status(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> str:
    if row.source_theorem_kernel_verified:
        return "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
    if row.proof_body_goal_reached and row.semantic_alignment_blockers:
        return "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR"
    if row.semantic_alignment_blockers:
        return "PENDING_EXACT_SEMANTIC_DEFINITION_REVIEW"
    if row.artifact_kernel_verified:
        return "PENDING_SOURCE_THEOREM_ENVIRONMENT_CLOSURE"
    if row.failure_classification == "proof_body_dependency_context_missing":
        return "PENDING_EXACT_SOURCE_THEOREM_PROOF_DEPENDENCY_CONTEXT"
    if (
        row.failure_classification
        == "proof_body_reduction_closure_adapter_instantiation_missing"
    ):
        return "PENDING_SOURCE_THEOREM_PROOF_BODY_ADAPTER_INSTANTIATION"
    if row.failure_classification == "proof_body_verified_adapter_context_insufficient":
        return "PENDING_EXACT_SOURCE_THEOREM_PROOF_BODY_REPAIR_WITH_VERIFIED_ADAPTER"
    if row.failure_classification == "proof_body_incomplete":
        return "PENDING_EXACT_SOURCE_THEOREM_PROOF_BODY_REPAIR"
    if row.local_lean_checked and not row.local_lean_compiled:
        return "PENDING_EXACT_SOURCE_THEOREM_LOCAL_LEAN_REPAIR"
    if row.local_lean_requested:
        return "PENDING_EXACT_SOURCE_THEOREM_LOCAL_LEAN_RERUN"
    return "PENDING_EXACT_SOURCE_THEOREM_PROOF_BODY_LOCAL_LEAN"


def _runtime_learning_recommended_next_action(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> str:
    if row.source_theorem_kernel_verified:
        return "Record source_theorem_kernel_verified=true and stop proof-body repair."
    if row.proof_body_goal_reached and row.semantic_alignment_blockers:
        return (
            "Review or replace exact semantic definitions before retrying the exact "
            "source theorem proof body."
        )
    if row.semantic_alignment_blockers:
        return (
            "Route to exact semantic-definition source lookup/review; do not spend "
            "ProofEngineer budget on the proof body yet."
        )
    if row.failure_classification == "proof_body_dependency_context_missing":
        return (
            "Route to ProofEngineer with the reached Lean goal and the missing proof "
            "dependency diagnostics. Import, inline, or materialize the verified "
            "reduction/bridge lemmas in the exact source-theorem candidate before "
            "retrying tactic search."
        )
    if (
        row.failure_classification
        == "proof_body_reduction_closure_adapter_instantiation_missing"
    ):
        return (
            "Route to ProofEngineer adapter synthesis: the verified theorem-reduction "
            "closure declaration is available, but direct exact/simpa attempts do not "
            "instantiate it against the exact source theorem. Build a source-to-closure "
            "adapter that supplies covered/BadRanks/rank/alpha_total assumptions and "
            "bridges ENNReal/real-valued coverage before retrying the exact theorem."
        )
    if row.failure_classification == "proof_body_verified_adapter_context_insufficient":
        return (
            "Route to ProofEngineer with the verified adapter materialized: the "
            "adapter is available, but its conclusion still does not close the exact "
            "source theorem. Strengthen the proof body or adapter to bridge the exact "
            "goal shape, including real/ENNReal conversion and any missing two-sided "
            "coverage component, before rerunning local Lean."
        )
    if row.failure_classification == "proof_body_incomplete":
        return (
            "Route to ProofEngineer with the reached Lean goal, failed tactic "
            "attempts, and diagnostics; the formal environment is closed enough "
            "for proof-body repair, but the source theorem is still unproved."
        )
    if row.artifact_kernel_verified:
        return (
            "Close remaining source-theorem evidence gates before promotion; an "
            "artifact kernel check alone is not exact source theorem proof."
        )
    if row.local_lean_checked and not row.local_lean_compiled:
        return "Classify the Lean failure and rerun local Lean after repairing the candidate."
    return "Run local Lean/AXLE on the exact source theorem candidate before promotion."


def _runtime_learning_trigger(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> str:
    if row.source_theorem_kernel_verified:
        return "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
    if row.proof_body_goal_reached and (
        row.semantic_alignment_blockers
        or row.failure_classification
        == "proof_body_reached_semantic_alignment_unreviewed"
    ):
        return "EXACT_SOURCE_PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED"
    if row.semantic_alignment_blockers:
        return "EXACT_SOURCE_SEMANTIC_ALIGNMENT_REVIEW_REQUIRED"
    if row.artifact_kernel_verified:
        return "EXACT_SOURCE_PROOF_BODY_ARTIFACT_KERNEL_ENVIRONMENT_OPEN"
    if row.failure_classification == "proof_body_dependency_context_missing":
        return "EXACT_SOURCE_PROOF_BODY_DEPENDENCY_CONTEXT_MISSING"
    if (
        row.failure_classification
        == "proof_body_reduction_closure_adapter_instantiation_missing"
    ):
        return "EXACT_SOURCE_PROOF_BODY_REDUCTION_CLOSURE_ADAPTER_REQUIRED"
    if row.failure_classification == "proof_body_verified_adapter_context_insufficient":
        return "EXACT_SOURCE_PROOF_BODY_VERIFIED_ADAPTER_CONTEXT_INSUFFICIENT"
    if row.failure_classification == "proof_body_incomplete":
        return "EXACT_SOURCE_PROOF_BODY_REACHED_PROOF_INCOMPLETE"
    if row.local_lean_checked:
        return "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    return "EXACT_SOURCE_PROOF_BODY_CANDIDATE_MATERIALIZED"


def _runtime_learning_target_behavior(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> str:
    if row.semantic_alignment_blockers:
        if row.proof_body_goal_reached:
            return (
                "Route this feedback to exact semantic-definition source review/promotion. "
                "The exact theorem proof body is reachable, but proof-body search remains "
                "blocked until synthesized semantics are reviewed or replaced by source-faithful "
                "Lean definitions."
            )
        return (
            "Route this feedback to exact semantic-definition source lookup/review "
            "before any further proof-body search. The candidate declaration may match, "
            "but the source-theorem semantics remain unreviewed."
        )
    if row.failure_classification == "proof_body_dependency_context_missing":
        return (
            "Use this as ProofEngineer dependency-context feedback. The exact theorem "
            "goal is reachable, but attempted proof terms referenced unavailable "
            "reduction/bridge declarations; provide the verified dependency context "
            "before spending more tactic-search budget."
        )
    if (
        row.failure_classification
        == "proof_body_reduction_closure_adapter_instantiation_missing"
    ):
        return (
            "Use this as ProofEngineer adapter feedback. The exact theorem goal is "
            "reachable and verified closure dependencies are materialized, but the "
            "closure theorem does not directly match the exact source theorem. The "
            "next artifact should be a checked adapter/instantiation layer, not "
            "another blind direct tactic attempt."
        )
    if row.failure_classification == "proof_body_verified_adapter_context_insufficient":
        return (
            "Use this as ProofEngineer post-adapter feedback. The exact theorem goal "
            "is reachable and a kernel-verified source-to-bridge adapter is present, "
            "but direct use of that adapter does not prove the exact source theorem. "
            "The next artifact should strengthen the exact proof body or adapter "
            "toward the exact theorem shape."
        )
    return (
        "Use this as ProofEngineer runtime feedback. Do not count it "
        "as source-theorem proof unless source_theorem_kernel_verified=true."
    )


def _runtime_learning_acceptance_gate(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> str:
    if row.semantic_alignment_blockers:
        return (
            "Reviewed or Lean-verified exact semantic definitions replace the "
            "unreviewed synthesized definitions, source-theorem target provenance "
            "is promoted, and only then local Lean/AXLE retries the exact proof body."
        )
    return "source_theorem_kernel_verified=true for the exact source theorem target"


def _classify_failure(
    diagnostics: tuple[str, ...],
    *,
    errors: list[str],
    proof_body_attempt_summaries: tuple[str, ...] = (),
    placeholder_symbols: tuple[str, ...],
    typeclass_blockers: tuple[str, ...],
    semantic_alignment_blockers: tuple[str, ...] = (),
    proof_body_goal_reached: bool = False,
    theorem_reduction_closure_declarations: tuple[str, ...] = (),
    verified_adapter_declarations: tuple[str, ...] = (),
) -> str:
    if placeholder_symbols:
        return "formal_environment_placeholder_primitives"
    if typeclass_blockers:
        return "formal_environment_typeclass_blockers_unreviewed"
    if semantic_alignment_blockers:
        if proof_body_goal_reached:
            return "proof_body_reached_semantic_alignment_unreviewed"
        return "source_theorem_semantic_alignment_unreviewed"
    text = "\n".join(diagnostics or tuple(errors)).lower()
    if "timed out" in text or "timeout" in text:
        return "local_lean_timeout"
    if "unknown module prefix" in text or "invalid 'import' command" in text:
        return "lean_import_environment_missing"
    if "unknown identifier" in text or "unknown constant" in text or "function expected" in text:
        return "formal_environment_symbol_missing"
    if "failed to synthesize" in text:
        return "formal_environment_instance_missing"
    attempt_text = "\n".join(proof_body_attempt_summaries).lower()
    if proof_body_goal_reached and (
        "diagnostic_kind=unknown_identifier" in attempt_text
        or "diagnostic_kind=unknown_constant" in attempt_text
    ):
        return "proof_body_dependency_context_missing"
    if _proof_body_verified_adapter_context_insufficient(
        proof_body_attempt_summaries,
        verified_adapter_declarations=verified_adapter_declarations,
    ):
        return "proof_body_verified_adapter_context_insufficient"
    if _proof_body_reduction_closure_adapter_instantiation_missing(
        proof_body_attempt_summaries,
        theorem_reduction_closure_declarations=(
            theorem_reduction_closure_declarations
        ),
    ):
        return "proof_body_reduction_closure_adapter_instantiation_missing"
    if "unsolved goals" in text:
        return "proof_body_incomplete"
    if errors:
        return "static_execution_contract_failed"
    return ""


def _exact_goal_shape_obligation_ids(
    *,
    source: str,
    diagnostics: tuple[str, ...],
    proof_body_attempt_summaries: tuple[str, ...],
    verified_adapter_declarations: tuple[str, ...],
    failure_classification: str,
) -> tuple[str, ...]:
    """Extract machine-routable proof obligations from the reached Lean goal shape."""

    text = "\n".join((source, *diagnostics, *proof_body_attempt_summaries))
    normalized = text.lower()
    obligations: list[str] = []
    if (
        failure_classification == "proof_body_verified_adapter_context_insufficient"
        or _proof_body_verified_adapter_context_insufficient(
            proof_body_attempt_summaries,
            verified_adapter_declarations=verified_adapter_declarations,
        )
    ):
        obligations.append("source_to_bridge_adapter_goal_shape_mismatch")
    if "∧" in text:
        obligations.append("conjunctive_source_theorem_split")
    if "p.real" in normalized:
        obligations.append("real_probability_lower_bound_from_ennreal_adapter")
    if "≤ 1 - alpha + 1 /" in text or "<= 1 - alpha + 1 /" in normalized:
        obligations.append("upper_coverage_bound_component")
    if "hexch : exchangeable" in normalized or "(hexch : exchangeable" in normalized:
        obligations.append("exchangeability_rank_uniformity_instantiation")
    if "orderstat" in normalized or "q_hat" in normalized:
        obligations.append("order_statistic_quantile_rank_instantiation")
    if "hc :" in normalized or "hC :" in text:
        obligations.append("coverage_event_identification_from_hC")
    return tuple(dict.fromkeys(obligations))


def _exact_goal_shape_obligation_description(obligation_id: str) -> str:
    descriptions = {
        "source_to_bridge_adapter_goal_shape_mismatch": (
            "Kernel-verified source-to-bridge adapter is available, but its conclusion "
            "does not directly close the exact source theorem goal."
        ),
        "conjunctive_source_theorem_split": (
            "Exact source theorem goal is a conjunction; ProofEngineer must prove each "
            "component separately before assembling the final proof."
        ),
        "real_probability_lower_bound_from_ennreal_adapter": (
            "Bridge the ENNReal measure lower-bound adapter to the source theorem's "
            "real-valued probability statement."
        ),
        "upper_coverage_bound_component": (
            "Prove or supply the upper split-conformal coverage component; the current "
            "verified adapter only supports the lower-bound direction."
        ),
        "exchangeability_rank_uniformity_instantiation": (
            "Instantiate exchangeability into the finite-rank/uniformity primitive "
            "needed by the exact source theorem proof."
        ),
        "order_statistic_quantile_rank_instantiation": (
            "Connect the exact order statistic/quantile definition to the rank event "
            "used by bridge and coverage lemmas."
        ),
        "coverage_event_identification_from_hC": (
            "Use the exact coverage-set hypothesis hC to identify the event in the "
            "source theorem with the bridge theorem's covered set."
        ),
    }
    return descriptions.get(
        obligation_id,
        "Repair an exact source theorem goal-shape obligation before rerunning local Lean.",
    )


def _proof_body_verified_adapter_context_insufficient(
    proof_body_attempt_summaries: tuple[str, ...],
    *,
    verified_adapter_declarations: tuple[str, ...],
) -> bool:
    if not proof_body_attempt_summaries or not verified_adapter_declarations:
        return False
    attempt_text = "\n".join(proof_body_attempt_summaries).lower()
    mentions_adapter = any(
        declaration.lower() in attempt_text
        for declaration in verified_adapter_declarations
    )
    if not mentions_adapter:
        return False
    if "diagnostic_kind=unknown_identifier" in attempt_text:
        return False
    if "diagnostic_kind=unknown_constant" in attempt_text:
        return False
    insufficient_markers = (
        "diagnostic_kind=type_mismatch",
        "type mismatch",
        "unsolved goals",
        "diagnostic_kind=unsolved_goals",
        "tactic `assumption` failed",
    )
    return any(marker in attempt_text for marker in insufficient_markers)


def _proof_body_reduction_closure_adapter_instantiation_missing(
    proof_body_attempt_summaries: tuple[str, ...],
    *,
    theorem_reduction_closure_declarations: tuple[str, ...],
) -> bool:
    if not proof_body_attempt_summaries or not theorem_reduction_closure_declarations:
        return False
    attempt_text = "\n".join(proof_body_attempt_summaries).lower()
    if "diagnostic_kind=unknown_identifier" in attempt_text:
        return False
    if "diagnostic_kind=unknown_constant" in attempt_text:
        return False
    mentions_closure = any(
        declaration.lower() in attempt_text
        for declaration in theorem_reduction_closure_declarations
    )
    if not mentions_closure:
        return False
    adapter_markers = (
        "typeclass instance problem is stuck",
        "diagnostic_kind=type_mismatch",
        "type mismatch",
        "failed to synthesize",
        "function expected",
    )
    return any(marker in attempt_text for marker in adapter_markers)


def _source_theorem_target_identity_status(
    *,
    source_theorem_target_known: bool,
    target_identity_status: str,
    target_identity_errors: tuple[str, ...],
    expected_target_lean_declaration: str,
    target_lean_declaration: str,
) -> str:
    if target_identity_errors or target_identity_status == "TARGET_DECLARATION_MISMATCH":
        return "TARGET_DECLARATION_MISMATCH"
    if source_theorem_target_known:
        return "SOURCE_THEOREM_TARGET_KNOWN"
    if (
        target_identity_status == "TARGET_DECLARATION_MATCHED"
        and expected_target_lean_declaration
        and target_lean_declaration
        and expected_target_lean_declaration == target_lean_declaration
    ):
        return "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    if target_lean_declaration:
        return "DECLARATION_FOUND_SOURCE_THEOREM_TARGET_UNPROMOTED"
    return "SOURCE_THEOREM_TARGET_UNKNOWN"


def _semantic_alignment_constraints_block_source_kernel(
    constraints: tuple[str, ...],
) -> tuple[str, ...]:
    blocking_markers = (
        "draft",
        "unreviewed",
        "semantic_definition_risk",
        "semantic risk",
        "requires semantic review",
        "not reviewed",
        "placeholder",
        "support only",
        "marginal coverage only",
        "not exact",
        "weaker than",
        "ignores rank",
    )
    blockers: list[str] = []
    for constraint in constraints:
        text = str(constraint).strip()
        lowered = text.lower()
        if lowered.startswith("unreviewed synthesized definition review note:"):
            continue
        if any(marker in lowered for marker in blocking_markers):
            blockers.append(text)
    return tuple(blockers)


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


def _dominant_failure_classification(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
) -> str:
    failures = Counter(row.failure_classification for row in rows if row.failure_classification)
    if not failures:
        return ""
    return failures.most_common(1)[0][0]


def _markdown_report(payload: Mapping[str, object]) -> str:
    lines = [
        "# Exact Source Theorem Proof-Body Executor",
        "",
        f"- Rows: {payload.get('n_ok')}/{payload.get('n_execution_result_rows')}",
        f"- Local Lean checked: {payload.get('n_local_lean_checked')}",
        f"- Proof body goal reached: {payload.get('n_proof_body_goal_reached')}",
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
            f"source_kernel={row.get('source_theorem_kernel_verified')} "
            f"proof_body_goal_reached={row.get('proof_body_goal_reached')}"
        )
        if row.get("proof_body_gate_status"):
            lines.append(f"  proof-body gate: `{row.get('proof_body_gate_status')}`")
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
