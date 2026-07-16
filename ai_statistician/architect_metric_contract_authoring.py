from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from .architect_metric_repair_ownership_router_llm import (
    ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED,
    LLMArchitectMetricRepairOwnershipRouterAgent,
    apply_architect_metric_repair_ownership_routes,
)
from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY,
    ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT,
    LLMArchitectMetricSemanticReviewerAgent,
    architect_metric_semantic_recommended_repair_scope,
)
from .fingerprint import stable_hash
from .generated_metric_contract import (
    GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS,
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_json_schema,
    generated_metric_requirement_prompt_schema,
    generated_metric_requirement_set_id,
    generated_metric_requirement_target_namespace_contract,
    validate_generated_metric_requirements,
)
from .llm_json_repair import (
    PacketValidationError,
    extract_json_object,
    generate_validated_json_packet,
)
from .model_backend import GeneratorBackend, GeneratorRequest
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
)
from .metric_protocol_finding_ledger import (
    active_metric_protocol_finding_ledger,
    metric_protocol_finding_ledger_fingerprint,
    metric_protocol_finding_ledger_from_review_history,
    update_metric_protocol_finding_ledger,
)
from .research_schema import OpenResearchQuestion


ARCHITECT_METRIC_REQUIREMENT_AUTHORING_SCHEMA_VERSION = 2


class ArchitectMetricSemanticReviewRejected(PacketValidationError):
    """Bounded pre-execution metric authoring exhausted without acceptance."""

    def __init__(
        self,
        *,
        question_id: str,
        semantic_review_history: list[dict[str, Any]],
        source_theory_packet_id: str = "",
        source_theory_packet_hash: str = "",
    ) -> None:
        history = [dict(row) for row in semantic_review_history]
        last_review = history[-1] if history else {}
        self.question_id = str(question_id)
        self.semantic_review_history = history
        self.source_theory_packet_id = str(source_theory_packet_id or "")
        self.source_theory_packet_hash = str(source_theory_packet_hash or "")
        self.recommended_repair_scope = str(
            last_review.get("recommended_repair_scope", "")
            or ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT
        )
        super().__init__(
            validation_label="Architect pre-execution metric semantic review",
            attempts=len(history),
            errors=[
                "independent semantic reviewer did not accept any metric contract "
                f"candidate after {len(history)} attempt(s)",
                *[
                    str(value)
                    for value in last_review.get("repair_instructions", [])
                    if str(value).strip()
                ],
            ],
            history=history,
        )


def _metric_protocol_combined_repair_scope(
    *,
    verdict: str,
    findings: list[dict[str, Any]],
) -> str:
    if str(verdict or "").strip().upper() == "ACCEPT":
        return "none"
    scopes = {
        str(row.get("repair_scope", "") or "").strip()
        for row in findings
        if isinstance(row, Mapping)
    }
    if ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED in scopes:
        return ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED
    return architect_metric_semantic_recommended_repair_scope(
        verdict=verdict,
        findings=findings,
    )


@dataclass(frozen=True)
class ArchitectMetricContractAuthoringConfig:
    max_tokens: int = 5000
    model_tier: str = "sonnet"
    provider_name: str = "anthropic"
    max_repair_attempts: int = 2
    metric_semantic_reviewer_max_revisions: int = 2


def author_reviewed_architect_metric_requirements(
    *,
    provider: GeneratorBackend,
    config: ArchitectMetricContractAuthoringConfig,
    request_model: str,
    semantic_reviewer: LLMArchitectMetricSemanticReviewerAgent | None,
    repair_ownership_router: (
        LLMArchitectMetricRepairOwnershipRouterAgent | None
    ),
    question: OpenResearchQuestion,
    runtime_contract: Mapping[str, Any],
    theory_protocol_material: Mapping[str, Any] | None = None,
    prior_rejection_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if (
        runtime_contract.get("capability_eval_requires_typed_metric_contracts")
        is not True
        or runtime_contract.get("empirical_metric_requirements")
        or str(getattr(provider, "provider_name", config.provider_name)).lower()
        != "anthropic"
    ):
        return {}
    if (
        runtime_contract.get("empirical_metric_protocol_phase")
        != METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED
    ):
        return {}
    if semantic_reviewer is None:
        raise ValueError(
            "capability-eval metric authoring requires an independent "
            "ArchitectMetricSemanticReviewer"
        )

    theory_material = (
        dict(theory_protocol_material)
        if isinstance(theory_protocol_material, Mapping)
        else {}
    )
    if (
        theory_material.get("artifact_kind")
        != "RuntimeTheoryInformedMetricProtocolMaterial"
        or theory_material.get("execution_results_available") is not False
        or not str(
            theory_material.get("source_theory_packet_id", "") or ""
        ).strip()
        or not isinstance(
            theory_material.get("theory_semantic_material"), Mapping
        )
        or not theory_material.get("theory_semantic_material")
    ):
        raise ValueError(
            "theory-informed metric authoring requires a structured, pre-execution "
            "TheoryDeveloper semantic handoff"
        )

    runtime_replicates = int(
        runtime_contract.get("generated_sandbox_runtime_replicates", 0) or 0
    )
    response_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["empirical_metric_requirements"],
        "properties": {
            "empirical_metric_requirements": {
                "type": "array",
                "minItems": 1,
                "items": generated_metric_requirement_json_schema(),
            }
        },
    }
    prompt_payload = {
        "task": (
            "Author the pre-execution empirical acceptance requirements used by "
            "the AI Statistician coding and simulation agents."
        ),
        "question": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
        "theory_developer_protocol_material": theory_material,
        "runtime_owned_replicates": runtime_replicates,
        "target_namespace": generated_metric_requirement_target_namespace_contract(),
        "metric_evaluation_semantics": (
            generated_metric_evaluation_semantics_contract()
        ),
        "requirement_schema": generated_metric_requirement_prompt_schema(),
        "required_target_rows": [
            generated_metric_requirement_prompt_schema(target_subsystem=target)
            for target in GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
        ],
        "hard_requirements": [
            (
                "Return at least one required empirical metric row for each "
                "generated-code author subsystem; a row may correctly target both."
            ),
            (
                "Each row must represent exactly one independently compared scalar "
                "quantity, or one homogeneous collection whose members share this "
                "row's one operator, bounds, tolerance, aggregation, and quorum."
            ),
            (
                "When acceptance requires multiple quantities or different "
                "operators, thresholds, bounds, aggregations, or quorums, split them "
                "into separate requirement rows; never bundle independent gates in "
                "prose inside one row."
            ),
            "Use only operator and aggregation enum values from requirement_schema.",
            (
                "For identity/mean/min/max, operator and threshold compare the one "
                "aggregate. For all/any/at_least_count/at_least_fraction, operator "
                "and threshold compare every raw returned value before the boolean "
                "results are aggregated."
            ),
            (
                "Keep the comparison boundary and quorum separate: threshold or "
                "bounds describe when one measurement passes; minimum_pass_count or "
                "minimum_pass_fraction describes how many comparisons must pass."
            ),
            (
                "Before emitting any numeric constant, recompute it from the stated "
                "definitions and assumptions instead of relying on a memorized "
                "approximation; place a concise derivation or exact source anchor in "
                "source_anchors."
            ),
            (
                "Bind every procedure, estimand, data-generating regime, pivot, and "
                "calibration assumption to theory_developer_protocol_material. Do "
                "not invent an unspecified estimator, test, stopping strategy, or "
                "reference distribution merely to make a gate executable."
            ),
            (
                "Audit mathematical feasibility before freezing each row: the "
                "comparison must be attainable for the named procedure, data-generating "
                "regime, runtime budget, and estimand, and it must not contradict an "
                "analytic bound or expectation stated by the same packet."
            ),
            (
                "Translate the measurement_protocol into the evaluator's exact "
                "operator-then-aggregation semantics and verify that its pass set is "
                "equivalent to the prose, especially for upper versus lower limits "
                "and at-most versus at-least counts."
            ),
            (
                "Require raw measurements whenever they exist. Use bool/0/1 with "
                "operator == and threshold 1 only for an intrinsically boolean "
                "predicate."
            ),
            "Copy runtime_owned_replicates into every required_runtime_replicates field and state that exact count in each measurement_protocol.",
            "Use null for comparison or quorum fields that do not apply to the selected operator or aggregation.",
            "Define measurable returned quantities, not prose-only success claims or task-specific runtime code.",
            "These rows are empirical controls and never theorem proof evidence.",
        ],
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }
    semantic_review_history: list[dict[str, Any]] = []
    prior_authoring_packet: dict[str, Any] = {}
    prior_review_packet: dict[str, Any] = {}
    carry_forward = (
        dict(prior_rejection_context)
        if isinstance(prior_rejection_context, Mapping)
        else {}
    )
    carried_review = carry_forward.get("final_review", {})
    carry_forward_valid = bool(
        carry_forward.get("artifact_kind")
        == "RuntimeArchitectMetricProtocolPriorRejectionContext"
        and carry_forward.get("execution_results_available") is False
        and carry_forward.get("current_candidate_acceptance_eligible") is False
        and str(
            carry_forward.get("current_source_theory_packet_id", "") or ""
        )
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(
            carry_forward.get("current_source_theory_packet_hash", "") or ""
        )
        == str(theory_material.get("source_theory_packet_hash", "") or "")
        and isinstance(carried_review, Mapping)
        and carried_review.get("empirical_metric_requirements")
    )
    cumulative_finding_ledger: list[dict[str, Any]] = []
    if carry_forward_valid:
        carried_history = carry_forward.get("semantic_review_history", [])
        if not isinstance(carried_history, list) or not carried_history:
            carried_history = [dict(carried_review)]
        cumulative_finding_ledger = (
            metric_protocol_finding_ledger_from_review_history(
                question_id=question.id,
                semantic_review_history=carried_history,
            )
        )
        prior_authoring_packet = {
            "packet_id": str(
                carried_review.get("authoring_packet_id", "") or ""
            ),
            "empirical_metric_requirement_set_id": str(
                carried_review.get(
                    "empirical_metric_requirement_set_id", ""
                )
                or ""
            ),
            "empirical_metric_requirements": [
                dict(row)
                for row in carried_review.get(
                    "empirical_metric_requirements", []
                )
                if isinstance(row, Mapping)
            ],
        }
        prior_review_packet = {
            "packet_id": str(
                carried_review.get("semantic_review_packet_id", "") or ""
            ),
            "dimension_reviews": [
                dict(row)
                for row in carried_review.get("dimension_reviews", []) or []
                if isinstance(row, Mapping)
            ],
            "findings": [
                dict(row)
                for row in carried_review.get("findings", []) or []
                if isinstance(row, Mapping)
            ],
            "repair_instructions": [
                str(value)
                for value in carried_review.get("repair_instructions", []) or []
                if str(value).strip()
            ],
            "recommended_repair_scope": str(
                carried_review.get("recommended_repair_scope", "") or ""
            ),
        }
    max_semantic_revisions = max(
        0, int(config.metric_semantic_reviewer_max_revisions or 0)
    )
    for revision_index in range(max_semantic_revisions + 1):
        active_finding_ledger = active_metric_protocol_finding_ledger(
            cumulative_finding_ledger
        )
        active_finding_ids = [
            str(row.get("finding_id", "") or "")
            for row in active_finding_ledger
            if str(row.get("finding_id", "") or "").strip()
        ]
        active_finding_ledger_fingerprint = (
            metric_protocol_finding_ledger_fingerprint(active_finding_ledger)
            if active_finding_ledger
            else ""
        )
        candidate_prompt_payload = dict(prompt_payload)
        if prior_review_packet:
            candidate_prompt_payload["independent_semantic_review_repair"] = {
                "revision_index": revision_index,
                "rejected_authoring_packet_id": str(
                    prior_authoring_packet.get("packet_id", "") or ""
                ),
                "rejected_requirement_set_id": str(
                    prior_authoring_packet.get(
                        "empirical_metric_requirement_set_id", ""
                    )
                    or ""
                ),
                "rejected_empirical_metric_requirements": [
                    dict(row)
                    for row in prior_authoring_packet.get(
                        "empirical_metric_requirements", []
                    )
                    if isinstance(row, Mapping)
                ],
                "semantic_review_packet_id": str(
                    prior_review_packet.get("packet_id", "") or ""
                ),
                "dimension_reviews": list(
                    prior_review_packet.get("dimension_reviews", []) or []
                ),
                "findings": list(prior_review_packet.get("findings", []) or []),
                "repair_instructions": list(
                    prior_review_packet.get("repair_instructions", []) or []
                ),
                "active_prior_finding_ledger": active_finding_ledger,
                "required_prior_finding_ids": active_finding_ids,
                "active_prior_finding_ledger_fingerprint": (
                    active_finding_ledger_fingerprint
                ),
                "cross_theory_revision_context": (
                    {
                        "source_rejection_manifest_id": carry_forward.get(
                            "source_rejection_manifest_id", ""
                        ),
                        "source_rejection_manifest_hash": carry_forward.get(
                            "source_rejection_manifest_hash", ""
                        ),
                        "prior_source_theory_packet_id": carried_review.get(
                            "source_theory_packet_id", ""
                        ),
                        "prior_source_theory_packet_hash": carried_review.get(
                            "source_theory_packet_hash", ""
                        ),
                        "current_source_theory_packet_id": str(
                            theory_material.get("source_theory_packet_id", "")
                            or ""
                        ),
                        "current_source_theory_packet_hash": str(
                            theory_material.get("source_theory_packet_hash", "")
                            or ""
                        ),
                        "boundary": str(
                            carry_forward.get("boundary", "") or ""
                        ),
                    }
                    if carry_forward
                    else {}
                ),
                "revision_policy": (
                    "Return the complete contract required by the schema, but repair "
                    "the rejected contract in place. Preserve stable requirement_id "
                    "values and all rows and fields not implicated by a finding unless "
                    "the current revised theory requires a change. Edit, add, or remove "
                    "only what is needed to resolve every finding; do not replace the "
                    "metric portfolio with unrelated gates, drop a required author "
                    "subsystem, or claim that execution passed. The current theory "
                    "material is authoritative over stale assumptions in the rejected "
                    "contract. Resolve every active_prior_finding_ledger row in this "
                    "one complete revision and then rerun a whole-contract numeric, "
                    "estimand, DGP, evaluator-order, and cross-row consistency audit. "
                    "Do not treat a finding as resolved merely because it is absent "
                    "from the latest review prose."
                ),
            }
        request = GeneratorRequest(
            system_prompt=(
                "You are the ArchitectMetricContractPlanner inside the AI Statistician. "
                "Author domain-appropriate, executable empirical gates before either "
                "coding agent sees the task. Return JSON only."
            ),
            user_prompt=json.dumps(
                candidate_prompt_payload,
                separators=(",", ":"),
                default=str,
            ),
            model=request_model,
            max_tokens=min(max(1, int(config.max_tokens)), 4000),
            temperature=0.0,
            schema=response_schema,
            metadata={
                "subsystem": "ArchitectMetricContractPlanner",
                "agent": "LLMArchitectCoordinatorAgent",
                "provider_name": config.provider_name,
                "model_tier": config.model_tier,
                "resolved_model": request_model,
                "provider_structured_output": True,
                "semantic_review_revision_index": revision_index,
                "semantic_review_feedback_packet_id": str(
                    prior_review_packet.get("packet_id", "") or ""
                ),
                "active_prior_finding_count": len(active_finding_ids),
                "active_prior_finding_ledger_fingerprint": (
                    active_finding_ledger_fingerprint
                ),
            },
        )

        def build_packet(
            payload: Mapping[str, Any],
            response: Any,
            _raw_text: str,
        ) -> dict[str, Any]:
            requirements = payload.get("empirical_metric_requirements", [])
            requirement_rows = [
                dict(row) for row in requirements if isinstance(row, Mapping)
            ]
            parent_packet_id = str(
                prior_authoring_packet.get("packet_id", "") or ""
            )
            return {
                "schema_version": ARCHITECT_METRIC_REQUIREMENT_AUTHORING_SCHEMA_VERSION,
                "artifact_kind": "ArchitectMetricRequirementAuthoringPacket",
                "packet_id": (
                    "architect_metric_requirement_authoring:"
                    + stable_hash(
                        [
                            question.id,
                            requirement_rows,
                            revision_index,
                            parent_packet_id,
                        ]
                    )[:20]
                ),
                "question_id": question.id,
                "source_theory_packet_id": str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
                "source_theory_packet_hash": str(
                    theory_material.get("source_theory_packet_hash", "") or ""
                ),
                "source_agent": "ArchitectMetricContractPlanner",
                "provider_name": response.provider,
                "model": response.model or request_model,
                "model_tier": config.model_tier,
                "semantic_review_revision_index": revision_index,
                "parent_authoring_packet_id": parent_packet_id,
                "semantic_review_feedback_packet_id": str(
                    prior_review_packet.get("packet_id", "") or ""
                ),
                "repair_target_finding_ids": active_finding_ids,
                "repair_target_finding_ledger_fingerprint": (
                    active_finding_ledger_fingerprint
                ),
                "empirical_metric_requirements": requirement_rows,
                "empirical_metric_requirement_set_id": (
                    generated_metric_requirement_set_id(requirement_rows)
                ),
                "proof_evidence_status": (
                    "ARCHITECT_METRIC_REQUIREMENT_AUTHORING_NOT_PROOF_EVIDENCE"
                ),
                "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
            }

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            return validate_generated_metric_requirements(
                packet.get("empirical_metric_requirements", []),
                required_target_subsystems=(
                    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                ),
                expected_runtime_replicates=runtime_replicates,
            )

        authoring_packet = generate_validated_json_packet(
            provider=provider,
            request=request,
            extract_payload=extract_json_object,
            build_packet=build_packet,
            validate_packet=validate_packet,
            validation_label="LLM Architect metric-requirement packet",
            max_repair_attempts=config.max_repair_attempts,
            repair_context_builder=lambda **_kwargs: {
                "runtime_owned_replicates": runtime_replicates,
                "target_namespace": (
                    generated_metric_requirement_target_namespace_contract()
                ),
                "requirement_schema": generated_metric_requirement_prompt_schema(),
                "required_target_rows": prompt_payload["required_target_rows"],
                "repair_prompt_priority_instructions": prompt_payload[
                    "hard_requirements"
                ],
                "independent_semantic_review_repair": (
                    candidate_prompt_payload.get(
                        "independent_semantic_review_repair", {}
                    )
                ),
            },
        )
        authoring_packet_hash = stable_hash(authoring_packet)
        review_material = {
            "review_stage": "pre_execution_metric_contract_review",
            "execution_results_available": False,
            "runtime_owned_replicates": runtime_replicates,
            "target_namespace": (
                generated_metric_requirement_target_namespace_contract()
            ),
            "metric_evaluation_semantics": (
                generated_metric_evaluation_semantics_contract()
            ),
            "theory_developer_protocol_material": theory_material,
            "active_prior_finding_ledger": active_finding_ledger,
            "active_prior_finding_ledger_fingerprint": (
                active_finding_ledger_fingerprint
            ),
            "empirical_metric_requirements": [
                dict(row)
                for row in authoring_packet.get(
                    "empirical_metric_requirements", []
                )
                if isinstance(row, Mapping)
            ],
            "pre_execution_invariants": [
                "No generated code, simulation output, metric result, or acceptance decision exists yet.",
                "Review the candidate contract without proposing a post-result relaxation.",
                "Every accepted target subsystem must remain covered by at least one required row.",
            ],
        }
        trusted_review_lineage = {
            "authoring_packet_id": str(authoring_packet["packet_id"]),
            "authoring_packet_hash": authoring_packet_hash,
            "empirical_metric_requirement_set_id": str(
                authoring_packet["empirical_metric_requirement_set_id"]
            ),
            "source_theory_packet_id": str(
                theory_material.get("source_theory_packet_id", "") or ""
            ),
            "source_theory_packet_hash": str(
                theory_material.get("source_theory_packet_hash", "") or ""
            ),
            "source_agent": str(authoring_packet["source_agent"]),
            "source_model": str(authoring_packet["model"]),
            "source_model_tier": str(authoring_packet["model_tier"]),
        }
        semantic_review_packet = semantic_reviewer.review(
            question=question,
            review_material=review_material,
            trusted_lineage=trusted_review_lineage,
        )
        review_packet_hash = stable_hash(semantic_review_packet)
        routed_current_findings = [
            dict(row)
            for row in semantic_review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ]
        repair_ownership_packet: dict[str, Any] = {}
        if (
            semantic_review_packet.get("overall_verdict") == "REVISE"
            and repair_ownership_router is not None
            and routed_current_findings
        ):
            repair_ownership_packet = repair_ownership_router.route(
                question=question,
                review_material=review_material,
                semantic_review_packet=semantic_review_packet,
                trusted_lineage=trusted_review_lineage,
            )
            routed_current_findings = apply_architect_metric_repair_ownership_routes(
                findings=semantic_review_packet.get("findings", []),
                ownership_packet=repair_ownership_packet,
            )
        cumulative_finding_ledger = update_metric_protocol_finding_ledger(
            question_id=question.id,
            prior_ledger=cumulative_finding_ledger,
            prior_finding_reviews=semantic_review_packet.get(
                "prior_finding_reviews", []
            ),
            current_findings=routed_current_findings,
            current_verdict=str(
                semantic_review_packet.get("overall_verdict", "") or ""
            ),
            review_packet_id=str(semantic_review_packet["packet_id"]),
            revision_index=revision_index,
        )
        active_finding_ledger_after_review = (
            active_metric_protocol_finding_ledger(cumulative_finding_ledger)
        )
        current_finding_ids = {
            str(row.get("finding_id", "") or "")
            for row in routed_current_findings
            if str(row.get("finding_id", "") or "").strip()
        }
        carried_findings = []
        for ledger_row in active_finding_ledger_after_review:
            finding_id = str(ledger_row.get("finding_id", "") or "")
            finding = ledger_row.get("finding", {})
            if finding_id in current_finding_ids or not isinstance(
                finding, Mapping
            ):
                continue
            carried = dict(finding)
            carried["carried_forward_finding_id"] = finding_id
            carried_findings.append(carried)
        routed_findings = [*routed_current_findings, *carried_findings]
        recommended_repair_scope = _metric_protocol_combined_repair_scope(
            verdict=str(
                semantic_review_packet.get("overall_verdict", "") or ""
            ),
            findings=routed_findings,
        )
        semantic_review_history.append(
            {
                "revision_index": revision_index,
                "authoring_packet_id": str(authoring_packet["packet_id"]),
                "authoring_packet_hash": authoring_packet_hash,
                "empirical_metric_requirement_set_id": str(
                    authoring_packet["empirical_metric_requirement_set_id"]
                ),
                "source_theory_packet_id": str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
                "source_theory_packet_hash": str(
                    theory_material.get("source_theory_packet_hash", "") or ""
                ),
                "empirical_metric_requirements": [
                    dict(row)
                    for row in authoring_packet.get(
                        "empirical_metric_requirements", []
                    )
                    if isinstance(row, Mapping)
                ],
                "semantic_review_packet_id": str(
                    semantic_review_packet["packet_id"]
                ),
                "semantic_review_packet_hash": review_packet_hash,
                "semantic_review_model": str(
                    semantic_review_packet.get("model", "") or ""
                ),
                "semantic_review_model_tier": str(
                    semantic_review_packet.get("model_tier", "") or ""
                ),
                "independent_agent": bool(
                    semantic_review_packet.get("independent_agent")
                ),
                "independent_model": bool(
                    semantic_review_packet.get("independent_model")
                ),
                "independent_model_tier": bool(
                    semantic_review_packet.get("independent_model_tier")
                ),
                "overall_verdict": str(
                    semantic_review_packet.get("overall_verdict", "") or ""
                ),
                "semantic_reviewer_recommended_repair_scope": str(
                    semantic_review_packet.get(
                        "recommended_repair_scope", ""
                    )
                    or ""
                ),
                "recommended_repair_scope": recommended_repair_scope,
                "repair_ownership_packet_id": str(
                    repair_ownership_packet.get("packet_id", "") or ""
                ),
                "repair_ownership_packet_hash": (
                    stable_hash(repair_ownership_packet)
                    if repair_ownership_packet
                    else ""
                ),
                "repair_ownership_model": str(
                    repair_ownership_packet.get("model", "") or ""
                ),
                "repair_ownership_model_tier": str(
                    repair_ownership_packet.get("model_tier", "") or ""
                ),
                "repair_ownership_decisions": list(
                    repair_ownership_packet.get("decisions", []) or []
                ),
                "repair_target_finding_ids": list(
                    authoring_packet.get("repair_target_finding_ids", []) or []
                ),
                "repair_target_finding_ledger_fingerprint": str(
                    authoring_packet.get(
                        "repair_target_finding_ledger_fingerprint", ""
                    )
                    or ""
                ),
                "prior_finding_reviews": [
                    dict(row)
                    for row in semantic_review_packet.get(
                        "prior_finding_reviews", []
                    )
                    if isinstance(row, Mapping)
                ],
                "cumulative_finding_ledger": [
                    dict(row) for row in cumulative_finding_ledger
                ],
                "cumulative_finding_ledger_fingerprint": (
                    metric_protocol_finding_ledger_fingerprint(
                        cumulative_finding_ledger
                    )
                    if cumulative_finding_ledger
                    else ""
                ),
                "active_unresolved_finding_ids": [
                    str(row.get("finding_id", "") or "")
                    for row in active_finding_ledger_after_review
                    if str(row.get("finding_id", "") or "").strip()
                ],
                "carried_forward_finding_ids": [
                    str(row.get("carried_forward_finding_id", "") or "")
                    for row in carried_findings
                    if str(row.get("carried_forward_finding_id", "") or "").strip()
                ],
                "dimension_reviews": list(
                    semantic_review_packet.get("dimension_reviews", []) or []
                ),
                "findings": routed_findings,
                "repair_instructions": list(
                    semantic_review_packet.get("repair_instructions", []) or []
                ),
                "proof_evidence_status": (
                    "ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        if semantic_review_packet.get("overall_verdict") == "ACCEPT":
            authoring_packet["semantic_review_status"] = "ACCEPT"
            authoring_packet["semantic_review_packet"] = semantic_review_packet
            authoring_packet["semantic_review_packet_hash"] = review_packet_hash
            authoring_packet["semantic_review_revision_count"] = revision_index
            authoring_packet["semantic_review_history"] = semantic_review_history
            authoring_packet["cumulative_finding_ledger"] = [
                dict(row) for row in cumulative_finding_ledger
            ]
            authoring_packet["cumulative_finding_ledger_fingerprint"] = (
                metric_protocol_finding_ledger_fingerprint(
                    cumulative_finding_ledger
                )
                if cumulative_finding_ledger
                else ""
            )
            authoring_packet["semantic_review_boundary"] = (
                ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY
            )
            return authoring_packet
        if recommended_repair_scope != (
            ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT
        ):
            raise ArchitectMetricSemanticReviewRejected(
                question_id=question.id,
                semantic_review_history=semantic_review_history,
                source_theory_packet_id=str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
                source_theory_packet_hash=str(
                    theory_material.get("source_theory_packet_hash", "") or ""
                ),
            )
        prior_authoring_packet = authoring_packet
        prior_review_packet = {
            **dict(semantic_review_packet),
            "findings": routed_findings,
            "recommended_repair_scope": recommended_repair_scope,
            "repair_ownership_packet": repair_ownership_packet,
        }

    raise ArchitectMetricSemanticReviewRejected(
        question_id=question.id,
        semantic_review_history=semantic_review_history,
        source_theory_packet_id=str(
            theory_material.get("source_theory_packet_id", "") or ""
        ),
        source_theory_packet_hash=str(
            theory_material.get("source_theory_packet_hash", "") or ""
        ),
    )
