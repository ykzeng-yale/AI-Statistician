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
)
from .fingerprint import stable_hash
from .exact_source_theorem_proof_body_executor import (
    EXACT_TARGET_STATEMENT_HASH_ALGORITHM,
    exact_target_statement_hash,
)
from .formal_target_semantic_reviewer_llm import (
    FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
    FORMAL_TARGET_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE,
    FORMAL_TARGET_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS,
    LLMFormalTargetSemanticReviewerAgent,
    validate_formal_target_semantic_review_packet,
)
from .llm_json_repair import PacketValidationError
from .model_backend import LIVE_EVALUATION_CLAUDE_MODEL_TIER
from .research_schema import OpenResearchQuestion
from .typed_repair_handoff import build_typed_repair_handoff_contract


RUNTIME_SCHEMA_VERSION = 1


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
    repair_feedback: Mapping[str, Any],
    architect_context: Mapping[str, Any],
    deferred_next_task: AgentTask,
    max_revisions: int,
) -> dict[str, Any] | None:
    repair_context = (
        dict(repair_feedback.get("proofengineer_repair_context", {}) or {})
        if isinstance(
            repair_feedback.get("proofengineer_repair_context", {}), Mapping
        )
        else {}
    )
    if not _bool_like(
        repair_context.get("formalizer_candidate_exact_search_eligible", False)
    ):
        return None
    if str(
        repair_context.get("formalizer_candidate_semantic_review_status", "") or ""
    ) == "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE":
        return None

    candidate_path = str(
        repair_context.get("candidate_artifact_path", "") or ""
    ).strip()
    candidate_source_hash = str(
        repair_context.get("lineage_candidate_artifact_hash", "")
        or repair_context.get("target_declaration_source_hash", "")
        or ""
    ).strip()
    target_statement = str(
        repair_context.get("target_theorem_statement", "") or ""
    ).strip()
    target_statement_hash = str(
        repair_context.get("target_theorem_statement_hash", "") or ""
    ).strip()
    target_statement_hash_algorithm = str(
        repair_context.get("target_theorem_statement_hash_algorithm", "") or ""
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
    elif exact_target_statement_hash(target_statement) != target_statement_hash:
        dispatch_validation_errors.append(
            "target_theorem_statement_hash does not match the shared exact-target identity"
        )
    if target_statement_hash_algorithm != EXACT_TARGET_STATEMENT_HASH_ALGORITHM:
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
            repair_context.get("target_lean_declaration", "") or ""
        ),
        "target_theorem_statement": target_statement,
        "target_theorem_statement_hash": target_statement_hash,
        "target_theorem_statement_hash_algorithm": (
            target_statement_hash_algorithm
        ),
        "target_ids": list(repair_context.get("target_ids", []) or []),
        "source_theorem_target_provenance": dict(
            repair_context.get("source_theorem_target_provenance", {}) or {}
        )
        if isinstance(
            repair_context.get("source_theorem_target_provenance", {}), Mapping
        )
        else {},
        "semantic_alignment_constraints": list(
            repair_context.get("semantic_alignment_constraints", []) or []
        ),
        "semantic_alignment_blockers": list(
            repair_context.get("semantic_alignment_blockers", []) or []
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
            )[:1200],
            "local_lean_stderr": str(
                candidate_row.get("local_lean_stderr", "") or ""
            )[:1200],
        },
        "proofengineer_repair_context_hash": stable_hash(repair_context),
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
        "repair_task": asdict(task),
        "deferred_next_task": asdict(deferred_next_task),
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
            "question and TheoryDeveloper derivation before proof search."
        ),
        inputs={
            "question": _question_to_payload(question),
            "architect_context": dict(architect_context),
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
            "target or routes concrete feedback to Formalizer/TheoryDeveloper"
        ),
        stop_condition=(
            "semantic review accepts, schedules a fresh upstream revision, or "
            "records a bounded blocker"
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
            "semantic review before proof search"
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
    if target_statement_hash_algorithm != EXACT_TARGET_STATEMENT_HASH_ALGORITHM:
        errors.append("formal-target theorem statement hash algorithm mismatch")
    if not target_statement or exact_target_statement_hash(target_statement) != str(
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
            *, id_field: str, hash_field: str, kind: str
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
            if kind and str(artifact.get("artifact_kind", "") or "") != kind:
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
            kind="FormalizerProofEngineerProposalPacket",
        )
        repair_task_payload = (
            dict(work_order.get("repair_task", {}) or {})
            if isinstance(work_order.get("repair_task", {}), Mapping)
            else {}
        )
        deferred_task_payload = (
            dict(work_order.get("deferred_next_task", {}) or {})
            if isinstance(work_order.get("deferred_next_task", {}), Mapping)
            else {}
        )
        if str(repair_task_payload.get("task_id", "") or "") != str(
            work_order.get("source_task_id", "") or ""
        ):
            validation_errors.append("formal-target review repair task identity mismatch")
        if str(deferred_task_payload.get("owner_subsystem", "") or "") != (
            "ProofEngineer"
        ):
            validation_errors.append("formal-target review deferred task is not ProofEngineer")

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
                    "model_requested_overall_verdict",
                    "model_requested_repair_owner",
                    "model_requested_repair_scope",
                    "overall_verdict",
                    "repair_scope",
                    "repair_owner",
                    "dimension_reviews",
                    "findings",
                    "repair_instructions",
                    "blocking_reason",
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
                "llm_json_repair_history": [
                    dict(row) for row in exc.history
                ],
                "last_invalid_packet_available": bool(last_invalid_packet),
                "last_invalid_packet_fingerprint": (
                    stable_hash(last_invalid_packet)
                    if last_invalid_packet
                    else ""
                ),
                "last_invalid_review_projection": (
                    invalid_review_projection
                ),
                "external_proof_search_dispatch_eligible": False,
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
                    "repair without a contract-valid verdict."
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
                            "external_proof_search_dispatch_eligible": False,
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
        repair_scope = str(review_packet.get("repair_scope", "") or "")
        repair_scopes = [
            str(value or "")
            for value in review_packet.get("repair_scopes", []) or []
            if str(value or "")
        ]
        review_findings = [
            dict(row)
            for row in review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ]
        active_repair_findings = [
            dict(row)
            for row in review_findings
            if str(row.get("repair_scope", "") or "") == repair_scope
        ]
        deferred_repair_findings = [
            dict(row)
            for row in review_findings
            if str(row.get("repair_scope", "") or "")
            not in {"", "none", repair_scope}
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
            "repair_scope": repair_scope,
            "repair_scopes": repair_scopes,
            "n_active_repair_findings": len(active_repair_findings),
            "n_deferred_repair_findings": len(deferred_repair_findings),
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
        feedback = {
            "feedback_type": "formal_target_semantic_review_feedback",
            "feedback_source": FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM,
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
            "repair_scope": repair_scope,
            "repair_scopes": repair_scopes,
            "repair_owner_agent": str(review_packet.get("repair_owner", "") or ""),
            "dimension_reviews": list(review_packet.get("dimension_reviews", []) or []),
            "findings": review_findings,
            "active_repair_findings": active_repair_findings,
            "deferred_repair_findings": deferred_repair_findings,
            "repair_instructions": list(
                review_packet.get("repair_instructions", []) or []
            ),
            "blocking_reason": str(review_packet.get("blocking_reason", "") or ""),
            "external_proof_search_dispatch_eligible": verdict == "ACCEPT",
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
            "evidence_boundary": FORMAL_TARGET_SEMANTIC_REVIEW_BOUNDARY,
        }
        revision_count = int(work_order.get("review_revision_count", 0) or 0)
        max_revisions = max(
            self.max_revisions,
            int(work_order.get("max_revisions", 0) or 0),
        )
        if verdict == "ACCEPT":
            deferred_task = _agent_task_from_runtime_payload(deferred_task_payload)
            next_inputs = dict(deferred_task.inputs)
            prior_feedback = (
                dict(next_inputs.get("environment_feedback", {}) or {})
                if isinstance(next_inputs.get("environment_feedback", {}), Mapping)
                else {}
            )
            repair_context = (
                dict(prior_feedback.get("proofengineer_repair_context", {}) or {})
                if isinstance(
                    prior_feedback.get("proofengineer_repair_context", {}), Mapping
                )
                else {}
            )
            target_provenance = (
                dict(
                    repair_context.get("source_theorem_target_provenance", {})
                    or {}
                )
                if isinstance(
                    repair_context.get("source_theorem_target_provenance", {}),
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
            repair_context.update(
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
                    "external_proof_search_dispatch_eligible": True,
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
                "proofengineer_repair_context": repair_context,
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
                "the hash-bound target is now eligible for typed prover search, "
                "but remains unproved until the runtime-owned kernel gate passes."
            )
            failure_classification = ""
        elif revision_count < max_revisions:
            repair_owner = str(review_packet.get("repair_owner", "") or "")
            prior_repair_task = _agent_task_from_runtime_payload(repair_task_payload)
            next_inputs = dict(prior_repair_task.inputs)
            prior_feedback = (
                dict(next_inputs.get("environment_feedback", {}) or {})
                if isinstance(next_inputs.get("environment_feedback", {}), Mapping)
                else {}
            )
            stale_context = (
                dict(prior_feedback.get("proofengineer_repair_context", {}) or {})
                if isinstance(
                    prior_feedback.get("proofengineer_repair_context", {}), Mapping
                )
                else {}
            )
            stale_context["external_proof_search_dispatch_eligible"] = False
            stale_context["external_proof_search_dispatch_blockers"] = [
                "Independent whole-target semantic review rejected the current "
                "exact theorem statement; generate a fresh hash-bound target."
            ]
            next_feedback = {
                **prior_feedback,
                **feedback,
                "proofengineer_repair_context": stale_context,
            }
            next_inputs["environment_feedback"] = next_feedback
            next_inputs["formal_target_semantic_review_revision_count"] = (
                revision_count + 1
            )
            next_context = dict(next_inputs.get("architect_context", {}) or {})
            next_context["environment_feedback"] = next_feedback
            next_context["runtime_feedback_loop"] = {
                **(
                    dict(next_context.get("runtime_feedback_loop", {}) or {})
                    if isinstance(
                        next_context.get("runtime_feedback_loop", {}), Mapping
                    )
                    else {}
                ),
                "source_subsystem": FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM,
                "handoff": "formal_target_semantic_review_repair",
                "semantic_review_execution_id": execution_id,
                "formal_target_semantic_review_revision_count": revision_count + 1,
            }
            next_context["formal_target_semantic_review_revision_count"] = (
                revision_count + 1
            )
            next_inputs["architect_context"] = next_context
            if repair_owner == "TheoryDeveloper":
                previous_theory_packet_id = str(
                    work_order.get("theory_packet_id", "") or ""
                ).strip()
                previous_theory_packet_hash = str(
                    work_order.get("theory_packet_hash", "") or ""
                ).strip()
                next_context["previous_theory_packet_id"] = (
                    previous_theory_packet_id
                )
                next_context["previous_theory_packet_hash"] = (
                    previous_theory_packet_hash
                )
                next_task = AgentTask(
                    task_id=(
                        f"formal-target-theory-revise:{question.id}:"
                        f"{stable_hash([execution_id, revision_count + 1])[:8]}"
                    ),
                    owner_subsystem="TheoryDeveloper",
                    objective=(
                        "Revise the mathematical derivation and theorem contract "
                        "using independent whole-target semantic-review feedback."
                    ),
                    inputs={
                        "question": _question_to_payload(question),
                        "architect_context": next_context,
                        "environment_feedback": next_feedback,
                        "previous_theory_packet_id": previous_theory_packet_id,
                        "previous_theory_packet_hash": previous_theory_packet_hash,
                        "formal_target_semantic_review_revision_count": (
                            revision_count + 1
                        ),
                    },
                    allowed_tools=("model_backend", "rag_memory", "evidence_ledger"),
                    expected_artifacts=("theory_derivation_packet",),
                    acceptance_gate=(
                        "revised derivation supports a faithful non-vacuous formal "
                        "target without claiming proof evidence"
                    ),
                    stop_condition=(
                        "revised theory routes back through formalization and review"
                    ),
                )
            else:
                next_task = replace(
                    prior_repair_task,
                    task_id=(
                        f"formal-target-review-revise:{question.id}:"
                        f"{stable_hash([execution_id, revision_count + 1])[:8]}"
                    ),
                    owner_subsystem=(
                        repair_owner
                        if repair_owner in FORMAL_TARGET_SEMANTIC_REVIEW_SOURCE_SUBSYSTEMS
                        else source_subsystem
                    ),
                    inputs=next_inputs,
                )
            status = "REVISE"
            rationale = (
                "Independent semantic review found a defect in the supplied theory "
                "and routed only theory-owned findings to TheoryDeveloper before "
                "formal-target regeneration."
                if repair_owner == "TheoryDeveloper"
                else "Independent semantic review rejected the exact theorem target "
                "while finding the supplied theory sufficient; target-owned findings "
                "are returning to Formalizer for fresh generation."
            )
            failure_classification = (
                "formal_target_semantic_review_theory_block"
                if verdict == "BLOCK"
                else "formal_target_semantic_review_revise"
            )
        else:
            next_task = None
            status = "BLOCKED"
            rationale = (
                "The exact theorem target still failed independent semantic review "
                "after the bounded revision budget; proof search remained disabled."
            )
            failure_classification = (
                "formal_target_semantic_review_revision_budget_exhausted"
            )

        if status == "REVISE" and next_task is not None:
            typed_inputs = dict(next_task.inputs)
            typed_context = dict(typed_inputs.get("architect_context", {}) or {})
            feedback_loop = (
                dict(typed_context.get("runtime_feedback_loop", {}) or {})
                if isinstance(
                    typed_context.get("runtime_feedback_loop", {}), Mapping
                )
                else {}
            )
            feedback_loop["direct_repair_handoff_contract"] = (
                build_typed_repair_handoff_contract(
                    source_reviewer_subsystem=(
                        FORMAL_TARGET_SEMANTIC_REVIEWER_SUBSYSTEM
                    ),
                    source_task_id=task.task_id,
                    target_repair_subsystem=next_task.owner_subsystem,
                    target_task_id=next_task.task_id,
                    feedback_artifact_id=review_packet_id,
                    feedback_artifact_kind="FormalTargetSemanticReviewPacket",
                    feedback_execution_id=execution_id,
                    feedback_execution_artifact_kind=(
                        "RuntimeFormalTargetSemanticReviewExecutionManifest"
                    ),
                    feedback_type="formal_target_semantic_review_feedback",
                    revision_count=revision_count + 1,
                    max_revisions=max_revisions,
                )
            )
            typed_context["runtime_feedback_loop"] = feedback_loop
            typed_inputs["architect_context"] = typed_context
            next_task = replace(next_task, inputs=typed_inputs)

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
                        "external_proof_search_dispatch_eligible": (
                            verdict == "ACCEPT"
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
