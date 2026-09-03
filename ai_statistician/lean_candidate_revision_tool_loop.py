from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY,
    CLIENT_TOOL_RECENT_HISTORY_ROUNDS,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    apply_model_exact_text_edits,
    client_tool_authorization_fingerprint,
    model_exact_text_edits_json_schema,
    persist_client_tool_session,
    resume_client_tool_session_from_checkpoint,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .lean_project import (
    MAX_LEAN_PROJECT_FILE_BYTES,
    LeanProjectFile,
    lean_project_build_order_errors,
    lean_project_hash,
    load_model_authored_lean_project,
    model_authored_lean_project,
    normalized_lean_project_files,
    persist_model_authored_lean_project,
)
from .structured_output_retry import PacketValidationError
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from . import theory_workspace as theory_documents


LeanCandidateCheck = Callable[[str, str], Mapping[str, Any]]
LeanCandidateProjectCheck = Callable[
    [str, str, Sequence[Mapping[str, Any]], Sequence[str]], Mapping[str, Any]
]
LeanSupportFileCheck = Callable[
    [str, Sequence[Mapping[str, Any]], Sequence[str]], Mapping[str, Any]
]
FormalEnvironmentSearch = Callable[[str, int], Any]
ProofCandidateSearch = Callable[[str, str, int, Mapping[str, Any]], Any]
LeanStateInspection = Callable[[str, Mapping[str, Any]], Any]
LeanDeclarationInspection = Callable[
    [str, str, int, Mapping[str, Any]], Any
]
LEAN_SOURCE_SUBMISSION_TOOL = "submit_lean_source"
LEAN_SOURCE_EDIT_TOOL = "edit_current_lean_source"
LEAN_SOURCE_READ_TOOL = "read_current_lean_source"
LEAN_SUPPORT_FILE_WRITE_TOOL = "write_lean_support_file"
LEAN_SUPPORT_FILE_EDIT_TOOL = "edit_lean_support_file"
LEAN_SUPPORT_FILE_READ_TOOL = "read_lean_support_file"
LEAN_SUPPORT_FILE_REMOVE_TOOL = "remove_lean_support_file"
LEAN_SUPPORT_FILE_CHECK_TOOL = "check_lean_support_file"
LEAN_SCRATCH_TOOL = "run_lean_scratch"
LEAN_FORMAL_GAP_TOOL = "report_formal_gap"
LEAN_CANDIDATE_WORKSPACE_CHECKPOINT_KIND = (
    "LeanCandidateWorkspaceRecoveryCheckpoint"
)
_LEAN_WORKSPACE_COUNTER_FIELDS = (
    "source_updates",
    "declaration_updates",
    "source_reads",
    "support_file_writes",
    "support_file_edits",
    "support_file_reads",
    "support_file_removals",
    "support_file_checks",
    "searches",
    "proof_searches",
    "state_inspections",
    "declaration_inspections",
    "scratch_checks",
    "checks",
)
_LEAN_WORKSPACE_OBSERVATION_FIELDS = (
    "latest_check_observation",
    "latest_formal_environment_search",
    "latest_proof_search",
    "latest_state_inspection",
    "latest_declaration_inspection",
    "latest_support_file_check",
    "theory_document_inspection_refs",
)


@dataclass(frozen=True)
class LeanCandidateRevisionToolLoopResult:
    lean_source: str
    source_hash: str
    candidate_lean_declaration: str
    disposition: str
    formal_gap: Mapping[str, Any]
    check_result: Mapping[str, Any]
    lean_project: Mapping[str, Any]
    evidence: Mapping[str, Any]


def _apply_exact_source_edit(
    source: str,
    *,
    edits: Any,
) -> tuple[str, dict[str, Any]]:
    """Materialize one model-authored atomic edit batch without parsing Lean."""

    if not source.strip():
        raise ClientToolInputError(
            "edit_current_lean_source requires an existing current source; use "
            "submit_lean_source for initial authoring"
        )
    updated, metadata = apply_model_exact_text_edits(
        source,
        edits=edits,
        replacement_key="new_text",
    )
    if len(updated) > 20_000:
        raise ClientToolInputError(
            "edited Lean source exceeds the runtime artifact-size boundary"
        )
    return updated, {"n_edits": len(metadata), "edits": metadata}


def seal_lean_candidate_workspace_checkpoint(
    checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind a complete Lean workspace checkpoint to all of its exact fields."""

    body = deepcopy(dict(checkpoint))
    body.pop("checkpoint_id", None)
    return {
        **body,
        "checkpoint_id": (
            "lean_candidate_workspace_checkpoint:" + stable_hash(body)[:20]
        ),
    }


def _lean_workspace_checkpoint_identity_errors(
    checkpoint: Mapping[str, Any],
    *,
    candidate_id: str | None = None,
    parent_candidate_lean_declaration: str | None = None,
    parent_source: str | None = None,
    rejected_source_hash: str | None = None,
    rejected_lean_project_hash: str | None = None,
    require_resumable: bool = True,
) -> list[str]:
    errors: list[str] = []
    if checkpoint.get("artifact_kind") != LEAN_CANDIDATE_WORKSPACE_CHECKPOINT_KIND:
        errors.append("checkpoint artifact kind is not the canonical Lean workspace kind")
    checkpoint_schema = checkpoint.get("schema_version")
    if checkpoint_schema not in {2, 3}:
        errors.append("checkpoint schema version is not supported")
    checkpoint_id = str(checkpoint.get("checkpoint_id", "") or "").strip()
    expected_checkpoint = seal_lean_candidate_workspace_checkpoint(checkpoint)
    if checkpoint_id != expected_checkpoint["checkpoint_id"]:
        errors.append("checkpoint content identity is missing or stale")
    if candidate_id is not None and str(
        checkpoint.get("candidate_id", "") or ""
    ) != str(candidate_id):
        errors.append("checkpoint candidate id does not match the active workspace")
    if not str(checkpoint.get("candidate_id", "") or "").strip():
        errors.append("checkpoint candidate id is empty")
    if parent_candidate_lean_declaration is not None and str(
        checkpoint.get("parent_candidate_lean_declaration", "") or ""
    ).strip() != str(parent_candidate_lean_declaration).strip():
        errors.append("checkpoint parent declaration does not match the active workspace")
    if parent_source is not None and str(
        checkpoint.get("parent_source_hash", "") or ""
    ) != stable_hash(parent_source):
        errors.append("checkpoint parent source hash does not match the active workspace")
    if rejected_source_hash is not None and str(
        checkpoint.get("rejected_source_hash", "") or ""
    ).strip() != str(rejected_source_hash or "").strip():
        errors.append("checkpoint rejected-source binding changed across continuation")
    if rejected_lean_project_hash is not None and str(
        checkpoint.get("rejected_lean_project_hash", "") or ""
    ).strip() != str(rejected_lean_project_hash or "").strip():
        errors.append("checkpoint rejected-project binding changed across continuation")

    source = str(checkpoint.get("current_source", "") or "")
    source_hash = str(checkpoint.get("current_source_hash", "") or "")
    declaration = str(
        checkpoint.get("candidate_lean_declaration", "") or ""
    ).strip()
    workspace_phase = str(checkpoint.get("workspace_phase", "") or "")
    if workspace_phase not in {"initial_authoring", "revision"}:
        errors.append("checkpoint workspace phase is invalid")
    if not str(checkpoint.get("parent_source_hash", "") or ""):
        errors.append("checkpoint parent source hash is empty")
    if parent_source is not None:
        expected_phase = "revision" if parent_source.strip() else "initial_authoring"
        if workspace_phase != expected_phase:
            errors.append("checkpoint workspace phase changed across continuation")
    empty_initial_checkpoint = bool(
        not source.strip()
        and source_hash == stable_hash("")
        and workspace_phase == "initial_authoring"
    )
    if source_hash != stable_hash(source):
        errors.append("checkpoint current source hash is stale")
    if not source.strip() and not empty_initial_checkpoint:
        errors.append("checkpoint current source is empty outside initial authoring")
    if len(source) > 20000:
        errors.append("checkpoint current source exceeds the artifact-size boundary")
    if source.strip() and not declaration:
        errors.append("checkpoint source has no model-selected Lean declaration")
    support_files: tuple[LeanProjectFile, ...] = ()
    support_build_order: tuple[str, ...] = ()
    try:
        support_files = normalized_lean_project_files(
            checkpoint.get("support_files", [])
        )
        support_build_order = tuple(
            checkpoint.get("support_build_order", []) or []
        )
        errors.extend(
            lean_project_build_order_errors(
                support_build_order,
                project_files=support_files,
                require_complete=False,
            )
        )
    except ValueError as exc:
        errors.append(str(exc))
    if checkpoint_schema == 2 and (support_files or support_build_order):
        errors.append("legacy Lean checkpoint cannot contain project support files")
    if checkpoint.get("model_owned_lean_code") is not bool(
        source.strip() or support_files
    ):
        errors.append("checkpoint model-owned source boundary is inconsistent")
    if (
        checkpoint.get("runtime_selected_lean_code") is not False
        or checkpoint.get("kernel_verified") is not False
        or checkpoint.get("accepted") is not False
    ):
        errors.append("checkpoint crosses the runtime or proof-evidence boundary")

    counters: dict[str, int] = {}
    starts = checkpoint.get("segment_start_counters", {})
    if not isinstance(starts, Mapping):
        starts = {}
        errors.append("checkpoint segment-start counters are malformed")
    for field in _LEAN_WORKSPACE_COUNTER_FIELDS:
        value = checkpoint.get(field, 0)
        start = starts.get(field, 0)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or isinstance(start, bool)
            or not isinstance(start, int)
            or start < 0
            or start > value
        ):
            errors.append(f"checkpoint {field} counter lineage is invalid")
            continue
        counters[field] = value

    checked_rows = checkpoint.get("checked_candidate_keys", [])
    checked_keys: set[tuple[str, str, str]] = set()
    empty_project_hash = lean_project_hash(
        target_source=source,
        project_files=(),
        support_build_order=(),
    )
    if not isinstance(checked_rows, list):
        errors.append("checkpoint checked Lean candidates are malformed")
    else:
        for row in checked_rows:
            expected_fields = (
                {"source_hash", "candidate_lean_declaration"}
                if checkpoint_schema == 2
                else {
                    "source_hash",
                    "candidate_lean_declaration",
                    "lean_project_hash",
                }
            )
            if not isinstance(row, Mapping) or set(row) != expected_fields:
                errors.append("checkpoint contains an invalid checked Lean candidate")
                continue
            key = (
                str(row.get("source_hash", "") or ""),
                str(row.get("candidate_lean_declaration", "") or "").strip(),
                str(row.get("lean_project_hash", "") or empty_project_hash),
            )
            if not key[0] or not key[1] or not key[2] or key in checked_keys:
                errors.append("checkpoint checked Lean candidate identity is invalid")
                continue
            checked_keys.add(key)
    if "checks" in counters and counters["checks"] != len(checked_keys):
        errors.append("checkpoint check count does not match checked candidates")

    last_check = checkpoint.get("last_check", {})
    if not isinstance(last_check, Mapping):
        last_check = {}
        errors.append("checkpoint last Lean check is malformed")
    last_check = dict(last_check)
    if stable_hash(last_check) != str(
        checkpoint.get("last_check_hash", "") or ""
    ):
        errors.append("checkpoint last Lean check identity is stale")
    if last_check:
        if not counters.get("checks", 0):
            errors.append("checkpoint has a Lean check without a recorded check action")
        if (
            str(last_check.get("source_hash", "") or "") != source_hash
            or (
                source_hash,
                declaration,
                str(
                    last_check.get("lean_project_hash", "")
                    or empty_project_hash
                ),
            )
            not in checked_keys
        ):
            errors.append("checkpoint last Lean check is not bound to current source")
        latest_check = checkpoint.get("latest_check_observation", {})
        if not isinstance(latest_check, Mapping) or stable_hash(dict(latest_check)) != (
            stable_hash(last_check)
        ):
            errors.append("checkpoint latest Lean diagnostic is not exact")
    elif checkpoint_schema == 2 and counters.get("checks", 0):
        errors.append("legacy checkpoint lost its current Lean diagnostic")
    elif checkpoint.get("latest_check_observation", {}):
        errors.append("checkpoint retained a stale current Lean diagnostic")
    fingerprints = checkpoint.get("workspace_observation_fingerprints", [])
    if (
        not isinstance(fingerprints, list)
        or any(not isinstance(value, str) or not value for value in fingerprints)
        or len(fingerprints) != len(set(fingerprints))
    ):
        errors.append("checkpoint workspace observation identities are malformed")
        fingerprints = []
    if last_check:
        check_fingerprint_material = {
            "source_hash": source_hash,
            "candidate_lean_declaration": declaration,
            "check_result": last_check,
        }
        if checkpoint_schema == 3:
            check_fingerprint_material["lean_project_hash"] = str(
                last_check.get("lean_project_hash", "")
                or empty_project_hash
            )
        check_fingerprint = "lean-check:" + stable_hash(
            check_fingerprint_material
        )
        if check_fingerprint not in fingerprints:
            errors.append("checkpoint current Lean check observation is untracked")
    segment_start = checkpoint.get("segment_start_observation_count", 0)
    if (
        isinstance(segment_start, bool)
        or not isinstance(segment_start, int)
        or segment_start < 0
        or segment_start > len(fingerprints)
    ):
        errors.append("checkpoint segment observation boundary is invalid")
        segment_start = len(fingerprints)
    new_progress = len(fingerprints) > segment_start
    if checkpoint.get("resumable") is not new_progress:
        errors.append("checkpoint resumable status does not match observed progress")
    if checkpoint.get("model_owned_workspace_actions") is not new_progress:
        errors.append("checkpoint model-action status does not match observed progress")
    if require_resumable and not new_progress:
        errors.append("Lean workspace made no new environment-observed progress")
    return errors


def load_lean_candidate_workspace_checkpoint(
    *,
    candidate_id: str,
    candidate_lean_declaration: str,
    parent_source: str,
    rejected_source_hash: str,
    checkpoint: Mapping[str, Any],
    rejected_lean_project_hash: str = "",
    parent_formalizer_artifact_id: str | None = None,
    initial_authoring: bool | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Restore exact Lean source, diagnostics, retrieval, and progress identities."""

    errors = _lean_workspace_checkpoint_identity_errors(
        checkpoint,
        candidate_id=candidate_id,
        parent_candidate_lean_declaration=candidate_lean_declaration,
        parent_source=parent_source,
        rejected_source_hash=rejected_source_hash,
        rejected_lean_project_hash=rejected_lean_project_hash,
    )
    if parent_formalizer_artifact_id is not None:
        lane_binding = (
            "parent_formalizer_workspace_target_id"
            if initial_authoring
            else "parent_formalizer_packet_id"
        )
        if (
            str(checkpoint.get("parent_formalizer_artifact_id", "") or "")
            != parent_formalizer_artifact_id
            or str(checkpoint.get(lane_binding, "") or "")
            != parent_formalizer_artifact_id
        ):
            errors.append("checkpoint parent Formalizer artifact is stale")
    if errors:
        raise PacketValidationError(
            validation_label="Lean workspace checkpoint lineage",
            attempts=1,
            errors=errors,
            history=[],
            recovery_checkpoint=checkpoint,
        )
    current_source = str(checkpoint.get("current_source", "") or "")
    legacy_project_hash = lean_project_hash(
        target_source=current_source,
        project_files=(),
        support_build_order=(),
    )
    checked_keys = {
        (
            str(row["source_hash"]),
            str(row["candidate_lean_declaration"]),
            str(row.get("lean_project_hash", "") or legacy_project_hash),
        )
        for row in checkpoint.get("checked_candidate_keys", [])
    }
    state = {
        "source": current_source,
        "source_hash": str(checkpoint.get("current_source_hash", "") or ""),
        "candidate_lean_declaration": str(
            checkpoint.get("candidate_lean_declaration", "") or ""
        ).strip(),
        "checked_candidate_keys": checked_keys,
        "workspace_observation_fingerprints": set(
            checkpoint.get("workspace_observation_fingerprints", [])
        ),
        "support_files": {
            row.path: row.content
            for row in normalized_lean_project_files(
                checkpoint.get("support_files", [])
            )
        },
        "support_build_order": list(
            checkpoint.get("support_build_order", []) or []
        ),
        **{
            field: int(checkpoint.get(field, 0) or 0)
            for field in _LEAN_WORKSPACE_COUNTER_FIELDS
        },
        "last_check": deepcopy(dict(checkpoint.get("last_check", {}) or {})),
        **{
            field: deepcopy(checkpoint.get(field, {}))
            for field in _LEAN_WORKSPACE_OBSERVATION_FIELDS
        },
    }
    metadata = {
        "resumed_from_model_checkpoint": True,
        "parent_source_hash": stable_hash(parent_source),
        "resume_checkpoint_id": str(checkpoint.get("checkpoint_id", "") or ""),
        "resume_checkpoint_source_hash": state["source_hash"],
        "resume_checkpoint_transcript_fingerprint": str(
            checkpoint.get("transcript_fingerprint", "") or ""
        ),
    }
    return state, metadata


def lean_candidate_workspace_continuation_errors(
    checkpoint: Mapping[str, Any],
    *,
    prior_checkpoint: Mapping[str, Any] | None = None,
) -> list[str]:
    """Reject stale, overlapping, or observation-free outer continuations."""

    errors = _lean_workspace_checkpoint_identity_errors(checkpoint)
    predecessor = (
        prior_checkpoint if isinstance(prior_checkpoint, Mapping) else {}
    )
    resumed_from = str(
        checkpoint.get("resumed_from_checkpoint_id", "") or ""
    )
    if predecessor:
        prior_errors = _lean_workspace_checkpoint_identity_errors(predecessor)
        if prior_errors:
            errors.append("prior Lean workspace checkpoint is invalid")
        prior_id = str(predecessor.get("checkpoint_id", "") or "")
        if resumed_from != prior_id:
            errors.append("Lean workspace checkpoint predecessor is stale")
        prior_fingerprints = set(
            predecessor.get("workspace_observation_fingerprints", []) or []
        )
        current_fingerprints = set(
            checkpoint.get("workspace_observation_fingerprints", []) or []
        )
        if not prior_fingerprints < current_fingerprints:
            errors.append("Lean workspace continuation added no new observation")
        if checkpoint.get("segment_start_observation_count") != len(
            prior_fingerprints
        ):
            errors.append("Lean workspace continuation observation boundary is stale")
        starts = checkpoint.get("segment_start_counters", {})
        if not isinstance(starts, Mapping) or any(
            starts.get(field, 0) != predecessor.get(field, 0)
            for field in _LEAN_WORKSPACE_COUNTER_FIELDS
        ):
            errors.append("Lean workspace continuation counter boundary is stale")
    elif resumed_from:
        errors.append("Lean workspace checkpoint has an unbound predecessor")
    return sorted(set(errors))


def lean_candidate_workspace_checkpoint_summary(
    checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    """Project checkpoint telemetry without copying source or observations."""

    source_hash = str(checkpoint.get("current_source_hash", "") or "")
    parent_hash = str(checkpoint.get("parent_source_hash", "") or "")
    last_check = checkpoint.get("last_check", {})
    last_check = last_check if isinstance(last_check, Mapping) else {}
    searches = int(checkpoint.get("searches", 0) or 0)
    proof_searches = int(checkpoint.get("proof_searches", 0) or 0)
    return {
        "candidate_source_hash": source_hash,
        "parent_source_hash": parent_hash,
        "source_changed": bool(
            parent_hash and source_hash and parent_hash != source_hash
        ),
        "source_updates": int(checkpoint.get("source_updates", 0) or 0),
        "current_source_reads": int(checkpoint.get("source_reads", 0) or 0),
        "local_lean_checks": int(checkpoint.get("checks", 0) or 0),
        "latest_check_compiled": bool(last_check.get("compiled", False)),
        "n_client_tool_calls": int(checkpoint.get("tool_calls", 0) or 0),
        "n_formal_source_search_calls": searches,
        "n_proof_candidate_search_calls": proof_searches,
        "n_formal_rag_tool_calls": searches + proof_searches,
        "provider": str(checkpoint.get("provider", "") or ""),
        "model": str(checkpoint.get("model", "") or ""),
        "checkpoint_id": str(checkpoint.get("checkpoint_id", "") or ""),
        "resumed_from_checkpoint_id": str(
            checkpoint.get("resumed_from_checkpoint_id", "") or ""
        ),
        "model_owned_lean_code": bool(
            checkpoint.get("model_owned_lean_code", False)
        ),
        "runtime_selected_lean_code": False,
    }


def run_lean_candidate_revision_tool_loop(
    *,
    provider: Any,
    system_prompt: str,
    user_prompt: str,
    model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_no_progress_turns: int,
    candidate_id: str,
    candidate_lean_declaration: str,
    initial_source: str,
    check_candidate: LeanCandidateCheck,
    search_formal_environment: FormalEnvironmentSearch,
    check_candidate_project: LeanCandidateProjectCheck | None = None,
    check_support_file: LeanSupportFileCheck | None = None,
    initial_lean_project: Mapping[str, Any] | None = None,
    search_proof_candidates: ProofCandidateSearch | None = None,
    inspect_lean_state: LeanStateInspection | None = None,
    inspect_lean_declaration: LeanDeclarationInspection | None = None,
    rejected_source_hash: str = "",
    rejected_lean_project_hash: str = "",
    allow_formal_gap: bool = False,
    request_metadata: Mapping[str, Any] | None = None,
    recovery_checkpoint: Mapping[str, Any] | None = None,
    session_dir: Path | None = None,
    authoritative_theory_document_rows: Sequence[Mapping[str, Any]] = (),
) -> LeanCandidateRevisionToolLoopResult:
    """Let the model author or revise one immutable-bound Lean target."""

    if not candidate_id.strip():
        raise ValueError("Lean candidate tool loop requires a bound semantic target id")
    if initial_source.strip() and not candidate_lean_declaration.strip():
        raise ValueError("an existing Lean source requires its declaration identity")
    for value, label in (
        (max_turns, "turn"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"Lean candidate {label} budget must be positive")

    parent_source = str(initial_source)
    parent_source_hash = stable_hash(parent_source)
    parent_candidate_lean_declaration = candidate_lean_declaration.strip()
    rejected_source_hash = str(rejected_source_hash or "").strip()
    rejected_lean_project_hash = str(rejected_lean_project_hash or "").strip()
    if rejected_source_hash and not parent_source.strip():
        raise ValueError("a rejected source hash requires an existing Lean source")
    if rejected_lean_project_hash and not rejected_source_hash:
        raise ValueError("a rejected Lean project hash requires a rejected source hash")
    workspace_phase = "revision" if parent_source.strip() else "initial_authoring"
    initial_project_files, initial_support_build_order = (
        load_model_authored_lean_project(
            initial_lean_project,
            target_source=parent_source,
        )
    )
    project_tools_enabled = bool(
        check_candidate_project is not None and check_support_file is not None
    )
    if initial_project_files and not project_tools_enabled:
        raise ValueError(
            "an existing multi-file Lean project requires project check tools"
        )
    theory_document_catalog, theory_document_map = (
        theory_documents.externalize_theory_document_rows(
            authoritative_theory_document_rows
        )
    )
    theory_document_set_hash = stable_hash(
        [(row["path"], row["sha256"]) for row in theory_document_catalog]
    ) if theory_document_catalog else ""
    checkpoint_document_set_hash = str(
        (recovery_checkpoint or {}).get("authoritative_theory_document_set_hash", "")
        or ""
    )
    if recovery_checkpoint and (
        checkpoint_document_set_hash != theory_document_set_hash
    ):
        raise PacketValidationError(
            validation_label="Lean workspace checkpoint lineage",
            attempts=1,
            errors=["authoritative Theory documents changed across continuation"],
            history=[],
            recovery_checkpoint=recovery_checkpoint,
        )
    state: dict[str, Any] = {
        "source": parent_source,
        "source_hash": parent_source_hash,
        "candidate_lean_declaration": parent_candidate_lean_declaration,
        "checked_candidate_keys": set(),
        "workspace_observation_fingerprints": set(),
        "support_files": {
            row.path: row.content for row in initial_project_files
        },
        "support_build_order": list(initial_support_build_order),
        "source_updates": 0,
        "declaration_updates": 0,
        "source_reads": 0,
        "support_file_writes": 0,
        "support_file_edits": 0,
        "support_file_reads": 0,
        "support_file_removals": 0,
        "support_file_checks": 0,
        "searches": 0,
        "proof_searches": 0,
        "state_inspections": 0,
        "declaration_inspections": 0,
        "scratch_checks": 0,
        "checks": 0,
        "last_check": {},
        "latest_check_observation": {},
        "latest_formal_environment_search": {},
        "latest_proof_search": {},
        "latest_state_inspection": {},
        "latest_declaration_inspection": {},
        "latest_support_file_check": {},
        "theory_document_inspection_refs": [],
    }
    resume_metadata = {
        "resumed_from_model_checkpoint": False,
        "parent_source_hash": parent_source_hash,
        "resume_checkpoint_id": "",
    }
    if isinstance(recovery_checkpoint, Mapping) and recovery_checkpoint:
        state, resume_metadata = load_lean_candidate_workspace_checkpoint(
            candidate_id=candidate_id,
            candidate_lean_declaration=parent_candidate_lean_declaration,
            parent_source=parent_source,
            rejected_source_hash=rejected_source_hash,
            checkpoint=recovery_checkpoint,
            rejected_lean_project_hash=rejected_lean_project_hash,
        )
    state["authoritative_theory_document_catalog"] = deepcopy(theory_document_catalog)
    state["authoritative_theory_document_set_hash"] = theory_document_set_hash
    tools = _lean_candidate_revision_tools(
        include_proof_search=search_proof_candidates is not None,
        include_state_inspection=inspect_lean_state is not None,
        include_declaration_inspection=inspect_lean_declaration is not None,
        include_formal_gap=allow_formal_gap,
        include_project_tools=project_tools_enabled,
    )
    if theory_document_map:
        tools = (*tools, *theory_documents.theory_document_client_tools())

    def current_project_files() -> tuple[LeanProjectFile, ...]:
        return normalized_lean_project_files(
            [
                {"path": path, "content": content}
                for path, content in state["support_files"].items()
            ]
        )

    def current_project_payload(*, require_complete: bool = True) -> dict[str, Any]:
        rows = current_project_files()
        errors = lean_project_build_order_errors(
            state["support_build_order"],
            project_files=rows,
            require_complete=require_complete,
        )
        if errors:
            raise ClientToolInputError("; ".join(errors))
        if require_complete:
            return model_authored_lean_project(
                target_source=str(state["source"]),
                project_files=rows,
                support_build_order=state["support_build_order"],
            )
        return {
            "support_files": [row.to_json() for row in rows],
            "support_build_order": list(state["support_build_order"]),
            "workspace_project_hash": stable_hash(
                {
                    "target_source_hash": state["source_hash"],
                    "support_files": [row.to_json() for row in rows],
                    "support_build_order": list(state["support_build_order"]),
                }
            ),
        }

    def check_current_source() -> dict[str, Any]:
        project = current_project_payload(require_complete=True)
        if check_candidate_project is not None:
            raw_result = check_candidate_project(
                str(state["source"]),
                str(state["candidate_lean_declaration"]),
                project["support_files"],
                project["support_build_order"],
            )
        else:
            raw_result = check_candidate(
                str(state["source"]),
                str(state["candidate_lean_declaration"]),
            )
        if not isinstance(raw_result, Mapping):
            raise ClientToolInputError("Lean checker returned a non-object result")
        check_result = deepcopy(dict(raw_result))
        observed_hash = str(check_result.get("source_hash", "") or "")
        if observed_hash != state["source_hash"]:
            raise ClientToolInputError(
                "Lean checker result is not bound to the current source hash"
            )
        observed_project_hash = str(
            check_result.get("lean_project_hash", "")
            or project["project_hash"]
        )
        if observed_project_hash != project["project_hash"]:
            raise ClientToolInputError(
                "Lean checker result is not bound to the current project hash"
            )
        check_result.pop("lean_project", None)
        if project_tools_enabled:
            check_result["lean_project_hash"] = project["project_hash"]
        state["checks"] += 1
        state["last_check"] = check_result
        state["latest_check_observation"] = check_result
        state["checked_candidate_keys"].add(
            (
                str(state["source_hash"]),
                str(state["candidate_lean_declaration"]),
                project["project_hash"],
            )
        )
        check_fingerprint_material = {
            "source_hash": state["source_hash"],
            "candidate_lean_declaration": state[
                "candidate_lean_declaration"
            ],
            "check_result": check_result,
        }
        if project_tools_enabled:
            check_fingerprint_material["lean_project_hash"] = project[
                "project_hash"
            ]
        state["workspace_observation_fingerprints"].add(
            "lean-check:" + stable_hash(check_fingerprint_material)
        )
        return check_result

    def invalidate_project_bound_observations() -> None:
        for field in (
            "last_check",
            "latest_check_observation",
            "latest_proof_search",
            "latest_state_inspection",
        ):
            state[field] = {}

    # A resumed source is rechecked in the active project before the first model
    # turn, so the initial message carries fresh diagnostics rather than a copied
    # observation from an earlier runtime packet.
    if parent_source.strip() and not resume_metadata["resumed_from_model_checkpoint"]:
        check_current_source()

    segment_start_counters = {
        field: int(state[field] or 0) for field in _LEAN_WORKSPACE_COUNTER_FIELDS
    }
    segment_start_observation_count = len(
        state["workspace_observation_fingerprints"]
    )

    def current_workspace_observation() -> dict[str, Any]:
        support_rows = current_project_files()
        return {
            "current_source_hash": str(state["source_hash"]),
            "lean_support_files": [
                {
                    "path": row.path,
                    "content_sha256": row.content_sha256,
                    "byte_size": len(row.content.encode("utf-8")),
                }
                for row in support_rows
            ],
            "support_build_order": list(state["support_build_order"]),
            **(
                {
                    "candidate_lean_declaration": str(
                        state["candidate_lean_declaration"]
                    )
                }
                if state["candidate_lean_declaration"]
                else {}
            ),
        }

    def execute_source_candidate(
        *,
        source: str,
        declaration: str,
        source_action: str,
        edit_metadata: Mapping[str, Any] | None = None,
    ) -> ClientToolExecutionResult:
        if not source.strip():
            raise ClientToolInputError("Lean source must be nonempty")
        if len(source) > 20000:
            raise ClientToolInputError(
                "Lean source exceeds the runtime artifact-size boundary"
            )
        if not declaration:
            raise ClientToolInputError(
                "every checked source requires the exact globally resolvable "
                "declaration name"
            )
        source_hash = stable_hash(source)
        changed = source_hash != state["source_hash"]
        declaration_changed = declaration != state["candidate_lean_declaration"]
        try:
            project = model_authored_lean_project(
                target_source=source,
                project_files=current_project_files(),
                support_build_order=state["support_build_order"],
            )
            project_hash = str(project["project_hash"])
        except ValueError as exc:
            raise ClientToolInputError(str(exc)) from exc
        candidate_key = (source_hash, declaration, project_hash)
        if candidate_key in state["checked_candidate_keys"]:
            raise ClientToolInputError(
                "the resulting source and declaration are byte-identical to a "
                "previously checked Lean candidate; its deterministic observation "
                "is already recorded"
            )
        if changed:
            state["source"] = source
            state["source_hash"] = source_hash
            state["source_updates"] += 1
        if declaration_changed:
            state["candidate_lean_declaration"] = declaration
            state["declaration_updates"] += 1
        if changed or declaration_changed:
            invalidate_project_bound_observations()
        check_result = check_current_source()
        compiled = bool(check_result.get("compiled", False))
        rejected_source_reused = bool(
            compiled
            and rejected_source_hash
            and source_hash == rejected_source_hash
            and (
                not rejected_lean_project_hash
                or project_hash == rejected_lean_project_hash
            )
        )
        content = {
            **check_result,
            "ok": compiled and not rejected_source_reused,
            "source_action": source_action,
            "changed": changed,
            "declaration_changed": declaration_changed,
            "source_hash": source_hash,
            "candidate_lean_declaration": declaration,
            "lean_project_hash": project_hash,
            "source_updates": state["source_updates"],
            "declaration_updates": state["declaration_updates"],
            "checks": state["checks"],
            "proof_evidence_status": (
                "LOCAL_LEAN_OBSERVATION_REQUIRES_RUNTIME_PROMOTION_GATE"
            ),
        }
        if edit_metadata:
            content["model_authored_exact_edit"] = deepcopy(dict(edit_metadata))
        if rejected_source_reused:
            content.update(
                {
                    "error": "independently_rejected_source_unchanged",
                    "rejected_source_hash": rejected_source_hash,
                    "rejected_lean_project_hash": rejected_lean_project_hash,
                    "detail": (
                        "Lean compiled this exact source-and-support project, but "
                        "it is identical to the project rejected by independent "
                        "semantic review. Use the findings to author a changed "
                        "project, or report a grounded formal gap."
                    ),
                }
            )
        elif compiled:
            content.update(
                {
                    "handed_off": True,
                    "independent_semantic_review_required": True,
                    "runtime_kernel_promotion_required": True,
                }
            )
        return ClientToolExecutionResult(
            content=content,
            is_error=not compiled or rejected_source_reused,
            state_changed=changed or declaration_changed,
            terminal=compiled and not rejected_source_reused,
            terminal_payload=(
                {
                    "lean_source": state["source"],
                    "source_hash": state["source_hash"],
                    "candidate_lean_declaration": state[
                        "candidate_lean_declaration"
                    ],
                    "check_result": deepcopy(check_result),
                    "lean_project": deepcopy(
                        check_result.get("lean_project", project)
                    ),
                    "source_action": source_action,
                }
                if compiled and not rejected_source_reused
                else None
            ),
            observation_key="lean-source-action:"
            + stable_hash(
                {
                    "source_action": source_action,
                    "source_hash": source_hash,
                    "candidate_lean_declaration": declaration,
                    "lean_project_hash": project_hash,
                    "check_result": check_result,
                    "rejected_source_reused": rejected_source_reused,
                    "edit_metadata": dict(edit_metadata or {}),
                }
            ),
        )

    def execute_tool(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == LEAN_SOURCE_SUBMISSION_TOOL:
            if set(tool_input) != {"lean_source", "candidate_declaration_name"}:
                raise ClientToolInputError(
                    "submit_lean_source requires exactly lean_source and "
                    "candidate_declaration_name on every submission"
                )
            source = tool_input.get("lean_source")
            if not isinstance(source, str) or not source.strip():
                raise ClientToolInputError("lean_source must be a nonempty string")
            declaration = str(
                tool_input.get("candidate_declaration_name", "") or ""
            ).strip()
            return execute_source_candidate(
                source=source,
                declaration=declaration,
                source_action="complete_source_submission",
            )

        if call.name == LEAN_SOURCE_EDIT_TOOL:
            if set(tool_input) != {"edits"}:
                raise ClientToolInputError(
                    "edit_current_lean_source requires exactly edits"
                )
            updated_source, edit_metadata = _apply_exact_source_edit(
                str(state["source"]),
                edits=tool_input.get("edits"),
            )
            return execute_source_candidate(
                source=updated_source,
                declaration=str(state["candidate_lean_declaration"]),
                source_action="atomic_exact_text_edits",
                edit_metadata=edit_metadata,
            )

        if call.name == LEAN_SOURCE_READ_TOOL:
            if set(tool_input) != {"line_start", "line_end"}:
                raise ClientToolInputError(
                    "read_current_lean_source requires line_start and line_end"
                )
            line_start = tool_input.get("line_start")
            line_end = tool_input.get("line_end")
            if (
                isinstance(line_start, bool)
                or not isinstance(line_start, int)
                or isinstance(line_end, bool)
                or not isinstance(line_end, int)
                or line_start < 1
                or line_end < line_start
            ):
                raise ClientToolInputError(
                    "Lean source line range must be positive and ordered"
                )
            source = str(state["source"] or "")
            if not source.strip():
                raise ClientToolInputError(
                    "no current Lean source exists; author it first"
                )
            lines = source.splitlines(keepends=True)
            if line_end > len(lines):
                raise ClientToolInputError(
                    f"current Lean source has {len(lines)} line(s)"
                )
            content = "".join(lines[line_start - 1 : line_end])
            state["source_reads"] += 1
            observation = {
                "ok": True,
                "line_start": line_start,
                "line_end": line_end,
                "total_lines": len(lines),
                "content": content,
                "source_hash": state["source_hash"],
                "candidate_lean_declaration": state[
                    "candidate_lean_declaration"
                ],
                "source_reads": state["source_reads"],
                "proof_evidence_status": "LEAN_SOURCE_READ_NOT_PROOF_EVIDENCE",
            }
            observation_key = "lean-source-read:" + stable_hash(
                {
                    "source_hash": state["source_hash"],
                    "line_start": line_start,
                    "line_end": line_end,
                    "content": content,
                }
            )
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=observation,
                observation_key=observation_key,
            )

        if call.name == LEAN_SUPPORT_FILE_WRITE_TOOL:
            if not project_tools_enabled:
                raise ClientToolInputError("Lean project support files are unavailable")
            if set(tool_input) != {"path", "content"}:
                raise ClientToolInputError(
                    "write_lean_support_file requires exactly path and content"
                )
            path = tool_input.get("path")
            content = tool_input.get("content")
            if not isinstance(path, str) or not isinstance(content, str):
                raise ClientToolInputError(
                    "Lean support file path and content must be strings"
                )
            previous = state["support_files"].get(path)
            if previous == content:
                raise ClientToolInputError(
                    "Lean support file is byte-identical to the current file"
                )
            prospective = dict(state["support_files"])
            prospective[path] = content
            try:
                rows = normalized_lean_project_files(
                    [
                        {"path": file_path, "content": file_content}
                        for file_path, file_content in prospective.items()
                    ]
                )
            except ValueError as exc:
                raise ClientToolInputError(str(exc)) from exc
            state["support_files"] = {
                row.path: row.content for row in rows
            }
            state["support_build_order"] = []
            state["support_file_writes"] += 1
            invalidate_project_bound_observations()
            content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
            observation = {
                "ok": True,
                "path": path,
                "content_sha256": content_sha256,
                "byte_size": len(content.encode("utf-8")),
                "support_file_count": len(rows),
                "support_build_order_reset": True,
                "runtime_edited_source": False,
                "proof_evidence_status": "LEAN_SUPPORT_FILE_WRITE_NOT_PROOF_EVIDENCE",
            }
            observation_key = "lean-support-write:" + stable_hash(observation)
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=observation,
                state_changed=True,
                observation_key=observation_key,
            )

        if call.name == LEAN_SUPPORT_FILE_EDIT_TOOL:
            if not project_tools_enabled:
                raise ClientToolInputError("Lean project support files are unavailable")
            if set(tool_input) != {"path", "current_content_sha256", "edits"}:
                raise ClientToolInputError(
                    "edit_lean_support_file requires path, current_content_sha256, and edits"
                )
            path = tool_input.get("path")
            if not isinstance(path, str) or path not in state["support_files"]:
                raise ClientToolInputError("unknown Lean support file")
            current = str(state["support_files"][path])
            current_sha256 = hashlib.sha256(current.encode("utf-8")).hexdigest()
            if tool_input.get("current_content_sha256") != current_sha256:
                raise ClientToolInputError(
                    "Lean support file edit is stale; read the current hash first"
                )
            try:
                updated, edit_rows = apply_model_exact_text_edits(
                    current,
                    edits=tool_input.get("edits"),
                    replacement_key="new_text",
                )
                normalized_lean_project_files(
                    [
                        {
                            "path": file_path,
                            "content": updated if file_path == path else file_content,
                        }
                        for file_path, file_content in state["support_files"].items()
                    ]
                )
            except (ClientToolInputError, ValueError) as exc:
                raise ClientToolInputError(str(exc)) from exc
            state["support_files"][path] = updated
            state["support_build_order"] = []
            state["support_file_edits"] += 1
            invalidate_project_bound_observations()
            updated_sha256 = hashlib.sha256(updated.encode("utf-8")).hexdigest()
            observation = {
                "ok": True,
                "path": path,
                "previous_content_sha256": current_sha256,
                "content_sha256": updated_sha256,
                "model_authored_exact_edits": deepcopy(edit_rows),
                "support_build_order_reset": True,
                "runtime_edited_source": False,
                "proof_evidence_status": "LEAN_SUPPORT_FILE_EDIT_NOT_PROOF_EVIDENCE",
            }
            observation_key = "lean-support-edit:" + stable_hash(observation)
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=observation,
                state_changed=True,
                observation_key=observation_key,
            )

        if call.name == LEAN_SUPPORT_FILE_READ_TOOL:
            if not project_tools_enabled:
                raise ClientToolInputError("Lean project support files are unavailable")
            if set(tool_input) != {"path", "line_start", "line_end"}:
                raise ClientToolInputError(
                    "read_lean_support_file requires path, line_start, and line_end"
                )
            path = tool_input.get("path")
            line_start = tool_input.get("line_start")
            line_end = tool_input.get("line_end")
            if not isinstance(path, str) or path not in state["support_files"]:
                raise ClientToolInputError("unknown Lean support file")
            if (
                isinstance(line_start, bool)
                or not isinstance(line_start, int)
                or isinstance(line_end, bool)
                or not isinstance(line_end, int)
                or line_start < 1
                or line_end < line_start
            ):
                raise ClientToolInputError(
                    "Lean support file line range must be positive and ordered"
                )
            file_content = str(state["support_files"][path])
            lines = file_content.splitlines(keepends=True)
            if line_end > len(lines):
                raise ClientToolInputError(
                    f"Lean support file has {len(lines)} line(s)"
                )
            selected = "".join(lines[line_start - 1 : line_end])
            state["support_file_reads"] += 1
            observation = {
                "ok": True,
                "path": path,
                "line_start": line_start,
                "line_end": line_end,
                "total_lines": len(lines),
                "content": selected,
                "content_sha256": hashlib.sha256(
                    file_content.encode("utf-8")
                ).hexdigest(),
                "proof_evidence_status": "LEAN_SUPPORT_FILE_READ_NOT_PROOF_EVIDENCE",
            }
            observation_key = "lean-support-read:" + stable_hash(observation)
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=observation,
                observation_key=observation_key,
            )

        if call.name == LEAN_SUPPORT_FILE_REMOVE_TOOL:
            if not project_tools_enabled:
                raise ClientToolInputError("Lean project support files are unavailable")
            if set(tool_input) != {"path", "current_content_sha256"}:
                raise ClientToolInputError(
                    "remove_lean_support_file requires path and current_content_sha256"
                )
            path = tool_input.get("path")
            if not isinstance(path, str) or path not in state["support_files"]:
                raise ClientToolInputError("unknown Lean support file")
            current = str(state["support_files"][path])
            current_sha256 = hashlib.sha256(current.encode("utf-8")).hexdigest()
            if tool_input.get("current_content_sha256") != current_sha256:
                raise ClientToolInputError(
                    "Lean support file removal is stale; read the current hash first"
                )
            del state["support_files"][path]
            state["support_build_order"] = []
            state["support_file_removals"] += 1
            invalidate_project_bound_observations()
            observation = {
                "ok": True,
                "path": path,
                "removed_content_sha256": current_sha256,
                "support_build_order_reset": True,
                "runtime_edited_source": False,
                "proof_evidence_status": "LEAN_SUPPORT_FILE_REMOVE_NOT_PROOF_EVIDENCE",
            }
            observation_key = "lean-support-remove:" + stable_hash(observation)
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=observation,
                state_changed=True,
                observation_key=observation_key,
            )

        if call.name == LEAN_SUPPORT_FILE_CHECK_TOOL:
            if not project_tools_enabled or check_support_file is None:
                raise ClientToolInputError("Lean project support checks are unavailable")
            if set(tool_input) != {"path"}:
                raise ClientToolInputError(
                    "check_lean_support_file requires exactly path"
                )
            path = tool_input.get("path")
            if not isinstance(path, str) or path not in state["support_files"]:
                raise ClientToolInputError("unknown Lean support file")
            if path in state["support_build_order"]:
                raise ClientToolInputError(
                    "Lean support file is already checked in the current build order"
                )
            workspace_identity = current_project_payload(
                require_complete=False
            )["workspace_project_hash"]
            rows = current_project_files()
            raw_result = check_support_file(
                path,
                [row.to_json() for row in rows],
                list(state["support_build_order"]),
            )
            if not isinstance(raw_result, Mapping):
                raise ClientToolInputError(
                    "Lean support checker returned a non-object result"
                )
            observation = deepcopy(dict(raw_result))
            expected_hash = stable_hash(str(state["support_files"][path]))
            if str(observation.get("source_hash", "") or "") != expected_hash:
                raise ClientToolInputError(
                    "Lean support check is not bound to the current file hash"
                )
            compiled = bool(observation.get("compiled", False))
            if compiled:
                state["support_build_order"].append(path)
            state["support_file_checks"] += 1
            state["latest_support_file_check"] = deepcopy(observation)
            content = {
                **observation,
                "ok": compiled,
                "support_build_order": list(state["support_build_order"]),
                "support_files_remaining": sorted(
                    set(state["support_files"]) - set(state["support_build_order"])
                ),
                "support_file_checks": state["support_file_checks"],
                "proof_evidence_status": "LEAN_SUPPORT_FILE_CHECK_NOT_TARGET_PROOF_EVIDENCE",
            }
            observation_key = "lean-support-check:" + stable_hash(
                {
                    "path": path,
                    "workspace_project_hash": workspace_identity,
                    "observation": observation,
                }
            )
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=content,
                is_error=not compiled,
                state_changed=compiled,
                observation_key=observation_key,
            )

        if call.name == LEAN_SCRATCH_TOOL:
            if set(tool_input) != {"lean_source"}:
                raise ClientToolInputError("run_lean_scratch requires exactly lean_source")
            source = tool_input.get("lean_source")
            if not isinstance(source, str) or not source.strip():
                raise ClientToolInputError("scratch Lean source must be nonempty")
            if len(source) > 20_000:
                raise ClientToolInputError("scratch Lean source exceeds size boundary")
            workspace_identity = current_project_payload(
                require_complete=False
            )["workspace_project_hash"]
            raw_result = check_candidate(source, "")
            if not isinstance(raw_result, Mapping):
                raise ClientToolInputError("Lean scratch checker returned a non-object")
            observation = deepcopy(dict(raw_result))
            source_hash = stable_hash(source)
            if str(observation.get("source_hash", "") or "") != source_hash:
                raise ClientToolInputError("Lean scratch result has a stale source hash")
            compiled = bool(observation.get(
                "local_lean_source_compiled", observation.get("compiled", False)
            ))
            state["scratch_checks"] += 1
            content = {
                "ok": compiled,
                "scratch_source_hash": source_hash,
                "scratch_source_compiled": compiled,
                "observation": observation,
                "scratch_checks": state["scratch_checks"],
                **current_workspace_observation(),
                "candidate_source_unchanged": True,
                "proof_evidence_status": "LEAN_SCRATCH_NOT_PROOF_EVIDENCE",
            }
            observation_key = "lean-scratch:" + stable_hash(
                {
                    "scratch_source_hash": source_hash,
                    "workspace_project_hash": workspace_identity,
                    "observation": observation,
                }
            )
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=content,
                is_error=not compiled,
                observation_key=observation_key,
            )

        if call.name == LEAN_FORMAL_GAP_TOOL:
            if not allow_formal_gap:
                raise ClientToolInputError("formal-gap reporting is unavailable")
            if set(tool_input) - {
                "summary",
                "missing_primitives",
                "blocking_observations",
            }:
                raise ClientToolInputError(
                    "report_formal_gap accepts summary, missing_primitives, and "
                    "blocking_observations"
                )
            summary = tool_input.get("summary")
            if not isinstance(summary, str) or not summary.strip():
                raise ClientToolInputError("formal-gap summary must be nonempty")
            missing_primitives = tool_input.get("missing_primitives", [])
            blocking_observations = tool_input.get("blocking_observations", [])
            if not isinstance(missing_primitives, list) or not all(
                isinstance(value, str) and value.strip()
                for value in missing_primitives
            ):
                raise ClientToolInputError(
                    "missing_primitives must be an array of nonempty strings"
                )
            if not isinstance(blocking_observations, list) or not all(
                isinstance(value, str) and value.strip()
                for value in blocking_observations
            ):
                raise ClientToolInputError(
                    "blocking_observations must be an array of nonempty strings"
                )
            n_environment_observations = sum(
                int(state[key] or 0)
                for key in (
                    "checks",
                    "support_file_checks",
                    "scratch_checks",
                    "searches",
                    "proof_searches",
                    "state_inspections",
                    "declaration_inspections",
                )
            )
            if n_environment_observations == 0:
                raise ClientToolInputError(
                    "report_formal_gap requires at least one concrete compiler, "
                    "search, or inspection observation from the active environment"
                )
            current_source = str(state["source"] or "")
            latest_check = state["last_check"]
            if current_source.strip() and not bool(
                latest_check.get(
                    "local_lean_source_compiled",
                    latest_check.get("compiled", False),
                )
            ):
                raise ClientToolInputError(
                    "report_formal_gap cannot promote an unelaborated model-authored "
                    "source into a foundation gap; rewrite and resubmit the complete "
                    "source, or first establish the unchanged target with a locally "
                    "elaborated statement-level witness"
                )
            formal_gap = {
                "summary": summary.strip(),
                "missing_primitives": [value.strip() for value in missing_primitives],
                "blocking_observations": [
                    value.strip() for value in blocking_observations
                ],
            }
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "disposition": "FORMAL_GAP",
                    "formal_gap": deepcopy(formal_gap),
                    "proof_evidence_status": (
                        "MODEL_REPORTED_FORMAL_GAP_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=True,
                terminal=True,
                terminal_payload={
                    "disposition": "FORMAL_GAP",
                    "formal_gap": formal_gap,
                },
                observation_key="formal-gap:" + stable_hash(formal_gap),
            )

        if call.name == "search_formal_environment":
            if set(tool_input) - {"query", "max_results"}:
                raise ClientToolInputError(
                    "search_formal_environment accepts query and optional max_results"
                )
            query = tool_input.get("query")
            if not isinstance(query, str) or not query.strip():
                raise ClientToolInputError("search query must be a nonempty string")
            requested_k = tool_input.get("max_results", 5)
            if isinstance(requested_k, bool) or not isinstance(requested_k, int):
                raise ClientToolInputError("max_results must be an integer")
            k = max(1, min(8, requested_k))
            state["searches"] += 1
            results = search_formal_environment(query.strip(), k)
            content = {
                "ok": True,
                "query": query.strip(),
                "results": deepcopy(results),
                "searches": state["searches"],
                **current_workspace_observation(),
                "proof_evidence_status": "FORMAL_SOURCE_SEARCH_NOT_PROOF_EVIDENCE",
            }
            state["latest_formal_environment_search"] = deepcopy(content)
            observation_key = "search:" + stable_hash(
                {"query": content["query"], "results": content["results"]}
            )
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=content,
                observation_key=observation_key,
            )

        if call.name == "search_proof_candidates":
            if search_proof_candidates is None:
                raise ClientToolInputError("proof-candidate search is unavailable")
            if set(tool_input) - {"query", "max_results", "lean_header"}:
                raise ClientToolInputError(
                    "search_proof_candidates accepts query, max_results, and lean_header"
                )
            query = tool_input.get("query")
            if not isinstance(query, str) or not query.strip():
                raise ClientToolInputError("proof-search query must be a nonempty string")
            requested_k = tool_input.get("max_results", 4)
            if isinstance(requested_k, bool) or not isinstance(requested_k, int):
                raise ClientToolInputError("max_results must be an integer")
            lean_header = tool_input.get("lean_header", "")
            if not isinstance(lean_header, str) or len(lean_header) > 20_000:
                raise ClientToolInputError(
                    "lean_header must be text within the artifact-size boundary"
                )
            k = max(1, min(8, requested_k))
            state["proof_searches"] += 1
            search_context = deepcopy(dict(state["last_check"]))
            state_inspection = state["latest_state_inspection"]
            if (
                isinstance(state_inspection, Mapping)
                and state_inspection
                and state_inspection.get("source_hash") == state["source_hash"]
                and state_inspection.get("lean_project_hash", "")
                == search_context.get("lean_project_hash", "")
            ):
                search_context["latest_state_inspection"] = deepcopy(
                    dict(state_inspection)
                )
            if lean_header.strip():
                search_context["model_lean_header"] = lean_header
            results = search_proof_candidates(
                str(state["source"]),
                query.strip(),
                k,
                search_context,
            )
            content = {
                "ok": True,
                "query": query.strip(),
                "results": deepcopy(results),
                "proof_searches": state["proof_searches"],
                **current_workspace_observation(),
                "proof_evidence_status": (
                    "PROOF_SEARCH_RESULT_NOT_PROOF_EVIDENCE"
                ),
                "source_ownership": (
                    "The model must choose and submit the complete next Lean source; "
                    "the runtime does not splice returned proof bodies."
                ),
            }
            state["latest_proof_search"] = deepcopy(content)
            observation_key = "proof-search:" + stable_hash(
                {
                    "source_hash": state["source_hash"],
                    "query": content["query"],
                    "results": content["results"],
                }
            )
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=content,
                observation_key=observation_key,
            )

        if call.name == "inspect_lean_state":
            if inspect_lean_state is None:
                raise ClientToolInputError("Lean state inspection is unavailable")
            if tool_input:
                raise ClientToolInputError("inspect_lean_state takes an empty object")
            if not state["last_check"]:
                raise ClientToolInputError(
                    "the current source must be checked before inspect_lean_state so "
                    "the inspection is bound to exact source bytes and diagnostics"
                )
            state["state_inspections"] += 1
            result = inspect_lean_state(
                str(state["source"]),
                deepcopy(dict(state["last_check"])),
            )
            if not isinstance(result, Mapping):
                raise ClientToolInputError(
                    "Lean state inspector returned a non-object result"
                )
            result = deepcopy(dict(result))
            if result.get("source_hash") != state["source_hash"]:
                raise ClientToolInputError(
                    "Lean state inspection is not bound to the current source hash"
                )
            if result.get("lean_project_hash", "") != state["last_check"].get(
                "lean_project_hash", ""
            ):
                raise ClientToolInputError(
                    "Lean state inspection is not bound to the current project hash"
                )
            state["latest_state_inspection"] = deepcopy(result)
            content = {
                "ok": True,
                **current_workspace_observation(),
                "observation": deepcopy(result),
                "state_inspections": state["state_inspections"],
                "proof_evidence_status": (
                    "LEAN_STATE_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }
            observation_key = "lean-state:" + stable_hash(
                {
                    "source_hash": state["source_hash"],
                    "observation": content["observation"],
                }
            )
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=content,
                observation_key=observation_key,
            )

        if call.name == "inspect_lean_declaration":
            if inspect_lean_declaration is None:
                raise ClientToolInputError(
                    "Lean declaration inspection is unavailable"
                )
            if set(tool_input) - {"symbol", "context_lines"}:
                raise ClientToolInputError(
                    "inspect_lean_declaration accepts symbol and optional context_lines"
                )
            symbol = tool_input.get("symbol")
            if not isinstance(symbol, str) or not symbol.strip():
                raise ClientToolInputError(
                    "declaration symbol must be a nonempty string"
                )
            requested_context = tool_input.get("context_lines", 20)
            if isinstance(requested_context, bool) or not isinstance(
                requested_context, int
            ):
                raise ClientToolInputError("context_lines must be an integer")
            context_lines = max(0, min(40, requested_context))
            state["declaration_inspections"] += 1
            result = inspect_lean_declaration(
                str(state["source"]),
                symbol.strip(),
                context_lines,
                deepcopy(dict(state["last_check"])),
            )
            state["latest_declaration_inspection"] = deepcopy(result)
            content = {
                "ok": bool(result.get("ok", True))
                if isinstance(result, Mapping)
                else True,
                **current_workspace_observation(),
                "symbol": symbol.strip(),
                "observation": deepcopy(result),
                "declaration_inspections": state["declaration_inspections"],
                "proof_evidence_status": (
                    "LEAN_DECLARATION_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }
            observation_key = "lean-declaration:" + stable_hash(
                {
                    "source_hash": state["source_hash"],
                    "symbol": content["symbol"],
                    "observation": content["observation"],
                }
            )
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=content,
                is_error=not content["ok"],
                observation_key=observation_key,
            )

        if call.name in {
            theory_documents.THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
            theory_documents.THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        }:
            content, inspection_ref = (
                theory_documents.execute_theory_document_client_tool(
                    theory_document_map,
                    tool_name=call.name,
                    tool_input=tool_input,
                )
            )
            state["theory_document_inspection_refs"].append(inspection_ref)
            observation_key = "theory-document:" + stable_hash(inspection_ref)
            state["workspace_observation_fingerprints"].add(observation_key)
            return ClientToolExecutionResult(
                content=content,
                observation_key=observation_key,
            )

        raise ClientToolInputError("unsupported Lean candidate client tool")

    initial_workspace = {
        "artifact_kind": "LeanCandidateWorkspaceInitialState",
        "candidate_id": candidate_id,
        "candidate_lean_declaration": state["candidate_lean_declaration"],
        "current_source_hash": state["source_hash"],
        "current_source_manifest": {
            "source_hash": state["source_hash"],
            "line_count": len(str(state["source"]).splitlines()),
            "character_count": len(str(state["source"])),
            "source_present": bool(str(state["source"]).strip()),
            "complete_source_inline": False,
            "content_transport": LEAN_SOURCE_READ_TOOL,
        },
        "lean_support_file_catalog": [
            {
                "path": row.path,
                "content_sha256": row.content_sha256,
                "byte_size": len(row.content.encode("utf-8")),
                "line_count": len(row.content.splitlines()),
                "content_transport": LEAN_SUPPORT_FILE_READ_TOOL,
            }
            for row in current_project_files()
        ],
        "support_build_order": list(state["support_build_order"]),
        "latest_check_observation": _compact_lean_check_observation(
            state["latest_check_observation"]
        ),
        "latest_formal_environment_search": deepcopy(
            state["latest_formal_environment_search"]
        ),
        "latest_proof_search": deepcopy(state["latest_proof_search"]),
        "latest_state_inspection": deepcopy(state["latest_state_inspection"]),
        "latest_declaration_inspection": deepcopy(
            state["latest_declaration_inspection"]
        ),
        **(
            {
                "authoritative_theory_documents": theory_document_catalog,
                "authoritative_theory_document_set_hash": (
                    theory_document_set_hash
                ),
                "theory_document_content_transport": (
                    "hash_bound_read_only_client_tools"
                ),
            }
            if theory_document_catalog
            else {}
        ),
        "resumed_from_checkpoint_id": resume_metadata["resume_checkpoint_id"],
        **(
            {
                "revision_requirement": {
                    "rejected_source_hash": rejected_source_hash,
                    "rejected_lean_project_hash": rejected_lean_project_hash,
                    "required_disposition": (
                        "author a changed source/support project or report grounded formal gap"
                    ),
                }
            }
            if rejected_source_hash
            else {}
        ),
        "proof_evidence_status": "WORKSPACE_STATE_NOT_PROOF_EVIDENCE",
    }
    root_authorization_fingerprint = (
        client_tool_authorization_fingerprint(request_metadata)
        or stable_hash(["lean", candidate_id, theory_document_set_hash])
    )
    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=(
            {
                "role": "user",
                "content": (
                    user_prompt
                    + f"\n\nThis retained Lean session has up to {max_turns} model/tool turns; retrieval, source revision, checks, and terminal submission share that allowance."
                    + "\n\nThe complete current Lean source is authoritative in "
                    "the retained workspace and is not copied into this opening. "
                    "Use read_current_lean_source for exact line ranges before a "
                    "localized edit; submit_lean_source remains available for a "
                    "complete replacement or initial authoring."
                    + (
                        " Support files are optional model-owned project state. "
                        "Create, read, edit, remove, and compile them with the Lean "
                        "support-file tools. Compile dependencies before dependents; "
                        "the resulting successful order is replayed exactly before "
                        "every target check and final kernel promotion."
                        if project_tools_enabled
                        else ""
                    )
                    + "\n\nInitial authoritative Lean workspace state:\n"
                    + json.dumps(
                        initial_workspace,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                        ensure_ascii=False,
                    )
                ),
            },
        ),
        tools=tools,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=False,
        enable_prompt_caching=True,
        metadata={
            **dict(request_metadata or {}),
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: (
                root_authorization_fingerprint
            ),
            "model_tier": model_tier,
            "candidate_id": candidate_id,
            "candidate_lean_declaration": state["candidate_lean_declaration"],
            "parent_source_hash": parent_source_hash,
            "rejected_source_hash": rejected_source_hash,
            **(
                {"rejected_lean_project_hash": rejected_lean_project_hash}
                if project_tools_enabled
                else {}
            ),
            "resumed_from_checkpoint_id": resume_metadata[
                "resume_checkpoint_id"
            ],
        },
    )
    resolved_session_dir = session_dir.resolve() if session_dir else None
    resumed_client_tool_session_ref: dict[str, Any] = {}
    resumed_client_tool_context_window: dict[str, Any] = {}
    prior_client_tool_session_ref = (
        recovery_checkpoint.get("client_tool_session_ref", {})
        if isinstance(recovery_checkpoint, Mapping)
        else {}
    )
    if prior_client_tool_session_ref:
        if not isinstance(prior_client_tool_session_ref, Mapping):
            raise ValueError("Lean client-tool session reference is malformed")
        if resolved_session_dir is None:
            raise ValueError(
                "Lean client-tool session resume requires a persistent directory"
            )
        request, resumed_client_tool_context_window = (
            resume_client_tool_session_from_checkpoint(
                prior_client_tool_session_ref,
                session_dir=resolved_session_dir,
                session_id=f"lean:{candidate_id}",
                checkpoint_identity=resume_metadata["resume_checkpoint_id"],
                request=request,
                replay_recent_tool_rounds=CLIENT_TOOL_RECENT_HISTORY_ROUNDS,
            )
        )
        resumed_client_tool_session_ref = deepcopy(
            dict(prior_client_tool_session_ref)
        )

    # Permit one observation plus a final source action inside the same loop.
    max_tool_calls = max_turns + 1
    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
        )
    except ClientToolLoopError as exc:
        client_tool_session_ref = persist_client_tool_session(
            session_dir=resolved_session_dir,
            session_id=f"lean:{candidate_id}",
            request=request,
            messages=exc.messages,
        )
        new_progress = bool(
            len(state["workspace_observation_fingerprints"])
            > segment_start_observation_count
        )
        checkpoint_body = {
            "schema_version": 3 if project_tools_enabled else 2,
            "artifact_kind": LEAN_CANDIDATE_WORKSPACE_CHECKPOINT_KIND,
            "candidate_id": candidate_id,
            "parent_candidate_lean_declaration": (
                parent_candidate_lean_declaration
            ),
            "candidate_lean_declaration": state[
                "candidate_lean_declaration"
            ],
            "workspace_phase": workspace_phase,
            "parent_source_hash": parent_source_hash,
            "rejected_source_hash": rejected_source_hash,
            **(
                {"rejected_lean_project_hash": rejected_lean_project_hash}
                if project_tools_enabled
                else {}
            ),
            "current_source_hash": state["source_hash"],
            "current_source": state["source"],
            "support_files": [
                row.to_json() for row in current_project_files()
            ],
            "support_build_order": list(state["support_build_order"]),
            "checked_candidate_keys": [
                {
                    "source_hash": source_hash,
                    "candidate_lean_declaration": declaration,
                    **(
                        {"lean_project_hash": project_hash}
                        if project_tools_enabled
                        else {}
                    ),
                }
                for source_hash, declaration, project_hash in sorted(
                    state["checked_candidate_keys"]
                )
            ],
            "workspace_observation_fingerprints": sorted(
                state["workspace_observation_fingerprints"]
            ),
            **{
                field: int(state[field] or 0)
                for field in _LEAN_WORKSPACE_COUNTER_FIELDS
            },
            "segment_start_counters": segment_start_counters,
            "segment_start_observation_count": (
                segment_start_observation_count
            ),
            "last_check": deepcopy(state["last_check"]),
            "last_check_hash": stable_hash(state["last_check"]),
            **{
                field: deepcopy(state[field])
                for field in _LEAN_WORKSPACE_OBSERVATION_FIELDS
            },
            "resumed_from_checkpoint_id": resume_metadata[
                "resume_checkpoint_id"
            ],
            "resumed_from_client_tool_session_ref": deepcopy(
                resumed_client_tool_session_ref
            ),
            "client_tool_checkpoint_window": deepcopy(
                resumed_client_tool_context_window
            ),
            "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
            "authoritative_theory_document_set_hash": (
                theory_document_set_hash
            ),
            "turns": exc.turns,
            "tool_calls": exc.tool_calls,
            "interaction_policy": "single_model_tool_observation_budget_v1",
            "transcript_fingerprint": exc.transcript_fingerprint,
            "provider": exc.provider,
            "model": exc.model or model,
            "model_tier": model_tier,
            **(
                {"client_tool_session_ref": client_tool_session_ref}
                if client_tool_session_ref
                else {}
            ),
            "resumable": new_progress,
            "accepted": False,
            "runtime_selected_lean_code": False,
            "model_owned_lean_code": bool(
                str(state["source"]).strip() or state["support_files"]
            ),
            "model_owned_workspace_actions": new_progress,
            "kernel_verified": False,
            "proof_evidence_status": (
                "CLIENT_TOOL_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
        }
        raise PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool workspace",
            attempts=exc.turns,
            errors=[exc.reason],
            history=theory_documents.workspace_evidence_history(
                exc.history
            ),
            recovery_checkpoint=seal_lean_candidate_workspace_checkpoint(
                checkpoint_body
            ),
        ) from exc

    client_tool_session_ref = persist_client_tool_session(
        session_dir=resolved_session_dir,
        session_id=f"lean:{candidate_id}",
        request=request,
        messages=loop.messages,
    )
    terminal = dict(loop.terminal_payload)
    disposition = str(terminal.get("disposition", "AUTHOR_LEAN") or "AUTHOR_LEAN")
    if disposition == "FORMAL_GAP":
        formal_gap = terminal.get("formal_gap", {})
        if not isinstance(formal_gap, Mapping) or not str(
            formal_gap.get("summary", "") or ""
        ).strip():
            raise PacketValidationError(
                validation_label="LLM Formalizer Lean candidate client-tool workspace",
                attempts=loop.turns,
                errors=["terminal formal-gap payload is incomplete"],
                history=theory_documents.workspace_evidence_history(
                    loop.history
                ),
            )
        return _lean_candidate_revision_success_result(
            source=str(state["source"]),
            check_result=deepcopy(dict(state["last_check"])),
            state=state,
            candidate_id=candidate_id,
            candidate_lean_declaration=str(
                state["candidate_lean_declaration"]
            ),
            disposition=disposition,
            terminal_source_action="formal_gap",
            formal_gap=formal_gap,
            parent_source_hash=parent_source_hash,
            tools=tools,
            max_turns=max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
            rejected_source_hash=rejected_source_hash,
            rejected_lean_project_hash=rejected_lean_project_hash,
            lean_project_persistence_root=resolved_session_dir,
            turns=loop.turns,
            tool_calls=loop.tool_calls,
            runtime_executed_tool_calls=loop.runtime_executed_tool_calls,
            provider=loop.provider,
            model=loop.model,
            model_tier=model_tier,
            provider_usage=loop.provider_usage,
            response_metadata=loop.final_response_metadata,
            history=loop.history,
            transcript_fingerprint=loop.transcript_fingerprint,
            workspace_phase=workspace_phase,
            resumed_from_checkpoint_id=resume_metadata[
                "resume_checkpoint_id"
            ],
            segment_start_counters=segment_start_counters,
            segment_start_observation_count=(
                segment_start_observation_count
            ),
            client_tool_session_ref=client_tool_session_ref,
            resumed_client_tool_session_ref=(
                resumed_client_tool_session_ref
            ),
            client_tool_context_window=(
                resumed_client_tool_context_window
            ),
        )
    source = str(terminal.get("lean_source", "") or "")
    source_hash = str(terminal.get("source_hash", "") or "")
    submitted_declaration = str(
        terminal.get("candidate_lean_declaration", "") or ""
    ).strip()
    check_result = terminal.get("check_result", {})
    terminal_project = terminal.get("lean_project", {})
    try:
        terminal_project_files, terminal_build_order = (
            load_model_authored_lean_project(
                terminal_project,
                target_source=source,
            )
        )
        terminal_project_hash = lean_project_hash(
            target_source=source,
            project_files=terminal_project_files,
            support_build_order=terminal_build_order,
        )
    except ValueError:
        terminal_project_hash = ""
    if (
        not source.strip()
        or source_hash != stable_hash(source)
        or not submitted_declaration
        or not isinstance(check_result, Mapping)
        or str(check_result.get("source_hash", "") or "") != source_hash
        or str(
            check_result.get("lean_project_hash", "")
            or terminal_project_hash
        )
        != terminal_project_hash
        or not terminal_project_hash
        or not bool(check_result.get("compiled", False))
        or bool(
            rejected_source_hash
            and source_hash == rejected_source_hash
            and (
                not rejected_lean_project_hash
                or terminal_project_hash == rejected_lean_project_hash
            )
        )
    ):
        raise PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool workspace",
            attempts=loop.turns,
            errors=["terminal payload was not bound to a compiled current source"],
            history=theory_documents.workspace_evidence_history(
                loop.history
            ),
        )

    return _lean_candidate_revision_success_result(
        source=source,
        check_result=check_result,
        state=state,
        candidate_id=candidate_id,
        candidate_lean_declaration=submitted_declaration,
        disposition="AUTHOR_LEAN",
        terminal_source_action=str(
            terminal.get("source_action", "complete_source_submission")
            or "complete_source_submission"
        ),
        formal_gap={},
        parent_source_hash=parent_source_hash,
        tools=tools,
        max_turns=max_turns,
        max_tool_calls=max_tool_calls,
        max_no_progress_turns=max_no_progress_turns,
        rejected_source_hash=rejected_source_hash,
        rejected_lean_project_hash=rejected_lean_project_hash,
        lean_project_persistence_root=resolved_session_dir,
        turns=loop.turns,
        tool_calls=loop.tool_calls,
        runtime_executed_tool_calls=loop.runtime_executed_tool_calls,
        provider=loop.provider,
        model=loop.model,
        model_tier=model_tier,
        provider_usage=loop.provider_usage,
        response_metadata=loop.final_response_metadata,
        history=loop.history,
        transcript_fingerprint=loop.transcript_fingerprint,
        workspace_phase=workspace_phase,
        resumed_from_checkpoint_id=resume_metadata["resume_checkpoint_id"],
        segment_start_counters=segment_start_counters,
        segment_start_observation_count=segment_start_observation_count,
        client_tool_session_ref=client_tool_session_ref,
        resumed_client_tool_session_ref=resumed_client_tool_session_ref,
        client_tool_context_window=resumed_client_tool_context_window,
    )


def _lean_candidate_revision_success_result(
    *,
    source: str,
    check_result: Mapping[str, Any],
    state: Mapping[str, Any],
    candidate_id: str,
    candidate_lean_declaration: str,
    disposition: str,
    terminal_source_action: str,
    formal_gap: Mapping[str, Any],
    parent_source_hash: str,
    tools: tuple[ClientToolDefinition, ...],
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    rejected_source_hash: str,
    rejected_lean_project_hash: str,
    lean_project_persistence_root: Path | None,
    turns: int,
    tool_calls: int,
    runtime_executed_tool_calls: int,
    provider: str,
    model: str,
    model_tier: str,
    provider_usage: Mapping[str, int],
    response_metadata: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]],
    transcript_fingerprint: str,
    workspace_phase: str,
    resumed_from_checkpoint_id: str,
    segment_start_counters: Mapping[str, int],
    segment_start_observation_count: int,
    client_tool_session_ref: Mapping[str, Any],
    resumed_client_tool_session_ref: Mapping[str, Any],
    client_tool_context_window: Mapping[str, Any],
) -> LeanCandidateRevisionToolLoopResult:
    source_hash = stable_hash(source)
    accepted_model_source = disposition == "AUTHOR_LEAN"
    project_rows = normalized_lean_project_files(
        [
            {"path": path, "content": content}
            for path, content in state.get("support_files", {}).items()
        ]
    )
    if accepted_model_source:
        lean_project = model_authored_lean_project(
            target_source=source,
            project_files=project_rows,
            support_build_order=state.get("support_build_order", []),
        )
        lean_project = persist_model_authored_lean_project(
            lean_project,
            target_source=source,
            root=lean_project_persistence_root,
        )
    else:
        lean_project = {
            "artifact_kind": "ModelAuthoredLeanProjectDraft",
            "main_source_hash": source_hash,
            "support_files": [row.to_json() for row in project_rows],
            "support_build_order": list(
                state.get("support_build_order", [])
            ),
            "runtime_edited_source": False,
            "proof_evidence_status": "LEAN_PROJECT_DRAFT_NOT_PROOF_EVIDENCE",
        }
    model_owned_lean_code = bool(source.strip() or project_rows)
    model_explicit_submit = bool(
        int(state["source_updates"] or 0)
        or int(state["declaration_updates"] or 0)
        or int(state.get("support_file_writes", 0) or 0)
        or int(state.get("support_file_edits", 0) or 0)
        or int(state.get("support_file_removals", 0) or 0)
    )
    latest_check_compiled = bool(
        check_result.get(
            "local_lean_source_compiled",
            check_result.get("compiled", False),
        )
    )
    local_candidate_validation_passed = bool(
        check_result.get("compiled", False)
    )
    state_provider_tools = _lean_state_executed_tools(
        state.get("latest_state_inspection", {})
    )
    declaration_provider_tools = _lean_state_executed_tools(
        state.get("latest_declaration_inspection", {})
    )
    live_provider_tools = tuple(
        dict.fromkeys([*state_provider_tools, *declaration_provider_tools])
    )
    evidence = {
        "schema_version": 3,
        "artifact_kind": "LeanCandidateClientToolWorkspace",
        "transport": "native_client_tools",
        "candidate_id": candidate_id,
        "candidate_lean_declaration": candidate_lean_declaration,
        "disposition": disposition,
        "terminal_source_action": terminal_source_action,
        **({"formal_gap": deepcopy(dict(formal_gap))} if formal_gap else {}),
        "workspace_phase": workspace_phase,
        "resumed_from_checkpoint_id": resumed_from_checkpoint_id,
        "client_tool_session_ref": deepcopy(dict(client_tool_session_ref)),
        "resumed_from_client_tool_session_ref": deepcopy(
            dict(resumed_client_tool_session_ref)
        ),
        "client_tool_session_lineage_continued": bool(
            resumed_client_tool_session_ref
        ),
        "client_tool_checkpoint_window": deepcopy(
            dict(client_tool_context_window)
        ),
        "workspace_segment_start_counters": dict(segment_start_counters),
        "workspace_segment_start_observation_count": (
            segment_start_observation_count
        ),
        "parent_source_hash": parent_source_hash,
        "submitted_source_hash": source_hash,
        "source_changed": source_hash != parent_source_hash,
        "turns": turns,
        "tool_calls": tool_calls,
        "runtime_executed_tool_calls": runtime_executed_tool_calls,
        "runtime_verifier_checks": 0,
        "max_turns": max_turns,
        "max_tool_calls": max_tool_calls,
        "max_no_progress_turns": max_no_progress_turns,
        "interaction_policy": "single_model_tool_observation_budget_v1",
        "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
        "tool_surface_policy": "stable_for_workspace",
        "submit_and_check_atomic": True,
        "model_source_action_and_check_atomic": True,
        "incremental_exact_edit_available": LEAN_SOURCE_EDIT_TOOL
        in {tool.name for tool in tools},
        "current_source_read_available": LEAN_SOURCE_READ_TOOL
        in {tool.name for tool in tools},
        "current_source_content_transport": LEAN_SOURCE_READ_TOOL,
        "lean_project": deepcopy(lean_project),
        "lean_project_hash": str(lean_project.get("project_hash", "") or ""),
        "lean_support_file_count": len(project_rows),
        "lean_support_file_writes": int(
            state.get("support_file_writes", 0) or 0
        ),
        "lean_support_file_edits": int(
            state.get("support_file_edits", 0) or 0
        ),
        "lean_support_file_reads": int(
            state.get("support_file_reads", 0) or 0
        ),
        "lean_support_file_removals": int(
            state.get("support_file_removals", 0) or 0
        ),
        "lean_support_file_checks": int(
            state.get("support_file_checks", 0) or 0
        ),
        "tool_names": [tool.name for tool in tools],
        "source_updates": state["source_updates"],
        "declaration_updates": state["declaration_updates"],
        "current_source_reads": state["source_reads"],
        **(
            {"independently_rejected_source_hash": rejected_source_hash}
            if rejected_source_hash
            else {}
        ),
        **(
            {
                "independently_rejected_lean_project_hash": (
                    rejected_lean_project_hash
                )
            }
            if rejected_lean_project_hash
            else {}
        ),
        "formal_environment_searches": state["searches"],
        "proof_candidate_searches": state["proof_searches"],
        "lean_state_inspections": state["state_inspections"],
        "lean_state_provider_tools": list(state_provider_tools),
        "lean_declaration_inspections": state["declaration_inspections"],
        "lean_scratch_checks": state["scratch_checks"],
        "lean_declaration_provider_tools": list(
            declaration_provider_tools
        ),
        "authoritative_theory_documents": len(
            state.get("authoritative_theory_document_catalog", [])
        ),
        "authoritative_theory_document_set_hash": (
            state.get("authoritative_theory_document_set_hash", "")
        ),
        "theory_document_content_transport": (
            "hash_bound_read_only_client_tools"
            if state.get("authoritative_theory_document_set_hash", "")
            else ""
        ),
        "theory_document_inspections": len(
            state.get("theory_document_inspection_refs", [])
        ),
        "theory_document_inspection_refs": deepcopy(
            state.get("theory_document_inspection_refs", [])
        ),
        "lean_lsp_mcp_live_called": any(
            tool.startswith("lean_lsp_mcp.") for tool in live_provider_tools
        ),
        "local_lean_checks": state["checks"],
        "latest_check_compiled": latest_check_compiled,
        "provider": provider,
        "model": model,
        "model_tier": model_tier,
        "provider_usage": dict(provider_usage),
        "history": theory_documents.workspace_evidence_history(
            history
        ),
        "transcript_fingerprint": transcript_fingerprint,
        "handoff_mode": (
            "successful_model_source_submission"
            if accepted_model_source
            else "model_reported_formal_gap"
        ),
        "model_explicit_submit": model_explicit_submit,
        "model_explicit_source_action": model_explicit_submit,
        "budget_exhausted": False,
        "local_candidate_validation_passed": (
            local_candidate_validation_passed
        ),
        "tools_executed_by_runtime": bool(
            runtime_executed_tool_calls
        ),
        "tools_executed_by_backend": bool(
            response_metadata.get("tools_executed_by_backend", False)
        ),
        "runtime_selected_lean_code": False,
        "model_owned_lean_code": model_owned_lean_code,
        "independent_semantic_review_required": accepted_model_source,
        "runtime_kernel_promotion_required": accepted_model_source,
        "kernel_verified": False,
        "proof_evidence_status": (
            "LEAN_CANDIDATE_CLIENT_TOOL_LOOP_RECORDED_NOT_PROOF_EVIDENCE"
        ),
    }
    if formal_gap:
        evidence["formal_gap_observation"] = {
            "formal_gap": deepcopy(dict(formal_gap)),
            "candidate_id": candidate_id,
            "candidate_lean_declaration": candidate_lean_declaration,
            "current_source": source,
            "current_source_hash": source_hash,
            "parent_source_hash": parent_source_hash,
            "latest_check_observation": deepcopy(dict(check_result)),
            "latest_formal_environment_search": deepcopy(
                dict(state.get("latest_formal_environment_search", {}) or {})
            ),
            "latest_proof_search": deepcopy(
                dict(state.get("latest_proof_search", {}) or {})
            ),
            "latest_state_inspection": deepcopy(
                dict(state.get("latest_state_inspection", {}) or {})
            ),
            "latest_declaration_inspection": deepcopy(
                dict(state.get("latest_declaration_inspection", {}) or {})
            ),
            "model_owned_lean_code": model_owned_lean_code,
            "runtime_selected_lean_code": False,
            "kernel_verified": False,
            "proof_evidence_status": (
                "MODEL_REPORTED_FORMAL_GAP_OBSERVATION_NOT_PROOF_EVIDENCE"
            ),
        }
    return LeanCandidateRevisionToolLoopResult(
        lean_source=source,
        source_hash=source_hash,
        candidate_lean_declaration=candidate_lean_declaration,
        disposition=disposition,
        formal_gap=deepcopy(dict(formal_gap)),
        check_result=deepcopy(dict(check_result)),
        lean_project=deepcopy(lean_project),
        evidence=evidence,
    )


def _compact_lean_check_observation(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    keys = (
        "source_hash",
        "lean_project_hash",
        "candidate_lean_declaration",
        "compiled",
        "precheck_errors",
        "blocking_precheck_errors",
        "local_lean_attempted",
        "local_lean_source_compiled",
        "local_lean_exit_status",
        "local_lean_stdout",
        "local_lean_stderr",
        "candidate_identity_lean_checked",
        "candidate_identity_lean_verified",
        "candidate_identity_lean_stdout",
        "candidate_identity_lean_stderr",
        "candidate_declaration_elaborated",
        "candidate_development_status",
        "candidate_axiom_names",
        "candidate_untrusted_axiom_names",
        "candidate_axiom_audit_checked",
        "candidate_axiom_audit_clean",
    )
    return {key: deepcopy(value[key]) for key in keys if key in value}


def _lean_state_executed_tools(value: Any) -> tuple[str, ...]:
    tools: list[str] = []

    def visit(item: Any, *, depth: int = 0) -> None:
        if depth > 8:
            return
        if isinstance(item, Mapping):
            executed = item.get("executed_tools", [])
            if isinstance(executed, (list, tuple, set)):
                tools.extend(str(tool) for tool in executed if str(tool).strip())
            trace = item.get("tool_call_trace", [])
            if isinstance(trace, (list, tuple)):
                for row in trace:
                    if isinstance(row, Mapping):
                        tool = str(row.get("tool", "") or "").strip()
                        if tool:
                            tools.append(tool)
            for child in item.values():
                visit(child, depth=depth + 1)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child, depth=depth + 1)

    visit(value)
    return tuple(dict.fromkeys(tools))


def _lean_candidate_revision_tools(
    *,
    include_proof_search: bool = False,
    include_state_inspection: bool = False,
    include_declaration_inspection: bool = False,
    include_formal_gap: bool = False,
    include_project_tools: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    tools = [
        ClientToolDefinition(
            name=LEAN_SOURCE_SUBMISSION_TOOL,
            description=(
                "Submit one complete model-authored Lean source and its fully qualified "
                "declaration identifier. The configured project immediately checks the "
                "exact bytes and returns raw diagnostics; only a complete axiom-clean "
                "declaration can leave this source-owning workspace."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["lean_source", "candidate_declaration_name"],
                "properties": {
                    "lean_source": {"type": "string"},
                    "candidate_declaration_name": {"type": "string"},
                },
            },
            terminal=True,
        ),
        ClientToolDefinition(
            name=LEAN_SOURCE_EDIT_TOOL,
            description=(
                "Apply one ordered atomic batch of exact model-authored text edits and "
                "immediately check the complete result. Runtime applies every edit or "
                "none and never parses Lean. Use submit_lean_source for initial source "
                "or declaration-identity changes."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["edits"],
                "properties": {"edits": model_exact_text_edits_json_schema()},
            },
            terminal=True,
        ),
        ClientToolDefinition(
            name=LEAN_SOURCE_READ_TOOL,
            description=(
                "Read one exact line range from the current model-owned Lean source. "
                "The observation includes the complete source hash and declaration "
                "identity; it never edits, compiles, or promotes the source."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["line_start", "line_end"],
                "properties": {
                    "line_start": {"type": "integer", "minimum": 1},
                    "line_end": {"type": "integer", "minimum": 1},
                },
            },
        ),
        ClientToolDefinition(
            name=LEAN_SCRATCH_TOOL,
            description=(
                "Compile one self-contained model-authored Lean scratch file, including "
                "its imports, in the active project. Raw #check, #print, example, or "
                "diagnostic output returns here without changing the current candidate. "
                "Scratch execution is never proof or promotion evidence."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["lean_source"],
                "properties": {"lean_source": {"type": "string"}},
            },
        ),
        ClientToolDefinition(
            name="search_formal_environment",
            description=(
                "Search declarations and modules indexed from the active Lean project "
                "and its configured dependency/source scopes. Results are suggestions "
                "and must be checked by Lean."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 8,
                    },
                },
            },
        ),
    ]
    if include_project_tools:
        tools[3:3] = [
            ClientToolDefinition(
                name=LEAN_SUPPORT_FILE_WRITE_TOOL,
                description=(
                    "Create or replace one complete model-authored .lean support file "
                    "at a canonical project-relative path. This changes no target "
                    "source and performs no compile; check the file explicitly before "
                    "the target imports it."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "content"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "content": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": MAX_LEAN_PROJECT_FILE_BYTES,
                        },
                    },
                },
            ),
            ClientToolDefinition(
                name=LEAN_SUPPORT_FILE_EDIT_TOOL,
                description=(
                    "Apply one atomic exact model-authored edit batch to a current "
                    "support file. Supply its current SHA-256; all generated build "
                    "state is invalidated and the runtime never parses Lean."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "current_content_sha256", "edits"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "current_content_sha256": {"type": "string", "minLength": 64},
                        "edits": model_exact_text_edits_json_schema(),
                    },
                },
            ),
            ClientToolDefinition(
                name=LEAN_SUPPORT_FILE_READ_TOOL,
                description=(
                    "Read an exact line range from one current model-authored Lean "
                    "support file, including its SHA-256."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "line_start", "line_end"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "line_start": {"type": "integer", "minimum": 1},
                        "line_end": {"type": "integer", "minimum": 1},
                    },
                },
            ),
            ClientToolDefinition(
                name=LEAN_SUPPORT_FILE_REMOVE_TOOL,
                description=(
                    "Remove one current model-authored Lean support file using its "
                    "exact current SHA-256."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "current_content_sha256"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "current_content_sha256": {"type": "string", "minLength": 64},
                    },
                },
            ),
            ClientToolDefinition(
                name=LEAN_SUPPORT_FILE_CHECK_TOOL,
                description=(
                    "Compile one selected current support file after the already "
                    "successful model-established build order. Raw Lean diagnostics "
                    "return here; success is support evidence, never target proof."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                    },
                },
            ),
        ]
    if include_formal_gap:
        tools.append(
            ClientToolDefinition(
                name=LEAN_FORMAL_GAP_TOOL,
                description=(
                    "Report a concrete active-environment blocker for the unchanged "
                    "target after search, scratch, inspection, or compiler evidence. "
                    "Errors in model-authored source are revision feedback; an existing "
                    "target statement must elaborate first. This terminal result is not proof."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["summary"],
                    "properties": {
                        "summary": {"type": "string"},
                        "missing_primitives": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "blocking_observations": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                terminal=True,
            )
        )
    if include_proof_search:
        tools.insert(
            2,
            ClientToolDefinition(
                name="search_proof_candidates",
                description=(
                    "Ask the configured prover for candidate proof bodies and raw "
                    "diagnostics for the exact current target. Results are suggestions "
                    "only. Optionally provide exact model-authored imports and local "
                    "declarations as lean_header for the prover's isolated compile; "
                    "runtime neither derives nor applies it. Choose any useful idea "
                    "yourself, then submit the complete source for an immediate Lean check."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "lean_header": {
                            "type": "string",
                            "maxLength": 20000,
                        },
                        "max_results": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 8,
                        },
                    },
                },
            ),
        )
    if include_state_inspection:
        tools.insert(
            -1,
            ClientToolDefinition(
                name="inspect_lean_state",
                description=(
                    "Inspect the exact current source through the configured Lean "
                    "LSP/MCP or local proof-state provider after a failed check. "
                    "This is especially useful after Lean reports that the declaration "
                    "elaborated but its proof remains untrusted. "
                    "Returns raw diagnostic and goal observations; it never edits "
                    "or promotes the source."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {},
                },
            ),
        )
    if include_declaration_inspection:
        tools.insert(
            -1,
            ClientToolDefinition(
                name="inspect_lean_declaration",
                description=(
                    "Ask Lean LSP/MCP for the exact source context of a declaration "
                    "identifier selected from formal-environment search or referenced "
                    "by the current checked source. Choose the exact symbol and context "
                    "yourself. For an indexed active-project declaration, the result "
                    "binds its importable module identity, qualified name, namespace, "
                    "exact signature, bounded module prefix, and nearby source into one "
                    "active_project_api_context. This read-only observation can be used "
                    "as an atomic executable API example; it never edits or promotes "
                    "source."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {"type": "string"},
                        "context_lines": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 40,
                        },
                    },
                },
            ),
        )
    return tuple(tools)
