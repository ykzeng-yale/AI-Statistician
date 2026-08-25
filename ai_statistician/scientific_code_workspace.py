from __future__ import annotations

import json
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
    runtime_artifact_reference,
)
from .client_tool_loop import (
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
from .scientific_sandbox import (
    PYTHON_SCIENTIFIC_DEPENDENCIES,
    R_SCIENTIFIC_DEPENDENCIES,
    SCIENTIFIC_SANDBOX_LANGUAGES,
    SCIENTIFIC_SANDBOX_PROFILES,
    generated_code_execution_contract_errors,
    normalized_generated_code_language,
    normalized_generated_code_profile,
    normalized_scientific_dependencies,
)
from .structured_output_retry import PacketValidationError


ScientificCodeCheck = Callable[[Mapping[str, Any]], Mapping[str, Any]]

SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS = "native_client_tools"
SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET = "structured_packet"
SCIENTIFIC_SOURCE_SUBMISSION_TOOL = "submit_scientific_source"
SCIENTIFIC_SOURCE_COMMIT_TOOL = "commit_scientific_source"
SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL = "run_current_scientific_source"
SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL = "report_bound_dependency_failure"
SCIENTIFIC_SOURCE_REVISE_CURRENT = "revise_current_source"
SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER = (
    "return_to_bound_dependency_owner"
)
SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_KIND = "ScientificCodeWorkspaceCheckpoint"
SCIENTIFIC_CONSUMER_REVISION_BUDGET_KEY = "scientific_consumer_revision"
_SCIENTIFIC_PACKAGES = (
    PYTHON_SCIENTIFIC_DEPENDENCIES + R_SCIENTIFIC_DEPENDENCIES
)
_OUTCOME_DERIVED_SHAPE_FIELDS = frozenset(
    {"length", "dimensions", "field_count", "truncated_field_count"}
)


@dataclass(frozen=True)
class ScientificCodeWorkspaceResult:
    code_draft: Mapping[str, Any]
    check_result: Mapping[str, Any]
    evidence: Mapping[str, Any]


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
    if (
        not isinstance(observed_hashes, list)
        or draft_hash not in observed_hashes
        or any(not str(value or "").strip() for value in observed_hashes)
    ):
        raise ValueError("scientific code workspace observed source hashes are invalid")
    last_check = checkpoint.get("last_check", {})
    if not isinstance(last_check, Mapping) or not last_check:
        raise ValueError("scientific code workspace last check is missing")
    last_check = deepcopy(dict(last_check))
    if str(last_check.get("code_draft_hash", "") or "") != draft_hash:
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
        or checks <= segment_start_checks
        or checks < 1
    ):
        raise ValueError("scientific code workspace checkpoint made no executable progress")
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
            "outer iteration budget, without Architect routing."
        ),
        produced_artifacts=dict(produced_artifacts),
        observations=tuple(observations),
        tool_calls=tuple(tool_calls),
        evidence_entries=tuple(
            row for row in evidence_entries if row is not None
        ),
        next_task=next_task,
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
            "parent_script_hash": str(
                source_row.get("script_hash", "") or ""
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

    if confirmatory_result_blind:
        return bool(
            prototype.get("execution_smoke_passed") is True
            and not scientific_workspace_measurement_interface_failures(
                prototype
            )
        )
    return prototype.get("smoke_passed") is True


def run_source_owner_scientific_workspace(
    *,
    proposal_agent: Any,
    question: Any,
    artifact_id: str,
    code_draft: Mapping[str, Any],
    source_deferred: bool,
    workspace_context: Mapping[str, Any],
    execute_candidate: Callable[
        [Mapping[str, Any]],
        tuple[dict[str, Any], Any | Sequence[Any]],
    ],
    failure_identity: Mapping[str, Any],
    external_initial_observation: Mapping[str, Any] | None = None,
    confirmatory_result_blind: bool = False,
    allow_current_source_run: bool = False,
    disallowed_unchanged_source_hashes: Sequence[str] = (),
    recovery_checkpoint: Mapping[str, Any] | None = None,
    session_dir: Path | None = None,
) -> tuple[dict[str, Any], list[Any]]:
    """Run one source owner's direct model/tool feedback loop."""

    can_use_workspace = bool(
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
    tool_calls: list[Any] = []
    last_checked_prototype: dict[str, Any] = {}
    bound_execution_fields = (
        {
            "required_estimator_ids": deepcopy(
                list(code_draft.get("required_estimator_ids", []) or [])
            )
        }
        if "required_estimator_ids" in code_draft
        else {}
    )

    def record_tool_calls(value: Any | Sequence[Any]) -> None:
        if isinstance(value, (list, tuple)):
            tool_calls.extend(value)
        else:
            tool_calls.append(value)

    def source_candidate_accepted(prototype: Mapping[str, Any]) -> bool:
        return scientific_source_candidate_accepted(
            prototype,
            confirmatory_result_blind=confirmatory_result_blind,
        )

    def source_observation(prototype: Mapping[str, Any]) -> dict[str, Any]:
        return scientific_workspace_prototype_observation(
            prototype,
            include_empirical_outcomes=not confirmatory_result_blind,
        )

    def check_candidate(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        execution_candidate = {**dict(candidate), **bound_execution_fields}
        candidate_source = str(execution_candidate.get("code", "") or "")
        candidate_source_hash = stable_hash(candidate_source)
        if (
            candidate_source
            and candidate_source_hash in disallowed_unchanged_source_hashes
        ):
            prototype = {
                **dict(failure_identity),
                "prototype_status": "UNCHANGED_SOURCE_REJECTED",
                "source_code": candidate_source,
                "script_hash": candidate_source_hash,
                "parent_script_hash": candidate_source_hash,
                "execution_attempted": False,
                "execution_smoke_passed": False,
                "smoke_passed": False,
                "runtime_errors": [
                    "The candidate source hash matches a released parent source; "
                    "an unchanged candidate cannot consume a fresh evaluation cohort."
                ],
                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            }
        else:
            prototype, tool_call = execute_candidate(execution_candidate)
            record_tool_calls(tool_call)
        last_checked_prototype.clear()
        last_checked_prototype.update(deepcopy(dict(prototype)))
        check = {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": source_candidate_accepted(prototype),
            "prototype": source_observation(prototype),
        }
        disposition = str(
            prototype.get("source_iteration_disposition", "") or ""
        ).strip()
        if disposition:
            check["source_iteration_disposition"] = disposition
        source_owner = prototype.get("source_owner", {})
        if isinstance(source_owner, Mapping) and source_owner:
            check["source_owner"] = deepcopy(dict(source_owner))
        return check

    active_recovery_checkpoint = (
        deepcopy(dict(recovery_checkpoint))
        if isinstance(recovery_checkpoint, Mapping) and recovery_checkpoint
        else {}
    )
    if active_recovery_checkpoint:
        try:
            workspace_draft, initial_observation = (
                load_scientific_code_workspace_checkpoint(
                    active_recovery_checkpoint,
                    artifact_id=artifact_id,
                )
            )
        except ValueError as exc:
            return (
                {
                    **dict(failure_identity),
                    "prototype_status": "SCIENTIFIC_WORKSPACE_CHECKPOINT_INVALID",
                    "smoke_passed": False,
                    "execution_smoke_passed": False,
                    "scientific_code_workspace_failure": {
                        "validation_errors": [str(exc)],
                        "recovery_checkpoint": active_recovery_checkpoint,
                        "runtime_edited_source": False,
                    },
                },
                tool_calls,
            )
        workspace_operation = str(
            active_recovery_checkpoint.get(
                "workspace_operation", "targeted_revision"
            )
            or "targeted_revision"
        )
        prototype = {
            **dict(failure_identity),
            "prototype_status": "MODEL_SOURCE_WORKSPACE_FAILED",
            "smoke_passed": False,
            "execution_smoke_passed": False,
        }
    elif source_deferred:
        if not can_use_workspace:
            return (
                {
                    **dict(failure_identity),
                    "prototype_status": "MODEL_SOURCE_WORKSPACE_UNAVAILABLE",
                    "smoke_passed": False,
                    "execution_smoke_passed": False,
                    "reason": (
                        "The planning envelope deferred source to native client "
                        "tools, but the source-owning provider has no callable "
                        "workspace."
                    ),
                },
                tool_calls,
            )
        workspace_draft: Mapping[str, Any] | None = None
        workspace_operation = "initial_authoring"
        initial_observation = {
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "artifact_id": artifact_id,
            "execution_attempted": False,
            "observation": (
                "No source exists yet; author and run the complete candidate in "
                "this workspace."
            ),
        }
        prototype = {
            **dict(failure_identity),
            "prototype_status": "MODEL_SOURCE_WORKSPACE_FAILED",
            "smoke_passed": False,
            "execution_smoke_passed": False,
        }
    elif external_initial_observation and can_use_workspace:
        workspace_draft = {
            key: deepcopy(code_draft[key])
            for key in (
                "language",
                "execution_profile",
                "dependencies",
                "entrypoint",
                "code",
            )
            if key in code_draft
        }
        workspace_operation = "targeted_revision"
        initial_observation = {
            **deepcopy(dict(external_initial_observation)),
            "code_draft_hash": stable_hash(workspace_draft),
            "accepted": False,
        }
        prototype = {
            **dict(failure_identity),
            "prototype_status": "MODEL_SOURCE_WORKSPACE_FAILED",
            "smoke_passed": False,
            "execution_smoke_passed": False,
        }
    else:
        prototype, tool_call = execute_candidate(code_draft)
        record_tool_calls(tool_call)
        if (
            source_candidate_accepted(prototype)
            or prototype.get("source_iteration_disposition")
            == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
            or not can_use_workspace
        ):
            return prototype, tool_calls
        workspace_draft = {
            key: deepcopy(code_draft[key])
            for key in (
                "language",
                "execution_profile",
                "dependencies",
                "entrypoint",
                "code",
            )
            if key in code_draft
        }
        workspace_operation = "targeted_revision"
        initial_observation = {
            "code_draft_hash": stable_hash(workspace_draft),
            "accepted": False,
            "prototype": source_observation(prototype),
        }

    try:
        workspace_result = proposal_agent.iterate_code_with_tools(
            question=question,
            artifact_id=artifact_id,
            code_draft=workspace_draft,
            initial_observation=initial_observation,
            workspace_context=dict(workspace_context),
            check_candidate=check_candidate,
            workspace_operation=workspace_operation,
            allow_current_source_run=allow_current_source_run,
            recovery_checkpoint=(active_recovery_checkpoint or None),
            session_dir=session_dir,
        )
    except PacketValidationError as exc:
        if last_checked_prototype:
            prototype = deepcopy(last_checked_prototype)
        prototype["scientific_code_workspace_failure"] = {
            "validation_errors": list(exc.errors),
            "attempts": exc.attempts,
            "history": [dict(row) for row in exc.history],
            "recovery_checkpoint": dict(exc.recovery_checkpoint or {}),
            "runtime_edited_source": False,
        }
        return prototype, tool_calls

    if not last_checked_prototype:
        raise RuntimeError(
            "scientific workspace accepted without a persisted sandbox result"
        )
    prototype = deepcopy(last_checked_prototype)
    terminal_check = dict(workspace_result.check_result)
    if (
        terminal_check.get("source_iteration_disposition")
        == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
    ):
        prototype["source_iteration_disposition"] = (
            SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
        )
        prototype["source_owner"] = deepcopy(
            dict(terminal_check.get("source_owner", {}))
        )
        prototype["dependency_failure_report"] = deepcopy(
            dict(terminal_check.get("dependency_failure_report", {}))
        )
    prototype["scientific_code_workspace"] = dict(workspace_result.evidence)
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
) -> dict[str, Any]:
    """Project one persisted sandbox result into bounded model feedback."""

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
                key: _bounded_observation_value(value)
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
                "prototype_status",
                "smoke_passed",
                "stdout_summary",
                "metric_gate_errors",
                "result_hash",
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
            key: _bounded_observation_value(value)
            for key, value in direct_fields.items()
        },
        **(
            {
                "failed_metric_contracts": failed_contracts,
                "metrics_preview": _bounded_observation_value(
                    prototype.get("metrics", {})
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
        "proof_evidence_status": "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE",
    }


def scientific_workspace_measurement_interface_failures(
    prototype: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return outcome-blind failures in the generated metric output ABI."""

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
    failures: list[dict[str, Any]] = []
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
    proposal_id = str(
        manifest.get("llm_simulation_engineer_proposal_id", "") or ""
    ).strip()
    if not proposal_id:
        errors.append("consumer resume proposal identity is missing")
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
    return proposal_id, drafts, sorted(set(errors))


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
            or str(row.get("script_hash", "") or "")
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


def _bounded_observation_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 8:
        return {"preview": "depth_limit", "type": type(value).__name__}
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= 2_000 else value[:2_000] + "..."
    if isinstance(value, Mapping):
        items = list(value.items())
        preview = {
            str(key): _bounded_observation_value(child, depth=depth + 1)
            for key, child in items[:24]
        }
        if len(items) > 24:
            preview["truncated_key_count"] = len(items) - 24
        return preview
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        rows = list(value)
        if len(rows) <= 12:
            return [
                _bounded_observation_value(row, depth=depth + 1) for row in rows
            ]
        return {
            "preview": "sequence",
            "length": len(rows),
            "head": [
                _bounded_observation_value(row, depth=depth + 1)
                for row in rows[:8]
            ],
            "tail": [
                _bounded_observation_value(row, depth=depth + 1)
                for row in rows[-2:]
            ],
        }
    return str(value)[:2_000]


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
) -> ScientificCodeWorkspaceResult:
    """Let one model own complete scientific source across raw sandbox feedback."""

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
    resumed_checkpoint_id = ""
    prior_source_updates = 0
    prior_checks = 0
    prior_observed_hashes: set[str] = set()
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
    if workspace_operation == "targeted_revision" and not parent_draft:
        raise ValueError("targeted scientific source revision requires parent source")
    parent_hash = stable_hash(parent_draft) if parent_draft else ""
    observed_draft_hashes = set(prior_observed_hashes)
    if parent_hash:
        observed_draft_hashes.add(parent_hash)
    state: dict[str, Any] = {
        "code_draft": parent_draft,
        "code_draft_hash": parent_hash,
        "source_updates": prior_source_updates,
        "current_source_run_requests": 0,
        "checks": prior_checks,
        "last_check": deepcopy(dict(initial_check_result)),
        "last_check_turn_index": -1,
        "commit_turn_index": -1,
    }
    tools = _scientific_code_tools(
        allow_current_source_run=(
            bool(parent_draft) and allow_current_source_run
        ),
        allow_dependency_handoff=allow_dependency_handoff,
    )

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
            content={
                **check,
                "ok": accepted,
                "changed": source_changed,
                "current_source_reexecuted": current_source_reexecuted,
                "checks": state["checks"],
                "source_updates": state["source_updates"],
                "execution_evidence_status": (
                    "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE"
                ),
            },
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

    def execute_tool(call, context):
        tool_input = dict(call.input)
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
                or set(tool_input) - required_fields
            ):
                raise ClientToolInputError(
                    "submit_scientific_source requires the complete language, "
                    "execution_profile, dependencies, entrypoint, and code candidate"
                )
            draft = _complete_code_draft(tool_input)
            draft_hash = stable_hash(draft)
            changed = draft_hash != state["code_draft_hash"]
            if draft_hash in observed_draft_hashes:
                raise ClientToolInputError(
                    "replacement is byte-identical to a previously executed "
                    "scientific source; its deterministic observation is already "
                    "recorded, so submit a new complete candidate"
                )
            state["code_draft"] = draft
            state["code_draft_hash"] = draft_hash
            state["source_updates"] += 1
            observed_draft_hashes.add(draft_hash)
            return execute_checked_draft(
                state["code_draft"],
                source_changed=changed,
                current_source_reexecuted=False,
                turn_index=context.turn_index,
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
            if not parent_draft or not allow_current_source_run:
                raise ClientToolInputError(
                    "run_current_scientific_source is unavailable unless the current "
                    "source is bound to a newly changed dependency environment"
                )
            if state["current_source_run_requests"]:
                raise ClientToolInputError(
                    "the exact current source was already executed in the current "
                    "dependency environment"
                )
            if set(tool_input) != {"reason"} or not str(
                tool_input.get("reason", "") or ""
            ).strip():
                raise ClientToolInputError(
                    "run_current_scientific_source requires one nonempty reason"
                )
            state["current_source_run_requests"] += 1
            state["code_draft"] = deepcopy(parent_draft)
            state["code_draft_hash"] = parent_hash
            return execute_checked_draft(
                state["code_draft"],
                source_changed=False,
                current_source_reexecuted=True,
                turn_index=context.turn_index,
            )

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

    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=(
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\nThis workspace has at most "
                + str(max_turns)
                + " total model/tool turns. Retain the observed source hashes, "
                    "sandbox results, and attempted changes across those turns. Do "
                    "not resubmit a previously observed byte-identical candidate."
                )
                + (
                    "\n\nNo scientific source exists yet. Author the complete "
                    "candidate with submit_scientific_source. Each submission is "
                    "executed immediately without runtime source edits. Inspect the "
                    "returned observation before committing it."
                    if not parent_draft
                    else "\n\nCurrent complete code candidate:\n"
                    + _compact_json(parent_draft)
                )
                + "\n\nInitial workspace observation:\n"
                + _compact_json(initial_check_result)
                + (
                    "\n\nThis is a hash-bound continuation of checkpoint "
                    + resumed_checkpoint_id
                    + ". Continue from the exact current source and observation; "
                    "do not regenerate the planning envelope."
                    if resumed_checkpoint_id
                    else ""
                )
                + (
                    "\n\nThe current candidate has a failed consumer observation. "
                    "Diagnose that exact observation. If this source owns the defect, "
                    "submit a changed complete candidate; if another bound dependency "
                    "owns it, call run_current_scientific_source to execute the exact "
                    "current bytes in the newly changed dependency environment. Every "
                    "submission executes immediately; identical bytes are not a new "
                    "submission. Commit only after inspecting an accepted execution "
                    "observation."
                    if initial_check_result.get("accepted") is not True
                    and parent_draft
                    and allow_current_source_run
                    else "\n\nThe current candidate has a failed observation. Diagnose "
                    "that exact observation and submit a changed complete candidate. "
                    "Every submission executes immediately; identical bytes are not "
                    "a new submission. Commit only after inspecting an accepted "
                    "execution observation."
                    if initial_check_result.get("accepted") is not True
                    and parent_draft
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
            "model_tier": model_tier,
            "artifact_id": artifact_id,
            "parent_code_draft_hash": parent_hash,
            "workspace_operation": workspace_operation,
            "resumed_from_checkpoint_id": resumed_checkpoint_id,
        },
    )
    resolved_session_dir = session_dir.resolve() if session_dir else None
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
            )
        )
        resumed_client_tool_session_ref = deepcopy(
            dict(prior_client_tool_session_ref)
        )

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_turns,
            max_no_progress_turns=max_no_progress_turns,
        )
    except ClientToolLoopError as exc:
        client_tool_session_ref = persist_client_tool_session(
            session_dir=resolved_session_dir,
            session_id=f"scientific:{artifact_id}",
            request=request,
            messages=exc.messages,
        )
        last_check = deepcopy(dict(state["last_check"]))
        current_draft = deepcopy(dict(state["code_draft"]))
        current_draft_hash = str(state["code_draft_hash"] or "")
        last_check_bound = bool(
            current_draft
            and current_draft_hash
            and str(last_check.get("code_draft_hash", "") or "")
            == current_draft_hash
        )
        checkpoint_body = {
            "schema_version": 2,
            "artifact_kind": SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_KIND,
            "artifact_id": artifact_id,
            "workspace_operation": workspace_operation,
            "parent_code_draft_hash": parent_hash,
            "current_code_draft_hash": current_draft_hash,
            "current_code_draft": current_draft,
            "observed_code_draft_hashes": sorted(observed_draft_hashes),
            "source_updates": state["source_updates"],
            "checks": state["checks"],
            "segment_start_source_updates": prior_source_updates,
            "segment_start_checks": prior_checks,
            "last_check": last_check,
            "last_check_hash": stable_hash(last_check),
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
                last_check_bound and state["checks"] > prior_checks
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
            history=[deepcopy(dict(row)) for row in exc.history],
            recovery_checkpoint=checkpoint,
        ) from exc

    client_tool_session_ref = persist_client_tool_session(
        session_dir=resolved_session_dir,
        session_id=f"scientific:{artifact_id}",
        request=request,
        messages=loop.messages,
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
            history=[deepcopy(dict(row)) for row in loop.history],
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
        "source_changed": draft_hash != parent_hash,
        "current_source_run_requested": bool(
            state["current_source_run_requests"]
        ),
        "current_source_run_requests": state[
            "current_source_run_requests"
        ],
        "source_updates": state["source_updates"],
        "sandbox_checks": state["checks"],
        "submit_and_execute_atomic": True,
        "explicit_model_commit_required": True,
        "model_commit_after_observation": bool(
            state["commit_turn_index"] > state["last_check_turn_index"] >= 0
        ),
        "transcript_policy": CLIENT_TOOL_TRANSCRIPT_POLICY,
        "turns": loop.turns,
        "tool_calls": loop.tool_calls,
        "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
        "provider": loop.provider,
        "model": loop.model,
        "model_tier": model_tier,
        "provider_usage": dict(loop.provider_usage),
        "history": [deepcopy(dict(row)) for row in loop.history],
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
    draft = {
        "language": language,
        "execution_profile": execution_profile,
        "dependencies": normalized_dependencies,
        "entrypoint": entrypoint,
        "code": code,
    }
    contract_errors = generated_code_execution_contract_errors(draft)
    if contract_errors:
        raise ClientToolInputError("; ".join(contract_errors))
    return draft


def _scientific_code_tools(
    *,
    allow_current_source_run: bool,
    allow_dependency_handoff: bool,
) -> tuple[ClientToolDefinition, ...]:
    tools = [
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            description=(
                "Submit one complete Python or R candidate. The runtime stores and "
                "immediately executes the exact source, then returns the raw sandbox "
                "observation to this same model. This does not commit the candidate; "
                "inspect the observation, revise when needed, then explicitly commit "
                "the accepted current source. Match dependencies to language: "
                "Python allows "
                + ", ".join(PYTHON_SCIENTIFIC_DEPENDENCIES)
                + "; R allows "
                + ", ".join(R_SCIENTIFIC_DEPENDENCIES)
                + ". Never mix Python and R dependency names."
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
    if allow_current_source_run:
        tools.append(
            ClientToolDefinition(
                name=SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                description=(
                    "Execute the exact current source without editing it when a bound "
                    "dependency environment has changed since its prior observation. "
                    "The runtime returns the new raw observation and does not infer "
                    "whether this source or another dependency owns any defect."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["reason"],
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": (
                                "Why executing the current bytes in the changed bound "
                                "environment is the next useful diagnostic action."
                            ),
                        }
                    },
                },
                terminal=False,
            )
        )
    if allow_dependency_handoff:
        tools.append(
            ClientToolDefinition(
                name=SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
                description=(
                    "After a raw sandbox observation shows an exact bound estimator "
                    "binding or runtime failure, use this only when you judge the "
                    "current consumer call valid under the supplied interface and the "
                    "bound dependency source owns the defect. The runtime transfers "
                    "the hash-bound observation unchanged and does not edit either "
                    "source. Otherwise revise the current source instead."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["reason"],
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": (
                                "Why the observed valid consumer call demonstrates a "
                                "defect in the exact bound dependency rather than in "
                                "the current source."
                            ),
                        }
                    },
                },
                terminal=True,
            )
        )
    return tuple(tools)


def _compact_json(value: Any, *, max_chars: int = 30_000) -> str:
    encoded = json.dumps(value, separators=(",", ":"), default=str)
    if len(encoded) <= max_chars:
        return encoded
    marker = "\n[observation middle truncated]\n"
    available = max_chars - len(marker)
    head = available // 2
    return encoded[:head] + marker + encoded[-(available - head) :]
