from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from .agent_runtime import agent_runtime_substage
from .architect_metric_repair_ownership_router_llm import (
    ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED,
    LLMArchitectMetricRepairOwnershipRouterAgent,
    apply_architect_metric_repair_ownership_routes,
)
from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY,
    ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT,
    LLMArchitectMetricSemanticReviewerAgent,
    architect_metric_review_material_with_runtime_evaluator_certificate,
    architect_metric_semantic_recommended_repair_scope,
)
from .fingerprint import stable_hash
from .generated_metric_contract import (
    GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS,
    generated_metric_acceptance_authority_catalog,
    generated_metric_evaluation_semantics_contract,
    generated_metric_numeric_authority_repair_matrix,
    generated_metric_requirement_json_schema,
    generated_metric_requirement_prompt_schema,
    generated_metric_requirement_set_id,
    generated_metric_requirement_target_namespace_contract,
    is_generated_metric_numeric_authority_error,
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


def _metric_candidate_repair_available(findings: list[dict[str, Any]]) -> bool:
    return any(
        str(row.get("repair_scope", "") or "").strip()
        == ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT
        for row in findings
        if isinstance(row, Mapping)
    )


def _fresh_candidate_requirement_set_errors(
    *,
    candidate_requirement_set_id: str,
    fresh_candidate_revision_context: Mapping[str, Any],
) -> list[str]:
    source_requirement_set_id = str(
        fresh_candidate_revision_context.get("source_requirement_set_id", "")
        or ""
    )
    if (
        source_requirement_set_id
        and str(candidate_requirement_set_id or "") == source_requirement_set_id
    ):
        return [
            "versioned fresh candidate must not reuse the rejected "
            "requirement-set fingerprint"
        ]
    return []


@dataclass(frozen=True)
class ArchitectMetricContractAuthoringConfig:
    max_tokens: int = 5000
    model_tier: str = "sonnet"
    provider_name: str = "anthropic"
    max_repair_attempts: int = 2
    metric_semantic_reviewer_max_revisions: int = 2


def _metric_authoring_repair_priority_instructions(
    errors: Any,
) -> list[str]:
    error_rows = (
        [str(error) for error in errors]
        if isinstance(errors, list | tuple)
        else []
    )
    instructions: list[str] = []
    if any(
        is_generated_metric_numeric_authority_error(error)
        for error in error_rows
    ):
        instructions.append(
            "Use numeric_authority_repair_matrix as the local retrieval index. "
            "Each implicated row includes the exact current_requirement plus exact "
            "matching catalog nodes for each gate field, and marks values with no "
            "upstream numeric match. Preserve unimplicated fields. For each error, "
            "decide ownership "
            "from the current artifacts. If the value is explicitly source-derived "
            "or mandated, "
            "retain that authority kind and cite the exact catalog node containing "
            "it. If it is an Architect-chosen pre-execution empirical benchmark, "
            "tolerance, or quorum absent upstream, set that row to "
            "acceptance_authority_kind=architect_preregistered_design and rewrite "
            "its rationale; do not copy the value into theory or falsely relabel it "
            "as source-derived. Do not change a gate merely to match an anchor, and "
            "do not treat the matrix as an automatic repair."
        )
    instructions.extend(
        [
            (
                "Resolve every supplied local validation error while preserving "
                "valid requirement rows, stable requirement IDs, and unrelated "
                "fields."
            ),
            (
                "Use only exact anchor IDs from the current acceptance authority "
                "catalog; never invent or paraphrase an anchor."
            ),
            (
                "Keep one independently compared scalar quantity, or one truly "
                "homogeneous collection, per row and split independent gates."
            ),
            (
                "Retain at least one required SimulationEngineer row and copy the "
                "runtime-owned replicate count exactly into its field and protocol."
            ),
            (
                "Use only pre-execution artifacts: do not cite observed results, "
                "claim proof, relax a gate after execution, or add task-specific "
                "runtime rules."
            ),
        ]
    )
    return instructions[:6]


def _metric_authoring_repair_context(
    *,
    invalid_packet: Mapping[str, Any] | None,
    errors: Any,
    runtime_replicates: int,
    acceptance_authority_catalog_id: str,
    acceptance_authority_catalog: list[dict[str, Any]],
    required_target_rows: list[dict[str, Any]],
    independent_semantic_review_repair: Mapping[str, Any] | None,
) -> dict[str, Any]:
    error_rows = (
        [str(error) for error in errors]
        if isinstance(errors, list | tuple)
        else []
    )
    requirements = (
        invalid_packet.get("empirical_metric_requirements", [])
        if isinstance(invalid_packet, Mapping)
        else []
    )
    numeric_authority_repair_matrix = (
        generated_metric_numeric_authority_repair_matrix(
            requirements,
            validation_errors=error_rows,
            acceptance_authority_catalog=acceptance_authority_catalog,
        )
    )

    repair_catalog = acceptance_authority_catalog
    repair_catalog_scope = "full_catalog"
    if numeric_authority_repair_matrix:
        relevant_anchor_ids: set[str] = set()
        for matrix_row in numeric_authority_repair_matrix:
            relevant_anchor_ids.update(
                str(anchor_id)
                for anchor_id in matrix_row.get("current_source_anchors", [])
                if str(anchor_id).strip()
            )
            for gate_match in matrix_row.get("numeric_gate_matches", []):
                if not isinstance(gate_match, Mapping):
                    continue
                relevant_anchor_ids.update(
                    str(node.get("anchor_id", "") or "").strip()
                    for node in gate_match.get("matching_catalog_nodes", [])
                    if isinstance(node, Mapping)
                    and str(node.get("anchor_id", "") or "").strip()
                )
        repair_catalog = [
            dict(row)
            for row in acceptance_authority_catalog
            if str(row.get("anchor_id", "") or "").strip()
            in relevant_anchor_ids
        ]
        repair_catalog_scope = "numeric_authority_local_slice"

    return {
        "runtime_owned_replicates": runtime_replicates,
        "target_namespace": generated_metric_requirement_target_namespace_contract(),
        "requirement_schema": generated_metric_requirement_prompt_schema(),
        "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
        "acceptance_authority_catalog": repair_catalog,
        "acceptance_authority_catalog_scope": repair_catalog_scope,
        "acceptance_authority_catalog_total_rows": len(
            acceptance_authority_catalog
        ),
        "acceptance_authority_catalog_repair_rows": len(repair_catalog),
        "numeric_authority_repair_matrix": numeric_authority_repair_matrix,
        "numeric_authority_repair_automatic_selection": False,
        "required_target_rows": required_target_rows,
        "repair_prompt_priority_instructions": (
            _metric_authoring_repair_priority_instructions(error_rows)
        ),
        "independent_semantic_review_repair": dict(
            independent_semantic_review_repair or {}
        ),
    }


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
    fresh_candidate_revision_context: Mapping[str, Any] | None = None,
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
    fresh_revision = (
        dict(fresh_candidate_revision_context)
        if isinstance(fresh_candidate_revision_context, Mapping)
        else {}
    )
    if fresh_revision and not (
        fresh_revision.get("artifact_kind")
        == "RuntimeEvaluationProtocolFreshCandidateContext"
        and fresh_revision.get("prior_candidate_execution_observed") is True
        and fresh_revision.get("raw_execution_artifacts_included") is False
        and fresh_revision.get("post_result_threshold_relaxation_allowed") is False
        and fresh_revision.get("different_requirement_set_required") is True
        and str(fresh_revision.get("fresh_candidate_id", "") or "").strip()
        and str(
            fresh_revision.get("source_requirement_set_id", "") or ""
        ).strip()
        and isinstance(fresh_revision.get("source_requirement_rows"), list)
        and fresh_revision.get("source_requirement_rows")
        and isinstance(
            fresh_revision.get("structural_review_findings"), list
        )
        and fresh_revision.get("structural_review_findings")
        and str(
            fresh_revision.get("current_source_theory_packet_id", "") or ""
        )
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(
            fresh_revision.get("current_source_theory_packet_hash", "") or ""
        )
        == str(theory_material.get("source_theory_packet_hash", "") or "")
    ):
        raise ValueError(
            "fresh metric candidate authoring requires sanitized, theory-bound "
            "revision lineage with no raw prior execution artifacts"
        )

    runtime_replicates = int(
        runtime_contract.get("generated_sandbox_runtime_replicates", 0) or 0
    )
    question_material = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    acceptance_authority_catalog = generated_metric_acceptance_authority_catalog(
        question=question_material,
        runtime_contract=runtime_contract,
        theory_protocol_material=theory_material,
    )
    acceptance_authority_anchor_ids = [
        str(row["anchor_id"])
        for row in acceptance_authority_catalog
        if str(row.get("anchor_id", "") or "").strip()
    ]
    acceptance_authority_catalog_id = (
        "generated_metric_acceptance_authority_catalog:"
        + stable_hash(acceptance_authority_catalog)[:20]
    )
    response_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["empirical_metric_requirements"],
        "properties": {
            "empirical_metric_requirements": {
                "type": "array",
                "minItems": 1,
                "items": generated_metric_requirement_json_schema(
                    require_acceptance_authority=True,
                    authority_anchor_ids=acceptance_authority_anchor_ids,
                ),
            }
        },
    }
    prompt_payload = {
        "task": (
            "Author the pre-execution empirical acceptance requirements used by "
            "the AI Statistician confirmatory simulation agent."
        ),
        "question": question_material,
        "theory_developer_protocol_material": theory_material,
        "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
        "acceptance_authority_catalog": acceptance_authority_catalog,
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
                "generated empirical-evaluation subsystem. Algorithm implementation "
                "is accepted by execution plus independent semantic review; do not "
                "assign finite-sample statistical-performance thresholds to the "
                "AlgorithmEngineer artifact itself."
            ),
            (
                "Prefer the smallest nonredundant portfolio that covers the central "
                "plausible estimator, simulation, or DGP failure modes in the composed "
                "confirmatory experiment. Every row must distinguish a failure mode not "
                "already covered; do not add structural, calibration, or convenience "
                "checks merely because they are measurable."
            ),
            (
                "When an independent review shows that a row is ambiguous, fragile, "
                "or poorly calibrated and the remaining rows still cover its author "
                "subsystem and failure mode, delete that row instead of adding more "
                "gates or complicating the protocol."
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
                "For theory_derived and evaluation_mandated rows, each threshold, "
                "lower or upper bound, nonzero tolerance, and quorum must exactly "
                "match explicit_numeric_values on a cited node of the same kind. A "
                "theory_parameter_instantiation row must use the exact cited "
                "evaluation-design value. In an architect_preregistered_design row, "
                "those numbers are instead explicitly owned by this pre-execution "
                "empirical design and must not be copied into or misrepresented as "
                "theory."
            ),
            (
                "Every source_anchors entry must copy one exact anchor_id from "
                "acceptance_authority_catalog. Free-form citations, packet IDs with "
                "appended prose, and invented source labels are invalid."
            ),
            (
                "Set acceptance_authority_kind=theory_derived only when the cited "
                "theory nodes actually derive or bound every threshold, tolerance, "
                "and quorum in the row. A topical mention, monotonicity statement, "
                "asymptotic rate, or KL relationship does not by itself authorize a "
                "finite-sample performance cutoff."
            ),
            (
                "Use acceptance_authority_kind=theory_parameter_instantiation only "
                "when one cited theory_derived node gives the symbolic finite-sample "
                "gate (for example error <= alpha) and a separate cited "
                "evaluation_design node preregisters the exact parameter value. Every "
                "numeric gate must occur in that design node. A design value alone, "
                "or a performance wish in expected behavior, cannot authorize a gate."
            ),
            (
                "Set acceptance_authority_kind=evaluation_mandated only when an exact "
                "catalog node explicitly mandates the numeric gate. A request to "
                "evaluate power or stopping time, or a runtime simulation-planning "
                "target, does not specify a minimum power or maximum stopping time."
            ),
            (
                "Prefer theory_derived, theory_parameter_instantiation, or "
                "evaluation_mandated whenever their requirements are genuinely met. "
                "When a required finite-sample benchmark is an evaluation decision "
                "not fixed upstream, use "
                "acceptance_authority_kind=architect_preregistered_design. Cite the "
                "exact current question or theory nodes that define the metric, DGP, "
                "procedure, and estimand, then justify every chosen threshold, "
                "nonzero tolerance, and quorum from decision relevance, Monte Carlo "
                "uncertainty, the fixed runtime budget, and attainable behavior. The "
                "cited nodes provide semantic context and need not contain those "
                "candidate-owned numbers."
            ),
            (
                "An architect_preregistered_design gate is frozen before generated "
                "code or simulation, remains empirical-control evidence only, and "
                "must pass independent semantic review. Never describe it as a "
                "theorem guarantee, derive it from observed results, or retune it "
                "against its own confirmatory execution."
            ),
            (
                "When a useful measurement has no authority-backed acceptance cutoff, "
                "emit it only as required=false with "
                "acceptance_authority_kind=diagnostic_only, or omit it. Never turn an "
                "unsupported expectation into a theory-backed required gate. Use an "
                "architect_preregistered_design gate only when a statistically "
                "defensible pre-execution acceptance decision is actually needed."
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
    if fresh_revision:
        prompt_payload["fresh_candidate_revision_context"] = fresh_revision
        prompt_payload["hard_requirements"].extend(
            [
                (
                    "This is a new versioned candidate. The prior requirement set "
                    "and failed execution remain immutable and ineligible for "
                    "acceptance."
                ),
                (
                    "Use only structural_review_findings from the revision context; "
                    "they may summarize prior observations but are not acceptance "
                    "evidence. Do not request raw prior artifacts or lower a threshold "
                    "merely to accommodate the failed run."
                ),
                (
                    "Return a requirement set with a different set fingerprint that "
                    "resolves the structural identifiability or measurement defect. "
                    "Every confirmatory artifact will be regenerated under the new "
                    "frozen set and fresh_candidate_seed."
                ),
            ]
        )
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
                    "only what is needed to resolve every finding; an implicated row "
                    "may be deleted when it is redundant and remaining rows preserve "
                    "author-subsystem coverage and the central independent failure "
                    "modes; do not replace the "
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
            max_tokens=min(max(1, int(config.max_tokens)), 8000),
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
                "acceptance_authority_catalog_id": (
                    acceptance_authority_catalog_id
                ),
                "acceptance_authority_catalog_fingerprint": stable_hash(
                    acceptance_authority_catalog
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
                "fresh_candidate_id": str(
                    fresh_revision.get("fresh_candidate_id", "") or ""
                ),
                "source_requirement_set_id": str(
                    fresh_revision.get("source_requirement_set_id", "") or ""
                ),
                "source_revision_manifest_id": str(
                    fresh_revision.get("source_revision_manifest_id", "") or ""
                ),
                "proof_evidence_status": (
                    "ARCHITECT_METRIC_REQUIREMENT_AUTHORING_NOT_PROOF_EVIDENCE"
                ),
                "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
            }

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            errors = validate_generated_metric_requirements(
                packet.get("empirical_metric_requirements", []),
                required_target_subsystems=(
                    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                ),
                expected_runtime_replicates=runtime_replicates,
                require_acceptance_authority=True,
                acceptance_authority_catalog=acceptance_authority_catalog,
            )
            errors.extend(
                _fresh_candidate_requirement_set_errors(
                    candidate_requirement_set_id=str(
                        packet.get("empirical_metric_requirement_set_id", "")
                        or ""
                    ),
                    fresh_candidate_revision_context=fresh_revision,
                )
            )
            return errors

        with agent_runtime_substage(
            "architect_metric_requirement_author",
            metadata={
                "revision_index": revision_index,
                "model_tier": config.model_tier,
                "max_packet_repair_attempts": config.max_repair_attempts,
                "active_prior_finding_count": len(active_finding_ids),
            },
        ):
            authoring_packet = generate_validated_json_packet(
                provider=provider,
                request=request,
                extract_payload=extract_json_object,
                build_packet=build_packet,
                validate_packet=validate_packet,
                validation_label="LLM Architect metric-requirement packet",
                max_repair_attempts=config.max_repair_attempts,
                repair_context_builder=lambda **kwargs: (
                    _metric_authoring_repair_context(
                        invalid_packet=(
                            kwargs.get("invalid_packet")
                            if isinstance(
                                kwargs.get("invalid_packet"), Mapping
                            )
                            else None
                        ),
                        errors=kwargs.get("errors", []),
                        runtime_replicates=runtime_replicates,
                        acceptance_authority_catalog_id=(
                            acceptance_authority_catalog_id
                        ),
                        acceptance_authority_catalog=(
                            acceptance_authority_catalog
                        ),
                        required_target_rows=prompt_payload[
                            "required_target_rows"
                        ],
                        independent_semantic_review_repair=(
                            candidate_prompt_payload.get(
                                "independent_semantic_review_repair", {}
                            )
                        ),
                    )
                ),
                semantic_patch_repair=True,
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
            "requirement_schema": generated_metric_requirement_json_schema(
                require_acceptance_authority=True,
                authority_anchor_ids=acceptance_authority_anchor_ids,
            ),
            "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
            "acceptance_authority_catalog": acceptance_authority_catalog,
            "runtime_contract_authority": {
                "schema_version": 1,
                "runtime_owned": True,
                "allowed_retraction_status": (
                    "RETRACTED_RUNTIME_CONTRACT_CONFLICT"
                ),
                "allowed_retraction_evidence_ids": list(
                    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS
                ),
                "retraction_boundary": (
                    "This status only corrects a reviewer finding that conflicts "
                    "with the supplied runtime schema or evaluator order. It cannot "
                    "waive a statistical, theory, identifiability, feasibility, or "
                    "calibration defect."
                ),
            },
            "theory_developer_protocol_material": theory_material,
            "fresh_candidate_revision_context": fresh_revision,
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
                "No confirmatory simulation output, empirical metric result, or acceptance decision exists yet.",
                "A reviewed AlgorithmEngineer source artifact may exist, but its smoke diagnostics cannot tune statistical thresholds.",
                "The reviewer cannot require unavailable pilot results as a prerequisite; theory-grounded finite-sample uncertainty may remain advisory when the frozen experiment is designed to measure it.",
                "Review the candidate contract without proposing a post-result relaxation.",
                "Every empirical-evaluation target subsystem must remain covered by at least one required row.",
            ],
        }
        review_material = (
            architect_metric_review_material_with_runtime_evaluator_certificate(
                review_material
            )
        )
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
            "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
            "acceptance_authority_catalog_fingerprint": stable_hash(
                acceptance_authority_catalog
            ),
            "source_agent": str(authoring_packet["source_agent"]),
            "source_model": str(authoring_packet["model"]),
            "source_model_tier": str(authoring_packet["model_tier"]),
            "fresh_candidate_id": str(
                fresh_revision.get("fresh_candidate_id", "") or ""
            ),
            "source_revision_manifest_id": str(
                fresh_revision.get("source_revision_manifest_id", "") or ""
            ),
        }
        with agent_runtime_substage(
            "architect_metric_semantic_reviewer",
            metadata={
                "revision_index": revision_index,
                "model_tier": str(
                    getattr(
                        getattr(semantic_reviewer, "config", None),
                        "model_tier",
                        "",
                    )
                    or ""
                ),
                "blinded_independent_invocation": True,
            },
        ):
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
            with agent_runtime_substage(
                "architect_metric_repair_ownership_router",
                metadata={
                    "revision_index": revision_index,
                    "finding_count": len(routed_current_findings),
                    "model_tier": str(
                        getattr(
                            getattr(repair_ownership_router, "config", None),
                            "model_tier",
                            "",
                        )
                        or ""
                    ),
                },
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
                "acceptance_authority_catalog_id": (
                    acceptance_authority_catalog_id
                ),
                "acceptance_authority_catalog_fingerprint": stable_hash(
                    acceptance_authority_catalog
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
                "independent_invocation": bool(
                    semantic_review_packet.get("independent_invocation")
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
        if recommended_repair_scope == ARCHITECT_METRIC_REPAIR_SCOPE_UNRESOLVED or (
            recommended_repair_scope
            != ARCHITECT_METRIC_SEMANTIC_REPAIR_SCOPE_METRIC_CONTRACT
            and not _metric_candidate_repair_available(routed_findings)
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
