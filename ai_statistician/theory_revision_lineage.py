from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .fingerprint import stable_hash
from .metric_protocol_stage import build_theory_informed_metric_protocol_material


THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY = (
    "theory_developer_revision_binding"
)
THEORY_DEVELOPER_REVISION_BINDING_KIND = (
    "RuntimeTheoryDeveloperRevisionBinding"
)
THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE = (
    "THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE"
)


def build_theory_developer_revision_binding(
    *,
    revision_source: str,
    question_id: str,
    source_feedback: Mapping[str, Any],
    theory_material: Mapping[str, Any],
    feedback_id: str,
    upstream_theory_revision_count: int,
    max_upstream_theory_revisions: int,
    execution_results_observed: bool,
    source_review_packet_id: str = "",
    source_review_execution_id: str = "",
) -> dict[str, Any]:
    """Create one immutable parent/feedback binding for a theory revision."""

    feedback = deepcopy(dict(source_feedback))
    material = deepcopy(dict(theory_material))
    body = {
        "schema_version": 1,
        "artifact_kind": THEORY_DEVELOPER_REVISION_BINDING_KIND,
        "revision_source": str(revision_source or "").strip(),
        "question_id": str(question_id or "").strip(),
        "source_theory_packet_id": str(
            material.get("source_theory_packet_id", "") or ""
        ).strip(),
        "source_theory_packet_hash": str(
            material.get("source_theory_packet_hash", "") or ""
        ).strip(),
        "feedback_id": str(feedback_id or "").strip(),
        "source_feedback_fingerprint": stable_hash(feedback),
        "source_review_packet_id": str(source_review_packet_id or "").strip(),
        "source_review_execution_id": str(
            source_review_execution_id or ""
        ).strip(),
        "target_consumer_subsystem": "TheoryDeveloper",
        "upstream_theory_revision_count": max(
            0, int(upstream_theory_revision_count or 0)
        ),
        "max_upstream_theory_revisions": max(
            0, int(max_upstream_theory_revisions or 0)
        ),
        "execution_results_observed": bool(execution_results_observed),
        "execution_authorized": False,
        "source_feedback": feedback,
        "theory_material": material,
        "proof_evidence_status": (
            THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE
        ),
        "boundary": (
            "This binding authorizes one LLM theory revision against the exact "
            "named parent and routed diagnostic feedback. The parent semantic "
            "material is immutable, execution outcomes are not theory claims, and "
            "the binding is neither statistical acceptance nor proof evidence."
        ),
    }
    body["binding_id"] = (
        "theory_developer_revision_binding:" + stable_hash(body)[:20]
    )
    return body


def build_postexecution_theory_revision_binding(
    *,
    architect_context: Mapping[str, Any],
    question_id: str,
    artifacts: Mapping[str, Any],
    budget_state: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Adapt one generated-code review into the shared revision contract."""

    context = dict(architect_context)
    replan = budget_state.get("replan", {})
    replan = dict(replan) if isinstance(replan, Mapping) else {}
    source_feedback = context.get(
        "theory_developer_source_environment_feedback", {}
    )
    if not isinstance(source_feedback, Mapping) or not source_feedback:
        source_feedback = context.get("environment_feedback", {})
    feedback = dict(source_feedback) if isinstance(source_feedback, Mapping) else {}
    dispatch = context.get("architect_typed_repair_dispatch", {})
    dispatch = dict(dispatch) if isinstance(dispatch, Mapping) else {}
    pending_ids = replan.get("pending_artifact_ids", {})
    pending_ids = dict(pending_ids) if isinstance(pending_ids, Mapping) else {}

    errors: list[str] = []
    if replan.get("artifact_kind") != (
        "RuntimeGeneratedCodeSemanticReviewReplanContext"
    ):
        errors.append("post-execution theory revision has no typed replan context")
    if str(replan.get("question_id", "") or "") != question_id:
        errors.append("post-execution theory replan belongs to another question")
    if replan.get("repair_scope") != "upstream_theory":
        errors.append("post-execution theory replan is not upstream_theory")
    if feedback.get("feedback_type") != "generated_code_semantic_review_feedback":
        errors.append("post-execution theory revision has the wrong feedback type")
    if feedback.get("repair_scope") != "upstream_theory":
        errors.append("post-execution feedback is not routed to upstream theory")

    review_packet_id = str(replan.get("review_packet_id", "") or "").strip()
    review_execution_id = str(
        replan.get("review_execution_id", "") or ""
    ).strip()
    if not review_packet_id or review_packet_id != str(
        feedback.get("semantic_review_packet_id", "") or ""
    ).strip():
        errors.append("post-execution review packet lineage does not match")
    if not review_execution_id or review_execution_id != str(
        feedback.get("semantic_review_execution_id", "") or ""
    ).strip():
        errors.append("post-execution review execution lineage does not match")

    if dispatch.get("artifact_kind") != "RuntimeArchitectTypedRepairDispatch":
        errors.append("post-execution theory revision has no typed Architect dispatch")
    if dispatch.get("repair_scope") != "upstream_theory":
        errors.append("typed Architect dispatch is not for upstream theory")
    if str(dispatch.get("question_id", "") or "") != question_id:
        errors.append("typed Architect dispatch belongs to another question")
    if str(dispatch.get("review_packet_id", "") or "") != review_packet_id:
        errors.append("typed Architect dispatch review packet does not match")
    if str(dispatch.get("review_execution_id", "") or "") != review_execution_id:
        errors.append("typed Architect dispatch review execution does not match")
    if str(dispatch.get("feedback_fingerprint", "") or "") != stable_hash(feedback):
        errors.append("typed Architect dispatch feedback fingerprint does not match")

    parent_packet_id = str(
        pending_ids.get("theory_packet_id", "") or ""
    ).strip()
    current_packet_id = str(context.get("theory_packet_id", "") or "").strip()
    if not parent_packet_id:
        errors.append("post-execution theory replan has no parent theory packet id")
    if parent_packet_id != current_packet_id:
        errors.append("post-execution theory replan is not bound to current theory")

    parent_packet = artifacts.get(parent_packet_id, {})
    if not isinstance(parent_packet, Mapping) or not parent_packet:
        errors.append("post-execution parent theory packet is absent from blackboard")
        theory_material: dict[str, Any] = {}
    else:
        theory_material = build_theory_informed_metric_protocol_material(
            theory_packet=parent_packet,
            theory_packet_id=parent_packet_id,
        )
    expected_parent_hash = str(
        replan.get("theory_packet_hash", "") or ""
    ).strip()
    actual_parent_hash = str(
        theory_material.get("source_theory_packet_hash", "") or ""
    ).strip()
    if not expected_parent_hash or expected_parent_hash != actual_parent_hash:
        errors.append("post-execution parent theory hash does not match review lineage")

    carried_material = context.get("architect_metric_protocol_theory_material", {})
    carried_material = (
        dict(carried_material) if isinstance(carried_material, Mapping) else {}
    )
    if str(carried_material.get("source_theory_packet_id", "") or "") != (
        parent_packet_id
    ):
        errors.append("current theory handoff does not name the reviewed parent")
    if str(carried_material.get("source_theory_packet_hash", "") or "") != (
        actual_parent_hash
    ):
        errors.append("current theory handoff bytes do not match the reviewed parent")

    binding = build_theory_developer_revision_binding(
        revision_source="generated_code_semantic_review_postexecution",
        question_id=question_id,
        source_feedback=feedback,
        theory_material=theory_material,
        feedback_id=str(feedback.get("feedback_id", "") or ""),
        upstream_theory_revision_count=(
            int(budget_state.get("revisions_used", 0) or 0) + 1
        ),
        max_upstream_theory_revisions=int(
            budget_state.get("max_revisions", 0) or 0
        ),
        execution_results_observed=True,
        source_review_packet_id=review_packet_id,
        source_review_execution_id=review_execution_id,
    )
    errors.extend(
        theory_developer_revision_binding_errors(
            binding,
            question_id=question_id,
        )
    )
    return binding, list(dict.fromkeys(errors))


def theory_developer_revision_binding_errors(
    binding: Mapping[str, Any] | None,
    *,
    question_id: str,
) -> list[str]:
    """Validate identity, immutable parent bytes, and feedback provenance."""

    row = binding or {}
    errors: list[str] = []
    if row.get("artifact_kind") != THEORY_DEVELOPER_REVISION_BINDING_KIND:
        errors.append("theory revision binding has the wrong artifact kind")
    if not str(row.get("revision_source", "") or "").strip():
        errors.append("theory revision binding has no revision source")
    if str(row.get("question_id", "") or "").strip() != str(
        question_id or ""
    ).strip():
        errors.append("theory revision binding belongs to another question")
    if row.get("target_consumer_subsystem") != "TheoryDeveloper":
        errors.append("theory revision binding is not routed to TheoryDeveloper")
    if row.get("execution_authorized") is not False:
        errors.append("theory revision binding cannot authorize execution")
    if row.get("proof_evidence_status") != (
        THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE
    ):
        errors.append("theory revision binding crossed the proof boundary")

    source_packet_id = str(
        row.get("source_theory_packet_id", "") or ""
    ).strip()
    source_packet_hash = str(
        row.get("source_theory_packet_hash", "") or ""
    ).strip()
    feedback_id = str(row.get("feedback_id", "") or "").strip()
    if not source_packet_id:
        errors.append("theory revision binding has no parent packet id")
    if not source_packet_hash:
        errors.append("theory revision binding has no parent packet hash")
    if not feedback_id:
        errors.append("theory revision binding has no feedback id")

    source_feedback = row.get("source_feedback", {})
    if not isinstance(source_feedback, Mapping) or not source_feedback:
        errors.append("theory revision binding has no routed source feedback")
        source_feedback = {}
    if str(source_feedback.get("feedback_id", "") or "").strip() != feedback_id:
        errors.append("theory revision binding feedback id does not match its payload")
    feedback_packet_id = str(
        source_feedback.get("source_theory_packet_id", "") or ""
    ).strip()
    if feedback_packet_id and feedback_packet_id != source_packet_id:
        errors.append("revision feedback and parent material packet ids must match")
    feedback_packet_hash = str(
        source_feedback.get("source_theory_packet_hash", "") or ""
    ).strip()
    if feedback_packet_hash and feedback_packet_hash != source_packet_hash:
        errors.append("revision feedback and parent material packet hashes must match")
    feedback_question_id = str(
        source_feedback.get("question_id", "") or ""
    ).strip()
    if feedback_question_id and feedback_question_id != str(
        question_id or ""
    ).strip():
        errors.append("revision feedback belongs to another question")
    feedback_target = str(
        source_feedback.get("target_consumer_subsystem", "") or ""
    ).strip()
    if feedback_target and feedback_target != "TheoryDeveloper":
        errors.append("revision feedback is not routed to TheoryDeveloper")
    if source_feedback.get("execution_authorized") is True:
        errors.append("routed theory revision feedback cannot authorize execution")
    expected_feedback_fingerprint = str(
        row.get("source_feedback_fingerprint", "") or ""
    ).strip()
    if (
        not expected_feedback_fingerprint
        or expected_feedback_fingerprint != stable_hash(dict(source_feedback))
    ):
        errors.append("theory revision binding feedback fingerprint does not match")

    material = row.get("theory_material", {})
    if not isinstance(material, Mapping) or not material:
        errors.append("theory revision binding has no immutable theory material")
        material = {}
    if material.get("artifact_kind") != (
        "RuntimeTheoryInformedMetricProtocolMaterial"
    ):
        errors.append("theory revision binding has invalid theory material")
    if material.get("execution_results_available") is not False:
        errors.append("theory revision parent material contains execution results")
    if str(material.get("source_theory_packet_id", "") or "").strip() != (
        source_packet_id
    ):
        errors.append("theory revision parent packet id does not match its material")
    if str(material.get("source_theory_packet_hash", "") or "").strip() != (
        source_packet_hash
    ):
        errors.append("theory revision parent packet hash does not match its material")

    semantic_material = material.get("theory_semantic_material", {})
    if not isinstance(semantic_material, Mapping) or not semantic_material:
        errors.append("theory revision parent has no lossless semantic material")
        semantic_material = {}
    semantic_packet_id = str(
        semantic_material.get("packet_id", "") or ""
    ).strip()
    if semantic_packet_id and semantic_packet_id != source_packet_id:
        errors.append("theory revision semantic packet id does not match its parent")
    semantic_question = semantic_material.get("question", {})
    semantic_question_id = (
        str(semantic_question.get("id", "") or "").strip()
        if isinstance(semantic_question, Mapping)
        else ""
    )
    if semantic_question_id and semantic_question_id != str(
        question_id or ""
    ).strip():
        errors.append("theory revision parent belongs to another question")

    binding_id = str(row.get("binding_id", "") or "").strip()
    unsigned = {
        key: deepcopy(value)
        for key, value in row.items()
        if key != "binding_id"
    }
    expected_binding_id = (
        "theory_developer_revision_binding:" + stable_hash(unsigned)[:20]
    )
    if not binding_id or binding_id != expected_binding_id:
        errors.append("theory revision binding fingerprint does not match")
    return list(dict.fromkeys(errors))
