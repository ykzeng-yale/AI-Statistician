from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    EnvironmentObservation,
    EvidenceLedgerEntry,
    ToolCallRecord,
    agent_task_reference,
)
from .fingerprint import stable_hash
from .lean_candidate_identity import (
    LEAN_TARGET_STATEMENT_HASH_ALGORITHM,
    lean_target_statement_hash,
)
from .formal_target_semantic_reviewer_llm import (
    FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
    FORMAL_TARGET_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE,
    FORMAL_TARGET_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS,
    LLMFormalTargetSemanticReviewerAgent,
    validate_formal_target_semantic_review_packet,
)
from .structured_output_retry import PacketValidationError
from .model_backend import LIVE_EVALUATION_CLAUDE_MODEL_TIER
from .research_schema import OpenResearchQuestion


RUNTIME_SCHEMA_VERSION = 1
FORMAL_TARGET_REVIEW_PROPOSAL_PACKET_KINDS = frozenset(
    {
        "FormalizerProofEngineerProposalPacket",
        "FormalizerProofEngineerPacket",
    }
)


def _bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _question_to_payload(question: OpenResearchQuestion) -> dict[str, Any]:
    return {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }


def _question_from_payload(payload: Mapping[str, Any]) -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id=str(payload["id"]),
        title=str(payload.get("title", payload["id"])),
        description=str(payload["description"]),
        tags=tuple(str(row) for row in payload.get("tags", ()) or ()),
    )


def _agent_task_from_runtime_payload(payload: Mapping[str, Any]) -> AgentTask:
    task_id = str(payload.get("task_id", "") or "")
    owner_subsystem = str(payload.get("owner_subsystem", "") or "")
    if not task_id or not owner_subsystem:
        raise ValueError(
            "runtime task payload must include task_id and owner_subsystem"
        )
    return AgentTask(
        task_id=task_id,
        owner_subsystem=owner_subsystem,
        objective=str(payload.get("objective", "") or ""),
        inputs=(
            dict(payload.get("inputs", {}))
            if isinstance(payload.get("inputs", {}), Mapping)
            else {}
        ),
        allowed_tools=tuple(
            str(item)
            for item in (
                payload.get("allowed_tools", [])
                if isinstance(payload.get("allowed_tools", []), (list, tuple))
                else []
            )
        ),
        budget=(
            dict(payload.get("budget", {}))
            if isinstance(payload.get("budget", {}), Mapping)
            else {}
        ),
        expected_artifacts=tuple(
            str(item)
            for item in (
                payload.get("expected_artifacts", [])
                if isinstance(payload.get("expected_artifacts", []), (list, tuple))
                else []
            )
        ),
        acceptance_gate=str(payload.get("acceptance_gate", "") or ""),
        stop_condition=str(payload.get("stop_condition", "") or ""),
    )


FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM = "FormalTargetSemanticReviewer"


def _runtime_formal_target_semantic_review_dispatch(
    *,
    task: AgentTask,
    question: OpenResearchQuestion,
    source_subsystem: str,
    candidate_materialization: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    proposal_packet: Mapping[str, Any],
    candidate_feedback: Mapping[str, Any],
    architect_context: Mapping[str, Any],
    deferred_next_task: AgentTask,
    max_revisions: int,
) -> dict[str, Any] | None:
    target_context = (
        dict(candidate_feedback.get("formalizer_workspace_context", {}) or {})
        if isinstance(
            candidate_feedback.get("formalizer_workspace_context", {}), Mapping
        )
        else {}
    )
    if not _bool_like(
        target_context.get("formalizer_candidate_exact_search_eligible", False)
    ):
        return None
    if str(
        target_context.get("formalizer_candidate_semantic_review_status", "") or ""
    ) == "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE":
        return None

    candidate_path = str(
        target_context.get("candidate_artifact_path", "") or ""
    ).strip()
    candidate_source_hash = str(
        target_context.get("lineage_candidate_artifact_hash", "")
        or target_context.get("target_declaration_source_hash", "")
        or ""
    ).strip()
    target_statement = str(
        target_context.get("target_theorem_statement", "") or ""
    ).strip()
    target_statement_hash = str(
        target_context.get("target_theorem_statement_hash", "") or ""
    ).strip()
    target_statement_hash_algorithm = str(
        target_context.get("target_theorem_statement_hash_algorithm", "") or ""
    ).strip()
    dispatch_validation_errors: list[str] = []
    if not candidate_path:
        dispatch_validation_errors.append("candidate_artifact_path missing")
    if not candidate_source_hash:
        dispatch_validation_errors.append("candidate_source_hash missing")
    if not target_statement:
        dispatch_validation_errors.append("target_theorem_statement missing")
    if not target_statement_hash:
        dispatch_validation_errors.append("target_theorem_statement_hash missing")
    elif lean_target_statement_hash(target_statement) != target_statement_hash:
        dispatch_validation_errors.append(
            "target_theorem_statement_hash does not match the shared exact-target identity"
        )
    if target_statement_hash_algorithm != LEAN_TARGET_STATEMENT_HASH_ALGORITHM:
        dispatch_validation_errors.append(
            "target_theorem_statement_hash_algorithm mismatch"
        )

    candidate_row: dict[str, Any] = {}
    for raw_row in candidate_materialization.get("candidate_rows", []) or []:
        if not isinstance(raw_row, Mapping):
            continue
        row = dict(raw_row)
        if str(row.get("artifact_path", "") or "").strip() != candidate_path:
            continue
        if str(row.get("source_hash", "") or "").strip() != candidate_source_hash:
            continue
        candidate_row = row
        break
    if not candidate_row:
        dispatch_validation_errors.append(
            "candidate descriptor is not bound to the exact path and source hash"
        )

    candidate_materialization_id = str(
        candidate_materialization.get("manifest_id", "") or ""
    ).strip()
    theory_packet_id = str(theory_packet.get("packet_id", "") or "").strip()
    proposal_packet_id = str(proposal_packet.get("packet_id", "") or "").strip()
    candidate_id = str(candidate_row.get("candidate_id", "") or "").strip()
    for field_name, field_value in (
        ("candidate_materialization_id", candidate_materialization_id),
        ("theory_packet_id", theory_packet_id),
        ("proposal_packet_id", proposal_packet_id),
        ("candidate_id", candidate_id),
    ):
        if not field_value:
            dispatch_validation_errors.append(f"{field_name} missing")

    runtime_feedback_loop = architect_context.get("runtime_feedback_loop", {})
    if not isinstance(runtime_feedback_loop, Mapping):
        runtime_feedback_loop = {}
    review_revision_count = max(
        _nonnegative_int(
            task.inputs.get("formal_target_semantic_review_revision_count", 0)
        ),
        _nonnegative_int(
            architect_context.get(
                "formal_target_semantic_review_revision_count", 0
            )
        ),
        _nonnegative_int(
            runtime_feedback_loop.get(
                "formal_target_semantic_review_revision_count", 0
            )
        ),
    )
    runtime_contract = architect_context.get(
        "runtime_requested_evidence_contract", {}
    )
    capability_eval = bool(
        str(
            (runtime_contract if isinstance(runtime_contract, Mapping) else {}).get(
                "evaluation_mode", ""
            )
            or architect_context.get("runtime_evaluation_mode", "")
            or ""
        )
        == "capability_eval"
    )
    work_order_seed = {
        "source_task_id": task.task_id,
        "candidate_materialization_id": candidate_materialization_id,
        "candidate_id": candidate_id,
        "candidate_source_hash": candidate_source_hash,
        "target_theorem_statement_hash": target_statement_hash,
        "target_theorem_statement_hash_algorithm": (
            target_statement_hash_algorithm
        ),
        "review_revision_count": review_revision_count,
    }
    work_order_id = "formal_target_semantic_review_work_order:" + stable_hash(
        work_order_seed
    )[:20]
    deferred_task_payload = asdict(deferred_next_task)
    deferred_task_snapshot_id = "agent_task_snapshot:" + stable_hash(
        deferred_task_payload
    )[:20]
    deferred_task_snapshot = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeAgentTaskSnapshot",
        "snapshot_id": deferred_task_snapshot_id,
        "task_ref": agent_task_reference(deferred_next_task),
        "task": deferred_task_payload,
    }
    work_order = {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "artifact_kind": "RuntimeFormalTargetSemanticReviewWorkOrder",
        "work_order_id": work_order_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "source_task_id": task.task_id,
        "source_subsystem": source_subsystem,
        "target_subsystem": FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM,
        "candidate_materialization_id": candidate_materialization_id,
        "candidate_materialization_hash": stable_hash(candidate_materialization),
        "theory_packet_id": theory_packet_id,
        "theory_packet_hash": stable_hash(theory_packet),
        "proposal_packet_id": proposal_packet_id,
        "proposal_packet_hash": stable_hash(proposal_packet),
        "candidate_id": candidate_id,
        "candidate_artifact_path": candidate_path,
        "candidate_source_hash": candidate_source_hash,
        "target_lean_declaration": str(
            target_context.get("target_lean_declaration", "") or ""
        ),
        "target_theorem_statement": target_statement,
        "target_theorem_statement_hash": target_statement_hash,
        "target_theorem_statement_hash_algorithm": (
            target_statement_hash_algorithm
        ),
        "target_ids": list(target_context.get("target_ids", []) or []),
        "source_theorem_target_provenance": dict(
            target_context.get("source_theorem_target_provenance", {}) or {}
        )
        if isinstance(
            target_context.get("source_theorem_target_provenance", {}), Mapping
        )
        else {},
        "semantic_alignment_constraints": list(
            target_context.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            target_context.get("semantic_alignment_blockers", []) or []
        ),
        "compiler_context": {
            "precheck_errors": list(candidate_row.get("precheck_errors", []) or []),
            "local_lean_attempted": _bool_like(
                candidate_row.get("local_lean_attempted", False)
            ),
            "local_lean_compiled": _bool_like(
                candidate_row.get("local_lean_compiled", False)
            ),
            "local_lean_exit_status": str(
                candidate_row.get("local_lean_exit_status", "") or ""
            ),
            "local_lean_stdout": str(
                candidate_row.get("local_lean_stdout", "") or ""
            ),
            "local_lean_stderr": str(
                candidate_row.get("local_lean_stderr", "") or ""
            ),
        },
        "formalizer_target_context_hash": stable_hash(target_context),
        "source_agent": str(proposal_packet.get("source_agent", "") or ""),
        "source_model": str(proposal_packet.get("model", "") or ""),
        "source_model_tier": str(
            proposal_packet.get("model_tier", "") or ""
        ),
        "capability_eval": capability_eval,
        "review_revision_count": review_revision_count,
        "max_revisions": max(0, int(max_revisions or 0)),
        "dispatch_status": (
            "BLOCKED" if dispatch_validation_errors else "READY"
        ),
        "dispatch_validation_errors": sorted(
            set(dispatch_validation_errors)
        ),
        "deferred_next_task_ref": agent_task_reference(deferred_next_task),
        "deferred_next_task_snapshot_id": deferred_task_snapshot_id,
        "deferred_next_task_snapshot_hash": stable_hash(deferred_task_snapshot),
        "proof_evidence_status": (
            "FORMAL_TARGET_SEMANTIC_REVIEW_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
        "evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
    }
    work_order_hash = stable_hash(work_order)
    review_task = AgentTask(
        task_id=(
            f"formal-target-semantic-review:{question.id}:"
            f"{stable_hash([work_order_id, work_order_hash])[:10]}"
        ),
        owner_subsystem=FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM,
        objective=(
            "Independently review whether the exact hash-bound Lean theorem "
            "statement faithfully and non-vacuously formalizes the research "
            "question and TheoryDeveloper derivation before kernel promotion."
        ),
        inputs={
            "question": _question_to_payload(question),
            "work_order_id": work_order_id,
            "work_order_hash": work_order_hash,
        },
        allowed_tools=("model_backend", "filesystem", "blackboard"),
        expected_artifacts=(
            "formal_target_semantic_review_materialization",
            "formal_target_semantic_review_packet",
            "formal_target_semantic_review_execution_manifest",
        ),
        acceptance_gate=(
            "an independent lineage-bound mathematical review accepts the exact "
            "target or records evidence-grounded observations for Architect routing"
        ),
        stop_condition=(
            "semantic review accepts or Architect receives the rejected target's "
            "immutable observations and revision-budget facts"
        ),
    )
    evidence = EvidenceLedgerEntry(
        evidence_id="evidence:" + stable_hash([task.task_id, work_order_id])[:20],
        task_id=task.task_id,
        artifact_id=work_order_id,
        evidence_type="formal_target_semantic_review_work_order",
        status="WORK_ORDER_RECORDED_NOT_SEMANTIC_ACCEPTANCE",
        boundary=FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
        payload={
            "candidate_materialization_id": candidate_materialization_id,
            "candidate_id": candidate_id,
            "target_theorem_statement_hash": target_statement_hash,
            "target_theorem_statement_hash_algorithm": (
                target_statement_hash_algorithm
            ),
            "next_owner_subsystem": FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )
    observation = EnvironmentObservation(
        observation_type="formal_target_semantic_review_dispatched",
        summary=(
            "hash-bound exact theorem target routed to independent mathematical "
            "semantic review before kernel promotion"
        ),
        payload={
            "work_order_id": work_order_id,
            "work_order_hash": work_order_hash,
            "candidate_id": candidate_id,
            "candidate_source_hash": candidate_source_hash,
            "target_theorem_statement_hash": target_statement_hash,
            "target_theorem_statement_hash_algorithm": (
                target_statement_hash_algorithm
            ),
            "dispatch_validation_errors": sorted(
                set(dispatch_validation_errors)
            ),
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
    )
    return {
        "dispatch_status": (
            "BLOCKED" if dispatch_validation_errors else "READY"
        ),
        "work_order_id": work_order_id,
        "work_order": work_order,
        "deferred_task_snapshot_id": deferred_task_snapshot_id,
        "deferred_task_snapshot": deferred_task_snapshot,
        "artifacts": {
            work_order_id: work_order,
            deferred_task_snapshot_id: deferred_task_snapshot,
        },
        "next_task": review_task,
        "evidence": evidence,
        "observation": observation,
    }


def _runtime_formal_target_semantic_review_material(
    *,
    work_order: Mapping[str, Any],
    candidate_materialization: Mapping[str, Any],
    theory_packet: Mapping[str, Any],
    proposal_packet: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    candidate_id = str(work_order.get("candidate_id", "") or "")
    candidate_path = str(work_order.get("candidate_artifact_path", "") or "")
    candidate_source_hash = str(
        work_order.get("candidate_source_hash", "") or ""
    )
    matching_rows = [
        dict(row)
        for row in candidate_materialization.get("candidate_rows", []) or []
        if isinstance(row, Mapping)
        and str(row.get("candidate_id", "") or "") == candidate_id
        and str(row.get("artifact_path", "") or "") == candidate_path
        and str(row.get("source_hash", "") or "") == candidate_source_hash
    ]
    if len(matching_rows) != 1:
        errors.append("formal-target candidate descriptor is not uniquely bound")
        candidate_row: dict[str, Any] = {}
    else:
        candidate_row = matching_rows[0]
    matching_proposal_targets = [
        dict(row)
        for row in proposal_packet.get("formal_targets", []) or []
        if isinstance(row, Mapping)
        and str(row.get("id", "") or "") == candidate_id
    ]
    if len(matching_proposal_targets) != 1:
        errors.append("formal-target proposal target is not uniquely bound")
        proposal_target: dict[str, Any] = {}
    else:
        proposal_target = matching_proposal_targets[0]
    proposal_target_provenance = proposal_target.get(
        "source_theorem_target_provenance", {}
    )
    if not isinstance(proposal_target_provenance, Mapping):
        proposal_target_provenance = {}
    explicit_goal_ids = [
        str(value or "").strip()
        for value in (
            proposal_target.get("source_theorem_goal_id", ""),
            proposal_target_provenance.get("source_theorem_goal_id", ""),
        )
        if str(value or "").strip()
    ]
    candidate_goal_ids = [
        *explicit_goal_ids,
        str(proposal_target.get("source_identity", "") or "").strip(),
        *[
            str(value or "").strip()
            for value in work_order.get("target_ids", []) or []
        ],
    ]
    theory_cards_by_id = {
        str(row.get("id", "") or ""): dict(row)
        for row in theory_packet.get("theorem_cards", []) or []
        if isinstance(row, Mapping) and str(row.get("id", "") or "")
    }
    matching_theory_goal_ids = list(
        dict.fromkeys(
            goal_id
            for goal_id in candidate_goal_ids
            if goal_id and goal_id in theory_cards_by_id
        )
    )
    if len(matching_theory_goal_ids) > 1:
        errors.append("formal-target theory theorem card binding is ambiguous")
        source_theorem_goal_id = ""
    elif matching_theory_goal_ids:
        source_theorem_goal_id = matching_theory_goal_ids[0]
    else:
        source_theorem_goal_id = explicit_goal_ids[0] if explicit_goal_ids else ""
    matching_theory_cards = (
        [theory_cards_by_id[source_theorem_goal_id]]
        if source_theorem_goal_id in theory_cards_by_id
        else []
    )
    bound_theory_card = (
        matching_theory_cards[0] if len(matching_theory_cards) == 1 else {}
    )
    if source_theorem_goal_id and len(matching_theory_cards) != 1:
        errors.append("formal-target theory theorem card is not uniquely bound")
    source = ""
    path = Path(candidate_path).expanduser() if candidate_path else Path()
    if not candidate_path or not path.is_file():
        errors.append("formal-target exact source artifact is missing")
    else:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"formal-target exact source artifact unreadable: {exc!r}")
    if source and stable_hash(source) != candidate_source_hash:
        errors.append("formal-target exact source hash mismatch")
    target_statement = str(
        work_order.get("target_theorem_statement", "") or ""
    ).strip()
    target_statement_hash_algorithm = str(
        work_order.get("target_theorem_statement_hash_algorithm", "") or ""
    )
    if target_statement_hash_algorithm != LEAN_TARGET_STATEMENT_HASH_ALGORITHM:
        errors.append("formal-target theorem statement hash algorithm mismatch")
    if not target_statement or lean_target_statement_hash(target_statement) != str(
        work_order.get("target_theorem_statement_hash", "") or ""
    ):
        errors.append("formal-target theorem statement hash mismatch")
    material = {
        "theory_derivation_packet": dict(theory_packet),
        "formalizer_proposal_packet": dict(proposal_packet),
        "bound_target_contract": {
            "candidate_id": candidate_id,
            "target_ids": list(work_order.get("target_ids", []) or []),
            "source_theorem_goal_id": source_theorem_goal_id,
            "proposal_target": proposal_target,
            "theory_theorem_card": bound_theory_card,
        },
        "exact_formal_target": {
            "candidate_id": candidate_id,
            "target_ids": list(work_order.get("target_ids", []) or []),
            "target_lean_declaration": str(
                work_order.get("target_lean_declaration", "") or ""
            ),
            "target_theorem_statement": target_statement,
            "target_theorem_statement_hash": str(
                work_order.get("target_theorem_statement_hash", "") or ""
            ),
            "target_theorem_statement_hash_algorithm": (
                target_statement_hash_algorithm
            ),
            "exact_lean_source": source,
            "exact_lean_source_hash": candidate_source_hash,
            "source_theorem_target_provenance": dict(
                work_order.get("source_theorem_target_provenance", {}) or {}
            ),
            "semantic_alignment_constraints": list(
                work_order.get("semantic_alignment_constraints", []) or []
            ),
            "semantic_alignment_blockers": list(
                work_order.get("semantic_alignment_blockers", []) or []
            ),
        },
        "compiler_context_not_semantic_authority": dict(
            work_order.get("compiler_context", {}) or {}
        ),
        "candidate_materialization_summary": {
            "manifest_id": str(
                candidate_materialization.get("manifest_id", "") or ""
            ),
            "candidate_row": candidate_row,
        },
        "evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
    }
    return material, sorted(set(errors))


class FormalTargetSemanticReviewerRuntimeSubsystem:
    name = FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM

    def __init__(
        self,
        *,
        reviewer: LLMFormalTargetSemanticReviewerAgent,
        max_revisions: int = 1,
    ) -> None:
        self.reviewer = reviewer
        self.max_revisions = max(0, int(max_revisions or 0))

    def run(self, task: AgentTask, blackboard: BlackboardState) -> AgentStepResult:
        question = _question_from_payload(task.inputs["question"])
        work_order_id = str(task.inputs.get("work_order_id", "") or "")
        work_order_hash = str(task.inputs.get("work_order_hash", "") or "")
        raw_work_order = blackboard.artifacts.get(work_order_id, {})
        work_order = (
            dict(raw_work_order) if isinstance(raw_work_order, Mapping) else {}
        )
        validation_errors: list[str] = []
        validation_errors.extend(
            str(error)
            for error in work_order.get("dispatch_validation_errors", []) or []
            if str(error)
        )
        if not work_order_id or not work_order:
            validation_errors.append("formal-target semantic review work order missing")
        if str(work_order.get("artifact_kind", "") or "") != (
            "RuntimeFormalTargetSemanticReviewWorkOrder"
        ):
            validation_errors.append("formal-target review work-order kind mismatch")
        if str(work_order.get("work_order_id", "") or "") != work_order_id:
            validation_errors.append("formal-target review work-order identity mismatch")
        if not work_order_hash or stable_hash(work_order) != work_order_hash:
            validation_errors.append("formal-target review immutable work-order hash mismatch")
        if str(work_order.get("question_id", "") or "") != question.id:
            validation_errors.append("formal-target review question identity mismatch")
        source_subsystem = str(work_order.get("source_subsystem", "") or "")
        if source_subsystem not in FORMAL_TARGET_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS:
            validation_errors.append("formal-target review source subsystem is invalid")

        def bound_artifact(
            *,
            id_field: str,
            hash_field: str,
            kind: str = "",
            allowed_kinds: frozenset[str] = frozenset(),
        ) -> dict[str, Any]:
            artifact_id = str(work_order.get(id_field, "") or "")
            expected_hash = str(work_order.get(hash_field, "") or "")
            raw_artifact = blackboard.artifacts.get(artifact_id, {})
            if not artifact_id or not isinstance(raw_artifact, Mapping):
                validation_errors.append(f"{id_field} missing from blackboard")
                return {}
            artifact = dict(raw_artifact)
            if not expected_hash or stable_hash(artifact) != expected_hash:
                validation_errors.append(f"{id_field} immutable hash mismatch")
            artifact_kind = str(artifact.get("artifact_kind", "") or "")
            accepted_kinds = allowed_kinds or (
                frozenset({kind}) if kind else frozenset()
            )
            if accepted_kinds and artifact_kind not in accepted_kinds:
                validation_errors.append(f"{id_field} artifact kind mismatch")
            return artifact

        candidate_materialization = bound_artifact(
            id_field="candidate_materialization_id",
            hash_field="candidate_materialization_hash",
            kind="RuntimeFormalizerLeanCandidateMaterialization",
        )
        theory_packet = bound_artifact(
            id_field="theory_packet_id",
            hash_field="theory_packet_hash",
            kind="TheoryDerivationPacket",
        )
        proposal_packet = bound_artifact(
            id_field="proposal_packet_id",
            hash_field="proposal_packet_hash",
            allowed_kinds=FORMAL_TARGET_REVIEW_PROPOSAL_PACKET_KINDS,
        )
        deferred_task_snapshot = bound_artifact(
            id_field="deferred_next_task_snapshot_id",
            hash_field="deferred_next_task_snapshot_hash",
            kind="RuntimeAgentTaskSnapshot",
        )
        deferred_task_payload = (
            dict(deferred_task_snapshot.get("task", {}) or {})
            if isinstance(deferred_task_snapshot.get("task", {}), Mapping)
            else {}
        )
        deferred_task_ref = work_order.get("deferred_next_task_ref", {})
        if str(deferred_task_snapshot.get("snapshot_id", "") or "") != str(
            work_order.get("deferred_next_task_snapshot_id", "") or ""
        ):
            validation_errors.append(
                "formal-target review deferred task snapshot identity mismatch"
            )
        if deferred_task_snapshot.get("task_ref") != deferred_task_ref:
            validation_errors.append(
                "formal-target review deferred task snapshot ref mismatch"
            )
        try:
            deferred_task = _agent_task_from_runtime_payload(
                deferred_task_payload
            )
        except ValueError as exc:
            validation_errors.append(str(exc))
            deferred_task = None
        if deferred_task is not None and (
            deferred_task.owner_subsystem != "FormalizationEvaluator"
        ):
            validation_errors.append(
                "formal-target review deferred task is not ProofEngineer"
            )
        if (
            deferred_task is not None
            and agent_task_reference(deferred_task) != deferred_task_ref
        ):
            validation_errors.append("formal-target review deferred task ref mismatch")

        review_material: dict[str, Any] = {}
        if not validation_errors:
            review_material, material_errors = (
                _runtime_formal_target_semantic_review_material(
                    work_order=work_order,
                    candidate_materialization=candidate_materialization,
                    theory_packet=theory_packet,
                    proposal_packet=proposal_packet,
                )
            )
            validation_errors.extend(material_errors)
        if validation_errors:
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "FormalTargetSemanticReviewer rejected changed, missing, or "
                    "cross-task inputs before calling the reviewer model."
                ),
                observations=(
                    EnvironmentObservation(
                        observation_type="formal_target_semantic_review_input_rejected",
                        summary="; ".join(validation_errors)[:500],
                        payload={
                            "work_order_id": work_order_id,
                            "validation_errors": sorted(set(validation_errors)),
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification="formal_target_semantic_review_input_invalid",
            )

        materialization_id = "formal_target_semantic_review_materialization:" + stable_hash(
            [work_order_id, review_material]
        )[:20]
        materialization = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeFormalTargetSemanticReviewMaterialization",
            "materialization_id": materialization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question_id": question.id,
            "work_order_id": work_order_id,
            "work_order_hash": work_order_hash,
            "review_input_fingerprint": stable_hash(review_material),
            "review_material": review_material,
            "proof_evidence_status": (
                "FORMAL_TARGET_SEMANTIC_REVIEW_INPUT_NOT_PROOF_EVIDENCE"
            ),
            "evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
        }
        trusted_lineage = {
            key: work_order.get(key, "")
            for key in (
                "work_order_id",
                "source_task_id",
                "source_subsystem",
                "candidate_materialization_id",
                "candidate_materialization_hash",
                "theory_packet_id",
                "theory_packet_hash",
                "proposal_packet_id",
                "proposal_packet_hash",
                "candidate_id",
                "candidate_source_hash",
                "target_lean_declaration",
                "target_theorem_statement_hash",
                "target_theorem_statement_hash_algorithm",
                "source_agent",
                "source_model",
                "source_model_tier",
            )
        }
        trusted_lineage["work_order_hash"] = work_order_hash
        try:
            review_packet = self.reviewer.review(
                question=question,
                review_material=review_material,
                trusted_lineage=trusted_lineage,
            )
        except PacketValidationError as exc:
            last_invalid_packet = (
                dict(exc.last_invalid_packet)
                if isinstance(exc.last_invalid_packet, Mapping)
                else {}
            )
            invalid_review_projection = {
                key: last_invalid_packet.get(key)
                for key in (
                    "packet_id",
                    "review_input_fingerprint",
                    "overall_verdict",
                    "dimension_reviews",
                    "findings",
                    "routing_authority",
                    "runtime_selected_owner",
                    "proof_evidence_status",
                )
                if key in last_invalid_packet
            }
            failure_id = (
                "formal_target_semantic_review_validation_failure:"
                + stable_hash(
                    [
                        work_order_id,
                        list(exc.errors),
                        exc.history,
                        invalid_review_projection,
                    ]
                )[:20]
            )
            failure_artifact = {
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "artifact_kind": (
                    "RuntimeFormalTargetSemanticReviewValidationFailure"
                ),
                "failure_id": failure_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "question_id": question.id,
                "task_id": task.task_id,
                "work_order_id": work_order_id,
                "work_order_hash": work_order_hash,
                "materialization_id": materialization_id,
                "materialization_hash": stable_hash(materialization),
                "validation_label": exc.validation_label,
                "validation_errors": list(exc.errors),
                "validation_attempts": exc.attempts,
                "llm_packet_regeneration_history": [
                    dict(row) for row in exc.history
                ],
                "last_invalid_packet_available": bool(last_invalid_packet),
                "last_invalid_packet_fingerprint": (
                    stable_hash(last_invalid_packet)
                    if last_invalid_packet
                    else ""
                ),
                "last_invalid_packet": last_invalid_packet,
                "last_invalid_review_projection": (
                    invalid_review_projection
                ),
                "kernel_verified": False,
                "proof_evidence_status": (
                    "FORMAL_TARGET_SEMANTIC_REVIEW_VALIDATION_FAILURE_NOT_PROOF_EVIDENCE"
                ),
                "evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
            }
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "The independent formal-target reviewer exhausted typed packet "
                    "regeneration without a contract-valid observation packet."
                ),
                produced_artifacts={
                    materialization_id: materialization,
                    failure_id: failure_artifact,
                },
                observations=(
                    EnvironmentObservation(
                        observation_type="formal_target_semantic_review_packet_invalid",
                        summary=str(exc)[:500],
                        payload={
                            "work_order_id": work_order_id,
                            "failure_id": failure_id,
                            "validation_errors": list(exc.errors),
                            "validation_attempts": exc.attempts,
                                "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification="formal_target_semantic_review_packet_invalid",
            )

        runtime_review_errors = validate_formal_target_semantic_review_packet(
            review_packet
        )
        if str(review_packet.get("review_input_fingerprint", "") or "") != stable_hash(
            review_material
        ):
            runtime_review_errors.append("formal-target review input fingerprint mismatch")
        capability_eval = bool(work_order.get("capability_eval", False))
        source_agent = str(work_order.get("source_agent", "") or "")
        source_model = str(work_order.get("source_model", "") or "")
        source_tier = str(work_order.get("source_model_tier", "") or "")
        reviewer_agent = str(review_packet.get("source_agent", "") or "")
        reviewer_model = str(review_packet.get("model", "") or "")
        reviewer_tier = str(review_packet.get("model_tier", "") or "")
        if capability_eval and not all((source_agent, source_model, source_tier)):
            runtime_review_errors.append(
                "capability-eval formal-target review requires source provenance"
            )
        if capability_eval and source_agent == reviewer_agent:
            runtime_review_errors.append(
                "capability-eval formal-target reviewer agent must be independent"
            )
        if (
            capability_eval
            and reviewer_tier != LIVE_EVALUATION_CLAUDE_MODEL_TIER
        ):
            runtime_review_errors.append(
                "capability-eval formal-target reviewer must use the configured "
                f"evaluation tier {LIVE_EVALUATION_CLAUDE_MODEL_TIER}"
            )
        if runtime_review_errors:
            return AgentStepResult(
                status="BLOCKED",
                rationale=(
                    "FormalTargetSemanticReviewer rejected an independence, "
                    "evaluation-model, or lineage-inconsistent verdict."
                ),
                produced_artifacts={materialization_id: materialization},
                observations=(
                    EnvironmentObservation(
                        observation_type="formal_target_semantic_review_verdict_rejected",
                        summary="; ".join(sorted(set(runtime_review_errors)))[:500],
                        payload={
                            "work_order_id": work_order_id,
                            "validation_errors": sorted(set(runtime_review_errors)),
                            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                        },
                    ),
                ),
                failure_classification="formal_target_semantic_review_verdict_invalid",
            )

        review_packet_id = str(review_packet.get("packet_id", "") or "")
        review_packet_hash = stable_hash(review_packet)
        verdict = str(review_packet.get("overall_verdict", "") or "")
        review_findings = [
            dict(row)
            for row in review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ]
        execution_id = "formal_target_semantic_review_execution:" + stable_hash(
            [work_order_id, work_order_hash, review_packet_id, review_packet_hash]
        )[:20]
        execution_manifest = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "artifact_kind": "RuntimeFormalTargetSemanticReviewExecutionManifest",
            "execution_id": execution_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question_id": question.id,
            "task_id": task.task_id,
            "work_order_id": work_order_id,
            "work_order_hash": work_order_hash,
            "source_subsystem": source_subsystem,
            "candidate_materialization_id": str(
                work_order.get("candidate_materialization_id", "") or ""
            ),
            "candidate_id": str(work_order.get("candidate_id", "") or ""),
            "candidate_source_hash": str(
                work_order.get("candidate_source_hash", "") or ""
            ),
            "target_theorem_statement_hash": str(
                work_order.get("target_theorem_statement_hash", "") or ""
            ),
            "target_theorem_statement_hash_algorithm": str(
                work_order.get("target_theorem_statement_hash_algorithm", "") or ""
            ),
            "materialization_id": materialization_id,
            "materialization_hash": stable_hash(materialization),
            "review_packet_id": review_packet_id,
            "review_packet_hash": review_packet_hash,
            "review_input_fingerprint": stable_hash(review_material),
            "source_agent": source_agent,
            "source_model": source_model,
            "source_model_tier": source_tier,
            "reviewer_agent": reviewer_agent,
            "reviewer_model": reviewer_model,
            "reviewer_model_tier": reviewer_tier,
            "independent_agent": bool(source_agent and reviewer_agent != source_agent),
            "independent_invocation": True,
            "independent_model": bool(source_model and reviewer_model != source_model),
            "overall_verdict": verdict,
            "n_findings": len(review_findings),
            "semantic_review_accepted": verdict == "ACCEPT",
            "review_revision_count": int(
                work_order.get("review_revision_count", 0) or 0
            ),
            "proof_evidence_status": (
                FORMAL_TARGET_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE
            ),
            "evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
        }
        produced_artifacts = {
            materialization_id: materialization,
            review_packet_id: review_packet,
            execution_id: execution_manifest,
        }
        feedback_id = "formal_target_semantic_review_feedback:" + stable_hash(
            [question.id, work_order_id, review_packet_id, execution_id]
        )[:20]
        feedback = {
            "feedback_id": feedback_id,
            "feedback_type": "formal_target_semantic_review_feedback",
            "feedback_source": FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM,
            "question_id": question.id,
            "source_theory_packet_id": str(
                work_order.get("theory_packet_id", "") or ""
            ),
            "source_theory_packet_hash": str(
                work_order.get("theory_packet_hash", "") or ""
            ),
            "candidate_materialization_id": str(
                work_order.get("candidate_materialization_id", "") or ""
            ),
            "candidate_id": str(work_order.get("candidate_id", "") or ""),
            "candidate_source_hash": str(
                work_order.get("candidate_source_hash", "") or ""
            ),
            "target_theorem_statement_hash": str(
                work_order.get("target_theorem_statement_hash", "") or ""
            ),
            "target_theorem_statement_hash_algorithm": str(
                work_order.get("target_theorem_statement_hash_algorithm", "") or ""
            ),
            "semantic_review_execution_id": execution_id,
            "semantic_review_packet_id": review_packet_id,
            "semantic_review_packet_hash": review_packet_hash,
            "overall_verdict": verdict,
            "dimension_reviews": list(review_packet.get("dimension_reviews", []) or []),
            "findings": review_findings,
            "routing_authority": "same_formalizer_workspace",
            "runtime_selected_owner": False,
            "model_route_required_for_cross_owner_revision": False,
            "execution_results_observed": False,
            "execution_authorized": False,
            "model_owned_complete_source_tool_loop_eligible": True,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            "evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
        }
        revision_count = int(work_order.get("review_revision_count", 0) or 0)
        max_revisions = max(
            self.max_revisions,
            int(work_order.get("max_revisions", 0) or 0),
        )
        if verdict == "ACCEPT":
            if deferred_task is None:
                raise RuntimeError("validated deferred formal-target task missing")
            next_inputs = dict(deferred_task.inputs)
            prior_feedback = (
                dict(next_inputs.get("environment_feedback", {}) or {})
                if isinstance(next_inputs.get("environment_feedback", {}), Mapping)
                else {}
            )
            workspace_context = (
                dict(prior_feedback.get("formalizer_workspace_context", {}) or {})
                if isinstance(
                    prior_feedback.get("formalizer_workspace_context", {}), Mapping
                )
                else {}
            )
            target_provenance = (
                dict(
                    workspace_context.get("source_theorem_target_provenance", {})
                    or {}
                )
                if isinstance(
                    workspace_context.get("source_theorem_target_provenance", {}),
                    Mapping,
                )
                else {}
            )
            target_provenance.update(
                {
                    "source_theorem_target_known": True,
                    "source_theorem_target_identity_status": (
                        "CURRENT_THEORY_TARGET_INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED"
                    ),
                    "formal_target_semantic_review_execution_id": execution_id,
                    "formal_target_semantic_review_packet_id": review_packet_id,
                    "formal_target_semantic_review_packet_hash": review_packet_hash,
                    "formal_target_semantic_review_candidate_source_hash": str(
                        work_order.get("candidate_source_hash", "") or ""
                    ),
                    "formal_target_semantic_review_target_statement_hash": str(
                        work_order.get("target_theorem_statement_hash", "") or ""
                    ),
                }
            )
            workspace_context.update(
                {
                    "formalizer_candidate_semantic_review_status": (
                        "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
                    ),
                    "formalizer_candidate_semantic_review_execution_id": execution_id,
                    "formalizer_candidate_semantic_review_packet_id": review_packet_id,
                    "formalizer_candidate_semantic_review_packet_hash": (
                        review_packet_hash
                    ),
                    "formalizer_candidate_semantic_review_candidate_source_hash": str(
                        work_order.get("candidate_source_hash", "") or ""
                    ),
                    "formalizer_candidate_semantic_review_target_statement_hash": str(
                        work_order.get("target_theorem_statement_hash", "") or ""
                    ),
                    "formalizer_candidate_semantic_review_target_statement_hash_algorithm": str(
                        work_order.get(
                            "target_theorem_statement_hash_algorithm", ""
                        )
                        or ""
                    ),
                    "model_owned_complete_source_tool_loop_eligible": True,
                    "source_theorem_target_known": True,
                    "source_theorem_target_identity_status": (
                        "CURRENT_THEORY_TARGET_INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED"
                    ),
                    "source_theorem_target_provenance": target_provenance,
                    "source_theorem_kernel_evidence_eligible": True,
                    "source_theorem_promotion_blockers": [],
                }
            )
            next_feedback = {
                **prior_feedback,
                **feedback,
                "formalizer_workspace_context": workspace_context,
            }
            next_inputs["environment_feedback"] = next_feedback
            next_context = dict(next_inputs.get("architect_context", {}) or {})
            next_context["environment_feedback"] = next_feedback
            next_context["accepted_formal_target_semantic_review"] = {
                "execution_id": execution_id,
                "review_packet_id": review_packet_id,
                "review_packet_hash": review_packet_hash,
                "candidate_source_hash": str(
                    work_order.get("candidate_source_hash", "") or ""
                ),
                "target_theorem_statement_hash": str(
                    work_order.get("target_theorem_statement_hash", "") or ""
                ),
                "target_theorem_statement_hash_algorithm": str(
                    work_order.get("target_theorem_statement_hash_algorithm", "")
                    or ""
                ),
            }
            next_inputs["architect_context"] = next_context
            next_task = replace(
                deferred_task,
                task_id=(
                    f"formal-target-review-accepted:{question.id}:"
                    f"{stable_hash([execution_id, deferred_task.task_id])[:8]}"
                ),
                inputs=next_inputs,
            )
            status = "REROUTE"
            rationale = (
                "Independent semantic review accepted the exact theorem target; "
                "the unchanged hash-bound source is now eligible for the local "
                "identity/kernel promotion gate."
            )
            failure_classification = ""
        else:
            if deferred_task is None:
                raise RuntimeError("validated deferred formal-target task missing")
            deferred_inputs = dict(deferred_task.inputs)
            prior_feedback = (
                dict(deferred_inputs.get("environment_feedback", {}) or {})
                if isinstance(
                    deferred_inputs.get("environment_feedback", {}), Mapping
                )
                else {}
            )
            revision_context = (
                dict(prior_feedback.get("formalizer_workspace_context", {}) or {})
                if isinstance(
                    prior_feedback.get("formalizer_workspace_context", {}),
                    Mapping,
                )
                else {}
            )
            revision_context.update(
                {
                    "formalizer_candidate_semantic_review_status": (
                        "INDEPENDENT_SEMANTIC_REVIEW_REVISE_NOT_PROOF_EVIDENCE"
                    ),
                    "formalizer_candidate_semantic_review_execution_id": execution_id,
                    "formalizer_candidate_semantic_review_packet_id": review_packet_id,
                    "formalizer_candidate_semantic_review_packet_hash": (
                        review_packet_hash
                    ),
                    "formalizer_candidate_semantic_review_candidate_source_hash": str(
                        work_order.get("candidate_source_hash", "") or ""
                    ),
                    "formalizer_candidate_semantic_review_target_statement_hash": str(
                        work_order.get("target_theorem_statement_hash", "") or ""
                    ),
                    "formalizer_candidate_semantic_review_target_statement_hash_algorithm": str(
                        work_order.get(
                            "target_theorem_statement_hash_algorithm", ""
                        )
                        or ""
                    ),
                    "model_owned_complete_source_tool_loop_eligible": True,
                    "source_theorem_kernel_evidence_eligible": False,
                    "source_theorem_promotion_blockers": [
                        "The changed source must pass a fresh independent semantic "
                        "review before source-theorem kernel promotion."
                    ],
                }
            )
            feedback = {
                **prior_feedback,
                **feedback,
                "formalizer_workspace_context": revision_context,
            }
            if revision_count < max_revisions:
                next_inputs = dict(deferred_task.inputs)
                next_inputs["environment_feedback"] = feedback
                next_inputs["formal_target_semantic_review_revision_count"] = (
                    revision_count + 1
                )
                next_task = replace(
                    deferred_task,
                    task_id=(
                        f"formal-target-revise:{question.id}:"
                        f"{stable_hash([execution_id, deferred_task.task_id])[:8]}"
                    ),
                    inputs=next_inputs,
                )
                status = "REVISE"
                rationale = (
                    "Independent semantic review returned its exact findings to the "
                    "same Formalizer workspace for a complete model-authored source "
                    "revision."
                )
                failure_classification = "formal_target_semantic_review_revise"
            else:
                next_task = None
                status = "BLOCKED"
                rationale = (
                    "The same Formalizer workspace exhausted its bounded semantic "
                    "revision budget; the target remains unpromoted."
                )
                failure_classification = (
                    "formal_target_semantic_review_revision_budget_exhausted"
                )

        evidence = EvidenceLedgerEntry(
            evidence_id="evidence:" + stable_hash([task.task_id, execution_id])[:20],
            task_id=task.task_id,
            artifact_id=execution_id,
            evidence_type="formal_target_semantic_review",
            status=(
                "SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
                if verdict == "ACCEPT"
                else "SEMANTIC_REVIEW_REVISION_REQUIRED_NOT_PROOF_EVIDENCE"
            ),
            boundary=FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
            payload={
                "candidate_id": str(work_order.get("candidate_id", "") or ""),
                "candidate_source_hash": str(
                    work_order.get("candidate_source_hash", "") or ""
                ),
                "overall_verdict": verdict,
                "reviewer_model": reviewer_model,
                "reviewer_model_tier": reviewer_tier,
                "n_findings": len(review_packet.get("findings", []) or []),
                "kernel_verified": False,
            },
        )
        return AgentStepResult(
            status=status,
            rationale=rationale,
            produced_artifacts=produced_artifacts,
            observations=(
                EnvironmentObservation(
                    observation_type="formal_target_semantic_review_result",
                    summary=(
                        f"candidate={work_order.get('candidate_id', '')} "
                        f"verdict={verdict} "
                        f"findings={len(review_packet.get('findings', []) or [])}"
                    ),
                    payload={
                        "execution_id": execution_id,
                        "review_packet_id": review_packet_id,
                        "overall_verdict": verdict,
                        "next_owner_subsystem": (
                            next_task.owner_subsystem if next_task else ""
                        ),
                        "model_owned_complete_source_tool_loop_eligible": (
                            True
                        ),
                        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
                    },
                ),
            ),
            tool_calls=(
                ToolCallRecord(
                    tool_name="LLMFormalTargetSemanticReviewerAgent.review",
                    inputs={
                        "work_order_id": work_order_id,
                        "review_input_fingerprint": stable_hash(review_material),
                        "candidate_source_hash": str(
                            work_order.get("candidate_source_hash", "") or ""
                        ),
                    },
                    input_hash=stable_hash(review_material),
                    output_hash=review_packet_hash,
                    exit_status="0",
                    stdout_summary=(
                        f"verdict={verdict} reviewer_model={reviewer_model}"
                    ),
                    safety_boundary=FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
                ),
            ),
            evidence_entries=(evidence,),
            next_task=next_task,
            failure_classification=failure_classification,
        )
