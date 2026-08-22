from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .agent_runtime import (
    RuntimeArtifactReferenceError,
    resolve_runtime_artifact_references,
    runtime_artifact_reference,
)
from .fingerprint import stable_hash
from .theory_semantic_material import (
    build_theory_semantic_material,
)
from .theory_workspace import THEORY_WORKSPACE_CONTENT_AUTHORITY


THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY = (
    "theory_developer_revision_binding"
)
THEORY_DEVELOPER_REVISION_BINDING_KIND = (
    "RuntimeTheoryDeveloperRevisionBinding"
)
THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE = (
    "THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE"
)
RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY = (
    "runtime_theory_revision_progress"
)
THEORY_DEVELOPER_RESOLVED_PARENT_MATERIAL_CONTEXT_KEY = (
    "runtime_resolved_theory_revision_parent_material"
)
THEORY_CLAIM_REVISION_DELTA_KIND = "RuntimeTheoryClaimRevisionDelta"
THEORY_CLAIM_REVISION_DELTA_NOT_PROOF_EVIDENCE = (
    "THEORY_CLAIM_REVISION_DELTA_NOT_PROOF_EVIDENCE"
)


def build_theory_claim_revision_delta(
    *,
    parent_theory_packet: Mapping[str, Any],
    revised_theory_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare model-authored claim/document references without copying mathematics."""

    if not (
        parent_theory_packet.get("theory_content_authority")
        == THEORY_WORKSPACE_CONTENT_AUTHORITY
        and revised_theory_packet.get("theory_content_authority")
        == THEORY_WORKSPACE_CONTENT_AUTHORITY
    ):
        return {}
    parent_packet_id = str(
        parent_theory_packet.get("packet_id", "") or ""
    ).strip()
    revised_packet_id = str(
        revised_theory_packet.get("packet_id", "") or ""
    ).strip()
    if not parent_packet_id or not revised_packet_id:
        return {}
    parent_question_id = _theory_packet_question_id(parent_theory_packet)
    revised_question_id = _theory_packet_question_id(revised_theory_packet)
    if (
        parent_question_id
        and revised_question_id
        and parent_question_id != revised_question_id
    ):
        raise ValueError("theory claim revision packets belong to different questions")

    parent_documents = _theory_document_reference_index(parent_theory_packet)
    revised_documents = _theory_document_reference_index(revised_theory_packet)
    parent_claims = _theory_claim_reference_index(
        parent_theory_packet,
        document_refs=parent_documents,
    )
    revised_claims = _theory_claim_reference_index(
        revised_theory_packet,
        document_refs=revised_documents,
    )
    if not parent_claims or not revised_claims:
        return {}

    parent_ids = set(parent_claims)
    revised_ids = set(revised_claims)
    added_claim_refs = [
        revised_claims[claim_id] for claim_id in sorted(revised_ids - parent_ids)
    ]
    removed_claim_refs = [
        parent_claims[claim_id] for claim_id in sorted(parent_ids - revised_ids)
    ]
    changed_claim_refs: list[dict[str, Any]] = []
    for claim_id in sorted(parent_ids.intersection(revised_ids)):
        parent_ref = parent_claims[claim_id]
        revised_ref = revised_claims[claim_id]
        changes = {
            field: {
                "parent": deepcopy(parent_ref.get(field)),
                "revised": deepcopy(revised_ref.get(field)),
            }
            for field in (
                "kind",
                "status",
                "document_path",
                "anchor",
                "depends_on",
            )
            if parent_ref.get(field) != revised_ref.get(field)
        }
        if changes:
            changed_claim_refs.append(
                {"claim_id": claim_id, "changes": changes}
            )

    changed_document_refs: list[dict[str, Any]] = []
    for path in sorted(set(parent_documents).union(revised_documents)):
        parent_ref = parent_documents.get(path, {})
        revised_ref = revised_documents.get(path, {})
        if parent_ref == revised_ref:
            continue
        change = (
            "ADDED"
            if not parent_ref
            else "REMOVED"
            if not revised_ref
            else "MODIFIED"
        )
        changed_document_refs.append(
            {
                "document_path": path,
                "change": change,
                "parent": deepcopy(parent_ref),
                "revised": deepcopy(revised_ref),
            }
        )

    parent_manifest = _mapping(
        parent_theory_packet.get("theory_workspace_manifest")
    )
    revised_manifest = _mapping(
        revised_theory_packet.get("theory_workspace_manifest")
    )
    body = {
        "schema_version": 1,
        "artifact_kind": THEORY_CLAIM_REVISION_DELTA_KIND,
        "question_id": revised_question_id or parent_question_id,
        "parent_theory_packet_id": parent_packet_id,
        "parent_theory_packet_hash": stable_hash(dict(parent_theory_packet)),
        "revised_theory_packet_id": revised_packet_id,
        "revised_theory_packet_hash": stable_hash(dict(revised_theory_packet)),
        "parent_document_set_hash": str(
            parent_manifest.get("document_set_hash", "") or ""
        ),
        "revised_document_set_hash": str(
            revised_manifest.get("document_set_hash", "") or ""
        ),
        "parent_claim_graph_hash": stable_hash(
            [parent_claims[claim_id] for claim_id in sorted(parent_claims)]
        ),
        "revised_claim_graph_hash": stable_hash(
            [revised_claims[claim_id] for claim_id in sorted(revised_claims)]
        ),
        "added_claim_refs": added_claim_refs,
        "removed_claim_refs": removed_claim_refs,
        "changed_claim_refs": changed_claim_refs,
        "changed_document_refs": changed_document_refs,
        "counts": {
            "parent_claims": len(parent_claims),
            "revised_claims": len(revised_claims),
            "unchanged_claims": (
                len(parent_ids.intersection(revised_ids))
                - len(changed_claim_refs)
            ),
            "added_claims": len(added_claim_refs),
            "removed_claims": len(removed_claim_refs),
            "changed_claims": len(changed_claim_refs),
            "changed_documents": len(changed_document_refs),
        },
        "proof_evidence_status": (
            THEORY_CLAIM_REVISION_DELTA_NOT_PROOF_EVIDENCE
        ),
        "boundary": (
            "This delta records model-authored claim IDs, direct dependencies, "
            "statuses, document anchors, and document hashes across one exact theory "
            "revision. It contains no mathematical body, execution result, semantic "
            "acceptance, or proof evidence."
        ),
    }
    body["delta_id"] = "theory_claim_revision_delta:" + stable_hash(body)[:20]
    return body


def _theory_packet_question_id(packet: Mapping[str, Any]) -> str:
    question = packet.get("question", {})
    return (
        str(question.get("id", "") or "").strip()
        if isinstance(question, Mapping)
        else ""
    )


def _theory_document_reference_index(
    packet: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    manifest = _mapping(packet.get("theory_workspace_manifest"))
    rows = manifest.get("documents", [])
    document_rows = rows if isinstance(rows, list) else []
    return {
        str(row.get("relative_path", "") or "").strip(): {
            "document_id": str(row.get("document_id", "") or ""),
            "sha256": str(row.get("sha256", "") or ""),
            "byte_size": int(row.get("byte_size", 0) or 0),
        }
        for row in document_rows
        if isinstance(row, Mapping)
        and str(row.get("relative_path", "") or "").strip()
    }


def _theory_claim_reference_index(
    packet: Mapping[str, Any],
    *,
    document_refs: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    derivation = _mapping(packet.get("theory_derivation_packet"))
    rows = derivation.get("claim_index", [])
    claim_rows = rows if isinstance(rows, list) else []
    claims: dict[str, dict[str, Any]] = {}
    for row in claim_rows:
        if not isinstance(row, Mapping):
            continue
        claim_id = str(row.get("id", "") or "").strip()
        if not claim_id:
            continue
        document_path = str(row.get("document_path", "") or "").strip()
        document_ref = document_refs.get(document_path, {})
        raw_dependencies = row.get("depends_on", [])
        dependencies = (
            raw_dependencies if isinstance(raw_dependencies, list) else []
        )
        claims[claim_id] = {
            "claim_id": claim_id,
            "kind": str(row.get("kind", "") or ""),
            "status": str(row.get("status", "") or ""),
            "document_path": document_path,
            "document_sha256": str(document_ref.get("sha256", "") or ""),
            "anchor": str(row.get("anchor", "") or ""),
            "depends_on": sorted(
                {
                    str(value).strip()
                    for value in dependencies
                    if str(value).strip()
                }
            ),
        }
    return claims


def runtime_theory_revision_count(
    architect_context: Mapping[str, Any],
) -> int:
    """Return revision lineage depth without creating a second loop budget."""

    context = dict(architect_context)
    explicit_progress = _mapping(
        context.get(RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY)
    )
    metric_gate = _mapping(context.get("architect_metric_protocol_gate"))
    return max(
        _nonnegative_int(explicit_progress.get("revisions_used", 0)),
        _nonnegative_int(
            metric_gate.get("upstream_theory_revision_count", 0)
        ),
    )


def build_theory_developer_revision_binding(
    *,
    revision_source: str,
    question_id: str,
    source_feedback: Mapping[str, Any],
    parent_theory_packet: Mapping[str, Any],
    feedback_id: str,
    upstream_theory_revision_count: int,
    execution_results_observed: bool,
    source_review_packet_id: str = "",
    source_review_execution_id: str = "",
) -> dict[str, Any]:
    """Create one immutable parent/feedback binding for a theory revision."""

    feedback = deepcopy(dict(source_feedback))
    parent_packet = dict(parent_theory_packet)
    parent_packet_id = str(parent_packet.get("packet_id", "") or "").strip()
    parent_ref = runtime_artifact_reference(parent_packet_id, parent_packet)
    body = {
        "schema_version": 1,
        "artifact_kind": THEORY_DEVELOPER_REVISION_BINDING_KIND,
        "revision_source": str(revision_source or "").strip(),
        "question_id": str(question_id or "").strip(),
        "source_theory_packet_id": parent_packet_id,
        "source_theory_packet_hash": parent_ref["content_hash"],
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
        "continuation_budget_authority": "AgentRuntime.max_iterations",
        "execution_results_observed": bool(execution_results_observed),
        "execution_authorized": False,
        "source_feedback": feedback,
        "parent_theory_packet_ref": parent_ref,
        "proof_evidence_status": (
            THEORY_DEVELOPER_REVISION_BINDING_NOT_PROOF_EVIDENCE
        ),
        "boundary": (
            "This binding authorizes one LLM theory revision against the exact "
            "named parent and routed diagnostic feedback. Canonical runtime resolves "
            "the parent packet reference only at TheoryDeveloper execution; execution "
            "outcomes are not theory claims, and the binding is neither statistical "
            "acceptance nor proof evidence."
        ),
    }
    body["binding_id"] = (
        "theory_developer_revision_binding:" + stable_hash(body)[:20]
    )
    return body


def resolve_theory_developer_revision_parent_material(
    *,
    revision_binding: Mapping[str, Any],
    artifacts: Mapping[str, Any],
) -> dict[str, Any]:
    """Hydrate one exact parent packet reference into transient semantic material."""

    parent_ref = revision_binding.get("parent_theory_packet_ref", {})
    if not isinstance(parent_ref, Mapping) or not parent_ref:
        raise ValueError("theory revision binding has no parent packet reference")
    expected_packet_id = str(
        revision_binding.get("source_theory_packet_id", "") or ""
    ).strip()
    expected_packet_hash = str(
        revision_binding.get("source_theory_packet_hash", "") or ""
    ).strip()
    if (
        str(parent_ref.get("artifact_id", "") or "").strip()
        != expected_packet_id
        or str(parent_ref.get("content_hash", "") or "").strip()
        != expected_packet_hash
    ):
        raise ValueError("theory revision parent reference identity mismatch")
    try:
        resolved_packet = resolve_runtime_artifact_references(
            parent_ref,
            artifacts,
        )
    except RuntimeArtifactReferenceError as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(resolved_packet, Mapping) or not resolved_packet:
        raise ValueError("theory revision parent packet could not be resolved")
    packet = dict(resolved_packet)
    packet_id = str(packet.get("packet_id", "") or "").strip()
    if packet_id != expected_packet_id:
        raise ValueError("theory revision parent packet identity mismatch")
    packet_question_id = _theory_packet_question_id(packet)
    binding_question_id = str(
        revision_binding.get("question_id", "") or ""
    ).strip()
    if (
        packet_question_id
        and binding_question_id
        and packet_question_id != binding_question_id
    ):
        raise ValueError("theory revision parent belongs to another question")
    material = build_theory_semantic_material(
        theory_packet=packet,
        theory_packet_id=packet_id,
    )
    material["source_theory_packet_hash"] = expected_packet_hash
    session_refs = [
        deepcopy(dict(session_ref))
        for artifact in artifacts.values()
        if isinstance(artifact, Mapping)
        and artifact.get("artifact_kind") == "TheoryDeveloperWorkspaceEvidence"
        and artifact.get("runtime_source_theory_packet_id") == packet_id
        and artifact.get("runtime_source_theory_packet_hash")
        == expected_packet_hash
        and isinstance(
            (session_ref := artifact.get("client_tool_session_ref", {})),
            Mapping,
        )
        and session_ref
    ]
    if len(session_refs) > 1 and len(
        {stable_hash(session_ref) for session_ref in session_refs}
    ) > 1:
        raise ValueError("theory revision parent has conflicting session references")
    if session_refs:
        material["parent_client_tool_session_ref"] = session_refs[-1]
    return material


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
        return {}, errors
    if str(parent_packet.get("packet_id", "") or "").strip() != parent_packet_id:
        errors.append("model-routed parent theory packet identity is inconsistent")
        return {}, errors
    parent_packet_hash = stable_hash(parent_packet)
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
    revisions_used = runtime_theory_revision_count(context)
    binding = build_theory_developer_revision_binding(
        revision_source="architect_routed_environment_observations",
        question_id=question_id,
        source_feedback=feedback,
        parent_theory_packet=parent_packet,
        feedback_id=str(feedback.get("feedback_id", "") or ""),
        upstream_theory_revision_count=revisions_used + 1,
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
    context[RUNTIME_THEORY_REVISION_PROGRESS_CONTEXT_KEY] = {
        "revisions_used": revisions_used,
        "continuation_budget_authority": "AgentRuntime.max_iterations",
        "reset_scope": "fresh_question_runtime_only",
    }
    metric_gate = _mapping(context.get("architect_metric_protocol_gate"))
    if metric_gate:
        context["architect_metric_protocol_gate"] = {
            **metric_gate,
            "upstream_theory_revision_count": revisions_used,
            "continuation_budget_authority": "AgentRuntime.max_iterations",
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
    if row.get("continuation_budget_authority") != (
        "AgentRuntime.max_iterations"
    ):
        errors.append("theory revision binding has invalid budget authority")
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

    parent_ref = row.get("parent_theory_packet_ref", {})
    if not isinstance(parent_ref, Mapping) or not parent_ref:
        errors.append("theory revision binding has no parent packet reference")
        parent_ref = {}
    if parent_ref.get("artifact_kind") != "RuntimeArtifactRef":
        errors.append("theory revision parent reference has the wrong kind")
    if parent_ref.get("reference_scope") != "runtime_blackboard":
        errors.append("theory revision parent reference has the wrong scope")
    if str(parent_ref.get("artifact_id", "") or "").strip() != source_packet_id:
        errors.append("theory revision parent reference id does not match")
    if str(parent_ref.get("content_hash", "") or "").strip() != source_packet_hash:
        errors.append("theory revision parent reference hash does not match")
    if str(parent_ref.get("payload_kind", "") or "").strip() != (
        "TheoryDerivationPacket"
    ):
        errors.append("theory revision parent reference payload kind is invalid")
    if parent_ref.get("evidence_status") != "REFERENCE_ONLY_NOT_EVIDENCE":
        errors.append("theory revision parent reference crossed the evidence boundary")

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
