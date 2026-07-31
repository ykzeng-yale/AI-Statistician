from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


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
        return dict(theory_packet)
    raw_trace = theory_packet.get("theory_derivation_packet", {})
    if not isinstance(raw_trace, Mapping):
        return dict(theory_packet)

    supported_derivation_steps = _string_set(
        alignment_contract.get("supported_derivation_steps", [])
    )
    supported_equation_steps = _string_set(
        alignment_contract.get("supported_equation_steps", [])
    )
    supported_assumptions = _string_set(
        alignment_contract.get("supported_assumptions", [])
    )
    supported_formalization_targets = _string_set(
        alignment_contract.get("supported_formalization_targets", [])
    )
    if not any(
        (
            supported_derivation_steps,
            supported_equation_steps,
            supported_assumptions,
            supported_formalization_targets,
        )
    ):
        return dict(theory_packet)

    derivation_steps = _rows_selected_by_field(
        raw_trace.get("derivation_steps", []),
        field="id",
        allowed=supported_derivation_steps,
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
            in supported_derivation_steps
            or bool(
                _string_set(row.get("depends_on", [])).intersection(
                    supported_derivation_steps
                )
            )
        )
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
            "This per-artifact projection contains only theory anchors that the "
            "coding proposal's validated trace-alignment contract consumed. "
            "Unreferenced derivation branches, critic findings, and future work "
            "remain available to system-level theory review but cannot create a "
            "repair obligation for this generated-code artifact."
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
        "implementation_gaps",
        "theory_trace_alignment",
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
                    "registered_template_hint",
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
        upstream_handoff = proposal_packet.get(
            "upstream_algorithm_handoff",
            {},
        )
        if isinstance(upstream_handoff, Mapping) and upstream_handoff:
            projected["upstream_algorithm_handoff"] = {
                field: deepcopy(value)
                for field, value in upstream_handoff.items()
                if field != "exact_algorithm_artifacts"
            }
            projected["upstream_algorithm_handoff"][
                "exact_algorithm_artifact_refs"
            ] = [
                {
                    "artifact_id": str(
                        row.get("estimator_id", "") or ""
                    ),
                    "exact_source_hash": str(
                        row.get("exact_source_hash", "") or ""
                    ),
                }
                for row in upstream_handoff.get(
                    "exact_algorithm_artifacts",
                    [],
                )
                or []
                if isinstance(row, Mapping)
            ]
            reviewed_claim_fields.append("upstream_algorithm_handoff")
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
            "exact_result": deepcopy(
                row.get("exact_smoke_result", {})
                if isinstance(row.get("exact_smoke_result", {}), Mapping)
                else {}
            ),
            "exact_result_hash": str(
                row.get("exact_smoke_result_hash", "") or ""
            ),
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
            "generated artifact, not to the current consumer source. Repair it "
            "through ArchitectCoordinator and its owning coding subsystem, then "
            "rerun every dependent artifact under unchanged evidence gates."
        ),
        "proof_evidence_status": (
            "UPSTREAM_GENERATED_DEPENDENCY_NOT_PROOF_EVIDENCE"
        ),
    }


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
