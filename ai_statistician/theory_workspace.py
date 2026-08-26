from __future__ import annotations

import hashlib
import json
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    CLIENT_TOOL_RECENT_HISTORY_ROUNDS,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    persist_client_tool_session,
    resume_client_tool_session_from_checkpoint,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .research_source_library import (
    MAX_SOURCE_SEARCH_HITS,
    RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_RESULT_READ_TOOL,
    RESEARCH_SOURCE_RUN_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceExecutionSpec,
    ResearchSourceSnapshot,
    execute_research_source,
    read_source_replication_result,
    source_replication_model_observation,
)
from .research_source_discovery import (
    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE,
    RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
    ResearchSourceDiscovery,
    ResearchSourceDiscoveryError,
    ResearchSourceDiscoveryInputError,
)
from .scientific_sandbox import (
    SCIENTIFIC_WASM_SANDBOX_PROFILE,
    ScientificInputArtifactBinding,
    execute_scientific_sandbox,
    generated_code_draft_json_schema,
)
from .structured_output_retry import PacketValidationError


THEORY_WORKSPACE_CHECKPOINT_KIND = "TheoryDeveloperWorkspaceCheckpoint"
THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND = (
    "TheoryDeveloperProgressCheckpoint"
)
THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT = "model_owned_documents_and_handoff_v2"
THEORY_WORKSPACE_WRITE_TOOL = "write_theory_workspace"
THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL = "write_theory_document"
THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL = "edit_theory_document"
THEORY_WORKSPACE_READ_DOCUMENT_TOOL = "read_theory_document"
THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL = "search_theory_documents"
THEORY_WORKSPACE_COMMIT_TOOL = "commit_theory_checkpoint"
THEORY_WORKSPACE_PROGRESS_TOOL = "checkpoint_theory_progress"
SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL = "commit_source_replication_checkpoint"
THEORY_WORKSPACE_GAP_TOOL = "report_theory_gap"
THEORY_SCRATCHPAD_TOOL = "run_theory_scratchpad"
THEORY_WORKSPACE_CONTENT_AUTHORITY = "model_authored_markdown_latex_documents"
THEORY_WORKSPACE_HANDOFF_ROLE = "structured_cross_agent_index_and_abi"
SOURCE_REPLICATION_CHECKPOINT_KIND = "SourceReplicationCheckpoint"
THEORY_WORKSPACE_DOCUMENT_SUFFIXES = frozenset({".md", ".tex", ".bib"})
MAX_THEORY_DOCUMENT_OBSERVATION_CHARS = 50_000
MAX_THEORY_DOCUMENT_SEARCH_HITS = 20
THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE = (
    "THEORY_SCRATCHPAD_EXECUTION_NOT_PROOF_EVIDENCE"
)
TheoryWorkspaceCandidateBuilder = Callable[
    [
        Mapping[str, Any],
        tuple[str, ...],
        Mapping[str, Any],
        tuple[str, ...],
    ],
    Mapping[str, Any],
]
TheoryWorkspaceCandidateValidator = Callable[[Mapping[str, Any]], Sequence[str]]


@dataclass(frozen=True)
class TheoryWorkspaceResult:
    core_packet: Mapping[str, Any]
    evidence: Mapping[str, Any]


class TheoryWorkspaceGapError(RuntimeError):
    """Intentional model-owned stop for an unresolved mathematical gap."""

    def __init__(
        self,
        *,
        theory_gap: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> None:
        super().__init__(str(theory_gap.get("summary", "unresolved theory gap")))
        self.theory_gap = deepcopy(dict(theory_gap))
        self.evidence = deepcopy(dict(evidence))


class TheoryWorkspaceProgressError(RuntimeError):
    """Model-owned partial checkpoint requesting same-owner continuation."""

    def __init__(
        self,
        *,
        progress_checkpoint: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> None:
        progress = progress_checkpoint.get("progress", {})
        summary = (
            str(progress.get("summary", "") or "")
            if isinstance(progress, Mapping)
            else ""
        )
        super().__init__(summary or "theory research progress checkpoint")
        self.progress_checkpoint = deepcopy(dict(progress_checkpoint))
        self.evidence = deepcopy(dict(evidence))


@dataclass(frozen=True)
class TheoryScratchpadConfig:
    """Resource boundary for model-authored exploratory Python/R calculations."""

    sandbox_dir: Path
    seed: int
    replicates: int
    timeout_s: int = 20
    max_runs: int = 2


def theory_scratchpad_client_tool() -> ClientToolDefinition:
    """Return the shared exploratory Python/R tool used by theory agents."""

    scratch_schema = generated_code_draft_json_schema(
        artifact_properties={},
        artifact_required=(),
        code_max_length=100_000,
    )
    scratch_schema["properties"]["execution_profile"]["enum"] = [
        SCIENTIFIC_WASM_SANDBOX_PROFILE
    ]
    scratch_schema["properties"]["source_result_artifact_paths"] = {
        "type": "array",
        "description": (
            "Optional declared UTF-8 result paths from the completed published-"
            "source run. When nonempty, define run_sandbox(seed, replicates, "
            "artifacts); artifacts maps each selected path to exact content, "
            "media_type, and sha256."
        ),
        "uniqueItems": True,
        "maxItems": 8,
        "items": {"type": "string", "minLength": 1},
    }
    return ClientToolDefinition(
        name=THEORY_SCRATCHPAD_TOOL,
        description=(
            "Run one complete model-authored exploratory Python or R calculation, "
            "including exact symbolic algebra with SymPy when useful, "
            "in the isolated scientific sandbox. Define, but do not call, "
            "run_sandbox(seed, replicates); when selecting source-result artifacts, "
            "accept the additional artifacts argument described in the schema. It "
            "must return named JSON-finite quantities or predicates computed from the definitions, not a prewritten verdict or unconditional verification "
            "flag. Raw results return here and never edit theory automatically."
        ),
        input_schema=scratch_schema,
    )


def execute_theory_scratchpad_tool(
    *,
    tool_input: Mapping[str, Any],
    scratchpad: TheoryScratchpadConfig,
    sandbox_binding: Sequence[Any],
    artifact_id: str,
    run_index: int,
    owner_label: str,
    input_artifacts: Sequence[ScientificInputArtifactBinding] = (),
) -> tuple[ClientToolExecutionResult, dict[str, Any]]:
    """Execute exact model-authored exploratory code and return compact lineage."""

    language = str(tool_input.get("language", "") or "")
    execution_profile = str(tool_input.get("execution_profile", "") or "")
    dependencies = tool_input.get("dependencies", [])
    code = str(tool_input.get("code", "") or "")
    entrypoint = str(tool_input.get("entrypoint", "") or "")
    if entrypoint != "run_sandbox":
        raise ClientToolInputError(
            "theory scratchpad entrypoint must be run_sandbox"
        )
    if execution_profile != SCIENTIFIC_WASM_SANDBOX_PROFILE:
        raise ClientToolInputError(
            "theory scratchpad execution_profile must be scientific_wasm"
        )
    if not isinstance(dependencies, list):
        raise ClientToolInputError(
            "theory scratchpad dependencies must be an array"
        )
    execution = execute_scientific_sandbox(
        sandbox_dir=(
            scratchpad.sandbox_dir / stable_hash(list(sandbox_binding))[:16]
        ),
        artifact_id=artifact_id,
        language=language,
        code=code,
        dependencies=[str(value) for value in dependencies],
        seed=int(scratchpad.seed),
        replicates=int(scratchpad.replicates),
        timeout_s=int(scratchpad.timeout_s),
        max_output_bytes=64 * 1024,
        input_artifacts=input_artifacts,
    )
    request_hash = execution.request_hash or stable_hash(
        {
            "schema_version": 1,
            "artifact_kind": "TheoryScratchpadModelToolRequest",
            "artifact_id": artifact_id,
            "language": language,
            "execution_profile": execution_profile,
            "dependencies": [str(value) for value in dependencies],
            "entrypoint": entrypoint,
            "code_hash": execution.code_hash or stable_hash(code),
            "seed": int(scratchpad.seed),
            "replicates": int(scratchpad.replicates),
            "timeout_s": int(scratchpad.timeout_s),
            "max_output_bytes": 64 * 1024,
            "sandbox_binding_hash": stable_hash(list(sandbox_binding)),
            "input_artifact_hashes": {
                binding.artifact_id: binding.content_sha256
                for binding in input_artifacts
            },
        }
    )
    request_identity_source = (
        "scientific_sandbox_request"
        if execution.request_hash
        else "model_tool_request"
    )
    execution_ref = {
        "scratch_run": int(run_index),
        "status": execution.status,
        "language": execution.language,
        "execution_attempted": execution.execution_attempted,
        "returncode": execution.returncode,
        "dependencies": list(execution.dependencies),
        "errors": list(execution.errors),
        "code_hash": execution.code_hash,
        "request_hash": request_hash,
        "request_identity_source": request_identity_source,
        "result_hash": execution.result_hash,
        "metrics_hash": stable_hash(execution.metrics),
        "code_path": execution.code_path,
        "request_path": execution.request_path,
        "result_path": execution.result_path,
        "runtime_edited_source": False,
        "runtime_edited_theory": False,
        "input_artifact_hashes": dict(execution.input_artifact_hashes),
        "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    }
    observation = {
        "scratch_run": int(run_index),
        "remaining_scratch_runs": max(0, scratchpad.max_runs - run_index),
        **execution.to_json(),
        "request_hash": request_hash,
        "request_identity_source": request_identity_source,
        "seed": int(scratchpad.seed),
        "replicates": int(scratchpad.replicates),
        "timeout_s": int(scratchpad.timeout_s),
        "runtime_edited_source": False,
        "runtime_edited_theory": False,
        "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
        "boundary": (
            "This is a model-authored exploratory calculation returned to the "
            f"same {owner_label} session. It may expose a counterexample or "
            "numerical inconsistency, but it is not confirmatory simulation "
            "evidence and not theorem proof evidence."
        ),
    }
    result = ClientToolExecutionResult(
        content={"ok": True, **observation},
        state_changed=True,
        observation_key=(
            "theory-scratchpad:"
            + stable_hash(
                [
                    list(sandbox_binding),
                    run_index,
                    execution.code_hash,
                    request_hash,
                    execution.status,
                    execution.result_hash,
                    list(execution.errors),
                ]
            )
        ),
    )
    return result, execution_ref


def run_theory_artifact_workspace(
    *,
    provider: Any,
    system_prompt: str,
    user_prompt: str,
    model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    workspace_id: str,
    question_id: str,
    authoring_binding_id: str,
    workspace_operation: str,
    initial_artifacts: Mapping[str, Any],
    initial_documents: Mapping[str, str] | None = None,
    read_only_artifacts: Mapping[str, Any] | None = None,
    build_candidate: TheoryWorkspaceCandidateBuilder,
    validate_candidate: TheoryWorkspaceCandidateValidator,
    request_metadata: Mapping[str, Any] | None = None,
    scratchpad: TheoryScratchpadConfig | None = None,
    research_sources: ResearchSourceSnapshot | None = None,
    research_source_discovery: ResearchSourceDiscovery | None = None,
    research_source_execution: ResearchSourceExecutionSpec | None = None,
    allow_source_replication_checkpoint: bool = False,
    task_intent: Mapping[str, str] | None = None,
    workspace_dir: Path | None = None,
    require_document_authority: bool = False,
    writable_artifact_names: Sequence[str] | None = None,
    prior_changed_artifact_names: Sequence[str] = (),
    prior_changed_document_paths: Sequence[str] = (),
    prior_client_tool_session_ref: Mapping[str, Any] | None = None,
) -> TheoryWorkspaceResult:
    """Let one model author text mathematics and a structured handoff in place."""

    if not all(
        str(value).strip()
        for value in (
            workspace_id,
            question_id,
            authoring_binding_id,
            workspace_operation,
        )
    ):
        raise ValueError(
            "theory workspace requires workspace, question, authoring, and "
            "operation identity"
        )
    for value, label in (
        (max_turns, "turn"),
        (max_tool_calls, "tool-call"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"theory workspace {label} budget must be positive")
    if scratchpad is not None:
        for value, label in (
            (scratchpad.replicates, "scratch replicate"),
            (scratchpad.timeout_s, "scratch timeout"),
            (scratchpad.max_runs, "scratch run"),
        ):
            if value < 1:
                raise ValueError(f"theory workspace {label} budget must be positive")
    if research_source_execution is not None and research_sources is None:
        raise ValueError(
            "research source execution requires a configured research source snapshot"
        )
    if allow_source_replication_checkpoint and research_source_execution is None:
        raise ValueError(
            "source replication checkpoint requires source execution"
        )
    parent = {
        str(name): deepcopy(value)
        for name, value in initial_artifacts.items()
        if str(name).strip()
    }
    if not parent:
        raise ValueError("theory workspace requires initial artifacts")
    parent_documents = _normalized_theory_documents(initial_documents or {})
    if require_document_authority and workspace_dir is None:
        prior_session_root = str(
            (prior_client_tool_session_ref or {}).get("root_path", "") or ""
        ).strip()
        if prior_session_root:
            prior_session_root_path = Path(prior_session_root)
            if not prior_session_root_path.is_absolute():
                raise ValueError(
                    "theory client-tool session root must be absolute"
                )
            workspace_dir = prior_session_root_path
        else:
            workspace_dir = Path(tempfile.mkdtemp(prefix="ai-stat-theory-"))
    resolved_workspace_dir = workspace_dir.resolve() if workspace_dir else None
    if resolved_workspace_dir is not None:
        resolved_workspace_dir.mkdir(parents=True, exist_ok=True)
        _persist_theory_documents(
            parent_documents,
            workspace_dir=resolved_workspace_dir,
        )
    read_only = {
        str(name): deepcopy(value)
        for name, value in (read_only_artifacts or {}).items()
        if str(name).strip()
    }
    if research_source_execution is not None and research_sources is not None:
        read_only["research_source_execution_descriptor"] = (
            research_source_execution.descriptor(research_sources)
        )
    overlapping_names = sorted(set(parent).intersection(read_only))
    if overlapping_names:
        raise ValueError(
            "theory workspace read-only names overlap writable artifacts: "
            + ", ".join(overlapping_names)
        )
    parent_hash = stable_hash(
        {"artifacts": parent, "documents": parent_documents}
    )
    artifact_names = tuple(sorted({*parent, *read_only}))
    parent_shapes = {
        name: _artifact_shape(value) for name, value in parent.items()
    }
    selected_writable_names = tuple(
        sorted(
            parent
            if writable_artifact_names is None
            else {
                str(name).strip()
                for name in writable_artifact_names
                if str(name).strip()
            }
        )
    )
    unknown_writable_names = sorted(set(selected_writable_names) - set(parent))
    if unknown_writable_names:
        raise ValueError(
            "theory workspace has unknown writable artifacts: "
            + ", ".join(unknown_writable_names)
        )
    if not selected_writable_names:
        raise ValueError("theory workspace requires a writable artifact")
    writable_artifact_shapes = {
        name: parent_shapes[name] for name in selected_writable_names
    }
    prior_artifact_changes = tuple(
        dict.fromkeys(str(name).strip() for name in prior_changed_artifact_names)
    )
    unknown_prior_artifacts = sorted(set(prior_artifact_changes) - set(parent))
    if unknown_prior_artifacts:
        raise ValueError(
            "theory progress checkpoint has unknown changed artifacts: "
            + ", ".join(unknown_prior_artifacts)
        )
    prior_document_changes = tuple(
        dict.fromkeys(
            _normalized_theory_document_path(path)
            for path in prior_changed_document_paths
        )
    )
    unknown_prior_documents = sorted(
        set(prior_document_changes) - set(parent_documents)
    )
    if unknown_prior_documents:
        raise ValueError(
            "theory progress checkpoint has unknown changed documents: "
            + ", ".join(unknown_prior_documents)
        )
    state: dict[str, Any] = {
        "artifacts": deepcopy(parent),
        "documents": deepcopy(parent_documents),
        "reads": 0,
        "submissions": 0,
        "last_validation_errors": [],
        "last_candidate": {},
        "model_artifact_writes": [],
        "model_document_writes": [],
        "document_inspection_refs": [],
        "scratch_runs": 0,
        "scratch_execution_refs": [],
        "source_search_refs": [],
        "source_read_refs": [],
        "source_discovery_search_refs": [],
        "source_discovery_read_refs": [],
        "source_replication_runs": 0,
        "source_replication_manifests": [],
        "source_result_read_refs": [],
    }
    tools = _theory_workspace_tools(
        scratchpad_enabled=scratchpad is not None,
        research_sources_enabled=research_sources is not None,
        research_source_discovery_enabled=research_source_discovery is not None,
        research_source_execution_enabled=research_source_execution is not None,
        source_replication_checkpoint_enabled=allow_source_replication_checkpoint,
        document_authority_enabled=require_document_authority,
    )

    def current_changed_artifact_names(
        artifacts: Mapping[str, Any],
    ) -> tuple[str, ...]:
        return tuple(
            name
            for name in selected_writable_names
            if stable_hash(artifacts[name]) != stable_hash(parent[name])
        )

    def changed_artifact_names(artifacts: Mapping[str, Any]) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                [
                    *prior_artifact_changes,
                    *current_changed_artifact_names(artifacts),
                ]
            )
        )

    def current_changed_document_paths(
        documents: Mapping[str, str],
    ) -> tuple[str, ...]:
        return tuple(
            sorted(
                path
                for path in set(parent_documents).union(documents)
                if documents.get(path) != parent_documents.get(path)
            )
        )

    def changed_document_paths(documents: Mapping[str, str]) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                [
                    *prior_document_changes,
                    *current_changed_document_paths(documents),
                ]
            )
        )

    def document_manifest(documents: Mapping[str, str]) -> dict[str, Any]:
        return theory_workspace_document_manifest(
            documents,
            workspace_dir=resolved_workspace_dir,
        )

    def source_discovery_evidence() -> dict[str, Any]:
        return {
            "research_source_discovery": (
                dict(research_source_discovery.descriptor())
                if research_source_discovery is not None
                else {"configured": False}
            ),
            "source_discovery_search_refs": deepcopy(
                state["source_discovery_search_refs"]
            ),
            "source_discovery_read_refs": deepcopy(
                state["source_discovery_read_refs"]
            ),
        }

    def readable_artifact(name: str) -> Any:
        if name in read_only:
            return read_only[name]
        return state["artifacts"][name]

    def evaluate_model_write(
        candidate_artifacts: Mapping[str, Any],
        candidate_documents: Mapping[str, str],
        *,
        artifact_writes: Sequence[Mapping[str, Any]] = (),
        document_writes: Sequence[Mapping[str, Any]] = (),
    ) -> ClientToolExecutionResult:
        state["submissions"] += 1
        state_changed = stable_hash(
            {
                "artifacts": candidate_artifacts,
                "documents": candidate_documents,
            }
        ) != stable_hash(
            {
                "artifacts": state["artifacts"],
                "documents": state["documents"],
            }
        )
        state["artifacts"] = deepcopy(dict(candidate_artifacts))
        state["documents"] = deepcopy(dict(candidate_documents))
        if resolved_workspace_dir is not None:
            _persist_theory_documents(
                candidate_documents,
                workspace_dir=resolved_workspace_dir,
            )
        if state_changed and artifact_writes:
            state["model_artifact_writes"].extend(
                [
                    {
                        "submission_index": state["submissions"] - 1,
                        **deepcopy(dict(row)),
                    }
                    for row in artifact_writes
                ]
            )
        if state_changed and document_writes:
            state["model_document_writes"].extend(
                [
                    {
                        "submission_index": state["submissions"] - 1,
                        **deepcopy(dict(row)),
                    }
                    for row in document_writes
                ]
            )
        changed = changed_artifact_names(candidate_artifacts)
        changed_documents = changed_document_paths(candidate_documents)
        if (
            allow_source_replication_checkpoint
            and document_writes
            and not artifact_writes
        ):
            state["last_candidate"] = {}
            state["last_validation_errors"] = []
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "state_changed": state_changed,
                    "write_accepted": True,
                    "source_report_write_ready": bool(changed_documents),
                    "changed_artifact_names": list(changed),
                    "changed_document_paths": list(changed_documents),
                    "submissions": state["submissions"],
                    "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
                    "runtime_edited_theory": False,
                    "proof_evidence_status": (
                        "SOURCE_REPLICATION_REPORT_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=state_changed,
                terminal=False,
                observation_key="source-replication-report-write:"
                + stable_hash(
                    [
                        workspace_id,
                        [
                            (path, _text_sha256(candidate_documents[path]))
                            for path in changed_documents
                        ],
                    ]
                ),
            )
        if not changed and not changed_documents:
            errors = [
                "the submitted theory workspace is unchanged from its parent"
            ]
            candidate: dict[str, Any] = {}
        else:
            raw_candidate = build_candidate(
                candidate_artifacts,
                changed,
                document_manifest(candidate_documents),
                changed_documents,
            )
            if not isinstance(raw_candidate, Mapping):
                raise ClientToolInputError(
                    "theory workspace candidate builder returned a non-object"
                )
            candidate = deepcopy(dict(raw_candidate))
            errors = [
                str(error)
                for error in validate_candidate(candidate)
                if str(error).strip()
            ]
        state["last_candidate"] = candidate
        state["last_validation_errors"] = errors
        candidate_hash = stable_hash(candidate) if candidate else ""
        common_content = {
            "ok": True,
            "state_changed": state_changed,
            "candidate_hash": candidate_hash,
            "changed_artifact_names": list(changed),
            "changed_document_paths": list(changed_documents),
            "submissions": state["submissions"],
            "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
            "model_artifact_writes_applied": len(artifact_writes),
            "model_document_writes_applied": len(document_writes),
            "runtime_edited_theory": False,
        }
        if errors:
            content = {
                **common_content,
                "write_accepted": True,
                "workspace_valid": False,
                "validation_errors": errors,
                "omitted_artifacts_retained": True,
                "proof_evidence_status": (
                    "THEORY_WORKSPACE_VALIDATION_NOT_PROOF_EVIDENCE"
                ),
            }
            return ClientToolExecutionResult(
                content=content,
                state_changed=state_changed,
                terminal=False,
                observation_key="theory-workspace-validation:"
                + stable_hash([candidate_hash, errors]),
            )
        checkpoint_blockers: list[str] = []
        if require_document_authority and not changed_documents:
            checkpoint_blockers.append("authoritative_document_change_required")
        return ClientToolExecutionResult(
            content={
                **common_content,
                "write_accepted": True,
                "workspace_valid": True,
                "validation_errors": [],
                "checkpoint_committed": False,
                "checkpoint_commit_ready": not checkpoint_blockers,
                "checkpoint_blockers": checkpoint_blockers,
                "proof_evidence_status": (
                    "THEORY_WORKSPACE_SUBMISSION_NOT_PROOF_EVIDENCE"
                ),
            },
            state_changed=state_changed,
            terminal=False,
            observation_key="theory-workspace-valid:" + candidate_hash,
        )

    def execute_tool(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == "read_theory_workspace":
            if set(tool_input) - {"artifact_names", "document_paths"}:
                raise ClientToolInputError(
                    "read_theory_workspace accepts artifact_names and document_paths"
                )
            requested = tool_input.get("artifact_names", [])
            requested_documents = tool_input.get("document_paths", [])
            for values, label in (
                (requested, "artifact_names"),
                (requested_documents, "document_paths"),
            ):
                if not isinstance(values, Sequence) or isinstance(
                    values, (str, bytes)
                ):
                    raise ClientToolInputError(
                        f"read_theory_workspace {label} must be an array"
                    )
            if not requested and not requested_documents:
                raise ClientToolInputError(
                    "read_theory_workspace requires at least one artifact or document"
                )
            names = [str(name) for name in requested]
            if len(names) != len(set(names)):
                raise ClientToolInputError("theory workspace read names must be unique")
            unknown = sorted(set(names) - set(artifact_names))
            if unknown:
                raise ClientToolInputError(
                    "unknown theory workspace artifacts: " + ", ".join(unknown)
                )
            selected = {
                name: deepcopy(readable_artifact(name)) for name in names
            }
            document_paths = [
                _normalized_theory_document_path(path)
                for path in requested_documents
            ]
            if len(document_paths) != len(set(document_paths)):
                raise ClientToolInputError(
                    "theory workspace document paths must be unique"
                )
            unknown_documents = sorted(
                set(document_paths) - set(state["documents"])
            )
            if unknown_documents:
                raise ClientToolInputError(
                    "unknown theory workspace documents: "
                    + ", ".join(unknown_documents)
                )
            selected_documents = {
                path: state["documents"][path] for path in document_paths
            }
            if len(_compact_json(selected)) + sum(
                len(value) for value in selected_documents.values()
            ) > 55_000:
                raise ClientToolInputError(
                    "selected theory material exceeds one observation; read less material"
                )
            for path, content in selected_documents.items():
                state["document_inspection_refs"].append(
                    {
                        "tool": "read_theory_workspace",
                        "path": path,
                        "document_sha256": _text_sha256(content),
                        "complete_document": True,
                        "line_start": 1,
                        "line_end": len(content.splitlines()),
                        "content_sha256": _text_sha256(content),
                        "proof_evidence_status": (
                            "THEORY_DOCUMENT_INSPECTION_NOT_PROOF_EVIDENCE"
                        ),
                    }
                )
            state["reads"] += 1
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "artifacts": selected,
                    "artifact_hashes": {
                        name: stable_hash(selected[name]) for name in names
                    },
                    "documents": selected_documents,
                    "document_sha256": {
                        path: _text_sha256(selected_documents[path])
                        for path in document_paths
                    },
                    "reads": state["reads"],
                    "proof_evidence_status": (
                        "THEORY_WORKSPACE_READ_NOT_PROOF_EVIDENCE"
                    ),
                },
                observation_key="theory-workspace-read:"
                + stable_hash(
                    [
                        workspace_id,
                        [(name, stable_hash(selected[name])) for name in names],
                        [
                            (path, _text_sha256(selected_documents[path]))
                            for path in document_paths
                        ],
                    ]
                ),
            )

        if call.name == THEORY_WORKSPACE_READ_DOCUMENT_TOOL:
            if set(tool_input) != {"path", "line_start", "line_end"}:
                raise ClientToolInputError(
                    "read_theory_document requires path, line_start, and line_end"
                )
            observation, inspection_ref = read_theory_document_lines(
                state["documents"],
                path=tool_input.get("path"),
                line_start=tool_input.get("line_start"),
                line_end=tool_input.get("line_end"),
            )
            state["document_inspection_refs"].append(inspection_ref)
            state["reads"] += 1
            return ClientToolExecutionResult(
                content={
                    **observation,
                    "reads": state["reads"],
                },
                observation_key="theory-document-read:"
                + stable_hash(inspection_ref),
            )

        if call.name == THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL:
            if set(tool_input) - {"query", "document_paths", "max_results"}:
                raise ClientToolInputError(
                    "search_theory_documents accepts query, document_paths, and "
                    "optional max_results"
                )
            observation, inspection_ref = search_theory_document_lines(
                state["documents"],
                query=tool_input.get("query"),
                document_paths=tool_input.get("document_paths", []),
                max_results=tool_input.get(
                    "max_results", MAX_THEORY_DOCUMENT_SEARCH_HITS
                ),
            )
            state["document_inspection_refs"].append(inspection_ref)
            state["reads"] += 1
            return ClientToolExecutionResult(
                content={
                    **observation,
                    "reads": state["reads"],
                },
                observation_key="theory-document-search:"
                + stable_hash(inspection_ref),
            )

        if call.name == RESEARCH_SOURCE_SEARCH_TOOL:
            if research_sources is None:
                raise ClientToolInputError("research source snapshot is unavailable")
            if set(tool_input) - {"query", "top_k"}:
                raise ClientToolInputError(
                    "search_research_sources accepts query and optional top_k"
                )
            query = tool_input.get("query")
            top_k = tool_input.get("top_k", 5)
            if not isinstance(query, str):
                raise ClientToolInputError("research source query must be text")
            if isinstance(top_k, bool) or not isinstance(top_k, int):
                raise ClientToolInputError("research source top_k must be an integer")
            try:
                observation = research_sources.search(query, top_k=top_k)
            except ValueError as exc:
                raise ClientToolInputError(str(exc)) from exc
            source_ref = {
                "tool": RESEARCH_SOURCE_SEARCH_TOOL,
                "snapshot_id": observation["snapshot_id"],
                "snapshot_hash": observation["snapshot_hash"],
                "query_hash": observation["query_hash"],
                "retrieval_policy": observation["retrieval_policy"],
                "hits": [
                    {
                        key: hit[key]
                        for key in (
                            "document_id",
                            "sha256",
                            "line_start",
                            "line_end",
                            "score",
                            "matched_terms",
                        )
                        if key in hit
                    }
                    for hit in observation["hits"]
                ],
                "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
            }
            state["source_search_refs"].append(source_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key="research-source-search:" + stable_hash(source_ref),
            )

        if call.name == RESEARCH_SOURCE_READ_TOOL:
            if research_sources is None:
                raise ClientToolInputError("research source snapshot is unavailable")
            if set(tool_input) != {"document_id", "line_start", "line_end"}:
                raise ClientToolInputError(
                    "read_research_source requires document_id, line_start, and line_end"
                )
            document_id = tool_input.get("document_id")
            line_start = tool_input.get("line_start")
            line_end = tool_input.get("line_end")
            if not isinstance(document_id, str):
                raise ClientToolInputError(
                    "research source document_id must be text"
                )
            if any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in (line_start, line_end)
            ):
                raise ClientToolInputError(
                    "research source line_start and line_end must be integers"
                )
            try:
                observation = research_sources.read(
                    document_id,
                    line_start=line_start,
                    line_end=line_end,
                )
            except ValueError as exc:
                raise ClientToolInputError(str(exc)) from exc
            source_ref = {
                "tool": RESEARCH_SOURCE_READ_TOOL,
                "snapshot_id": observation["snapshot_id"],
                "snapshot_hash": observation["snapshot_hash"],
                "document_id": observation["document_id"],
                "document_sha256": observation["sha256"],
                "line_start": observation["line_start"],
                "line_end": observation["line_end"],
                "content_sha256": observation["content_sha256"],
                "citation_ref": observation["citation_ref"],
                "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
            }
            state["source_read_refs"].append(source_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key="research-source-read:" + stable_hash(source_ref),
            )

        if call.name == RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL:
            if research_source_discovery is None:
                raise ClientToolInputError(
                    "public research source discovery is unavailable"
                )
            if set(tool_input) - {"query", "source_kind", "top_k"}:
                raise ClientToolInputError(
                    "discover_research_sources accepts query, source_kind, and top_k"
                )
            try:
                observation = research_source_discovery.search(
                    tool_input.get("query", ""),
                    source_kind=tool_input.get("source_kind", "all"),
                    top_k=tool_input.get("top_k", 5),
                )
            except ResearchSourceDiscoveryInputError as exc:
                raise ClientToolInputError(str(exc)) from exc
            except ResearchSourceDiscoveryError as exc:
                return ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "public_research_source_discovery_failed",
                        "detail": str(exc)[:1_200],
                        "model_may_continue_without_this_source": True,
                    },
                    is_error=True,
                    observation_key=(
                        "public-research-source-discovery-failed:"
                        + stable_hash([call.name, type(exc).__name__, str(exc)])
                    ),
                )
            if not isinstance(observation, Mapping):
                raise RuntimeError(
                    "research source discovery returned a non-object observation"
                )
            results = observation.get("results", [])
            source_ref = {
                "tool": RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
                "provider": str(observation.get("provider", "") or ""),
                "source_horizon": str(
                    observation.get("source_horizon", "") or ""
                ),
                "query_hash": str(observation.get("query_hash", "") or ""),
                "source_kind": str(observation.get("source_kind", "") or ""),
                "results": [
                    {
                        key: row[key]
                        for key in (
                            "source_handle",
                            "source_kind",
                            "title",
                            "url",
                            "publication_date",
                        )
                        if key in row
                    }
                    for row in results
                    if isinstance(row, Mapping)
                ],
                "proof_evidence_status": (
                    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
                ),
            }
            state["source_discovery_search_refs"].append(source_ref)
            return ClientToolExecutionResult(
                content=dict(observation),
                observation_key="research-source-discovery-search:"
                + stable_hash(source_ref),
            )

        if call.name == RESEARCH_SOURCE_DISCOVERY_READ_TOOL:
            if research_source_discovery is None:
                raise ClientToolInputError(
                    "public research source discovery is unavailable"
                )
            if set(tool_input) - {"source_handle", "path", "revision"}:
                raise ClientToolInputError(
                    "read_discovered_research_source accepts source_handle, path, "
                    "and revision"
                )
            try:
                observation = research_source_discovery.read(
                    tool_input.get("source_handle", ""),
                    path=tool_input.get("path", ""),
                    revision=tool_input.get("revision", ""),
                )
            except ResearchSourceDiscoveryInputError as exc:
                raise ClientToolInputError(str(exc)) from exc
            except ResearchSourceDiscoveryError as exc:
                return ClientToolExecutionResult(
                    content={
                        "ok": False,
                        "error": "public_research_source_discovery_failed",
                        "detail": str(exc)[:1_200],
                        "model_may_continue_without_this_source": True,
                    },
                    is_error=True,
                    observation_key=(
                        "public-research-source-discovery-failed:"
                        + stable_hash([call.name, type(exc).__name__, str(exc)])
                    ),
                )
            if not isinstance(observation, Mapping):
                raise RuntimeError(
                    "research source discovery read returned a non-object observation"
                )
            source_ref = {
                "tool": RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                **{
                    key: observation[key]
                    for key in (
                        "provider",
                        "source_handle",
                        "source_kind",
                        "title",
                        "url",
                        "publication_date",
                        "revision",
                        "path",
                        "content_sha256",
                        "content_truncated",
                        "citation_ref",
                    )
                    if key in observation
                },
                "proof_evidence_status": (
                    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
                ),
            }
            state["source_discovery_read_refs"].append(source_ref)
            return ClientToolExecutionResult(
                content=dict(observation),
                observation_key="research-source-discovery-read:"
                + stable_hash(source_ref),
            )

        if call.name == RESEARCH_SOURCE_RUN_TOOL:
            if research_sources is None or research_source_execution is None:
                raise ClientToolInputError("research source execution is unavailable")
            if tool_input:
                raise ClientToolInputError("run_research_source accepts no input fields")
            if state["source_replication_runs"]:
                raise ClientToolInputError(
                    "the immutable research source has already been executed"
                )
            execution_root = (
                resolved_workspace_dir
                if resolved_workspace_dir is not None
                else Path(tempfile.mkdtemp(prefix="ai-stat-source-replication-"))
            )
            run_index = state["source_replication_runs"] + 1
            output_dir = execution_root / (
                "source-replication-"
                + stable_hash(
                    [workspace_id, authoring_binding_id, run_index]
                )[:16]
            )
            try:
                manifest = execute_research_source(
                    execution=research_source_execution,
                    research_sources=research_sources,
                    output_dir=output_dir,
                    question_id=question_id,
                )
            except (OSError, UnicodeError, ValueError) as exc:
                raise ClientToolInputError(str(exc)) from exc
            state["source_replication_runs"] = run_index
            state["source_replication_manifests"].append(deepcopy(manifest))
            return ClientToolExecutionResult(
                content={
                    "ok": manifest.get("execution_status") == "EXECUTED",
                    "source_replication_manifest": (
                        source_replication_model_observation(manifest)
                    ),
                    "remaining_source_replication_runs": 0,
                },
                state_changed=True,
                observation_key="research-source-execution:"
                + str(manifest.get("manifest_hash", "") or stable_hash(manifest)),
            )

        if call.name == RESEARCH_SOURCE_RESULT_READ_TOOL:
            if set(tool_input) != {"relative_path", "line_start", "line_end"}:
                raise ClientToolInputError(
                    "read_research_source_result requires relative_path, "
                    "line_start, and line_end"
                )
            if len(state["source_replication_manifests"]) != 1:
                raise ClientToolInputError(
                    "read_research_source_result requires one completed source run"
                )
            try:
                observation = read_source_replication_result(
                    state["source_replication_manifests"][0],
                    relative_path=tool_input.get("relative_path"),
                    line_start=tool_input.get("line_start"),
                    line_end=tool_input.get("line_end"),
                )
            except (OSError, UnicodeError, ValueError) as exc:
                raise ClientToolInputError(str(exc)) from exc
            result_ref = {
                key: observation[key]
                for key in (
                    "artifact_id",
                    "relative_path",
                    "artifact_sha256",
                    "line_count",
                    "line_start",
                    "line_end",
                    "content_sha256",
                    "proof_evidence_status",
                )
            }
            state["source_result_read_refs"].append(result_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key="research-source-result-read:"
                + stable_hash(result_ref),
            )

        if call.name == THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL:
            if not require_document_authority:
                raise ClientToolInputError(
                    "write_theory_document is unavailable"
                )
            candidate_documents, document_write_record = (
                _replace_theory_workspace_document(
                    state["documents"],
                    tool_input,
                )
            )
            return evaluate_model_write(
                state["artifacts"],
                candidate_documents,
                document_writes=[document_write_record],
            )

        if call.name == THEORY_WORKSPACE_WRITE_TOOL:
            if set(tool_input) - {"writes"}:
                raise ClientToolInputError(
                    "write_theory_workspace accepts only structured writes; "
                    "use write_theory_document for Markdown, LaTeX, or BibTeX"
                )
            raw_artifact_writes = tool_input.get("writes", [])
            if not raw_artifact_writes:
                raise ClientToolInputError(
                    "write_theory_workspace requires at least one structured write"
                )
            candidate_artifacts, write_records = (
                _replace_theory_workspace_artifacts(
                    state["artifacts"],
                    raw_artifact_writes,
                    writable_artifact_shapes=writable_artifact_shapes,
                    allow_empty=True,
                )
            )
            return evaluate_model_write(
                candidate_artifacts,
                state["documents"],
                artifact_writes=write_records,
            )

        if call.name == THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL:
            if not require_document_authority:
                raise ClientToolInputError(
                    "localized theory document editing is unavailable"
                )
            candidate_documents, edit_record = (
                _edit_theory_workspace_document(
                    state["documents"],
                    tool_input,
                )
            )
            return evaluate_model_write(
                state["artifacts"],
                candidate_documents,
                document_writes=[edit_record],
            )

        if call.name == THEORY_WORKSPACE_COMMIT_TOOL:
            if set(tool_input) != {"readiness_rationale"}:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires exactly readiness_rationale"
                )
            readiness_rationale = tool_input.get("readiness_rationale")
            if (
                not isinstance(readiness_rationale, str)
                or not readiness_rationale.strip()
            ):
                raise ClientToolInputError(
                    "theory checkpoint readiness_rationale must be nonempty"
                )
            changed = changed_artifact_names(state["artifacts"])
            changed_documents = changed_document_paths(state["documents"])
            if (not changed and not changed_documents) or not state["submissions"]:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires a prior model-authored "
                    "workspace revision"
                )
            if require_document_authority and not state["documents"]:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires model-authored Markdown or LaTeX"
                )
            if require_document_authority and not changed_documents:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires a changed authoritative "
                    "Markdown or LaTeX document"
                )
            raw_candidate = build_candidate(
                state["artifacts"],
                changed,
                document_manifest(state["documents"]),
                changed_documents,
            )
            if not isinstance(raw_candidate, Mapping):
                raise ClientToolInputError(
                    "theory workspace candidate builder returned a non-object"
                )
            candidate = deepcopy(dict(raw_candidate))
            errors = [
                str(error)
                for error in validate_candidate(candidate)
                if str(error).strip()
            ]
            state["last_candidate"] = candidate
            state["last_validation_errors"] = errors
            if errors:
                raise ClientToolInputError(
                    "theory checkpoint is not structurally valid: "
                    + "; ".join(errors[:6])
                )
            rationale = readiness_rationale.strip()
            candidate_hash = stable_hash(candidate)
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "disposition": "THEORY_CHECKPOINT_COMMITTED",
                    "workspace_valid": True,
                    "checkpoint_committed": True,
                    "candidate_hash": candidate_hash,
                    "changed_artifact_names": list(changed),
                    "changed_document_paths": list(changed_documents),
                    "runtime_edited_theory": False,
                    "proof_evidence_status": (
                        "THEORY_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=True,
                terminal=True,
                terminal_payload={
                    "disposition": "THEORY_CHECKPOINT_COMMITTED",
                    "core_packet": candidate,
                    "core_packet_hash": candidate_hash,
                    "workspace_hash": stable_hash(
                        {
                            "artifacts": state["artifacts"],
                            "documents": state["documents"],
                        }
                    ),
                    "changed_artifact_names": list(changed),
                    "changed_document_paths": list(changed_documents),
                    "theory_workspace_manifest": document_manifest(
                        state["documents"]
                    ),
                    "readiness_rationale": rationale,
                },
                observation_key="theory-workspace-committed:"
                + stable_hash([candidate_hash, rationale]),
            )

        if call.name == SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL:
            if not allow_source_replication_checkpoint:
                raise ClientToolInputError(
                    "source replication checkpoint is unavailable"
                )
            if set(tool_input) != {
                "report_document_path",
                "readiness_rationale",
                "unresolved_gaps",
            }:
                raise ClientToolInputError(
                    "commit_source_replication_checkpoint requires exactly "
                    "report_document_path, readiness_rationale, and unresolved_gaps"
                )
            if state["source_replication_runs"] != 1 or len(
                state["source_replication_manifests"]
            ) != 1:
                raise ClientToolInputError(
                    "source replication checkpoint requires one completed source run"
                )
            report_path = _normalized_theory_document_path(
                tool_input.get("report_document_path")
            )
            if report_path not in state["documents"]:
                raise ClientToolInputError(
                    "source replication report document is unavailable"
                )
            if report_path not in changed_document_paths(state["documents"]):
                raise ClientToolInputError(
                    "source replication checkpoint requires a model-authored report"
                )
            rationale = tool_input.get("readiness_rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                raise ClientToolInputError(
                    "source replication readiness_rationale must be nonempty"
                )
            unresolved_gaps = tool_input.get("unresolved_gaps")
            if not isinstance(unresolved_gaps, list) or not all(
                isinstance(value, str) and value.strip()
                for value in unresolved_gaps
            ):
                raise ClientToolInputError(
                    "source replication unresolved_gaps must be an array of nonempty text"
                )
            source_manifest = deepcopy(
                state["source_replication_manifests"][0]
            )
            if (
                source_manifest.get("execution_status") != "EXECUTED"
                and not unresolved_gaps
            ):
                raise ClientToolInputError(
                    "failed source execution requires an explicit unresolved gap"
                )
            workspace_manifest = document_manifest(state["documents"])
            report_rows = [
                row
                for row in workspace_manifest.get("documents", []) or []
                if row.get("relative_path") == report_path
            ]
            if len(report_rows) != 1:
                raise ClientToolInputError(
                    "source replication report identity is ambiguous"
                )
            checkpoint_body = {
                "schema_version": 1,
                "artifact_kind": SOURCE_REPLICATION_CHECKPOINT_KIND,
                "question_id": question_id,
                "workspace_id": workspace_id,
                "task_intent": dict(task_intent or {}),
                "source_replication_manifest_ref": {
                    "artifact_id": str(
                        source_manifest.get("artifact_id", "") or ""
                    ),
                    "manifest_hash": str(
                        source_manifest.get("manifest_hash", "") or ""
                    ),
                    "execution_status": str(
                        source_manifest.get("execution_status", "") or ""
                    ),
                    "stdout_sha256": str(
                        source_manifest.get("stdout_sha256", "") or ""
                    ),
                },
                "report_document": deepcopy(report_rows[0]),
                "unresolved_gaps": [value.strip() for value in unresolved_gaps],
                "readiness_rationale": rationale.strip(),
                "runtime_edited_source": False,
                "runtime_edited_report": False,
                "model_authored_report": True,
                "proof_evidence_status": (
                    "SOURCE_REPLICATION_CHECKPOINT_NOT_PROOF_EVIDENCE"
                ),
                "kernel_verified": False,
            }
            checkpoint_id = "source_replication_checkpoint:" + stable_hash(
                checkpoint_body
            )[:20]
            checkpoint = {
                **checkpoint_body,
                "checkpoint_id": checkpoint_id,
            }
            checkpoint_hash = stable_hash(checkpoint)
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "disposition": "SOURCE_REPLICATION_CHECKPOINT_COMMITTED",
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_hash": checkpoint_hash,
                    "runtime_edited_source": False,
                    "proof_evidence_status": checkpoint[
                        "proof_evidence_status"
                    ],
                },
                state_changed=True,
                terminal=True,
                terminal_payload={
                    "disposition": "SOURCE_REPLICATION_CHECKPOINT_COMMITTED",
                    "core_packet": checkpoint,
                    "core_packet_hash": checkpoint_hash,
                    "workspace_hash": stable_hash(
                        {
                            "artifacts": state["artifacts"],
                            "documents": state["documents"],
                        }
                    ),
                    "changed_artifact_names": list(
                        changed_artifact_names(state["artifacts"])
                    ),
                    "changed_document_paths": list(
                        changed_document_paths(state["documents"])
                    ),
                    "theory_workspace_manifest": workspace_manifest,
                },
                observation_key="source-replication-checkpoint:"
                + checkpoint_hash,
            )

        if call.name == THEORY_SCRATCHPAD_TOOL:
            if scratchpad is None:
                raise ClientToolInputError("theory scratchpad is unavailable")
            if state["scratch_runs"] >= scratchpad.max_runs:
                raise ClientToolInputError(
                    "theory scratchpad run budget is exhausted"
                )
            raw_result_paths = tool_input.get(
                "source_result_artifact_paths", []
            )
            if not isinstance(raw_result_paths, list) or not all(
                isinstance(value, str) and value.strip()
                for value in raw_result_paths
            ):
                raise ClientToolInputError(
                    "theory scratchpad source_result_artifact_paths must be an "
                    "array of nonempty paths"
                )
            input_artifacts: list[ScientificInputArtifactBinding] = []
            if raw_result_paths:
                if len(state["source_replication_manifests"]) != 1:
                    raise ClientToolInputError(
                        "theory scratchpad source-result inputs require one "
                        "completed source run"
                    )
                source_manifest = state["source_replication_manifests"][0]
                result_rows = {
                    str(row.get("relative_path", "") or ""): row
                    for row in source_manifest.get("result_artifacts", []) or []
                    if isinstance(row, Mapping)
                    and str(row.get("relative_path", "") or "")
                }
                for relative_path in dict.fromkeys(raw_result_paths):
                    row = result_rows.get(relative_path)
                    if row is None:
                        raise ClientToolInputError(
                            "unknown source result artifact: " + relative_path
                        )
                    content = row.get("raw_text")
                    if not isinstance(content, str):
                        raise ClientToolInputError(
                            "source result artifact is not available as UTF-8 text: "
                            + relative_path
                        )
                    expected_sha256 = str(row.get("sha256", "") or "")
                    observed_sha256 = hashlib.sha256(
                        content.encode("utf-8")
                    ).hexdigest()
                    if observed_sha256 != expected_sha256:
                        raise ClientToolInputError(
                            "source result artifact hash mismatch: " + relative_path
                        )
                    input_artifacts.append(
                        ScientificInputArtifactBinding(
                            artifact_id=relative_path,
                            content=content,
                            content_sha256=observed_sha256,
                            media_type="text/plain",
                        )
                    )
            run_index = state["scratch_runs"] + 1
            execution_result, execution_ref = execute_theory_scratchpad_tool(
                tool_input=tool_input,
                scratchpad=scratchpad,
                sandbox_binding=[workspace_id, authoring_binding_id],
                artifact_id=(
                    f"theory-scratch-{stable_hash(workspace_id)[:12]}-{run_index}"
                ),
                run_index=run_index,
                owner_label="TheoryDeveloper",
                input_artifacts=input_artifacts,
            )
            state["scratch_runs"] = run_index
            state["scratch_execution_refs"].append(execution_ref)
            return execution_result

        if call.name == THEORY_WORKSPACE_PROGRESS_TOOL:
            if not require_document_authority:
                raise ClientToolInputError(
                    "theory progress checkpoints require document authority"
                )
            if set(tool_input) != {"summary", "evidence_refs", "next_step"}:
                raise ClientToolInputError(
                    "checkpoint_theory_progress requires exactly summary, "
                    "evidence_refs, and next_step"
                )
            summary = tool_input.get("summary")
            evidence_refs = tool_input.get("evidence_refs")
            next_step = tool_input.get("next_step")
            if not isinstance(summary, str) or not summary.strip():
                raise ClientToolInputError(
                    "theory progress summary must be nonempty text"
                )
            if not isinstance(evidence_refs, list) or not evidence_refs or not all(
                isinstance(value, str) and value.strip()
                for value in evidence_refs
            ):
                raise ClientToolInputError(
                    "theory progress evidence_refs must be a nonempty array of text"
                )
            if not isinstance(next_step, str) or not next_step.strip():
                raise ClientToolInputError(
                    "theory progress next_step must be nonempty text"
                )
            phase_document_changes = current_changed_document_paths(
                state["documents"]
            )
            if not phase_document_changes:
                raise ClientToolInputError(
                    "checkpoint_theory_progress requires a new or revised "
                    "authoritative document in the current continuation phase"
                )
            progress = {
                "summary": summary.strip(),
                "evidence_refs": [
                    value.strip() for value in evidence_refs
                ],
                "next_step": next_step.strip(),
                "phase_changed_artifact_names": list(
                    current_changed_artifact_names(state["artifacts"])
                ),
                "phase_changed_document_paths": list(
                    phase_document_changes
                ),
            }
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "disposition": "THEORY_PROGRESS_CHECKPOINT",
                    "progress": progress,
                    "accepted": False,
                    "proof_evidence_status": (
                        "THEORY_PROGRESS_CHECKPOINT_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=True,
                terminal=True,
                terminal_payload={
                    "disposition": "THEORY_PROGRESS_CHECKPOINT",
                    "progress": progress,
                },
                observation_key=(
                    "theory-progress:" + stable_hash(progress)
                ),
            )

        if call.name == THEORY_WORKSPACE_GAP_TOOL:
            if set(tool_input) - {
                "summary",
                "blocking_claims",
                "evidence_refs",
                "next_step",
            }:
                raise ClientToolInputError(
                    "report_theory_gap accepts summary, blocking_claims, "
                    "evidence_refs, and next_step"
                )
            summary = tool_input.get("summary")
            evidence_refs = tool_input.get("evidence_refs")
            blocking_claims = tool_input.get("blocking_claims", [])
            next_step = tool_input.get("next_step", "")
            if not isinstance(summary, str) or not summary.strip():
                raise ClientToolInputError("theory-gap summary must be nonempty")
            for values, label in (
                (blocking_claims, "blocking_claims"),
                (evidence_refs, "evidence_refs"),
            ):
                if not isinstance(values, list) or not all(
                    isinstance(value, str) and value.strip() for value in values
                ):
                    raise ClientToolInputError(
                        f"{label} must be an array of nonempty strings"
                    )
            if not evidence_refs:
                raise ClientToolInputError(
                    "report_theory_gap requires at least one model-observed evidence ref"
                )
            if not isinstance(next_step, str):
                raise ClientToolInputError("theory-gap next_step must be a string")
            if not (
                state["reads"]
                or state["submissions"]
                or state["scratch_runs"]
                or state["source_search_refs"]
                or state["source_read_refs"]
                or state["source_result_read_refs"]
                or state["source_discovery_search_refs"]
                or state["source_discovery_read_refs"]
            ):
                raise ClientToolInputError(
                    "report_theory_gap requires a prior workspace read, write "
                    "observation, source observation, or scratch execution"
                )
            theory_gap = {
                "summary": summary.strip(),
                "blocking_claims": [
                    value.strip() for value in blocking_claims
                ],
                "evidence_refs": [value.strip() for value in evidence_refs],
                "next_step": next_step.strip(),
            }
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "disposition": "THEORY_GAP",
                    "theory_gap": deepcopy(theory_gap),
                    "proof_evidence_status": (
                        "MODEL_REPORTED_THEORY_GAP_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=True,
                terminal=True,
                terminal_payload={
                    "disposition": "THEORY_GAP",
                    "theory_gap": theory_gap,
                },
                observation_key="theory-gap:" + stable_hash(theory_gap),
            )

        raise ClientToolInputError("unsupported theory workspace tool")

    catalog = {
        name: {
            "shape": _artifact_shape(readable_artifact(name)),
            "content_hash": stable_hash(readable_artifact(name)),
            "byte_size": len(
                _compact_json(readable_artifact(name)).encode("utf-8")
            ),
            "writable": name in selected_writable_names,
        }
        for name in artifact_names
    }
    document_catalog = {
        row["relative_path"]: {
            "media_type": row["media_type"],
            "sha256": row["sha256"],
            "byte_size": row["byte_size"],
            "line_count": len(
                state["documents"][row["relative_path"]].splitlines()
            ),
        }
        for row in document_manifest(state["documents"]).get("documents", [])
    }
    write_guidance = (
        (
            "Use write_theory_document(path, content) to write one complete "
            "Markdown/LaTeX document or BibTeX file, and use "
            "write_theory_workspace only for the small structured cross-agent "
            "index or executable ABI. The text documents are the authority for "
            "definitions, derivations, equations, counterexamples, and unresolved "
            "reasoning; JSON artifacts are not the mathematical content. "
        )
        if require_document_authority
        else (
            "Use write_theory_workspace to write complete model-owned structured "
            "artifacts. Authoritative Markdown/LaTeX documents are unavailable in "
            "this compatibility workspace. "
        )
    ) + (
        "Omitted files and artifacts remain byte-identical. The runtime stores your "
        "exact text and values without merging or inventing content. A structurally "
        "valid write is retained and returned to you, but it does not end the "
        "workspace or assert scientific readiness. "
    )
    document_inspection_guidance = (
        "For long or multi-file mathematics, use search_theory_documents to locate "
        "a literal claim, heading, or LaTeX label and read_theory_document to inspect "
        "the exact current line range needed for your reasoning. Both observations "
        "name the current document SHA-256. Whole-document reads remain available "
        "when the selected material fits one observation. Your own writes and tool "
        "observations remain in this session, so choose whether another read would "
        "improve the argument; runtime read counts are not a substitute for your "
        "readiness judgment or the later independent review. "
        if require_document_authority
        else ""
    )
    edit_guidance = (
        "For a localized revision to an existing mathematical document, use "
        "edit_theory_document with the current document SHA-256 and an ordered batch "
        "of exact, unique model-selected text replacements. The runtime validates the "
        "whole batch against progressively revised bytes before applying it, then "
        "returns the resulting hash; it does not interpret or rewrite mathematics. "
        if require_document_authority
        else ""
    )
    progress_guidance = (
        "When you have made substantive document-backed progress but additional "
        "derivation or handoff work is genuinely needed beyond this session, call "
        "checkpoint_theory_progress with the evidence you inspected and one concrete "
        "next step. Each progress phase must create or revise an authoritative "
        "document. This requests same-owner continuation and is not accepted theory, "
        "empirical evidence, or proof. Address validator observations directly while "
        "a write remains. If no submission remains after substantive document work, "
        "checkpoint that progress so the same owner can continue; an unfinished "
        "structured handoff or exhausted write quota is not a mathematical gap. "
        if require_document_authority
        else ""
    )
    scratch_guidance = (
        "Use run_theory_scratchpad when a small Python or R calculation, exact "
        "model-chosen SymPy reduction, numerical check, or counterexample would resolve "
        "a mathematical uncertainty. Submit "
        "complete source defining run_sandbox(seed, replicates); the isolated runtime "
        "executes those exact bytes and returns the raw observation. After a published-"
        "source run, you may select declared UTF-8 result paths and define "
        "run_sandbox(seed, replicates, artifacts) to query their exact hash-bound "
        "contents with your own Python or R rather than asking the runtime to "
        "interpret them. Encode the disputed claim as computed quantities, predicates, "
        "residuals, or witnesses rather than a prewritten conclusion. "
        "Interpret the raw observation yourself. If it conflicts with an active "
        "document or earlier calculation, rederive and revise, retract, or mark the claim uncertain before checkpointing. Scratch output is exploratory, not "
        "confirmatory simulation or proof; a universal claim still needs an argument. "
        if scratchpad is not None
        else ""
    )
    source_guidance = (
        "A hash-bound model-visible research source snapshot is available. Use "
        "search_research_sources and read_research_source directly in this same "
        "session when a definition, assumption, theorem, algorithm, or claimed "
        "precedent depends on prior work. Decide what to search and how to use it "
        "yourself. For a method, model class, score, or implementation-specific "
        "claim, inspect the most specific primary definition or implementation "
        "available; do not substitute a nearby model family merely because its "
        "paper passage ranks highly. Cite the exact citation_ref returned by a "
        "source read in the authoritative Markdown/LaTeX whenever a claim relies "
        "on that passage. Retrieved text is source evidence, not proof or "
        "independent review. "
        if research_sources is not None
        else ""
    )
    source_discovery_guidance = (
        "Live public paper and repository discovery is available in this same "
        "TheoryDeveloper session. Use discover_research_sources with your own query, "
        "then read_discovered_research_source only for results worth inspecting. For "
        "GitHub repositories, an empty path returns the root listing at a commit no "
        "later than the configured source horizon; use the returned revision for exact "
        "subsequent file reads. Cite the returned citation_ref when your Markdown/LaTeX "
        "depends on an inspected source. Discovery metadata, source text, and repository "
        "code are research evidence only: they are not independent review, execution, "
        "replication, or proof. Strict historical benchmarks must use their frozen "
        "source snapshot instead of this live provider. "
        if research_source_discovery is not None
        else ""
    )
    source_execution_guidance = (
        "An operator-bound hash-verified author-source execution is available through "
        "run_research_source. The tool accepts no command, path, argument, or code from "
        "you: it revalidates the pinned snapshot and environment, denies network and "
        "secret inheritance, runs the exact published entrypoint, and returns raw "
        "stdout/stderr plus any operator-declared result artifacts from an isolated "
        "copy-on-write source workspace to this same session. Inspect and interpret "
        "that observation yourself. The visible execution descriptor and returned "
        "manifest state the exact working directory and argument vector. For larger "
        "UTF-8 outputs, either read exact lines or select the result paths in your "
        "existing scratch tool and analyze them with model-authored code. It is "
        "source-replication evidence, not model-authored "
        "scientific code, confirmatory simulation, or theorem proof. "
        if research_source_execution is not None
        else ""
    )
    source_checkpoint_guidance = (
        "This task has no required substantive lane beyond exact source replication "
        "and honest gap disclosure. After inspecting the sources and raw run, write a "
        "durable Markdown report with the reproduced outputs, identity evidence, "
        "comparison, interpretation, and caveats. Keep exact execution facts separate "
        "from mathematical interpretation; if an interpretation is not grounded in "
        "an exact source read, record that limitation as an unresolved gap. Then call "
        "commit_source_replication_checkpoint. You may instead continue into a full "
        "theory checkpoint if your own judgment finds that useful, but do not invent "
        "estimator, simulation, formalization, or novelty work merely to satisfy empty "
        "handoff fields. Pass unresolved_gaps as [] or as an array of nonempty plain "
        "strings; do not use objects or placeholder empty strings. "
        if allow_source_replication_checkpoint
        else ""
    )
    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=(
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\nAuthoritative theory workspace catalog:\n"
                    + _compact_json(
                        {
                            "structured_handoff_artifacts": catalog,
                            "mathematical_documents": document_catalog,
                            **(
                                {
                                    "research_source_snapshot": (
                                        research_sources.descriptor()
                                    )
                                }
                                if research_sources is not None
                                else {}
                            ),
                            **(
                                {
                                    "public_research_source_discovery": dict(
                                        research_source_discovery.descriptor()
                                    )
                                }
                                if research_source_discovery is not None
                                else {}
                            ),
                            **(
                                {
                                    "research_source_execution": (
                                        research_source_execution.descriptor(
                                            research_sources
                                        )
                                    )
                                }
                                if research_source_execution is not None
                                and research_sources is not None
                                else {}
                            ),
                            "content_authority": (
                                THEORY_WORKSPACE_CONTENT_AUTHORITY
                                if require_document_authority
                                else "legacy_structured_artifacts"
                            ),
                        }
                    )
                    + "\n\nRead the artifacts needed for mathematical judgment. "
                    + source_discovery_guidance
                    + source_guidance
                    + source_execution_guidance
                    + source_checkpoint_guidance
                    + scratch_guidance
                    + write_guidance
                    + document_inspection_guidance
                    + edit_guidance
                    + progress_guidance
                    + "When the current workspace is scientifically ready for "
                    "independent review, call commit_theory_checkpoint and explain "
                    "your own readiness judgment. There is no required number of "
                    "reads, rewrites, scratch runs, or counterexample attempts: choose "
                    "only actions that improve the mathematics. Independent read, "
                    "search, or inspection calls whose outputs do not depend on one "
                    "another may be batched in one model turn. Keep any write, "
                    "execution, or terminal action after the observations it depends "
                    "on, and make a terminal action the final call of its turn. "
                    "Structural validation "
                    "checks the handoff contract, not whether the theory is correct. "
                    "Before committing, edit the authoritative documents into a clean "
                    "current argument: no step you have already shown false may remain "
                    "as an active derivation or SUPPORTED claim. Preserve a failed "
                    "attempt only when it is clearly separated as rejected or scratch "
                    "work and no active claim depends on it. "
                    + "If a mathematical contradiction, missing premise, or unresolved "
                    "question prevents a coherent submission, use report_theory_gap "
                    "after inspecting the relevant artifacts. State the blocker and "
                    "model-observed evidence directly; this ends the workspace as "
                    "blocked and never counts as theory or proof success. "
                    "Do not report a mathematical gap merely because a structured "
                    "index is unfinished or the current phase has no write left after "
                    "substantive document progress; use checkpoint_theory_progress "
                    "for same-owner continuation instead. "
                    + "Each structurally valid model write is retained even when the "
                    "combined workspace still fails validation, so a validator "
                    "observation is not a rollback and later calls should contain only "
                    "artifacts that still need to be added or revised. "
                    "The runtime returns validator observations to this same model "
                    "context. A structurally valid write returns "
                    "checkpoint_commit_ready, but that flag checks only the handoff "
                    "contract. Decide yourself whether further derivation, source "
                    "inspection, scratch work, or self-review is scientifically useful "
                    "before committing for independent review."
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
            "model_tier": model_tier,
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
            "parent_workspace_hash": parent_hash,
        },
    )
    resumed_client_tool_session_ref: dict[str, Any] = {}
    resumed_client_tool_context_window: dict[str, Any] = {}
    if prior_client_tool_session_ref:
        if resolved_workspace_dir is None:
            raise ValueError(
                "theory client-tool session resume requires a persistent workspace"
            )
        request, resumed_client_tool_context_window = (
            resume_client_tool_session_from_checkpoint(
                prior_client_tool_session_ref,
                session_dir=resolved_workspace_dir,
                session_id=workspace_id,
                checkpoint_identity=parent_hash,
                request=request,
                replay_recent_tool_rounds=CLIENT_TOOL_RECENT_HISTORY_ROUNDS,
            )
        )
        resumed_client_tool_session_ref = deepcopy(
            dict(prior_client_tool_session_ref)
        )

    def recovery_checkpoint() -> dict[str, Any]:
        current_artifacts = deepcopy(dict(state["artifacts"]))
        current_documents = deepcopy(dict(state["documents"]))
        return {
            "schema_version": 1,
            "artifact_kind": THEORY_WORKSPACE_CHECKPOINT_KIND,
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
            "parent_workspace_hash": parent_hash,
            "current_workspace_hash": stable_hash(
                {
                    "artifacts": current_artifacts,
                    "documents": current_documents,
                }
            ),
            "current_artifacts": current_artifacts,
            "theory_workspace_manifest": document_manifest(current_documents),
            "changed_artifact_names": list(
                changed_artifact_names(current_artifacts)
            ),
            "changed_document_paths": list(
                changed_document_paths(current_documents)
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "model_artifact_writes": deepcopy(
                state["model_artifact_writes"]
            ),
            "model_document_writes": deepcopy(
                state["model_document_writes"]
            ),
            "document_inspection_refs": deepcopy(
                state["document_inspection_refs"]
            ),
            "scratch_runs": state["scratch_runs"],
            "scratch_execution_refs": deepcopy(
                state["scratch_execution_refs"]
            ),
            "research_source_snapshot": (
                research_sources.descriptor()
                if research_sources is not None
                else {"configured": False}
            ),
            "source_search_refs": deepcopy(state["source_search_refs"]),
            "source_read_refs": deepcopy(state["source_read_refs"]),
            "source_result_read_refs": deepcopy(
                state["source_result_read_refs"]
            ),
            **source_discovery_evidence(),
            "source_replication_runs": state["source_replication_runs"],
            "source_replication_manifests": deepcopy(
                state["source_replication_manifests"]
            ),
            "client_tool_checkpoint_window": deepcopy(
                resumed_client_tool_context_window
            ),
            "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
            "last_validation_errors": list(state["last_validation_errors"]),
            "model_owned_theory": True,
            "runtime_edited_theory": False,
            "proof_evidence_status": (
                "THEORY_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
            "kernel_verified": False,
        }

    # The shared loop reserves terminal disposition outside this action budget.
    effective_max_turns = (
        max(max_turns, max_tool_calls)
        if allow_source_replication_checkpoint
        else max_turns
    )
    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=effective_max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
            max_terminal_recovery_turns=1,
        )
    except ClientToolLoopError as exc:
        client_tool_session_ref = persist_client_tool_session(
            session_dir=resolved_workspace_dir,
            session_id=workspace_id,
            request=request,
            messages=exc.messages,
        )
        checkpoint = recovery_checkpoint()
        if client_tool_session_ref:
            checkpoint["client_tool_session_ref"] = client_tool_session_ref
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=exc.turns,
            errors=list(
                dict.fromkeys(
                    [exc.reason, *state["last_validation_errors"]]
                )
            ),
            history=_theory_workspace_evidence_history(exc.history),
            last_invalid_packet=(
                deepcopy(dict(state["last_candidate"]))
                if state["last_candidate"]
                else None
            ),
            recovery_checkpoint=checkpoint,
        ) from exc

    client_tool_session_ref = persist_client_tool_session(
        session_dir=resolved_workspace_dir,
        session_id=workspace_id,
        request=request,
        messages=loop.messages,
    )
    client_tool_session_evidence = {
        "client_tool_session_ref": deepcopy(client_tool_session_ref),
        "resumed_from_client_tool_session_ref": deepcopy(
            resumed_client_tool_session_ref
        ),
        "client_tool_session_lineage_continued": bool(
            resumed_client_tool_session_ref
        ),
        "client_tool_checkpoint_window": deepcopy(
            resumed_client_tool_context_window
        ),
        "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
    }
    terminal = dict(loop.terminal_payload)
    if terminal.get("disposition") == "SOURCE_REPLICATION_CHECKPOINT_COMMITTED":
        core_packet = terminal.get("core_packet", {})
        packet = deepcopy(dict(core_packet)) if isinstance(core_packet, Mapping) else {}
        packet_hash = stable_hash(packet) if packet else ""
        report = packet.get("report_document", {})
        source_ref = packet.get("source_replication_manifest_ref", {})
        source_manifests = state["source_replication_manifests"]
        terminal_errors: list[str] = []
        if not (
            packet.get("artifact_kind") == SOURCE_REPLICATION_CHECKPOINT_KIND
            and packet.get("question_id") == question_id
            and packet.get("workspace_id") == workspace_id
            and terminal.get("core_packet_hash") == packet_hash
            and isinstance(report, Mapping)
            and str(report.get("relative_path", "") or "")
            and isinstance(source_ref, Mapping)
            and len(source_manifests) == 1
            and source_ref.get("artifact_id")
            == source_manifests[0].get("artifact_id")
            and source_ref.get("manifest_hash")
            == source_manifests[0].get("manifest_hash")
        ):
            terminal_errors.append(
                "terminal source replication checkpoint identity is invalid"
            )
        if terminal_errors:
            raise PacketValidationError(
                validation_label="source replication workspace checkpoint",
                attempts=loop.turns,
                errors=terminal_errors,
                history=_theory_workspace_evidence_history(loop.history),
                last_invalid_packet=packet or None,
                recovery_checkpoint=recovery_checkpoint(),
            )
        evidence = {
            "schema_version": 1,
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "artifact_id": "source_replication_workspace:"
            + stable_hash(
                [
                    workspace_id,
                    packet_hash,
                    loop.transcript_fingerprint,
                ]
            )[:20],
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "transport": "native_client_tools",
            "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
            "parent_workspace_hash": parent_hash,
            "submitted_workspace_hash": str(
                terminal.get("workspace_hash", "") or ""
            ),
            "submitted_core_packet_hash": packet_hash,
            "changed_artifact_names": list(
                terminal.get("changed_artifact_names", []) or []
            ),
            "changed_document_paths": list(
                terminal.get("changed_document_paths", []) or []
            ),
            "theory_workspace_manifest": deepcopy(
                dict(terminal.get("theory_workspace_manifest", {}) or {})
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "source_replication_runs": state["source_replication_runs"],
            "source_replication_manifests": deepcopy(source_manifests),
            "document_inspection_refs": deepcopy(
                state["document_inspection_refs"]
            ),
            "research_source_snapshot": (
                research_sources.descriptor()
                if research_sources is not None
                else {"configured": False}
            ),
            "source_search_refs": deepcopy(state["source_search_refs"]),
            "source_read_refs": deepcopy(state["source_read_refs"]),
            "source_result_read_refs": deepcopy(
                state["source_result_read_refs"]
            ),
            **source_discovery_evidence(),
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "provider": loop.provider,
            "model": loop.model,
            "model_tier": model_tier,
            "provider_usage": dict(loop.provider_usage),
            "history": _theory_workspace_evidence_history(loop.history),
            "transcript_fingerprint": loop.transcript_fingerprint,
            **client_tool_session_evidence,
            "disposition": "SOURCE_REPLICATION_CHECKPOINT_COMMITTED",
            "checkpoint_committed": True,
            "model_owned_theory": False,
            "model_owned_source_report": True,
            "runtime_edited_theory": False,
            "runtime_edited_source": False,
            "accepted": True,
            "proof_evidence_status": (
                "SOURCE_REPLICATION_WORKSPACE_NOT_PROOF_EVIDENCE"
            ),
            "kernel_verified": False,
        }
        return TheoryWorkspaceResult(core_packet=packet, evidence=evidence)
    if terminal.get("disposition") == "THEORY_PROGRESS_CHECKPOINT":
        raw_progress = terminal.get("progress", {})
        if not isinstance(raw_progress, Mapping) or not str(
            raw_progress.get("summary", "") or ""
        ).strip():
            raise PacketValidationError(
                validation_label="LLM TheoryDeveloper progress checkpoint",
                attempts=loop.turns,
                errors=["terminal theory progress payload is invalid"],
                history=_theory_workspace_evidence_history(loop.history),
                recovery_checkpoint=recovery_checkpoint(),
            )
        progress = deepcopy(dict(raw_progress))
        checkpoint_body = {
            **recovery_checkpoint(),
            "artifact_kind": THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND,
            "progress": progress,
            "client_tool_session_ref": deepcopy(
                client_tool_session_ref
            ),
            "resumable": True,
            "accepted": False,
            "proof_evidence_status": (
                "THEORY_PROGRESS_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
            "boundary": (
                "This is exact model-authored partial theory state requesting "
                "same-owner continuation. It is not independent review acceptance, "
                "empirical evidence, formal proof, or kernel evidence."
            ),
        }
        checkpoint_id = "theory_progress_checkpoint:" + stable_hash(
            checkpoint_body
        )[:20]
        checkpoint = {
            **checkpoint_body,
            "checkpoint_id": checkpoint_id,
        }
        evidence = {
            "schema_version": 1,
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "artifact_id": "theory_workspace_progress:"
            + stable_hash(
                [
                    workspace_id,
                    checkpoint_id,
                    loop.transcript_fingerprint,
                ]
            )[:20],
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "transport": "native_client_tools",
            "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
            "parent_workspace_hash": parent_hash,
            "current_workspace_hash": checkpoint["current_workspace_hash"],
            "changed_artifact_names": list(
                checkpoint.get("changed_artifact_names", []) or []
            ),
            "changed_document_paths": list(
                checkpoint.get("changed_document_paths", []) or []
            ),
            "theory_workspace_manifest": deepcopy(
                dict(checkpoint["theory_workspace_manifest"])
            ),
            "progress": progress,
            "reads": state["reads"],
            "submissions": state["submissions"],
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "provider": loop.provider,
            "model": loop.model,
            "model_tier": model_tier,
            "provider_usage": dict(loop.provider_usage),
            "history": _theory_workspace_evidence_history(loop.history),
            "transcript_fingerprint": loop.transcript_fingerprint,
            **client_tool_session_evidence,
            "disposition": "THEORY_PROGRESS_CHECKPOINT",
            "checkpoint_id": checkpoint_id,
            "checkpoint_committed": True,
            "resumable": True,
            "model_owned_theory": True,
            "runtime_edited_theory": False,
            "accepted": False,
            "proof_evidence_status": (
                "THEORY_PROGRESS_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
            "kernel_verified": False,
        }
        raise TheoryWorkspaceProgressError(
            progress_checkpoint=checkpoint,
            evidence=evidence,
        )
    if terminal.get("disposition") == "THEORY_GAP":
        theory_gap = terminal.get("theory_gap", {})
        if not isinstance(theory_gap, Mapping) or not str(
            theory_gap.get("summary", "") or ""
        ).strip():
            raise PacketValidationError(
                validation_label="LLM TheoryDeveloper artifact workspace",
                attempts=loop.turns,
                errors=["terminal theory-gap payload is invalid"],
                history=_theory_workspace_evidence_history(loop.history),
                recovery_checkpoint=recovery_checkpoint(),
            )
        gap = deepcopy(dict(theory_gap))
        evidence = {
            "schema_version": 1,
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "artifact_id": "theory_workspace_gap:"
            + stable_hash(
                [workspace_id, workspace_operation, gap, loop.transcript_fingerprint]
            )[:20],
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "transport": "native_client_tools",
            "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
            "parent_workspace_hash": parent_hash,
            "current_workspace_hash": stable_hash(
                {
                    "artifacts": state["artifacts"],
                    "documents": state["documents"],
                }
            ),
            "changed_artifact_names": list(
                changed_artifact_names(state["artifacts"])
            ),
            "changed_document_paths": list(
                changed_document_paths(state["documents"])
            ),
            "theory_workspace_manifest": document_manifest(
                state["documents"]
            ),
            "document_inspection_refs": deepcopy(
                state["document_inspection_refs"]
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "scratch_runs": state["scratch_runs"],
            "research_source_snapshot": (
                research_sources.descriptor()
                if research_sources is not None
                else {"configured": False}
            ),
            "source_search_refs": deepcopy(state["source_search_refs"]),
            "source_read_refs": deepcopy(state["source_read_refs"]),
            "source_result_read_refs": deepcopy(
                state["source_result_read_refs"]
            ),
            **source_discovery_evidence(),
            "source_replication_runs": state["source_replication_runs"],
            "source_replication_manifests": deepcopy(
                state["source_replication_manifests"]
            ),
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "provider": loop.provider,
            "model": loop.model,
            "model_tier": model_tier,
            "provider_usage": dict(loop.provider_usage),
            "history": _theory_workspace_evidence_history(loop.history),
            "transcript_fingerprint": loop.transcript_fingerprint,
            **client_tool_session_evidence,
            "disposition": "THEORY_GAP",
            "theory_gap": gap,
            "model_owned_theory": True,
            "runtime_edited_theory": False,
            "accepted": False,
            "proof_evidence_status": (
                "MODEL_REPORTED_THEORY_GAP_NOT_PROOF_EVIDENCE"
            ),
            "kernel_verified": False,
        }
        raise TheoryWorkspaceGapError(theory_gap=gap, evidence=evidence)
    core_packet = terminal.get("core_packet", {})
    if not isinstance(core_packet, Mapping):
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=loop.turns,
            errors=["terminal theory workspace packet is not an object"],
            history=_theory_workspace_evidence_history(loop.history),
        )
    packet = deepcopy(dict(core_packet))
    packet_hash = stable_hash(packet)
    terminal_errors = [
        str(error)
        for error in validate_candidate(packet)
        if str(error).strip()
    ]
    terminal_errors = list(
        dict.fromkeys(
            [
                *[
                    str(error)
                    for error in terminal.get("validation_errors", []) or []
                    if str(error).strip()
                ],
                *terminal_errors,
            ]
        )
    )
    if terminal.get("core_packet_hash") != packet_hash or terminal_errors:
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=loop.turns,
            errors=(
                terminal_errors
                or ["terminal theory workspace packet hash does not match"]
            ),
            history=_theory_workspace_evidence_history(loop.history),
            last_invalid_packet=packet,
            recovery_checkpoint=recovery_checkpoint(),
        )

    evidence_id = "theory_workspace:" + stable_hash(
        [
            workspace_id,
            workspace_operation,
            parent_hash,
            packet_hash,
            loop.transcript_fingerprint,
        ]
    )[:20]
    evidence = {
        "schema_version": 2,
        "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
        "artifact_id": evidence_id,
        "workspace_id": workspace_id,
        "question_id": question_id,
        "authoring_binding_id": authoring_binding_id,
        "workspace_operation": workspace_operation,
        "transport": "native_client_tools",
        "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
        "parent_workspace_hash": parent_hash,
        "submitted_workspace_hash": str(terminal.get("workspace_hash", "") or ""),
        "submitted_core_packet_hash": packet_hash,
        "read_only_artifact_hashes": {
            name: stable_hash(value) for name, value in sorted(read_only.items())
        },
        "changed_artifact_names": list(
            terminal.get("changed_artifact_names", []) or []
        ),
        "changed_document_paths": list(
            terminal.get("changed_document_paths", []) or []
        ),
        "theory_workspace_manifest": deepcopy(
            dict(terminal.get("theory_workspace_manifest", {}) or {})
        ),
        "reads": state["reads"],
        "submissions": state["submissions"],
        "n_model_artifact_writes": len(state["model_artifact_writes"]),
        "model_artifact_writes": deepcopy(
            state["model_artifact_writes"]
        ),
        "n_model_document_writes": len(state["model_document_writes"]),
        "model_document_writes": deepcopy(
            state["model_document_writes"]
        ),
        "document_inspection_refs": deepcopy(
            state["document_inspection_refs"]
        ),
        "theory_content_authority": (
            THEORY_WORKSPACE_CONTENT_AUTHORITY
            if require_document_authority
            else "legacy_structured_artifacts"
        ),
        "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
        "scratchpad_enabled": scratchpad is not None,
        "scratch_runs": state["scratch_runs"],
        "scratch_execution_refs": deepcopy(state["scratch_execution_refs"]),
        "research_source_snapshot": (
            research_sources.descriptor()
            if research_sources is not None
            else {"configured": False}
        ),
        "source_search_refs": deepcopy(state["source_search_refs"]),
        "source_read_refs": deepcopy(state["source_read_refs"]),
        "source_result_read_refs": deepcopy(
            state["source_result_read_refs"]
        ),
        **source_discovery_evidence(),
        "source_replication_runs": state["source_replication_runs"],
        "source_replication_manifests": deepcopy(
            state["source_replication_manifests"]
        ),
        "turns": loop.turns,
        "tool_calls": loop.tool_calls,
        "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
        "provider": loop.provider,
        "model": loop.model,
        "model_tier": model_tier,
        "provider_usage": dict(loop.provider_usage),
        "history": _theory_workspace_evidence_history(loop.history),
        "transcript_fingerprint": loop.transcript_fingerprint,
        **client_tool_session_evidence,
        "disposition": "THEORY_CHECKPOINT_COMMITTED",
        "checkpoint_committed": True,
        "checkpoint_readiness_rationale": str(
            terminal.get("readiness_rationale", "") or ""
        ),
        "model_owned_theory": True,
        "runtime_edited_theory": False,
        "accepted": True,
        "proof_evidence_status": "THEORY_WORKSPACE_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
    }
    return TheoryWorkspaceResult(core_packet=packet, evidence=evidence)


def _theory_workspace_evidence_history(
    history: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    persisted = [deepcopy(dict(row)) for row in history]
    workspace_content_tools = {
        "read_theory_workspace",
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    }
    source_tools = {
        RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
        RESEARCH_SOURCE_RUN_TOOL,
        RESEARCH_SOURCE_RESULT_READ_TOOL,
        RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
        RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    }
    for turn in persisted:
        tool_calls = turn.get("tool_calls", [])
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            tool_name = str(tool_call.get("name", "") or "")
            if tool_name in source_tools:
                tool_call["result_excerpt"] = (
                    "[research source text omitted from persisted evidence; raw "
                    "execution also omitted from transcript; use snapshot/document/"
                    "range or source-replication refs]"
                )
            elif tool_name in workspace_content_tools:
                tool_call["result_excerpt"] = (
                    "[theory workspace content omitted from persisted evidence; use "
                    "hash-bound artifact or document inspection refs]"
                )
    return persisted


def theory_document_client_tools() -> tuple[ClientToolDefinition, ...]:
    return (
        ClientToolDefinition(
            name=THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
            description=(
                "Search exact current hash-bound Markdown/LaTeX/BibTeX theory "
                "documents for a case-insensitive literal string. Returns "
                "line-addressed hits and document hashes; it does not interpret "
                "mathematics."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "document_paths": {
                        "type": "array",
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_THEORY_DOCUMENT_SEARCH_HITS,
                    },
                },
            },
        ),
        ClientToolDefinition(
            name=THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
            description=(
                "Read an exact inclusive line range from one current hash-bound "
                "Markdown/LaTeX/BibTeX theory document. Returns the full document "
                "hash and exact range hash for model-owned reasoning."
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
    )


def research_source_client_tools() -> tuple[ClientToolDefinition, ...]:
    return (
        ClientToolDefinition(
            name=RESEARCH_SOURCE_SEARCH_TOOL,
            description=(
                "Search exact UTF-8 paper, code, and documentation text in "
                "the configured hash-bound model-visible source snapshot. "
                "Returns line-addressed excerpts to this same model session."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_SOURCE_SEARCH_HITS,
                    },
                },
            },
        ),
        ClientToolDefinition(
            name=RESEARCH_SOURCE_READ_TOOL,
            description=(
                "Read an exact inclusive line range from one document in "
                "the configured hash-bound research source snapshot."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["document_id", "line_start", "line_end"],
                "properties": {
                    "document_id": {"type": "string", "minLength": 1},
                    "line_start": {"type": "integer", "minimum": 1},
                    "line_end": {"type": "integer", "minimum": 1},
                },
            },
        ),
    )


def research_source_discovery_client_tools() -> tuple[ClientToolDefinition, ...]:
    return (
        ClientToolDefinition(
            name=RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
            description=(
                "Search public scholarly metadata and GitHub repositories under the "
                "operator-configured source horizon. You choose the query and source "
                "kind; use the returned opaque handle to inspect a promising result."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 500},
                    "source_kind": {
                        "type": "string",
                        "enum": ["all", "paper", "repository"],
                    },
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 10},
                },
            },
        ),
        ClientToolDefinition(
            name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
            description=(
                "Read exact bounded metadata or repository text from a handle returned "
                "by discover_research_sources. For a repository, first omit path and "
                "revision to resolve a horizon-bound commit and list root entries, then "
                "read a selected text path at that returned revision."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["source_handle"],
                "properties": {
                    "source_handle": {"type": "string", "minLength": 1},
                    "path": {"type": "string"},
                    "revision": {"type": "string"},
                },
            },
        ),
    )


def _theory_workspace_tools(
    *,
    scratchpad_enabled: bool = False,
    research_sources_enabled: bool = False,
    research_source_discovery_enabled: bool = False,
    research_source_execution_enabled: bool = False,
    source_replication_checkpoint_enabled: bool = False,
    document_authority_enabled: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    read_tool = ClientToolDefinition(
        name="read_theory_workspace",
        description=(
            "Read the exact current contents of one or more named theory "
            "workspace artifacts before deciding what to revise."
        ),
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "artifact_names": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                },
                **(
                    {
                        "document_paths": {
                            "type": "array",
                            "uniqueItems": True,
                            "items": {"type": "string", "minLength": 1},
                        }
                    }
                    if document_authority_enabled
                    else {}
                ),
            },
        },
    )
    tools = [read_tool]
    if document_authority_enabled:
        tools.extend(theory_document_client_tools())
    if research_sources_enabled:
        tools.extend(research_source_client_tools())
    if research_source_discovery_enabled:
        tools.extend(research_source_discovery_client_tools())
    if research_source_execution_enabled:
        tools.extend(
            (
                ClientToolDefinition(
                    name=RESEARCH_SOURCE_RUN_TOOL,
                    description=(
                        "Run the exact operator-pinned published entrypoint once in its "
                        "hash-bound, network-denied environment. This tool accepts no "
                        "model-selected command or source. Raw stdout/stderr, plus any "
                        "operator-declared CSV, text, or binary result artifacts from "
                        "an isolated copy-on-write workspace, return to this same "
                        "session as hash-bound compact observations. Use "
                        "read_research_source_result for exact result lines instead of "
                        "requesting embedded files."
                    ),
                    input_schema={
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {},
                    },
                ),
                ClientToolDefinition(
                    name=RESEARCH_SOURCE_RESULT_READ_TOOL,
                    description=(
                        "Read an exact inclusive line range from one declared UTF-8 "
                        "result artifact produced by run_research_source. The runtime "
                        "rechecks the artifact SHA-256 before returning bytes."
                    ),
                    input_schema={
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "relative_path",
                            "line_start",
                            "line_end",
                        ],
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "line_start": {
                                "type": "integer",
                                "minimum": 1,
                            },
                            "line_end": {
                                "type": "integer",
                                "minimum": 1,
                            },
                        },
                    },
                ),
            )
        )
    if scratchpad_enabled:
        tools.append(theory_scratchpad_client_tool())
    if document_authority_enabled:
        tools.append(
            ClientToolDefinition(
                name=THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                description=(
                    "Write one complete model-authored Markdown, LaTeX, or BibTeX "
                    "document. The exact text becomes the authoritative mathematical "
                    "workspace; runtime validates the path and bytes but never edits "
                    "or interprets the mathematics."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "content"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "content": {"type": "string", "minLength": 1},
                    },
                },
                strict=True,
                terminal=False,
            )
        )
    tools.append(
        ClientToolDefinition(
            name=THEORY_WORKSPACE_WRITE_TOOL,
            description=(
                (
                    "Write one or more complete structured cross-agent handoff "
                    "values. These JSON values are only a claim index or executable "
                    "ABI; put all substantive mathematics in "
                    "write_theory_document. "
                )
                if document_authority_enabled
                else "Write one or more complete model-owned structured artifacts. "
            )
            + (
                "Omitted values are retained exactly, and runtime never merges or "
                "infers content."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["writes"],
                "properties": {
                    "writes": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["artifact_name", "value"],
                            "properties": {
                                "artifact_name": {
                                    "type": "string",
                                    "minLength": 1,
                                },
                                "value": {
                                    "anyOf": [
                                        {"type": "object"},
                                        {"type": "array"},
                                    ]
                                },
                            },
                        },
                    },
                },
            },
            terminal=False,
        )
    )
    if document_authority_enabled:
        tools.append(
            ClientToolDefinition(
                name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                description=(
                    "Atomically apply an ordered batch of exact model-authored "
                    "replacements to an existing Markdown/LaTeX/BibTeX document. "
                    "The batch is bound to the current document SHA-256; each old_text "
                    "must occur exactly once in the progressively revised bytes. The "
                    "runtime validates every replacement before mutating the document "
                    "and never authors or interprets mathematics."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "expected_sha256", "edits"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "expected_sha256": {"type": "string", "minLength": 64, "maxLength": 64},
                        "edits": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["old_text", "new_text"],
                                "properties": {
                                    "old_text": {"type": "string", "minLength": 1},
                                    "new_text": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                terminal=False,
            )
        )
    if source_replication_checkpoint_enabled:
        tools.append(
            ClientToolDefinition(
                name=SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL,
                description=(
                    "Commit a model-authored Markdown source-replication report after "
                    "the immutable source run. This ends a source-replication-only task "
                    "without fabricating theory, code, simulation, or proof artifacts."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "report_document_path",
                        "readiness_rationale",
                        "unresolved_gaps",
                    ],
                    "properties": {
                        "report_document_path": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "readiness_rationale": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "unresolved_gaps": {
                            "type": "array",
                            "description": (
                                "Use [] when no gap remains; otherwise use only "
                                "nonempty plain strings, never objects or empty "
                                "placeholders."
                            ),
                            "items": {"type": "string", "minLength": 1},
                        },
                    },
                },
                terminal=True,
            )
        )
    if document_authority_enabled:
        tools.append(
            ClientToolDefinition(
                name=THEORY_WORKSPACE_PROGRESS_TOOL,
                description=(
                    "Checkpoint substantive model-authored mathematical progress and "
                    "request another TheoryDeveloper continuation. Use this only "
                    "after creating or revising an authoritative document when more "
                    "derivation is genuinely needed. The checkpoint is not accepted "
                    "theory, empirical evidence, or proof."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["summary", "evidence_refs", "next_step"],
                    "properties": {
                        "summary": {"type": "string", "minLength": 1},
                        "evidence_refs": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "string", "minLength": 1},
                        },
                        "next_step": {"type": "string", "minLength": 1},
                    },
                },
                strict=True,
                terminal=True,
            )
        )
    tools.append(
        ClientToolDefinition(
            name=THEORY_WORKSPACE_COMMIT_TOOL,
            description=(
                "Commit the current structurally valid, model-authored workspace as "
                "ready for independent scientific review. This records the model's "
                "stopping decision; structural validity and any author-side reads do "
                "not make the theory correct and are not proof evidence."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["readiness_rationale"],
                "properties": {
                    "readiness_rationale": {
                        "type": "string",
                        "minLength": 1,
                    }
                },
            },
            terminal=True,
        )
    )
    tools.append(
        ClientToolDefinition(
            name=THEORY_WORKSPACE_GAP_TOOL,
            description=(
                "Stop with an explicit unresolved mathematical gap after inspecting "
                "the current workspace. Use this when you cannot make the authoritative "
                "artifacts coherent within the available evidence and budget. Report "
                "your own blocker and evidence; this is a non-success, non-proof result."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["summary", "evidence_refs"],
                "properties": {
                    "summary": {"type": "string"},
                    "blocking_claims": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "evidence_refs": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                    "next_step": {"type": "string"},
                },
            },
            terminal=True,
        )
    )
    return tuple(tools)


def _replace_theory_workspace_artifacts(
    current_artifacts: Mapping[str, Any],
    raw_writes: Any,
    *,
    writable_artifact_shapes: Mapping[str, str],
    allow_empty: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Replace complete model-authored artifacts atomically."""

    if (
        not isinstance(raw_writes, Sequence)
        or isinstance(raw_writes, (str, bytes))
        or (not raw_writes and not allow_empty)
    ):
        raise ClientToolInputError(
            "write_theory_workspace requires writes to be an array"
        )
    candidate = deepcopy(dict(current_artifacts))
    records: list[dict[str, Any]] = []
    observed_names: set[str] = set()
    for index, raw_write in enumerate(raw_writes):
        if not isinstance(raw_write, Mapping):
            raise ClientToolInputError(
                f"theory artifact write {index} must be an object"
            )
        write = dict(raw_write)
        if set(write) != {"artifact_name", "value"}:
            raise ClientToolInputError(
                f"theory artifact write {index} requires exactly "
                "artifact_name and value"
            )
        artifact_name = write["artifact_name"]
        if not isinstance(artifact_name, str):
            raise ClientToolInputError(
                f"theory artifact write {index} artifact_name must be a string"
            )
        if artifact_name not in writable_artifact_shapes:
            raise ClientToolInputError(
                f"theory artifact write {index} names unknown writable artifact "
                f"{artifact_name!r}"
            )
        if artifact_name in observed_names:
            raise ClientToolInputError(
                f"theory artifact write {index} repeats {artifact_name!r}"
            )
        observed_names.add(artifact_name)
        value = write["value"]
        expected_shape = writable_artifact_shapes[artifact_name]
        actual_shape = _artifact_shape(value)
        if actual_shape != expected_shape:
            raise ClientToolInputError(
                f"write_theory_workspace requires {artifact_name} to remain "
                f"{expected_shape}, received {actual_shape}"
            )
        candidate[artifact_name] = deepcopy(value)
        records.append(
            {
                "artifact_name": artifact_name,
                "value_hash": stable_hash(value),
            }
        )
    return candidate, records


def _replace_theory_workspace_document(
    current_documents: Mapping[str, str],
    raw_write: Any,
) -> tuple[dict[str, str], dict[str, Any]]:
    if not isinstance(raw_write, Mapping):
        raise ClientToolInputError(
            "write_theory_document requires an object"
        )
    candidate = dict(current_documents)
    write = dict(raw_write)
    if set(write) != {"path", "content"}:
        raise ClientToolInputError(
            "write_theory_document requires exactly path and content"
        )
    path = _normalized_theory_document_path(write["path"])
    content = write["content"]
    if not isinstance(content, str) or not content.strip():
        raise ClientToolInputError(
            "write_theory_document content must be nonempty text"
        )
    candidate[path] = content
    return candidate, {
        "relative_path": path,
        "sha256": _text_sha256(content),
        "byte_size": len(content.encode("utf-8")),
    }


def _edit_theory_workspace_document(
    current_documents: Mapping[str, str],
    raw_edit: Any,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Atomically apply model-selected replacements without interpreting text."""

    if not isinstance(raw_edit, Mapping):
        raise ClientToolInputError("theory document edit must be an object")
    edit = dict(raw_edit)
    required = {"path", "expected_sha256", "edits"}
    if set(edit) != required:
        raise ClientToolInputError(
            "edit_theory_document requires exactly path, expected_sha256, and edits"
        )
    path = _normalized_theory_document_path(edit["path"])
    if path not in current_documents:
        raise ClientToolInputError(f"cannot edit unknown theory document {path!r}")
    current = current_documents[path]
    expected_sha256 = edit["expected_sha256"]
    if not isinstance(expected_sha256, str):
        raise ClientToolInputError("edit_theory_document expected_sha256 must be text")
    current_sha256 = _text_sha256(current)
    if expected_sha256 != current_sha256:
        raise ClientToolInputError(
            f"theory document {path!r} changed since it was read; expected "
            f"{expected_sha256!r}, current {current_sha256!r}"
        )
    raw_edits = edit["edits"]
    if not isinstance(raw_edits, list) or not raw_edits:
        raise ClientToolInputError("edit_theory_document edits must be a nonempty array")
    revised = current
    edit_records: list[dict[str, str]] = []
    for edit_index, raw_replacement in enumerate(raw_edits):
        if not isinstance(raw_replacement, Mapping) or set(raw_replacement) != {
            "old_text", "new_text"
        }:
            raise ClientToolInputError(
                "edit_theory_document edits must contain exactly old_text and "
                f"new_text; invalid edit index {edit_index}"
            )
        old_text = raw_replacement.get("old_text")
        new_text = raw_replacement.get("new_text")
        if not (isinstance(old_text, str) and old_text
                and isinstance(new_text, str) and old_text != new_text):
            raise ClientToolInputError(
                "edit_theory_document edits require distinct nonempty old_text "
                f"and textual new_text; invalid edit index {edit_index}"
            )
        occurrence_count = revised.count(old_text)
        if occurrence_count != 1:
            raise ClientToolInputError(
                f"edit_theory_document old_text must occur exactly once in {path!r}; "
                f"edit index {edit_index} found {occurrence_count}"
            )
        revised = revised.replace(old_text, new_text, 1)
        edit_records.append({"old_text_sha256": _text_sha256(old_text),
                             "new_text_sha256": _text_sha256(new_text)})
    if not revised.strip():
        raise ClientToolInputError("edit_theory_document cannot leave a document empty")
    candidate = dict(current_documents)
    candidate[path] = revised
    return candidate, {
        "operation": "atomic_exact_text_replacement_batch",
        "relative_path": path,
        "parent_sha256": current_sha256,
        "edit_count": len(edit_records),
        "edits": edit_records,
        "sha256": _text_sha256(revised),
        "byte_size": len(revised.encode("utf-8")),
    }


def _normalized_theory_document_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ClientToolInputError("theory document path must be nonempty text")
    path = PurePosixPath(value.strip())
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ClientToolInputError(
            "theory document path must be workspace-relative without traversal"
        )
    if path.suffix.lower() not in THEORY_WORKSPACE_DOCUMENT_SUFFIXES:
        raise ClientToolInputError(
            "theory documents must use .md, .tex, or .bib"
        )
    return path.as_posix()


def _normalized_theory_documents(
    documents: Mapping[str, str],
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_path, content in documents.items():
        path = _normalized_theory_document_path(raw_path)
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"theory document {path!r} must contain text")
        normalized[path] = content
    return normalized


def _text_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def search_theory_document_lines(
    documents: Mapping[str, str],
    *,
    query: Any,
    document_paths: Any = (),
    max_results: Any = MAX_THEORY_DOCUMENT_SEARCH_HITS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized_documents = _normalized_theory_documents(documents)
    if not isinstance(query, str) or not query.strip():
        raise ClientToolInputError("theory document search query must be nonempty text")
    if not isinstance(document_paths, Sequence) or isinstance(
        document_paths, (str, bytes)
    ):
        raise ClientToolInputError(
            "theory document search document_paths must be an array"
        )
    paths = [_normalized_theory_document_path(path) for path in document_paths]
    if len(paths) != len(set(paths)):
        raise ClientToolInputError("theory document search paths must be unique")
    if not paths:
        paths = sorted(normalized_documents)
    unknown_paths = sorted(set(paths) - set(normalized_documents))
    if unknown_paths:
        raise ClientToolInputError(
            "unknown theory workspace documents: " + ", ".join(unknown_paths)
        )
    if (
        isinstance(max_results, bool)
        or not isinstance(max_results, int)
        or max_results < 1
        or max_results > MAX_THEORY_DOCUMENT_SEARCH_HITS
    ):
        raise ClientToolInputError(
            "theory document search max_results must be between 1 and "
            f"{MAX_THEORY_DOCUMENT_SEARCH_HITS}"
        )
    normalized_query = query.strip().casefold()
    hits: list[dict[str, Any]] = []
    total_matches = 0
    for path in paths:
        for line_number, line in enumerate(
            normalized_documents[path].splitlines(), start=1
        ):
            if normalized_query not in line.casefold():
                continue
            total_matches += 1
            if len(hits) < max_results:
                hits.append(
                    {
                        "path": path,
                        "line_number": line_number,
                        "line": line,
                        "line_sha256": _text_sha256(line),
                    }
                )
    if len(_compact_json(hits)) > MAX_THEORY_DOCUMENT_OBSERVATION_CHARS:
        raise ClientToolInputError(
            "theory document search exceeds one model observation; use a more "
            "specific query or fewer results"
        )
    document_hashes = {
        path: _text_sha256(normalized_documents[path]) for path in paths
    }
    inspection_ref = {
        "tool": THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        "query_hash": _text_sha256(query.strip()),
        "document_hashes": document_hashes,
        "max_results": max_results,
        "total_matches": total_matches,
        "hits": [
            {
                key: hit[key]
                for key in ("path", "line_number", "line_sha256")
            }
            for hit in hits
        ],
        "proof_evidence_status": "THEORY_DOCUMENT_INSPECTION_NOT_PROOF_EVIDENCE",
    }
    return (
        {
            "ok": True,
            "query": query.strip(),
            "document_hashes": document_hashes,
            "hits": hits,
            "total_matches": total_matches,
            "results_truncated": total_matches > len(hits),
            "proof_evidence_status": (
                "THEORY_DOCUMENT_INSPECTION_NOT_PROOF_EVIDENCE"
            ),
        },
        inspection_ref,
    )


def read_theory_document_lines(
    documents: Mapping[str, str],
    *,
    path: Any,
    line_start: Any,
    line_end: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized_documents = _normalized_theory_documents(documents)
    document_path = _normalized_theory_document_path(path)
    if document_path not in normalized_documents:
        raise ClientToolInputError(
            f"unknown theory workspace document: {document_path}"
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in (line_start, line_end)
    ):
        raise ClientToolInputError(
            "theory document line_start and line_end must be integers"
        )
    lines = normalized_documents[document_path].splitlines()
    if line_start < 1 or line_end < line_start:
        raise ClientToolInputError(
            "theory document line range must be positive and ordered"
        )
    if line_end > len(lines):
        raise ClientToolInputError(
            f"theory document line_end exceeds document length {len(lines)}"
        )
    content = "\n".join(lines[line_start - 1 : line_end])
    if len(content) > MAX_THEORY_DOCUMENT_OBSERVATION_CHARS:
        raise ClientToolInputError(
            "theory document line range exceeds one model observation; read a "
            "smaller range"
        )
    document_sha256 = _text_sha256(normalized_documents[document_path])
    content_sha256 = _text_sha256(content)
    inspection_ref = {
        "tool": THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        "path": document_path,
        "document_sha256": document_sha256,
        "line_start": line_start,
        "line_end": line_end,
        "content_sha256": content_sha256,
        "proof_evidence_status": "THEORY_DOCUMENT_INSPECTION_NOT_PROOF_EVIDENCE",
    }
    return (
        {
            "ok": True,
            "path": document_path,
            "document_sha256": document_sha256,
            "document_line_count": len(lines),
            "line_start": line_start,
            "line_end": line_end,
            "content": content,
            "content_sha256": content_sha256,
            "proof_evidence_status": (
                "THEORY_DOCUMENT_INSPECTION_NOT_PROOF_EVIDENCE"
            ),
        },
        inspection_ref,
    )


def _theory_document_media_type(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    return {
        ".md": "text/markdown",
        ".tex": "text/x-tex",
        ".bib": "application/x-bibtex",
    }[suffix]


def _persist_theory_documents(
    documents: Mapping[str, str],
    *,
    workspace_dir: Path,
) -> None:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, content in documents.items():
        target = workspace_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)


def theory_workspace_document_manifest(
    documents: Mapping[str, str],
    *,
    workspace_dir: Path | None,
) -> dict[str, Any]:
    rows = [
        {
            "document_id": "theory_document:"
            + stable_hash([relative_path, _text_sha256(content)])[:20],
            "relative_path": relative_path,
            "path": (
                str((workspace_dir / relative_path).resolve())
                if workspace_dir is not None
                else ""
            ),
            "media_type": _theory_document_media_type(relative_path),
            "sha256": _text_sha256(content),
            "byte_size": len(content.encode("utf-8")),
        }
        for relative_path, content in sorted(documents.items())
    ]
    return {
        "schema_version": 1,
        "artifact_kind": "TheoryWorkspaceDocumentManifest",
        "content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
        "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
        "workspace_root": str(workspace_dir.resolve()) if workspace_dir else "",
        "documents": rows,
        "document_set_hash": stable_hash(
            [(row["relative_path"], row["sha256"]) for row in rows]
        ),
        "runtime_edited_theory": False,
        "proof_evidence_status": "THEORY_DOCUMENTS_NOT_PROOF_EVIDENCE",
    }


def load_theory_workspace_documents(
    packet: Mapping[str, Any],
) -> dict[str, str]:
    manifest = packet.get("theory_workspace_manifest", {})
    if not isinstance(manifest, Mapping):
        return {}
    rows = manifest.get("documents", []) or []
    workspace_root_value = str(manifest.get("workspace_root", "") or "")
    if rows and not workspace_root_value:
        raise ValueError("theory workspace root is missing")
    workspace_root = (
        Path(workspace_root_value).resolve() if workspace_root_value else None
    )
    documents: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("theory workspace document reference must be an object")
        relative_path = _normalized_theory_document_path(
            row.get("relative_path", "")
        )
        path = Path(str(row.get("path", "") or "")).resolve()
        expected_path = (
            (workspace_root / relative_path).resolve()
            if workspace_root is not None
            else None
        )
        if expected_path is None or path != expected_path:
            raise ValueError(
                f"theory workspace document path mismatch: {relative_path}"
            )
        if not path.is_file():
            raise ValueError(f"theory workspace document is missing: {relative_path}")
        content = path.read_text(encoding="utf-8")
        content_sha256 = _text_sha256(content)
        if content_sha256 != str(row.get("sha256", "") or ""):
            raise ValueError(
                f"theory workspace document hash mismatch: {relative_path}"
            )
        if int(row.get("byte_size", -1) or -1) != len(content.encode("utf-8")):
            raise ValueError(
                f"theory workspace document byte-size mismatch: {relative_path}"
            )
        if row.get("media_type") != _theory_document_media_type(relative_path):
            raise ValueError(
                f"theory workspace document media-type mismatch: {relative_path}"
            )
        expected_document_id = "theory_document:" + stable_hash(
            [relative_path, content_sha256]
        )[:20]
        if row.get("document_id") != expected_document_id:
            raise ValueError(
                f"theory workspace document id mismatch: {relative_path}"
            )
        documents[relative_path] = content
    return documents


def load_theory_progress_checkpoint_state(
    checkpoint: Mapping[str, Any],
    *,
    question_id: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Verify and load exact partial theory state without accepting its claims."""

    if checkpoint.get("artifact_kind") != (
        THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND
    ):
        raise ValueError("theory progress checkpoint kind mismatch")
    if str(checkpoint.get("question_id", "") or "") != str(question_id):
        raise ValueError("theory progress checkpoint belongs to another question")
    if (
        checkpoint.get("resumable") is not True
        or checkpoint.get("accepted") is not False
        or checkpoint.get("model_owned_theory") is not True
        or checkpoint.get("runtime_edited_theory") is not False
        or checkpoint.get("kernel_verified") is not False
    ):
        raise ValueError("theory progress checkpoint evidence boundary mismatch")
    checkpoint_id = str(checkpoint.get("checkpoint_id", "") or "").strip()
    checkpoint_body = dict(checkpoint)
    checkpoint_body.pop("checkpoint_id", None)
    expected_checkpoint_id = "theory_progress_checkpoint:" + stable_hash(
        checkpoint_body
    )[:20]
    if not checkpoint_id or checkpoint_id != expected_checkpoint_id:
        raise ValueError("theory progress checkpoint identity mismatch")
    artifacts = checkpoint.get("current_artifacts", {})
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise ValueError("theory progress checkpoint has no structured state")
    manifest = checkpoint.get("theory_workspace_manifest", {})
    if not isinstance(manifest, Mapping):
        raise ValueError("theory progress checkpoint document manifest is missing")
    documents = load_theory_workspace_documents(
        {"theory_workspace_manifest": manifest}
    )
    if not documents:
        raise ValueError("theory progress checkpoint has no authoritative documents")
    if stable_hash(
        {
            "artifacts": dict(artifacts),
            "documents": documents,
        }
    ) != str(checkpoint.get("current_workspace_hash", "") or ""):
        raise ValueError("theory progress checkpoint workspace hash mismatch")
    changed_artifacts = checkpoint.get("changed_artifact_names", [])
    changed_documents = checkpoint.get("changed_document_paths", [])
    if not isinstance(changed_artifacts, list) or not all(
        isinstance(value, str) and value.strip()
        for value in changed_artifacts
    ):
        raise ValueError("theory progress changed artifacts are invalid")
    if (
        not isinstance(changed_documents, list)
        or not changed_documents
        or not all(
            isinstance(value, str) and value.strip()
            for value in changed_documents
        )
        or not set(changed_documents).issubset(documents)
    ):
        raise ValueError("theory progress changed documents are invalid")
    progress = checkpoint.get("progress", {})
    if not isinstance(progress, Mapping):
        raise ValueError("theory progress checkpoint summary is missing")
    if not all(
        str(progress.get(field, "") or "").strip()
        for field in ("summary", "next_step")
    ):
        raise ValueError("theory progress checkpoint summary is incomplete")
    evidence_refs = progress.get("evidence_refs", [])
    phase_documents = progress.get("phase_changed_document_paths", [])
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or not all(isinstance(value, str) and value.strip() for value in evidence_refs)
        or not isinstance(phase_documents, list)
        or not phase_documents
        or not set(phase_documents).issubset(changed_documents)
    ):
        raise ValueError("theory progress checkpoint evidence is incomplete")
    return deepcopy(dict(artifacts)), documents


def load_theory_workspace_document_rows(
    packet: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "sha256": _text_sha256(content),
            "content": content,
        }
        for path, content in sorted(
            load_theory_workspace_documents(packet).items()
        )
    ]


def theory_workspace_manifest_errors(
    packet: Mapping[str, Any],
    *,
    required: bool,
) -> list[str]:
    manifest = packet.get("theory_workspace_manifest", {})
    if not isinstance(manifest, Mapping) or not manifest:
        return ["theory workspace document manifest is required"] if required else []
    errors: list[str] = []
    if manifest.get("artifact_kind") != "TheoryWorkspaceDocumentManifest":
        errors.append("theory workspace document manifest kind mismatch")
    if manifest.get("content_authority") != THEORY_WORKSPACE_CONTENT_AUTHORITY:
        errors.append("theory workspace content authority mismatch")
    if manifest.get("structured_handoff_role") != THEORY_WORKSPACE_HANDOFF_ROLE:
        errors.append("theory workspace structured handoff role mismatch")
    rows = manifest.get("documents", [])
    if not isinstance(rows, list) or not rows:
        errors.append("theory workspace requires at least one Markdown/LaTeX document")
        rows = []
    expected_pairs: list[tuple[str, str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"theory workspace document {index} must be an object")
            continue
        try:
            relative_path = _normalized_theory_document_path(
                row.get("relative_path", "")
            )
        except ClientToolInputError as exc:
            errors.append(str(exc))
            continue
        sha256 = str(row.get("sha256", "") or "")
        if len(sha256) != 64:
            errors.append(f"theory document {relative_path} has invalid sha256")
        expected_pairs.append((relative_path, sha256))
    if manifest.get("document_set_hash") != stable_hash(expected_pairs):
        errors.append("theory workspace document-set hash mismatch")
    try:
        loaded = load_theory_workspace_documents(packet)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
    else:
        if len(loaded) != len(rows):
            errors.append("theory workspace document identity is not unique")
    return errors


def _artifact_shape(value: Any) -> str:
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, list):
        return "array"
    return "scalar"


def _compact_json(value: Any) -> str:
    return json.dumps(
        value,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )
