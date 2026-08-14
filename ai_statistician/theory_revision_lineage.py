from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .fingerprint import stable_hash
from .theory_semantic_material import (
    THEORY_SEMANTIC_MATERIAL_KINDS,
    THEORY_SEMANTIC_MATERIAL_PROOF_STATUSES,
    build_theory_semantic_material,
)


THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY = (
    "theory_developer_revision_binding"
)
THEORY_DEVELOPER_REVISION_BINDING_KIND = (
    "RuntimeTheoryDeveloperRevisionBinding"
)
THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE = (
    "THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE"
)
RUNTIME_THEORY_REVISION_BUDGET_CONTEXT_KEY = (
    "runtime_theory_revision_budget"
)


def runtime_theory_revision_budget(
    architect_context: Mapping[str, Any],
    *,
    default_max_revisions: int = 1,
) -> tuple[int, int]:
    """Return the strict question-level theory revision budget."""

    context = dict(architect_context)
    explicit_budget = _mapping(
        context.get(RUNTIME_THEORY_REVISION_BUDGET_CONTEXT_KEY)
    )
    metric_gate = _mapping(context.get("architect_metric_protocol_gate"))

    revisions_used = max(
        _nonnegative_int(explicit_budget.get("revisions_used", 0)),
        _nonnegative_int(
            metric_gate.get("upstream_theory_revision_count", 0)
        ),
    )
    declared_limits = []
    if "max_revisions" in explicit_budget:
        declared_limits.append(
            _nonnegative_int(explicit_budget.get("max_revisions"))
        )
    if "max_upstream_theory_revisions" in metric_gate:
        declared_limits.append(
            _nonnegative_int(
                metric_gate.get("max_upstream_theory_revisions")
            )
        )
    max_revisions = (
        min(declared_limits)
        if declared_limits
        else max(0, int(default_max_revisions or 0))
    )
    return revisions_used, max_revisions


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


def build_architect_routed_theory_revision_binding(
    *,
    architect_context: Mapping[str, Any],
    question_id: str,
    artifacts: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Bind any Architect-routed observations to one immutable theory parent."""

    context = dict(architect_context)
    feedback = _mapping(context.get("theory_developer_source_environment_feedback"))
    if not feedback:
        feedback = _mapping(context.get("environment_feedback"))
    route_packet = _mapping(context.get("architect_feedback_route_decision"))
    routing = _mapping(context.get("architect_initial_routing"))
    errors: list[str] = []

    if not feedback:
        errors.append("model-routed theory revision has no environment observations")
    if not str(feedback.get("feedback_id", "") or "").strip():
        errors.append("model-routed theory revision feedback has no identity")
    feedback_question_id = str(
        feedback.get("question_id", "") or ""
    ).strip()
    if feedback_question_id and feedback_question_id != question_id:
        errors.append("model-routed theory revision feedback belongs to another question")
    if feedback.get("overall_verdict") == "ACCEPT":
        errors.append("accepted observations cannot request a theory revision")
    if feedback.get("execution_authorized") is True:
        errors.append("model-routed theory feedback cannot authorize execution")

    route_id = ""
    expected_routing_source = "architect_packet"
    if route_packet:
        route_id = str(route_packet.get("route_decision_id", "") or "").strip()
        expected_routing_source = "architect_feedback_route_model"
        if route_packet.get("artifact_kind") != "ArchitectFeedbackRouteDecision":
            errors.append("model-routed theory revision has the wrong route artifact")
        if route_packet.get("decision") != "ROUTE":
            errors.append("model-routed theory revision has no Architect ROUTE decision")
        if route_packet.get("selected_subsystem") != "TheoryDeveloper":
            errors.append("Architect feedback route did not select TheoryDeveloper")
        if str(
            route_packet.get("environment_feedback_fingerprint", "") or ""
        ) != stable_hash(feedback):
            errors.append("Architect feedback route does not match observation bytes")
    else:
        route_id = str(
            context.get("architect_coordinator_proposal_id", "") or ""
        ).strip()
        if not route_id:
            errors.append("model-routed theory revision has no Architect model packet")

    if routing.get("artifact_kind") != "ArchitectInitialRoutingDecision":
        errors.append("model-routed theory revision has no Architect routing record")
    if str(routing.get("architect_packet_id", "") or "") != route_id:
        errors.append("Architect routing record does not match its model packet")
    if str(routing.get("question_id", "") or "") != question_id:
        errors.append("Architect routing record belongs to another question")
    if routing.get("source") != expected_routing_source:
        errors.append("theory revision was not selected by the Architect model")
    if routing.get("requested_subsystem") != "TheoryDeveloper" or routing.get(
        "selected_subsystem"
    ) != "TheoryDeveloper":
        errors.append("Architect model route did not select TheoryDeveloper")
    if str(routing.get("environment_feedback_hash", "") or "") != stable_hash(
        feedback
    ):
        errors.append("Architect routing record does not match observation bytes")

    parent_packet_id = str(
        context.get("theory_packet_id", "")
        or feedback.get("source_theory_packet_id", "")
        or ""
    ).strip()
    parent_packet = _mapping(artifacts.get(parent_packet_id))
    if not parent_packet:
        errors.append("model-routed parent theory packet is absent from blackboard")
        theory_material: dict[str, Any] = {}
    else:
        theory_material = build_theory_semantic_material(
            theory_packet=parent_packet,
            theory_packet_id=parent_packet_id,
        )
    parent_packet_hash = str(
        theory_material.get("source_theory_packet_hash", "") or ""
    ).strip()
    feedback_parent_id = str(
        feedback.get("source_theory_packet_id", "") or ""
    ).strip()
    feedback_parent_hash = str(
        feedback.get("source_theory_packet_hash", "") or ""
    ).strip()
    if feedback_parent_id and feedback_parent_id != parent_packet_id:
        errors.append("routed observations name a different parent theory packet")
    if feedback_parent_hash and feedback_parent_hash != parent_packet_hash:
        errors.append("routed observations do not match parent theory bytes")

    carried_material = _mapping(
        context.get("architect_metric_protocol_theory_material")
    )
    if carried_material and (
        str(carried_material.get("source_theory_packet_id", "") or "").strip()
        != parent_packet_id
        or str(
            carried_material.get("source_theory_packet_hash", "") or ""
        ).strip()
        != parent_packet_hash
    ):
        errors.append("current theory handoff does not match parent theory bytes")

    review_packet_id = str(
        feedback.get("semantic_review_packet_id", "") or ""
    ).strip()
    review_execution_id = str(
        feedback.get("semantic_review_execution_id", "") or ""
    ).strip()
    revisions_used, max_revisions = runtime_theory_revision_budget(context)
    if max_revisions <= 0 or revisions_used >= max_revisions:
        errors.append(
            "question-level TheoryDeveloper revision budget is exhausted"
        )
    binding = build_theory_developer_revision_binding(
        revision_source="architect_routed_environment_observations",
        question_id=question_id,
        source_feedback=feedback,
        theory_material=theory_material,
        feedback_id=str(feedback.get("feedback_id", "") or ""),
        upstream_theory_revision_count=revisions_used + 1,
        max_upstream_theory_revisions=max_revisions,
        execution_results_observed=bool(
            feedback.get("execution_results_observed", False)
        ),
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


def consume_architect_routed_theory_revision(
    *,
    architect_context: Mapping[str, Any],
    revision_binding: Mapping[str, Any],
    revised_theory_packet_id: str,
    revised_theory_packet_hash: str,
) -> dict[str, Any]:
    """Retire model-routed feedback after a fresh theory packet is produced."""

    context = dict(architect_context)
    parent_packet_id = str(
        revision_binding.get("source_theory_packet_id", "") or ""
    ).strip()
    if not (
        revision_binding.get("revision_source")
        == "architect_routed_environment_observations"
        and parent_packet_id
        and revised_theory_packet_id
        and revised_theory_packet_id != parent_packet_id
        and revised_theory_packet_hash
    ):
        return context

    resolution = {
        "artifact_kind": "RuntimeModelRoutedTheoryRevisionResolution",
        "resolution_status": "CONSUMED_BY_MODEL_ROUTED_THEORY_REVISION",
        "question_id": str(revision_binding.get("question_id", "") or ""),
        "source_feedback_id": str(
            revision_binding.get("feedback_id", "") or ""
        ),
        "source_feedback_fingerprint": str(
            revision_binding.get("source_feedback_fingerprint", "") or ""
        ),
        "source_feedback_type": str(
            _mapping(revision_binding.get("source_feedback")).get(
                "feedback_type", ""
            )
            or ""
        ),
        "execution_results_observed": bool(
            revision_binding.get("execution_results_observed", False)
        ),
        "source_review_execution_id": str(
            revision_binding.get("source_review_execution_id", "") or ""
        ),
        "source_review_packet_id": str(
            revision_binding.get("source_review_packet_id", "") or ""
        ),
        "prior_theory_packet_id": parent_packet_id,
        "prior_theory_packet_hash": str(
            revision_binding.get("source_theory_packet_hash", "") or ""
        ),
        "revised_theory_packet_id": revised_theory_packet_id,
        "revised_theory_packet_hash": revised_theory_packet_hash,
        "theory_revision_binding_id": str(
            revision_binding.get("binding_id", "") or ""
        ),
        "next_subsystem_was_model_selected": True,
        "proof_evidence_status": (
            "MODEL_ROUTED_THEORY_REVISION_RESOLUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    resolution["resolution_id"] = (
        "model_routed_theory_revision_resolution:"
        + stable_hash(resolution)[:20]
    )
    context["runtime_model_routed_theory_revision_resolution"] = resolution
    revisions_used = _nonnegative_int(
        revision_binding.get("upstream_theory_revision_count", 0)
    )
    max_revisions = _nonnegative_int(
        revision_binding.get("max_upstream_theory_revisions", 0)
    )
    context[RUNTIME_THEORY_REVISION_BUDGET_CONTEXT_KEY] = {
        "revisions_used": revisions_used,
        "max_revisions": max_revisions,
        "budget_exhausted": bool(
            max_revisions <= 0 or revisions_used >= max_revisions
        ),
        "reset_scope": "fresh_question_runtime_only",
    }
    metric_gate = _mapping(context.get("architect_metric_protocol_gate"))
    if metric_gate:
        context["architect_metric_protocol_gate"] = {
            **metric_gate,
            "upstream_theory_revision_count": revisions_used,
            "max_upstream_theory_revisions": max_revisions,
        }
    for key in (
        "environment_feedback",
        "theory_developer_source_environment_feedback",
        "runtime_feedback_loop",
        "runtime_generated_code_semantic_review_replan",
        "formal_target_semantic_review_replan",
        "workspace_replan",
        "runtime_metric_gate_replan",
        "runtime_packet_validation_replan",
        "accepted_algorithm_handoff",
        "accepted_implementation_interface_handoff",
        "accepted_algorithm_semantic_review_materialization",
        "simulation_generated_code_draft",
    ):
        context.pop(key, None)
    context["previous_theory_packet_id"] = parent_packet_id
    context["theory_packet_id"] = revised_theory_packet_id
    return context


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


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
    if material.get("artifact_kind") not in THEORY_SEMANTIC_MATERIAL_KINDS:
        errors.append("theory revision binding has invalid theory material")
    if (
        material.get("proof_evidence_status")
        not in THEORY_SEMANTIC_MATERIAL_PROOF_STATUSES
    ):
        errors.append("theory revision parent crossed the proof boundary")
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
        errors.append("theory revision parent has no current semantic material")
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


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
