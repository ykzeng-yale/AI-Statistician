from __future__ import annotations

import json
import re
import shutil
import textwrap
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from .fingerprint import stable_hash
from .lean_proof_agent_contract import llm_proof_body_generation_contract
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    FORBIDDEN_ARTIFACT_TOKENS,
    _lean_command,
    _run_local_lean,
)
from .source_theorem_exact_semantic_definition_source_lookup import (
    EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS,
    normalize_exact_semantic_definition_signature_probe_context,
)
from .source_theorem_semantic_primitive_proofengineer_bridge import (
    inferred_exact_goal_shape_obligation_ids_from_feedback as _policy_goal_obligations_from_feedback,
    semantic_gap_for_exact_goal_shape_obligation as _policy_goal_obligation_gap,
)
from .exact_semantic_definition_policy import (
    exact_semantic_definition_proof_body_adapter_synthesis_instruction,
)


SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
ARTIFACT_KERNEL_NOT_SOURCE_STATUS = (
    "EXACT_SOURCE_THEOREM_PROOF_BODY_ARTIFACT_KERNEL_VERIFIED_NOT_SOURCE_THEOREM"
)
SOURCE_KERNEL_STATUS = "EXACT_SOURCE_THEOREM_PROOF_BODY_SOURCE_KERNEL_VERIFIED"
EXTERNAL_CANDIDATE_KERNEL_STATUS = (
    "EXTERNAL_PROOF_CANDIDATE_EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
)
EXTERNAL_CANDIDATE_ARTIFACT_KERNEL_STATUS = (
    "EXTERNAL_PROOF_CANDIDATE_ARTIFACT_KERNEL_VERIFIED_NOT_SOURCE_THEOREM"
)
EXTERNAL_CANDIDATE_NOT_PROOF_STATUS = (
    "EXTERNAL_PROOF_CANDIDATE_RERUN_NOT_PROOF_EVIDENCE"
)
SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE = (
    "source_theorem_candidate_materialization_required"
)
SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_CONTRACT = (
    "Formalizer/ProofEngineer must materialize an exact source-theorem Lean "
    "candidate artifact with a signature probe and live proof-body location "
    "before exact proof-body execution can run."
)
PROOF_EVIDENCE_BOUNDARY = (
    "Exact source-theorem proof-body executor rows materialize ProofEngineer "
    "candidate artifacts from the source prefix environment plus the exact target "
    "declaration and run optional local Lean/AXLE checks. Commands after the target "
    "are content-hash-bound lineage but are intentionally outside the theorem's "
    "visible elaboration environment and are not claimed to compile. A candidate "
    "is source-theorem proof evidence only when the exact declaration passes "
    "Lean/AXLE and the prefix environment has no placeholder primitives or "
    "unresolved semantic repairs."
)
def execute_external_exact_source_theorem_proof_candidates(
    *,
    request: Mapping[str, Any],
    provider_result: Mapping[str, Any],
    out_dir: Path,
    local_lean: bool = False,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
    local_lean_runner: Callable[..., tuple[bool, int, tuple[str, ...]]] | None = None,
    max_candidates: int = 4,
) -> dict[str, object]:
    """Materialize external proof bodies against the preserved exact declaration.

    The external provider remains proposal/search infrastructure. Source-theorem
    evidence is emitted only when the original lineage-bound declaration is
    preserved and the resulting artifact passes this process's local Lean gate.
    """

    request_payload = dict(request)
    result_payload = dict(provider_result)
    request_fingerprint = str(
        request_payload.get("request_fingerprint", "") or ""
    )
    target_declaration = str(
        request_payload.get("target_lean_declaration", "") or ""
    ).strip()
    target_statement = str(
        request_payload.get("target_theorem_statement", "") or ""
    ).strip()
    target_ids = _str_tuple(request_payload.get("target_ids", []))
    source_candidate_path_text = str(
        request_payload.get("lineage_candidate_artifact_path", "")
        or request_payload.get("source_candidate_artifact_path", "")
        or request_payload.get("candidate_artifact_path", "")
        or ""
    )
    source_candidate_path = Path(source_candidate_path_text)
    proof_bodies = _external_proof_candidate_bodies(
        result_payload,
        max_candidates=max_candidates,
    )
    project_path = Path(lean_project) if lean_project else None
    command = lean_command or _lean_command(project_path)
    runner = local_lean_runner or _run_local_lean

    source = ""
    source_errors: list[str] = []
    if not request_fingerprint:
        source_errors.append("request_fingerprint missing")
    provider_fingerprint = str(
        result_payload.get("request_fingerprint", "") or ""
    )
    if provider_fingerprint != request_fingerprint:
        source_errors.append("provider result request_fingerprint mismatch")
    provider_target = str(
        result_payload.get("target_lean_declaration", "") or ""
    ).strip()
    if provider_target != target_declaration:
        source_errors.append("provider result target_lean_declaration mismatch")
    if not target_declaration:
        source_errors.append("target_lean_declaration missing")
    if not target_statement:
        source_errors.append("target_theorem_statement missing")
    if not source_candidate_path_text:
        source_errors.append("lineage-bound candidate artifact path missing")
    elif not source_candidate_path.is_file():
        source_errors.append(
            f"lineage-bound candidate artifact missing: {source_candidate_path}"
        )
    else:
        try:
            source = source_candidate_path.read_text(encoding="utf-8")
        except OSError as exc:
            source_errors.append(
                "failed to read lineage-bound candidate artifact: "
                f"{type(exc).__name__}: {exc}"
            )
    observed_statement = _external_exact_target_statement(
        source,
        target_declaration=target_declaration,
    )
    exact_target_span = _exact_target_statement_span(
        source,
        target_declaration=target_declaration,
        target_statement=target_statement,
    )
    if source and not observed_statement:
        source_errors.append(
            "lineage-bound candidate artifact lacks the exact target declaration proof"
        )
    elif observed_statement and _normalized_lean_signature(
        observed_statement
    ) != _normalized_lean_signature(target_statement):
        source_errors.append(
            "lineage-bound candidate theorem signature differs from "
            "target_theorem_statement"
        )
    if source and exact_target_span is None:
        source_errors.append(
            "target_theorem_statement is not the exact byte-preserved declaration "
            "header immediately followed by `:= by`"
        )
    exact_target_prefix_hash = stable_hash(
        source[: exact_target_span[0]] if exact_target_span is not None else ""
    )
    source_after_exact_target_marker_hash = stable_hash(
        source[exact_target_span[2] :] if exact_target_span is not None else ""
    )
    source_errors.extend(
        _external_candidate_lineage_errors(
            request_payload,
            source=source,
            observed_statement=observed_statement,
            target_declaration=target_declaration,
            target_statement=target_statement,
            source_candidate_path=source_candidate_path,
        )
    )

    run_started_at = datetime.now(timezone.utc).isoformat()
    source_candidate_artifact_hash = stable_hash(source)
    provider_result_fingerprint = stable_hash(result_payload)
    verification_config_fingerprint = stable_hash(
        {
            "local_lean": bool(local_lean),
            "lean_command": list(command),
            "lean_project": str(project_path or ""),
            "lean_timeout": max(1, int(lean_timeout or 90)),
            "runner": (
                f"{getattr(runner, '__module__', '')}."
                f"{getattr(runner, '__qualname__', type(runner).__qualname__)}"
            ),
        }
    )
    input_fingerprint = stable_hash(
        {
            "request_fingerprint": request_fingerprint,
            "request_lineage": {
                key: request_payload.get(key)
                for key in (
                    "source_work_order_id",
                    "execution_queue_id",
                    "lineage_candidate_artifact_path",
                    "lineage_candidate_artifact_hash",
                    "target_declaration_source_hash",
                    "target_theorem_statement_hash",
                    "target_theorem_statement_hash_algorithm",
                    "proof_body_signature_probe_artifact_path",
                )
            },
            "target_declaration": target_declaration,
            "target_statement": target_statement,
            "source_candidate_artifact_hash": source_candidate_artifact_hash,
            "provider_result_fingerprint": provider_result_fingerprint,
            "proof_bodies": proof_bodies,
            "verification_config_fingerprint": verification_config_fingerprint,
        }
    )
    execution_fingerprint = stable_hash(
        [input_fingerprint, run_started_at, uuid4().hex]
    )
    run_key = f"{input_fingerprint[:20]}/{execution_fingerprint[:20]}"
    artifact_dir = Path(out_dir) / run_key
    artifact_dir.mkdir(parents=True, exist_ok=False)
    execution_id = (
        "external_exact_proof_candidate_rerun_execution:"
        + execution_fingerprint[:20]
    )
    manifest_id = "external_exact_proof_candidate_rerun:" + execution_fingerprint[:20]
    manifest_path = artifact_dir / "external_exact_proof_candidate_rerun_manifest.json"
    rows_path = artifact_dir / "external_exact_proof_candidate_rerun_rows.jsonl"

    evidence_blockers = _external_candidate_source_evidence_blockers(
        request_payload,
        target_ids=target_ids,
        target_declaration=target_declaration,
    )
    rows: list[dict[str, object]] = []
    safe_target = re.sub(r"[^A-Za-z0-9_.-]+", "_", target_declaration).strip("_")
    safe_target = safe_target or "exact_source_theorem"
    for index, raw_body in enumerate(proof_bodies, start=1):
        body = _normalize_external_proof_body(raw_body)
        precheck_errors = [
            *source_errors,
            *_external_proof_body_contract_errors(body),
        ]
        candidate_source = ""
        materialized_support_asset_names: tuple[str, ...] = ()
        materialized_support_asset_hashes: tuple[str, ...] = ()
        candidate_path = artifact_dir / f"{index:03d}_{safe_target}.lean"
        candidate_written = False
        if not precheck_errors:
            (
                candidate_source,
                materialized_support_asset_names,
                materialized_support_asset_hashes,
                materialization_errors,
            ) = materialize_external_exact_source_candidate(
                source=source,
                proof_body=body,
                support_assets=result_payload.get(
                    "verified_support_assets",
                    [],
                ),
                target_declaration=target_declaration,
                target_statement=target_statement,
            )
            precheck_errors.extend(materialization_errors)
            materialized_statement = _external_exact_target_statement(
                candidate_source,
                target_declaration=target_declaration,
            )
            if candidate_source and _normalized_lean_signature(
                materialized_statement
            ) != _normalized_lean_signature(target_statement):
                precheck_errors.append(
                    "materialized candidate did not preserve target_theorem_statement"
                )
        else:
            materialized_statement = ""
        exact_signature_preserved = bool(
            materialized_statement
            and _normalized_lean_signature(materialized_statement)
            == _normalized_lean_signature(target_statement)
        )
        if candidate_source and not precheck_errors:
            candidate_path.write_text(candidate_source, encoding="utf-8")
            candidate_written = True

        checked = False
        compiled = False
        returncode = -1
        diagnostics: tuple[str, ...] = ()
        candidate_artifact_hash = ""
        candidate_artifact_unchanged_after_verification = candidate_written
        if local_lean and not command:
            diagnostics = ("Lean executable not found",)
        elif local_lean and not precheck_errors:
            checked = True
            compiled, returncode, diagnostics = runner(
                candidate_path,
                lean_command=command,
                lean_project=project_path,
                timeout_s=max(1, int(lean_timeout or 90)),
            )
            diagnostics = tuple(str(value) for value in diagnostics)
        if candidate_written:
            try:
                persisted_candidate_source = candidate_path.read_text(encoding="utf-8")
            except OSError as exc:
                persisted_candidate_source = ""
                candidate_artifact_unchanged_after_verification = False
                diagnostics = (
                    *diagnostics,
                    "candidate artifact unreadable after local Lean verification: "
                    f"{type(exc).__name__}: {exc}",
                )
            else:
                candidate_artifact_hash = stable_hash(persisted_candidate_source)
                candidate_artifact_unchanged_after_verification = (
                    persisted_candidate_source == candidate_source
                )
            if not candidate_artifact_unchanged_after_verification:
                compiled = False
                diagnostics = (
                    *diagnostics,
                    "candidate artifact changed during local Lean verification",
                )
        artifact_kernel_verified = bool(
            checked
            and compiled
            and candidate_artifact_unchanged_after_verification
            and not precheck_errors
        )
        source_theorem_kernel_verified = bool(
            artifact_kernel_verified and not evidence_blockers
        )
        if source_theorem_kernel_verified:
            status = "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
            proof_status = EXTERNAL_CANDIDATE_KERNEL_STATUS
        elif artifact_kernel_verified:
            status = "ARTIFACT_KERNEL_VERIFIED_LINEAGE_BLOCKED"
            proof_status = EXTERNAL_CANDIDATE_ARTIFACT_KERNEL_STATUS
        elif precheck_errors:
            status = "CANDIDATE_PRECHECK_REJECTED"
            proof_status = EXTERNAL_CANDIDATE_NOT_PROOF_STATUS
        elif checked:
            status = "LOCAL_LEAN_FAILED"
            proof_status = EXTERNAL_CANDIDATE_NOT_PROOF_STATUS
        else:
            status = "MATERIALIZED_REQUIRES_LOCAL_LEAN"
            proof_status = EXTERNAL_CANDIDATE_NOT_PROOF_STATUS
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "artifact_kind": "ExternalExactProofCandidateRerunRow",
                "row_id": "external_exact_proof_candidate_rerun_row:"
                + stable_hash([manifest_id, index, body])[:20],
                "candidate_index": index,
                "candidate_proof_body": body,
                "candidate_proof_body_hash": stable_hash(body),
                "candidate_origin": "external_llm_or_prover_provider",
                "runtime_generated_proof_body": False,
                "request_fingerprint": request_fingerprint,
                "input_fingerprint": input_fingerprint,
                "execution_id": execution_id,
                "question_id": str(request_payload.get("question_id", "") or ""),
                "source_task_id": str(
                    request_payload.get("source_task_id", "") or ""
                ),
                "source_work_order_id": str(
                    request_payload.get("source_work_order_id", "") or ""
                ),
                "execution_queue_id": str(
                    request_payload.get("execution_queue_id", "") or ""
                ),
                "source_lineage_id": str(
                    request_payload.get("source_lineage_id", "") or ""
                ),
                "materialized_verified_support_asset_names": list(
                    materialized_support_asset_names
                ),
                "materialized_verified_support_asset_hashes": list(
                    materialized_support_asset_hashes
                ),
                "source_candidate_artifact_path": source_candidate_path_text,
                "source_candidate_artifact_hash": (
                    source_candidate_artifact_hash
                ),
                "candidate_artifact_path": str(candidate_path) if candidate_written else "",
                "candidate_artifact_hash": (
                    candidate_artifact_hash
                ),
                "candidate_artifact_unchanged_after_verification": (
                    candidate_artifact_unchanged_after_verification
                ),
                "target_ids": list(target_ids),
                "target_lean_declaration": target_declaration,
                "target_theorem_statement": target_statement,
                "verification_scope": (
                    "source_prefix_environment_plus_exact_target_declaration"
                ),
                "exact_target_prefix_hash": exact_target_prefix_hash,
                "source_after_exact_target_marker_hash": (
                    source_after_exact_target_marker_hash
                ),
                "source_suffix_commands_executed": False,
                "exact_signature_preserved": exact_signature_preserved,
                "precheck_errors": precheck_errors,
                "source_theorem_evidence_blockers": list(evidence_blockers),
                "local_lean_requested": bool(local_lean),
                "local_lean_checked": checked,
                "local_lean_compiled": compiled,
                "lean_command": list(command),
                "lean_project": str(project_path or ""),
                "lean_timeout": max(1, int(lean_timeout or 90)),
                "returncode": returncode,
                "diagnostics": list(diagnostics)[:24],
                "artifact_kernel_verified": artifact_kernel_verified,
                "source_theorem_kernel_verified": (
                    source_theorem_kernel_verified
                ),
                "verification_strength": (
                    "local_lean_exact_external_whole_proof_candidate_kernel"
                    if checked
                    else "deterministic_exact_candidate_materialization"
                ),
                "proof_evidence_status": proof_status,
                "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
                "status": status,
            }
        )
        if source_theorem_kernel_verified:
            break

    rows_path.write_text(
        "".join(json.dumps(row, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )
    verified_rows = [
        row for row in rows if row["source_theorem_kernel_verified"] is True
    ]
    compiled_rows = [
        row for row in rows if row["local_lean_compiled"] is True
    ]
    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "RuntimeExternalExactProofCandidateRerunManifest",
        "manifest_id": manifest_id,
        "execution_id": execution_id,
        "created_at": run_started_at,
        "input_fingerprint": input_fingerprint,
        "provider_result_fingerprint": provider_result_fingerprint,
        "verification_config_fingerprint": verification_config_fingerprint,
        "request_fingerprint": request_fingerprint,
        "question_id": str(request_payload.get("question_id", "") or ""),
        "source_task_id": str(request_payload.get("source_task_id", "") or ""),
        "source_lineage_id": str(
            request_payload.get("source_lineage_id", "") or ""
        ),
        "source_work_order_id": str(
            request_payload.get("source_work_order_id", "") or ""
        ),
        "execution_queue_id": str(
            request_payload.get("execution_queue_id", "") or ""
        ),
        "provider": str(result_payload.get("provider", "") or ""),
        "provider_result_id": str(result_payload.get("result_id", "") or ""),
        "target_ids": list(target_ids),
        "target_lean_declaration": target_declaration,
        "target_theorem_statement": target_statement,
        "verification_scope": (
            "source_prefix_environment_plus_exact_target_declaration"
        ),
        "exact_target_prefix_hash": exact_target_prefix_hash,
        "source_after_exact_target_marker_hash": (
            source_after_exact_target_marker_hash
        ),
        "source_suffix_commands_executed": False,
        "source_candidate_artifact_path": source_candidate_path_text,
        "source_candidate_artifact_hash": source_candidate_artifact_hash,
        "proof_body_signature_probe_artifact_path": str(
            request_payload.get(
                "proof_body_signature_probe_artifact_path",
                "",
            )
            or ""
        ),
        "proof_body_signature_probe_artifact_hash": str(
            request_payload.get(
                "proof_body_signature_probe_artifact_hash",
                "",
            )
            or ""
        ),
        "source_precheck_errors": source_errors,
        "manifest_path": str(manifest_path),
        "rows_path": str(rows_path),
        "rows": rows,
        "n_candidate_proof_bodies": len(proof_bodies),
        "n_runtime_generated_proof_bodies": 0,
        "proof_body_generation_contract": llm_proof_body_generation_contract(),
        "n_result_rows": len(rows),
        "n_precheck_rejected": sum(
            1 for row in rows if row["status"] == "CANDIDATE_PRECHECK_REJECTED"
        ),
        "n_local_lean_checked": sum(
            1 for row in rows if row["local_lean_checked"] is True
        ),
        "n_local_lean_compiled": len(compiled_rows),
        "n_artifact_kernel_verified": sum(
            1 for row in rows if row["artifact_kernel_verified"] is True
        ),
        "n_source_theorem_kernel_verified": len(verified_rows),
        "source_theorem_kernel_verified": bool(verified_rows),
        "source_theorem_kernel_verified_target_ids": (
            list(target_ids) if verified_rows else []
        ),
        "source_theorem_kernel_verified_target_names": (
            [target_declaration] if verified_rows else []
        ),
        "local_lean_requested": bool(local_lean),
        "full_frontier_theorem_proved": False,
        "proof_evidence_status": (
            EXTERNAL_CANDIDATE_KERNEL_STATUS
            if verified_rows
            else EXTERNAL_CANDIDATE_ARTIFACT_KERNEL_STATUS
            if compiled_rows
            else EXTERNAL_CANDIDATE_NOT_PROOF_STATUS
        ),
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest


def _bool_like(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
        return default
    if isinstance(value, (int, float)):
        return value != 0
    return bool(value)


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
    target_ids: tuple[str, ...]
    target_lean_declaration: str
    expected_target_lean_declaration: str
    source_theorem_target_known: bool
    source_theorem_target_identity_status: str
    source_theorem_target_provenance: dict[str, object]
    semantic_alignment_constraints: tuple[str, ...]
    semantic_alignment_blockers: tuple[str, ...]
    exact_semantic_definition_context: dict[str, object]
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
    target_identity_source: str
    signature_probe_artifact_hash: str
    signature_probe_artifact_hash_verified: bool
    target_artifact_lineage_verified: bool
    source_candidate_artifact_path: str
    signature_probe_artifact_path: str
    source_theorem_signature_probe_artifact_path: str
    proof_body_signature_probe_artifact_path: str
    candidate_artifact_path: str
    execution_transcript_path: str
    live_goal_location_ready: bool
    candidate_live_proof_state_request: dict[str, object]
    next_owner_subsystem: str
    proofengineer_repair_context: dict[str, object]
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
        "n_runtime_generated_proof_bodies": 0,
        "proof_body_generation_contract": llm_proof_body_generation_contract(),
        "n_artifact_kernel_verified": sum(1 for row in rows if row.artifact_kernel_verified),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_execution_result_rows_from_pseudo_formal": sum(
            1 for row in rows if _row_has_pseudo_formal_origin(row)
        ),
        "n_execution_result_rows_from_formalizer_pf_component_gate": sum(
            1 for row in rows if _row_has_formalizer_pf_component_gate_origin(row)
        ),
        "n_local_lean_checked_from_pseudo_formal": sum(
            1
            for row in rows
            if row.local_lean_checked and _row_has_pseudo_formal_origin(row)
        ),
        "n_local_lean_checked_from_formalizer_pf_component_gate": sum(
            1
            for row in rows
            if row.local_lean_checked
            and _row_has_formalizer_pf_component_gate_origin(row)
        ),
        "n_local_lean_compiled_from_pseudo_formal": sum(
            1
            for row in rows
            if row.local_lean_compiled and _row_has_pseudo_formal_origin(row)
        ),
        "n_local_lean_compiled_from_formalizer_pf_component_gate": sum(
            1
            for row in rows
            if row.local_lean_compiled
            and _row_has_formalizer_pf_component_gate_origin(row)
        ),
        "n_proof_body_goal_reached_from_pseudo_formal": sum(
            1
            for row in rows
            if row.proof_body_goal_reached and _row_has_pseudo_formal_origin(row)
        ),
        "n_proof_body_goal_reached_from_formalizer_pf_component_gate": sum(
            1
            for row in rows
            if row.proof_body_goal_reached
            and _row_has_formalizer_pf_component_gate_origin(row)
        ),
        "n_source_theorem_kernel_verified_from_pseudo_formal": sum(
            1
            for row in rows
            if row.source_theorem_kernel_verified
            and _row_has_pseudo_formal_origin(row)
        ),
        "n_source_theorem_kernel_verified_from_formalizer_pf_component_gate": sum(
            1
            for row in rows
            if row.source_theorem_kernel_verified
            and _row_has_formalizer_pf_component_gate_origin(row)
        ),
        "source_pseudo_formal_work_order_ids": _source_pseudo_formal_ids(
            rows,
            "source_pseudo_formal_work_order_id",
        ),
        "source_pseudo_formal_block_ids": _source_pseudo_formal_ids(
            rows,
            "source_pseudo_formal_block_id",
        ),
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": (
            _formalizer_pf_component_gate_exact_rows_jsonl_paths(rows)
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
        "n_proof_body_gate_open_for_kernel_repair": sum(
            1 for row in rows if _proof_body_gate_open_for_kernel_repair(row)
        ),
        "proof_body_gate_open_target_names": _proof_body_gate_open_target_names(rows),
        "proof_body_gate_open_target_ids": _proof_body_gate_open_target_ids(rows),
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
        "n_exact_semantic_definition_context_rows": sum(
            1 for row in rows if row.exact_semantic_definition_context
        ),
        "n_proof_body_signature_probe_artifact_rows": sum(
            1 for row in rows if row.proof_body_signature_probe_artifact_path
        ),
        "proof_body_signature_probe_artifact_paths": list(
            dict.fromkeys(
                row.proof_body_signature_probe_artifact_path
                for row in rows
                if row.proof_body_signature_probe_artifact_path
            )
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
        "verified_source_to_bridge_premise_derivation_artifact_paths": (
            _verified_source_to_bridge_premise_derivation_artifact_paths(rows)
        ),
        "verified_source_to_bridge_premise_derivation_declarations": (
            _verified_source_to_bridge_premise_derivation_declarations(rows)
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
    target_ids = _proof_body_target_ids(
        row,
        fallback_target=target_theorem_name,
    )
    target_lean_declaration = str(row.get("target_lean_declaration", "") or "")
    expected_target_lean_declaration = str(
        row.get("expected_target_lean_declaration", "") or target_lean_declaration
    )
    source_theorem_target_known = _bool_like(
        row.get("source_theorem_target_known", False)
    )
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
    explicit_semantic_alignment_blockers = _str_tuple(
        row.get("semantic_alignment_blockers", [])
    )
    semantic_review_approved = _row_has_reviewed_exact_semantic_definition_approval(row)
    semantic_alignment_blockers = _semantic_alignment_constraints_block_source_kernel(
        semantic_alignment_constraints,
        explicit_blockers=explicit_semantic_alignment_blockers,
        semantic_review_approved=semantic_review_approved,
    )
    exact_semantic_definition_context = _exact_semantic_definition_context(row)
    target_identity_status = str(row.get("target_identity_status", "") or "")
    target_identity_errors = _str_tuple(row.get("target_identity_errors", []))
    target_identity_source = str(
        row.get("target_identity_source", "") or "legacy_unbound_target_identity"
    )
    signature_probe_artifact_hash = str(
        row.get("signature_probe_artifact_hash", "") or ""
    )
    expected_signature_probe_artifact_hash = str(
        row.get("expected_signature_probe_artifact_hash", "") or ""
    )
    signature_probe_artifact_hash_verified = False
    target_artifact_lineage_verified = False
    source_theorem_target_identity_status = str(
        row.get("source_theorem_target_identity_status", "") or ""
    ) or _source_theorem_target_identity_status(
        source_theorem_target_known=source_theorem_target_known,
        target_identity_status=target_identity_status,
        target_identity_errors=target_identity_errors,
        expected_target_lean_declaration=expected_target_lean_declaration,
        target_lean_declaration=target_lean_declaration,
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
    source_theorem_proof_body_adapter_kernel_verified = (
        _bool_like(row.get("source_theorem_proof_body_adapter_kernel_verified", False))
        or bool(kernel_verified_source_theorem_proof_body_adapter_ids)
    )
    source_theorem_proof_body_adapter_feedback_available = (
        _bool_like(
            row.get("source_theorem_proof_body_adapter_feedback_available", False)
        )
        or source_theorem_proof_body_adapter_kernel_verified
        or bool(verified_source_theorem_proof_body_adapter_artifact_paths)
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
    reviewed_target_kernel_eligible = (
        semantic_review_approved
        and source_theorem_target_known
        and target_identity_status == "TARGET_DECLARATION_MATCHED"
        and not target_identity_errors
    )
    source_theorem_kernel_evidence_eligible = (
        _bool_like(
            row.get(
                "source_theorem_kernel_evidence_eligible",
                source_theorem_target_known and not semantic_alignment_blockers,
            ),
            default=source_theorem_target_known and not semantic_alignment_blockers,
        )
        or reviewed_target_kernel_eligible
    ) and not semantic_alignment_blockers
    source_candidate_artifact_path = str(
        row.get("source_candidate_artifact_path", "") or ""
    )
    signature_probe_artifact_path = str(
        row.get("signature_probe_artifact_path", "")
        or exact_semantic_definition_context.get("signature_probe_artifact_path", "")
        or row.get("source_theorem_signature_probe_artifact_path", "")
        or exact_semantic_definition_context.get(
            "source_theorem_signature_probe_artifact_path",
            "",
        )
        or row.get("proof_body_signature_probe_artifact_path", "")
        or exact_semantic_definition_context.get(
            "proof_body_signature_probe_artifact_path",
            "",
        )
        or ""
    )
    source_theorem_signature_probe_artifact_path = str(
        row.get("source_theorem_signature_probe_artifact_path", "")
        or exact_semantic_definition_context.get(
            "source_theorem_signature_probe_artifact_path",
            "",
        )
        or signature_probe_artifact_path
    )
    proof_body_signature_probe_artifact_path = str(
        row.get("proof_body_signature_probe_artifact_path", "")
        or exact_semantic_definition_context.get(
            "proof_body_signature_probe_artifact_path",
            "",
        )
        or source_theorem_signature_probe_artifact_path
        or signature_probe_artifact_path
    )
    normalize_exact_semantic_definition_signature_probe_context(
        exact_semantic_definition_context,
        {
            "signature_probe_artifact_path": signature_probe_artifact_path,
            "source_theorem_signature_probe_artifact_path": (
                source_theorem_signature_probe_artifact_path
            ),
            "proof_body_signature_probe_artifact_path": (
                proof_body_signature_probe_artifact_path
            ),
        },
    )
    candidate_artifact_path = Path(str(row.get("candidate_artifact_path", "") or ""))
    execution_transcript_path = Path(str(row.get("execution_transcript_path", "") or ""))
    source_path = Path(signature_probe_artifact_path)
    already_repaired = row.get("already_repaired_environment", {})
    if not isinstance(already_repaired, Mapping):
        already_repaired = {}
    placeholder_symbols = _str_tuple(already_repaired.get("missing_formal_symbols", []))
    typeclass_blockers = _str_tuple(already_repaired.get("typeclass_blockers", []))
    signature_typecheck_reached_proof_body = _bool_like(
        already_repaired.get("signature_typecheck_reached_proof_body", False)
    )
    live_goal_ready = _bool_like(row.get("live_goal_location_ready", False))
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
    if not target_lean_declaration:
        errors.append("target_lean_declaration missing")
    if not signature_probe_artifact_path:
        errors.append("signature_probe_artifact_path missing")
    elif not source_path.exists():
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
            observed_source_hash = stable_hash(source)
            signature_probe_artifact_hash_verified = bool(
                signature_probe_artifact_hash
                and observed_source_hash == signature_probe_artifact_hash
                and (
                    not expected_signature_probe_artifact_hash
                    or expected_signature_probe_artifact_hash
                    == signature_probe_artifact_hash
                )
            )
            if (
                target_identity_source
                == "upstream_structured_target_declaration_and_artifact_hash"
                and not signature_probe_artifact_hash_verified
            ):
                errors.append(
                    "structured target identity is not bound to the exact "
                    "signature-probe artifact hash"
                )
            if target_identity_source != (
                "upstream_structured_target_declaration_and_artifact_hash"
            ):
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
        exact_declaration_present = (
            target_identity_status == "TARGET_DECLARATION_MATCHED"
            and not target_identity_errors
            and expected_target_lean_declaration == target_lean_declaration
            and (
                signature_probe_artifact_hash_verified
                if target_identity_source
                == "upstream_structured_target_declaration_and_artifact_hash"
                else _has_exact_declaration(source, target_lean_declaration)
            )
        )
        target_artifact_lineage_verified = bool(
            target_identity_source
            == "upstream_structured_target_declaration_and_artifact_hash"
            and exact_declaration_present
            and signature_probe_artifact_hash_verified
            and source_work_order_id
            and execution_queue_id
        )
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
        if (
            not compiled
            and target_identity_source
            != "upstream_structured_target_declaration_and_artifact_hash"
            and _proof_body_attempts(row)
            and _proof_body_attempts_should_run(
                diagnostics,
                placeholder_symbols=placeholder_symbols,
                typeclass_blockers=typeclass_blockers,
                semantic_alignment_blockers=semantic_alignment_blockers,
            )
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
        and (
            target_artifact_lineage_verified
            if target_identity_source
            == "upstream_structured_target_declaration_and_artifact_hash"
            else True
        )
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
    proofengineer_repair_context = _proofengineer_whole_proof_repair_context(
        source=source,
        target_declaration=target_lean_declaration,
        target_ids=target_ids,
        candidate_artifact_path=candidate_artifact_path,
        source_candidate_artifact_path=source_candidate_artifact_path,
        proof_body_goal_excerpt=proof_body_goal_excerpt,
        proof_body_attempt_summaries=proof_body_attempt_summaries,
        semantic_alignment_constraints=semantic_alignment_constraints,
        semantic_alignment_blockers=semantic_alignment_blockers,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_identity_status=(
            source_theorem_target_identity_status
        ),
        source_theorem_target_provenance=source_theorem_target_provenance,
        expected_target_lean_declaration=expected_target_lean_declaration,
        source_work_order_id=source_work_order_id,
        execution_queue_id=execution_queue_id,
        signature_probe_artifact_path=signature_probe_artifact_path,
        source_theorem_signature_probe_artifact_path=(
            source_theorem_signature_probe_artifact_path
        ),
        proof_body_signature_probe_artifact_path=(
            proof_body_signature_probe_artifact_path
        ),
        target_identity_status=target_identity_status,
        target_identity_errors=target_identity_errors,
        target_identity_source=target_identity_source,
        target_declaration_source_excerpt=str(
            row.get("target_declaration_source_excerpt", "") or ""
        ),
        target_declaration_source_hash=str(
            row.get("target_declaration_source_hash", "") or ""
        ),
        target_theorem_statement=str(
            row.get("target_theorem_statement", "") or ""
        ),
        current_proof_body_excerpt=str(
            row.get("current_proof_body_excerpt", "") or ""
        ),
        source_theorem_kernel_evidence_eligible=(
            source_theorem_kernel_evidence_eligible
        ),
        formal_environment_placeholder_symbols=placeholder_symbols,
        formal_environment_typeclass_blockers=typeclass_blockers,
        compiler_diagnostics=diagnostics,
        compiler_returncode=returncode,
        compiler_checked=checked,
    )
    if candidate_live_request and proofengineer_repair_context:
        candidate_live_request["proofengineer_repair_context"] = (
            proofengineer_repair_context
        )
        candidate_live_request["proof_body_repair_scope"] = (
            proofengineer_repair_context["repair_scope"]
        )
    next_owner_subsystem = _proof_body_next_owner_subsystem(
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        proof_body_goal_reached=proof_body_goal_reached,
        semantic_alignment_blockers=semantic_alignment_blockers,
        candidate_materialization_required=bool(
            failure_classification
            in {
                SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE,
                "source_theorem_candidate_artifact_missing",
            }
            or _source_candidate_materialization_required_errors(errors)
        ),
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
        target_ids=target_ids,
        target_lean_declaration=target_lean_declaration,
        expected_target_lean_declaration=expected_target_lean_declaration,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_identity_status=source_theorem_target_identity_status,
        source_theorem_target_provenance=source_theorem_target_provenance,
        semantic_alignment_constraints=semantic_alignment_constraints,
        semantic_alignment_blockers=semantic_alignment_blockers,
        exact_semantic_definition_context=exact_semantic_definition_context,
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
        target_identity_source=target_identity_source,
        signature_probe_artifact_hash=signature_probe_artifact_hash,
        signature_probe_artifact_hash_verified=(
            signature_probe_artifact_hash_verified
        ),
        target_artifact_lineage_verified=target_artifact_lineage_verified,
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
        target_ids=target_ids,
        target_lean_declaration=target_lean_declaration,
        expected_target_lean_declaration=expected_target_lean_declaration,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_identity_status=source_theorem_target_identity_status,
        source_theorem_target_provenance=source_theorem_target_provenance,
        semantic_alignment_constraints=semantic_alignment_constraints,
        semantic_alignment_blockers=semantic_alignment_blockers,
        exact_semantic_definition_context=exact_semantic_definition_context,
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
        target_identity_source=target_identity_source,
        signature_probe_artifact_hash=signature_probe_artifact_hash,
        signature_probe_artifact_hash_verified=(
            signature_probe_artifact_hash_verified
        ),
        target_artifact_lineage_verified=target_artifact_lineage_verified,
        source_candidate_artifact_path=source_candidate_artifact_path,
        signature_probe_artifact_path=signature_probe_artifact_path,
        source_theorem_signature_probe_artifact_path=(
            source_theorem_signature_probe_artifact_path
        ),
        proof_body_signature_probe_artifact_path=(
            proof_body_signature_probe_artifact_path
        ),
        candidate_artifact_path=str(candidate_artifact_path),
        execution_transcript_path=str(execution_transcript_path),
        live_goal_location_ready=live_goal_ready,
        candidate_live_proof_state_request=candidate_live_request,
        next_owner_subsystem=next_owner_subsystem,
        proofengineer_repair_context=proofengineer_repair_context,
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


def _proof_body_gate_open_for_kernel_repair(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> bool:
    return bool(
        row.proof_body_gate_status == "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
        and row.proof_body_goal_reached
        and row.source_theorem_kernel_evidence_eligible
        and not row.source_theorem_kernel_verified
        and not row.semantic_alignment_blockers
        and not row.formal_environment_placeholder_symbols
        and not row.formal_environment_typeclass_blockers
    )


def _proof_body_gate_open_target_names(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
) -> list[str]:
    names: list[str] = []
    for row in rows:
        if not _proof_body_gate_open_for_kernel_repair(row):
            continue
        name = (
            row.target_theorem_name
            or row.target_lean_declaration
            or next(iter(row.target_ids), "")
        )
        if name:
            names.append(str(name))
    return list(dict.fromkeys(names))


def _proof_body_gate_open_target_ids(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
) -> list[str]:
    target_ids: list[str] = []
    for row in rows:
        if not _proof_body_gate_open_for_kernel_repair(row):
            continue
        target_ids.extend(str(value) for value in row.target_ids if str(value).strip())
    return list(dict.fromkeys(target_ids))


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
    live_request = (
        row.get("live_proof_state_request", {})
        if isinstance(row.get("live_proof_state_request", {}), Mapping)
        else {}
    )
    for source in (row, live_request):
        for value in source.get("proof_body_attempts", []) or []:
            text = str(value).strip()
            if text:
                attempts.append(text)
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


def _external_proof_candidate_bodies(
    provider_result: Mapping[str, Any],
    *,
    max_candidates: int,
) -> tuple[str, ...]:
    raw = provider_result.get("source_theorem_candidate_proof_bodies", [])
    if not isinstance(raw, (list, tuple)):
        return ()
    bodies: list[str] = []
    for value in raw:
        body = str(value or "").strip()
        if body and body not in bodies:
            bodies.append(body)
        if len(bodies) >= max(0, int(max_candidates)):
            break
    return tuple(bodies)


def _normalize_external_proof_body(source: str) -> str:
    body = textwrap.dedent(str(source or "")).strip()
    if body.startswith(":= by"):
        body = body[len(":= by") :].strip()
    if body == "by":
        return ""
    if body.startswith("by\n"):
        body = textwrap.dedent(body.split("\n", 1)[1]).strip()
    elif body.startswith("by "):
        body = body[3:].strip()
    return body


def _external_proof_body_contract_errors(body: str) -> list[str]:
    errors: list[str] = []
    if not body:
        errors.append("external proof candidate body is empty")
        return errors
    if len(body) > 20000:
        errors.append("external proof candidate body exceeds 20000 characters")
    forbidden = [
        token
        for token in FORBIDDEN_ARTIFACT_TOKENS
        if re.search(r"\b" + re.escape(token) + r"\b", body, flags=re.I)
    ]
    if forbidden:
        errors.append(
            "external proof candidate contains forbidden tokens: "
            + ", ".join(forbidden)
        )
    if re.search(r"\b(?:by|exact)\?", body):
        errors.append("external proof candidate contains an interactive proof hole")
    if "```" in body:
        errors.append("external proof candidate contains fenced markdown")
    if re.search(
        r"(?m)^\s*(?:import|theorem|lemma|def|abbrev|opaque|instance|"
        r"axiom|constant|structure|class|inductive|namespace|section|end|"
        r"example|notation|infix|prefix|postfix|open|attribute|set_option|"
        r"macro|syntax|elab)\b",
        body,
    ):
        errors.append(
            "external proof candidate must be a proof body, not a declaration or module"
        )
    if re.search(r"(?m)^\s*#", body):
        errors.append("external proof candidate contains a command elaborator")
    if re.search(r"\brun_tac\b|\bIO\.(?:FS|Process)\b", body):
        errors.append(
            "external proof candidate contains a compile-time side-effect primitive"
        )
    return errors


def _external_exact_target_statement(
    source: str,
    *,
    target_declaration: str,
) -> str:
    block = _extract_lean_declaration_block(source, target_declaration)
    if not block:
        return ""
    proof_marker = _lean_top_level_proof_marker_span(block)
    if proof_marker is None:
        return ""
    return block[: proof_marker[0]].rstrip()


def _lean_top_level_proof_marker_span(source: str) -> tuple[int, int] | None:
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    block_comment_depth = 0
    in_line_comment = False
    in_string = False
    escaped = False
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            index += 1
            continue
        if block_comment_depth > 0:
            if char == "/" and next_char == "-":
                block_comment_depth += 1
                index += 2
                continue
            if char == "-" and next_char == "/":
                block_comment_depth -= 1
                index += 2
                continue
            index += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == "-" and next_char == "-":
            in_line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "-":
            block_comment_depth = 1
            index += 2
            continue
        if char == '"':
            in_string = True
            index += 1
            continue
        if char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth = max(0, brace_depth - 1)
        elif (
            char == ":"
            and next_char == "="
            and paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
        ):
            body_start = index + 2
            while body_start < len(source) and source[body_start].isspace():
                body_start += 1
            if source.startswith("by", body_start) and (
                body_start + 2 == len(source)
                or not (
                    source[body_start + 2].isalnum()
                    or source[body_start + 2] in {"_", "'"}
                )
            ):
                return index, body_start + 2
        index += 1
    return None


def _exact_target_statement_span(
    source: str,
    *,
    target_declaration: str,
    target_statement: str,
) -> tuple[int, int, int] | None:
    if not source or not target_declaration or not target_statement:
        return None
    declaration_span = _lean_declaration_span(source, target_declaration)
    if declaration_span is None:
        return None
    declaration_start, _ = declaration_span
    statement_start = declaration_start
    while statement_start < len(source) and source[statement_start] in {" ", "\t"}:
        statement_start += 1
    statement = target_statement.rstrip()
    if source[statement_start : statement_start + len(statement)] != statement:
        return None
    statement_end = statement_start + len(statement)
    marker_start = statement_end
    while marker_start < len(source) and source[marker_start].isspace():
        marker_start += 1
    if not source.startswith(":=", marker_start):
        return None
    body_start = marker_start + 2
    while body_start < len(source) and source[body_start].isspace():
        body_start += 1
    if not source.startswith("by", body_start) or (
        body_start + 2 < len(source)
        and (
            source[body_start + 2].isalnum()
            or source[body_start + 2] in {"_", "'"}
        )
    ):
        return None
    return statement_start, statement_end, body_start + 2


def _normalized_lean_signature(source: str) -> str:
    return re.sub(r"\s+", " ", str(source or "").strip())


EXACT_TARGET_STATEMENT_HASH_ALGORITHM = (
    "stable_hash:lean_whitespace_normalized_signature:v1"
)


def exact_target_statement_hash(source: str) -> str:
    """Return the shared identity hash for an exact Lean declaration signature."""

    return stable_hash(_normalized_lean_signature(source))


def _external_source_lineage_id(payload: Mapping[str, Any]) -> str:
    return "source_theorem_lineage:" + stable_hash(dict(payload))[:20]


def _external_candidate_lineage_errors(
    request: Mapping[str, Any],
    *,
    source: str,
    observed_statement: str,
    target_declaration: str,
    target_statement: str,
    source_candidate_path: Path,
) -> list[str]:
    errors: list[str] = []
    expected_declaration = str(
        request.get("expected_target_lean_declaration", "") or ""
    )
    if expected_declaration != target_declaration:
        errors.append(
            "expected_target_lean_declaration does not bind the exact declaration"
        )
    source_work_order_id = str(request.get("source_work_order_id", "") or "")
    execution_queue_id = str(request.get("execution_queue_id", "") or "")
    if not str(request.get("question_id", "") or ""):
        errors.append("question_id missing")
    if not str(request.get("source_task_id", "") or ""):
        errors.append("source_task_id missing")
    if not source_work_order_id:
        errors.append("source_work_order_id missing")
    if not execution_queue_id:
        errors.append("execution_queue_id missing")

    lineage_path_text = str(
        request.get("lineage_candidate_artifact_path", "") or ""
    )
    if not lineage_path_text:
        errors.append("lineage_candidate_artifact_path missing")
    else:
        try:
            lineage_path = Path(lineage_path_text).expanduser().resolve()
            observed_path = source_candidate_path.expanduser().resolve()
        except OSError:
            lineage_path = Path(lineage_path_text)
            observed_path = source_candidate_path
        if lineage_path != observed_path:
            errors.append(
                "lineage_candidate_artifact_path does not match the rerun source"
            )

    expected_source_hash = str(
        request.get("lineage_candidate_artifact_hash", "") or ""
    )
    if not expected_source_hash:
        errors.append("lineage_candidate_artifact_hash missing")
    elif expected_source_hash != stable_hash(source):
        errors.append("lineage candidate artifact content hash mismatch")

    declaration_source = _extract_lean_declaration_block(
        source,
        target_declaration,
    )
    expected_declaration_hash = str(
        request.get("target_declaration_source_hash", "") or ""
    )
    if not expected_declaration_hash:
        errors.append("target_declaration_source_hash missing")
    elif expected_declaration_hash != stable_hash(declaration_source):
        errors.append("target declaration source hash mismatch")

    expected_statement_hash = str(
        request.get("target_theorem_statement_hash", "") or ""
    )
    statement_hash_algorithm = str(
        request.get("target_theorem_statement_hash_algorithm", "") or ""
    )
    observed_statement_hash = exact_target_statement_hash(observed_statement)
    requested_statement_hash = exact_target_statement_hash(target_statement)
    if statement_hash_algorithm != EXACT_TARGET_STATEMENT_HASH_ALGORITHM:
        errors.append("target_theorem_statement_hash_algorithm mismatch")
    if not expected_statement_hash:
        errors.append("target_theorem_statement_hash missing")
    elif expected_statement_hash not in {
        observed_statement_hash,
        requested_statement_hash,
    }:
        errors.append("target theorem statement hash mismatch")

    probe_path_text = str(
        request.get("proof_body_signature_probe_artifact_path", "") or ""
    )
    expected_probe_hash = str(
        request.get("proof_body_signature_probe_artifact_hash", "") or ""
    )
    if not probe_path_text:
        errors.append("proof_body_signature_probe_artifact_path missing")
    elif not expected_probe_hash:
        errors.append("proof_body_signature_probe_artifact_hash missing")
    else:
        probe_path = Path(probe_path_text).expanduser()
        try:
            probe_source = probe_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(
                "proof-body signature probe artifact unreadable: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            if stable_hash(probe_source) != expected_probe_hash:
                errors.append("proof-body signature probe artifact hash mismatch")
            probe_statement = _external_exact_target_statement(
                probe_source,
                target_declaration=target_declaration,
            )
            if _normalized_lean_signature(probe_statement) != (
                _normalized_lean_signature(target_statement)
            ):
                errors.append(
                    "proof-body signature probe does not bind target_theorem_statement"
                )

    lineage_payload = {
        key: request.get(key)
        for key in (
            "source_work_order_id",
            "execution_queue_id",
            "lineage_candidate_artifact_path",
            "lineage_candidate_artifact_hash",
            "target_declaration_source_hash",
            "target_theorem_statement_hash",
            "target_theorem_statement_hash_algorithm",
            "proof_body_signature_probe_artifact_path",
            "proof_body_signature_probe_artifact_hash",
            "expected_target_lean_declaration",
            "target_lean_declaration",
            "target_ids",
        )
    }
    source_lineage_id = str(request.get("source_lineage_id", "") or "")
    if not source_lineage_id:
        errors.append("source_lineage_id missing")
    elif source_lineage_id != _external_source_lineage_id(lineage_payload):
        errors.append("source_lineage_id does not match the exact lineage payload")
    return errors


def _external_candidate_source_evidence_blockers(
    request: Mapping[str, Any],
    *,
    target_ids: tuple[str, ...],
    target_declaration: str,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not target_ids:
        blockers.append("target_ids missing")
    if not _bool_like(request.get("source_theorem_target_known", False)):
        blockers.append("source_theorem_target_known is false")
    if str(
        request.get("source_theorem_target_identity_status", "") or ""
    ) != "SOURCE_THEOREM_TARGET_KNOWN":
        blockers.append(
            "source_theorem_target_identity_status is not "
            "SOURCE_THEOREM_TARGET_KNOWN"
        )
    provenance = (
        request.get("source_theorem_target_provenance", {})
        if isinstance(
            request.get("source_theorem_target_provenance", {}),
            Mapping,
        )
        else {}
    )
    if str(provenance.get("target_lean_declaration", "") or "") != (
        target_declaration
    ):
        blockers.append(
            "source_theorem_target_provenance does not bind the exact declaration"
        )
    provenance_target_ids = _str_tuple(provenance.get("target_ids", []))
    if set(provenance_target_ids) != set(target_ids):
        blockers.append(
            "source_theorem_target_provenance does not bind the exact target_ids"
        )
    if not any(
        str(provenance.get(key, "") or "")
        for key in (
            "source_theorem_question_id",
            "question_id",
            "source_theorem_goal_id",
            "source_theorem_route_id",
        )
    ):
        blockers.append("source_theorem_target_provenance lacks a source identity")
    request_question_id = str(request.get("question_id", "") or "")
    provenance_question_id = str(
        provenance.get("source_theorem_question_id", "")
        or provenance.get("question_id", "")
        or ""
    )
    if request_question_id != provenance_question_id:
        blockers.append(
            "source_theorem_target_provenance question identity mismatch"
        )
    if str(provenance.get("source_work_order_id", "") or "") != str(
        request.get("source_work_order_id", "") or ""
    ):
        blockers.append(
            "source_theorem_target_provenance work-order identity mismatch"
        )
    if str(provenance.get("execution_queue_id", "") or "") != str(
        request.get("execution_queue_id", "") or ""
    ):
        blockers.append(
            "source_theorem_target_provenance execution-queue identity mismatch"
        )
    if str(request.get("target_identity_status", "") or "") != (
        "TARGET_DECLARATION_MATCHED"
    ):
        blockers.append("target_identity_status is not TARGET_DECLARATION_MATCHED")
    target_identity_errors = _str_tuple(request.get("target_identity_errors", []))
    if target_identity_errors:
        blockers.append("target_identity_errors are present")
    if not _bool_like(
        request.get("source_theorem_kernel_evidence_eligible", False)
    ):
        blockers.append("source_theorem_kernel_evidence_eligible is false")
    semantic_blockers = _str_tuple(
        request.get("semantic_alignment_blockers", [])
    )
    if semantic_blockers:
        blockers.append("semantic_alignment_blockers are unresolved")
    placeholder_symbols = _str_tuple(
        request.get("formal_environment_placeholder_symbols", [])
    )
    if placeholder_symbols:
        blockers.append("formal_environment_placeholder_symbols are unresolved")
    typeclass_blockers = _str_tuple(
        request.get("formal_environment_typeclass_blockers", [])
    )
    if typeclass_blockers:
        blockers.append("formal_environment_typeclass_blockers are unresolved")
    return tuple(blockers)


def materialize_external_exact_source_candidate(
    *,
    source: str,
    proof_body: str,
    support_assets: Any,
    target_declaration: str,
    target_statement: str,
) -> tuple[str, tuple[str, ...], tuple[str, ...], list[str]]:
    """Deterministically build the only candidate shape accepted by the rerun gate."""

    body = _normalize_external_proof_body(proof_body)
    errors = _external_proof_body_contract_errors(body)
    if errors:
        return "", (), (), errors
    candidate_source = _replace_exact_theorem_proof_body(
        source,
        declaration_name=target_declaration,
        tactic=body,
        target_statement=target_statement,
        exact_target_only=True,
    )
    if not candidate_source:
        return "", (), (), [
            "could not replace the exact theorem proof body conservatively"
        ]
    (
        candidate_source,
        materialized_names,
        materialized_hashes,
        support_errors,
    ) = _materialize_referenced_external_support_assets(
        candidate_source,
        proof_body=body,
        support_assets=support_assets,
        target_declaration=target_declaration,
    )
    errors.extend(support_errors)
    forbidden_source_tokens = [
        token
        for token in FORBIDDEN_ARTIFACT_TOKENS
        if re.search(
            r"\b" + re.escape(token) + r"\b",
            candidate_source,
            flags=re.I,
        )
    ]
    if forbidden_source_tokens:
        errors.append(
            "materialized exact candidate contains forbidden tokens: "
            + ", ".join(forbidden_source_tokens)
        )
    return (
        candidate_source,
        materialized_names,
        materialized_hashes,
        list(dict.fromkeys(errors)),
    )


def _materialize_referenced_external_support_assets(
    source: str,
    *,
    proof_body: str,
    support_assets: Any,
    target_declaration: str,
) -> tuple[str, tuple[str, ...], tuple[str, ...], list[str]]:
    if not isinstance(support_assets, (list, tuple)):
        return source, (), (), []
    assets_by_name: dict[str, Mapping[str, Any]] = {}
    duplicate_names: set[str] = set()
    asset_order: list[str] = []
    for raw_asset in support_assets[:16]:
        if not isinstance(raw_asset, Mapping):
            continue
        theorem_source = str(raw_asset.get("theorem_src", "") or "").strip()
        declared_names = re.findall(
            r"\b(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
            theorem_source,
        )
        asset_name = str(raw_asset.get("name", "") or "").strip()
        if not asset_name and len(declared_names) == 1:
            asset_name = declared_names[0]
        if not asset_name:
            continue
        if asset_name in assets_by_name:
            duplicate_names.add(asset_name)
            continue
        assets_by_name[asset_name] = raw_asset
        asset_order.append(asset_name)

    directly_referenced = [
        name
        for name in asset_order
        if _lean_identifier_referenced(proof_body, name)
    ]
    ordered_names: list[str] = []
    sanitized_sources: dict[str, str] = {}
    visited: set[str] = set()
    visiting: set[str] = set()
    errors: list[str] = []

    def visit(name: str) -> bool:
        if name in visited:
            return True
        if name in visiting:
            errors.append(
                f"referenced external support asset dependency cycle at {name}"
            )
            return False
        if name in duplicate_names:
            errors.append(
                f"referenced external support asset name is duplicated: {name}"
            )
            return False
        raw_asset = assets_by_name.get(name)
        if raw_asset is None:
            return False
        theorem_source, validation_errors = (
            _sanitized_external_support_theorem_source(
                raw_asset,
                asset_name=name,
                target_declaration=target_declaration,
            )
        )
        if validation_errors:
            errors.extend(validation_errors)
            return False
        sanitized_sources[name] = theorem_source
        visiting.add(name)
        dependencies_ok = True
        for dependency_name in asset_order:
            if dependency_name == name:
                continue
            if _lean_identifier_referenced(theorem_source, dependency_name):
                dependencies_ok = visit(dependency_name) and dependencies_ok
        visiting.remove(name)
        if dependencies_ok:
            visited.add(name)
            ordered_names.append(name)
        return dependencies_ok

    for name in directly_referenced:
        visit(name)

    materialized_names: list[str] = []
    materialized_hashes: list[str] = []
    updated = source
    for asset_name in ordered_names:
        theorem_source = sanitized_sources[asset_name]
        existing_source = _extract_lean_declaration_block(updated, asset_name)
        if existing_source:
            if _normalized_lean_signature(existing_source) != (
                _normalized_lean_signature(theorem_source)
            ):
                errors.append(
                    f"referenced external support asset {asset_name} collides with "
                    "a different existing declaration"
                )
                continue
            materialized_names.append(asset_name)
            materialized_hashes.append(stable_hash(theorem_source))
            continue
        inserted = _insert_before_lean_declaration(
            updated,
            declaration_name=target_declaration,
            insertion=theorem_source,
        )
        if inserted == updated:
            errors.append(
                f"could not materialize referenced external support asset {asset_name}"
            )
            continue
        updated = inserted
        materialized_names.append(asset_name)
        materialized_hashes.append(stable_hash(theorem_source))
    return (
        updated,
        tuple(materialized_names),
        tuple(materialized_hashes),
        errors,
    )


def _sanitized_external_support_theorem_source(
    raw_asset: Mapping[str, Any],
    *,
    asset_name: str,
    target_declaration: str,
) -> tuple[str, list[str]]:
    theorem_source = str(raw_asset.get("theorem_src", "") or "").strip()
    proof_body = _normalize_external_proof_body(
        str(raw_asset.get("proof", "") or "")
    )
    errors: list[str] = []
    if not theorem_source:
        return "", [
            f"referenced external support asset {asset_name} lacks theorem_src"
        ]
    if not proof_body:
        errors.append(
            f"referenced external support asset {asset_name} lacks structured proof"
        )
    declared_names = re.findall(
        r"\b(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
        theorem_source,
    )
    if len(declared_names) != 1 or declared_names[0] != asset_name:
        errors.append(
            "referenced external support asset declaration mismatch: "
            f"expected {asset_name}"
        )
    forbidden = [
        token
        for token in FORBIDDEN_ARTIFACT_TOKENS
        if re.search(
            r"\b" + re.escape(token) + r"\b",
            theorem_source,
            flags=re.I,
        )
    ]
    if forbidden:
        errors.append(
            f"referenced external support asset {asset_name} contains forbidden "
            "tokens: "
            + ", ".join(forbidden)
        )
    if re.search(r"(?m)^[ \t]*@\[", theorem_source):
        errors.append(
            f"referenced external support asset {asset_name} may not attach "
            "declaration attributes"
        )
    declaration_span = _lean_declaration_span(theorem_source, asset_name)
    if declaration_span is None or declaration_span[0] != 0:
        errors.append(
            f"referenced external support asset {asset_name} must begin with its "
            "theorem or lemma declaration"
        )
    proof_marker = _lean_top_level_proof_marker_span(theorem_source)
    if proof_marker is None:
        errors.append(
            f"referenced external support asset {asset_name} lacks a top-level "
            "`:= by` proof marker"
        )
        theorem_header = ""
        observed_proof_body = ""
    else:
        theorem_header = theorem_source[: proof_marker[0]].strip()
        observed_proof_body = _normalize_external_proof_body(
            theorem_source[proof_marker[1] :]
        )
        if _normalized_lean_signature(observed_proof_body) != (
            _normalized_lean_signature(proof_body)
        ):
            errors.append(
                f"referenced external support asset {asset_name} theorem_src "
                "does not match its structured proof field"
            )
    errors.extend(_external_proof_body_contract_errors(proof_body))
    if asset_name == target_declaration:
        errors.append(
            "referenced external support asset aliases the exact target declaration"
        )
    elif _lean_identifier_referenced(theorem_source, target_declaration):
        errors.append(
            f"referenced external support asset {asset_name} depends on the exact "
            "target declaration"
        )
    errors = list(dict.fromkeys(errors))
    if errors:
        return "", errors
    indented_proof = "\n".join(
        "  " + line if line else ""
        for line in textwrap.dedent(proof_body).strip().splitlines()
    )
    return theorem_header + " := by\n" + indented_proof + "\n", []


def _lean_identifier_referenced(source: str, name: str) -> bool:
    return bool(
        re.search(
            r"(?<![A-Za-z0-9_'])"
            + re.escape(name)
            + r"(?![A-Za-z0-9_'])",
            source,
        )
    )


def _replace_exact_theorem_proof_body(
    source: str,
    *,
    declaration_name: str,
    tactic: str,
    target_statement: str = "",
    exact_target_only: bool = False,
) -> str:
    if not source or not declaration_name or not tactic.strip():
        return ""
    normalized_tactic = textwrap.dedent(tactic).strip()
    if target_statement:
        exact_span = _exact_target_statement_span(
            source,
            target_declaration=declaration_name,
            target_statement=target_statement,
        )
        if exact_span is None:
            return ""
        theorem_start, statement_end, _ = exact_span
        indented_tactic = _indent_tactic_for_declaration(
            source,
            declaration_start=theorem_start,
            tactic=normalized_tactic,
        )
        replacement = (
            target_statement.rstrip()
            + " := by\n"
            + indented_tactic
            + "\n"
        )
        if exact_target_only:
            return source[:theorem_start] + replacement
    else:
        span = _lean_declaration_span(source, declaration_name)
        if span is None:
            return ""
        theorem_start, theorem_end = span
        declaration_source = source[theorem_start:theorem_end]
        proof_marker = _lean_top_level_proof_marker_span(declaration_source)
        if proof_marker is None:
            return ""
        statement_end = theorem_start + proof_marker[0]
        indented_tactic = _indent_tactic_for_declaration(
            source,
            declaration_start=theorem_start,
            tactic=normalized_tactic,
        )
        replacement = (
            source[theorem_start:statement_end].rstrip()
            + " := by\n"
            + indented_tactic
            + "\n"
        )
    span = _lean_declaration_span(source, declaration_name)
    if span is None:
        return ""
    _, theorem_end = span
    suffix = source[theorem_end:]
    if suffix and not suffix.startswith("\n"):
        replacement += "\n"
    return source[:theorem_start] + replacement + suffix


def _indent_tactic_for_declaration(
    source: str,
    *,
    declaration_start: int,
    tactic: str,
) -> str:
    line_start = source.rfind("\n", 0, declaration_start) + 1
    declaration_indent = source[line_start:declaration_start]
    if declaration_indent.strip():
        declaration_indent = ""
    tactic_indent = declaration_indent + "  "
    return "\n".join(
        tactic_indent + line if line else ""
        for line in tactic.splitlines()
    )


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


def _lean_declaration_span(
    source: str,
    declaration_name: str,
) -> tuple[int, int] | None:
    if not source or not declaration_name:
        return None
    declaration_head = (
        r"(?m)^(?P<indent>[ \t]*)(?:@\[[^\]\n]*\][ \t]*)*"
        r"(?:noncomputable[ \t]+)?(?:private[ \t]+)?"
        r"(?:theorem|lemma|def|abbrev)\s+"
        + re.escape(declaration_name)
        + r"\b"
    )
    matches = list(re.finditer(declaration_head, source))
    if len(matches) != 1:
        return None
    match = matches[0]
    declaration_start = _lean_attribute_prefix_start(
        source,
        command_start=match.start(),
        command_indent=len(match.group("indent").expandtabs(4)),
    )
    rest = source[match.end() :]
    declaration_indent = len(match.group("indent").expandtabs(4))
    next_command = next(
        (
            candidate
            for candidate in re.finditer(
                r"(?m)^(?P<indent>[ \t]*)(?:@\[[^\]\n]*\][ \t]*)*"
                r"(?:noncomputable[ \t]+)?(?:private[ \t]+)?"
                r"(?:theorem|lemma|def|abbrev|opaque|"
                r"instance|axiom|constant|structure|class|inductive|"
                r"namespace|section|end|open|attribute|set_option|macro|"
                r"syntax)\b",
                rest,
            )
            if len(candidate.group("indent").expandtabs(4))
            <= declaration_indent
        ),
        None,
    )
    if next_command is None:
        end = len(source)
    else:
        next_command_start = match.end() + next_command.start()
        end = _lean_attribute_prefix_start(
            source,
            command_start=next_command_start,
            command_indent=len(next_command.group("indent").expandtabs(4)),
        )
    return declaration_start, end


def _lean_attribute_prefix_start(
    source: str,
    *,
    command_start: int,
    command_indent: int,
) -> int:
    start = command_start
    while start > 0:
        previous_line_end = start - 1
        previous_line_start = source.rfind("\n", 0, previous_line_end) + 1
        previous_line = source[previous_line_start:previous_line_end].rstrip("\r")
        match = re.fullmatch(r"(?P<indent>[ \t]*)@\[[^\]\n]*\][ \t]*", previous_line)
        if match is None or len(match.group("indent").expandtabs(4)) != (
            command_indent
        ):
            break
        start = previous_line_start
    return start


def _extract_lean_declaration_block(source: str, declaration_name: str) -> str:
    span = _lean_declaration_span(source, declaration_name)
    if span is None:
        return ""
    start, end = span
    return source[start:end].strip()


def _proofengineer_whole_proof_repair_context(
    *,
    source: str,
    target_declaration: str,
    target_ids: tuple[str, ...],
    candidate_artifact_path: Path,
    source_candidate_artifact_path: str,
    proof_body_goal_excerpt: tuple[str, ...],
    proof_body_attempt_summaries: tuple[str, ...],
    semantic_alignment_constraints: tuple[str, ...],
    semantic_alignment_blockers: tuple[str, ...],
    source_theorem_target_known: bool = False,
    source_theorem_target_identity_status: str = "",
    source_theorem_target_provenance: Mapping[str, object] | None = None,
    expected_target_lean_declaration: str = "",
    source_work_order_id: str = "",
    execution_queue_id: str = "",
    signature_probe_artifact_path: str = "",
    source_theorem_signature_probe_artifact_path: str = "",
    proof_body_signature_probe_artifact_path: str = "",
    target_identity_status: str = "",
    target_identity_errors: tuple[str, ...] = (),
    target_identity_source: str = "",
    target_declaration_source_excerpt: str = "",
    target_declaration_source_hash: str = "",
    target_theorem_statement: str = "",
    current_proof_body_excerpt: str = "",
    source_theorem_kernel_evidence_eligible: bool = False,
    formal_environment_placeholder_symbols: tuple[str, ...] = (),
    formal_environment_typeclass_blockers: tuple[str, ...] = (),
    compiler_diagnostics: tuple[str, ...] = (),
    compiler_returncode: int = -1,
    compiler_checked: bool = False,
) -> dict[str, object]:
    if target_identity_source == (
        "upstream_structured_target_declaration_and_artifact_hash"
    ):
        declaration_source = target_declaration_source_excerpt
        target_statement = target_theorem_statement
        current_proof_body = current_proof_body_excerpt
    else:
        declaration_source = _extract_lean_declaration_block(
            source,
            target_declaration,
        )
        if not declaration_source:
            return {}
        proof_marker = _lean_top_level_proof_marker_span(declaration_source)
        if proof_marker is None:
            target_statement = declaration_source
            current_proof_body = ""
        else:
            target_statement = declaration_source[: proof_marker[0]].rstrip()
            current_proof_body = declaration_source[proof_marker[1] :].strip()
    normalized_provenance = dict(source_theorem_target_provenance or {})
    normalized_provenance.setdefault(
        "target_lean_declaration",
        target_declaration,
    )
    normalized_provenance.setdefault("target_ids", list(target_ids))
    normalized_provenance.setdefault("source_work_order_id", source_work_order_id)
    normalized_provenance.setdefault("execution_queue_id", execution_queue_id)
    lineage_candidate_artifact_hash = stable_hash(source)
    target_declaration_source_hash = (
        target_declaration_source_hash
        or (stable_hash(declaration_source) if declaration_source else "")
    )
    target_theorem_statement_hash = exact_target_statement_hash(target_statement)
    proof_body_probe_path = str(
        proof_body_signature_probe_artifact_path
        or source_theorem_signature_probe_artifact_path
        or signature_probe_artifact_path
        or ""
    )
    proof_body_probe_source = ""
    if proof_body_probe_path:
        try:
            proof_body_probe_source = Path(proof_body_probe_path).read_text(
                encoding="utf-8"
            )
        except OSError:
            proof_body_probe_source = ""
    proof_body_signature_probe_artifact_hash = (
        stable_hash(proof_body_probe_source) if proof_body_probe_source else ""
    )
    lineage_payload = {
        "source_work_order_id": source_work_order_id,
        "execution_queue_id": execution_queue_id,
        "lineage_candidate_artifact_path": str(candidate_artifact_path),
        "lineage_candidate_artifact_hash": lineage_candidate_artifact_hash,
        "target_declaration_source_hash": target_declaration_source_hash,
        "target_theorem_statement_hash": target_theorem_statement_hash,
        "target_theorem_statement_hash_algorithm": (
            EXACT_TARGET_STATEMENT_HASH_ALGORITHM
        ),
        "proof_body_signature_probe_artifact_path": proof_body_probe_path,
        "proof_body_signature_probe_artifact_hash": (
            proof_body_signature_probe_artifact_hash
        ),
        "expected_target_lean_declaration": (
            expected_target_lean_declaration or target_declaration
        ),
        "target_lean_declaration": target_declaration,
        "target_ids": list(target_ids),
    }
    return {
        "context_kind": "exact_source_theorem_whole_proof_repair",
        "owner_subsystem": "ProofEngineer",
        "repair_scope": "replace_entire_exact_declaration_proof_body",
        "target_lean_declaration": target_declaration,
        "target_ids": list(target_ids),
        "source_theorem_target_known": source_theorem_target_known,
        "source_theorem_target_identity_status": (
            source_theorem_target_identity_status
        ),
        "source_theorem_target_provenance": dict(
            normalized_provenance
        ),
        **lineage_payload,
        "source_lineage_id": _external_source_lineage_id(lineage_payload),
        "target_identity_status": target_identity_status,
        "target_identity_errors": list(target_identity_errors),
        "target_identity_source": target_identity_source,
        "source_theorem_kernel_evidence_eligible": (
            source_theorem_kernel_evidence_eligible
        ),
        "candidate_artifact_path": str(candidate_artifact_path),
        "source_candidate_artifact_path": source_candidate_artifact_path,
        "target_declaration_source_excerpt": declaration_source[:12000],
        "candidate_source_excerpt": source[:12000],
        "target_theorem_statement": target_statement[:9000],
        "current_proof_body_excerpt": current_proof_body[:6000],
        "candidate_imports": _lean_import_lines(source)[:16],
        "residual_goal_excerpt": list(proof_body_goal_excerpt)[:12],
        "residual_goal_role": (
            "Diagnostic subgoal produced after elaborating the current candidate proof. "
            "It is not an authoritative replacement for target_theorem_statement."
        ),
        "failed_proof_body_attempts": list(proof_body_attempt_summaries)[:8],
        "compiler_feedback": {
            "provider": "local.exact_source_theorem_proof_body_executor",
            "checked": bool(compiler_checked),
            "returncode": int(compiler_returncode),
            "diagnostics": list(compiler_diagnostics)[:24],
            "diagnostics_hash": stable_hash(list(compiler_diagnostics)),
            "candidate_artifact_hash": stable_hash(source),
            "role": (
                "Lean compiler diagnostics are repair observations for the next "
                "LLM/OpenProver turn, not handwritten proof-strategy rules and not "
                "proof evidence."
            ),
        },
        "proof_body_generation_contract": llm_proof_body_generation_contract(),
        "semantic_alignment_constraints": list(semantic_alignment_constraints)[:8],
        "semantic_alignment_blockers": list(semantic_alignment_blockers)[:8],
        "formal_environment_placeholder_symbols": list(
            formal_environment_placeholder_symbols
        )[:16],
        "formal_environment_typeclass_blockers": list(
            formal_environment_typeclass_blockers
        )[:16],
        "required_behavior": (
            "Preserve target_theorem_statement exactly, replace the entire proof body, "
            "and return a complete Lean declaration or a typed mathematical/formal-library "
            "blocker. Do not patch only a nested residual goal."
        ),
        "acceptance_gate": (
            "The exact declaration compiles under local Lean/AXLE with no forbidden "
            "placeholders and source_theorem_kernel_verified=true."
        ),
        "proof_evidence_status": "PROOFENGINEER_REPAIR_CONTEXT_NOT_PROOF_EVIDENCE",
    }


def _proof_body_next_owner_subsystem(
    *,
    source_theorem_kernel_verified: bool,
    proof_body_goal_reached: bool,
    semantic_alignment_blockers: tuple[str, ...],
    candidate_materialization_required: bool,
) -> str:
    if source_theorem_kernel_verified:
        return ""
    if semantic_alignment_blockers or candidate_materialization_required:
        return "Formalizer/ProofEngineer"
    if proof_body_goal_reached:
        return "ProofEngineer"
    return "Formalizer/ProofEngineer"


def _insert_before_lean_declaration(
    source: str,
    *,
    declaration_name: str,
    insertion: str,
) -> str:
    if not source or not declaration_name or not insertion.strip():
        return source
    span = _lean_declaration_span(source, declaration_name)
    if span is None:
        return source
    start, _ = span
    prefix = source[:start].rstrip()
    prefix_separator = "\n\n" if prefix else ""
    return (
        prefix
        + prefix_separator
        + insertion.strip()
        + "\n\n"
        + source[start:]
    )


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
    exact_semantic_context = _exact_semantic_definition_context(row)
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
    for key, value in exact_semantic_context.items():
        candidate_request.setdefault(key, value)
    candidate_request["exact_semantic_definition_context"] = exact_semantic_context
    proof_body_attempts = list(_proof_body_attempts(row))
    formal_environment_open = bool(
        placeholder_symbols or typeclass_blockers or semantic_alignment_blockers
    )
    calls = []
    for call in request.get("mcp_tool_calls", []) or []:
        if not isinstance(call, Mapping):
            continue
        cloned = dict(call)
        if (
            cloned.get("tool") == "lean_multi_attempt"
            and (formal_environment_open or not proof_body_attempts)
        ):
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
            or (
                "upstream_llm_or_prover_proposal"
                if proof_body_attempts
                else "llm_prover_generation_required"
            )
        )
    candidate_request["proof_body_generation_contract"] = (
        llm_proof_body_generation_contract()
    )
    candidate_request["proof_evidence_status"] = "LIVE_PROOF_STATE_REQUEST_NOT_PROOF_EVIDENCE"
    return candidate_request


def _exact_semantic_definition_context(row: Mapping[str, Any]) -> dict[str, object]:
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    nested_context = (
        row.get("exact_semantic_definition_context", {})
        if isinstance(row.get("exact_semantic_definition_context", {}), Mapping)
        else {}
    )
    nested_input_context = (
        input_summary.get("exact_semantic_definition_context", {})
        if isinstance(input_summary.get("exact_semantic_definition_context", {}), Mapping)
        else {}
    )
    sources: tuple[Mapping[str, Any], ...] = (
        row,
        input_summary,
        nested_context,
        nested_input_context,
    )
    context: dict[str, object] = {}
    for key in EXACT_SEMANTIC_DEFINITION_CONTEXT_KEYS:
        for source in sources:
            value = source.get(key, None)
            if value in (None, "", [], {}):
                continue
            if isinstance(value, Mapping):
                context[key] = dict(value)
            elif isinstance(value, list):
                context[key] = list(value)
            else:
                context[key] = value
            break
    normalize_exact_semantic_definition_signature_probe_context(
        context,
        row,
        input_summary,
        nested_context,
        nested_input_context,
    )
    return context


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
    target_ids: tuple[str, ...],
    target_lean_declaration: str,
    expected_target_lean_declaration: str,
    source_theorem_target_known: bool,
    source_theorem_target_identity_status: str,
    source_theorem_target_provenance: dict[str, object],
    semantic_alignment_constraints: tuple[str, ...],
    semantic_alignment_blockers: tuple[str, ...],
    exact_semantic_definition_context: dict[str, object],
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
    target_identity_source: str,
    signature_probe_artifact_hash: str,
    signature_probe_artifact_hash_verified: bool,
    target_artifact_lineage_verified: bool,
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
            "target_ids": target_ids,
            "target_lean_declaration": target_lean_declaration,
            "expected_target_lean_declaration": expected_target_lean_declaration,
            "source_theorem_target_known": source_theorem_target_known,
            "source_theorem_target_identity_status": (
                source_theorem_target_identity_status
            ),
            "source_theorem_target_provenance": source_theorem_target_provenance,
            "semantic_alignment_constraints": semantic_alignment_constraints,
            "semantic_alignment_blockers": semantic_alignment_blockers,
            "exact_semantic_definition_context": exact_semantic_definition_context,
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
            "target_identity_source": target_identity_source,
            "signature_probe_artifact_hash": signature_probe_artifact_hash,
            "signature_probe_artifact_hash_verified": (
                signature_probe_artifact_hash_verified
            ),
            "target_artifact_lineage_verified": (
                target_artifact_lineage_verified
            ),
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
        exact_semantic_context = dict(row.exact_semantic_definition_context)
        proof_body_gate_open = _proof_body_gate_open_for_kernel_repair(row)
        proof_body_gate_open_target_name = (
            row.target_theorem_name
            or row.target_lean_declaration
            or next(iter(row.target_ids), "")
        )
        learning_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "question_id": row.question_id,
                "question_title": row.question_title,
                "learning_task": "exact_source_theorem_proof_body_execution_feedback",
                "next_owner_subsystem": row.next_owner_subsystem,
                **exact_semantic_context,
                "target_theorem_name": row.target_theorem_name,
                "target_ids": list(row.target_ids),
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
                "source_candidate_artifact_path": row.source_candidate_artifact_path,
                "signature_probe_artifact_path": row.signature_probe_artifact_path,
                "source_theorem_signature_probe_artifact_path": (
                    row.source_theorem_signature_probe_artifact_path
                    or row.signature_probe_artifact_path
                ),
                "proof_body_signature_probe_artifact_path": (
                    row.proof_body_signature_probe_artifact_path
                    or row.source_theorem_signature_probe_artifact_path
                    or row.signature_probe_artifact_path
                ),
                "candidate_artifact_path": row.candidate_artifact_path,
                "execution_transcript_path": row.execution_transcript_path,
                "proofengineer_repair_context": row.proofengineer_repair_context,
                "runtime_queue_status": _runtime_learning_queue_status(row),
                "candidate_materialization_required": (
                    _row_requires_source_candidate_materialization(row)
                ),
                "candidate_materialization_statuses": list(
                    _source_candidate_materialization_statuses(row)
                ),
                "candidate_materialization_contract": (
                    SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_CONTRACT
                    if _row_requires_source_candidate_materialization(row)
                    else ""
                ),
                "exact_semantic_definition_context": exact_semantic_context,
                "missing_formal_symbols": list(
                    row.formal_environment_placeholder_symbols
                ),
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
                "source_theorem_exact_proof_body_reached": (
                    row.proof_body_goal_reached
                ),
                "proof_body_goal_excerpt": list(row.proof_body_goal_excerpt),
                "proof_body_gate_status": row.proof_body_gate_status,
                "source_theorem_exact_proof_body_gate_open_for_kernel_repair": (
                    proof_body_gate_open
                ),
                "source_theorem_exact_proof_body_gate_open_target_names": (
                    [str(proof_body_gate_open_target_name)]
                    if proof_body_gate_open and proof_body_gate_open_target_name
                    else []
                ),
                "source_theorem_exact_proof_body_gate_open_target_ids": (
                    list(row.target_ids) if proof_body_gate_open else []
                ),
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
        "n_runtime_learning_rows_from_pseudo_formal": sum(
            1 for row in rows if _row_has_pseudo_formal_origin(row)
        ),
        "n_runtime_learning_rows_from_formalizer_pf_component_gate": sum(
            1 for row in rows if _row_has_formalizer_pf_component_gate_origin(row)
        ),
        "n_source_theorem_kernel_verified_from_pseudo_formal": sum(
            1
            for row in rows
            if row.source_theorem_kernel_verified
            and _row_has_pseudo_formal_origin(row)
        ),
        "n_source_theorem_kernel_verified_from_formalizer_pf_component_gate": sum(
            1
            for row in rows
            if row.source_theorem_kernel_verified
            and _row_has_formalizer_pf_component_gate_origin(row)
        ),
        "source_pseudo_formal_work_order_ids": _source_pseudo_formal_ids(
            rows,
            "source_pseudo_formal_work_order_id",
        ),
        "source_pseudo_formal_block_ids": _source_pseudo_formal_ids(
            rows,
            "source_pseudo_formal_block_id",
        ),
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": (
            _formalizer_pf_component_gate_exact_rows_jsonl_paths(rows)
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
        "n_exact_semantic_definition_context_rows": sum(
            1 for row in rows if row.exact_semantic_definition_context
        ),
        "n_proof_body_signature_probe_artifact_rows": sum(
            1 for row in rows if row.proof_body_signature_probe_artifact_path
        ),
        "proof_body_signature_probe_artifact_paths": list(
            dict.fromkeys(
                row.proof_body_signature_probe_artifact_path
                for row in rows
                if row.proof_body_signature_probe_artifact_path
            )
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
        "verified_source_to_bridge_premise_derivation_artifact_paths": (
            _verified_source_to_bridge_premise_derivation_artifact_paths(rows)
        ),
        "verified_source_to_bridge_premise_derivation_declarations": (
            _verified_source_to_bridge_premise_derivation_declarations(rows)
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
        "n_proof_body_gate_open_for_kernel_repair": sum(
            1 for row in rows if _proof_body_gate_open_for_kernel_repair(row)
        ),
        "proof_body_gate_open_target_names": _proof_body_gate_open_target_names(rows),
        "proof_body_gate_open_target_ids": _proof_body_gate_open_target_ids(rows),
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
        "n_runtime_learning_rows_from_pseudo_formal": manifest[
            "n_runtime_learning_rows_from_pseudo_formal"
        ],
        "n_runtime_learning_rows_from_formalizer_pf_component_gate": manifest[
            "n_runtime_learning_rows_from_formalizer_pf_component_gate"
        ],
        "n_source_theorem_kernel_verified_from_pseudo_formal": manifest[
            "n_source_theorem_kernel_verified_from_pseudo_formal"
        ],
        "n_source_theorem_kernel_verified_from_formalizer_pf_component_gate": manifest[
            "n_source_theorem_kernel_verified_from_formalizer_pf_component_gate"
        ],
        "source_pseudo_formal_work_order_ids": manifest[
            "source_pseudo_formal_work_order_ids"
        ],
        "source_pseudo_formal_block_ids": manifest[
            "source_pseudo_formal_block_ids"
        ],
        "formalizer_pf_component_gate_exact_rows_jsonl_paths": manifest[
            "formalizer_pf_component_gate_exact_rows_jsonl_paths"
        ],
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
        "n_exact_semantic_definition_context_rows": manifest[
            "n_exact_semantic_definition_context_rows"
        ],
        "n_proof_body_signature_probe_artifact_rows": manifest[
            "n_proof_body_signature_probe_artifact_rows"
        ],
        "proof_body_signature_probe_artifact_paths": manifest[
            "proof_body_signature_probe_artifact_paths"
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
        "n_proof_body_gate_open_for_kernel_repair": manifest[
            "n_proof_body_gate_open_for_kernel_repair"
        ],
        "proof_body_gate_open_target_names": manifest[
            "proof_body_gate_open_target_names"
        ],
        "proof_body_gate_open_target_ids": manifest[
            "proof_body_gate_open_target_ids"
        ],
        "source_theorem_route_ids": manifest["source_theorem_route_ids"],
        "proof_evidence_status": manifest["proof_evidence_status"],
    }


def _runtime_learning_queue_status(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> str:
    if row.source_theorem_kernel_verified:
        return "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
    if _row_requires_source_candidate_materialization(row):
        return "PENDING_EXACT_SOURCE_THEOREM_CANDIDATE_MATERIALIZATION"
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
    if _row_requires_source_candidate_materialization(row):
        return (
            "Route back to exact source-theorem candidate materialization: produce "
            "a runnable Lean artifact, signature probe, and live proof-body location "
            "before retrying exact proof-body execution."
        )
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
        return exact_semantic_definition_proof_body_adapter_synthesis_instruction()
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
            "Route to ProofEngineer with the lineage-bound whole-declaration repair context. "
            "Preserve the exact theorem statement, replace the entire candidate proof "
            "body, and use the reached residual goal, failed attempts, and diagnostics "
            "as observations rather than treating a nested residual goal as the theorem."
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
    if _row_requires_source_candidate_materialization(row):
        return "EXACT_SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED"
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
    if _row_requires_source_candidate_materialization(row):
        return (
            "Use this as source-theorem candidate materialization feedback. The "
            "proof-body executor cannot run until a concrete exact-source Lean "
            "candidate and signature probe have been materialized; this is not "
            "proof evidence and should not trigger blind proof-body search."
        )
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
        "Use this as ProofEngineer runtime feedback and treat "
        "proofengineer_repair_context as the authoritative lineage-bound repair task. "
        "Preserve target_theorem_statement and replace the whole proof body; "
        "proof_body_goal_excerpt is a diagnostic residual subgoal, not a replacement "
        "theorem target. Do not count the candidate as source-theorem proof unless "
        "source_theorem_kernel_verified=true."
    )


def _runtime_learning_acceptance_gate(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> str:
    if _row_requires_source_candidate_materialization(row):
        return SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_CONTRACT
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
    if _source_candidate_materialization_required_errors(errors):
        return SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE
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


def _source_candidate_materialization_required_errors(
    errors: tuple[str, ...] | list[str],
) -> bool:
    text = "\n".join(str(error).lower() for error in errors)
    return bool(
        "execution queue row is not ready for exact source proof-body work" in text
        or "signature_probe_artifact_path missing" in text
        or "signature probe artifact missing" in text
        or "target_lean_declaration missing" in text
    )


def _source_candidate_materialization_statuses(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> tuple[str, ...]:
    statuses: list[str] = []
    error_text = "\n".join(str(error).lower() for error in row.errors)
    if "execution queue row is not ready for exact source proof-body work" in error_text:
        statuses.append("EXACT_SOURCE_PROOF_BODY_QUEUE_NOT_READY")
    if "target_lean_declaration missing" in error_text:
        statuses.append("EXACT_SOURCE_THEOREM_TARGET_LOCATION_MISSING")
    if "signature_probe_artifact_path missing" in error_text:
        statuses.append("SIGNATURE_PROBE_ARTIFACT_PATH_MISSING")
    if "signature probe artifact missing" in error_text:
        statuses.append("SIGNATURE_PROBE_ARTIFACT_NOT_FOUND")
    return tuple(dict.fromkeys(statuses))


def _row_requires_source_candidate_materialization(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> bool:
    return bool(
        row.failure_classification
        in {
            SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED_FAILURE,
            "source_theorem_candidate_artifact_missing",
        }
        or _source_candidate_materialization_required_errors(row.errors)
    )


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
    inferred_failure_classification = failure_classification
    if (
        failure_classification == "proof_body_verified_adapter_context_insufficient"
        or _proof_body_verified_adapter_context_insufficient(
            proof_body_attempt_summaries,
            verified_adapter_declarations=verified_adapter_declarations,
        )
    ):
        inferred_failure_classification = (
            "proof_body_verified_adapter_context_insufficient"
        )
    return _policy_goal_obligations_from_feedback(
        failure_classification=inferred_failure_classification,
        goal_text=text,
    )


def _exact_goal_shape_obligation_description(obligation_id: str) -> str:
    description = _policy_goal_obligation_gap(obligation_id)
    if description:
        return description
    return (
        "Repair an exact source theorem goal-shape obligation before rerunning "
        "local Lean."
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


def _semantic_alignment_constraint_is_nonblocking_review_context(text: str) -> bool:
    lowered = text.lower()
    if lowered.startswith("unreviewed synthesized definition review note:"):
        return True
    if (
        ("no sorry" in lowered or "do not add sorry" in lowered)
        and "admit" in lowered
        and "unsafe" in lowered
    ):
        return True
    if (
        "proof body is a proposal" in lowered
        and "kernel verification required" in lowered
    ):
        return True
    return False


def _semantic_alignment_constraints_block_source_kernel(
    constraints: tuple[str, ...],
    *,
    explicit_blockers: tuple[str, ...] = (),
    semantic_review_approved: bool = False,
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
    for blocker in explicit_blockers:
        text = str(blocker).strip()
        if text and not _semantic_alignment_constraint_is_nonblocking_review_context(text):
            blockers.append(text)
    if semantic_review_approved:
        return tuple(dict.fromkeys(blockers))
    for constraint in constraints:
        text = str(constraint).strip()
        lowered = text.lower()
        if _semantic_alignment_constraint_is_nonblocking_review_context(text):
            continue
        if any(marker in lowered for marker in blocking_markers):
            blockers.append(text)
    return tuple(dict.fromkeys(blockers))


def _row_has_reviewed_exact_semantic_definition_approval(row: Mapping[str, Any]) -> bool:
    already_repaired = row.get("already_repaired_environment", {})
    already_repaired_mapping = (
        already_repaired if isinstance(already_repaired, Mapping) else {}
    )
    modes = {
        str(value).strip()
        for value in [
            *list(row.get("definition_candidate_review_modes", []) or []),
            *list(
                already_repaired_mapping.get("definition_candidate_review_modes", [])
                or []
            ),
        ]
        if str(value).strip()
    }
    if "typechecked_candidate_source_semantic_review_approved" in modes:
        return True
    if str(row.get("semantic_review_decision", "") or "").strip() == (
        "approved_definition_candidate"
    ):
        return True
    if str(row.get("semantic_review_status", "") or "").strip() == (
        "verifier_gate_approved_definition_candidate_not_proof"
    ):
        return True
    reviewed_paths = [
        str(row.get("reviewed_exact_semantic_definition_artifact_path", "") or ""),
        *[
            str(value)
            for value in row.get("reviewed_exact_semantic_definition_artifact_paths", [])
            or []
        ],
    ]
    has_reviewed_path = any(value.strip() for value in reviewed_paths)
    constraints = [
        str(value).lower()
        for value in row.get("semantic_alignment_constraints", []) or []
    ]
    if has_reviewed_path and any(
        "reviewed exact semantic-definition candidate approved" in value
        for value in constraints
    ):
        return True
    return False


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


def _proof_body_target_ids(
    row: Mapping[str, Any],
    *,
    fallback_target: str = "",
) -> tuple[str, ...]:
    input_summary = (
        row.get("input_summary", {})
        if isinstance(row.get("input_summary", {}), Mapping)
        else {}
    )
    raw_values = (
        row.get("target_ids", [])
        or row.get("target_id", "")
        or row.get("target_theorem_goal_ids", [])
        or row.get("source_theorem_exact_proof_body_repair_target_names", [])
        or input_summary.get("target_ids", [])
        or input_summary.get("target_id", "")
        or input_summary.get("target_theorem_goal_ids", [])
        or input_summary.get("source_theorem_exact_proof_body_repair_target_names", [])
        or []
    )
    if isinstance(raw_values, Mapping):
        values = [str(key).strip() for key in raw_values.keys()]
    elif isinstance(raw_values, str):
        values = [raw_values.strip()]
    elif isinstance(raw_values, (list, tuple, set)):
        values = [str(value).strip() for value in raw_values]
    else:
        values = [str(raw_values).strip()]
    target_ids = [value for value in values if value]
    fallback = str(fallback_target or "").strip()
    if not target_ids and fallback:
        target_ids = [fallback]
    return tuple(dict.fromkeys(target_ids))


def _dominant_failure_classification(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
) -> str:
    failures = Counter(row.failure_classification for row in rows if row.failure_classification)
    if not failures:
        return ""
    return failures.most_common(1)[0][0]


def _row_has_pseudo_formal_origin(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> bool:
    return bool(
        str(
            row.exact_semantic_definition_context.get(
                "source_pseudo_formal_work_order_id",
                "",
            )
            or ""
        ).strip()
        or _row_has_formalizer_pf_component_gate_origin(row)
    )


def _row_has_formalizer_pf_component_gate_origin(
    row: ExactSourceTheoremProofBodyExecutionResultRow,
) -> bool:
    return (
        str(
            row.exact_semantic_definition_context.get("source_component_gate", "") or ""
        ).strip()
        == "formalizer_pseudo_formal_packet_component_gate"
    )


def _source_pseudo_formal_ids(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
    key: str,
) -> list[str]:
    return list(
        dict.fromkeys(
            str(row.exact_semantic_definition_context.get(key, "") or "")
            for row in rows
            if str(row.exact_semantic_definition_context.get(key, "") or "").strip()
        )
    )


def _formalizer_pf_component_gate_exact_rows_jsonl_paths(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
) -> list[str]:
    paths: list[str] = []
    for row in rows:
        if not _row_has_formalizer_pf_component_gate_origin(row):
            continue
        path = str(
            row.exact_semantic_definition_context.get(
                "source_component_gate_exact_rows_jsonl",
                "",
            )
            or ""
        ).strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def _verified_source_to_bridge_premise_derivation_artifact_paths(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
) -> list[str]:
    return list(
        dict.fromkeys(
            path
            for row in rows
            for path in row.verified_source_to_bridge_premise_derivation_artifact_paths
            if str(path).strip()
        )
    )


def _verified_source_to_bridge_premise_derivation_declarations(
    rows: list[ExactSourceTheoremProofBodyExecutionResultRow],
) -> list[str]:
    return list(
        dict.fromkeys(
            declaration
            for row in rows
            for declaration in row.verified_source_to_bridge_premise_derivation_declarations
            if str(declaration).strip()
        )
    )


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
