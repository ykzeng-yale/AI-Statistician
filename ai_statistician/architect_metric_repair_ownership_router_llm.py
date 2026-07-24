from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT,
    ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY,
)
from .fingerprint import stable_hash
from .llm_json_repair import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .model_backend import GeneratorBackend, GeneratorRequest, resolve_generator_model
from .research_schema import OpenResearchQuestion


ARCHITECT_METRIC_REPAIR_OWNERSHIP_SCHEMA_VERSION = 5
ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION = (
    "pre_execution_metric_protocol"
)
ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION = (
    "post_execution_generated_code"
)
ARCHITECT_METRIC_REPAIR_ROUTING_PHASES = (
    ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
    ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
)
ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY = "source_theory_packet"
ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL = "metric_protocol_candidate"
ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY = (
    "upstream_generated_dependency"
)
ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE = "generated_source_artifact"
ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY = (
    "upstream_generated_dependency"
)
ARCHITECT_METRIC_REPAIR_TARGETS = (
    ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY,
    ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL,
)
ARCHITECT_GENERATED_CODE_REPAIR_TARGETS = (
    ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY,
    ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL,
    ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY,
    ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE,
)
ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED = "unresolved"
ARCHITECT_METRIC_REPAIR_OWNERSHIP_CERTAINTIES = (
    "resolved",
    "resolved_no_change",
    "unresolved",
)
ARCHITECT_METRIC_REPAIR_OWNERSHIP_NOT_PROOF_EVIDENCE = (
    "ARCHITECT_METRIC_REPAIR_OWNERSHIP_NOT_PROOF_EVIDENCE"
)
ARCHITECT_METRIC_REPAIR_OWNERSHIP_BOUNDARY = (
    "Repair ownership routing classifies which immutable artifact must change. It "
    "does not repair statistical theory, authorize generated execution, accept an "
    "empirical protocol, relax a frozen post-result gate, or provide theorem proof "
    "evidence."
)

_POSTEXECUTION_EVIDENCE_PREFIXES_BY_ARTIFACT_ROLE = {
    ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY: (
        "source_theory_packet",
        "theory_packet",
        "theory_derivation",
    ),
    ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL: (
        "architect_frozen_evidence_contract",
        "metric_protocol_candidate",
        "empirical_metric_requirement",
    ),
    ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY: (
        "upstream_generated_dependency",
        "exact_dependency_artifacts",
        "algorithm_sandbox_manifest",
    ),
    ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE: (
        "coding_agent_proposal_packet",
        "exact_executed_artifacts",
        "exact_result",
        "exact_source_code",
        "generated_source_artifact",
        "result",
        "simulation_manifest",
        "source_manifest",
        "source_responsibility_contract",
    ),
}
_POSTEXECUTION_OUTCOME_EVIDENCE_PREFIXES = (
    "exact_dependency_artifacts",
    "exact_executed_artifacts",
    "exact_result",
    "execution",
    "metric_contract_evaluation",
    "result",
    "simulation_manifest",
    "source_manifest",
    "upstream_generated_dependency",
)


@dataclass(frozen=True)
class ArchitectMetricRepairOwnershipRouterConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 5000
    temperature: float = 0.0
    provider_name: str = "anthropic"
    max_repair_attempts: int = 1


class LLMArchitectMetricRepairOwnershipRouterAgent:
    """Independent artifact-owner router for rejected metric-review findings."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: ArchitectMetricRepairOwnershipRouterConfig = (
            ArchitectMetricRepairOwnershipRouterConfig()
        ),
    ) -> None:
        self.provider = provider
        self.config = config

    def route(
        self,
        *,
        question: OpenResearchQuestion,
        review_material: Mapping[str, Any],
        semantic_review_packet: Mapping[str, Any],
        trusted_lineage: Mapping[str, Any],
    ) -> dict[str, Any]:
        semantic_review_findings = _ownership_routing_findings(
            semantic_review_packet
        )
        routing_material = {
            "theory_developer_protocol_material": review_material.get(
                "theory_developer_protocol_material", {}
            ),
            "empirical_metric_requirements": review_material.get(
                "empirical_metric_requirements", []
            ),
            "semantic_review_findings": semantic_review_findings,
            "execution_results_available": False,
            "frozen_protocol_immutable_after_execution": False,
        }
        return self._route(
            question=question,
            routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
            routing_material=routing_material,
            semantic_review_packet=semantic_review_packet,
            trusted_lineage=trusted_lineage,
        )

    def route_generated_code_review(
        self,
        *,
        question: OpenResearchQuestion,
        review_material: Mapping[str, Any],
        semantic_review_packet: Mapping[str, Any],
        trusted_lineage: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Route post-execution defects without letting results retune a gate."""

        semantic_review_findings = _ownership_routing_findings(
            semantic_review_packet,
            actionable_only=True,
        )
        artifact_projection = _postexecution_router_artifact_projection(
            review_material
        )
        routing_material = {
            **artifact_projection,
            "semantic_review_artifact_assessments": _mapping_projection(
                semantic_review_packet,
                (
                    "reviewed_source_assessment",
                    "frozen_metric_contract_assessment",
                    "source_theory_assessment",
                ),
            ),
            "semantic_review_dimensions": list(
                semantic_review_packet.get("dimension_reviews", []) or []
            ),
            "semantic_review_findings": semantic_review_findings,
            "artifact_target_eligibility": (
                _postexecution_artifact_target_eligibility(
                    semantic_review_findings,
                    semantic_review_dimensions=list(
                        semantic_review_packet.get("dimension_reviews", []) or []
                    ),
                    available_artifact_roles=(
                        _postexecution_available_artifact_roles(
                            artifact_projection
                        )
                    ),
                )
            ),
            "execution_results_available": True,
            "frozen_protocol_immutable_after_execution": True,
        }
        return self._route(
            question=question,
            routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
            routing_material=routing_material,
            semantic_review_packet=semantic_review_packet,
            trusted_lineage=trusted_lineage,
        )

    def _route(
        self,
        *,
        question: OpenResearchQuestion,
        routing_phase: str,
        routing_material: Mapping[str, Any],
        semantic_review_packet: Mapping[str, Any],
        trusted_lineage: Mapping[str, Any],
    ) -> dict[str, Any]:
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        request = GeneratorRequest(
            system_prompt=ARCHITECT_METRIC_REPAIR_OWNERSHIP_SYSTEM_PROMPT,
            user_prompt=build_architect_metric_repair_ownership_prompt(
                question=question,
                routing_material=routing_material,
                routing_phase=routing_phase,
            ),
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            schema=architect_metric_repair_ownership_json_schema(
                routing_phase
            ),
            metadata={
                "subsystem": "ArchitectMetricRepairOwnershipRouter",
                "agent": "LLMArchitectMetricRepairOwnershipRouterAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                "routing_input_fingerprint": stable_hash(routing_material),
                "routing_phase": routing_phase,
                "provider_structured_output": True,
            },
        )

        def build_packet(
            payload: Mapping[str, Any],
            response: Any,
            raw_text: str,
        ) -> dict[str, Any]:
            return _normalize_architect_metric_repair_ownership_packet(
                payload,
                question=question,
                routing_phase=routing_phase,
                routing_material=routing_material,
                semantic_review_packet=semantic_review_packet,
                trusted_lineage=trusted_lineage,
                model=response.model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or response.provider,
                raw_response=raw_text,
            )

        try:
            return generate_validated_json_packet(
                provider=self.provider,
                request=request,
                extract_payload=extract_json_object,
                build_packet=build_packet,
                validate_packet=(
                    validate_architect_metric_repair_ownership_packet
                ),
                validation_label="Architect metric repair ownership packet",
                max_repair_attempts=self.config.max_repair_attempts,
                repair_context_builder=lambda **kwargs: (
                    _architect_metric_repair_ownership_repair_context(
                        routing_phase=routing_phase,
                        routing_material=routing_material,
                        invalid_packet=(
                            kwargs.get("invalid_packet")
                            if isinstance(
                                kwargs.get("invalid_packet"), Mapping
                            )
                            else None
                        ),
                    )
                ),
            )
        except PacketValidationError as exc:
            return _unresolved_architect_metric_repair_ownership_packet(
                question=question,
                routing_phase=routing_phase,
                routing_material=routing_material,
                semantic_review_packet=semantic_review_packet,
                trusted_lineage=trusted_lineage,
                model=request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name,
                validation_failure=exc,
            )


def _ownership_routing_findings(
    semantic_review_packet: Mapping[str, Any],
    *,
    actionable_only: bool = False,
) -> list[dict[str, Any]]:
    untrusted_owner_fields = {
        "repair_scope",
        "repair_scopes",
        "repair_owner",
        "repair_plan",
        "required_change",
        "model_requested_repair_scope",
    }
    findings: list[dict[str, Any]] = []
    for row in semantic_review_packet.get("findings", []) or []:
        if not isinstance(row, Mapping):
            continue
        if actionable_only and str(row.get("repair_scope", "") or "") not in {
            "source_code",
            "upstream_metric_contract",
            "upstream_theory",
        }:
            continue
        findings.append(
            {
                str(key): value
                for key, value in row.items()
                if str(key) not in untrusted_owner_fields
            }
        )
    return findings


def _architect_metric_repair_ownership_repair_context(
    *,
    routing_phase: str,
    routing_material: Mapping[str, Any],
    invalid_packet: Mapping[str, Any] | None,
) -> dict[str, Any]:
    findings = routing_material.get("semantic_review_findings", [])
    finding_count = len(findings) if isinstance(findings, list) else 0
    invalid_decisions = (
        invalid_packet.get("decisions", [])
        if isinstance(invalid_packet, Mapping)
        else []
    )
    return {
        "routing_phase": routing_phase,
        "required_finding_indices": list(range(finding_count)),
        "allowed_artifact_roles": list(
            _ownership_targets_for_phase(routing_phase)
        ),
        "artifact_target_eligibility": deepcopy(
            routing_material.get("artifact_target_eligibility", [])
        ),
        "invalid_decisions": [
            {
                key: deepcopy(row[key])
                for key in (
                    "finding_index",
                    "required_artifact_changes",
                    "ownership_certainty",
                )
                if key in row
            }
            for row in invalid_decisions
            if isinstance(row, Mapping)
        ],
        "repair_instructions": [
            "Return exactly one decision for every required_finding_indices value.",
            (
                "For post-execution routing, choose artifact roles only from that "
                "finding's artifact_target_eligibility row."
            ),
            (
                "Preserve valid decisions and repair only the indexed ownership or "
                "target inconsistency named by local validation."
            ),
            (
                "Use ownership_certainty=unresolved with no targets when the supplied "
                "eligible artifacts cannot support a unique owner."
            ),
        ],
    }


def _postexecution_router_artifact_projection(
    review_material: Mapping[str, Any],
) -> dict[str, Any]:
    theory_packet = review_material.get("theory_packet", {})
    proposal_packet = review_material.get("coding_agent_proposal_packet", {})
    exact_artifacts = review_material.get("exact_executed_artifacts", [])
    return {
        "source_theory_packet": _mapping_projection(
            theory_packet,
            (
                "packet_id",
                "question",
                "problem_card",
                "theory_derivation_packet",
                "theory_derivation_contract",
                "estimator_specs",
                "theorem_cards",
                "lemma_cards",
                "simulation_ademp_spec",
                "formalization_requests",
                "critic_findings",
                "serious_theory_mode",
            ),
        ),
        "metric_protocol_candidate": deepcopy(
            review_material.get("architect_frozen_evidence_contract", {})
        ),
        "generated_source_artifact": {
            "coding_agent_proposal_packet": _mapping_projection(
                proposal_packet,
                (
                    "packet_id",
                    "question",
                    "simulation_targets",
                    "empirical_metric_requirements",
                    "metric_contracts",
                    "runtime_budget",
                    "runtime_execution_plan",
                    "theory_trace_alignment",
                    "theory_trace_alignment_contract",
                    "theory_trace_consumption_contract",
                    "critic_findings",
                ),
            ),
            "source_responsibility_contract": deepcopy(
                review_material.get("source_responsibility_contract", {})
            ),
            "review_scope_projection": deepcopy(
                review_material.get("review_scope_projection", {})
            ),
            "exact_executed_artifacts": [
                _postexecution_exact_artifact_projection(row)
                for row in exact_artifacts
                if isinstance(row, Mapping)
            ]
            if isinstance(exact_artifacts, list)
            else [],
        },
        "upstream_generated_dependency": deepcopy(
            review_material.get("upstream_generated_dependency", {})
        ),
    }


def _mapping_projection(
    value: Any,
    fields: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        field: deepcopy(value[field])
        for field in fields
        if field in value
    }


def _postexecution_exact_artifact_projection(
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    exact_result = artifact.get("exact_result", {})
    source_row = artifact.get("source_row", {})
    return {
        **_mapping_projection(
            artifact,
            (
                "artifact_id",
                "actual_runtime_arguments",
                "exact_source_code",
                "exact_source_hash",
                "exact_result_hash",
            ),
        ),
        "exact_result_summary": deepcopy(
            exact_result.get("summary", {})
            if isinstance(exact_result, Mapping)
            else {}
        ),
        "source_execution_summary": _mapping_projection(
            source_row,
            (
                "backend",
                "bound_estimator_code_hashes",
                "dependencies",
                "estimator_binding_errors",
                "estimator_invocation_counts",
                "estimator_runtime_errors",
                "execution_attempted",
                "execution_smoke_passed",
                "language",
                "mechanical_estimator_invocation_verified",
                "metric_contract_evaluation",
                "metric_gate_errors",
                "metric_gate_policy_mode",
                "metric_gate_targets",
                "metric_requirement_set_id",
                "returncode",
                "runtime_errors",
                "runtime_replicates",
                "runtime_seed",
                "safety_errors",
                "script_hash",
                "simulation_id",
                "spec",
                "stderr_summary",
                "stdout_summary",
            ),
        ),
    }


def _postexecution_available_artifact_roles(
    artifact_projection: Mapping[str, Any],
) -> set[str]:
    available = {
        role
        for role in (
            ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY,
            ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL,
        )
        if isinstance(artifact_projection.get(role), Mapping)
        and artifact_projection.get(role)
    }
    current_source = artifact_projection.get(
        ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE,
        {},
    )
    if (
        isinstance(current_source, Mapping)
        and current_source.get("exact_executed_artifacts")
    ):
        available.add(ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE)
    dependency = artifact_projection.get(
        ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY,
        {},
    )
    if (
        isinstance(dependency, Mapping)
        and dependency.get("exact_dependency_artifacts")
    ):
        available.add(
            ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY
        )
    return available


def _postexecution_artifact_target_eligibility(
    findings: list[dict[str, Any]],
    *,
    semantic_review_dimensions: list[Any],
    available_artifact_roles: set[str] | None = None,
) -> list[dict[str, Any]]:
    dimension_evidence_refs = {
        str(row.get("dimension", "") or "").strip().lower(): [
            str(ref or "").strip().lower()
            for ref in row.get("evidence_refs", []) or []
            if str(ref or "").strip()
        ]
        for row in semantic_review_dimensions
        if isinstance(row, Mapping)
        and str(row.get("dimension", "") or "").strip()
    }
    dimension_artifact_citations = {
        str(row.get("dimension", "") or "").strip().lower(): [
            str(role or "").strip()
            for role in row.get("artifact_citations", []) or []
            if str(role or "").strip()
            in ARCHITECT_GENERATED_CODE_REPAIR_TARGETS
        ]
        for row in semantic_review_dimensions
        if isinstance(row, Mapping)
        and str(row.get("dimension", "") or "").strip()
    }
    eligibility: list[dict[str, Any]] = []
    for finding_index, finding in enumerate(findings):
        direct_evidence_refs = [
            str(ref or "").strip().lower()
            for ref in finding.get("evidence_refs", []) or []
            if str(ref or "").strip()
        ]
        referenced_dimensions = [
            dimension
            for dimension in dimension_evidence_refs
            if any(
                evidence_ref.startswith(dimension)
                for evidence_ref in direct_evidence_refs
            )
        ]
        evidence_refs = list(
            dict.fromkeys(
                [
                    *direct_evidence_refs,
                    *[
                        evidence_ref
                        for dimension in referenced_dimensions
                        for evidence_ref in dimension_evidence_refs[dimension]
                    ],
                ]
            )
        )
        direct_artifact_citations = [
            str(role or "").strip()
            for role in finding.get("artifact_citations", []) or []
            if str(role or "").strip()
            in ARCHITECT_GENERATED_CODE_REPAIR_TARGETS
        ]
        typed_artifact_citations = list(
            dict.fromkeys(
                [
                    *direct_artifact_citations,
                    *[
                        role
                        for dimension in referenced_dimensions
                        for role in dimension_artifact_citations.get(
                            dimension, []
                        )
                    ],
                ]
            )
        )
        rooted_evidence_roles = {
            role
            for role in ARCHITECT_GENERATED_CODE_REPAIR_TARGETS
            if any(
                evidence_ref.startswith(f"{role}#")
                for evidence_ref in evidence_refs
            )
        }
        if "artifact_citations" in finding:
            eligible_roles = [
                role
                for role in ARCHITECT_GENERATED_CODE_REPAIR_TARGETS
                if role in typed_artifact_citations
                and (
                    available_artifact_roles is None
                    or role in available_artifact_roles
                )
            ]
        else:
            # Compatibility for replaying schema-v3 reviewer packets. Fresh
            # schema-v4+ packets carry typed citations and never use this parser.
            eligible_roles = [
                role
                for role, prefixes in (
                    _POSTEXECUTION_EVIDENCE_PREFIXES_BY_ARTIFACT_ROLE.items()
                )
                if any(
                    evidence_ref.startswith(prefix)
                    for evidence_ref in evidence_refs
                    for prefix in prefixes
                )
                and (
                    available_artifact_roles is None
                    or role in available_artifact_roles
                )
            ]
        if ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL in eligible_roles:
            fresh_rooted_evidence = bool(evidence_refs) and all(
                any(
                    evidence_ref.startswith(f"{role}#")
                    for role in ARCHITECT_GENERATED_CODE_REPAIR_TARGETS
                )
                for evidence_ref in evidence_refs
            )
            metric_protocol_evidence_eligible = (
                ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL
                in rooted_evidence_roles
                and not rooted_evidence_roles.intersection(
                    {
                        ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE,
                        (
                            ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY
                        ),
                    }
                )
                if fresh_rooted_evidence
                else not any(
                    prefix in evidence_ref
                    for evidence_ref in evidence_refs
                    for prefix in _POSTEXECUTION_OUTCOME_EVIDENCE_PREFIXES
                )
            )
            if not metric_protocol_evidence_eligible:
                eligible_roles.remove(
                    ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL
                )
        eligibility.append(
            {
                "finding_index": finding_index,
                "eligible_artifact_roles": eligible_roles,
                "basis": (
                    "A post-execution target is eligible only when the finding "
                    "cites that artifact. A frozen metric protocol is eligible "
                    "only from outcome-independent protocol evidence."
                ),
                "expanded_review_dimensions": referenced_dimensions,
            }
        )
    return eligibility


def _ownership_targets_for_phase(routing_phase: str) -> tuple[str, ...]:
    if routing_phase == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION:
        return ARCHITECT_GENERATED_CODE_REPAIR_TARGETS
    return ARCHITECT_METRIC_REPAIR_TARGETS


def _ownership_artifact_role_descriptions(
    routing_phase: str,
) -> dict[str, str]:
    descriptions = {
        ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY: (
            "the immutable TheoryDeveloper packet whose estimand, procedure, "
            "estimator, DGP, assumptions, derivations, calibrations, or "
            "feasibility claims may require revision"
        ),
        ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL: (
            "the proposed or frozen measurement, evaluator encoding, aggregation, "
            "threshold, source anchors, or coverage rows"
        ),
        ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY: (
            "an exact immutable generated artifact injected into the current "
            "consumer and owned by its upstream coding subsystem"
        ),
        ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE: (
            "the exact generated source, runtime argument binding, or returned "
            "measurement implementation"
        ),
    }
    return {
        role: descriptions[role]
        for role in _ownership_targets_for_phase(routing_phase)
    }


def build_architect_metric_repair_ownership_prompt(
    *,
    question: OpenResearchQuestion,
    routing_material: Mapping[str, Any],
    routing_phase: str = ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
) -> str:
    findings = routing_material.get("semantic_review_findings", [])
    finding_count = len(findings) if isinstance(findings, list) else 0
    payload = {
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "routing_material": dict(routing_material),
        "reviewed_finding_count": finding_count,
        "required_finding_indices": list(range(finding_count)),
        "routing_phase": routing_phase,
        "artifact_roles": _ownership_artifact_role_descriptions(routing_phase),
        "required_output_contract": (
            ARCHITECT_METRIC_REPAIR_OWNERSHIP_OUTPUT_CONTRACT
        ),
        "boundary": ARCHITECT_METRIC_REPAIR_OWNERSHIP_BOUNDARY,
    }
    phase_instruction = (
        "No execution result exists. Decide whether each defect originates in the "
        "source theory packet or only in the proposed metric protocol. "
        if routing_phase
        == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION
        else "Execution results are visible, but the accepted metric protocol is "
        "frozen. A failed gate, conservative result, noisy estimate, zero event, or "
        "unexpected performance is empirical evidence about the candidate and is "
        "not by itself a protocol defect. Target metric_protocol_candidate only "
        "when exact pre-execution protocol fields are structurally contradictory, "
        "undefined, unidentifiable, or infeasible independently of the observed "
        "outcome. Such a decision terminates the current candidate and requires a "
        "new independently reviewed protocol; never propose an in-place threshold "
        "relaxation. Target generated_source_artifact for an exact source, runtime-"
        "argument, measurement-path, or implementation mismatch under coherent "
        "theory and protocol. Target upstream_generated_dependency when the current "
        "consumer invokes an immutable generated dependency and the defect is inside "
        "that dependency rather than the consumer. The consumer cannot compensate "
        "for such a defect; its owning coding subsystem must produce a fresh "
        "independently reviewed dependency before descendants rerun. Target "
        "source_theory_packet when a premise, formula, "
        "procedure, calibration, or feasibility claim is missing or contradictory. "
        "Use the minimum necessary owner under a downstream-repair counterfactual: "
        "first ask whether a correct generated-source repair can restore exact "
        "agreement while leaving the mathematical theory and frozen protocol "
        "unchanged. Finite-precision arithmetic, numerical stability, overflow or "
        "underflow, loop boundaries, runtime checks, logging, diagnostics, and "
        "stress-test coverage belong to generated_source_artifact unless the source "
        "theory explicitly makes a claim about that computational model. A finite "
        "Monte Carlo observation or a missing non-required diagnostic does not make "
        "the mathematical theory incomplete. Target source_theory_packet only when "
        "an exact theory field is false, internally contradictory, or omits research "
        "semantics needed by every coherent implementation. In that case identify "
        "the exact field and explain why generated-source-only repair cannot restore "
        "conformance. If one post-execution finding genuinely supports both "
        "generated_source_artifact or upstream_generated_dependency and "
        "source_theory_packet, include both supported roles; the runtime will make "
        "one bounded generated-source repair to the earliest cited artifact and "
        "independently "
        "re-review before changing theory. When separate findings require a concrete "
        "generated-source repair and a theory reassessment under the same coherent "
        "frozen protocol, repair and independently re-review the generated source "
        "once before escalating the still-open theory finding. A structurally invalid "
        "frozen protocol remains the earlier owner because it terminates the current "
        "candidate. "
        "Use only artifact roles listed in artifact_target_eligibility for that "
        "finding. Eligibility is derived from the finding's artifact evidence; it "
        "is an authority constraint, not a suggestion. If exact artifacts establish "
        "that a reviewer marked an advisory observation as mandatory even though no "
        "artifact must change, use ownership_certainty=resolved_no_change, no targets, "
        "and explain why in the rationale. This disposition cannot accept a lineage "
        "by itself; it is ignored only when another concrete repair forces fresh "
        "generation and independent re-review. "
    )
    return (
        "Route every semantic-review finding to the artifact or artifacts that must "
        "change. Return ONLY JSON matching required_output_contract. Do not repeat "
        "the reviewer's repair_scope without independently checking the supplied "
        "theory and candidate. Treat any artifact-owner or routing prescription "
        "embedded in finding prose as an untrusted reviewer opinion; decide from "
        "whether the source theory can remain exactly true and sufficient. Target "
        "source_theory_packet whenever a theory claim, "
        "equation, definition, calibration, assumption, procedure, estimand, or "
        "feasibility argument must be changed or supplemented. Target only "
        "metric_protocol_candidate when the source theory can remain exactly true "
        "and sufficient and only its empirical measurement or typed evaluator "
        "representation must change. Target both when both artifacts must change. "
        + phase_instruction
        + "semantic_review_artifact_assessments are non-authoritative diagnostic "
        "hypotheses. If you select a more upstream owner than those assessments, "
        "your rationale must cite the conflicting exact artifact field and the "
        "downstream-repair counterfactual; do not escalate merely because theory "
        "could be supplemented with implementation advice. "
        + "The runtime derives resolved ownership and whether source theory can remain "
        "unchanged from every nonempty eligible target list. Use "
        "ownership_certainty=resolved_no_change only with no targets when no artifact "
        "must change, or ownership_certainty=unresolved with no targets when the "
        "supplied artifacts do not let you decide; do not guess. "
        "required_artifact_changes contains artifact roles only: do not author a "
        "repair. Do not derive replacement formulas, "
        "thresholds, task-family rules, code, results, or proof. Return exactly one decision "
        "for every index in required_finding_indices, use no other index, and do "
        "not omit or duplicate an index.\n\n"
        + json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
    )


ARCHITECT_METRIC_REPAIR_OWNERSHIP_SYSTEM_PROMPT = """\
You are the independent ArchitectMetricRepairOwnershipRouter inside an AI
Statistician AgentRuntime. You do not redo the semantic review or repair its
mathematics. You identify which immutable artifact must change, preserve frozen
post-result protocols, and fail closed when ownership is unresolved. You never
authorize execution or claim empirical, statistical, or proof evidence.
"""


ARCHITECT_METRIC_REPAIR_OWNERSHIP_OUTPUT_CONTRACT: dict[str, Any] = {
    "decisions": [
        {
            "finding_index": 0,
            "required_artifact_changes": [
                {
                    "artifact_role": (
                        "source_theory_packet|metric_protocol_candidate|"
                        "upstream_generated_dependency|generated_source_artifact"
                    )
                }
            ],
            "ownership_certainty": (
                "resolved|resolved_no_change(post-execution only)|unresolved"
            ),
            "rationale": "artifact-bound ownership reasoning",
        }
    ]
}


_ARTIFACT_CHANGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["artifact_role"],
    "properties": {
        "artifact_role": {
            "type": "string",
            "enum": list(ARCHITECT_METRIC_REPAIR_TARGETS),
        },
    },
}


_OWNERSHIP_DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "finding_index",
        "required_artifact_changes",
        "ownership_certainty",
        "rationale",
    ],
    "properties": {
        "finding_index": {"type": "integer", "minimum": 0},
        "required_artifact_changes": {
            "type": "array",
            "maxItems": len(ARCHITECT_METRIC_REPAIR_TARGETS),
            "items": _ARTIFACT_CHANGE_SCHEMA,
        },
        "ownership_certainty": {
            "type": "string",
            "enum": list(ARCHITECT_METRIC_REPAIR_OWNERSHIP_CERTAINTIES),
        },
        "rationale": {"type": "string", "minLength": 1},
    },
}


ARCHITECT_METRIC_REPAIR_OWNERSHIP_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["decisions"],
    "properties": {
        "decisions": {"type": "array", "items": _OWNERSHIP_DECISION_SCHEMA}
    },
}


def architect_metric_repair_ownership_json_schema(
    routing_phase: str,
) -> dict[str, Any]:
    schema = deepcopy(ARCHITECT_METRIC_REPAIR_OWNERSHIP_JSON_SCHEMA)
    decision_schema = schema["properties"]["decisions"]["items"]
    changes_schema = decision_schema["properties"]["required_artifact_changes"]
    targets = _ownership_targets_for_phase(routing_phase)
    changes_schema["maxItems"] = len(targets)
    changes_schema["items"]["properties"]["artifact_role"]["enum"] = list(
        targets
    )
    decision_schema["properties"]["ownership_certainty"]["enum"] = [
        "resolved",
        *(
            ["resolved_no_change"]
            if routing_phase
            == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
            else []
        ),
        "unresolved",
    ]
    return schema


def architect_metric_repair_scope_from_decision(
    decision: Mapping[str, Any],
) -> str:
    return _repair_scope_from_ownership_decision(
        decision,
        routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
    )


def generated_code_repair_scope_from_ownership_decision(
    decision: Mapping[str, Any],
) -> str:
    return _repair_scope_from_ownership_decision(
        decision,
        routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
    )


def _repair_scope_from_ownership_decision(
    decision: Mapping[str, Any],
    *,
    routing_phase: str,
) -> str:
    certainty = str(decision.get("ownership_certainty", "") or "").strip()
    changes = decision.get("required_artifact_changes", [])
    roles = {
        str(row.get("artifact_role", "") or "").strip()
        for row in changes
        if isinstance(row, Mapping)
    } if isinstance(changes, list) else set()
    theory_unchanged = decision.get("source_theory_can_remain_unchanged")
    if certainty == "resolved_no_change":
        return (
            "none"
            if not roles and theory_unchanged is True
            else ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
        )
    if certainty != "resolved":
        return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    if (
        routing_phase
        == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
        and ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY
        in roles
        and ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL not in roles
    ):
        # Repair an immutable upstream implementation before asking its consumer
        # or mathematical theory to compensate for the dependency defect.
        return ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY
    if (
        routing_phase
        == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
        and roles
        == {
            ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY,
            ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE,
        }
        and theory_unchanged is False
    ):
        # A post-result symptom can support both a concrete implementation defect
        # and an upstream hypothesis. Repair the concrete artifact once, then let
        # an independent fresh review decide whether theory still has to change.
        return "source_code"
    if (
        ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY in roles
        and theory_unchanged is False
    ):
        return ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY
    if theory_unchanged is not True:
        return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    if routing_phase == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION:
        if ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL in roles:
            return "upstream_metric_contract"
        if roles == {ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE}:
            return "source_code"
        return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    if roles == {ARCHITECT_METRIC_REPAIR_TARGET_METRIC_PROTOCOL}:
        return ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT
    return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED


def architect_metric_recommended_scope_from_ownership_decisions(
    decisions: Any,
) -> str:
    return _recommended_scope_from_ownership_decisions(
        decisions,
        routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
    )


def generated_code_recommended_scope_from_ownership_decisions(
    decisions: Any,
) -> str:
    return _recommended_scope_from_ownership_decisions(
        decisions,
        routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
    )


def _recommended_scope_from_ownership_decisions(
    decisions: Any,
    *,
    routing_phase: str,
) -> str:
    if not isinstance(decisions, list) or not decisions:
        return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    scopes = {
        _repair_scope_from_ownership_decision(
            row,
            routing_phase=routing_phase,
        )
        for row in decisions
        if isinstance(row, Mapping)
    }
    if ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED in scopes:
        return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    if routing_phase == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION:
        if "upstream_metric_contract" in scopes:
            return "upstream_metric_contract"
        if ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY in scopes:
            return ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY
        if "source_code" in scopes:
            return "source_code"
        if ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY in scopes:
            return ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY
        return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    if ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY in scopes:
        return ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_UPSTREAM_THEORY
    if scopes == {ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT}:
        return ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT
    return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED


def apply_architect_metric_repair_ownership_routes(
    *,
    findings: Any,
    ownership_packet: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return _apply_repair_ownership_routes(
        findings=findings,
        ownership_packet=ownership_packet,
        routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION,
        replace_repair_instruction=False,
    )


def apply_generated_code_repair_ownership_routes(
    *,
    findings: Any,
    ownership_packet: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return _apply_repair_ownership_routes(
        findings=findings,
        ownership_packet=ownership_packet,
        routing_phase=ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION,
        replace_repair_instruction=True,
    )


def _apply_repair_ownership_routes(
    *,
    findings: Any,
    ownership_packet: Mapping[str, Any],
    routing_phase: str,
    replace_repair_instruction: bool,
) -> list[dict[str, Any]]:
    source_findings = [
        dict(row) for row in findings if isinstance(row, Mapping)
    ] if isinstance(findings, list) else []
    decision_rows = {
        int(row.get("finding_index", -1)): dict(row)
        for row in ownership_packet.get("decisions", []) or []
        if isinstance(row, Mapping)
    }
    actionable_source_indices = (
        [
            index
            for index, row in enumerate(source_findings)
            if str(row.get("repair_scope", "") or "")
            in {"source_code", "upstream_metric_contract", "upstream_theory"}
        ]
        if routing_phase
        == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
        else list(range(len(source_findings)))
    )
    decisions = {
        source_index: decision_rows.get(compact_index, {})
        for compact_index, source_index in enumerate(actionable_source_indices)
    }
    routed: list[dict[str, Any]] = []
    for index, finding in enumerate(source_findings):
        if index not in decisions:
            routed.append(finding)
            continue
        decision = decisions.get(index, {})
        original_scope = str(finding.get("repair_scope", "") or "")
        finding["semantic_reviewer_repair_scope"] = original_scope
        finding["repair_scope"] = _repair_scope_from_ownership_decision(
            decision,
            routing_phase=routing_phase,
        )
        target_artifacts = [
            dict(row)
            for row in decision.get("required_artifact_changes", []) or []
            if isinstance(row, Mapping)
        ]
        finding["repair_target_artifacts"] = target_artifacts
        if replace_repair_instruction:
            finding["semantic_reviewer_required_change"] = str(
                finding.get("required_change", "") or ""
            )
            target_roles = [
                str(row.get("artifact_role", "") or "").strip()
                for row in target_artifacts
                if str(row.get("artifact_role", "") or "").strip()
            ]
            immediate_target_roles = list(target_roles)
            if finding["repair_scope"] in {
                "source_code",
                ARCHITECT_GENERATED_CODE_REPAIR_SCOPE_UPSTREAM_DEPENDENCY,
            }:
                expected_immediate_role = (
                    ARCHITECT_METRIC_REPAIR_TARGET_GENERATED_SOURCE
                    if finding["repair_scope"] == "source_code"
                    else (
                        ARCHITECT_METRIC_REPAIR_TARGET_UPSTREAM_GENERATED_DEPENDENCY
                    )
                )
                immediate_target_roles = [
                    role
                    for role in target_roles
                    if role == expected_immediate_role
                ]
            finding["deferred_repair_target_artifacts"] = [
                dict(row)
                for row in target_artifacts
                if str(row.get("artifact_role", "") or "").strip()
                not in set(immediate_target_roles)
            ]
            finding_summary = str(finding.get("summary", "") or "").strip()
            finding["required_change"] = (
                "Reinspect "
                + ", ".join(immediate_target_roles)
                + " against the semantic finding and its cited evidence; author a "
                "fresh artifact and repeat independent review. Finding: "
                + finding_summary
                if immediate_target_roles
                else (
                    "No artifact change is authorized for this advisory finding; "
                    "preserve it for the next independent review."
                    if finding["repair_scope"] == "none"
                    else "Artifact repair ownership is unresolved; stop this lineage."
                )
            )
        finding["repair_ownership_certainty"] = str(
            decision.get("ownership_certainty", "") or ""
        )
        finding["repair_ownership_rationale"] = str(
            decision.get("rationale", "") or ""
        )
        finding["repair_ownership_packet_id"] = str(
            ownership_packet.get("packet_id", "") or ""
        )
        routed.append(finding)
    return routed


def validate_architect_metric_repair_ownership_packet(
    packet: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    routing_phase = str(packet.get("routing_phase", "") or "").strip()
    if routing_phase not in ARCHITECT_METRIC_REPAIR_ROUTING_PHASES:
        errors.append("repair ownership router has invalid routing phase")
        routing_phase = ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_PREEXECUTION
    if packet.get("proof_evidence_status") != (
        ARCHITECT_METRIC_REPAIR_OWNERSHIP_NOT_PROOF_EVIDENCE
    ):
        errors.append("repair ownership router must preserve the non-proof boundary")
    expected_execution_observed = bool(
        routing_phase
        == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
    )
    if packet.get("execution_results_observed") is not expected_execution_observed:
        errors.append("repair ownership execution-result phase is inconsistent")
    if (
        expected_execution_observed
        and packet.get("frozen_protocol_immutable_after_execution") is not True
    ):
        errors.append("post-execution ownership routing must freeze the protocol")
    common_lineage_fields = (
        "question_id",
        "semantic_review_packet_id",
        "semantic_review_packet_hash",
        "source_theory_packet_id",
        "source_theory_packet_hash",
        "routing_input_fingerprint",
    )
    phase_lineage_fields = (
        ("work_order_id", "work_order_hash", "source_manifest_id", "source_manifest_hash")
        if expected_execution_observed
        else ("authoring_packet_id", "authoring_packet_hash")
    )
    for field in (*common_lineage_fields, *phase_lineage_fields):
        if not str(packet.get(field, "") or "").strip():
            errors.append(f"repair ownership router missing trusted lineage: {field}")
    findings_count = int(packet.get("reviewed_finding_count", 0) or 0)
    decisions = packet.get("decisions", [])
    if not isinstance(decisions, list):
        errors.append("repair ownership decisions must be an array")
        decisions = []
    indices: list[int] = []
    allowed_targets = set(_ownership_targets_for_phase(routing_phase))
    target_eligibility: dict[int, set[str]] = {}
    if expected_execution_observed:
        eligibility_rows = packet.get("artifact_target_eligibility", [])
        if not isinstance(eligibility_rows, list):
            errors.append("post-execution artifact target eligibility must be an array")
            eligibility_rows = []
        for row in eligibility_rows:
            if not isinstance(row, Mapping):
                continue
            try:
                eligibility_index = int(row.get("finding_index", -1))
            except (TypeError, ValueError):
                eligibility_index = -1
            roles = row.get("eligible_artifact_roles", [])
            target_eligibility[eligibility_index] = {
                str(role or "") for role in roles
            } if isinstance(roles, list) else set()
        if sorted(target_eligibility) != list(range(findings_count)):
            errors.append(
                "post-execution artifact target eligibility must cover every finding"
            )
    for decision in decisions:
        if not isinstance(decision, Mapping):
            errors.append("repair ownership decision must be an object")
            continue
        try:
            finding_index = int(decision.get("finding_index", -1))
        except (TypeError, ValueError):
            finding_index = -1
        indices.append(finding_index)
        changes = decision.get("required_artifact_changes", [])
        certainty = str(decision.get("ownership_certainty", "") or "")
        if not isinstance(changes, list) or (
            certainty == "resolved" and not changes
        ):
            errors.append(f"repair ownership decision {finding_index} has no targets")
        else:
            roles: list[str] = []
            for change in changes:
                if not isinstance(change, Mapping):
                    errors.append(
                        f"repair ownership decision {finding_index} target is invalid"
                    )
                    continue
                role = str(change.get("artifact_role", "") or "")
                roles.append(role)
                if role not in allowed_targets:
                    errors.append(
                        f"repair ownership decision {finding_index} has unknown target"
                    )
                if (
                    expected_execution_observed
                    and role not in target_eligibility.get(finding_index, set())
                ):
                    errors.append(
                        f"repair ownership decision {finding_index} targets an "
                        "artifact not supported by its typed artifact citations"
                    )
            if len(roles) != len(set(roles)):
                errors.append(
                    f"repair ownership decision {finding_index} repeats a target"
                )
        allowed_certainties = {
            "resolved",
            "unresolved",
            *(
                {"resolved_no_change"}
                if expected_execution_observed
                else set()
            ),
        }
        if certainty not in allowed_certainties:
            errors.append(
                f"repair ownership decision {finding_index} has invalid certainty"
            )
        if not isinstance(
            decision.get("source_theory_can_remain_unchanged"),
            bool,
        ):
            errors.append(
                f"repair ownership decision {finding_index} has invalid repair flag"
            )
        roles = {
            str(row.get("artifact_role", "") or "")
            for row in changes
            if isinstance(row, Mapping)
        } if isinstance(changes, list) else set()
        theory_can_remain = decision.get("source_theory_can_remain_unchanged")
        if certainty == "resolved" and theory_can_remain is not (
            ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY not in roles
        ):
            errors.append(
                f"repair ownership decision {finding_index} has inconsistent "
                "source-theory preservation flag"
            )
        if certainty == "resolved_no_change" and (
            roles or theory_can_remain is not True
        ):
            errors.append(
                f"repair ownership decision {finding_index} has inconsistent "
                "no-change disposition"
            )
        expected_scope = _repair_scope_from_ownership_decision(
            decision,
            routing_phase=routing_phase,
        )
        if (
            certainty == "resolved"
            and expected_scope == ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
        ):
            errors.append(
                f"repair ownership decision {finding_index} claims resolved "
                "ownership but its targets and repair flag contradict"
            )
        if decision.get("derived_repair_scope") != expected_scope:
            errors.append(
                f"repair ownership decision {finding_index} has inconsistent scope"
            )
        if not str(decision.get("rationale", "") or "").strip():
            errors.append(
                f"repair ownership decision {finding_index} missing rationale"
            )
    if sorted(indices) != list(range(findings_count)):
        errors.append("repair ownership decisions must cover every finding exactly once")
    expected_recommended = (
        _recommended_scope_from_ownership_decisions(
            decisions,
            routing_phase=routing_phase,
        )
    )
    if packet.get("recommended_repair_scope") != expected_recommended:
        errors.append("repair ownership packet has inconsistent recommended scope")
    return sorted(set(errors))


def _normalize_architect_metric_repair_ownership_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    routing_phase: str,
    routing_material: Mapping[str, Any],
    semantic_review_packet: Mapping[str, Any],
    trusted_lineage: Mapping[str, Any],
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    raw_decisions = payload.get("decisions", [])
    decisions: list[dict[str, Any]] = []
    for row in raw_decisions if isinstance(raw_decisions, list) else []:
        if not isinstance(row, Mapping):
            continue
        changes = deepcopy(row.get("required_artifact_changes", []))
        requested_certainty = str(
            row.get("ownership_certainty", "") or ""
        ).strip()
        if requested_certainty == "unresolved":
            changes = []
        roles = {
            str(change.get("artifact_role", "") or "").strip()
            for change in changes
            if isinstance(change, Mapping)
        } if isinstance(changes, list) else set()
        # Eligible target rows authorize repair only; they can never accept
        # evidence or turn an explicitly unresolved diagnosis into a repair.
        if requested_certainty == "unresolved":
            certainty = "unresolved"
        elif isinstance(changes, list) and changes:
            certainty = "resolved"
        elif (
            routing_phase
            == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
            and requested_certainty == "resolved_no_change"
        ):
            certainty = "resolved_no_change"
        else:
            certainty = "unresolved"
        decision = {
            "finding_index": deepcopy(row.get("finding_index")),
            "required_artifact_changes": changes,
            "source_theory_can_remain_unchanged": (
                ARCHITECT_METRIC_REPAIR_TARGET_SOURCE_THEORY not in roles
                if certainty == "resolved"
                else certainty == "resolved_no_change"
            ),
            "ownership_certainty": certainty,
            "rationale": deepcopy(row.get("rationale", "")),
        }
        if requested_certainty != certainty:
            decision["model_requested_ownership_certainty"] = (
                requested_certainty
            )
        decision["derived_repair_scope"] = (
            _repair_scope_from_ownership_decision(
                decision,
                routing_phase=routing_phase,
            )
        )
        decisions.append(decision)
    body = {
        "schema_version": ARCHITECT_METRIC_REPAIR_OWNERSHIP_SCHEMA_VERSION,
        "artifact_kind": "ArchitectMetricRepairOwnershipPacket",
        "routing_phase": routing_phase,
        "question_id": question.id,
        "authoring_packet_id": str(
            trusted_lineage.get("authoring_packet_id", "") or ""
        ),
        "authoring_packet_hash": str(
            trusted_lineage.get("authoring_packet_hash", "") or ""
        ),
        "semantic_review_packet_id": str(
            semantic_review_packet.get("packet_id", "") or ""
        ),
        "semantic_review_packet_hash": stable_hash(dict(semantic_review_packet)),
        "source_theory_packet_id": str(
            trusted_lineage.get("source_theory_packet_id", "")
            or trusted_lineage.get("theory_packet_id", "")
            or ""
        ),
        "source_theory_packet_hash": str(
            trusted_lineage.get("source_theory_packet_hash", "")
            or trusted_lineage.get("theory_packet_hash", "")
            or ""
        ),
        "work_order_id": str(trusted_lineage.get("work_order_id", "") or ""),
        "work_order_hash": str(
            trusted_lineage.get("work_order_hash", "") or ""
        ),
        "source_manifest_id": str(
            trusted_lineage.get("source_manifest_id", "") or ""
        ),
        "source_manifest_hash": str(
            trusted_lineage.get("source_manifest_hash", "") or ""
        ),
        "reviewed_finding_count": len(
            routing_material.get("semantic_review_findings", []) or []
        ),
        "artifact_target_eligibility": deepcopy(
            routing_material.get("artifact_target_eligibility", [])
        ),
        "decisions": decisions,
        "recommended_repair_scope": (
            _recommended_scope_from_ownership_decisions(
                decisions,
                routing_phase=routing_phase,
            )
        ),
        "routing_input_fingerprint": stable_hash(routing_material),
        "source_agent": "LLMArchitectMetricRepairOwnershipRouterAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "execution_results_observed": bool(
            routing_phase
            == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
        ),
        "frozen_protocol_immutable_after_execution": bool(
            routing_phase
            == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
        ),
        "proof_evidence_status": (
            ARCHITECT_METRIC_REPAIR_OWNERSHIP_NOT_PROOF_EVIDENCE
        ),
        "boundary": ARCHITECT_METRIC_REPAIR_OWNERSHIP_BOUNDARY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "raw_response_fingerprint": stable_hash(raw_response),
    }
    body["packet_id"] = "metric_repair_ownership:" + stable_hash(body)[:20]
    return body


def _unresolved_architect_metric_repair_ownership_packet(
    *,
    question: OpenResearchQuestion,
    routing_phase: str,
    routing_material: Mapping[str, Any],
    semantic_review_packet: Mapping[str, Any],
    trusted_lineage: Mapping[str, Any],
    model: str,
    model_tier: str,
    provider_name: str,
    validation_failure: PacketValidationError,
) -> dict[str, Any]:
    findings = [
        row
        for row in routing_material.get("semantic_review_findings", []) or []
        if isinstance(row, Mapping)
    ]
    decisions = [
        {
            "finding_index": finding_index,
            "required_artifact_changes": [],
            "source_theory_can_remain_unchanged": False,
            "ownership_certainty": "unresolved",
            "rationale": (
                "The ownership router exhausted bounded structured-output repair; "
                "artifact ownership remains unresolved and must be replanned before "
                "execution."
            ),
            "derived_repair_scope": ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED,
        }
        for finding_index, _finding in enumerate(findings)
    ]
    body = {
        "schema_version": ARCHITECT_METRIC_REPAIR_OWNERSHIP_SCHEMA_VERSION,
        "artifact_kind": "ArchitectMetricRepairOwnershipPacket",
        "routing_phase": routing_phase,
        "question_id": question.id,
        "authoring_packet_id": str(
            trusted_lineage.get("authoring_packet_id", "") or ""
        ),
        "authoring_packet_hash": str(
            trusted_lineage.get("authoring_packet_hash", "") or ""
        ),
        "semantic_review_packet_id": str(
            semantic_review_packet.get("packet_id", "") or ""
        ),
        "semantic_review_packet_hash": stable_hash(dict(semantic_review_packet)),
        "source_theory_packet_id": str(
            trusted_lineage.get("source_theory_packet_id", "")
            or trusted_lineage.get("theory_packet_id", "")
            or ""
        ),
        "source_theory_packet_hash": str(
            trusted_lineage.get("source_theory_packet_hash", "")
            or trusted_lineage.get("theory_packet_hash", "")
            or ""
        ),
        "work_order_id": str(trusted_lineage.get("work_order_id", "") or ""),
        "work_order_hash": str(
            trusted_lineage.get("work_order_hash", "") or ""
        ),
        "source_manifest_id": str(
            trusted_lineage.get("source_manifest_id", "") or ""
        ),
        "source_manifest_hash": str(
            trusted_lineage.get("source_manifest_hash", "") or ""
        ),
        "reviewed_finding_count": len(findings),
        "artifact_target_eligibility": deepcopy(
            routing_material.get("artifact_target_eligibility", [])
        ),
        "decisions": decisions,
        "recommended_repair_scope": ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED,
        "routing_input_fingerprint": stable_hash(routing_material),
        "source_agent": "LLMArchitectMetricRepairOwnershipRouterAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "execution_results_observed": bool(
            routing_phase
            == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
        ),
        "frozen_protocol_immutable_after_execution": bool(
            routing_phase
            == ARCHITECT_METRIC_REPAIR_ROUTING_PHASE_POSTEXECUTION
        ),
        "proof_evidence_status": (
            ARCHITECT_METRIC_REPAIR_OWNERSHIP_NOT_PROOF_EVIDENCE
        ),
        "boundary": ARCHITECT_METRIC_REPAIR_OWNERSHIP_BOUNDARY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "validation_errors": list(validation_failure.errors),
        "llm_json_repair_attempts": max(0, validation_failure.attempts - 1),
        "llm_json_repair_history": list(validation_failure.history),
        "fallback_reason": "bounded_router_packet_validation_exhausted",
    }
    body["packet_id"] = "metric_repair_ownership:" + stable_hash(body)[:20]
    return body
