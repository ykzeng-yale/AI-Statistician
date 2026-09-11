from __future__ import annotations

import hashlib
import json
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
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
    workspace_history_tool,
)
from .estimator_interface_contract import normalize_theory_estimator_interface_contracts
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .research_source_library import (
    RESEARCH_SOURCE_LIST_TOOL,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_RESULT_INSPECT_TOOL,
    RESEARCH_SOURCE_RESULT_READ_TOOL,
    RESEARCH_SOURCE_RUN_TOOL,
    MAX_SOURCE_RESULT_ARTIFACTS,
    RESEARCH_SOURCE_SEARCH_TOOL,
    SOURCE_COMMAND_MODEL_SELECTED,
    ResearchSourceExecutionSpec,
    ResearchSourceSnapshot,
    execute_research_source_client_tool,
    execute_research_source,
    inspect_source_replication_result,
    load_source_replication_text_result,
    read_source_replication_result,
    select_research_source_execution_command,
    research_source_client_tools,
    source_replication_model_observation,
)
from .research_source_discovery import (
    RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL,
    RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
    ResearchSourceDiscovery,
    ResearchSourceDiscoveryInputError,
    execute_research_source_discovery_client_tool,
    research_source_discovery_client_tools,
)
from .scientific_sandbox import (
    SCIENTIFIC_WASM_SANDBOX_PROFILE,
    ScientificInputArtifactBinding,
    execute_scientific_sandbox,
    generated_code_draft_json_schema,
)
from .packet_validation import PacketValidationError


THEORY_WORKSPACE_CHECKPOINT_KIND = "TheoryDeveloperWorkspaceCheckpoint"
THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND = (
    "TheoryDeveloperProgressCheckpoint"
)
THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT = "model_owned_documents_and_handoff_v3"
THEORY_WORKSPACE_WRITE_TOOL = "write_theory_workspace"
THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL = "write_theory_document"
THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL = "edit_theory_document"
THEORY_WORKSPACE_REMOVE_DOCUMENT_TOOL = "remove_theory_document"
THEORY_WORKSPACE_READ_DOCUMENT_TOOL = "read_theory_document"
THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL = "search_theory_documents"
THEORY_WORKSPACE_COMMIT_TOOL = "commit_theory_checkpoint"
THEORY_WORKSPACE_PROGRESS_TOOL = "checkpoint_theory_progress"
SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL = "commit_source_replication_checkpoint"
THEORY_WORKSPACE_GAP_TOOL = "report_theory_gap"
THEORY_SCRATCHPAD_TOOL = "run_theory_scratchpad"
THEORY_SCRATCHPAD_READ_TOOL = "read_theory_scratch"
THEORY_WORKSPACE_CONTENT_AUTHORITY = "model_authored_markdown_latex_documents"
THEORY_WORKSPACE_HANDOFF_ROLE = "structured_cross_agent_index_and_abi"
THEORY_MODEL_REASONING_CONTRACT = (
    "Choose the smallest set of load-bearing claims needed for the frozen objective "
    "and independently reconstruct each from exact definitions and stated assumptions. "
    "Preserve the identity and type of every object, its domain, dependence or "
    "conditioning, scaling, and limiting regime; judge a claimed equivalence by "
    "deriving both sides from common definitions, not by familiarity or a matching "
    "endpoint. Select source reads, symbolic reductions, numerical probes, boundary "
    "cases, or counterexamples that make the reasoning decisive, but first verify that "
    "each tool call encodes the proposition and assumptions it is used to test. Inspect "
    "all active candidate text. A correct conclusion does not validate a false, "
    "circular, or unsupported step; revise, retract, or report uncertainty when the "
    "current evidence does not resolve it."
)
THEORY_FILE_CLAIM_KINDS = (
    "definition", "assumption", "lemma", "theorem", "equation", "counterexample"
)
THEORY_FILE_CLAIM_STATUSES = ("OPEN", "SUPPORTED", "REJECTED", "INCONCLUSIVE")
THEORY_FILE_SANITY_STATUSES = ("PASS", "FAIL", "INCONCLUSIVE")
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
    """Isolated environment for model-authored exploratory calculations."""

    sandbox_dir: Path
    seed: int
    replicates: int
    timeout_s: int = 20


def theory_scratchpad_client_tool() -> ClientToolDefinition:
    """Return the shared exploratory Python/R tool used by theory agents."""

    scratch_schema = generated_code_draft_json_schema(
        artifact_properties={},
        artifact_required=(),
        code_max_length=100_000,
    )
    for field in ("entrypoint", "execution_profile", "project_files"):
        scratch_schema["properties"].pop(field, None)
        if field in scratch_schema["required"]:
            scratch_schema["required"].remove(field)
    scratch_schema["properties"]["code"]["description"] = (
        "Complete Python or R script, executed once as written. Use print/cat for "
        "observations; no function entrypoint or JSON return is required. Globals "
        "seed, replicates and artifacts are supplied. Choose any useful calculation; "
        "replicates is a default, not a mandatory loop count."
    )
    scratch_schema["properties"]["source_result_artifact_paths"] = {
        "type": "array",
        "description": (
            "Optional declared UTF-8 result paths from the completed published-"
            "source run. The artifacts global maps each selected path to exact content, "
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
            "in the isolated scientific sandbox. Submit an ordinary script and print "
            "the quantities, symbolic expressions or predicates computed from "
            "the definitions, not a prewritten verdict or unconditional verification "
            "flag. Successful execution validates only this submitted program, not "
            "the stochastic model it encoded; compare its random variables, joint "
            "dependence, conditioning, parameterization, and regime with the object "
            "under review before drawing a conclusion. Raw results return here and "
            "never edit theory automatically."
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
    execution_profile = SCIENTIFIC_WASM_SANDBOX_PROFILE
    dependencies = tool_input.get("dependencies", [])
    code = str(tool_input.get("code", "") or "")
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
        entrypoint=None,
    )
    source_hash = stable_hash(code)
    if execution.code_hash and execution.code_hash != source_hash:
        raise RuntimeError("theory scratch sandbox returned a different source hash")
    code_path = execution.code_path
    if not code_path:
        source_dir = scratchpad.sandbox_dir / "model_scratch_sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        extension = "R" if language == "r" else "py"
        source_path = source_dir / f"theory_scratch_{source_hash[:24]}.{extension}"
        source_path.write_text(code, encoding="utf-8")
        code_path = str(source_path.resolve())
    request_hash = execution.request_hash or stable_hash(
        {
            "schema_version": 1,
            "artifact_kind": "TheoryScratchpadModelToolRequest",
            "artifact_id": artifact_id,
            "language": language,
            "execution_profile": execution_profile,
            "dependencies": [str(value) for value in dependencies],
            "invocation_mode": "script",
            "code_hash": source_hash,
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
        "execution_profile": execution_profile,
        "invocation_mode": execution.invocation_mode,
        "execution_attempted": execution.execution_attempted,
        "returncode": execution.returncode,
        "dependencies": list(execution.dependencies),
        "seed": int(scratchpad.seed),
        "replicates": int(scratchpad.replicates),
        "timeout_s": int(scratchpad.timeout_s),
        "errors": list(execution.errors),
        "code_hash": source_hash,
        "request_hash": request_hash,
        "request_identity_source": request_identity_source,
        "result_hash": execution.result_hash,
        "metrics_hash": stable_hash(execution.metrics),
        "code_path": code_path,
        "request_path": execution.request_path,
        "result_path": execution.result_path,
        "runtime_edited_source": False,
        "runtime_edited_theory": False,
        "input_artifact_hashes": dict(execution.input_artifact_hashes),
        "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    }
    observation = {
        "scratch_run": int(run_index),
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


def theory_scratch_execution_catalog(refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validate scratch identity while withholding host filesystem paths."""
    catalog: list[dict[str, Any]] = []
    seen_runs: set[int] = set()
    for raw_ref in refs:
        if not isinstance(raw_ref, Mapping):
            raise ValueError("theory scratch ref must be an object")
        scratch_run = raw_ref.get("scratch_run")
        if (isinstance(scratch_run, bool) or not isinstance(scratch_run, int)
                or scratch_run < 1 or scratch_run in seen_runs):
            raise ValueError("theory scratch run identity is invalid or duplicated")
        seen_runs.add(scratch_run)
        code_hash = str(raw_ref.get("code_hash", "") or "").strip()
        result_hash = str(raw_ref.get("result_hash", "") or "").strip()
        if not code_hash or not str(raw_ref.get("code_path", "") or "").strip():
            raise ValueError("theory scratch source identity is incomplete")
        if result_hash and not str(raw_ref.get("result_path", "") or "").strip():
            raise ValueError("theory scratch result identity is incomplete")
        if raw_ref.get("proof_evidence_status") != THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE:
            raise ValueError("theory scratch ref crosses the proof boundary")
        catalog.append({
            "scratch_run": scratch_run,
            "status": str(raw_ref.get("status", "") or ""),
            "language": str(raw_ref.get("language", "") or ""),
            "execution_attempted": raw_ref.get("execution_attempted"),
            "code_hash": code_hash,
            "request_hash": str(raw_ref.get("request_hash", "") or ""),
            "result_hash": result_hash,
            "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
        })
    return sorted(catalog, key=lambda row: int(row["scratch_run"]))


def read_theory_scratch_execution(*, ref: Mapping[str, Any], scratch_root: Path) -> dict[str, Any]:
    """Read one exact exploratory calculation without promoting its result."""
    root = scratch_root.expanduser().resolve()

    def bound_path(raw_path: Any, *, label: str) -> Path:
        path = Path(str(raw_path or "")).expanduser()
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
        except (FileNotFoundError, OSError, ValueError) as exc:
            raise ClientToolInputError(
                f"theory scratch {label} path is unavailable or outside its sandbox") from exc
        if path.is_symlink() or not resolved.is_file():
            raise ClientToolInputError(f"theory scratch {label} is not a regular file")
        return resolved
    source_path = bound_path(ref.get("code_path"), label="source")
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ClientToolInputError("theory scratch source is not readable UTF-8") from exc
    if stable_hash(source) != str(ref.get("code_hash", "") or ""):
        raise ClientToolInputError("theory scratch source hash is stale")
    result_payload: Any = None
    result_hash = str(ref.get("result_hash", "") or "").strip()
    if result_hash:
        result_path = bound_path(ref.get("result_path"), label="result")
        try:
            result_payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ClientToolInputError("theory scratch result is not readable JSON") from exc
        if stable_hash(result_payload) != result_hash:
            raise ClientToolInputError("theory scratch result hash is stale")
    inspection_ref = {
        "scratch_run": int(ref["scratch_run"]),
        "code_hash": str(ref["code_hash"]),
        "request_hash": str(ref.get("request_hash", "") or ""),
        "result_hash": result_hash,
        "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    }
    inspection_ref["inspection_id"] = (
        "theory-scratch-inspection:" + stable_hash(inspection_ref)[:20])
    return {
        "ok": True,
        "source": source,
        "result": result_payload,
        "request": {
            key: deepcopy(ref.get(key))
            for key in (
                "status", "language", "execution_profile", "invocation_mode", "dependencies",
                "seed", "replicates", "timeout_s", "execution_attempted",
                "returncode", "errors", "request_hash", "request_identity_source",
                "input_artifact_hashes",
            )
        },
        "inspection_ref": inspection_ref,
        "boundary": ("This is one exact TheoryDeveloper exploratory calculation. It may expose "
                     "a counterexample, but does not validate the encoded claim, establish "
                     "confirmatory evidence, or prove a theorem."),
    }


_THEORY_PROGRESS_COUNTER_FIELDS = (
    "reads",
    "submissions",
    "scratch_runs",
    "source_replication_runs",
)
_THEORY_PROGRESS_ROW_FIELDS = (
    "model_artifact_writes",
    "model_document_writes",
    "workspace_read_refs",
    "document_inspection_refs",
    "scratch_execution_refs",
    "scratch_inspection_refs",
    "source_search_refs",
    "source_read_refs",
    "source_discovery_search_refs",
    "source_discovery_read_refs",
    "source_replication_manifests",
    "source_result_read_refs",
)
_THEORY_PROGRESS_OBSERVATION_ROW_FIELDS = tuple(
    field
    for field in _THEORY_PROGRESS_ROW_FIELDS
    if field not in {"model_artifact_writes", "model_document_writes"}
)


def _theory_progress_workspace_state(
    checkpoint: Mapping[str, Any] | None,
    *,
    workspace_id: str,
    question_id: str,
    authoring_binding_id: str,
    workspace_operation: str,
) -> dict[str, Any]:
    """Restore cumulative environment state from one verified progress checkpoint."""

    state: dict[str, Any] = {
        field: 0 for field in _THEORY_PROGRESS_COUNTER_FIELDS
    }
    state.update({field: [] for field in _THEORY_PROGRESS_ROW_FIELDS})
    if not checkpoint:
        return state
    if not isinstance(checkpoint, Mapping):
        raise ValueError("prior theory progress checkpoint must be an object")
    expected_identity = {
        "artifact_kind": THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND,
        "workspace_id": workspace_id,
        "question_id": question_id,
        "authoring_binding_id": authoring_binding_id,
        "workspace_operation": workspace_operation,
    }
    for field, expected in expected_identity.items():
        if checkpoint.get(field) != expected:
            raise ValueError(
                f"prior theory progress checkpoint {field} mismatch"
            )
    for field in _THEORY_PROGRESS_COUNTER_FIELDS:
        value = checkpoint.get(field, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(
                f"prior theory progress checkpoint {field} is invalid"
            )
        state[field] = value
    for field in _THEORY_PROGRESS_ROW_FIELDS:
        rows = checkpoint.get(field, [])
        if not isinstance(rows, list) or any(
            not isinstance(row, Mapping) for row in rows
        ):
            raise ValueError(
                f"prior theory progress checkpoint {field} is invalid"
            )
        state[field] = [deepcopy(dict(row)) for row in rows]
    if state["scratch_runs"] != len(state["scratch_execution_refs"]):
        raise ValueError(
            "prior theory progress scratch count does not match executions"
        )
    for index, ref in enumerate(state["scratch_execution_refs"], start=1):
        if ref.get("scratch_run") != index:
            raise ValueError(
                "prior theory progress scratch execution order is invalid"
            )
    if state["source_replication_runs"] != len(
        state["source_replication_manifests"]
    ):
        raise ValueError(
            "prior theory progress source-run count does not match manifests"
        )
    if state["source_replication_runs"] > 1 and not all(
        manifest.get("command_owned_by_model") is True
        for manifest in state["source_replication_manifests"]
    ):
        raise ValueError(
            "repeated source execution requires model-selected command lineage"
        )
    return state


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
    read_only_documents: Mapping[str, str] | None = None,
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
    prior_removed_document_paths: Sequence[str] = (),
    prior_client_tool_session_ref: Mapping[str, Any] | None = None,
    prior_workspace_checkpoint: Mapping[str, Any] | None = None,
    prior_scratch_execution_refs: Sequence[Mapping[str, Any]] = (),
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
    source_replication_required = (task_intent or {}).get("source_replication") == "required"
    if source_replication_required and research_source_execution is None:
        raise ValueError("required source replication requires source execution")
    integrated_source_replication_required = source_replication_required and not allow_source_replication_checkpoint
    model_selected_source_execution = bool(
        research_source_execution is not None
        and research_source_execution.command_selection_mode
        == SOURCE_COMMAND_MODEL_SELECTED
    )
    integrated_commit_fields = (
        {
            "source_replication_report_document_path",
            "source_replication_readiness_rationale",
            "source_replication_unresolved_gaps",
        }
        if integrated_source_replication_required
        else set()
    )
    if integrated_source_replication_required and model_selected_source_execution:
        integrated_commit_fields.add("source_replication_selected_source_run")
    restored_tool_state = _theory_progress_workspace_state(
        prior_workspace_checkpoint,
        workspace_id=workspace_id,
        question_id=question_id,
        authoring_binding_id=authoring_binding_id,
        workspace_operation=workspace_operation,
    )
    inherited_scratch_refs = [deepcopy(dict(ref)) for ref in prior_scratch_execution_refs]
    theory_scratch_execution_catalog(inherited_scratch_refs)
    if inherited_scratch_refs and prior_workspace_checkpoint:
        # A progress checkpoint may append observations to its published parent.
        if stable_hash(inherited_scratch_refs) != stable_hash(
                restored_tool_state["scratch_execution_refs"][:len(inherited_scratch_refs)]):
            raise ValueError("continued theory scratch lineage conflicts with checkpoint")
    elif inherited_scratch_refs:
        restored_tool_state["scratch_execution_refs"] = inherited_scratch_refs
        restored_tool_state["scratch_runs"] = len(inherited_scratch_refs)
    theory_scratch_execution_catalog(restored_tool_state["scratch_execution_refs"])
    if restored_tool_state["scratch_execution_refs"] and scratchpad is None:
        raise ValueError("continued theory scratch lineage requires its sandbox")
    if (
        restored_tool_state["source_replication_runs"]
        and research_source_execution is None
    ):
        raise ValueError(
            "continued source-replication state requires source execution"
        )
    restored_source_manifests = restored_tool_state[
        "source_replication_manifests"
    ]
    if restored_source_manifests and any(
        (manifest.get("command_owned_by_model") is True)
        != model_selected_source_execution
        for manifest in restored_source_manifests
    ):
        raise ValueError(
            "continued source-execution state changed command authority"
        )
    parent = {
        str(name): deepcopy(value)
        for name, value in initial_artifacts.items()
        if str(name).strip()
    }
    if not parent:
        raise ValueError("theory workspace requires initial artifacts")
    if "estimator_specs" in parent:
        normalize_theory_estimator_interface_contracts(parent)
    parent_documents = _normalized_theory_documents(initial_documents or {})
    context_documents = _normalized_theory_documents(read_only_documents or {})
    overlapping_document_paths = sorted(
        set(parent_documents).intersection(context_documents)
    )
    if overlapping_document_paths:
        raise ValueError(
            "theory workspace read-only documents overlap writable documents: "
            + ", ".join(overlapping_document_paths)
        )
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
    prior_removed_documents = tuple(
        dict.fromkeys(
            _normalized_theory_document_path(path)
            for path in prior_removed_document_paths
        )
    )
    if set(prior_removed_documents) - set(prior_document_changes):
        raise ValueError(
            "theory progress removed documents must be changed documents"
        )
    if set(prior_removed_documents).intersection(parent_documents):
        raise ValueError(
            "theory progress removed documents remain in the current workspace"
        )
    unknown_prior_documents = sorted(
        set(prior_document_changes)
        - set(parent_documents)
        - set(prior_removed_documents)
    )
    if unknown_prior_documents:
        raise ValueError(
            "theory progress checkpoint has unknown changed documents: "
            + ", ".join(unknown_prior_documents)
        )
    state: dict[str, Any] = {
        "artifacts": deepcopy(parent),
        "documents": deepcopy(parent_documents),
        **restored_tool_state,
        "last_validation_errors": [],
        "last_candidate": {},
    }
    phase_prior_observation_hashes = {
        field: {stable_hash(row) for row in state[field]}
        for field in _THEORY_PROGRESS_OBSERVATION_ROW_FIELDS
    }
    tools = _theory_workspace_tools(
        scratchpad_enabled=scratchpad is not None,
        research_sources_enabled=research_sources is not None,
        research_source_discovery_enabled=research_source_discovery is not None,
        research_repository_acquisition_enabled=bool(
            research_source_discovery is not None
            and research_source_discovery.descriptor().get("repository_snapshot_acquisition_allowed") is True
        ),
        research_source_execution_enabled=research_source_execution is not None,
        model_selected_source_execution=model_selected_source_execution,
        source_replication_checkpoint_enabled=allow_source_replication_checkpoint,
        integrated_source_replication_required=(
            integrated_source_replication_required
        ),
        document_authority_enabled=require_document_authority,
        writable_artifact_names=selected_writable_names,
    )
    if resolved_workspace_dir is not None:
        tools = (*tools, workspace_history_tool())

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

    def current_removed_document_paths(
        documents: Mapping[str, str],
    ) -> tuple[str, ...]:
        return tuple(path for path in parent_documents if path not in documents)

    def removed_document_paths(documents: Mapping[str, str]) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                path
                for path in (
                    *prior_removed_documents,
                    *current_removed_document_paths(documents),
                )
                if path not in documents
            )
        )

    def current_phase_observation_refs() -> tuple[dict[str, Any], ...]:
        refs: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for field in _THEORY_PROGRESS_OBSERVATION_ROW_FIELDS:
            prior_hashes = phase_prior_observation_hashes[field]
            for row_index, row in enumerate(state[field], start=1):
                row_hash = stable_hash(row)
                identity = (field, row_hash)
                if row_hash in prior_hashes or identity in seen:
                    continue
                seen.add(identity)
                refs.append(
                    {
                        "state_field": field,
                        "row_index": row_index,
                        "row_hash": row_hash,
                    }
                )
        return tuple(refs)

    def document_manifest(documents: Mapping[str, str]) -> dict[str, Any]:
        snapshot_dir = resolved_workspace_dir
        if snapshot_dir is not None:
            snapshot_hash = stable_hash(dict(documents))
            snapshot_dir = snapshot_dir / ".immutable_checkpoints" / snapshot_hash
            _persist_theory_documents(documents, workspace_dir=snapshot_dir)
        return theory_workspace_document_manifest(
            documents,
            workspace_dir=snapshot_dir,
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

    def readable_documents() -> dict[str, str]:
        return {**state["documents"], **context_documents}

    def evaluate_model_write(
        candidate_artifacts: Mapping[str, Any],
        candidate_documents: Mapping[str, str],
        *,
        artifact_writes: Sequence[Mapping[str, Any]] = (),
        document_writes: Sequence[Mapping[str, Any]] = (),
    ) -> ClientToolExecutionResult:
        # Bind the same derived interface identities used by the published handoff.
        candidate_artifacts = deepcopy(dict(candidate_artifacts))
        if "estimator_specs" in candidate_artifacts:
            normalize_theory_estimator_interface_contracts(candidate_artifacts)
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
        if resolved_workspace_dir is not None:
            _persist_theory_documents(
                candidate_documents,
                workspace_dir=resolved_workspace_dir,
                previous_documents=state["documents"],
            )
        state["artifacts"] = deepcopy(dict(candidate_artifacts))
        state["documents"] = deepcopy(dict(candidate_documents))
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
        removed_documents = removed_document_paths(candidate_documents)
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
                    "removed_document_paths": list(removed_documents),
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
                            (
                                path,
                                _text_sha256(candidate_documents[path])
                                if path in candidate_documents
                                else None,
                            )
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
            "removed_document_paths": list(removed_documents),
            "current_document_sha256": {path: _text_sha256(candidate_documents[path]) for path in changed_documents if path in candidate_documents},
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

    def source_replication_checkpoint(
        tool_input: Mapping[str, Any],
        *,
        report_field: str,
        rationale_field: str,
        gaps_field: str,
        selected_run_field: str,
    ) -> dict[str, Any]:
        manifests = state["source_replication_manifests"]
        if not manifests or state["source_replication_runs"] != len(manifests):
            raise ClientToolInputError(
                "source replication checkpoint requires completed source runs"
            )
        report_path = _normalized_theory_document_path(tool_input.get(report_field))
        if report_path not in state["documents"]:
            raise ClientToolInputError("source replication report document is unavailable")
        if report_path not in changed_document_paths(state["documents"]):
            raise ClientToolInputError("source replication checkpoint requires a model-authored report")
        rationale = tool_input.get(rationale_field)
        if not isinstance(rationale, str) or not rationale.strip():
            raise ClientToolInputError("source replication readiness_rationale must be nonempty")
        unresolved_gaps = tool_input.get(gaps_field)
        if not isinstance(unresolved_gaps, list) or not all(
            isinstance(value, str) and value.strip() for value in unresolved_gaps
        ):
            raise ClientToolInputError("source replication unresolved_gaps must be an array of nonempty text")
        model_selected_lineage = model_selected_source_execution
        if model_selected_lineage and any(
            manifest.get("command_owned_by_model") is not True
            or manifest.get("command_selection_mode")
            != SOURCE_COMMAND_MODEL_SELECTED
            or not str(manifest.get("command_request_hash", "") or "")
            or not str(manifest.get("execution_attempt_id", "") or "")
            for manifest in manifests
        ):
            raise ClientToolInputError(
                "model-selected source attempts have incomplete lineage"
            )
        if not model_selected_lineage and len(manifests) != 1:
            raise ClientToolInputError(
                "operator-fixed source execution requires exactly one run"
            )
        if model_selected_lineage:
            selected_source_run = tool_input.get(selected_run_field)
            if (
                isinstance(selected_source_run, bool)
                or not isinstance(selected_source_run, int)
                or selected_source_run < 1
                or selected_source_run > len(manifests)
            ):
                raise ClientToolInputError(
                    "source replication selected_source_run must identify one "
                    "completed model-selected run"
                )
        else:
            selected_source_run = 1
        source_manifest = manifests[selected_source_run - 1]
        if source_manifest.get("execution_status") != "EXECUTED" and not unresolved_gaps:
            raise ClientToolInputError("failed source execution requires an explicit unresolved gap")
        report_rows = [
            row for row in document_manifest(state["documents"]).get("documents", []) or []
            if row.get("relative_path") == report_path
        ]
        if len(report_rows) != 1:
            raise ClientToolInputError("source replication report identity is ambiguous")
        checkpoint_body = {
            "schema_version": 1, "artifact_kind": SOURCE_REPLICATION_CHECKPOINT_KIND,
            "question_id": question_id, "workspace_id": workspace_id,
            "task_intent": dict(task_intent or {}),
            "source_replication_manifest_ref": {
                key: str(source_manifest.get(key, "") or "")
                for key in ("artifact_id", "manifest_hash", "execution_status", "stdout_sha256")
            },
            "report_document": deepcopy(report_rows[0]),
            "unresolved_gaps": [value.strip() for value in unresolved_gaps],
            "readiness_rationale": rationale.strip(),
            "runtime_edited_source": False, "runtime_edited_report": False,
            "model_authored_report": True, "kernel_verified": False,
            "proof_evidence_status": "SOURCE_REPLICATION_CHECKPOINT_NOT_PROOF_EVIDENCE",
        }
        if source_manifest.get("command_owned_by_model") is True:
            checkpoint_body.update({
                "source_execution_attempt_refs": [
                    {
                        "source_run": index,
                        "artifact_id": str(manifest.get("artifact_id", "") or ""),
                        "manifest_hash": str(manifest.get("manifest_hash", "") or ""),
                        "execution_status": str(
                            manifest.get("execution_status", "") or ""
                        ),
                        "command_request_hash": str(
                            manifest.get("command_request_hash", "") or ""
                        ),
                        "execution_attempt_id": str(
                            manifest.get("execution_attempt_id", "") or ""
                        ),
                    }
                    for index, manifest in enumerate(manifests, start=1)
                ],
                "selected_source_run": selected_source_run,
            })
        return {
            **checkpoint_body,
            "checkpoint_id": "source_replication_checkpoint:" + stable_hash(checkpoint_body)[:20],
        }

    def source_manifest_for_run(raw_source_run: Any = None) -> dict[str, Any]:
        manifests = state["source_replication_manifests"]
        if not manifests:
            raise ClientToolInputError(
                "source result inspection requires a completed source run"
            )
        source_run = len(manifests) if raw_source_run is None else raw_source_run
        if (
            isinstance(source_run, bool)
            or not isinstance(source_run, int)
            or source_run < 1
            or source_run > len(manifests)
        ):
            raise ClientToolInputError("unknown source_run")
        return manifests[source_run - 1]

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
            current_readable_documents = readable_documents()
            unknown_documents = sorted(
                set(document_paths) - set(current_readable_documents)
            )
            if unknown_documents:
                raise ClientToolInputError(
                    "unknown theory workspace documents: "
                    + ", ".join(unknown_documents)
                )
            selected_documents = {
                path: current_readable_documents[path] for path in document_paths
            }
            if len(_compact_json(selected)) + sum(
                len(value) for value in selected_documents.values()
            ) > 55_000:
                raise ClientToolInputError(
                    "selected theory material exceeds one observation; read less material"
                )
            state["workspace_read_refs"].append(
                {
                    "tool": "read_theory_workspace",
                    "artifact_hashes": {
                        name: stable_hash(selected[name])
                        for name in sorted(selected)
                    },
                    "document_sha256": {
                        path: _text_sha256(selected_documents[path])
                        for path in sorted(selected_documents)
                    },
                    "proof_evidence_status": (
                        "THEORY_WORKSPACE_READ_NOT_PROOF_EVIDENCE"
                    ),
                }
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

        if call.name in {
            THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
            THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        }:
            observation, inspection_ref = execute_theory_document_client_tool(
                readable_documents(), tool_name=call.name, tool_input=tool_input
            )
            state["document_inspection_refs"].append(inspection_ref)
            state["reads"] += 1
            return ClientToolExecutionResult(
                content={**observation, "reads": state["reads"]},
                observation_key="theory-document:" + stable_hash(inspection_ref),
            )

        if call.name in {
            RESEARCH_SOURCE_LIST_TOOL,
            RESEARCH_SOURCE_SEARCH_TOOL,
            RESEARCH_SOURCE_READ_TOOL,
        }:
            if research_sources is None:
                raise ClientToolInputError("research source snapshot is unavailable")
            try:
                observation, source_ref = execute_research_source_client_tool(
                    research_sources,
                    tool_name=call.name,
                    tool_input=tool_input,
                )
            except ValueError as exc:
                raise ClientToolInputError(str(exc)) from exc
            state[
                "source_read_refs"
                if call.name == RESEARCH_SOURCE_READ_TOOL
                else "source_search_refs"
            ].append(source_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key=call.name + ":" + stable_hash(source_ref),
            )

        if call.name in {RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL, RESEARCH_SOURCE_DISCOVERY_READ_TOOL, RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL}:
            if research_source_discovery is None:
                raise ClientToolInputError(
                    "public research source discovery is unavailable"
                )
            try:
                observation, source_ref, is_error = (
                    execute_research_source_discovery_client_tool(
                        research_source_discovery,
                        tool_name=call.name,
                        tool_input=tool_input,
                    )
                )
            except ResearchSourceDiscoveryInputError as exc:
                raise ClientToolInputError(str(exc)) from exc
            if source_ref:
                state[
                    "source_discovery_search_refs"
                    if call.name == RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL
                    else "source_discovery_read_refs"
                ].append(source_ref)
            return ClientToolExecutionResult(
                content=observation,
                is_error=is_error,
                observation_key=call.name + ":" + stable_hash(source_ref or observation),
            )

        if call.name == RESEARCH_SOURCE_RUN_TOOL:
            if research_sources is None or research_source_execution is None:
                raise ClientToolInputError("research source execution is unavailable")
            if model_selected_source_execution:
                try:
                    active_execution = select_research_source_execution_command(
                        research_source_execution,
                        research_sources=research_sources,
                        command=tool_input,
                    )
                except ValueError as exc:
                    raise ClientToolInputError(str(exc)) from exc
            else:
                if tool_input:
                    raise ClientToolInputError(
                        "run_research_source accepts no input fields"
                    )
                if state["source_replication_runs"]:
                    raise ClientToolInputError(
                        "the immutable research source has already been executed"
                    )
                active_execution = research_source_execution
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
                    execution=active_execution,
                    research_sources=research_sources,
                    output_dir=output_dir,
                    question_id=question_id,
                    execution_attempt_id=(
                        "source_attempt:"
                        + stable_hash(
                            [workspace_id, authoring_binding_id, run_index]
                        )[:20]
                        if model_selected_source_execution
                        else ""
                    ),
                )
            except (OSError, UnicodeError, ValueError) as exc:
                raise ClientToolInputError(str(exc)) from exc
            state["source_replication_runs"] = run_index
            state["source_replication_manifests"].append(deepcopy(manifest))
            execution_observation = {
                "ok": manifest.get("execution_status") == "EXECUTED",
                "source_replication_manifest": (
                    source_replication_model_observation(manifest)
                ),
            }
            if model_selected_source_execution:
                execution_observation.update({
                    "source_run": run_index,
                    "additional_model_selected_commands_allowed": True,
                })
            else:
                execution_observation["remaining_source_replication_runs"] = 0
            return ClientToolExecutionResult(
                content=execution_observation,
                state_changed=True,
                observation_key="research-source-execution:"
                + str(manifest.get("manifest_hash", "") or stable_hash(manifest)),
            )

        if call.name == RESEARCH_SOURCE_RESULT_READ_TOOL:
            result_read_fields = {
                "relative_path", "line_start", "line_end"
            }
            if model_selected_source_execution:
                result_read_fields.add("source_run")
            if set(tool_input) - result_read_fields or not {
                "relative_path", "line_start", "line_end"
            }.issubset(tool_input):
                raise ClientToolInputError(
                    "read_research_source_result requires relative_path, "
                    "line_start, and line_end"
                    + (
                        "; source_run is optional"
                        if model_selected_source_execution
                        else ""
                    )
                )
            source_manifest = source_manifest_for_run(tool_input.get("source_run"))
            try:
                observation = read_source_replication_result(
                    source_manifest,
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
            if model_selected_source_execution:
                result_ref["source_run"] = (
                    int(tool_input["source_run"])
                    if "source_run" in tool_input
                    else len(state["source_replication_manifests"])
                )
            state["source_result_read_refs"].append(result_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key="research-source-result-read:"
                + stable_hash(result_ref),
            )

        if call.name == RESEARCH_SOURCE_RESULT_INSPECT_TOOL:
            result_inspection_fields = {"relative_path"}
            if model_selected_source_execution:
                result_inspection_fields.add("source_run")
            if set(tool_input) - result_inspection_fields or (
                "relative_path" not in tool_input
            ):
                raise ClientToolInputError(
                    "inspect_research_source_result requires relative_path"
                    + (
                        "; source_run is optional"
                        if model_selected_source_execution
                        else ""
                    )
                )
            source_manifest = source_manifest_for_run(tool_input.get("source_run"))
            try:
                observation, media_block = inspect_source_replication_result(
                    source_manifest,
                    relative_path=tool_input.get("relative_path"),
                )
            except (OSError, UnicodeError, ValueError) as exc:
                raise ClientToolInputError(str(exc)) from exc
            result_ref = {**observation, "tool": call.name}
            if model_selected_source_execution:
                result_ref["source_run"] = (
                    int(tool_input["source_run"])
                    if "source_run" in tool_input
                    else len(state["source_replication_manifests"])
                )
            state["source_result_read_refs"].append(result_ref)
            return ClientToolExecutionResult(
                content=observation, model_content_blocks=(media_block,),
                observation_key="research-source-result-inspection:"
                + stable_hash(result_ref),
            )

        if call.name == THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL:
            if not require_document_authority:
                raise ClientToolInputError(
                    "write_theory_document is unavailable"
                )
            requested_path = _normalized_theory_document_path(
                tool_input.get("path", "")
            )
            if requested_path in context_documents:
                raise ClientToolInputError(
                    f"theory workspace document {requested_path!r} is read-only"
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
            requested_path = _normalized_theory_document_path(
                tool_input.get("path", "")
            )
            if requested_path in context_documents:
                raise ClientToolInputError(
                    f"theory workspace document {requested_path!r} is read-only"
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

        if call.name == THEORY_WORKSPACE_REMOVE_DOCUMENT_TOOL:
            if not require_document_authority:
                raise ClientToolInputError(
                    "theory document removal is unavailable"
                )
            requested_path = _normalized_theory_document_path(
                tool_input.get("path", "")
            )
            if requested_path in context_documents:
                raise ClientToolInputError(
                    f"theory workspace document {requested_path!r} is read-only"
                )
            candidate_documents, remove_record = (
                _remove_theory_workspace_document(
                    state["documents"],
                    tool_input,
                )
            )
            return evaluate_model_write(
                state["artifacts"],
                candidate_documents,
                document_writes=[remove_record],
            )

        if call.name == THEORY_WORKSPACE_COMMIT_TOOL:
            expected_commit_fields = {"readiness_rationale", *integrated_commit_fields}
            if set(tool_input) != expected_commit_fields:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires exactly "
                    + ", ".join(sorted(expected_commit_fields))
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
            removed_documents = removed_document_paths(state["documents"])
            if (not changed and not changed_documents) or not state["submissions"]:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires a prior model-authored "
                    "workspace revision"
                )
            integrated_source_checkpoint = (
                source_replication_checkpoint(
                    tool_input,
                    report_field="source_replication_report_document_path",
                    rationale_field="source_replication_readiness_rationale",
                    gaps_field="source_replication_unresolved_gaps",
                    selected_run_field=(
                        "source_replication_selected_source_run"
                    ),
                )
                if integrated_source_replication_required
                else {}
            )
            report_path = str(integrated_source_checkpoint.get("report_document", {}).get("relative_path", "") or "")
            theory_documents = {path: content for path, content in state["documents"].items() if path != report_path}
            theory_changed_documents = tuple(path for path in changed_documents if path != report_path)
            if require_document_authority and not theory_documents:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires model-authored Markdown or LaTeX"
                )
            if require_document_authority and not theory_changed_documents:
                raise ClientToolInputError(
                    "commit_theory_checkpoint requires a changed authoritative "
                    "Markdown or LaTeX document"
                )
            raw_candidate = build_candidate(
                state["artifacts"],
                changed,
                document_manifest(theory_documents),
                theory_changed_documents,
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
                    "removed_document_paths": list(removed_documents),
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
                    "removed_document_paths": list(removed_documents),
                    "theory_workspace_manifest": document_manifest(
                        state["documents"]
                    ),
                    "readiness_rationale": rationale,
                    "source_replication_checkpoint": integrated_source_checkpoint,
                },
                observation_key="theory-workspace-committed:"
                + stable_hash([candidate_hash, rationale]),
            )

        if call.name == SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL:
            if not allow_source_replication_checkpoint:
                raise ClientToolInputError(
                    "source replication checkpoint is unavailable"
                )
            expected_source_commit_fields = {
                "report_document_path",
                "readiness_rationale",
                "unresolved_gaps",
            }
            if model_selected_source_execution:
                expected_source_commit_fields.add("selected_source_run")
            if set(tool_input) != expected_source_commit_fields:
                raise ClientToolInputError(
                    "commit_source_replication_checkpoint requires exactly "
                    + ", ".join(sorted(expected_source_commit_fields))
                )
            checkpoint = source_replication_checkpoint(
                tool_input,
                report_field="report_document_path",
                rationale_field="readiness_rationale",
                gaps_field="unresolved_gaps",
                selected_run_field="selected_source_run",
            )
            checkpoint_id = checkpoint["checkpoint_id"]
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
                    "removed_document_paths": list(
                        removed_document_paths(state["documents"])
                    ),
                    "theory_workspace_manifest": document_manifest(
                        state["documents"]
                    ),
                },
                observation_key="source-replication-checkpoint:"
                + checkpoint_hash,
            )

        if call.name == THEORY_SCRATCHPAD_READ_TOOL:
            if scratchpad is None:
                raise ClientToolInputError("theory scratch environment is unavailable")
            if set(tool_input) != {"scratch_run"}:
                raise ClientToolInputError("read_theory_scratch requires scratch_run")
            scratch_run = tool_input.get("scratch_run")
            if isinstance(scratch_run, bool) or not isinstance(scratch_run, int):
                raise ClientToolInputError("theory scratch_run must be an integer")
            refs_by_run = {int(ref["scratch_run"]): ref
                           for ref in state["scratch_execution_refs"]}
            if scratch_run not in refs_by_run:
                raise ClientToolInputError("unknown theory scratch_run")
            observation = read_theory_scratch_execution(
                ref=refs_by_run[scratch_run], scratch_root=scratchpad.sandbox_dir)
            state["scratch_inspection_refs"].append(observation["inspection_ref"])
            state["reads"] += 1
            return ClientToolExecutionResult(
                content={**observation, "reads": state["reads"]},
                observation_key="theory-scratch-read:" + stable_hash(
                    observation["inspection_ref"]),
            )

        if call.name == THEORY_SCRATCHPAD_TOOL:
            if scratchpad is None:
                raise ClientToolInputError("theory scratchpad is unavailable")
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
                source_manifest = source_manifest_for_run()
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
                    try:
                        loaded_result = load_source_replication_text_result(
                            source_manifest,
                            relative_path=relative_path,
                        )
                    except (OSError, UnicodeError, ValueError) as exc:
                        raise ClientToolInputError(
                            "source result artifact is not available as UTF-8 text: "
                            + relative_path
                        ) from exc
                    content = str(loaded_result["content"])
                    expected_sha256 = str(row.get("sha256", "") or "")
                    observed_sha256 = str(loaded_result["artifact_sha256"])
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
            phase_artifact_changes = current_changed_artifact_names(
                state["artifacts"]
            )
            phase_document_changes = current_changed_document_paths(state["documents"])
            phase_removed_documents = current_removed_document_paths(
                state["documents"]
            )
            phase_observation_refs = current_phase_observation_refs()
            if not (
                phase_artifact_changes
                or phase_document_changes
                or phase_removed_documents
                or phase_observation_refs
            ):
                raise ClientToolInputError(
                    "checkpoint_theory_progress requires a new or revised "
                    "workspace artifact or a new exact environment observation "
                    "in the current continuation phase"
                )
            progress = {
                "summary": summary.strip(),
                "evidence_refs": [
                    value.strip() for value in evidence_refs
                ],
                "next_step": next_step.strip(),
                "phase_changed_artifact_names": list(phase_artifact_changes),
                "phase_changed_document_paths": list(phase_document_changes),
                "phase_removed_document_paths": list(phase_removed_documents),
                "phase_observation_refs": [
                    deepcopy(ref) for ref in phase_observation_refs
                ],
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
    scratch_catalog = theory_scratch_execution_catalog(
        state["scratch_execution_refs"]
    )
    document_catalog = {
        row["relative_path"]: {
            "media_type": row["media_type"],
            "sha256": row["sha256"],
            "byte_size": row["byte_size"],
            "line_count": len(
                state["documents"][row["relative_path"]].splitlines()
            ),
            "writable": True,
        }
        for row in document_manifest(state["documents"]).get("documents", [])
    }
    context_document_catalog = {
        path: {
            "media_type": _theory_document_media_type(path),
            "sha256": _text_sha256(content),
            "byte_size": len(content.encode("utf-8")),
            "line_count": len(content.splitlines()),
            "writable": False,
        }
        for path, content in sorted(context_documents.items())
    }
    write_guidance = (
        (
            "Use write_theory_document(path, content) to write one complete "
            "Markdown/LaTeX document or BibTeX file, and use "
            "write_theory_workspace only for the compact cross-agent index or "
            "executable ABI. Text documents remain the mathematical authority. "
        )
        if require_document_authority
        else (
            "Use write_theory_workspace for complete model-owned structured artifacts; "
            "Authoritative Markdown/LaTeX documents are unavailable in this "
            "compatibility workspace. "
        )
    ) + "Omitted files remain byte-identical; runtime stores values without merging or inventing content. "
    document_inspection_guidance = (
        "For long mathematics, use search_theory_documents for literal claims or "
        "labels and read_theory_document for only the "
        "needed hash-bound ranges. Choose inspections that improve the argument; "
        "read counts never substitute for readiness judgment or independent review. "
        if require_document_authority
        else ""
    )
    edit_guidance = (
        "For a localized revision to an existing mathematical document, use "
        "edit_theory_document with the current document SHA-256 and one ordered atomic "
        "batch of exact model-selected replacements. The runtime applies all edits or "
        "none, returns current_document_sha256 for the next edit, and never interprets "
        "mathematics. "
        if require_document_authority
        else ""
    )
    progress_guidance = (
        "When you have made substantive workspace progress but additional derivation "
        "or handoff work is genuinely needed beyond this session, call "
        "checkpoint_theory_progress with the evidence you inspected and one concrete "
        "next step. Progress may be a model-authored workspace revision or a new exact "
        "source, scratch, or workspace observation that changes the next research "
        "step. An unchanged reread cannot justify another continuation. This requests "
        "same-owner continuation and is not accepted theory, empirical evidence, or "
        "proof. Address validator observations directly using the shared action "
        "budget; there is no separate read or write quota. An unfinished structured "
        "handoff is not a mathematical gap. Prior observations and their exact refs "
        "remain cumulative across continuation. "
        if require_document_authority
        else ""
    )
    scratch_guidance = (
        "Use run_theory_scratchpad when a small Python or R calculation, exact "
        "model-chosen SymPy reduction, numerical check, or counterexample would resolve "
        "a mathematical uncertainty. Submit "
        "an ordinary script and print its observations; the isolated runtime "
        "executes those exact bytes without requiring a function or JSON return. "
        "Globals seed, replicates and artifacts are provided. After a published-"
        "source run, you may select declared UTF-8 result paths and query their "
        "exact hash-bound "
        "contents with your own Python or R rather than asking the runtime to "
        "interpret them. Encode the complete disputed proposition as the left and right "
        "sides, residuals, predicates, or witnesses computed from definitions rather "
        "than a prewritten conclusion; a weaker consequence cannot validate a stronger "
        "claim merely by taking its label. "
        "Use read_theory_scratch(scratch_run) to reopen any exact prior request, source, "
        "status, and available result instead of rerunning it from memory. Interpret the "
        "raw observation yourself. If it conflicts with an active "
        "document or earlier calculation, rederive and revise, retract, or mark the claim uncertain before checkpointing. Scratch output is exploratory, not "
        "confirmatory simulation or proof; a universal claim still needs an argument. "
        if scratchpad is not None
        else ""
    )
    source_guidance = (
        "A hash-bound model-visible research source snapshot is available. Use "
        "list_research_source_directory to navigate a frozen project when paths are "
        "unknown, then search_research_sources and read_research_source directly in "
        "this same session when a definition, assumption, theorem, algorithm, or "
        "claimed precedent depends on prior work. Decide what to inspect and how to "
        "use it yourself. For a method, model class, score, or implementation-specific "
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
        (
            "A model-directed reproduction environment is available through "
            "run_research_source. Inspect the frozen project, then choose one exact "
            "entrypoint document, working directory, argument vector, and declared "
            "result paths. The runtime fixes and revalidates the interpreter, packages, "
            "snapshot, resource policy, network denial, and secret isolation. Each "
            "command runs in a fresh workspace and raw feedback returns here; revise "
            "your command choice rather than asking a repair worker. At checkpoint, "
            "explicitly select the completed source_run that your report advances; "
            "all attempt hashes remain evidence. "
            "Inspect and interpret each observation yourself. The visible execution "
            "descriptor and returned manifest state the exact working directory and "
            "argument vector. For larger UTF-8 outputs, either read exact lines or "
            "select the result paths in your existing scratch tool and analyze them "
            "with model-authored code. When the task calls for visual evidence, you "
            "may inspect declared PDF or image outputs; tool availability does not "
            "expand the task's permitted scope. It is exploratory source-execution evidence, "
            "not model-authored scientific code, confirmatory simulation, or theorem "
            "proof. "
        )
        if model_selected_source_execution
        else (
            "An operator-bound hash-verified author-source execution is available through "
            "run_research_source. The tool accepts no command, path, argument, or code from "
            "you: it revalidates the pinned snapshot and environment, denies network and "
            "secret inheritance, runs the exact published entrypoint, and returns raw "
            "stdout/stderr plus any operator-declared result artifacts from an isolated "
            "copy-on-write source workspace to this same session. Inspect and interpret "
            "that observation yourself. The visible execution descriptor and returned "
            "manifest state the exact working directory and argument vector. For larger "
            "UTF-8 outputs, either read exact lines or select the result paths in your "
            "existing scratch tool and analyze them with model-authored code. When "
            "the task calls for visual evidence, you may inspect declared PDF or image "
            "outputs; tool availability does not expand the task's permitted scope. It is "
            "source-replication evidence, not model-authored scientific code, "
            "confirmatory simulation, or theorem proof. "
        )
    ) if research_source_execution is not None else ""
    source_checkpoint_guidance = (
        "This task has no required substantive lane beyond "
        + (
            "model-directed source reproduction "
            if model_selected_source_execution
            else "exact source replication "
        )
        + "and honest gap disclosure. After inspecting the sources and raw run, write a "
        "durable Markdown report with the reproduced outputs, identity evidence, "
        "comparison, interpretation, and caveats. Keep exact execution facts separate "
        "from mathematical interpretation; if an interpretation is not grounded in "
        "an exact source read, record that limitation as an unresolved gap. Before "
        "committing, inspect the exact saved report in this same session and audit its "
        "active numerical comparisons, threshold decisions, method labels, scope, and "
        "gap disclosures against the raw execution observation, inspected source, and "
        "visible request. Search specifically for a locally false interpretation even "
        "when the surrounding table is copied correctly. Revise the report yourself if "
        "that audit finds a discrepancy; do not treat the first complete write as ready "
        "merely because it is well formed. Then call "
        "commit_source_replication_checkpoint. Do not invent theory, estimator, "
        "simulation, formalization, or novelty work. Pass unresolved_gaps as an empty "
        "array or an array of nonempty plain "
        "strings; do not use objects or placeholder empty strings. "
        if allow_source_replication_checkpoint
        else ""
    )
    integrated_source_checkpoint_guidance = (
        "This task requires "
        + (
            "model-directed source reproduction"
            if model_selected_source_execution
            else "exact source replication"
        )
        + " plus further research. In this retained workspace, execute the configured "
        "source lane and write a durable Markdown report. Audit it "
        "against raw observations and exact reads; distinguish facts, interpretation, and gaps. "
        "Pass its path, a replication-specific rationale, and plain-string gaps to the final "
        "theory commit. That commit binds both artifacts but replication validates neither "
        "theory, generated code, confirmatory evidence, nor proof. "
        if integrated_source_replication_required
        else ""
    )
    root_authorization_fingerprint = client_tool_authorization_fingerprint(
        request_metadata
    ) or stable_hash(["theory", workspace_id, question_id])
    source_environment_identity = {}
    if research_sources is not None:
        source_environment_identity["research_source_snapshot"] = (
            research_sources.descriptor()
        )
    if research_source_discovery is not None:
        source_environment_identity["public_research_source_discovery"] = dict(
            research_source_discovery.descriptor()
        )
    if research_source_execution is not None and research_sources is not None:
        source_environment_identity["research_source_execution"] = (
            research_source_execution.descriptor(research_sources)
        )
    if source_environment_identity:
        root_authorization_fingerprint = stable_hash(
            {
                "root_authorization_fingerprint": root_authorization_fingerprint,
                "source_environment": source_environment_identity,
            }
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
                            "theory_scratch_executions": scratch_catalog,
                            **(
                                {
                                    "read_only_context_documents": (
                                        context_document_catalog
                                    )
                                }
                                if context_document_catalog
                                else {}
                            ),
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
                    + (
                        "Read-only context documents use the same document read and "
                        "search tools; they are observations, not editable or "
                        "authoritative mathematics. "
                        if context_document_catalog
                        else ""
                    )
                    + source_discovery_guidance
                    + source_guidance
                    + source_execution_guidance
                    + source_checkpoint_guidance
                    + integrated_source_checkpoint_guidance
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
                    "current argument. Every unmarked paragraph and equation in an "
                    "authoritative document remains an active claim; narrative chronology "
                    "or a later correction does not revoke its authority. Remove or rewrite "
                    "a step you have shown false, or move it under a clearly delimited "
                    "REJECTED or SCRATCH section that no active claim depends on. "
                    + "If a mathematical contradiction, missing premise, or unresolved "
                    "question prevents a coherent submission, use report_theory_gap "
                    "after inspecting the relevant artifacts. State the blocker and "
                    "model-observed evidence directly; this ends the workspace as "
                    "blocked and never counts as theory or proof success. "
                    "Do not report a mathematical gap merely because a structured "
                    "index is unfinished. When substantive progress needs another "
                    "session, use checkpoint_theory_progress "
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
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: (
                root_authorization_fingerprint
            ),
            "model_tier": model_tier,
            "workspace_id": workspace_id,
            "question_id": question_id,
            "authoring_binding_id": authoring_binding_id,
            "workspace_operation": workspace_operation,
            "resumed_from_progress_checkpoint_id": str(
                (prior_workspace_checkpoint or {}).get("checkpoint_id", "")
                or ""
            ),
            "cumulative_tool_state_restored": bool(
                prior_workspace_checkpoint
            ),
            "write_transport": THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
            "parent_workspace_hash": parent_hash,
            "read_only_document_set_hash": stable_hash(
                [
                    (path, _text_sha256(content))
                    for path, content in sorted(context_documents.items())
                ]
            ),
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
                require_durable_state_binding=True,
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
            "removed_document_paths": list(
                removed_document_paths(current_documents)
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "model_artifact_writes": deepcopy(
                state["model_artifact_writes"]
            ),
            "model_document_writes": deepcopy(
                state["model_document_writes"]
            ),
            "workspace_read_refs": deepcopy(state["workspace_read_refs"]),
            "document_inspection_refs": deepcopy(
                state["document_inspection_refs"]
            ),
            "scratch_runs": state["scratch_runs"],
            "scratch_execution_refs": deepcopy(
                state["scratch_execution_refs"]
            ),
            "scratch_inspection_refs": deepcopy(
                state["scratch_inspection_refs"]
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
            session_dir=resolved_workspace_dir,
            session_id=workspace_id,
        )
    except ClientToolLoopError as exc:
        checkpoint = recovery_checkpoint()
        client_tool_session_ref = persist_client_tool_session(
            session_dir=resolved_workspace_dir,
            session_id=workspace_id,
            request=request,
            messages=exc.messages,
            observation_refs=exc.observation_refs,
            durable_state_identity=checkpoint["current_workspace_hash"],
        )
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
            history=workspace_evidence_history(exc.history),
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
        observation_refs=loop.observation_refs,
        durable_state_identity=recovery_checkpoint()["current_workspace_hash"],
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
        selected_source_run = packet.get("selected_source_run", 1)
        selected_source_manifest = (
            source_manifests[selected_source_run - 1]
            if (
                not isinstance(selected_source_run, bool)
                and isinstance(selected_source_run, int)
                and 1 <= selected_source_run <= len(source_manifests)
            )
            else {}
        )
        model_selected_terminal = bool(
            packet.get("source_execution_attempt_refs")
        )
        if not (
            packet.get("artifact_kind") == SOURCE_REPLICATION_CHECKPOINT_KIND
            and packet.get("question_id") == question_id
            and packet.get("workspace_id") == workspace_id
            and terminal.get("core_packet_hash") == packet_hash
            and isinstance(report, Mapping)
            and str(report.get("relative_path", "") or "")
            and isinstance(source_ref, Mapping)
            and bool(source_manifests)
            and (
                model_selected_terminal
                or (
                    len(source_manifests) == 1
                    and "selected_source_run" not in packet
                )
            )
            and bool(selected_source_manifest)
            and source_ref.get("artifact_id")
            == selected_source_manifest.get("artifact_id")
            and source_ref.get("manifest_hash")
            == selected_source_manifest.get("manifest_hash")
        ):
            terminal_errors.append(
                "terminal source replication checkpoint identity is invalid"
            )
        if terminal_errors:
            raise PacketValidationError(
                validation_label="source replication workspace checkpoint",
                attempts=loop.turns,
                errors=terminal_errors,
                history=workspace_evidence_history(loop.history),
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
            "removed_document_paths": list(
                terminal.get("removed_document_paths", []) or []
            ),
            "theory_workspace_manifest": deepcopy(
                dict(terminal.get("theory_workspace_manifest", {}) or {})
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "source_replication_runs": state["source_replication_runs"],
            "source_replication_manifests": deepcopy(source_manifests),
            "workspace_read_refs": deepcopy(state["workspace_read_refs"]),
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
            "history": workspace_evidence_history(loop.history),
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
                history=workspace_evidence_history(loop.history),
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
            "removed_document_paths": list(
                checkpoint.get("removed_document_paths", []) or []
            ),
            "theory_workspace_manifest": deepcopy(
                dict(checkpoint["theory_workspace_manifest"])
            ),
            "progress": progress,
            "reads": state["reads"],
            "submissions": state["submissions"],
            "workspace_read_refs": deepcopy(state["workspace_read_refs"]),
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "provider": loop.provider,
            "model": loop.model,
            "model_tier": model_tier,
            "provider_usage": dict(loop.provider_usage),
            "history": workspace_evidence_history(loop.history),
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
                history=workspace_evidence_history(loop.history),
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
            "removed_document_paths": list(
                removed_document_paths(state["documents"])
            ),
            "theory_workspace_manifest": document_manifest(
                state["documents"]
            ),
            "workspace_read_refs": deepcopy(state["workspace_read_refs"]),
            "document_inspection_refs": deepcopy(
                state["document_inspection_refs"]
            ),
            "reads": state["reads"],
            "submissions": state["submissions"],
            "scratch_runs": state["scratch_runs"],
            "scratch_inspection_refs": deepcopy(
                state["scratch_inspection_refs"]
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
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "provider": loop.provider,
            "model": loop.model,
            "model_tier": model_tier,
            "provider_usage": dict(loop.provider_usage),
            "history": workspace_evidence_history(loop.history),
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
            history=workspace_evidence_history(loop.history),
        )
    packet = deepcopy(dict(core_packet))
    packet_hash = stable_hash(packet)
    terminal_errors = [
        str(error)
        for error in validate_candidate(packet)
        if str(error).strip()
    ]
    raw_source_checkpoint = terminal.get("source_replication_checkpoint", {})
    integrated_source_checkpoint = (
        deepcopy(dict(raw_source_checkpoint))
        if isinstance(raw_source_checkpoint, Mapping)
        else {}
    )
    if integrated_source_replication_required and not integrated_source_checkpoint:
        terminal_errors.append("integrated source replication checkpoint is missing")
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
            history=workspace_evidence_history(loop.history),
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
        "resumed_from_progress_checkpoint_id": str(
            (prior_workspace_checkpoint or {}).get("checkpoint_id", "") or ""
        ),
        "cumulative_tool_state_restored": bool(prior_workspace_checkpoint),
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
        "removed_document_paths": list(
            terminal.get("removed_document_paths", []) or []
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
        "workspace_read_refs": deepcopy(state["workspace_read_refs"]),
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
        "scratch_inspection_refs": deepcopy(state["scratch_inspection_refs"]),
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
        "source_replication_checkpoint": integrated_source_checkpoint,
        "turns": loop.turns,
        "tool_calls": loop.tool_calls,
        "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
        "provider": loop.provider,
        "model": loop.model,
        "model_tier": model_tier,
        "provider_usage": dict(loop.provider_usage),
        "history": workspace_evidence_history(loop.history),
        "transcript_fingerprint": loop.transcript_fingerprint,
        **client_tool_session_evidence,
        "disposition": "THEORY_CHECKPOINT_COMMITTED",
        "checkpoint_committed": True,
        "checkpoint_readiness_rationale": str(
            terminal.get("readiness_rationale", "") or ""
        ),
        "model_owned_theory": True,
        "model_owned_source_report": bool(integrated_source_checkpoint),
        "runtime_edited_theory": False,
        "accepted": True,
        "proof_evidence_status": "THEORY_WORKSPACE_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
    }
    return TheoryWorkspaceResult(core_packet=packet, evidence=evidence)


def workspace_evidence_history(
    history: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    document_message = "[workspace document content omitted from persisted evidence; use the hash-bound document inspection refs]"
    source_message = "[research source text omitted from persisted evidence; raw execution also omitted from transcript; use snapshot/document/range or source-replication refs]"
    current_source_message = "[current model-owned source content omitted from persisted evidence; use the hash-bound source inspection refs]"
    redactions = {
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL: document_message,
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL: document_message,
        "read_current_scientific_source": current_source_message,
        "read_current_lean_source": current_source_message,
        **{name: source_message for name in (
            RESEARCH_SOURCE_LIST_TOOL, RESEARCH_SOURCE_SEARCH_TOOL,
            RESEARCH_SOURCE_READ_TOOL,
            RESEARCH_SOURCE_RUN_TOOL, RESEARCH_SOURCE_RESULT_READ_TOOL,
            RESEARCH_SOURCE_RESULT_INSPECT_TOOL,
            RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
            RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
        )},
        "read_theory_workspace": "[theory workspace content omitted from persisted evidence; use hash-bound artifact or document inspection refs]",
        THEORY_SCRATCHPAD_READ_TOOL: "[theory scratch source and result omitted from persisted evidence; use scratch inspection refs]",
    }
    return _redact_workspace_history(history, redactions)


def _redact_workspace_history(
    history: Sequence[Mapping[str, Any]], redactions: Mapping[str, str]
) -> list[dict[str, Any]]:
    persisted = [deepcopy(dict(row)) for row in history]
    for turn in persisted:
        tool_calls = turn.get("tool_calls", [])
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            replacement = redactions.get(str(tool_call.get("name", "") or ""))
            if replacement:
                tool_call["result_excerpt"] = replacement
    return persisted


def theory_document_client_tools() -> tuple[ClientToolDefinition, ...]:
    return (
        ClientToolDefinition(
            name=THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
            description=(
                "Search current hash-bound Markdown/LaTeX/BibTeX documents and "
                "read-only tool observations for a case-insensitive literal string. Returns "
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
                "document or read-only tool observation. Returns the full document "
                "hash and exact range hash for model-owned reasoning. Optional "
                "character_start/character_end select a zero-based, end-exclusive "
                "slice within that line range, including a single long line."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "line_start", "line_end"],
                "properties": {
                    "path": {"type": "string", "minLength": 1},
                    "line_start": {"type": "integer", "minimum": 1},
                    "line_end": {"type": "integer", "minimum": 1},
                    "character_start": {"type": "integer", "minimum": 0},
                    "character_end": {"type": "integer", "minimum": 1},
                },
            },
        ),
    )


def _theory_workspace_tools(
    *,
    scratchpad_enabled: bool = False,
    research_sources_enabled: bool = False,
    research_source_discovery_enabled: bool = False,
    research_repository_acquisition_enabled: bool = False,
    research_source_execution_enabled: bool = False,
    model_selected_source_execution: bool = False,
    source_replication_checkpoint_enabled: bool = False,
    integrated_source_replication_required: bool = False,
    document_authority_enabled: bool = False,
    writable_artifact_names: Sequence[str],
) -> tuple[ClientToolDefinition, ...]:
    source_commit_properties = {
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
                "Use [] when no gap remains; otherwise use only nonempty plain "
                "strings, never objects or empty placeholders."
            ),
            "items": {"type": "string", "minLength": 1},
        },
    }
    if model_selected_source_execution:
        source_commit_properties["selected_source_run"] = {
            "type": "integer",
            "minimum": 1,
            "description": (
                "Choose the completed source_run whose exact command and outputs "
                "this report advances as its checkpoint candidate. Every attempt "
                "remains in lineage."
            ),
        }
    integrated_commit_properties = (
        {
            "source_replication_" + field: deepcopy(schema)
            for field, schema in source_commit_properties.items()
        }
        if integrated_source_replication_required
        else {}
    )
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
        tools.extend(research_source_discovery_client_tools(
            repository_acquisition=research_repository_acquisition_enabled,
        ))
    if research_source_execution_enabled:
        tools.extend(
            (
                ClientToolDefinition(
                    name=RESEARCH_SOURCE_RUN_TOOL,
                    description=(
                        (
                            "Run one model-selected entrypoint from the exact frozen "
                            "project in the operator-owned, network-denied environment. "
                            "Choose the working directory, arguments, and expected result "
                            "paths; the interpreter, packages, source bytes, resource limits, "
                            "and isolation remain fixed. Raw feedback returns to this same "
                            "session so you may inspect and choose another command. "
                        )
                        if model_selected_source_execution
                        else (
                            "Run the exact operator-pinned published entrypoint once in its "
                            "hash-bound, network-denied environment. This tool accepts no "
                            "model-selected command or source. Raw stdout/stderr, plus any "
                            "operator-declared CSV, text, or binary result artifacts from "
                            "an isolated copy-on-write workspace, return to this same "
                            "session as hash-bound compact observations. "
                        )
                    ) + (
                        "Use read_research_source_result for exact result lines instead "
                        "of requesting embedded files."
                    ),
                    input_schema=(
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "reason",
                                "entrypoint_document_id",
                                "working_directory_relative",
                                "arguments",
                                "result_artifact_paths",
                            ],
                            "properties": {
                                "reason": {"type": "string", "minLength": 1},
                                "entrypoint_document_id": {
                                    "type": "string", "minLength": 1
                                },
                                "working_directory_relative": {
                                    "type": "string", "minLength": 1
                                },
                                "arguments": {
                                    "type": "array",
                                    "maxItems": 32,
                                    "items": {"type": "string"},
                                },
                                "result_artifact_paths": {
                                    "type": "array",
                                    "maxItems": MAX_SOURCE_RESULT_ARTIFACTS,
                                    "uniqueItems": True,
                                    "items": {"type": "string", "minLength": 1},
                                },
                            },
                        }
                        if model_selected_source_execution
                        else {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {},
                        }
                    ),
                ),
                ClientToolDefinition(
                    name=RESEARCH_SOURCE_RESULT_READ_TOOL,
                    description=(
                        "Read an exact inclusive line range from one UTF-8 execution "
                        "stream or declared result artifact returned by "
                        "run_research_source. The runtime rechecks its SHA-256 before "
                        "returning bytes."
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
                            **(
                                {
                                    "source_run": {
                                        "type": "integer",
                                        "minimum": 1,
                                    }
                                }
                                if model_selected_source_execution
                                else {}
                            ),
                        },
                    },
                ),
                ClientToolDefinition(
                    name=RESEARCH_SOURCE_RESULT_INSPECT_TOOL,
                    description=(
                        "Inspect one exact declared PDF, PNG, JPEG, GIF, or WebP "
                        "result from run_research_source. The runtime rechecks its "
                        "SHA-256 and returns provider-native visual content to this "
                        "same source-owning session without interpreting it."
                    ),
                    input_schema={
                        "type": "object", "additionalProperties": False,
                        "required": ["relative_path"],
                        "properties": {
                            "relative_path": {
                                "type": "string", "minLength": 1
                            },
                            **(
                                {
                                    "source_run": {
                                        "type": "integer", "minimum": 1
                                    }
                                }
                                if model_selected_source_execution
                                else {}
                            ),
                        },
                    },
                ),
            )
        )
    if scratchpad_enabled:
        tools.extend(
            (
                theory_scratchpad_client_tool(),
                ClientToolDefinition(
                    name=THEORY_SCRATCHPAD_READ_TOOL,
                    description=("Read one exact prior model-authored Theory scratch request, "
                                 "source, status, and available JSON result by scratch_run. "
                                 "The runtime rechecks sandbox location and hashes; this is an "
                                 "exploratory observation, not theory, confirmation, or proof."),
                    input_schema={
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["scratch_run"],
                        "properties": {"scratch_run": {"type": "integer", "minimum": 1}},
                    },
                ),
            )
        )
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
            )
            + (
                f" Current writable names: {', '.join(writable_artifact_names)}. "
                f"Claim kinds: {', '.join(THEORY_FILE_CLAIM_KINDS)}; claim statuses: "
                f"{', '.join(THEORY_FILE_CLAIM_STATUSES)}."
                if document_authority_enabled else ""
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
                                    "enum": list(writable_artifact_names),
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
                    "Apply one ordered atomic batch of exact model-authored replacements "
                    "to an existing Markdown/LaTeX/BibTeX document. The batch is bound "
                    "to the current SHA-256; runtime applies every edit or none and "
                    "returns the resulting document SHA-256 without authoring or "
                    "interpreting mathematics."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "path",
                        "expected_sha256",
                        "edits",
                    ],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "expected_sha256": {"type": "string", "minLength": 64, "maxLength": 64},
                        "edits": model_exact_text_edits_json_schema(),
                    },
                },
                terminal=False,
                strict=True,
            )
        )
        tools.append(
            ClientToolDefinition(
                name=THEORY_WORKSPACE_REMOVE_DOCUMENT_TOOL,
                description=(
                    "Remove one current model-owned Markdown, LaTeX, or BibTeX "
                    "document by exact path and SHA-256. Runtime verifies identity "
                    "and records deletion lineage but never chooses or interprets "
                    "the removed mathematics."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "expected_sha256"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "expected_sha256": {
                            "type": "string", "minLength": 64, "maxLength": 64
                        },
                    },
                },
                terminal=False,
                strict=True,
            )
        )
    if source_replication_checkpoint_enabled:
        tools.append(
            ClientToolDefinition(
                name=SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL,
                description=(
                    "Commit a model-authored Markdown source-replication report after "
                    "the immutable source run without fabricating theory, code, simulation, "
                    "or proof artifacts; the frozen outer graph may continue other workspaces."
                    + (
                        " Explicitly select which completed source run the report "
                        "advances; all attempts remain immutable evidence."
                        if model_selected_source_execution
                        else ""
                    )
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(source_commit_properties),
                    "properties": source_commit_properties,
                },
                terminal=True,
            )
        )
    if document_authority_enabled:
        tools.append(
            ClientToolDefinition(
                name=THEORY_WORKSPACE_PROGRESS_TOOL,
                description=(
                    "Checkpoint substantive model-authored workspace progress and "
                    "request another TheoryDeveloper continuation. Use this after a "
                    "workspace revision or a new exact source, scratch, or workspace "
                    "observation when more derivation is genuinely needed; unchanged "
                    "rereads do not qualify. The checkpoint is not accepted theory, "
                    "empirical evidence, or proof."
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
                + (
                    " The same commit must bind the required model-authored source "
                    "replication report and unresolved gaps."
                    if integrated_source_replication_required
                    else ""
                )
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["readiness_rationale", *integrated_commit_properties],
                "properties": {
                    "readiness_rationale": {"type": "string", "minLength": 1},
                    **integrated_commit_properties,
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
                f"{artifact_name!r}; allowed values are "
                + ", ".join(sorted(writable_artifact_shapes))
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
    """Apply one model-selected atomic edit batch without interpreting text."""

    if not isinstance(raw_edit, Mapping):
        raise ClientToolInputError("theory document edit must be an object")
    edit = dict(raw_edit)
    required = {"path", "expected_sha256", "edits"}
    edit_fields = set(edit)
    missing_fields = sorted(required - edit_fields)
    unexpected_fields = sorted(edit_fields - required)
    if missing_fields or unexpected_fields:
        raise ClientToolInputError(
            "edit_theory_document has invalid fields; "
            f"missing={missing_fields}, unexpected={unexpected_fields}, "
            f"required={sorted(required)}. expected_occurrences belongs inside an item in edits"
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
    revised, edit_records = apply_model_exact_text_edits(
        current,
        edits=edit["edits"],
        replacement_key="new_text",
    )
    if not revised.strip():
        raise ClientToolInputError("edit_theory_document cannot leave a document empty")
    candidate = dict(current_documents)
    candidate[path] = revised
    return candidate, {
        "operation": "atomic_exact_text_edits",
        "relative_path": path,
        "parent_sha256": current_sha256,
        "n_edits": len(edit_records),
        "edit_records": edit_records,
        "sha256": _text_sha256(revised),
        "byte_size": len(revised.encode("utf-8")),
    }


def _remove_theory_workspace_document(
    current_documents: Mapping[str, str],
    raw_remove: Any,
) -> tuple[dict[str, str], dict[str, Any]]:
    if not isinstance(raw_remove, Mapping):
        raise ClientToolInputError("remove_theory_document requires an object")
    remove = dict(raw_remove)
    if set(remove) != {"path", "expected_sha256"}:
        raise ClientToolInputError(
            "remove_theory_document requires exactly path and expected_sha256"
        )
    path = _normalized_theory_document_path(remove["path"])
    if path not in current_documents:
        raise ClientToolInputError(f"cannot remove unknown theory document {path!r}")
    current_sha256 = _text_sha256(current_documents[path])
    if remove["expected_sha256"] != current_sha256:
        raise ClientToolInputError(
            f"theory document {path!r} changed since it was read; expected "
            f"{remove['expected_sha256']!r}, current {current_sha256!r}"
        )
    candidate = dict(current_documents)
    del candidate[path]
    return candidate, {
        "operation": "remove_document",
        "relative_path": path,
        "parent_sha256": current_sha256,
        "removed": True,
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
    character_start: Any = None,
    character_end: Any = None,
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
    character_range = {}
    if character_start is not None or character_end is not None:
        start = 0 if character_start is None else character_start
        end = len(content) if character_end is None else character_end
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end)):
            raise ClientToolInputError("document character offsets must be integers")
        if start < 0 or end <= start or end > len(content):
            raise ClientToolInputError("document character range must be ordered and within the selected lines")
        character_range = {"character_start": start, "character_end": end}
        content = content[start:end]
    if len(content) > MAX_THEORY_DOCUMENT_OBSERVATION_CHARS:
        raise ClientToolInputError(
            "theory document line range exceeds one model observation; read a "
            "smaller line or character range"
        )
    document_sha256 = _text_sha256(normalized_documents[document_path])
    content_sha256 = _text_sha256(content)
    inspection_ref = {
        "tool": THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        "path": document_path,
        "document_sha256": document_sha256,
        "line_start": line_start,
        "line_end": line_end,
        **character_range,
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
            **character_range,
            "content": content,
            "content_sha256": content_sha256,
            "proof_evidence_status": (
                "THEORY_DOCUMENT_INSPECTION_NOT_PROOF_EVIDENCE"
            ),
        },
        inspection_ref,
    )


def execute_theory_document_client_tool(
    documents: Mapping[str, str],
    *,
    tool_name: str,
    tool_input: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute either shared read-only Theory document tool."""

    if tool_name == THEORY_WORKSPACE_READ_DOCUMENT_TOOL:
        required = {"path", "line_start", "line_end"}
        if not required.issubset(tool_input) or set(tool_input) - required - {"character_start", "character_end"}:
            raise ClientToolInputError(
                "read_theory_document requires path, line_start, and line_end; character_start and character_end are optional"
            )
        return read_theory_document_lines(documents, **dict(tool_input))
    if tool_name == THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL:
        if set(tool_input) - {"query", "document_paths", "max_results"}:
            raise ClientToolInputError(
                "search_theory_documents accepts query, document_paths, and max_results"
            )
        return search_theory_document_lines(documents, **dict(tool_input))
    raise ClientToolInputError("unsupported Theory document client tool")


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
    previous_documents: Mapping[str, str] | None = None,
) -> None:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, prior_content in (previous_documents or {}).items():
        if relative_path in documents:
            continue
        target = workspace_dir / relative_path
        if not target.is_file() or target.read_text(encoding="utf-8") != prior_content:
            raise ValueError(
                f"theory document changed before removal: {relative_path}"
            )
        target.unlink()
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
    if stable_hash(
        {
            "artifacts": dict(artifacts),
            "documents": documents,
        }
    ) != str(checkpoint.get("current_workspace_hash", "") or ""):
        raise ValueError("theory progress checkpoint workspace hash mismatch")
    changed_artifacts = checkpoint.get("changed_artifact_names", [])
    changed_documents = checkpoint.get("changed_document_paths", [])
    removed_documents = checkpoint.get("removed_document_paths", [])
    if not isinstance(changed_artifacts, list) or not all(
        isinstance(value, str) and value.strip()
        for value in changed_artifacts
    ) or len(set(changed_artifacts)) != len(changed_artifacts):
        raise ValueError("theory progress changed artifacts are invalid")
    if (
        not isinstance(changed_documents, list)
        or not all(isinstance(value, str) and value.strip() for value in changed_documents)
        or not isinstance(removed_documents, list)
        or not all(isinstance(value, str) and value.strip() for value in removed_documents)
    ):
        raise ValueError("theory progress changed documents are invalid")
    try:
        normalized_changed = [_normalized_theory_document_path(value) for value in changed_documents]
        normalized_removed = [_normalized_theory_document_path(value) for value in removed_documents]
    except ClientToolInputError as exc:
        raise ValueError("theory progress changed documents are invalid") from exc
    changed_document_set = set(changed_documents)
    removed_document_set = set(removed_documents)
    if (
        normalized_changed != changed_documents
        or normalized_removed != removed_documents
        or len(changed_document_set) != len(changed_documents)
        or len(removed_document_set) != len(removed_documents)
        or not changed_document_set.issubset(set(documents) | removed_document_set)
        or not removed_document_set.issubset(changed_document_set)
        or removed_document_set.intersection(documents)
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
    phase_artifacts = progress.get("phase_changed_artifact_names", [])
    phase_documents = progress.get("phase_changed_document_paths", [])
    phase_removed_documents = progress.get("phase_removed_document_paths", [])
    phase_observation_refs = progress.get("phase_observation_refs", [])
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or not all(isinstance(value, str) and value.strip() for value in evidence_refs)
        or not isinstance(phase_artifacts, list)
        or not all(
            isinstance(value, str) and value.strip() for value in phase_artifacts
        )
        or len(set(phase_artifacts)) != len(phase_artifacts)
        or not set(phase_artifacts).issubset(changed_artifacts)
        or not isinstance(phase_documents, list)
        or not all(isinstance(value, str) and value.strip() for value in phase_documents)
        or len(set(phase_documents)) != len(phase_documents)
        or not set(phase_documents).issubset(changed_documents)
        or not isinstance(phase_removed_documents, list)
        or not all(
            isinstance(value, str) and value.strip()
            for value in phase_removed_documents
        )
        or len(set(phase_removed_documents)) != len(phase_removed_documents)
        or not set(phase_removed_documents).issubset(removed_document_set)
        or not set(phase_removed_documents).issubset(phase_documents)
        or not isinstance(phase_observation_refs, list)
    ):
        raise ValueError("theory progress checkpoint evidence is incomplete")
    try:
        normalized_phase_documents = [
            _normalized_theory_document_path(value) for value in phase_documents
        ]
        normalized_phase_removed = [
            _normalized_theory_document_path(value)
            for value in phase_removed_documents
        ]
    except ClientToolInputError as exc:
        raise ValueError("theory progress checkpoint evidence is incomplete") from exc
    if (
        normalized_phase_documents != phase_documents
        or normalized_phase_removed != phase_removed_documents
    ):
        raise ValueError("theory progress checkpoint evidence is incomplete")
    restored_state = _theory_progress_workspace_state(
        checkpoint,
        workspace_id=str(checkpoint.get("workspace_id", "") or ""),
        question_id=str(checkpoint.get("question_id", "") or ""),
        authoring_binding_id=str(
            checkpoint.get("authoring_binding_id", "") or ""
        ),
        workspace_operation=str(
            checkpoint.get("workspace_operation", "") or ""
        ),
    )
    seen_observation_refs: set[tuple[str, int]] = set()
    for ref in phase_observation_refs:
        if not isinstance(ref, Mapping) or set(ref) != {
            "state_field",
            "row_index",
            "row_hash",
        }:
            raise ValueError("theory progress observation reference is invalid")
        state_field = ref.get("state_field")
        row_index = ref.get("row_index")
        row_hash = ref.get("row_hash")
        if (
            state_field not in _THEORY_PROGRESS_OBSERVATION_ROW_FIELDS
            or isinstance(row_index, bool)
            or not isinstance(row_index, int)
            or row_index < 1
            or row_index > len(restored_state[str(state_field)])
            or not isinstance(row_hash, str)
            or row_hash != stable_hash(
                restored_state[str(state_field)][row_index - 1]
            )
            or (str(state_field), row_index) in seen_observation_refs
        ):
            raise ValueError("theory progress observation reference is invalid")
        seen_observation_refs.add((str(state_field), row_index))
    if not (
        phase_artifacts
        or phase_documents
        or phase_removed_documents
        or phase_observation_refs
    ):
        raise ValueError("theory progress checkpoint records no phase progress")
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


def externalize_theory_document_rows(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Project exact Theory text into a hash-bound client-tool catalog."""

    if isinstance(rows, (str, bytes)):
        raise ValueError("theory document rows must be an array")
    documents: dict[str, str] = {}
    manifest: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("theory document row must be an object")
        path = _normalized_theory_document_path(row.get("path", ""))
        content = row.get("content")
        sha256 = str(row.get("sha256", "") or "")
        if (
            path in documents
            or not isinstance(content, str)
            or _text_sha256(content) != sha256
        ):
            raise ValueError("theory document identity mismatch")
        documents[path] = content
        manifest.append({
            "path": path,
            "sha256": sha256,
            "line_count": len(content.splitlines()),
            "byte_size": len(content.encode("utf-8")),
        })
    return manifest, documents


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
