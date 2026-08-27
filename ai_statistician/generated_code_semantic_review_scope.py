from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any, Mapping, Sequence

from .agent_runtime import (
    AgentStepResult,
    AgentTask,
    BlackboardState,
    agent_task_reference,
    resolve_runtime_artifact_references,
    restore_agent_task_continuation,
)
from .fingerprint import stable_hash
from .theory_workspace import load_theory_workspace_document_rows


def _generated_code_semantic_review_theory_core_projection(
    *,
    theory_packet: Mapping[str, Any],
    alignment_contract: Mapping[str, Any],
    fallback_reason: str,
) -> dict[str, Any]:
    """Keep canonical mathematical content when trace selection is unavailable."""

    semantic_fields = (
        "schema_version",
        "artifact_kind",
        "packet_id",
        "question",
        "problem_card",
        "theory_workspace_manifest",
        "theory_content_authority",
        "structured_handoff_role",
        "theory_derivation_contract",
        "theory_derivation_packet",
        "derivation_steps",
        "equation_chain",
        "assumption_ledger",
        "formalization_handoff",
        "theorem_cards",
        "lemma_cards",
        "estimator_specs",
        "estimator_interface_authoring",
        "simulation_ademp_spec",
        "formalization_requests",
        "theory_prompt_mode",
        "serious_theory_mode",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "kernel_verified",
    )
    projected = {
        field: deepcopy(theory_packet[field])
        for field in semantic_fields
        if field in theory_packet
    }
    projected["authoritative_theory_documents"] = (
        load_theory_workspace_document_rows(theory_packet)
    )
    projected["theory_review_projection"] = {
        "canonical_theory_packet_id": str(
            theory_packet.get("packet_id", "") or ""
        ),
        "canonical_theory_packet_fingerprint": stable_hash(theory_packet),
        "theory_trace_alignment_contract_fingerprint": stable_hash(
            alignment_contract
        ),
        "projection_mode": "canonical_semantic_core_fallback",
        "fallback_reason": fallback_reason,
        "excluded_non_authoritative_top_level_fields": sorted(
            str(field)
            for field in theory_packet
            if field not in projected
        ),
        "runtime_control_supplied_separately": True,
        "content_outside_projection_cannot_gate_current_artifact": True,
        "system_theory_coverage_owner": "CriticEvaluator",
        "boundary": (
            "Structured per-anchor selection is unavailable, so this review gets "
            "the canonical mathematical core rather than runtime transport, model "
            "history, next actions, or system-level critic bookkeeping. Excluded "
            "fields cannot create a generated-artifact repair obligation."
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_THEORY_REVIEW_PROJECTION_NOT_PROOF_EVIDENCE"
        ),
    }
    return projected


def generated_code_semantic_review_scope_projection(
    *,
    value: Any,
    assigned_requirements: Sequence[Mapping[str, Any]],
) -> Any:
    """Project duplicated metric context to the current source owner's rows."""

    if isinstance(value, Mapping):
        return {
            str(key): (
                [dict(row) for row in assigned_requirements]
                if str(key) == "empirical_metric_requirements"
                else generated_code_semantic_review_scope_projection(
                    value=item,
                    assigned_requirements=assigned_requirements,
                )
            )
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [
            generated_code_semantic_review_scope_projection(
                value=item,
                assigned_requirements=assigned_requirements,
            )
            for item in value
        ]
    return deepcopy(value)


def generated_code_semantic_review_theory_projection(
    *,
    theory_packet: Mapping[str, Any],
    proposal_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Limit per-artifact review to theory anchors consumed by its author."""

    alignment_contract = proposal_packet.get(
        "theory_trace_alignment_contract",
        {},
    )
    if not isinstance(alignment_contract, Mapping) or not bool(
        alignment_contract.get("structured_alignment_observed", False)
    ):
        return _generated_code_semantic_review_theory_core_projection(
            theory_packet=theory_packet,
            alignment_contract=(
                alignment_contract
                if isinstance(alignment_contract, Mapping)
                else {}
            ),
            fallback_reason="structured_theory_trace_alignment_unavailable",
        )
    raw_trace = theory_packet.get("theory_derivation_packet", {})
    if not isinstance(raw_trace, Mapping):
        return _generated_code_semantic_review_theory_core_projection(
            theory_packet=theory_packet,
            alignment_contract=alignment_contract,
            fallback_reason="canonical_theory_derivation_trace_unavailable",
        )

    claim_id_alignment = (
        str(alignment_contract.get("alignment_mode", "") or "")
        == "exact_claim_id_v1"
    )
    supported_claim_ids = _string_set(
        alignment_contract.get("supported_claim_ids", [])
    )
    claim_dependency_closure = _string_set(
        alignment_contract.get("claim_dependency_closure", [])
    ).union(supported_claim_ids)
    supported_derivation_steps = (
        set()
        if claim_id_alignment
        else _string_set(alignment_contract.get("supported_derivation_steps", []))
    )
    supported_equation_steps = (
        set()
        if claim_id_alignment
        else _string_set(alignment_contract.get("supported_equation_steps", []))
    )
    supported_assumptions = (
        set()
        if claim_id_alignment
        else _string_set(alignment_contract.get("supported_assumptions", []))
    )
    supported_formalization_targets = (
        set()
        if claim_id_alignment
        else _string_set(
            alignment_contract.get("supported_formalization_targets", [])
        )
    )
    if not any(
        (
            supported_claim_ids,
            supported_derivation_steps,
            supported_equation_steps,
            supported_assumptions,
            supported_formalization_targets,
        )
    ):
        unscoped = dict(theory_packet)
        unscoped["authoritative_theory_documents"] = (
            load_theory_workspace_document_rows(theory_packet)
        )
        return unscoped

    selected_claim_ids = (
        claim_dependency_closure if claim_id_alignment else supported_derivation_steps
    )
    derivation_steps = _rows_selected_by_field(
        raw_trace.get("derivation_steps", []),
        field="id",
        allowed=selected_claim_ids,
    )
    equation_chain = _rows_selected_by_field(
        raw_trace.get("equation_chain", []),
        field="step_id",
        allowed=supported_equation_steps,
    )
    assumption_ledger = _rows_selected_by_field(
        raw_trace.get("assumption_ledger", []),
        field="assumption",
        allowed=supported_assumptions,
    )
    sanity_checks = [
        deepcopy(row)
        for row in raw_trace.get("sanity_checks", []) or []
        if isinstance(row, Mapping)
        and (
            str(row.get("claim_ref", "") or "")
            in selected_claim_ids
            or bool(
                _string_set(row.get("depends_on", [])).intersection(
                    selected_claim_ids
                )
            )
        )
    ]
    claim_index = _rows_selected_by_field(
        raw_trace.get("claim_index", []),
        field="id",
        allowed=selected_claim_ids,
    )
    sanity_check_index = [
        deepcopy(row)
        for row in raw_trace.get("sanity_check_index", []) or []
        if isinstance(row, Mapping)
        and str(row.get("claim_ref", "") or "")
        in selected_claim_ids
    ]
    formalization_handoff = _formalization_handoff_projection(
        raw_trace.get("formalization_handoff", {}),
        supported_targets=supported_formalization_targets,
    )
    projected_trace = {
        field: value
        for field, value in {
            "derivation_steps": derivation_steps,
            "equation_chain": equation_chain,
            "assumption_ledger": assumption_ledger,
            "sanity_checks": sanity_checks,
            "claim_index": claim_index,
            "sanity_check_index": sanity_check_index,
            "formalization_handoff": formalization_handoff,
        }.items()
        if value not in (None, "", [], {})
    }
    common_fields = (
        "schema_version",
        "artifact_kind",
        "packet_id",
        "question",
        "problem_card",
        "theory_workspace_manifest",
        "theory_content_authority",
        "structured_handoff_role",
        "theory_derivation_contract",
        "theory_prompt_mode",
        "serious_theory_mode",
        "proof_evidence_status",
        "proof_evidence_boundary",
        "kernel_verified",
    )
    projected = {
        field: deepcopy(theory_packet[field])
        for field in common_fields
        if field in theory_packet
    }
    projected["theory_derivation_packet"] = projected_trace
    authoritative_documents = load_theory_workspace_document_rows(theory_packet)
    selected_document_paths = {
        str(row.get("document_path", "") or "")
        for row in claim_index
        if isinstance(row, Mapping) and str(row.get("document_path", "") or "")
    }
    projected["authoritative_theory_documents"] = (
        [
            row
            for row in authoritative_documents
            if str(row.get("path", "") or "") in selected_document_paths
        ]
        if claim_id_alignment and selected_document_paths
        else authoritative_documents
    )

    implementation_target_ids = {
        str(row.get("estimator_id", "") or "")
        for row in proposal_packet.get("implementation_targets", []) or []
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "")
    }
    if implementation_target_ids:
        estimator_specs = _rows_selected_by_field(
            theory_packet.get("estimator_specs", []),
            field="id",
            allowed=implementation_target_ids,
        )
        if estimator_specs:
            projected["estimator_specs"] = estimator_specs

    projected["theory_review_projection"] = {
        "canonical_theory_packet_id": str(
            theory_packet.get("packet_id", "") or ""
        ),
        "canonical_theory_packet_fingerprint": stable_hash(theory_packet),
        "theory_trace_alignment_contract_fingerprint": stable_hash(
            alignment_contract
        ),
        "alignment_mode": str(
            alignment_contract.get("alignment_mode", "legacy_anchor_v1")
            or "legacy_anchor_v1"
        ),
        "supported_claim_ids": sorted(supported_claim_ids),
        "claim_dependency_closure": sorted(claim_dependency_closure),
        "supported_derivation_steps": sorted(supported_derivation_steps),
        "supported_equation_steps": sorted(supported_equation_steps),
        "supported_assumptions": sorted(supported_assumptions),
        "supported_formalization_targets": sorted(
            supported_formalization_targets
        ),
        "excluded_non_authoritative_top_level_fields": sorted(
            str(field)
            for field in theory_packet
            if field not in projected
        ),
        "content_outside_projection_cannot_gate_current_artifact": True,
        "system_theory_coverage_owner": "CriticEvaluator",
        "boundary": (
            "This per-artifact projection contains the exact claims selected by the "
            "coding proposal and their declared dependency closure, or the historical "
            "legacy anchors for an older packet. Unreferenced branches, critic "
            "findings, and future work remain available to system-level theory review "
            "but cannot create a repair obligation for this generated-code artifact."
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_THEORY_REVIEW_PROJECTION_NOT_PROOF_EVIDENCE"
        ),
    }
    return projected


def generated_code_semantic_review_proposal_projection(
    *,
    source_subsystem: str,
    proposal_packet: Mapping[str, Any],
    assigned_requirements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Expose only current-artifact claims, not advisory future work."""

    common_fields = (
        "schema_version",
        "artifact_kind",
        "packet_id",
        "question",
        "source_agent",
        "model",
        "model_tier",
        "theory_trace_alignment_contract",
        "theory_trace_consumption_contract",
        "empirical_evaluation_phase",
        "confirmatory_empirical_evidence_eligible",
    )
    projected = {
        field: deepcopy(proposal_packet[field])
        for field in common_fields
        if field in proposal_packet
    }
    reviewed_claim_fields = list(projected)
    if source_subsystem == "AlgorithmEngineer":
        projected["implementation_targets"] = [
            {
                field: deepcopy(row[field])
                for field in (
                    "estimator_id",
                    "adapter_strategy",
                    "data_contract",
                    "estimator_interface_contract",
                    "estimator_interface_contract_id",
                    "estimator_interface_contract_authority",
                )
                if field in row
            }
            for row in proposal_packet.get("implementation_targets", []) or []
            if isinstance(row, Mapping)
        ]
        reviewed_claim_fields.append("implementation_targets")
    elif source_subsystem == "SimulationEvaluator":
        for field in (
            "simulation_targets",
            "runtime_budget",
            "runtime_execution_plan",
        ):
            if field in proposal_packet:
                projected[field] = deepcopy(proposal_packet[field])
                reviewed_claim_fields.append(field)
    projected = generated_code_semantic_review_scope_projection(
        value=projected,
        assigned_requirements=assigned_requirements,
    )
    projected["proposal_review_projection"] = {
        "canonical_proposal_packet_id": str(
            proposal_packet.get("packet_id", "") or ""
        ),
        "canonical_proposal_fingerprint": stable_hash(proposal_packet),
        "reviewed_claim_fields": reviewed_claim_fields,
        "excluded_non_authoritative_fields": sorted(
            str(field)
            for field in proposal_packet
            if field not in reviewed_claim_fields
        ),
        "advisory_fields_cannot_create_acceptance_obligations": True,
        "exact_generated_source_supplied_separately": True,
        "boundary": (
            "The semantic reviewer receives current-artifact implementation "
            "claims only. LLM-authored next actions, validation ideas, risk notes, "
            "and duplicate code envelopes are advisory and cannot expand the "
            "Architect-frozen acceptance contract."
        ),
        "proof_evidence_status": (
            "GENERATED_CODE_PROPOSAL_REVIEW_PROJECTION_NOT_PROOF_EVIDENCE"
        ),
    }
    return projected


def generated_code_semantic_review_upstream_dependency_projection(
    *,
    source_subsystem: str,
    upstream_algorithm_handoff: Mapping[str, Any],
) -> dict[str, Any]:
    """Expose a runtime-validated dependency separately from consumer claims."""

    if source_subsystem != "SimulationEvaluator":
        return {}
    handoff = upstream_algorithm_handoff
    exact_artifacts = [
        {
            "artifact_id": str(row.get("estimator_id", "") or ""),
            "exact_source_code": str(
                row.get("exact_source_code", "") or ""
            ),
            "exact_source_hash": str(
                row.get("exact_source_hash", "") or ""
            ),
            "exact_result_hash": str(
                row.get("exact_smoke_result_hash", "") or ""
            ),
            "exact_result_included": False,
            "language": str(row.get("language", "") or ""),
            "dependencies": list(row.get("dependencies", []) or []),
            "estimator_interface_contract": deepcopy(
                row.get("estimator_interface_contract", {})
                if isinstance(
                    row.get("estimator_interface_contract", {}),
                    Mapping,
                )
                else {}
            ),
            "estimator_interface_contract_id": str(
                row.get("estimator_interface_contract_id", "") or ""
            ),
            "estimator_interface_contract_authority": deepcopy(
                row.get("estimator_interface_contract_authority", {})
                if isinstance(
                    row.get("estimator_interface_contract_authority", {}),
                    Mapping,
                )
                else {}
            ),
        }
        for row in handoff.get("exact_algorithm_artifacts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "")
        and str(row.get("exact_source_code", "") or "")
    ]
    if not exact_artifacts:
        return {}
    return {
        "dependency_owner_subsystem": "AlgorithmEngineer",
        "consumer_subsystem": source_subsystem,
        "algorithm_sandbox_manifest_id": str(
            handoff.get("algorithm_sandbox_manifest_id", "") or ""
        ),
        "algorithm_sandbox_manifest_hash": str(
            handoff.get("algorithm_sandbox_manifest_hash", "") or ""
        ),
        "accepted_semantic_review_execution_id": str(
            handoff.get("semantic_review_execution_id", "") or ""
        ),
        "accepted_semantic_review_packet_id": str(
            handoff.get("semantic_review_packet_id", "") or ""
        ),
        "exact_dependency_artifacts": exact_artifacts,
        "current_source_may_not_modify_dependency": True,
        "routing_rule": (
            "A defect in an injected dependency belongs to its immutable upstream "
            "generated artifact, not to the current consumer source. Return the "
            "raw observation to that artifact's source-owning workspace, execute "
            "the replacement unchanged, independently review its new hash, and "
            "then rerun every dependent artifact under unchanged evidence gates."
        ),
        "proof_evidence_status": (
            "UPSTREAM_GENERATED_DEPENDENCY_NOT_PROOF_EVIDENCE"
        ),
    }


def generated_code_semantic_review_upstream_dependency_errors(
    dependency: Mapping[str, Any],
) -> list[str]:
    """Validate included bytes and hash-only outcome references by their own rules."""

    errors: list[str] = []
    if dependency and any(
        not str(dependency.get(field, "") or "")
        for field in (
            "algorithm_sandbox_manifest_id",
            "algorithm_sandbox_manifest_hash",
            "accepted_semantic_review_execution_id",
            "accepted_semantic_review_packet_id",
        )
    ):
        errors.append("upstream generated dependency lineage is incomplete")
    for row in dependency.get("exact_dependency_artifacts", []) or []:
        if not isinstance(row, Mapping):
            errors.append("upstream generated dependency is not an object")
            continue
        artifact_id = str(row.get("artifact_id", "") or "")
        source = str(row.get("exact_source_code", "") or "")
        if not artifact_id or not source:
            errors.append("upstream generated dependency is incomplete")
            continue
        if str(row.get("exact_source_hash", "") or "") != stable_hash(source):
            errors.append(
                f"upstream generated dependency source hash mismatch: {artifact_id}"
            )
        result_hash = str(row.get("exact_result_hash", "") or "")
        result_included = bool(
            row.get("exact_result_included", "exact_result" in row)
        )
        if result_included:
            result = row.get("exact_result", {})
            if not isinstance(result, Mapping) or result_hash != stable_hash(result):
                errors.append(
                    f"upstream generated dependency result hash mismatch: {artifact_id}"
                )
        elif "exact_result" in row:
            errors.append(
                "withheld upstream generated dependency unexpectedly includes a "
                f"result: {artifact_id}"
            )
        elif not result_hash:
            errors.append(
                f"upstream generated dependency result hash is missing: {artifact_id}"
            )
    return errors


def generated_code_semantic_review_upstream_dependency_artifacts(
    dependency: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Materialize dependency source while retaining intentionally withheld outcomes."""

    artifacts: list[dict[str, Any]] = []
    for row in dependency.get("exact_dependency_artifacts", []) or []:
        if not isinstance(row, Mapping):
            continue
        artifact = {
            "artifact_id": str(row.get("artifact_id", "") or ""),
            "exact_source_hash": str(row.get("exact_source_hash", "") or ""),
            "exact_source_code": str(row.get("exact_source_code", "") or ""),
            "exact_source_code_complete": True,
            "exact_result_hash": str(row.get("exact_result_hash", "") or ""),
            "actual_runtime_arguments": {},
            "artifact_role": "upstream_generated_dependency",
        }
        if row.get("exact_result_included") is True:
            artifact["exact_result"] = dict(row.get("exact_result", {}) or {})
        else:
            artifact["exact_result_withheld"] = True
            artifact["result_authority_owner"] = "AlgorithmEngineer"
        artifacts.append(artifact)
    return artifacts


def algorithm_handoff_artifacts(
    exact_artifacts: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Keep reviewed executable code while referring to raw outcomes by hash."""

    return [
        {
            str(key): deepcopy(value)
            for key, value in row.items()
            if str(key) != "exact_smoke_result"
        }
        for row in exact_artifacts
        if isinstance(row, Mapping)
    ]


def _executable_evaluator_source_identity(
    manifest: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Identify exact evaluator bytes without interpreting statistical content."""

    raw_rows = manifest.get("generated_simulation_sandbox_prototypes", [])
    if not isinstance(raw_rows, Sequence) or isinstance(raw_rows, (str, bytes, bytearray)):
        return [], ["executable evaluator source rows are not a sequence"]
    identities: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, raw_row in enumerate(raw_rows):
        if not isinstance(raw_row, Mapping):
            errors.append(f"executable evaluator source row {index} is not an object")
            continue
        artifact_id = str(raw_row.get("simulation_id", "")
                          or raw_row.get("estimator_id", "")
                          or raw_row.get("prototype_artifact_id", "") or "").strip()
        script_hash = str(raw_row.get("script_hash", "") or "").strip()
        source_code = str(raw_row.get("source_code", "") or "")
        language = str(raw_row.get("language", "") or "").strip().lower()
        if not artifact_id:
            errors.append(f"executable evaluator source row {index} lacks an id")
            continue
        if artifact_id in seen_ids:
            errors.append(f"duplicate executable evaluator source id: {artifact_id}")
            continue
        seen_ids.add(artifact_id)
        if not source_code or not script_hash:
            errors.append(
                f"executable evaluator source bytes or hash missing: {artifact_id}"
            )
            continue
        if stable_hash(source_code) != script_hash:
            errors.append(f"executable evaluator source hash mismatch: {artifact_id}")
        identities.append(
            {
                "artifact_id": artifact_id,
                "script_hash": script_hash,
                "language": language,
                "dependencies": sorted(str(value) for value in
                                       raw_row.get("dependencies", []) or [] if str(value)),
                "required_estimator_ids": sorted(str(value) for value in
                                                  raw_row.get("required_estimator_ids", []) or [] if str(value)),
            }
        )
    if not identities:
        errors.append("executable evaluator source identity is empty")
    return sorted(identities, key=lambda row: row["artifact_id"]), sorted(set(errors))


def executable_evaluator_review_binding(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    confirmation_manifest_id: str,
    confirmation_manifest: Mapping[str, Any],
    required_reviewer_model_tier: str = "",
) -> dict[str, Any]:
    """Bind hidden confirmation to reviewed, byte-identical evaluator authoring."""

    errors: list[str] = []
    if (
        confirmation_manifest.get("artifact_kind") != "RuntimeSimulationManifest"
        or str(confirmation_manifest.get("manifest_id", "") or "")
        != confirmation_manifest_id
    ):
        errors.append("executable evaluator confirmation manifest identity is invalid")
    for field in (
        "executable_evaluator_source_authority",
        "evaluator_source_confirmation",
        "confirmatory_empirical_evidence_eligible",
        "consumer_resume_exact_source_replayed",
    ):
        if confirmation_manifest.get(field) is not True:
            errors.append(f"executable evaluator confirmation requires {field}=true")

    authoring_manifest_id = str(
        confirmation_manifest.get("consumer_resume_manifest_id", "") or ""
    ).strip()
    authoring_manifest_hash = str(
        confirmation_manifest.get("consumer_resume_manifest_hash", "") or ""
    ).strip()
    authoring_manifest = artifacts.get(authoring_manifest_id, {})
    if not authoring_manifest_id or not isinstance(authoring_manifest, Mapping):
        errors.append("executable evaluator authoring manifest is missing")
        authoring_manifest = {}
    elif stable_hash(dict(authoring_manifest)) != authoring_manifest_hash:
        errors.append("executable evaluator authoring manifest hash mismatch")
    if authoring_manifest:
        if (
            authoring_manifest.get("artifact_kind") != "RuntimeSimulationManifest"
            or str(authoring_manifest.get("manifest_id", "") or "")
            != authoring_manifest_id
        ):
            errors.append("executable evaluator authoring manifest identity is invalid")
        for field in (
            "executable_evaluator_source_authority",
            "evaluator_source_authoring",
        ):
            if authoring_manifest.get(field) is not True:
                errors.append(f"executable evaluator authoring requires {field}=true")
        if authoring_manifest.get("confirmatory_empirical_evidence_eligible") is not False:
            errors.append(
                "executable evaluator authoring must remain non-confirmatory"
            )

    authoring_identity, authoring_errors = _executable_evaluator_source_identity(authoring_manifest)
    confirmation_identity, confirmation_errors = _executable_evaluator_source_identity(confirmation_manifest)
    errors.extend(authoring_errors)
    errors.extend(confirmation_errors)
    if authoring_identity != confirmation_identity:
        errors.append("executable evaluator confirmation changed reviewed source bytes")

    expected_tier = str(required_reviewer_model_tier or "").strip().lower()
    expected_authoring_hash = stable_hash(dict(authoring_manifest)) if authoring_manifest else ""
    accepted_reviews = [
        (str(artifact_id), artifact)
        for artifact_id, artifact in artifacts.items()
        if isinstance(artifact, Mapping)
        and artifact.get("artifact_kind") == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
        and artifact.get("source_subsystem") == "SimulationEvaluator"
        and artifact.get("source_manifest_id") == authoring_manifest_id
        and artifact.get("source_manifest_hash") == expected_authoring_hash
        and artifact.get("semantic_review_accepted") is True
        and artifact.get("independent_agent") is True
        and artifact.get("independent_invocation") is True
        and (not expected_tier or str(artifact.get("reviewer_model_tier", "") or "").lower() == expected_tier)
    ]
    if not accepted_reviews:
        errors.append(
            "executable evaluator authoring lacks an accepted independent review"
        )
    review_execution_id = (str(accepted_reviews[-1][1].get("execution_id", "")
                               or accepted_reviews[-1][0]) if accepted_reviews else "")
    return {
        "valid": not errors,
        "confirmation_manifest_id": confirmation_manifest_id,
        "authoring_manifest_id": authoring_manifest_id,
        "authoring_manifest_hash": authoring_manifest_hash,
        "review_execution_id": review_execution_id,
        "source_identity": confirmation_identity,
        "validation_errors": sorted(set(errors)),
        "proof_evidence_status": "EXECUTABLE_EVALUATOR_REVIEW_BINDING_NOT_PROOF_EVIDENCE",
    }


def accepted_semantic_review_deferred_continuation(
    *,
    task: AgentTask,
    result: AgentStepResult,
    next_task: AgentTask,
    blackboard: BlackboardState,
) -> bool:
    """Recognize the exact task restored after an accepted source review."""

    if task.owner_subsystem != "GeneratedCodeSemanticReviewer" or result.status != "REROUTE":
        return False
    work_order_id = str(task.inputs.get("work_order_id", "") or "")
    work_order = blackboard.artifacts.get(work_order_id, {})
    work_order_hash = str(task.inputs.get("work_order_hash", "") or "")
    if not (
        isinstance(work_order, Mapping)
        and work_order.get("artifact_kind") == "RuntimeGeneratedCodeSemanticReviewWorkOrder"
        and stable_hash(work_order) == work_order_hash
    ):
        return False
    accepted = any(
        isinstance(artifact, Mapping)
        and artifact.get("artifact_kind") == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
        and artifact.get("work_order_id") == work_order_id
        and artifact.get("work_order_hash") == work_order_hash
        and artifact.get("source_subsystem") == work_order.get("source_subsystem")
        and artifact.get("source_manifest_id") == work_order.get("source_manifest_id")
        and artifact.get("source_manifest_hash") == work_order.get("source_manifest_hash")
        and artifact.get("semantic_review_accepted") is True
        and artifact.get("independent_agent") is True
        and artifact.get("independent_invocation") is True
        for artifact in result.produced_artifacts.values()
    )
    if not accepted:
        return False
    continuation_id = str(work_order.get("deferred_next_task_continuation_id", "") or "")
    continuation = blackboard.artifacts.get(continuation_id, {})
    if not (
        isinstance(continuation, Mapping)
        and continuation.get("artifact_kind") == "RuntimeAgentTaskContinuation"
        and stable_hash(continuation) == str(
            work_order.get("deferred_next_task_continuation_hash", "") or ""
        )
        and continuation.get("task_ref") == work_order.get("deferred_next_task_ref")
    ):
        return False
    try:
        persisted = restore_agent_task_continuation(continuation, blackboard.artifacts)
        deferred = replace(
            persisted,
            inputs=resolve_runtime_artifact_references(persisted.inputs, blackboard.artifacts),
        )
    except ValueError:
        return False
    if (
        agent_task_reference(persisted) != work_order.get("deferred_next_task_ref")
        or deferred.owner_subsystem != next_task.owner_subsystem
        or deferred.objective != next_task.objective
        or deferred.allowed_tools != next_task.allowed_tools
        or deferred.expected_artifacts != next_task.expected_artifacts
        or deferred.acceptance_gate != next_task.acceptance_gate
        or deferred.stop_condition != next_task.stop_condition
    ):
        return False
    return all(
        key == "architect_context" or next_task.inputs.get(key) == value
        for key, value in deferred.inputs.items()
    )


def _string_set(value: Any) -> set[str]:
    if not isinstance(value, list | tuple | set | frozenset):
        return set()
    return {str(row) for row in value if str(row)}


def _rows_selected_by_field(
    value: Any,
    *,
    field: str,
    allowed: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [
        deepcopy(row)
        for row in value
        if isinstance(row, Mapping)
        and str(row.get(field, "") or "") in allowed
    ]


def _formalization_handoff_projection(
    value: Any,
    *,
    supported_targets: set[str],
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    projected: dict[str, Any] = {}
    for field, raw_value in value.items():
        if isinstance(raw_value, list | tuple):
            matched = [
                deepcopy(row)
                for row in raw_value
                if str(row) in supported_targets
            ]
            if matched:
                projected[str(field)] = matched
        elif str(raw_value) in supported_targets:
            projected[str(field)] = deepcopy(raw_value)
    return projected
