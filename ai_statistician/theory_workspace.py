from __future__ import annotations

import hashlib
import json
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .scientific_sandbox import (
    SCIENTIFIC_WASM_SANDBOX_PROFILE,
    execute_scientific_sandbox,
    generated_code_draft_json_schema,
)
from .structured_output_retry import PacketValidationError


THEORY_WORKSPACE_CHECKPOINT_KIND = "TheoryDeveloperWorkspaceCheckpoint"
THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT = "model_owned_documents_and_handoff_v1"
THEORY_WORKSPACE_WRITE_TOOL = "write_theory_workspace"
THEORY_WORKSPACE_COMMIT_TOOL = "commit_theory_checkpoint"
THEORY_WORKSPACE_GAP_TOOL = "report_theory_gap"
THEORY_SCRATCHPAD_TOOL = "run_theory_scratchpad"
THEORY_WORKSPACE_CONTENT_AUTHORITY = "model_authored_markdown_latex_documents"
THEORY_WORKSPACE_HANDOFF_ROLE = "structured_cross_agent_index_and_abi"
THEORY_WORKSPACE_DOCUMENT_SUFFIXES = frozenset({".md", ".tex", ".bib"})
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


@dataclass(frozen=True)
class TheoryScratchpadConfig:
    """Resource boundary for model-authored exploratory Python/R calculations."""

    sandbox_dir: Path
    seed: int
    replicates: int
    timeout_s: int = 20
    max_runs: int = 2


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
    max_reads: int,
    max_submissions: int,
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
    workspace_dir: Path | None = None,
    require_document_authority: bool = False,
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
        (max_reads, "read"),
        (max_submissions, "submission"),
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
    parent = {
        str(name): deepcopy(value)
        for name, value in initial_artifacts.items()
        if str(name).strip()
    }
    if not parent:
        raise ValueError("theory workspace requires initial artifacts")
    parent_documents = _normalized_theory_documents(initial_documents or {})
    if require_document_authority and workspace_dir is None:
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
    writable_artifact_names = tuple(sorted(parent))
    parent_shapes = {
        name: _artifact_shape(value) for name, value in parent.items()
    }
    state: dict[str, Any] = {
        "artifacts": deepcopy(parent),
        "documents": deepcopy(parent_documents),
        "reads": 0,
        "submissions": 0,
        "last_validation_errors": [],
        "last_candidate": {},
        "model_artifact_writes": [],
        "model_document_writes": [],
        "scratch_runs": 0,
        "scratch_execution_refs": [],
    }
    tools = _theory_workspace_tools(
        artifact_names,
        parent_shapes,
        scratchpad_enabled=scratchpad is not None,
        document_authority_enabled=require_document_authority,
    )

    def changed_artifact_names(artifacts: Mapping[str, Any]) -> tuple[str, ...]:
        return tuple(
            name
            for name in writable_artifact_names
            if stable_hash(artifacts[name]) != stable_hash(parent[name])
        )

    def changed_document_paths(documents: Mapping[str, str]) -> tuple[str, ...]:
        return tuple(
            sorted(
                path
                for path in set(parent_documents).union(documents)
                if documents.get(path) != parent_documents.get(path)
            )
        )

    def document_manifest(documents: Mapping[str, str]) -> dict[str, Any]:
        return theory_workspace_document_manifest(
            documents,
            workspace_dir=resolved_workspace_dir,
        )

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
        remaining_submissions = max_submissions - state["submissions"]
        common_content = {
            "ok": True,
            "state_changed": state_changed,
            "candidate_hash": candidate_hash,
            "changed_artifact_names": list(changed),
            "changed_document_paths": list(changed_documents),
            "submissions": state["submissions"],
            "remaining_submissions": remaining_submissions,
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
        return ClientToolExecutionResult(
            content={
                **common_content,
                "write_accepted": True,
                "workspace_valid": True,
                "validation_errors": [],
                "checkpoint_committed": False,
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
            if state["reads"] >= max_reads:
                raise ClientToolInputError("theory workspace read budget is exhausted")
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
                    "remaining_reads": max_reads - state["reads"],
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

        if call.name == THEORY_WORKSPACE_WRITE_TOOL:
            if state["submissions"] >= max_submissions:
                raise ClientToolInputError(
                    "theory workspace submission budget is exhausted"
                )
            if set(tool_input) - {"writes", "document_writes"}:
                raise ClientToolInputError(
                    "write_theory_workspace accepts writes and document_writes"
                )
            raw_artifact_writes = tool_input.get("writes", [])
            raw_document_writes = tool_input.get("document_writes", [])
            if not raw_artifact_writes and not raw_document_writes:
                raise ClientToolInputError(
                    "write_theory_workspace requires at least one artifact or document write"
                )
            candidate_artifacts, write_records = (
                _replace_theory_workspace_artifacts(
                    state["artifacts"],
                    raw_artifact_writes,
                    writable_artifact_shapes=parent_shapes,
                    allow_empty=True,
                )
            )
            candidate_documents, document_write_records = (
                _replace_theory_workspace_documents(
                    state["documents"],
                    raw_document_writes,
                    allow_empty=True,
                )
            )
            return evaluate_model_write(
                candidate_artifacts,
                candidate_documents,
                artifact_writes=write_records,
                document_writes=document_write_records,
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

        if call.name == THEORY_SCRATCHPAD_TOOL:
            if scratchpad is None:
                raise ClientToolInputError("theory scratchpad is unavailable")
            if state["scratch_runs"] >= scratchpad.max_runs:
                raise ClientToolInputError(
                    "theory scratchpad run budget is exhausted"
                )
            run_index = state["scratch_runs"] + 1
            language = str(tool_input.get("language", "") or "")
            execution_profile = str(
                tool_input.get("execution_profile", "") or ""
            )
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
                    scratchpad.sandbox_dir
                    / stable_hash([workspace_id, authoring_binding_id])[:16]
                ),
                artifact_id=(
                    f"theory-scratch-{stable_hash(workspace_id)[:12]}-{run_index}"
                ),
                language=language,
                code=code,
                dependencies=[str(value) for value in dependencies],
                seed=int(scratchpad.seed),
                replicates=int(scratchpad.replicates),
                timeout_s=int(scratchpad.timeout_s),
                max_output_bytes=64 * 1024,
            )
            state["scratch_runs"] = run_index
            observation = {
                "scratch_run": run_index,
                "remaining_scratch_runs": scratchpad.max_runs - run_index,
                **execution.to_json(),
                "seed": int(scratchpad.seed),
                "replicates": int(scratchpad.replicates),
                "timeout_s": int(scratchpad.timeout_s),
                "runtime_edited_source": False,
                "runtime_edited_theory": False,
                "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
                "boundary": (
                    "This is a model-authored exploratory calculation returned to "
                    "the same TheoryDeveloper session. It may expose a counterexample "
                    "or numerical inconsistency, but it is not confirmatory simulation "
                    "evidence and not theorem proof evidence."
                ),
            }
            state["scratch_execution_refs"].append(
                {
                    "scratch_run": run_index,
                    "status": execution.status,
                    "language": execution.language,
                    "execution_attempted": execution.execution_attempted,
                    "returncode": execution.returncode,
                    "dependencies": list(execution.dependencies),
                    "errors": list(execution.errors),
                    "code_hash": execution.code_hash,
                    "request_hash": execution.request_hash,
                    "result_hash": execution.result_hash,
                    "metrics_hash": stable_hash(execution.metrics),
                    "code_path": execution.code_path,
                    "request_path": execution.request_path,
                    "result_path": execution.result_path,
                    "runtime_edited_source": False,
                    "runtime_edited_theory": False,
                    "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
                }
            )
            return ClientToolExecutionResult(
                content={"ok": True, **observation},
                state_changed=True,
                observation_key=(
                    "theory-scratchpad:"
                    + stable_hash(
                        [
                            workspace_id,
                            run_index,
                            execution.code_hash,
                            execution.request_hash,
                            execution.status,
                            execution.result_hash,
                            list(execution.errors),
                        ]
                    )
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
            ):
                raise ClientToolInputError(
                    "report_theory_gap requires a prior workspace read, write "
                    "observation, or scratch execution"
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
            "writable": name in parent,
        }
        for name in artifact_names
    }
    document_catalog = {
        row["relative_path"]: {
            "media_type": row["media_type"],
            "sha256": row["sha256"],
            "byte_size": row["byte_size"],
        }
        for row in document_manifest(state["documents"]).get("documents", [])
    }
    write_guidance = (
        "Use write_theory_workspace to author Markdown/LaTeX documents and the small "
        "structured cross-agent handoff in one atomic call when practical. The text "
        "documents are the authority for definitions, derivations, equations, "
        "counterexamples, and unresolved reasoning; JSON artifacts are only an index, "
        "typed estimator/simulation ABI, and optional formal handoff. Omitted files and "
        "artifacts remain byte-identical. The runtime stores your exact text and values "
        "without merging or inventing content. A structurally valid write is retained "
        "and returned to you, but it does not end the workspace or assert scientific "
        "readiness. "
    )
    scratch_guidance = (
        "Use run_theory_scratchpad when a small Python or R calculation, numerical "
        "check, or counterexample would resolve a mathematical uncertainty. Submit "
        "complete source defining run_sandbox(seed, replicates); the isolated runtime "
        "executes those exact bytes and returns the raw observation. Interpret the "
        "observation yourself before editing theory. Scratch output is exploratory, "
        "not confirmatory simulation and not proof. Never promote finite scratch "
        "output into a universal mathematical premise; supply a mathematical "
        "argument or narrow the claim instead. "
        if scratchpad is not None
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
                            "content_authority": (
                                THEORY_WORKSPACE_CONTENT_AUTHORITY
                                if require_document_authority
                                else "legacy_structured_artifacts"
                            ),
                        }
                    )
                    + "\n\nRead the artifacts needed for mathematical judgment. "
                    + scratch_guidance
                    + write_guidance
                    + "When the current workspace is scientifically ready for "
                    "independent review, call commit_theory_checkpoint and explain "
                    "your own readiness judgment. There is no required number of "
                    "reads, rewrites, scratch runs, or counterexample attempts: choose "
                    "only actions that improve the mathematics. Structural validation "
                    "checks the handoff contract, not whether the theory is correct. "
                    + "If a mathematical contradiction, missing premise, or unresolved "
                    "question prevents a coherent submission, use report_theory_gap "
                    "after inspecting the relevant artifacts. State the blocker and "
                    "model-observed evidence directly; this ends the workspace as "
                    "blocked and never counts as theory or proof success. "
                    + "Each structurally valid model write is retained even when the "
                    "combined workspace still fails validation, so a validator "
                    "observation is not a rollback and later calls should contain only "
                    "artifacts that still need to be added or revised. "
                    "The runtime returns "
                    "validator observations to this same model context."
                ),
            },
        ),
        tools=tools,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=True,
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
            "reads": state["reads"],
            "submissions": state["submissions"],
            "model_artifact_writes": deepcopy(
                state["model_artifact_writes"]
            ),
            "model_document_writes": deepcopy(
                state["model_document_writes"]
            ),
            "scratch_runs": state["scratch_runs"],
            "scratch_execution_refs": deepcopy(
                state["scratch_execution_refs"]
            ),
            "last_validation_errors": list(state["last_validation_errors"]),
            "model_owned_theory": True,
            "runtime_edited_theory": False,
            "proof_evidence_status": (
                "THEORY_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
            "kernel_verified": False,
        }

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max(
                max_turns,
                max_reads
                + max_submissions
                + (scratchpad.max_runs if scratchpad is not None else 0),
            ),
            max_no_progress_turns=max_no_progress_turns,
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label="LLM TheoryDeveloper artifact workspace",
            attempts=exc.turns,
            errors=list(
                dict.fromkeys(
                    [exc.reason, *state["last_validation_errors"]]
                )
            ),
            history=[deepcopy(dict(row)) for row in exc.history],
            last_invalid_packet=(
                deepcopy(dict(state["last_candidate"]))
                if state["last_candidate"]
                else None
            ),
            recovery_checkpoint=recovery_checkpoint(),
        ) from exc

    terminal = dict(loop.terminal_payload)
    if terminal.get("disposition") == "THEORY_GAP":
        theory_gap = terminal.get("theory_gap", {})
        if not isinstance(theory_gap, Mapping) or not str(
            theory_gap.get("summary", "") or ""
        ).strip():
            raise PacketValidationError(
                validation_label="LLM TheoryDeveloper artifact workspace",
                attempts=loop.turns,
                errors=["terminal theory-gap payload is invalid"],
                history=[deepcopy(dict(row)) for row in loop.history],
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
            "reads": state["reads"],
            "submissions": state["submissions"],
            "scratch_runs": state["scratch_runs"],
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "provider": loop.provider,
            "model": loop.model,
            "model_tier": model_tier,
            "provider_usage": dict(loop.provider_usage),
            "history": [deepcopy(dict(row)) for row in loop.history],
            "transcript_fingerprint": loop.transcript_fingerprint,
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
            history=[deepcopy(dict(row)) for row in loop.history],
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
            history=[deepcopy(dict(row)) for row in loop.history],
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
        "schema_version": 1,
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
        "theory_content_authority": (
            THEORY_WORKSPACE_CONTENT_AUTHORITY
            if require_document_authority
            else "legacy_structured_artifacts"
        ),
        "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
        "scratchpad_enabled": scratchpad is not None,
        "scratch_runs": state["scratch_runs"],
        "scratch_execution_refs": deepcopy(state["scratch_execution_refs"]),
        "turns": loop.turns,
        "tool_calls": loop.tool_calls,
        "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
        "provider": loop.provider,
        "model": loop.model,
        "model_tier": model_tier,
        "provider_usage": dict(loop.provider_usage),
        "history": [deepcopy(dict(row)) for row in loop.history],
        "transcript_fingerprint": loop.transcript_fingerprint,
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


def _theory_workspace_tools(
    artifact_names: Sequence[str],
    writable_artifact_shapes: Mapping[str, str],
    *,
    scratchpad_enabled: bool = False,
    document_authority_enabled: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    name_schema = {"type": "string", "enum": list(artifact_names)}
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
                    "items": name_schema,
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
    if scratchpad_enabled:
        scratch_schema = generated_code_draft_json_schema(
            artifact_properties={},
            artifact_required=(),
            code_max_length=100_000,
        )
        scratch_schema["properties"]["execution_profile"]["enum"] = [
            SCIENTIFIC_WASM_SANDBOX_PROFILE
        ]
        tools.append(
            ClientToolDefinition(
                name=THEORY_SCRATCHPAD_TOOL,
                description=(
                    "Run one complete model-authored exploratory Python or R "
                    "calculation in the isolated scientific sandbox. Raw execution "
                    "results return to this session and never edit theory automatically."
                ),
                input_schema=scratch_schema,
            )
        )
    tools.append(
        ClientToolDefinition(
            name=THEORY_WORKSPACE_WRITE_TOOL,
            description=(
                "Atomically write model-authored Markdown/LaTeX mathematics and the "
                "structured cross-agent handoff. Text documents hold substantive "
                "reasoning; JSON values are only an index and executable ABI. Omitted "
                "material is retained exactly, and runtime never merges or infers "
                "content. A valid write remains available for further model-directed "
                "work and does not itself commit the checkpoint."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "writes": {
                        "type": "array",
                        **({} if document_authority_enabled else {"minItems": 1}),
                        "maxItems": len(writable_artifact_shapes),
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["artifact_name", "value"],
                            "properties": {
                                "artifact_name": {
                                    "type": "string",
                                    "enum": sorted(writable_artifact_shapes),
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
                    **(
                        {
                            "document_writes": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["path", "content"],
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "minLength": 1,
                                        },
                                        "content": {
                                            "type": "string",
                                            "minLength": 1,
                                        },
                                    },
                                },
                            }
                        }
                        if document_authority_enabled
                        else {}
                    ),
                },
                **({} if document_authority_enabled else {"required": ["writes"]}),
            },
            terminal=False,
        )
    )
    tools.append(
        ClientToolDefinition(
            name=THEORY_WORKSPACE_COMMIT_TOOL,
            description=(
                "Commit the current structurally valid, model-authored workspace as "
                "ready for independent scientific review. This records your stopping "
                "decision; it does not make the theory correct and is not proof evidence."
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


def _replace_theory_workspace_documents(
    current_documents: Mapping[str, str],
    raw_writes: Any,
    *,
    allow_empty: bool = False,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    if (
        not isinstance(raw_writes, Sequence)
        or isinstance(raw_writes, (str, bytes))
        or (not raw_writes and not allow_empty)
    ):
        raise ClientToolInputError(
            "write_theory_workspace requires document_writes to be an array"
        )
    candidate = dict(current_documents)
    records: list[dict[str, Any]] = []
    observed_paths: set[str] = set()
    for index, raw_write in enumerate(raw_writes):
        if not isinstance(raw_write, Mapping):
            raise ClientToolInputError(
                f"theory document write {index} must be an object"
            )
        write = dict(raw_write)
        if set(write) != {"path", "content"}:
            raise ClientToolInputError(
                f"theory document write {index} requires exactly path and content"
            )
        path = _normalized_theory_document_path(write["path"])
        if path in observed_paths:
            raise ClientToolInputError(
                f"theory document write {index} repeats {path!r}"
            )
        observed_paths.add(path)
        content = write["content"]
        if not isinstance(content, str) or not content.strip():
            raise ClientToolInputError(
                f"theory document write {index} content must be nonempty text"
            )
        candidate[path] = content
        records.append(
            {
                "relative_path": path,
                "sha256": _text_sha256(content),
                "byte_size": len(content.encode("utf-8")),
            }
        )
    return candidate, records


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
