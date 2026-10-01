from __future__ import annotations

from .native_project import NATIVE_PROJECT_TOOL, configured_native_project

import hashlib
import json
import tempfile
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    mark_workspace_continuation,
    runtime_artifact_reference,
)
from .client_tool_loop import (
    CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY,
    CLIENT_TOOL_RECENT_HISTORY_ROUNDS,
    CLIENT_TOOL_RESULT_MAX_CHARS,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    ClientToolLoopResult,
    PreparedClientToolWorkspace,
    apply_model_exact_text_edits,
    client_tool_authorization_fingerprint,
    externalize_client_tool_text_documents,
    model_exact_text_edit_json_schema,
    persist_client_tool_session,
    read_hash_bound_utf8_file,
    resume_client_tool_session_from_checkpoint,
    run_client_tool_workspace,
    workspace_history_tool,
)
from .fingerprint import stable_hash
from .model_backend import (
    ClientToolDefinition,
    ClientToolTurnRequest,
    resolve_generator_model,
)
from .research_schema import (
    OpenResearchQuestion,
    research_question_payload,
    research_workspace_authorization_fingerprint,
)
from .research_source_library import (
    RESEARCH_SOURCE_LIST_TOOL,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceSnapshot,
    execute_research_source_client_tool,
    research_source_client_tools,
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
    PYTHON_SCIENTIFIC_DEPENDENCIES,
    R_SCIENTIFIC_DEPENDENCIES,
    SCIENTIFIC_SANDBOX_LANGUAGES,
    SCIENTIFIC_SANDBOX_PROFILES,
    execute_scientific_sandbox,
    generated_code_execution_contract_errors,
    normalized_generated_code_language,
    normalized_generated_code_profile,
    normalized_scientific_dependencies,
)
from .scientific_project import (
    MAX_SCIENTIFIC_PROJECT_FILES,
    normalized_scientific_project_files,
    scientific_main_path,
    scientific_project_files_json_schema,
    scientific_project_hash,
)
from .packet_validation import PacketValidationError
from . import theory_workspace as theory_documents


ScientificCodeCheck = Callable[[Mapping[str, Any]], Mapping[str, Any]]
ScientificCandidateExecutor = Callable[[Mapping[str, Any]], tuple[dict[str, Any], Any | Sequence[Any]]]

SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS = "native_client_tools"
SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET = "structured_packet"
SCIENTIFIC_SOURCE_SUBMISSION_TOOL = "submit_scientific_source"
SCIENTIFIC_SOURCE_READ_TOOL = "read_current_scientific_source"
SCIENTIFIC_SOURCE_EDIT_TOOL = "edit_current_scientific_source"
SCIENTIFIC_SOURCE_COMMIT_TOOL = "commit_scientific_source"
SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL = "run_current_scientific_source"
SCIENTIFIC_PROJECT_FILE_WRITE_TOOL = "write_scientific_project_file"
SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL = "remove_scientific_project_file"
SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL = "import_research_source_files"
SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL = "report_bound_dependency_failure"
SCIENTIFIC_SOURCE_REVISE_CURRENT = "revise_current_source"
SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER = "return_to_bound_dependency_owner"
SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_KIND = "ScientificCodeWorkspaceCheckpoint"
SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY = "scientific_consumer_revision"
_SCIENTIFIC_PACKAGES = PYTHON_SCIENTIFIC_DEPENDENCIES + R_SCIENTIFIC_DEPENDENCIES
_OUTCOME_DERIVED_SHAPE_FIELDS = frozenset(
    {"length", "dimensions", "field_count", "truncated_field_count"}
)


def _scientific_project_manifest(draft: Mapping[str, Any]) -> list[dict[str, Any]]:
    language = normalized_generated_code_language(draft.get("language"))
    main_code = str(draft.get("code", "") or "")
    rows = [
        {
            "path": scientific_main_path(language),
            "content_hash": stable_hash(main_code),
            "line_count": len(main_code.splitlines()),
            "character_count": len(main_code),
            "entrypoint": True,
        }
    ]
    for project_file in normalized_scientific_project_files(
        draft.get("project_files", []),
        language=language,
    ):
        rows.append(
            {
                "path": project_file.path,
                "content_hash": project_file.content_sha256,
                "line_count": len(project_file.content.splitlines()),
                "character_count": len(project_file.content),
                "entrypoint": False,
            }
        )
    return rows


@dataclass(frozen=True)
class ScientificCodeWorkspaceResult:
    code_draft: Mapping[str, Any]
    check_result: Mapping[str, Any]
    evidence: Mapping[str, Any]


class ScientificSourceWorkspaceUnavailableError(RuntimeError):
    """Fresh scientific source cannot be authored through native client tools."""


class ScientificCodeWorkspaceAgent:
    """Shared retained source session for Python/R workspace owners."""

    scientific_workspace_system_prompt = ""
    scientific_workspace_instruction = ""
    scientific_workspace_subsystem = ""
    scientific_workspace_agent = ""
    scientific_workspace_allow_dependency_handoff = False

    def iterate_code_with_tools(
        self,
        *,
        question: OpenResearchQuestion,
        artifact_id: str,
        code_draft: Mapping[str, Any] | None,
        initial_observation: Mapping[str, Any],
        workspace_context: Mapping[str, Any],
        check_candidate: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        workspace_operation: str = "targeted_revision",
        allow_current_source_run: bool = False,
        recovery_checkpoint: Mapping[str, Any] | None = None,
        session_dir: Path | None = None,
        research_sources: ResearchSourceSnapshot | None = None,
        research_source_discovery: ResearchSourceDiscovery | None = None,
    ) -> ScientificCodeWorkspaceResult:
        return run_client_tool_workspace(
            backend=self.provider,
            workspace=self.prepare_code_workspace(
                question=question, artifact_id=artifact_id, code_draft=code_draft,
                initial_observation=initial_observation, workspace_context=workspace_context,
                check_candidate=check_candidate, workspace_operation=workspace_operation,
                allow_current_source_run=allow_current_source_run,
                recovery_checkpoint=recovery_checkpoint, session_dir=session_dir,
                research_sources=research_sources, research_source_discovery=research_source_discovery,
            ),
        )

    def prepare_code_workspace(
        self,
        *,
        question: OpenResearchQuestion,
        artifact_id: str,
        code_draft: Mapping[str, Any] | None,
        initial_observation: Mapping[str, Any],
        workspace_context: Mapping[str, Any],
        check_candidate: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        workspace_operation: str = "targeted_revision",
        allow_current_source_run: bool = False,
        recovery_checkpoint: Mapping[str, Any] | None = None,
        session_dir: Path | None = None,
        research_sources: ResearchSourceSnapshot | None = None,
        research_source_discovery: ResearchSourceDiscovery | None = None,
    ) -> PreparedClientToolWorkspace[ScientificCodeWorkspaceResult]:
        """Expose the production source binding without its role model driver."""

        config = self.config
        if not config.use_client_tool_code_workspace:
            raise ValueError(
                f"{self.scientific_workspace_subsystem} client-tool code workspace is disabled"
            )
        model = resolve_generator_model(
            provider_name=config.provider_name,
            requested_model=config.model,
            model_tier=config.model_tier,
        )
        prompt_context, context_documents = externalize_scientific_workspace_documents(
            workspace_context
        )
        return prepare_scientific_code_workspace(
            system_prompt=self.scientific_workspace_system_prompt,
            user_prompt=(
                self.scientific_workspace_instruction
                + " The runtime executes source unchanged and supplies no correction rule.\n"
                + json.dumps(
                    {
                        "question": research_question_payload(question),
                        "workspace_context": prompt_context,
                    },
                    separators=(",", ":"),
                    default=str,
                )
            ),
            model=model,
            model_tier=config.model_tier,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_turns=max(1, config.client_tool_code_max_turns),
            max_no_progress_turns=max(1, config.client_tool_code_max_no_progress_turns),
            artifact_id=artifact_id,
            initial_code_draft=code_draft,
            initial_check_result=initial_observation,
            check_candidate=check_candidate,
            workspace_operation=workspace_operation,
            allow_current_source_run=allow_current_source_run,
            allow_dependency_handoff=self.scientific_workspace_allow_dependency_handoff,
            recovery_checkpoint=recovery_checkpoint,
            session_dir=session_dir,
            context_documents=context_documents,
            research_sources=research_sources,
            research_source_discovery=research_source_discovery,
            request_metadata={
                CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: research_workspace_authorization_fingerprint(
                    question, workspace_context, {
                        "subsystem": self.scientific_workspace_subsystem, "artifact_id": artifact_id,
                        "research_source_snapshot": research_sources.descriptor() if research_sources else {},
                        "public_research_source_discovery": research_source_discovery.descriptor() if research_source_discovery else {},
                    }),
                "subsystem": self.scientific_workspace_subsystem,
                "agent": self.scientific_workspace_agent,
                "phase": "scientific_code_workspace",
            },
        )


def externalize_scientific_workspace_documents(
    workspace_context: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Move exact upstream documents out of the prompt and into read tools."""
    projected = deepcopy(dict(workspace_context))
    theory = projected.get("theory_context", {})
    documents: dict[str, str] = {}
    if isinstance(theory, Mapping):
        theory = deepcopy(dict(theory))
        rows = theory.get("authoritative_theory_documents", [])
        if rows and (not isinstance(rows, Sequence) or isinstance(rows, (str, bytes))):
            raise ValueError("scientific workspace theory documents are malformed")
        iterable = rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else ()
        manifest, documents = theory_documents.externalize_theory_document_rows(iterable)
        if documents:
            theory["authoritative_theory_documents"] = manifest
            theory["document_content_transport"] = "hash_bound_read_only_client_tools"
            projected["theory_context"] = theory
    replication = projected.get("source_replication_context", {})
    if isinstance(replication, Mapping) and replication:
        replication = deepcopy(dict(replication)); report = replication.get("report_document", {})
        if isinstance(report, Mapping) and report.get("content_loaded") is True:
            row = {"path": report.get("relative_path", ""), "sha256": report.get("sha256", ""), "content": report.get("content")}
            manifest, report_documents = theory_documents.externalize_theory_document_rows([row])
            if set(documents).intersection(report_documents):
                raise ValueError("scientific workspace document paths collide")
            documents.update(report_documents); replication["report_document"] = manifest[0]
            replication["document_content_transport"] = "hash_bound_read_only_client_tools"
        replication.pop("author_source_observations", None)
        execution = replication.get("source_execution", {})
        if isinstance(execution, Mapping):
            replication["source_execution"] = {key: deepcopy(value) for key, value in execution.items() if key not in {"raw_stdout", "raw_stderr"}}
        projected["source_replication_context"] = replication
    return projected, documents


def load_scientific_code_workspace_checkpoint(
    checkpoint: Mapping[str, Any],
    *,
    artifact_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify exact model-owned source and its last execution observation."""

    if checkpoint.get("artifact_kind") != SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_KIND:
        raise ValueError("scientific code workspace checkpoint kind mismatch")
    if str(checkpoint.get("artifact_id", "") or "") != str(artifact_id):
        raise ValueError("scientific code workspace checkpoint artifact mismatch")
    if (
        checkpoint.get("resumable") is not True
        or checkpoint.get("accepted") is not False
        or checkpoint.get("model_owned_source") is not True
        or checkpoint.get("runtime_edited_source") is not False
    ):
        raise ValueError("scientific code workspace checkpoint boundary mismatch")
    checkpoint_id = str(checkpoint.get("checkpoint_id", "") or "").strip()
    checkpoint_body = deepcopy(dict(checkpoint))
    checkpoint_body.pop("checkpoint_id", None)
    expected_checkpoint_id = "scientific_code_workspace_checkpoint:" + stable_hash(
        checkpoint_body
    )[:20]
    if not checkpoint_id or checkpoint_id != expected_checkpoint_id:
        raise ValueError("scientific code workspace checkpoint identity mismatch")

    draft = _complete_code_draft(checkpoint.get("current_code_draft", {}))
    draft_hash = stable_hash(draft)
    if draft_hash != str(
        checkpoint.get("current_code_draft_hash", "") or ""
    ):
        raise ValueError("scientific code workspace checkpoint source hash mismatch")
    observed_hashes = checkpoint.get("observed_code_draft_hashes", [])
    if not isinstance(observed_hashes, list) or any(
        not str(value or "").strip() for value in observed_hashes
    ):
        raise ValueError("scientific code workspace observed source hashes are invalid")
    current_source_executed = checkpoint.get("current_source_executed", True)
    if type(current_source_executed) is not bool:
        raise ValueError("scientific code workspace execution state is malformed")
    if current_source_executed != (draft_hash in observed_hashes):
        raise ValueError("scientific code workspace execution state is inconsistent")
    last_check = checkpoint.get("last_check", {})
    if not isinstance(last_check, Mapping):
        raise ValueError("scientific code workspace last check is malformed")
    last_check = deepcopy(dict(last_check))
    if current_source_executed and str(
        last_check.get("code_draft_hash", "") or ""
    ) != draft_hash:
        raise ValueError("scientific code workspace last check source hash mismatch")
    if stable_hash(last_check) != str(
        checkpoint.get("last_check_hash", "") or ""
    ):
        raise ValueError("scientific code workspace last check identity mismatch")
    source_updates = int(checkpoint.get("source_updates", 0) or 0)
    checks = int(checkpoint.get("checks", 0) or 0)
    segment_start_source_updates = int(
        checkpoint.get("segment_start_source_updates", 0) or 0
    )
    segment_start_checks = int(checkpoint.get("segment_start_checks", 0) or 0)
    if (
        source_updates < segment_start_source_updates
        or checks < segment_start_checks
        or (
            source_updates == segment_start_source_updates
            and checks == segment_start_checks
        )
    ):
        raise ValueError("scientific code workspace checkpoint made no progress")
    return draft, last_check


def scientific_workspace_resume_plan(
    *,
    manifest: Mapping[str, Any],
    proposal_packet: Mapping[str, Any],
    question_id: str,
    theory_packet_id: str,
    expected_manifest_kind: str,
    proposal_id_field: str,
    row_id_field: str,
    expected_source_ids: Sequence[str],
    source_accepted: Callable[[Mapping[str, Any]], bool],
) -> tuple[dict[str, Any], list[str]]:
    """Validate reusable rows and resumable checkpoints in one source manifest."""

    errors: list[str] = []
    question = manifest.get("question", {})
    if (
        manifest.get("artifact_kind") != expected_manifest_kind
        or not str(manifest.get("manifest_id", "") or "").strip()
        or str(manifest.get("theory_packet_id", "") or "")
        != theory_packet_id
        or not isinstance(question, Mapping)
        or str(question.get("id", "") or "") != question_id
    ):
        errors.append("scientific workspace progress manifest lineage is invalid")
    proposal_id = str(manifest.get(proposal_id_field, "") or "").strip()
    source_workspace_owns_planning = bool(
        manifest.get("scientific_source_workspace_owns_planning") is True
    )
    source_workspace_intent_id = str(
        manifest.get("scientific_source_workspace_intent_id", "") or ""
    ).strip()
    if source_workspace_owns_planning:
        if not source_workspace_intent_id:
            errors.append("scientific source workspace intent identity is missing")
        if proposal_id and str(proposal_packet.get("packet_id", "") or "") != proposal_id:
            errors.append("scientific workspace proposal packet is missing or stale")
    elif (
        not proposal_id
        or str(proposal_packet.get("packet_id", "") or "") != proposal_id
    ):
        errors.append("scientific workspace proposal packet is missing or stale")
    row_container = (
        "prototypes"
        if expected_manifest_kind == "RuntimeAlgorithmSandboxManifest"
        else "generated_simulation_sandbox_prototypes"
    )
    rows = {
        str(row.get(row_id_field, "") or "").strip(): deepcopy(dict(row))
        for row in manifest.get(row_container, []) or []
        if isinstance(row, Mapping)
        and str(row.get(row_id_field, "") or "").strip()
    }
    expected_ids = {
        str(value or "").strip()
        for value in expected_source_ids
        if str(value or "").strip()
    } or set(rows)
    checkpoints: dict[str, dict[str, Any]] = {}
    reusable_rows: dict[str, dict[str, Any]] = {}
    for source_id in expected_ids:
        row = rows.get(source_id, {})
        if not row:
            errors.append(f"{source_id}: scientific source row is missing")
            continue
        if source_accepted(row):
            reusable_rows[source_id] = row
            continue
        failure = row.get("scientific_code_workspace_failure", {})
        checkpoint = (
            deepcopy(dict(failure.get("recovery_checkpoint", {})))
            if isinstance(failure, Mapping)
            and isinstance(failure.get("recovery_checkpoint", {}), Mapping)
            else {}
        )
        try:
            load_scientific_code_workspace_checkpoint(
                checkpoint,
                artifact_id=f"{question_id}:{source_id}",
            )
        except ValueError as exc:
            errors.append(f"{source_id}: {exc}")
            continue
        checkpoints[source_id] = checkpoint
    if set(rows) - expected_ids:
        errors.append("scientific workspace manifest contains unknown source ids")
    if expected_ids != set(reusable_rows) | set(checkpoints):
        errors.append(
            "accepted parent sources and resumable checkpoints do not cover targets"
        )
    if errors:
        return {}, sorted(set(errors))
    return {
        "parent_manifest": deepcopy(dict(manifest)),
        "proposal_packet": deepcopy(dict(proposal_packet)),
        "source_workspace_owns_planning": source_workspace_owns_planning,
        "source_workspace_intent_id": source_workspace_intent_id,
        "rows": rows,
        "reusable_rows": reusable_rows,
        "checkpoints": checkpoints,
    }, []


def runtime_scientific_workspace_resume_plan(
    task: AgentTask,
    blackboard: BlackboardState,
    *,
    question_id: str,
    theory_packet_id: str,
    expected_manifest_kind: str,
    proposal_id_field: str,
    row_id_field: str,
    expected_source_ids: Sequence[str],
    source_accepted: Callable[[Mapping[str, Any]], bool],
) -> tuple[dict[str, Any], list[str]]:
    """Resolve one blackboard manifest ref, then validate its source state."""

    raw_manifest = task.inputs.get(
        "scientific_code_workspace_progress_manifest", {}
    )
    if not raw_manifest:
        return {}, []
    if not isinstance(raw_manifest, Mapping):
        return {}, ["scientific workspace progress manifest must be an object"]
    manifest = deepcopy(dict(raw_manifest))
    manifest_id = str(manifest.get("manifest_id", "") or "").strip()
    authoritative = blackboard.artifacts.get(manifest_id, {})
    if (
        not isinstance(authoritative, Mapping)
        or stable_hash(dict(authoritative)) != stable_hash(manifest)
    ):
        return {}, ["scientific workspace progress manifest is missing or stale"]
    proposal_id = str(manifest.get(proposal_id_field, "") or "").strip()
    if (
        manifest.get("scientific_source_workspace_owns_planning") is True
        and not proposal_id
    ):
        proposal = {}
    else:
        proposal = blackboard.artifacts.get(proposal_id, {})
        if not isinstance(proposal, Mapping):
            proposal = {}
    return scientific_workspace_resume_plan(
        manifest=manifest,
        proposal_packet=proposal,
        question_id=question_id,
        theory_packet_id=theory_packet_id,
        expected_manifest_kind=expected_manifest_kind,
        proposal_id_field=proposal_id_field,
        row_id_field=row_id_field,
        expected_source_ids=expected_source_ids,
        source_accepted=source_accepted,
    )


def scientific_workspace_progress_continuation(
    *,
    task: AgentTask,
    question_id: str,
    manifest: Mapping[str, Any],
    proposal_packet: Mapping[str, Any] | None,
    rows: Sequence[Mapping[str, Any]],
    row_id_field: str,
    incomplete_source_ids: Sequence[str],
) -> tuple[
    AgentTask | None,
    EvidenceLedgerEntry | None,
    EnvironmentObservation | None,
    list[str],
]:
    """Spend an outer iteration only after new executed model-source progress."""

    incomplete_ids = {
        str(value or "").strip()
        for value in incomplete_source_ids
        if str(value or "").strip()
    }
    if not incomplete_ids:
        return None, None, None, []
    manifest_id = str(manifest.get("manifest_id", "") or "").strip()
    proposal_id = str((proposal_packet or {}).get("packet_id", "") or "").strip()
    source_workspace_intent_id = str(
        manifest.get("scientific_source_workspace_intent_id", "") or ""
    ).strip()
    if not manifest_id or not (proposal_id or source_workspace_intent_id):
        return None, None, None, [
            "scientific progress requires bound source intent and manifest identities"
        ]
    prior_manifest = task.inputs.get(
        "scientific_code_workspace_progress_manifest", {}
    )
    row_container = (
        "prototypes"
        if task.owner_subsystem == "AlgorithmEngineer"
        else "generated_simulation_sandbox_prototypes"
    )
    prior_rows = {
        str(row.get(row_id_field, "") or "").strip(): row
        for row in (
            prior_manifest.get(row_container, [])
            if isinstance(prior_manifest, Mapping)
            else []
        )
        or []
        if isinstance(row, Mapping)
        and str(row.get(row_id_field, "") or "").strip()
    }
    rows_by_id = {
        str(row.get(row_id_field, "") or "").strip(): row
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get(row_id_field, "") or "").strip()
    }
    checkpoints: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for source_id in incomplete_ids:
        failure = rows_by_id.get(source_id, {}).get(
            "scientific_code_workspace_failure", {}
        )
        checkpoint = (
            deepcopy(dict(failure.get("recovery_checkpoint", {})))
            if isinstance(failure, Mapping)
            and isinstance(failure.get("recovery_checkpoint", {}), Mapping)
            else {}
        )
        try:
            load_scientific_code_workspace_checkpoint(
                checkpoint,
                artifact_id=f"{question_id}:{source_id}",
            )
        except ValueError as exc:
            errors.append(f"{source_id}: {exc}")
            continue
        prior_failure = prior_rows.get(source_id, {}).get(
            "scientific_code_workspace_failure", {}
        )
        prior_checkpoint = (
            prior_failure.get("recovery_checkpoint", {})
            if isinstance(prior_failure, Mapping)
            else {}
        )
        if isinstance(prior_checkpoint, Mapping) and prior_checkpoint:
            if (
                str(checkpoint.get("resumed_from_checkpoint_id", "") or "")
                != str(prior_checkpoint.get("checkpoint_id", "") or "")
                or int(checkpoint.get("checks", 0) or 0)
                <= int(prior_checkpoint.get("checks", 0) or 0)
            ):
                errors.append(
                    f"{source_id}: scientific workspace made no new executed progress"
                )
                continue
        elif str(checkpoint.get("resumed_from_checkpoint_id", "") or ""):
            errors.append(
                f"{source_id}: scientific checkpoint has an unbound predecessor"
            )
            continue
        checkpoints[source_id] = checkpoint
    if errors or set(checkpoints) != incomplete_ids:
        if set(checkpoints) != incomplete_ids:
            errors.append(
                "not every incomplete scientific source has resumable progress"
            )
        return None, None, None, sorted(set(errors))

    continuation_count = int(
        task.inputs.get("scientific_code_workspace_continuation_count", 0)
        or 0
    ) + 1
    checkpoint_ids = {
        source_id: str(checkpoint["checkpoint_id"])
        for source_id, checkpoint in checkpoints.items()
    }
    next_inputs = deepcopy(dict(task.inputs))
    next_inputs["scientific_code_workspace_progress_manifest"] = (
        runtime_artifact_reference(manifest_id, manifest)
    )
    next_inputs["scientific_code_workspace_continuation_count"] = (
        continuation_count
    )
    next_task = replace(
        task,
        task_id=(
            f"scientific-progress:{task.owner_subsystem}:{question_id}:"
            f"{continuation_count}:{stable_hash(checkpoint_ids)[:10]}"
        ),
        objective=(
            "Continue exact model-owned scientific source from its latest raw "
            "execution observation."
        ),
        inputs=next_inputs,
    )
    boundary = (
        "The manifest preserves exact model-authored Python/R source and raw "
        "sandbox observations for the same owner. It is not accepted code, "
        "empirical confirmation, formal proof, or kernel evidence."
    )
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:"
        + stable_hash([task.task_id, manifest_id, checkpoint_ids])[:20],
        task_id=task.task_id,
        artifact_id=manifest_id,
        evidence_type="scientific_workspace_progress_checkpoint",
        status="SCIENTIFIC_SOURCE_PROGRESS_RECORDED_NOT_ACCEPTED",
        boundary=boundary,
        payload={
            "source_subsystem": task.owner_subsystem,
            "continuation_count": continuation_count,
            "checkpoint_ids": checkpoint_ids,
            "runtime_edited_source": False,
            "kernel_verified": False,
        },
    )
    observation = EnvironmentObservation(
        observation_type="scientific_workspace_progress_checkpoint",
        summary=(
            f"same-owner continuation for {len(checkpoints)} exact scientific "
            "source workspace(s)"
        ),
        payload={
            "source_subsystem": task.owner_subsystem,
            "parent_manifest_id": manifest_id,
            "continuation_count": continuation_count,
            "source_ids": sorted(checkpoints),
            "architect_routing_used": False,
            "runtime_edited_source": False,
            "proof_evidence_status": (
                "SCIENTIFIC_WORKSPACE_PROGRESS_NOT_PROOF_EVIDENCE"
            ),
        },
    )
    return next_task, evidence, observation, []


def scientific_workspace_progress_rejected_result(
    *,
    task: AgentTask,
    validation_errors: Sequence[str],
    prior_observations: Sequence[EnvironmentObservation] = (),
) -> AgentStepResult:
    """Fail closed before a model call when a continuation ref is stale."""

    errors = sorted({str(value) for value in validation_errors if str(value)})
    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            f"{task.owner_subsystem} rejected an invalid scientific workspace "
            "continuation before any planning, source, or sandbox call."
        ),
        observations=tuple(prior_observations)
        + (
            EnvironmentObservation(
                observation_type="scientific_workspace_progress_rejected",
                summary="; ".join(errors)[:500],
                payload={
                    "validation_errors": errors,
                    "planning_model_call_authorized": False,
                    "source_model_call_authorized": False,
                    "runtime_edited_source": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            ),
        ),
        failure_classification="scientific_workspace_progress_invalid",
    )


def scientific_workspace_progress_result(
    *,
    task: AgentTask,
    source_owner: str,
    produced_artifacts: Mapping[str, Any],
    observations: Sequence[EnvironmentObservation],
    tool_calls: Sequence[Any],
    evidence_entries: Sequence[EvidenceLedgerEntry | None],
    next_task: AgentTask,
    failure_classification: str,
) -> AgentStepResult:
    """Return a same-owner continuation through the existing outer runtime."""

    return AgentStepResult(
        status="REVISE",
        rationale=(
            f"{source_owner} made new executed source progress. The exact "
            "checkpoint returns to the same coding owner under the existing "
            "workspace continuation budget, without Architect routing."
        ),
        produced_artifacts=dict(produced_artifacts),
        observations=tuple(observations),
        tool_calls=tuple(tool_calls),
        evidence_entries=tuple(
            row for row in evidence_entries if row is not None
        ),
        next_task=mark_workspace_continuation(
            parent_task=task,
            next_task=next_task,
        ),
        failure_classification=failure_classification,
    )


def scientific_workspace_resume_observation(
    *,
    source_owner: str,
    parent_manifest: Mapping[str, Any],
    checkpoints: Mapping[str, Mapping[str, Any]],
) -> EnvironmentObservation:
    """Describe a same-owner resume without copying source into the trace."""

    owner_label = str(source_owner or "scientific source owner")
    owner_key = owner_label.removesuffix("Engineer").removesuffix("Evaluator").lower()
    return EnvironmentObservation(
        observation_type=f"{owner_key}_source_workspace_resumed",
        summary=(
            f"{owner_label} resumed exact source checkpoints without regenerating "
            "its planning envelope."
        ),
        payload={
            "parent_manifest_id": str(
                parent_manifest.get("manifest_id", "") or ""
            ),
            "checkpoint_source_ids": sorted(checkpoints),
            "planning_model_call_used": False,
            "architect_routing_used": False,
            "runtime_edited_source": False,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )


def reusable_scientific_source_rows(
    *,
    parent_manifest: Mapping[str, Any],
    rows_by_id: Mapping[str, Mapping[str, Any]],
    checkpoints: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project accepted peer sources without executing or editing them again."""

    result: list[dict[str, Any]] = []
    for source_id, source_row in rows_by_id.items():
        if source_id in checkpoints:
            continue
        reused_row = deepcopy(dict(source_row))
        reused_row["prototype_status"] = "REUSED_WORKSPACE_SOURCE"
        reused_row["source_reused_without_execution"] = True
        reused_row["source_reuse_lineage"] = {
            "parent_manifest_id": str(
                parent_manifest.get("manifest_id", "") or ""
            ),
            "parent_manifest_hash": stable_hash(parent_manifest),
            "parent_project_hash": str(
                source_row.get("project_hash", "") or ""
            ),
            "runtime_edited_source": False,
            "proof_evidence_status": "SOURCE_REUSE_NOT_PROOF_EVIDENCE",
        }
        result.append(reused_row)
    return result


def incomplete_scientific_source_ids(
    rows: Sequence[Mapping[str, Any]],
    *,
    source_id_field: str,
    source_accepted: Callable[[Mapping[str, Any]], bool],
) -> tuple[str, ...]:
    """Return stable identities for rows that have not passed their lane gate."""

    return tuple(
        sorted(
            {
                source_id
                for row in rows
                if (source_id := str(row.get(source_id_field, "") or "").strip())
                and not source_accepted(row)
            }
        )
    )


def resumed_scientific_code_drafts(
    *,
    proposal_drafts: Sequence[Mapping[str, Any]],
    checkpoints: Mapping[str, Mapping[str, Any]],
    source_id_field: str,
    retained_fields: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Restore exact source while retaining only bound execution metadata."""

    proposals_by_id = {
        str(row.get(source_id_field, "") or "").strip(): row
        for row in proposal_drafts
        if str(row.get(source_id_field, "") or "").strip()
    }
    drafts: list[dict[str, Any]] = []
    for source_id, checkpoint in checkpoints.items():
        proposal = proposals_by_id.get(source_id, {})
        draft = {source_id_field: source_id}
        draft.update(
            {
                field: deepcopy(proposal[field])
                for field in retained_fields
                if field in proposal
            }
        )
        draft.update(deepcopy(dict(checkpoint["current_code_draft"])))
        drafts.append(draft)
    return drafts


def scientific_source_candidate_accepted(
    prototype: Mapping[str, Any],
    *,
    confirmatory_result_blind: bool,
) -> bool:
    """Apply the scientific source gate without interpreting its content."""

    if prototype.get("scientific_code_workspace_failure"):
        return False
    if confirmatory_result_blind:
        return bool(
            prototype.get("execution_smoke_passed") is True
            and not scientific_workspace_measurement_interface_failures(
                prototype
            )
        )
    return prototype.get("smoke_passed") is True


def scientific_source_workspace_available(proposal_agent: Any) -> bool:
    """Return whether one source owner can run its retained native tool loop."""

    return bool(
        proposal_agent is not None
        and callable(
            getattr(
                getattr(proposal_agent, "provider", None),
                "generate_client_tool_turn",
                None,
            )
        )
        and callable(getattr(proposal_agent, "iterate_code_with_tools", None))
    )


def scientific_source_workspace_unavailable_result(
    *,
    task: AgentTask,
    source_owner: str,
    prior_observations: Sequence[EnvironmentObservation] = (),
) -> AgentStepResult:
    """Fail closed before fresh source authoring changes execution paradigm."""

    return AgentStepResult(
        status="BLOCKED",
        rationale=(
            f"{source_owner} requires one retained native client-tool source "
            "workspace; structured proposal authoring is disabled."
        ),
        observations=tuple(prior_observations)
        + (
            EnvironmentObservation(
                observation_type="scientific_source_workspace_unavailable",
                summary="native client-tool source workspace is unavailable",
                payload={
                    "source_owner": source_owner,
                    "planning_model_call_authorized": False,
                    "source_model_call_authorized": False,
                    "structured_source_fallback_authorized": False,
                    "runtime_edited_source": False,
                    "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                },
            ),
        ),
        failure_classification="scientific_source_workspace_unavailable",
    )


def run_source_owner_scientific_workspace(
    *,
    proposal_agent: Any,
    question: Any,
    artifact_id: str,
    code_draft: Mapping[str, Any],
    source_deferred: bool,
    workspace_context: Mapping[str, Any],
    execute_candidate: ScientificCandidateExecutor,
    execute_authoring_diagnostic: ScientificCandidateExecutor | None = None,
    failure_identity: Mapping[str, Any],
    external_initial_observation: Mapping[str, Any] | None = None,
    confirmatory_result_blind: bool = False,
    defer_confirmatory_execution: bool = False,
    allow_current_source_run: bool = False,
    disallowed_unchanged_release_hashes: Sequence[str] = (),
    recovery_checkpoint: Mapping[str, Any] | None = None,
    recovery_prototype: Mapping[str, Any] | None = None,
    session_dir: Path | None = None,
    research_sources: ResearchSourceSnapshot | None = None,
    research_source_discovery: ResearchSourceDiscovery | None = None,
) -> tuple[dict[str, Any], list[Any]]:
    """Run one source owner's direct model/tool feedback loop."""

    if execute_authoring_diagnostic and not confirmatory_result_blind:
        raise ValueError("authoring diagnostic requires blinded confirmation")
    if defer_confirmatory_execution and not execute_authoring_diagnostic:
        raise ValueError(
            "deferred confirmation requires an authoring diagnostic executor"
        )

    can_use_workspace = scientific_source_workspace_available(proposal_agent)
    tool_calls: list[Any] = []
    last_checked_prototype: dict[str, Any] = {}
    authoring_diagnostic_enabled = bool(confirmatory_result_blind and execute_authoring_diagnostic and can_use_workspace)
    workspace_executor = execute_authoring_diagnostic if authoring_diagnostic_enabled else execute_candidate
    workspace_result_blind = confirmatory_result_blind and not authoring_diagnostic_enabled
    bound_execution_fields = {}
    if "required_estimator_ids" in code_draft:
        bound_execution_fields["required_estimator_ids"] = deepcopy(list(
            code_draft.get("required_estimator_ids", []) or []))

    def record_tool_calls(value: Any | Sequence[Any]) -> None:
        if isinstance(value, (list, tuple)):
            tool_calls.extend(value)
        else:
            tool_calls.append(value)

    def failed_prototype(status: str, **details: Any) -> dict[str, Any]:
        return {
            **dict(failure_identity), "prototype_status": status,
            "smoke_passed": False, "execution_smoke_passed": False, **details,
        }

    def failed_checkpoint(status: str, error: str) -> tuple[dict[str, Any], list[Any]]:
        failure = {"validation_errors": [error], "recovery_checkpoint": active_recovery_checkpoint,
                   "runtime_edited_source": False}
        return failed_prototype(status, scientific_code_workspace_failure=failure), tool_calls

    def source_draft(row: Mapping[str, Any]) -> dict[str, Any]:
        return {key: deepcopy(row[key]) for key in
                (
                    "language",
                    "execution_profile",
                    "dependencies",
                    "entrypoint",
                    "code",
                    "project_files",
                )
                if key in row}

    def source_candidate_accepted(prototype: Mapping[str, Any]) -> bool:
        return scientific_source_candidate_accepted(prototype, confirmatory_result_blind=confirmatory_result_blind)

    def source_observation(prototype: Mapping[str, Any]) -> dict[str, Any]:
        return scientific_workspace_prototype_observation(prototype,
            include_empirical_outcomes=not workspace_result_blind,
            include_acceptance_outcomes=not confirmatory_result_blind)

    def check_candidate(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        execution_candidate = {**dict(candidate), **bound_execution_fields}
        candidate_source = str(execution_candidate.get("code", "") or "")
        candidate_source_hash = stable_hash(candidate_source)
        candidate_project_files = execution_candidate.get("project_files", [])
        candidate_project_hash = scientific_project_hash(
            language=normalized_generated_code_language(
                execution_candidate.get("language")
            ),
            code=candidate_source,
            project_files=candidate_project_files,
        )
        candidate_release_identity = candidate_project_hash
        if (
            candidate_source
            and candidate_release_identity in disallowed_unchanged_release_hashes
        ):
            prototype = failed_prototype(
                "UNCHANGED_SOURCE_REJECTED",
                source_code=candidate_source,
                script_hash=candidate_source_hash,
                project_files=deepcopy(list(candidate_project_files)),
                project_hash=candidate_project_hash,
                parent_script_hash=candidate_source_hash,
                execution_attempted=False,
                runtime_errors=[
                    "The candidate project hash matches a released parent project; "
                    "an unchanged release cannot consume a fresh evaluation cohort."
                ],
                proof_evidence_status="NOT_PROOF_EVIDENCE",
            )
        else:
            prototype, tool_call = workspace_executor(execution_candidate)
            record_tool_calls(tool_call)
        last_checked_prototype.clear()
        last_checked_prototype.update(deepcopy(dict(prototype)))
        check = {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": source_candidate_accepted(prototype),
            "prototype": source_observation(prototype),
        }
        disposition = str(prototype.get("source_iteration_disposition", "") or "").strip()
        if disposition:
            check["source_iteration_disposition"] = disposition
        source_owner = prototype.get("source_owner", {})
        if isinstance(source_owner, Mapping) and source_owner:
            check["source_owner"] = deepcopy(dict(source_owner))
        return check

    active_recovery_checkpoint = (deepcopy(dict(recovery_checkpoint))
                                  if isinstance(recovery_checkpoint, Mapping) else {})
    if active_recovery_checkpoint:
        try:
            workspace_draft, initial_observation = load_scientific_code_workspace_checkpoint(
                active_recovery_checkpoint, artifact_id=artifact_id)
        except ValueError as exc:
            return failed_checkpoint("SCIENTIFIC_WORKSPACE_CHECKPOINT_INVALID", str(exc))
        workspace_operation = str(active_recovery_checkpoint.get(
            "workspace_operation", "targeted_revision") or "targeted_revision")
        prototype = failed_prototype("MODEL_SOURCE_WORKSPACE_FAILED")
        if active_recovery_checkpoint.get("current_source_executed") is True:
            restored_prototype = (deepcopy(dict(recovery_prototype))
                                  if isinstance(recovery_prototype, Mapping) else {})
            parent_failure = restored_prototype.pop(
                "scientific_code_workspace_failure", {})
            parent_checkpoint = (parent_failure.get("recovery_checkpoint", {})
                                 if isinstance(parent_failure, Mapping) else {})
            expected_observation = initial_observation.get("prototype", {})
            recovery_valid = (
                parent_checkpoint.get("checkpoint_id")
                == active_recovery_checkpoint.get("checkpoint_id")
                and str(restored_prototype.get("source_code", "") or "")
                == str(workspace_draft.get("code", "") or "")
                and isinstance(expected_observation, Mapping)
                and stable_hash(source_observation(restored_prototype))
                == stable_hash(dict(expected_observation))
                and source_candidate_accepted(restored_prototype)
                == (initial_observation.get("accepted") is True)
            )
            if not recovery_valid:
                return failed_checkpoint(
                    "SCIENTIFIC_WORKSPACE_RECOVERY_PROTOTYPE_INVALID",
                    "recovery prototype is not bound to checkpoint evidence")
            last_checked_prototype.update(restored_prototype)
    elif source_deferred:
        if not can_use_workspace:
            return failed_prototype(
                "MODEL_SOURCE_WORKSPACE_UNAVAILABLE",
                reason="Deferred source requires a callable source-owner workspace."
            ), tool_calls
        workspace_draft: Mapping[str, Any] | None = None
        workspace_operation = "initial_authoring"
        initial_observation = {
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "artifact_id": artifact_id,
            "execution_attempted": False,
            "observation": "No source exists; author and run the complete candidate here.",
        }
        prototype = failed_prototype("MODEL_SOURCE_WORKSPACE_FAILED")
    elif external_initial_observation and can_use_workspace:
        workspace_draft = source_draft(code_draft)
        workspace_operation = "targeted_revision"
        initial_observation = {
            **deepcopy(dict(external_initial_observation)),
            "code_draft_hash": stable_hash(workspace_draft),
            "accepted": False,
        }
        prototype = failed_prototype("MODEL_SOURCE_WORKSPACE_FAILED")
    else:
        prototype, tool_call = workspace_executor(code_draft)
        record_tool_calls(tool_call)
        last_checked_prototype.clear()
        last_checked_prototype.update(deepcopy(dict(prototype)))
        if (
            prototype.get("source_iteration_disposition")
            == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
            or not can_use_workspace
            or not authoring_diagnostic_enabled and source_candidate_accepted(prototype)
        ):
            return prototype, tool_calls
        workspace_draft = source_draft(code_draft)
        workspace_operation = "targeted_revision"
        initial_accepted = source_candidate_accepted(prototype)
        initial_observation = {
            "code_draft_hash": stable_hash(workspace_draft),
            "accepted": initial_accepted,
            "prototype": source_observation(prototype),
            "source_iteration_disposition": (
                "accepted" if initial_accepted else SCIENTIFIC_SOURCE_REVISE_CURRENT
            ),
        }

    workspace_context = dict(workspace_context)
    workspace_context.pop("consumer_execution_observation", None)
    workspace_context["initial_observation_binding"] = {"content_hash": stable_hash(initial_observation), "body_transport": "initial_workspace_observation"}
    try:
        workspace_result = proposal_agent.iterate_code_with_tools(
            question=question,
            artifact_id=artifact_id,
            code_draft=workspace_draft,
            initial_observation=initial_observation,
            workspace_context=workspace_context,
            check_candidate=check_candidate,
            workspace_operation=workspace_operation,
            allow_current_source_run=allow_current_source_run,
            recovery_checkpoint=(active_recovery_checkpoint or None),
            session_dir=session_dir,
            research_sources=research_sources,
            research_source_discovery=research_source_discovery,
        )
    except PacketValidationError as exc:
        if last_checked_prototype:
            prototype = deepcopy(last_checked_prototype)
        prototype["scientific_code_workspace_failure"] = {
            "validation_errors": list(exc.errors),
            "attempts": exc.attempts,
            "history": theory_documents.workspace_evidence_history(
                exc.history
            ),
            "recovery_checkpoint": dict(exc.recovery_checkpoint or {}),
            "runtime_edited_source": False,
        }
        return prototype, tool_calls

    if not last_checked_prototype:
        raise RuntimeError("scientific workspace accepted without a sandbox result")
    terminal_check = dict(workspace_result.check_result)
    if terminal_check.get(
        "source_iteration_disposition"
    ) == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER:
        prototype = deepcopy(last_checked_prototype)
        prototype["source_iteration_disposition"] = (
            SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
        )
        prototype["source_owner"] = deepcopy(dict(terminal_check.get("source_owner", {})))
        prototype["dependency_failure_report"] = deepcopy(dict(
            terminal_check.get("dependency_failure_report", {})
        ))
        prototype["scientific_code_workspace"] = dict(workspace_result.evidence)
        return prototype, tool_calls

    if authoring_diagnostic_enabled:
        committed_draft = {**dict(workspace_result.code_draft), **bound_execution_fields}
        if defer_confirmatory_execution:
            prototype = deepcopy(last_checked_prototype)
        else:
            prototype, tool_call = execute_candidate(committed_draft)
            record_tool_calls(tool_call)
        workspace_evidence = {
            **dict(workspace_result.evidence),
            "authoring_execution_phase": "exploratory_diagnostic",
            "authoring_diagnostic_accepted": terminal_check.get("accepted") is True,
            "authoring_diagnostic_source_hash": str(
                last_checked_prototype.get("script_hash", "") or ""),
            "authoring_diagnostic_result_hash": str(
                last_checked_prototype.get("result_hash", "") or ""),
            "authoring_diagnostic_runtime_replicates": (
                last_checked_prototype.get("runtime_replicates")
            ),
            "confirmatory_execution_after_model_commit": bool(
                not defer_confirmatory_execution
            ),
            "confirmatory_execution_deferred_for_independent_review": bool(
                defer_confirmatory_execution
            ),
            "confirmatory_outcomes_returned_to_source_model": False,
            "evidence_boundary": (
                "The model iterates on diagnostic execution; exact committed bytes "
                + (
                    "are held for independent review before confirmatory execution."
                    if defer_confirmatory_execution
                    else "then execute once on a blinded confirmatory cohort whose "
                    "outcome is not returned to the authoring session."
                )
            ),
        }
    else:
        prototype = deepcopy(last_checked_prototype)
        workspace_evidence = dict(workspace_result.evidence)
    prototype["scientific_code_workspace"] = workspace_evidence
    return prototype, tool_calls


def _outcome_blind_request_shape(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _outcome_blind_request_shape(child)
            for key, child in value.items()
            if str(key) not in _OUTCOME_DERIVED_SHAPE_FIELDS
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_outcome_blind_request_shape(child) for child in value]
    return deepcopy(value)


def scientific_workspace_prototype_observation(
    prototype: Mapping[str, Any],
    *,
    include_empirical_outcomes: bool = True,
    include_acceptance_outcomes: bool | None = None,
) -> dict[str, Any]:
    """Apply outcome visibility without summarizing the permitted diagnostics."""

    if include_acceptance_outcomes is None:
        include_acceptance_outcomes = include_empirical_outcomes
    if include_acceptance_outcomes and not include_empirical_outcomes:
        raise ValueError(
            "acceptance outcomes require empirical outcomes in workspace feedback"
        )
    contracts = {
        str(row.get("contract_id", "") or ""): row
        for row in prototype.get("metric_contracts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("contract_id", "") or "").strip()
    }
    evaluation = prototype.get("metric_contract_evaluation", {})
    evaluation_rows = (
        evaluation.get("evaluations", [])
        if isinstance(evaluation, Mapping)
        else []
    )
    measurement_interface_failures = (
        scientific_workspace_measurement_interface_failures(prototype)
    )
    failed_contracts: list[dict[str, Any]] = []
    for row in evaluation_rows or []:
        if not isinstance(row, Mapping) or row.get("passed") is True:
            continue
        contract_id = str(row.get("contract_id", "") or "").strip()
        contract = contracts.get(contract_id, {})
        failed_contracts.append(
            {
                key: deepcopy(value)
                for key, value in {
                    "contract_id": contract_id,
                    "requirement_id": row.get("requirement_id", ""),
                    "metric_path": row.get("metric_path", []),
                    "metric_semantics": contract.get("metric_semantics", ""),
                    "measurement_protocol": contract.get(
                        "measurement_protocol", ""
                    ),
                    "operator": row.get("operator", contract.get("operator", "")),
                    "aggregation": row.get(
                        "aggregation", contract.get("aggregation", "")
                    ),
                    "threshold": contract.get("threshold"),
                    "lower": contract.get("lower"),
                    "upper": contract.get("upper"),
                    "tolerance": contract.get("tolerance"),
                    "observed": row.get("resolved_values_preview", []),
                    "aggregate_value": row.get("aggregate_value"),
                    "errors": row.get("errors", []),
                }.items()
                if value not in (None, "", [], {})
            }
        )
    direct_field_names = [
        "execution_phase",
        "execution_attempted",
        "execution_smoke_passed",
        "returncode",
        "runtime_errors",
        "safety_errors",
        "estimator_binding_errors",
        "estimator_runtime_failure_ids",
        "estimator_runtime_errors",
        "result_parse_error",
        "stderr_summary",
        "required_estimator_ids",
        "available_upstream_estimator_ids",
        "estimator_invocation_counts",
        "mechanical_estimator_invocation_verified",
        "script_hash",
    ]
    if include_empirical_outcomes:
        direct_field_names.extend(
            (
                "runtime_seed",
                "runtime_replicates",
                "stdout_summary",
                "result_hash",
            )
        )
    if include_acceptance_outcomes:
        direct_field_names.extend(
            (
                "prototype_status",
                "smoke_passed",
                "metric_gate_errors",
            )
        )
    if (
        prototype.get("mechanical_estimator_invocation_verified") is not True
        or prototype.get("estimator_binding_errors")
        or prototype.get("estimator_runtime_errors")
    ):
        direct_field_names.append("estimator_invocation_samples")
    direct_fields = {
        key: deepcopy(prototype[key])
        for key in direct_field_names
        if prototype.get(key) not in (None, "", [], {})
    }
    if not include_empirical_outcomes and "estimator_invocation_samples" in direct_fields:
        direct_fields["estimator_invocation_samples"] = {
            str(artifact_id): [
                {
                    **{
                        "request_shape": _outcome_blind_request_shape(
                            row["request_shape"]
                        )
                    },
                    **{
                        key: deepcopy(row[key])
                        for key in ("response_status", "error_type")
                        if key in row
                    },
                }
                for row in rows
                if isinstance(row, Mapping) and row.get("request_shape")
            ]
            for artifact_id, rows in direct_fields["estimator_invocation_samples"].items()
            if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes))
        }
    return {
        "artifact_kind": "ScientificSandboxWorkspaceObservation",
        **{
            key: deepcopy(value)
            for key, value in direct_fields.items()
        },
        **(
            {
                **(
                    {"failed_metric_contracts": failed_contracts}
                    if include_acceptance_outcomes and failed_contracts
                    else {}
                ),
                "metrics_preview": deepcopy(
                    prototype.get("metrics", {})
                ),
                **(
                    {}
                    if include_acceptance_outcomes
                    else {
                        "acceptance_outcomes_withheld": True,
                        "acceptance_outcome_authority": "EmpiricalEvaluator",
                        **(
                            {
                                "measurement_interface_failures": (
                                    measurement_interface_failures
                                )
                            }
                            if measurement_interface_failures
                            else {}
                        ),
                    }
                ),
            }
            if include_empirical_outcomes
            else {
                "empirical_outcomes_withheld": True,
                "empirical_outcome_authority": "EmpiricalEvaluator",
                **(
                    {
                        "measurement_interface_failures": (
                            measurement_interface_failures
                        )
                    }
                    if measurement_interface_failures
                    else {}
                ),
            }
        ),
        "full_execution_artifact_persisted": True,
        "source_replayed_to_model": False,
        "empirical_evidence_status": prototype.get(
            "empirical_evidence_status",
            "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_CONFIRMATORY_EVIDENCE",
        ),
        "proof_evidence_status": "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE",
    }


def scientific_workspace_measurement_interface_failures(
    prototype: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return outcome-blind failures in the generated metric output ABI."""

    evaluator_failures = [
        {
            "measurement_interface_status": "INVALID",
            "measurement_interface_errors": [str(error)],
        }
        for error in prototype.get("executable_evaluator_interface_errors", []) or []
        if str(error).strip()
    ]
    contracts = {
        str(row.get("contract_id", "") or ""): row
        for row in prototype.get("metric_contracts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("contract_id", "") or "").strip()
    }
    evaluation = prototype.get("metric_contract_evaluation", {})
    rows = (
        evaluation.get("evaluations", [])
        if isinstance(evaluation, Mapping)
        else []
    )
    failures: list[dict[str, Any]] = evaluator_failures
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        if row.get("measurement_interface_valid") is not False:
            continue
        contract_id = str(row.get("contract_id", "") or "").strip()
        contract = contracts.get(contract_id, {})
        failures.append(
            {
                key: deepcopy(value)
                for key, value in {
                    "contract_id": contract_id,
                    "requirement_id": row.get("requirement_id", ""),
                    "metric_path": row.get("metric_path", []),
                    "metric_value_kind": contract.get("metric_value_kind"),
                    "operator": contract.get("operator"),
                    "aggregation": contract.get("aggregation"),
                    "threshold": contract.get("threshold"),
                    "lower": contract.get("lower"),
                    "upper": contract.get("upper"),
                    "tolerance": contract.get("tolerance"),
                    "minimum_pass_count": contract.get(
                        "minimum_pass_count"
                    ),
                    "minimum_pass_fraction": contract.get(
                        "minimum_pass_fraction"
                    ),
                    "required_runtime_replicates": contract.get(
                        "required_runtime_replicates"
                    ),
                    "measurement_interface_status": row.get(
                        "measurement_interface_status", "INVALID"
                    ),
                    "measurement_interface_errors": row.get(
                        "measurement_interface_errors", []
                    ),
                }.items()
                if value not in (None, "", [], {})
            }
        )
    return failures


def complete_scientific_source_draft(
    row: Mapping[str, Any],
    *,
    include_estimator_selection: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Recover one exact model-authored draft from persisted execution evidence."""

    source = str(row.get("source_code", "") or "")
    script_hash = str(row.get("script_hash", "") or "").strip()
    errors: list[str] = []
    if not source:
        errors.append("executed scientific source is missing")
    if not script_hash or (source and script_hash != stable_hash(source)):
        errors.append("executed scientific source hash mismatch")
    dependencies = row.get("dependencies", [])
    if not isinstance(dependencies, list):
        errors.append("executed scientific dependencies are not an array")
        dependencies = []
    raw_project_files = row.get("project_files", [])
    try:
        project_files = [
            project_file.to_json()
            for project_file in normalized_scientific_project_files(
                raw_project_files,
                language=normalized_generated_code_language(row.get("language")),
            )
        ]
    except ValueError as exc:
        errors.append("executed scientific project is invalid: " + str(exc))
        project_files = []
    computed_project_hash = scientific_project_hash(
        language=normalized_generated_code_language(row.get("language")),
        code=source,
        project_files=project_files,
    )
    persisted_project_hash = str(row.get("project_hash", "") or "").strip()
    if not persisted_project_hash:
        errors.append("executed scientific project hash is missing")
    elif persisted_project_hash != computed_project_hash:
        errors.append("executed scientific project hash mismatch")
    draft = {
        "language": str(row.get("language", "") or ""),
        "execution_profile": str(
            row.get("requested_execution_profile", "")
            or row.get("executor_profile", "")
            or ""
        ),
        "dependencies": deepcopy(dependencies),
        "entrypoint": "run_sandbox",
        "code": source,
    }
    if project_files:
        draft["project_files"] = project_files
    if include_estimator_selection:
        required_estimator_ids = row.get("required_estimator_ids", [])
        if not isinstance(required_estimator_ids, list):
            errors.append("consumer estimator selection is not an array")
        else:
            draft["required_estimator_ids"] = deepcopy(required_estimator_ids)
    if not errors:
        errors.extend(generated_code_execution_contract_errors(draft))
    return draft, sorted(set(errors))


def scientific_consumer_replay_drafts(
    manifest: Mapping[str, Any],
    *,
    question_id: str,
    theory_packet_id: str,
) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Recover exact consumer source from one bound execution manifest."""

    errors: list[str] = []
    question = manifest.get("question", {})
    if (
        manifest.get("artifact_kind") != "RuntimeSimulationManifest"
        or not str(manifest.get("manifest_id", "") or "").strip()
        or str(manifest.get("theory_packet_id", "") or "") != theory_packet_id
        or not isinstance(question, Mapping)
        or str(question.get("id", "") or "") != question_id
    ):
        errors.append("consumer resume manifest lineage is invalid")
    intent_artifact_id = str(
        manifest.get("simulation_source_workspace_intent_artifact_id", "") or ""
    ).strip()
    if not intent_artifact_id:
        errors.append("consumer resume source intent identity is missing")
    drafts: list[dict[str, Any]] = []
    for raw_row in manifest.get(
        "generated_simulation_sandbox_prototypes", []
    ) or []:
        if not isinstance(raw_row, Mapping):
            continue
        draft, draft_errors = complete_scientific_source_draft(
            raw_row,
            include_estimator_selection=True,
        )
        simulation_id = str(raw_row.get("simulation_id", "") or "").strip()
        if not simulation_id:
            draft_errors.append("consumer resume simulation id is missing")
        errors.extend(
            f"{simulation_id or 'unknown consumer'}: {error}"
            for error in draft_errors
        )
        if not draft_errors:
            drafts.append({"simulation_id": simulation_id, **draft})
    if not drafts:
        errors.append("consumer resume has no exact executable source")
    return intent_artifact_id, drafts, sorted(set(errors))


def scientific_consumer_revision_sources(
    manifest: Mapping[str, Any],
    *,
    dependency_context: Mapping[str, Any],
    revision_artifact_ids: Sequence[str],
    implementation_artifact_ids: Sequence[str],
    theory_packet_id: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Validate exact source rows selected by a downstream observation."""

    revision_ids = sorted(set(revision_artifact_ids))
    errors: list[str] = []
    if (
        not revision_ids
        or str(dependency_context.get("source_owner_subsystem", "") or "")
        != "AlgorithmEngineer"
        or list(dependency_context.get("dependency_artifact_ids", []) or [])
        != revision_ids
        or manifest.get("artifact_kind") != "RuntimeAlgorithmSandboxManifest"
        or str(manifest.get("manifest_id", "") or "")
        != str(dependency_context.get("source_manifest_id", "") or "")
        or stable_hash(manifest)
        != str(dependency_context.get("source_manifest_hash", "") or "")
        or str(manifest.get("theory_packet_id", "") or "") != theory_packet_id
    ):
        errors.append("algorithm consumer source lineage is incomplete or stale")
    rows = {
        str(row.get("estimator_id", "") or "").strip(): dict(row)
        for row in manifest.get("prototypes", []) or []
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "").strip()
    }
    expected_hashes = dependency_context.get("dependency_artifact_hashes", {})
    expected_hashes = (
        dict(expected_hashes) if isinstance(expected_hashes, Mapping) else {}
    )
    implementation_ids = set(implementation_artifact_ids)
    for artifact_id in revision_ids:
        row = rows.get(artifact_id, {})
        _, source_errors = (
            complete_scientific_source_draft(row)
            if row
            else ({}, ["executed scientific source is missing"])
        )
        if (
            artifact_id not in implementation_ids
            or row.get("smoke_passed") is not True
            or str(row.get("project_hash", "") or "")
            != str(expected_hashes.get(artifact_id, "") or "")
            or source_errors
        ):
            errors.append(
                f"consumer source artifact is unavailable or stale: {artifact_id}"
            )
    return rows, sorted(set(errors))


def scientific_consumer_dependency_context(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Bind raw consumer failures to their exact source-owned dependencies."""

    owners: list[dict[str, Any]] = []
    consumer_sources: list[dict[str, str]] = []
    observations_by_artifact: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    for raw_row in rows:
        if not isinstance(raw_row, Mapping):
            continue
        owner = raw_row.get("source_owner", {})
        if not isinstance(owner, Mapping) or not owner:
            continue
        owner_row = deepcopy(dict(owner))
        if str(owner_row.get("owner_subsystem", "") or "") != (
            "AlgorithmEngineer"
        ):
            errors.append("consumer dependency source owner is not AlgorithmEngineer")
            continue
        artifact_ids = owner_row.get("artifact_ids", [])
        artifact_hashes = owner_row.get("artifact_hashes", {})
        if (
            not isinstance(artifact_ids, list)
            or not artifact_ids
            or not isinstance(artifact_hashes, Mapping)
        ):
            errors.append("consumer dependency source identity is incomplete")
            continue
        normalized_ids = sorted(
            {
                str(value or "").strip()
                for value in artifact_ids
                if str(value or "").strip()
            }
        )
        if not normalized_ids or any(
            not str(artifact_hashes.get(artifact_id, "") or "").strip()
            for artifact_id in normalized_ids
        ):
            errors.append("consumer dependency artifact hash is missing")
            continue
        simulation_id = str(raw_row.get("simulation_id", "") or "").strip()
        script_hash = str(raw_row.get("script_hash", "") or "").strip()
        if not simulation_id or not script_hash:
            errors.append("failed consumer source identity is incomplete")
            continue
        consumer_sources.append(
            {
                "artifact_id": simulation_id,
                "source_hash": script_hash,
                "evaluation_contract_hash": stable_hash(
                    {
                        "metric_contracts": raw_row.get("metric_contracts", []),
                        "required_estimator_ids": raw_row.get(
                            "required_estimator_ids", []
                        ),
                    }
                ),
            }
        )
        observation = {
            "consumer_artifact_id": simulation_id,
            "consumer_source_hash": script_hash,
            "observation": scientific_workspace_prototype_observation(raw_row),
        }
        for artifact_id in normalized_ids:
            observations_by_artifact.setdefault(artifact_id, []).append(
                deepcopy(observation)
            )
        owners.append(owner_row)
    if not owners:
        errors.append("no exact dependency source owner was recorded")
        return {}, sorted(set(errors))

    source_manifest_ids = {
        str(row.get("source_manifest_id", "") or "").strip() for row in owners
    }
    source_manifest_hashes = {
        str(row.get("source_manifest_hash", "") or "").strip() for row in owners
    }
    if "" in source_manifest_ids or len(source_manifest_ids) != 1:
        errors.append("consumer dependency spans ambiguous source manifests")
    if "" in source_manifest_hashes or len(source_manifest_hashes) != 1:
        errors.append("consumer dependency source manifest hash is ambiguous")
    merged_hashes: dict[str, str] = {}
    for owner in owners:
        for artifact_id in owner.get("artifact_ids", []) or []:
            normalized_id = str(artifact_id or "").strip()
            content_hash = str(
                (owner.get("artifact_hashes", {}) or {}).get(normalized_id, "")
                or ""
            ).strip()
            prior_hash = merged_hashes.get(normalized_id)
            if prior_hash and prior_hash != content_hash:
                errors.append(
                    f"consumer dependency artifact hash conflicts: {normalized_id}"
                )
            elif normalized_id and content_hash:
                merged_hashes[normalized_id] = content_hash
    context = {
        "source_owner_subsystem": "AlgorithmEngineer",
        "source_manifest_id": next(iter(source_manifest_ids), ""),
        "source_manifest_hash": next(iter(source_manifest_hashes), ""),
        "dependency_artifact_ids": sorted(merged_hashes),
        "dependency_artifact_hashes": dict(sorted(merged_hashes.items())),
        "consumer_source_artifacts": sorted(
            consumer_sources,
            key=lambda row: (row["artifact_id"], row["source_hash"]),
        ),
        "consumer_observations_by_dependency": observations_by_artifact,
    }
    return context, sorted(set(errors))


def advance_scientific_consumer_revision_budget(
    *,
    task_budget: Mapping[str, Any],
    question_id: str,
    theory_packet_id: str,
    dependency_context: Mapping[str, Any],
    failure_classification: str,
    max_revisions: int,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Advance one bounded source-owner loop across outer runtime handoffs."""

    budget = deepcopy(dict(task_budget))
    prior_value = budget.get(SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY, {})
    prior = dict(prior_value) if isinstance(prior_value, Mapping) else {}
    lineage_identity = {
        "question_id": question_id,
        "theory_packet_id": theory_packet_id,
        "consumer_owner_subsystem": "SimulationEvaluator",
        "dependency_owner_subsystem": "AlgorithmEngineer",
        "consumer_contracts": [
            {
                "artifact_id": artifact_id,
                "evaluation_contract_hash": contract_hash,
            }
            for artifact_id, contract_hash in sorted(
                {
                    (
                        str(row.get("artifact_id", "") or ""),
                        str(row.get("evaluation_contract_hash", "") or ""),
                    )
                    for row in dependency_context.get(
                        "consumer_source_artifacts", []
                    )
                    or []
                    if isinstance(row, Mapping)
                }
            )
        ],
    }
    lineage_id = "scientific_consumer_lineage:" + stable_hash(lineage_identity)[:20]
    errors: list[str] = []
    prior_lineage_id = str(prior.get("lineage_id", "") or "")
    if prior_lineage_id and prior_lineage_id != lineage_id:
        errors.append("scientific consumer continuation changed source lineage")
    try:
        revisions_used = max(0, int(prior.get("revisions_used", 0) or 0))
        frozen_max_revisions = (
            max(0, int(prior.get("max_revisions", 0) or 0))
            if prior
            else max(0, int(max_revisions or 0))
        )
    except (TypeError, ValueError):
        errors.append("scientific consumer revision budget is malformed")
        revisions_used = 0
        frozen_max_revisions = 0
    revision_available = not errors and revisions_used < frozen_max_revisions
    failure_fingerprint = stable_hash(
        {
            "failure_classification": failure_classification,
            "dependency_artifact_hashes": dependency_context.get(
                "dependency_artifact_hashes", {}
            ),
            "consumer_observations": dependency_context.get(
                "consumer_observations_by_dependency", {}
            ),
        }
    )
    prior_fingerprints = [
        str(value)
        for value in prior.get("failure_fingerprints", []) or []
        if str(value)
    ]
    row = {
        "lineage_id": lineage_id,
        "revisions_used": revisions_used + (1 if revision_available else 0),
        "max_revisions": frozen_max_revisions,
        "revision_scheduled": revision_available,
        "budget_exhausted": not revision_available,
        "failure_fingerprints": (prior_fingerprints + [failure_fingerprint])[-8:],
    }
    budget[SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY] = row
    return budget, row, sorted(set(errors))


def run_scientific_code_workspace(
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
    artifact_id: str,
    initial_code_draft: Mapping[str, Any] | None,
    initial_check_result: Mapping[str, Any],
    check_candidate: ScientificCodeCheck,
    workspace_operation: str = "targeted_revision",
    allow_current_source_run: bool = False,
    allow_dependency_handoff: bool = False,
    request_metadata: Mapping[str, Any] | None = None,
    recovery_checkpoint: Mapping[str, Any] | None = None,
    session_dir: Path | None = None,
    context_documents: Mapping[str, str] | None = None,
    research_sources: ResearchSourceSnapshot | None = None,
    research_source_discovery: ResearchSourceDiscovery | None = None,
) -> ScientificCodeWorkspaceResult:
    """Run the existing owner-bound tools through the shared retained loop."""

    workspace = prepare_scientific_code_workspace(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        model_tier=model_tier,
        temperature=temperature,
        max_tokens=max_tokens,
        max_turns=max_turns,
        max_no_progress_turns=max_no_progress_turns,
        artifact_id=artifact_id,
        initial_code_draft=initial_code_draft,
        initial_check_result=initial_check_result,
        check_candidate=check_candidate,
        workspace_operation=workspace_operation,
        allow_current_source_run=allow_current_source_run,
        allow_dependency_handoff=allow_dependency_handoff,
        request_metadata=request_metadata,
        recovery_checkpoint=recovery_checkpoint,
        session_dir=session_dir,
        context_documents=context_documents,
        research_sources=research_sources,
        research_source_discovery=research_source_discovery,
    )
    return run_client_tool_workspace(backend=provider, workspace=workspace)


def prepare_scientific_code_workspace(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_no_progress_turns: int,
    artifact_id: str,
    initial_code_draft: Mapping[str, Any] | None,
    initial_check_result: Mapping[str, Any],
    check_candidate: ScientificCodeCheck,
    workspace_operation: str = "targeted_revision",
    allow_current_source_run: bool = False,
    allow_dependency_handoff: bool = False,
    request_metadata: Mapping[str, Any] | None = None,
    recovery_checkpoint: Mapping[str, Any] | None = None,
    session_dir: Path | None = None,
    context_documents: Mapping[str, str] | None = None,
    research_sources: ResearchSourceSnapshot | None = None,
    research_source_discovery: ResearchSourceDiscovery | None = None,
) -> PreparedClientToolWorkspace[ScientificCodeWorkspaceResult]:
    """Prepare executable owner-bound tools without making a model call."""

    if not str(artifact_id).strip():
        raise ValueError("scientific code workspace requires a bound artifact id")
    for value, label in (
        (max_turns, "turn"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"scientific code workspace {label} budget must be positive")
    if workspace_operation not in {"initial_authoring", "targeted_revision"}:
        raise ValueError("unsupported scientific code workspace operation")

    parent_draft = (
        _complete_code_draft(initial_code_draft)
        if isinstance(initial_code_draft, Mapping) and initial_code_draft
        else {}
    )
    resumed_checkpoint = (
        deepcopy(dict(recovery_checkpoint))
        if isinstance(recovery_checkpoint, Mapping) and recovery_checkpoint
        else {}
    )
    resolved_session_dir = session_dir.resolve() if session_dir else None
    observation_root = resolved_session_dir / "observation_documents" if resolved_session_dir else None
    if observation_root is not None and resolved_session_dir not in observation_root.resolve().parents:
        raise ValueError("scientific observation directory escapes workspace")
    context_documents = deepcopy(dict(context_documents or {}))
    observation_documents: dict[str, str] = {}
    observation_document_refs = deepcopy(resumed_checkpoint.get("observation_document_refs", {}))
    if not isinstance(observation_document_refs, dict):
        raise ValueError("scientific observation document references are malformed")

    def model_observation(value: Mapping[str, Any], *, retain_document: bool = False) -> dict[str, Any]:
        projected, documents, _ = externalize_client_tool_text_documents(
            value, min_characters=1024, path_prefix="observations/text",
        )
        if retain_document or len(_compact_json(projected)) > CLIENT_TOOL_RESULT_MAX_CHARS:
            path = f"observations/{stable_hash(dict(value))}.md"
            documents[path] = json.dumps(projected, indent=2, sort_keys=True, ensure_ascii=False, default=str)
            reference = {"client_tool_evidence_document_ref": path, "content_externalized_without_loss": True}
            projected = {**projected, **reference}
            if len(_compact_json(projected)) > CLIENT_TOOL_RESULT_MAX_CHARS:
                projected = reference
        for path, content in documents.items():
            if path in context_documents or (path in observation_documents and observation_documents[path] != content):
                raise ValueError("scientific observation document path collision")
            observation_documents[path] = content
            if observation_root is not None:
                target = (observation_root / path).resolve()
                if observation_root.resolve() not in target.parents:
                    raise ValueError("scientific observation document escapes workspace")
                encoded = content.encode("utf-8")
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    if target.read_bytes() != encoded:
                        raise ValueError("scientific observation document changed")
                else:
                    with target.open("xb") as stream:
                        stream.write(encoded)
                observation_document_refs[path] = {
                    "path": str(target), "sha256": hashlib.sha256(encoded).hexdigest(),
                    "byte_size": len(encoded),
                }
        return projected

    resumed_checkpoint_id = ""
    prior_source_updates = 0
    prior_checks = 0
    prior_observed_hashes: set[str] = set()
    resumed_current_source_executed = True
    prior_research_source_refs: list[dict[str, Any]] = []
    if resumed_checkpoint:
        resumed_draft, resumed_last_check = (
            load_scientific_code_workspace_checkpoint(
                resumed_checkpoint,
                artifact_id=artifact_id,
            )
        )
        if parent_draft and stable_hash(parent_draft) != stable_hash(resumed_draft):
            raise ValueError(
                "scientific code workspace resume source does not match initial source"
            )
        if stable_hash(dict(initial_check_result)) != stable_hash(resumed_last_check):
            raise ValueError(
                "scientific code workspace resume observation does not match checkpoint"
            )
        parent_draft = resumed_draft
        resumed_checkpoint_id = str(
            resumed_checkpoint.get("checkpoint_id", "") or ""
        )
        prior_source_updates = int(
            resumed_checkpoint.get("source_updates", 0) or 0
        )
        prior_checks = int(resumed_checkpoint.get("checks", 0) or 0)
        prior_observed_hashes = {
            str(value)
            for value in resumed_checkpoint.get(
                "observed_code_draft_hashes", []
            )
            or []
            if str(value or "").strip()
        }
        resumed_current_source_executed = bool(
            resumed_checkpoint.get("current_source_executed", True)
        )
        prior_refs = resumed_checkpoint.get("research_source_refs", [])
        if not isinstance(prior_refs, list) or any(not isinstance(row, Mapping) for row in prior_refs):
            raise ValueError("scientific checkpoint research source refs are malformed")
        prior_research_source_refs = [deepcopy(dict(row)) for row in prior_refs]
        if research_source_discovery is None and any(
            row.get("tool") in {RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL, RESEARCH_SOURCE_DISCOVERY_READ_TOOL, RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL}
            for row in prior_research_source_refs
        ):
            raise ValueError(
                "continued scientific source discovery requires its public provider"
            )
    if workspace_operation == "targeted_revision" and not parent_draft:
        raise ValueError("targeted scientific source revision requires parent source")
    for path, reference in observation_document_refs.items():
        relative_path = theory_documents._normalized_theory_document_path(path)
        if observation_root is None or not isinstance(reference, Mapping):
            raise ValueError("scientific observation resume requires its persistent directory")
        expected_path = (observation_root / relative_path).resolve()
        if observation_root.resolve() not in expected_path.parents or str(expected_path) != reference.get("path"):
            raise ValueError("scientific observation document path mismatch")
        content, errors = read_hash_bound_utf8_file(reference)
        if errors or path in context_documents:
            raise ValueError("scientific observation document identity mismatch")
        observation_documents[path] = content
    initial_model_observation = model_observation(initial_check_result)
    parent_hash = stable_hash(parent_draft) if parent_draft else ""
    observed_draft_hashes = set(prior_observed_hashes)
    initial_check_hash = str(
        initial_check_result.get("code_draft_hash", "") or ""
    )
    if (
        parent_hash
        and initial_check_hash == parent_hash
        and (not resumed_checkpoint or resumed_current_source_executed)
    ):
        observed_draft_hashes.add(parent_hash)
    state: dict[str, Any] = {
        "code_draft": parent_draft,
        "code_draft_hash": parent_hash,
        "source_updates": prior_source_updates,
        "current_source_run_requests": 0,
        "dependency_parent_reexecuted": False,
        "checks": prior_checks,
        "last_check": deepcopy(dict(initial_check_result)),
        "last_check_turn_index": -1,
        "commit_turn_index": -1,
    }
    tools = _scientific_code_tools(
        allow_current_source_run=bool(parent_draft) and allow_current_source_run,
        allow_dependency_handoff=allow_dependency_handoff,
        context_documents_available=True,
        script_execution_available=resolved_session_dir is not None,
        research_sources_available=research_sources is not None,
        research_source_discovery_available=research_source_discovery is not None,
        research_repository_acquisition_available=bool(
            research_source_discovery is not None
            and research_source_discovery.descriptor().get("repository_snapshot_acquisition_allowed") is True
        ),
    )
    research_source_refs = prior_research_source_refs
    if resolved_session_dir is not None:
        tools = (*tools, workspace_history_tool())

    def execute_checked_draft(
        draft: Mapping[str, Any],
        *,
        source_changed: bool,
        current_source_reexecuted: bool,
        turn_index: int,
    ) -> ClientToolExecutionResult:
        raw = check_candidate(deepcopy(dict(draft)))
        if not isinstance(raw, Mapping):
            raise ClientToolInputError("scientific sandbox returned a non-object result")
        check = deepcopy(dict(raw))
        observed_hash = str(check.get("code_draft_hash", "") or "")
        if observed_hash != state["code_draft_hash"]:
            raise ClientToolInputError(
                "scientific sandbox result is not bound to the current candidate hash"
            )
        state["checks"] += 1
        state["last_check"] = check
        state["last_check_turn_index"] = turn_index
        accepted = check.get("accepted") is True
        disposition = str(
            check.get("source_iteration_disposition", "") or ""
        ).strip()
        if not disposition:
            disposition = (
                "accepted" if accepted else SCIENTIFIC_SOURCE_REVISE_CURRENT
            )
            check["source_iteration_disposition"] = disposition
        if disposition not in {
            "accepted",
            SCIENTIFIC_SOURCE_REVISE_CURRENT,
            SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER,
        }:
            raise ClientToolInputError(
                "scientific sandbox returned an unsupported source iteration "
                "disposition"
            )
        if accepted != (disposition == "accepted"):
            raise ClientToolInputError(
                "scientific sandbox acceptance and source iteration disposition "
                "disagree"
            )
        if disposition == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER:
            source_owner = check.get("source_owner", {})
            if not (
                isinstance(source_owner, Mapping)
                and str(source_owner.get("owner_subsystem", "") or "").strip()
                and str(source_owner.get("source_manifest_id", "") or "").strip()
                and str(source_owner.get("source_manifest_hash", "") or "").strip()
                and isinstance(source_owner.get("artifact_ids"), Sequence)
                and not isinstance(source_owner.get("artifact_ids"), (str, bytes))
                and source_owner.get("artifact_ids")
                and isinstance(source_owner.get("artifact_hashes"), Mapping)
                and all(
                    str(
                        source_owner["artifact_hashes"].get(artifact_id, "")
                        or ""
                    ).strip()
                    for artifact_id in source_owner["artifact_ids"]
                )
            ):
                raise ClientToolInputError(
                    "dependency-owner disposition requires bound source owner refs"
                )
        return ClientToolExecutionResult(
            content=model_observation({
                **check,
                "ok": accepted,
                "changed": source_changed,
                "current_source_reexecuted": current_source_reexecuted,
                "checks": state["checks"],
                "source_updates": state["source_updates"],
                "execution_evidence_status": (
                    "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE"
                ),
            }),
            is_error=not accepted,
            state_changed=True,
            observation_key="scientific-submission:"
            + stable_hash(
                {
                    "code_draft_hash": state["code_draft_hash"],
                    "check": check,
                    "current_source_reexecuted": current_source_reexecuted,
                }
            ),
        )

    def store_model_source(
        draft: Mapping[str, Any],
        *,
        source_action: str,
        edit_metadata: Mapping[str, Any] | None = None,
    ) -> ClientToolExecutionResult:
        draft = _complete_code_draft(draft)
        draft_hash = stable_hash(draft)
        if draft_hash == state["code_draft_hash"]:
            raise ClientToolInputError(
                "byte-identical scientific source is already current"
            )
        if draft_hash in observed_draft_hashes:
            raise ClientToolInputError(
                "byte-identical scientific source was previously executed"
            )
        state["code_draft"], state["code_draft_hash"] = draft, draft_hash
        state["source_updates"] += 1
        return ClientToolExecutionResult(
            content={
                "ok": True,
                "source_updated": True,
                "source_action": source_action,
                "code_draft_hash": draft_hash,
                "project_hash": scientific_project_hash(
                    language=str(draft["language"]),
                    code=str(draft["code"]),
                    project_files=draft.get("project_files", []),
                ),
                "files": _scientific_project_manifest(draft),
                "source_updates": state["source_updates"],
                "execution_required": True,
                "instruction": (
                    "Continue editing if needed, then call "
                    "run_current_scientific_source to execute these exact bytes."
                ),
                **(
                    {"edit_metadata": dict(edit_metadata)}
                    if edit_metadata
                    else {}
                ),
            },
            state_changed=True,
            observation_key="scientific-source-update:"
            + stable_hash(
                {
                    "code_draft_hash": draft_hash,
                    "source_action": source_action,
                    "source_updates": state["source_updates"],
                }
            ),
        )

    def execute_tool(call, context):
        tool_input = dict(call.input)
        if call.name == NATIVE_PROJECT_TOOL and native_project is not None:
            result = native_project.execute(tool_input)
            research_source_refs.append({
                "tool": NATIVE_PROJECT_TOOL, "path": result.content["receipt_path"],
                "sha256": result.content["receipt_sha256"],
                "environment_identity": native_project.identity_hash,
            })
            return result
        if call.name in {
            RESEARCH_SOURCE_LIST_TOOL,
            RESEARCH_SOURCE_SEARCH_TOOL,
            RESEARCH_SOURCE_READ_TOOL,
        }:
            assert research_sources is not None
            try:
                observation, source_ref = execute_research_source_client_tool(
                    research_sources, tool_name=call.name, tool_input=tool_input
                )
            except ValueError as exc:
                raise ClientToolInputError(str(exc)) from exc
            research_source_refs.append(source_ref)
            return ClientToolExecutionResult(
                content=observation,
                observation_key=call.name + ":" + stable_hash(source_ref),
            )
        if call.name in {RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL, RESEARCH_SOURCE_DISCOVERY_READ_TOOL, RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL}:
            assert research_source_discovery is not None
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
                research_source_refs.append(source_ref)
            return ClientToolExecutionResult(
                content=observation,
                is_error=is_error,
                observation_key=call.name + ":" + stable_hash(source_ref or observation),
            )
        if call.name == SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL:
            if set(tool_input) != {"imports"}:
                raise ClientToolInputError(
                    "import_research_source_files requires one imports array"
                )
            current = deepcopy(dict(state["code_draft"]))
            if not current:
                raise ClientToolInputError(
                    "import_research_source_files requires an existing "
                    "scientific source project"
                )
            raw_imports = tool_input["imports"]
            if (
                not isinstance(raw_imports, list)
                or not raw_imports
                or len(raw_imports) > MAX_SCIENTIFIC_PROJECT_FILES
            ):
                raise ClientToolInputError(
                    "imports must be a nonempty bounded array"
                )
            required_fields = {
                "source_origin", "source_id", "revision", "source_path",
                "expected_content_sha256", "project_path",
            }
            imports = []
            project_paths: set[str] = set()
            for index, raw_import in enumerate(raw_imports):
                if not isinstance(raw_import, Mapping) or set(raw_import) != required_fields:
                    raise ClientToolInputError(
                        f"import index {index} requires source_origin, source_id, "
                        "revision, source_path, expected_content_sha256, and project_path"
                    )
                row = {
                    key: str(raw_import[key] or "").strip()
                    for key in required_fields
                }
                row["expected_content_sha256"] = row[
                    "expected_content_sha256"
                ].lower()
                if (
                    any(not row[key] for key in required_fields)
                    or row["source_origin"] not in {
                        "frozen_snapshot", "discovered_repository",
                    }
                    or len(row["expected_content_sha256"]) != 64
                    or any(
                        character not in "0123456789abcdef"
                        for character in row["expected_content_sha256"]
                    )
                ):
                    raise ClientToolInputError(
                        f"import index {index} has an invalid origin, identity, or SHA-256"
                    )
                if row["project_path"] in project_paths:
                    raise ClientToolInputError(
                        "imports contain duplicate project path: "
                        + row["project_path"]
                    )
                project_paths.add(row["project_path"])
                if row["source_origin"] == "frozen_snapshot":
                    if research_sources is None:
                        raise ClientToolInputError(
                            f"import index {index} requires a frozen source snapshot"
                        )
                    try:
                        document = research_sources.document(row["source_id"])
                    except ValueError as exc:
                        raise ClientToolInputError(str(exc)) from exc
                    if document.file_mode == "120000":
                        raise ClientToolInputError(
                            f"import index {index} is a repository symlink; preserve "
                            "it in the exact replication workspace"
                        )
                    if (
                        row["revision"] != research_sources.snapshot_hash
                        or row["source_path"] != document.relative_path
                        or row["expected_content_sha256"] != document.sha256
                        or document.content_mode != "text"
                    ):
                        raise ClientToolInputError(
                            f"import index {index} does not match one exact UTF-8 "
                            "frozen source document identity"
                        )
                    inspected = next(
                        (
                            ref
                            for ref in reversed(research_source_refs)
                            if ref.get("snapshot_hash") == row["revision"]
                            and (
                                (
                                    ref.get("document_id") == row["source_id"]
                                    and ref.get("sha256")
                                    == row["expected_content_sha256"]
                                )
                                or any(
                                    item.get("document_id") == row["source_id"]
                                    and item.get("sha256")
                                    == row["expected_content_sha256"]
                                    for item in (
                                        list(ref.get("entries", []) or [])
                                        + list(ref.get("hits", []) or [])
                                    )
                                    if isinstance(item, Mapping)
                                )
                            )
                        ),
                        None,
                    )
                    if inspected is None:
                        raise ClientToolInputError(
                            f"import index {index} requires a prior exact frozen "
                            "source identity observation"
                        )
                else:
                    if research_source_discovery is None:
                        raise ClientToolInputError(
                            f"import index {index} requires public source discovery"
                        )
                    inspected = next(
                        (
                            ref
                            for ref in reversed(research_source_refs)
                            if ref.get("tool") == RESEARCH_SOURCE_DISCOVERY_READ_TOOL
                            and ref.get("source_kind") == "repository"
                            and str(ref.get("source_handle", "") or "")
                            == row["source_id"]
                            and str(ref.get("revision", "") or "") == row["revision"]
                            and str(ref.get("path", "") or "") == row["source_path"]
                            and str(ref.get("content_sha256", "") or "").lower()
                            == row["expected_content_sha256"]
                        ),
                        None,
                    )
                    if (
                        inspected is None
                        or inspected.get("content_truncated") is not False
                    ):
                        raise ClientToolInputError(
                            f"import index {index} requires a prior complete read of "
                            "the exact repository identity and content SHA-256"
                        )
                row["source_observation_ref"] = stable_hash(inspected)
                imports.append(row)
            frozen_errors = (
                research_sources.identity_errors()
                if research_sources is not None
                and any(row["source_origin"] == "frozen_snapshot" for row in imports)
                else []
            )
            if frozen_errors:
                raise ClientToolInputError(
                    "frozen research source snapshot changed before import: "
                    + frozen_errors[0]
                )
            imported_files = []
            for index, row in enumerate(imports):
                if row["source_origin"] == "frozen_snapshot":
                    assert research_sources is not None
                    document = research_sources.document(row["source_id"])
                    try:
                        content = research_sources.document_path(
                            document.document_id
                        ).read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError, ValueError) as exc:
                        raise ClientToolInputError(
                            f"frozen source import index {index} is unreadable: {exc}"
                        ) from exc
                    actual_sha256 = hashlib.sha256(
                        content.encode("utf-8")
                    ).hexdigest()
                    if actual_sha256 != row["expected_content_sha256"]:
                        raise ClientToolInputError(
                            f"frozen source import index {index} changed after "
                            "identity validation"
                        )
                    imported_files.append({
                        **row,
                        "content": content,
                        "provider": "frozen_snapshot",
                        "citation_ref": "",
                    })
                    continue
                assert research_source_discovery is not None
                try:
                    observation, refreshed_ref, is_error = (
                        execute_research_source_discovery_client_tool(
                            research_source_discovery,
                            tool_name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                            tool_input={
                                "source_handle": row["source_id"],
                                "revision": row["revision"],
                                "path": row["source_path"],
                            },
                        )
                    )
                except ResearchSourceDiscoveryInputError as exc:
                    raise ClientToolInputError(str(exc)) from exc
                if is_error:
                    return ClientToolExecutionResult(
                        content={
                            **dict(observation),
                            "import_index": index,
                            "project_state_changed": False,
                        },
                        is_error=True,
                        observation_key=(
                            SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL
                            + ":"
                            + stable_hash([index, observation])
                        ),
                    )
                content = str(observation.get("content", "") or "")
                actual_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if (
                    observation.get("source_kind") != "repository"
                    or observation.get("content_truncated") is not False
                    or str(observation.get("source_handle", "") or "")
                    != row["source_id"]
                    or str(observation.get("revision", "") or "")
                    != row["revision"]
                    or str(observation.get("path", "") or "")
                    != row["source_path"]
                    or str(observation.get("content_sha256", "") or "").lower()
                    != row["expected_content_sha256"]
                    or actual_sha256 != row["expected_content_sha256"]
                ):
                    raise ClientToolInputError(
                        f"public repository source at import index {index} changed "
                        "or did not return complete bytes for the inspected identity"
                    )
                imported_files.append({
                    **row,
                    "content": content,
                    "provider": refreshed_ref.get("provider", ""),
                    "citation_ref": refreshed_ref.get("citation_ref", ""),
                })
            rows = [
                deepcopy(dict(row))
                for row in current.get("project_files", []) or []
                if isinstance(row, Mapping)
                and str(row.get("path", "") or "") not in project_paths
            ]
            rows.extend(
                {
                    "path": row["project_path"],
                    "content": row["content"],
                }
                for row in imported_files
            )
            current["project_files"] = rows
            update = store_model_source(
                current,
                source_action="research_source_files_import",
                edit_metadata={
                    "import_count": len(imported_files),
                    "project_paths": sorted(project_paths),
                },
            )
            import_ref = {
                "tool": SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
                "source_kind": "research_source_files",
                "imports": [
                    {
                        "provider": row["provider"],
                        "source_origin": row["source_origin"],
                        "source_id": row["source_id"],
                        "revision": row["revision"],
                        "source_path": row["source_path"],
                        "source_content_sha256": row[
                            "expected_content_sha256"
                        ],
                        "project_path": row["project_path"],
                        "citation_ref": row["citation_ref"],
                        "source_observation_ref": row[
                            "source_observation_ref"
                        ],
                    }
                    for row in imported_files
                ],
                "source_file_count": len(imported_files),
                "resulting_project_hash": update.content["project_hash"],
                "proof_evidence_status": (
                    "RESEARCH_SOURCE_IMPORT_NOT_EXECUTION_OR_PROOF_EVIDENCE"
                ),
            }
            research_source_refs.append(import_ref)
            return replace(
                update,
                content={
                    **dict(update.content),
                    "research_source_import": import_ref,
                    "source_content_omitted": True,
                },
                observation_key=(
                    SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL
                    + ":"
                    + stable_hash(import_ref)
                ),
            )
        if call.name in {
            theory_documents.THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
            theory_documents.THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        }:
            observation, _ = theory_documents.execute_theory_document_client_tool(
                {**context_documents, **observation_documents},
                tool_name=call.name, tool_input=tool_input,
            )
            return ClientToolExecutionResult(content=observation)
        if call.name == SCIENTIFIC_SOURCE_SUBMISSION_TOOL:
            required_fields = {
                "language",
                "execution_profile",
                "dependencies",
                "entrypoint",
                "code",
            }
            if (
                not required_fields.issubset(tool_input)
                or set(tool_input) - required_fields - {"project_files"}
            ):
                raise ClientToolInputError(
                    "submit_scientific_source requires one complete candidate"
                )
            return store_model_source(
                tool_input,
                source_action="complete_source_submission",
            )

        if call.name == SCIENTIFIC_SOURCE_READ_TOOL:
            if (
                not {"line_start", "line_end"}.issubset(tool_input)
                or set(tool_input) - {"path", "line_start", "line_end"}
            ):
                raise ClientToolInputError(
                    "read_current_scientific_source requires line_start and line_end; "
                    "path is optional"
                )
            line_start, line_end = tool_input["line_start"], tool_input["line_end"]
            if (
                isinstance(line_start, bool)
                or isinstance(line_end, bool)
                or not isinstance(line_start, int)
                or not isinstance(line_end, int)
                or line_start < 1
                or line_end < line_start
            ):
                raise ClientToolInputError(
                    "scientific source line range must be positive and ordered"
                )
            draft = deepcopy(dict(state["code_draft"]))
            if not draft:
                raise ClientToolInputError(
                    "no current scientific source exists; author it first"
                )
            main_path = scientific_main_path(str(draft["language"]))
            path = str(tool_input.get("path", "") or main_path).strip()
            if path == main_path:
                source = str(draft["code"])
                source_hash = stable_hash(source)
            else:
                project_rows = {
                    str(row.get("path", "") or ""): row
                    for row in draft.get("project_files", []) or []
                    if isinstance(row, Mapping)
                }
                project_row = project_rows.get(path)
                if project_row is None:
                    raise ClientToolInputError(
                        "scientific project file does not exist: " + path
                    )
                source = str(project_row.get("content", "") or "")
                source_hash = str(project_row.get("content_sha256", "") or "")
            lines = source.splitlines(keepends=True)
            if line_end > len(lines):
                raise ClientToolInputError(
                    f"scientific source has {len(lines)} line(s)"
                )
            content = "".join(lines[line_start - 1 : line_end])
            if len(content) > 55_000:
                raise ClientToolInputError(
                    "selected scientific source range exceeds one observation; read less"
                )
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "path": path,
                    "line_start": line_start,
                    "line_end": line_end,
                    "total_lines": len(lines),
                    "content": content,
                    "source_hash": source_hash,
                    "project_hash": scientific_project_hash(
                        language=str(draft["language"]),
                        code=str(draft["code"]),
                        project_files=draft.get("project_files", []),
                    ),
                    "code_draft_hash": state["code_draft_hash"],
                },
                observation_key="scientific-source-read:"
                + stable_hash(
                    [state["code_draft_hash"], path, line_start, line_end]
                ),
            )

        if call.name == SCIENTIFIC_SOURCE_EDIT_TOOL:
            required_fields = {"old_text", "new_text"}
            optional_fields = {"path", "expected_occurrences"}
            if (
                not required_fields.issubset(tool_input)
                or set(tool_input) - required_fields - optional_fields
            ):
                raise ClientToolInputError(
                    "edit_current_scientific_source requires top-level old_text and "
                    "new_text; path and expected_occurrences are optional"
                )
            current = deepcopy(dict(state["code_draft"]))
            if not current:
                raise ClientToolInputError(
                    "edit_current_scientific_source requires existing source; use "
                    "submit_scientific_source for initial authoring"
                )
            main_path = scientific_main_path(str(current["language"]))
            path = str(tool_input.get("path", "") or main_path).strip()
            project_rows = [
                deepcopy(dict(row))
                for row in current.get("project_files", []) or []
                if isinstance(row, Mapping)
            ]
            if path == main_path:
                source = str(current["code"])
                project_index = None
            else:
                project_index = next(
                    (
                        index
                        for index, row in enumerate(project_rows)
                        if str(row.get("path", "") or "") == path
                    ),
                    None,
                )
                if project_index is None:
                    raise ClientToolInputError(
                        "scientific project file does not exist: " + path
                    )
                source = str(project_rows[project_index].get("content", "") or "")
            edit_input = {
                key: value for key, value in tool_input.items() if key != "path"
            }
            edited_source, edit_records = apply_model_exact_text_edits(
                source,
                edits=[edit_input],
                replacement_key="new_text",
            )
            if project_index is None:
                current["code"] = edited_source
            else:
                project_rows[project_index]["content"] = edited_source
                project_rows[project_index].pop("content_sha256", None)
                current["project_files"] = project_rows
            return store_model_source(
                current,
                source_action="atomic_exact_text_edits",
                edit_metadata={
                    "path": path,
                    "n_edits": len(edit_records),
                    "edits": edit_records,
                },
            )

        if call.name == SCIENTIFIC_PROJECT_FILE_WRITE_TOOL:
            if set(tool_input) != {"path", "content"}:
                raise ClientToolInputError(
                    "write_scientific_project_file requires path and content"
                )
            current = deepcopy(dict(state["code_draft"]))
            if not current:
                raise ClientToolInputError(
                    "write_scientific_project_file requires existing source; use "
                    "submit_scientific_source for initial authoring"
                )
            path = str(tool_input.get("path", "") or "").strip()
            rows = [
                deepcopy(dict(row))
                for row in current.get("project_files", []) or []
                if isinstance(row, Mapping)
                and str(row.get("path", "") or "") != path
            ]
            rows.append({"path": path, "content": str(tool_input["content"])})
            current["project_files"] = rows
            return store_model_source(
                current,
                source_action="complete_project_file_write",
                edit_metadata={"path": path},
            )

        if call.name == SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL:
            if set(tool_input) != {"path"}:
                raise ClientToolInputError(
                    "remove_scientific_project_file requires path"
                )
            current = deepcopy(dict(state["code_draft"]))
            if not current:
                raise ClientToolInputError(
                    "remove_scientific_project_file requires existing source"
                )
            path = str(tool_input.get("path", "") or "").strip()
            rows = [
                deepcopy(dict(row))
                for row in current.get("project_files", []) or []
                if isinstance(row, Mapping)
            ]
            kept = [
                row for row in rows if str(row.get("path", "") or "") != path
            ]
            if len(kept) == len(rows):
                raise ClientToolInputError(
                    "scientific project file does not exist: " + path
                )
            current["project_files"] = kept
            return store_model_source(
                current,
                source_action="project_file_remove",
                edit_metadata={"path": path},
            )

        if call.name == SCIENTIFIC_SOURCE_COMMIT_TOOL:
            if tool_input:
                raise ClientToolInputError(
                    "commit_scientific_source does not accept arguments"
                )
            draft = state["code_draft"]
            check = state["last_check"]
            draft_hash = str(state["code_draft_hash"] or "")
            if not draft or not draft_hash:
                raise ClientToolInputError(
                    "no executed scientific source is available to commit"
                )
            if (
                not isinstance(check, Mapping)
                or check.get("accepted") is not True
                or str(check.get("source_iteration_disposition", "") or "")
                != "accepted"
                or str(check.get("code_draft_hash", "") or "") != draft_hash
            ):
                raise ClientToolInputError(
                    "the current scientific source has no accepted hash-bound "
                    "sandbox observation"
                )
            if int(state["last_check_turn_index"]) >= context.turn_index:
                raise ClientToolInputError(
                    "inspect the accepted sandbox observation in a subsequent model "
                    "turn before committing the current source"
                )
            state["commit_turn_index"] = context.turn_index
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "committed": True,
                    "code_draft_hash": draft_hash,
                    "check_result_hash": stable_hash(check),
                    "execution_evidence_status": (
                        "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=False,
                terminal=True,
                terminal_payload={
                    "code_draft": deepcopy(dict(draft)),
                    "code_draft_hash": draft_hash,
                    "check_result": deepcopy(dict(check)),
                },
                observation_key="scientific-commit:"
                + stable_hash([draft_hash, stable_hash(check)]),
            )

        if call.name == SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL:
            if "reason" not in tool_input or set(tool_input) - {"reason", "script_path", "seed", "replicates"} or not str(
                tool_input.get("reason", "") or ""
            ).strip():
                raise ClientToolInputError(
                    "run_current_scientific_source requires a reason; script_path, seed and replicates are optional for exploratory scripts"
                )
            draft = deepcopy(dict(state["code_draft"]))
            draft_hash = str(state["code_draft_hash"] or "")
            if not draft or not draft_hash:
                raise ClientToolInputError(
                    "run_current_scientific_source requires current source; use "
                    "submit_scientific_source for initial authoring"
                )
            if "script_path" in tool_input:
                if resolved_session_dir is None:
                    raise ClientToolInputError("project script execution requires a persistent workspace")
                script_path = tool_input["script_path"]
                seed, replicates = tool_input.get("seed", 0), tool_input.get("replicates", 1)
                if not isinstance(script_path, str) or not script_path or type(seed) is not int or type(replicates) is not int or replicates < 1:
                    raise ClientToolInputError("script_path must be nonempty, seed an integer, and replicates a positive integer")
                resolved_session_dir.mkdir(parents=True, exist_ok=True)
                execution = execute_scientific_sandbox(
                    sandbox_dir=Path(tempfile.mkdtemp(prefix="project-script-", dir=resolved_session_dir)),
                    artifact_id=artifact_id, language=draft["language"], code=draft["code"],
                    project_files=draft.get("project_files", []), dependencies=draft["dependencies"],
                    seed=seed, replicates=replicates, timeout_s=20, entrypoint=None, script_path=script_path,
                )
                return ClientToolExecutionResult(
                    content=model_observation({
                        **execution.to_json(), "script_path": script_path, "code_draft_hash": draft_hash,
                        "runtime_edited_source": False,
                        "execution_evidence_status": "EXPLORATORY_PROJECT_SCRIPT_NOT_RELEASE_OR_CONFIRMATION",
                    }, retain_document=True),
                    is_error=execution.status != "EXECUTED",
                    state_changed=execution.execution_attempted,
                    observation_key="project-script:" + stable_hash([draft_hash, tool_input, execution.request_hash, execution.result_hash]),
                )
            if set(tool_input) != {"reason"}:
                raise ClientToolInputError("seed and replicates overrides require an exploratory script_path")
            dependency_reexecution = bool(
                allow_current_source_run
                and not resumed_checkpoint_id
                and parent_hash
                and draft_hash == parent_hash
                and not state["dependency_parent_reexecuted"]
            )
            if draft_hash in observed_draft_hashes and not dependency_reexecution:
                raise ClientToolInputError(
                    "the exact current scientific source was already executed in "
                    "the current dependency environment"
                )
            state["current_source_run_requests"] += 1
            if dependency_reexecution:
                state["dependency_parent_reexecuted"] = True
            result = execute_checked_draft(
                draft,
                source_changed=draft_hash != parent_hash,
                current_source_reexecuted=dependency_reexecution,
                turn_index=context.turn_index,
            )
            observed_draft_hashes.add(draft_hash)
            return result

        if call.name == SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL:
            if not allow_dependency_handoff:
                raise ClientToolInputError(
                    "bound dependency handoff is unavailable in this workspace"
                )
            if set(tool_input) != {"reason"} or not str(
                tool_input.get("reason", "") or ""
            ).strip():
                raise ClientToolInputError(
                    "report_bound_dependency_failure requires one nonempty reason"
                )
            check = deepcopy(dict(state["last_check"]))
            prototype = check.get("prototype", {})
            source_owner = check.get("source_owner", {})
            runtime_failure_ids = (
                list(prototype.get("estimator_runtime_failure_ids", []) or [])
                if isinstance(prototype, Mapping)
                else []
            )
            binding_errors = (
                list(prototype.get("estimator_binding_errors", []) or [])
                if isinstance(prototype, Mapping)
                else []
            )
            if not runtime_failure_ids and not binding_errors:
                raise ClientToolInputError(
                    "no exact bound dependency failure is present in the latest "
                    "sandbox observation"
                )
            if not (
                isinstance(source_owner, Mapping)
                and str(source_owner.get("owner_subsystem", "") or "").strip()
                and str(source_owner.get("source_manifest_id", "") or "").strip()
                and str(source_owner.get("source_manifest_hash", "") or "").strip()
                and source_owner.get("artifact_ids")
                and isinstance(source_owner.get("artifact_hashes"), Mapping)
            ):
                raise ClientToolInputError(
                    "latest sandbox observation has no exact dependency source refs"
                )
            report = {
                "artifact_kind": "ModelSelectedScientificDependencyHandoff",
                "model_selected": True,
                "reason": str(tool_input["reason"]).strip(),
                "source_manifest_id": source_owner["source_manifest_id"],
                "source_manifest_hash": source_owner["source_manifest_hash"],
                "runtime_edited_source": False,
                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            }
            check["source_iteration_disposition"] = (
                SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
            )
            check["dependency_failure_report"] = report
            state["last_check"] = check
            return ClientToolExecutionResult(
                content={
                    "ok": False,
                    "accepted": False,
                    "source_iteration_disposition": (
                        SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
                    ),
                    "source_owner": deepcopy(dict(source_owner)),
                    "dependency_failure_report": report,
                },
                is_error=False,
                state_changed=True,
                terminal=True,
                terminal_payload={
                    "code_draft": deepcopy(dict(state["code_draft"])),
                    "code_draft_hash": state["code_draft_hash"],
                    "check_result": check,
                },
                observation_key="scientific-dependency-handoff:"
                + stable_hash(report),
            )

        raise ClientToolInputError("unsupported scientific code workspace tool")

    root_authorization_fingerprint = client_tool_authorization_fingerprint(request_metadata) or stable_hash(
        ["scientific", artifact_id, research_sources.descriptor() if research_sources else {},
         research_source_discovery.descriptor() if research_source_discovery else {}])
    native_project = configured_native_project(
        resolved_session_dir, owner=f"scientific:{artifact_id}",
        authorization=stable_hash([root_authorization_fingerprint,
            research_sources.descriptor() if research_sources else {},
            research_source_discovery.descriptor() if research_source_discovery else {}]),
        source_resolver=getattr(research_source_discovery, "acquired_repository_snapshot", None),
    )
    if any(row.get("tool") == NATIVE_PROJECT_TOOL and (
        native_project is None or row.get("environment_identity") != native_project.identity_hash
    ) for row in research_source_refs):
        raise ValueError("continued native scientific project requires its exact environment")
    if native_project is not None:
        tools = (*tools, native_project.tool())
        root_authorization_fingerprint = stable_hash(
            [root_authorization_fingerprint, native_project.descriptor()])
    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=(
            {
                "role": "user",
                "content": (
                    user_prompt
                    + f"\n\nThis retained source session has up to {max_turns} model/tool turns; retrieval, authoring, execution, and explicit commit share that allowance."
                    + "\n\nRetain observed source hashes and sandbox results. Do "
                    "not resubmit a previously observed byte-identical candidate. "
                    "The current artifact is a Python/R project: use path-aware read, "
                    "exact edit, support-file write, or support-file remove tools as "
                    "needed. Source changes do not execute. You may make "
                    "several one-replacement edit calls, then call "
                    "run_current_scientific_source only when "
                    "you want raw sandbox feedback. Commit remains separate and "
                    "requires an accepted execution observation."
                )
                + (
                    "\n\nNo scientific source exists yet. Author the complete "
                    "candidate with submit_scientific_source. Submission and exact "
                    "edits only change model-owned bytes. Continue editing as needed, "
                    "then explicitly call run_current_scientific_source when the "
                    "current source is ready for sandbox execution."
                    if not parent_draft
                    else "\n\nCurrent source artifact:\n"
                    + _compact_json({
                        **{
                            key: value
                            for key, value in parent_draft.items()
                            if key not in {"code", "project_files"}
                        },
                        "path": scientific_main_path(parent_draft["language"]),
                        "source_hash": stable_hash(parent_draft["code"]),
                        "project_hash": scientific_project_hash(
                            language=parent_draft["language"],
                            code=parent_draft["code"],
                            project_files=parent_draft.get("project_files", []),
                        ),
                        "files": _scientific_project_manifest(parent_draft),
                        "code_draft_hash": parent_hash,
                        "line_count": len(str(parent_draft["code"]).splitlines()),
                        "character_count": len(str(parent_draft["code"])),
                        "content_transport": SCIENTIFIC_SOURCE_READ_TOOL,
                    })
                )
                + "\n\nInitial workspace observation:\n"
                + _compact_json(initial_model_observation)
                + "\nLong permitted observations are exact read-only documents. Use read_theory_document or search_theory_documents for their referenced paths; they are separate from editable project files."
                + (
                    "\n\nPublic research source snapshot:\n"
                    + _compact_json(research_sources.descriptor())
                    + "\nUse list_research_source_directory to navigate an unfamiliar "
                    "frozen project before searching or reading exact files."
                    if research_sources is not None
                    else ""
                )
                + (
                    "\n\nPublic source discovery context:\n" + _compact_json({
                        "provider": research_source_discovery.descriptor()
                        if research_source_discovery is not None else {},
                        "previous_refs": prior_research_source_refs,
                    })
                    if research_source_discovery is not None or prior_research_source_refs else ""
                )
                + (
                    "\n\nWhen exact upstream Python/R files or UTF-8 project assets "
                    "should be reused, first "
                    "observe their frozen identity or completely read the discovered "
                    "repository bytes, then use import_research_source_files. The "
                    "result becomes part of the current model-owned project and still "
                    "requires your inspection, execution, and independent review."
                    if research_sources is not None
                    or research_source_discovery is not None
                    else ""
                )
                + (
                    "\n\nThis is a hash-bound continuation of checkpoint "
                    + resumed_checkpoint_id
                    + ". Continue from the exact current source and observation; "
                    "do not regenerate the planning envelope."
                    if resumed_checkpoint_id
                    else ""
                )
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
            CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: (
                root_authorization_fingerprint
            ),
            "model_tier": model_tier,
            "artifact_id": artifact_id,
            "parent_code_draft_hash": parent_hash,
            "workspace_operation": workspace_operation,
            "resumed_from_checkpoint_id": resumed_checkpoint_id,
        },
    )
    resumed_client_tool_session_ref: dict[str, Any] = {}
    resumed_client_tool_context_window: dict[str, Any] = {}
    prior_client_tool_session_ref = resumed_checkpoint.get(
        "client_tool_session_ref", {}
    )
    if prior_client_tool_session_ref:
        if not isinstance(prior_client_tool_session_ref, Mapping):
            raise ValueError("scientific client-tool session reference is malformed")
        if resolved_session_dir is None:
            raise ValueError(
                "scientific client-tool session resume requires a persistent directory"
            )
        request, resumed_client_tool_context_window = (
            resume_client_tool_session_from_checkpoint(
                prior_client_tool_session_ref,
                session_dir=resolved_session_dir,
                session_id=f"scientific:{artifact_id}",
                checkpoint_identity=resumed_checkpoint_id,
                request=request,
                replay_recent_tool_rounds=CLIENT_TOOL_RECENT_HISTORY_ROUNDS,
            )
        )
        resumed_client_tool_session_ref = deepcopy(
            dict(prior_client_tool_session_ref)
        )

    def on_error(exc: ClientToolLoopError) -> ScientificCodeWorkspaceResult:
        client_tool_session_ref = persist_client_tool_session(
            session_dir=resolved_session_dir,
            session_id=f"scientific:{artifact_id}",
            request=request,
            messages=exc.messages,
            observation_refs=exc.observation_refs,
        )
        last_check = deepcopy(dict(state["last_check"]))
        current_draft = deepcopy(dict(state["code_draft"]))
        current_draft_hash = str(state["code_draft_hash"] or "")
        last_check_bound = bool(
            current_draft
            and current_draft_hash
            and str(last_check.get("code_draft_hash", "") or "")
            == current_draft_hash
            and current_draft_hash in observed_draft_hashes
        )
        checkpoint_body = {
            "schema_version": 3,
            "artifact_kind": SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_KIND,
            "artifact_id": artifact_id,
            "workspace_operation": workspace_operation,
            "parent_code_draft_hash": parent_hash,
            "current_code_draft_hash": current_draft_hash,
            "current_code_draft": current_draft,
            "observed_code_draft_hashes": sorted(observed_draft_hashes),
            "current_source_executed": last_check_bound,
            "source_updates": state["source_updates"],
            "checks": state["checks"],
            "segment_start_source_updates": prior_source_updates,
            "segment_start_checks": prior_checks,
            "last_check": last_check,
            "last_check_hash": stable_hash(last_check),
            "observation_document_refs": deepcopy(observation_document_refs),
            "research_source_refs": deepcopy(research_source_refs),
            "resumed_from_checkpoint_id": resumed_checkpoint_id,
            "resumed_from_client_tool_session_ref": deepcopy(
                resumed_client_tool_session_ref
            ),
            "client_tool_checkpoint_window": deepcopy(
                resumed_client_tool_context_window
            ),
            "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
            **(
                {"client_tool_session_ref": client_tool_session_ref}
                if client_tool_session_ref
                else {}
            ),
            "resumable": bool(
                current_draft
                and (
                    state["source_updates"] > prior_source_updates
                    or state["checks"] > prior_checks
                )
            ),
            "accepted": False,
            "model_owned_source": True,
            "runtime_edited_source": False,
            "proof_evidence_status": (
                "SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
            ),
        }
        checkpoint = {
            **checkpoint_body,
            "checkpoint_id": (
                "scientific_code_workspace_checkpoint:"
                + stable_hash(checkpoint_body)[:20]
            ),
        }
        raise PacketValidationError(
            validation_label="LLM scientific code workspace",
            attempts=exc.turns,
            errors=[exc.reason],
            history=theory_documents.workspace_evidence_history(
                exc.history
            ),
            recovery_checkpoint=checkpoint,
        ) from exc

    def on_success(loop: ClientToolLoopResult) -> ScientificCodeWorkspaceResult:
        client_tool_session_ref = persist_client_tool_session(
            session_dir=resolved_session_dir,
            session_id=f"scientific:{artifact_id}",
            request=request,
            messages=loop.messages,
            observation_refs=loop.observation_refs,
        )
        terminal = dict(loop.terminal_payload)
        draft = _complete_code_draft(terminal.get("code_draft", {}))
        check = dict(terminal.get("check_result", {}))
        draft_hash = stable_hash(draft)
        disposition = str(
            check.get("source_iteration_disposition", "") or ""
        ).strip()
        if (
            terminal.get("code_draft_hash") != draft_hash
            or check.get("code_draft_hash") != draft_hash
            or disposition
            not in {"accepted", SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER}
            or (check.get("accepted") is True) != (disposition == "accepted")
        ):
            raise PacketValidationError(
                validation_label="LLM scientific code workspace",
                attempts=loop.turns,
                errors=[
                    "terminal payload is not bound to an accepted candidate or exact "
                    "dependency source owner"
                ],
                history=theory_documents.workspace_evidence_history(
                    loop.history
                ),
            )

        evidence = {
            "schema_version": 1,
            "artifact_kind": "ScientificCodeWorkspaceResult",
            "artifact_id": artifact_id,
            "transport": "native_client_tools",
            "workspace_operation": workspace_operation,
            "resumed_from_checkpoint_id": resumed_checkpoint_id,
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
            "parent_code_draft_hash": parent_hash,
            "initial_check_result_hash": stable_hash(dict(initial_check_result)),
            "initial_check_accepted": initial_check_result.get("accepted") is True,
            "submitted_code_draft_hash": draft_hash,
            "terminal_check_result_hash": stable_hash(check),
            "observation_document_refs": deepcopy(observation_document_refs),
            "source_changed": draft_hash != parent_hash,
            "current_source_run_requested": bool(
                state["current_source_run_requests"]
            ),
            "current_source_run_requests": state[
                "current_source_run_requests"
            ],
            "source_updates": state["source_updates"],
            "sandbox_checks": state["checks"],
            "submit_and_execute_atomic": False,
            "source_mutation_and_execution_separated": True,
            "explicit_model_commit_required": True,
            "model_commit_after_observation": bool(
                state["commit_turn_index"] >= 0 and (state["last_check_turn_index"] >= 0 or initial_check_hash == parent_hash)
            ),
            "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "provider": loop.provider,
            "model": loop.model,
            "model_tier": model_tier,
            "provider_usage": dict(loop.provider_usage),
            "history": theory_documents.workspace_evidence_history(
                loop.history
            ),
            "research_source_snapshot": (
                research_sources.descriptor() if research_sources is not None else {}
            ),
            "public_research_source_discovery": dict(research_source_discovery.descriptor())
            if research_source_discovery is not None else {},
            "research_source_refs": deepcopy(research_source_refs),
            "research_source_ref_fingerprint": stable_hash(research_source_refs),
            "transcript_fingerprint": loop.transcript_fingerprint,
            "model_owned_source": True,
            "runtime_edited_source": False,
            "accepted": check.get("accepted") is True,
            "source_iteration_disposition": disposition,
            "source_owner": deepcopy(dict(check.get("source_owner", {})))
            if isinstance(check.get("source_owner", {}), Mapping)
            else {},
            "proof_evidence_status": "SCIENTIFIC_CODE_EXECUTION_NOT_PROOF_EVIDENCE",
        }
        return ScientificCodeWorkspaceResult(
            code_draft=draft,
            check_result=check,
            evidence=evidence,
        )

    return PreparedClientToolWorkspace(
        request=request,
        execute_tool=execute_tool,
        max_turns=max_turns,
        max_tool_calls=max_turns,
        max_no_progress_turns=max_no_progress_turns,
        session_dir=resolved_session_dir,
        session_id=f"scientific:{artifact_id}",
        on_success=on_success,
        on_error=on_error,
        initial_context={
            "artifact_id": artifact_id,
            "workspace_operation": workspace_operation,
            "current_project_files": _scientific_project_manifest(parent_draft) if parent_draft else [],
            "initial_observation": deepcopy(initial_model_observation),
            "read_only_documents": [{"path": path, "sha256": hashlib.sha256(content.encode()).hexdigest(),
                                     "byte_size": len(content.encode())}
                                    for path, content in sorted(context_documents.items())],
            "research_source_snapshot": research_sources.descriptor() if research_sources else {},
            "public_source_discovery": research_source_discovery.descriptor() if research_source_discovery else {},
        },
    )


def _complete_code_draft(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ClientToolInputError("scientific code candidate must be an object")
    language = normalized_generated_code_language(value.get("language"))
    execution_profile = normalized_generated_code_profile(
        value.get("execution_profile"),
        language=language,
    )
    entrypoint = str(value.get("entrypoint", "") or "").strip()
    code = str(value.get("code", "") or "")
    dependencies = value.get("dependencies", [])
    if not isinstance(dependencies, Sequence) or isinstance(
        dependencies, (str, bytes)
    ):
        raise ClientToolInputError("dependencies must be an array")
    normalized_dependencies = list(
        normalized_scientific_dependencies(dependencies, language=language)
    )
    try:
        project_files = [
            project_file.to_json()
            for project_file in normalized_scientific_project_files(
                value.get("project_files", []),
                language=language,
            )
        ]
    except ValueError as exc:
        raise ClientToolInputError(str(exc)) from exc
    draft = {
        "language": language,
        "execution_profile": execution_profile,
        "dependencies": normalized_dependencies,
        "entrypoint": entrypoint,
        "code": code,
    }
    if project_files:
        draft["project_files"] = project_files
    contract_errors = generated_code_execution_contract_errors(draft)
    if contract_errors:
        raise ClientToolInputError("; ".join(contract_errors))
    return draft


def _scientific_code_tools(
    *,
    allow_current_source_run: bool,
    allow_dependency_handoff: bool,
    context_documents_available: bool = False,
    script_execution_available: bool = False,
    research_sources_available: bool = False,
    research_source_discovery_available: bool = False,
    research_repository_acquisition_available: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    edit_schema = deepcopy(model_exact_text_edit_json_schema())
    edit_schema["properties"]["path"] = {
        "type": "string",
        "description": (
            "Project-relative file path. Omit to edit main.py or main.R."
        ),
    }
    tools = [
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            description=(
                "Store one complete model-authored Python/R candidate without "
                "executing it. Continue editing if useful, then call "
                "run_current_scientific_source for raw sandbox feedback. Python allows "
                + ", ".join(PYTHON_SCIENTIFIC_DEPENDENCIES)
                + "; R allows "
                + ", ".join(R_SCIENTIFIC_DEPENDENCIES)
                + "."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "language",
                    "execution_profile",
                    "dependencies",
                    "entrypoint",
                    "code",
                ],
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": list(SCIENTIFIC_SANDBOX_LANGUAGES),
                    },
                    "execution_profile": {
                        "type": "string",
                        "enum": list(SCIENTIFIC_SANDBOX_PROFILES),
                    },
                    "dependencies": {
                        "type": "array",
                        "description": (
                            "For language=python, use only: "
                            + ", ".join(PYTHON_SCIENTIFIC_DEPENDENCIES)
                            + ". For language=r, use only: "
                            + ", ".join(R_SCIENTIFIC_DEPENDENCIES)
                            + ". Use [] when the source imports none of them."
                        ),
                        "items": {
                            "type": "string",
                            "enum": list(_SCIENTIFIC_PACKAGES),
                        },
                        "uniqueItems": True,
                    },
                    "entrypoint": {
                        "type": "string",
                        "enum": ["run_sandbox"],
                    },
                    "code": {"type": "string"},
                    "project_files": scientific_project_files_json_schema(),
                },
            },
            terminal=False,
        ),
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_EDIT_TOOL,
            description=(
                "Apply one exact model-authored replacement to a current Python/R "
                "project file without executing it. Omit path for the main source. "
                "Supply old_text and new_text directly as "
                "top-level strings, not as a JSON-encoded value or edits array. Runtime "
                "never interprets or repairs source; use multiple calls for multiple "
                "replacements and explicitly run the complete result afterward."
            ),
            input_schema=edit_schema,
            terminal=False,
        ),
        ClientToolDefinition(
            name=SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
            description=(
                "Create or replace one complete model-authored UTF-8 project file. "
                "The canonical project-relative path may hold Python/R source, text data, "
                "configuration, or a fixture. This stores bytes without executing them; "
                "only source loaded by the current program is executable."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "content"],
                "properties": {
                    "path": {"type": "string", "minLength": 1},
                    "content": {"type": "string"},
                },
            },
            terminal=False,
        ),
        ClientToolDefinition(
            name=SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
            description=(
                "Remove one current model-authored support file by project-relative "
                "path. The main source cannot be removed. This does not execute code."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["path"],
                "properties": {"path": {"type": "string", "minLength": 1}},
            },
            terminal=False,
        ),
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_READ_TOOL,
            description=(
                "Read an exact line range from a current model-owned UTF-8 project file. "
                "Omit path for the main Python/R source. "
                "The result includes the current source and draft hashes; this tool "
                "never edits or executes source."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["line_start", "line_end"],
                "properties": {
                    "path": {"type": "string", "minLength": 1},
                    "line_start": {"type": "integer", "minimum": 1},
                    "line_end": {"type": "integer", "minimum": 1},
                },
            },
            terminal=False,
        ),
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
            description=(
                "Run the bound execution check for the exact current Python/R project "
                "and return raw output. Source bytes are unchanged. This bound check "
                "can run once per newly authored source hash in this workspace"
                + (
                    "; the unchanged parent may also run once because its bound "
                    "dependency environment changed"
                    if allow_current_source_run
                    else ""
                )
                + "."
                + (" Alternatively, select script_path to run an exact current project file as an ordinary exploratory script, without the run_sandbox ABI. It may import/source the current main file. Globals seed (default 0), replicates (default 1), and empty artifacts are supplied. This uses an isolated fresh process and no confirmation data; its output cannot authorize source release. Omit script_path for the unchanged bound execution check."
                   if script_execution_available else "")
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["reason"],
                "properties": {
                    "reason": {"type": "string"},
                    **({
                        "script_path": {"type": "string", "minLength": 1},
                        "seed": {"type": "integer"},
                        "replicates": {"type": "integer", "minimum": 1},
                    } if script_execution_available else {}),
                },
            },
            terminal=False,
        ),
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_COMMIT_TOOL,
            description=(
                "Commit the exact current scientific source only after a prior model "
                "turn received and inspected its accepted hash-bound sandbox "
                "observation. This tool neither edits nor reruns source."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {},
            },
            terminal=True,
        ),
    ]
    source_tools = [
        *(
            research_source_discovery_client_tools(
                repository_acquisition=research_repository_acquisition_available,
            )
            if research_source_discovery_available
            else ()
        ),
        *(research_source_client_tools() if research_sources_available else ()),
    ]
    if research_sources_available or research_source_discovery_available:
        source_tools.append(
            ClientToolDefinition(
                name=SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
                description=(
                    "Atomically copy selected exact UTF-8 files from a configured "
                    "frozen snapshot or completely read public repository into the "
                    "current Python/R project under model-selected paths. Source modules, "
                    "text fixtures, data, and configuration remain exact project files. Use "
                    "source_origin=frozen_snapshot with source_id=document_id and "
                    "revision=snapshot_hash, or source_origin=discovered_repository "
                    "with source_id=source_handle and revision=repository revision. "
                    "This stores bytes without executing them; inspect, run, and review "
                    "the complete project afterward."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["imports"],
                    "properties": {
                        "imports": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": MAX_SCIENTIFIC_PROJECT_FILES,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": [
                                    "source_origin", "source_id", "revision", "source_path",
                                    "expected_content_sha256", "project_path",
                                ],
                                "properties": {
                                    "source_origin": {
                                        "type": "string",
                                        "enum": [
                                            "frozen_snapshot",
                                            "discovered_repository",
                                        ],
                                    },
                                    "source_id": {
                                        "type": "string", "minLength": 1,
                                    },
                                    "revision": {
                                        "type": "string", "minLength": 1,
                                    },
                                    "source_path": {
                                        "type": "string", "minLength": 1,
                                    },
                                    "expected_content_sha256": {
                                        "type": "string",
                                        "pattern": "^[0-9a-fA-F]{64}$",
                                    },
                                    "project_path": {
                                        "type": "string", "minLength": 1,
                                    },
                                },
                            },
                        },
                    },
                },
                terminal=False,
            ),
        )
    tools[0:0] = source_tools
    if context_documents_available:
        tools[0:0] = theory_documents.theory_document_client_tools()
    reason_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["reason"],
        "properties": {"reason": {"type": "string"}},
    }
    if allow_dependency_handoff:
        tools.append(
            ClientToolDefinition(
                name=SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
                description=(
                    "Report that a raw bound-consumer failure belongs to its exact "
                    "dependency. Runtime transfers the observation without editing."
                ),
                input_schema=reason_schema,
                terminal=True,
            )
        )
    return tuple(tools)


def _compact_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str, ensure_ascii=False)
