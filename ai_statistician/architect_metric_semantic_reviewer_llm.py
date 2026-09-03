from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .architect_theory_execution_preflight import (
    review_architect_theory_execution_preflight,
)
from .client_tool_loop import (
    ClientToolExecutionContext,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .generated_metric_contract import (
    evaluate_generated_metric_semantic_control,
    generated_metric_evaluator_certificate,
)
from .metric_protocol_finding_ledger import (
    METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT,
    METRIC_PROTOCOL_FINDING_UNRESOLVED,
    METRIC_PROTOCOL_PRIOR_FINDING_REVIEW_STATUSES,
    normalize_metric_protocol_findings,
)
from .model_backend import (
    ClientToolCall,
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorBackend,
    resolve_generator_model,
)
from .research_schema import OpenResearchQuestion, research_question_payload
from .packet_validation import PacketValidationError
from .theory_workspace import (
    THEORY_SCRATCHPAD_TOOL,
    TheoryScratchpadConfig,
    execute_theory_scratchpad_tool,
    theory_scratchpad_client_tool,
)


ARCHITECT_METRIC_SEMANTIC_REVIEW_SCHEMA_VERSION = 22
ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL_VERSION = 22
ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE = (
    "ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE"
)
ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY = (
    "Architect metric semantic review is an independent pre-execution judgment "
    "over a frozen empirical protocol. It may reject statistical or evaluator "
    "semantics, but it is not execution, simulation, acceptance, or proof evidence."
)
ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS = (
    "requirement_schema.required",
    "requirement_schema.properties.operator.enum",
    "metric_evaluation_semantics.scalar_aggregations.evaluation_order",
    "metric_evaluation_semantics.elementwise_aggregations.evaluation_order",
    "metric_evaluation_semantics.quorum_rule",
    "metric_evaluation_semantics.boolean_predicate_rule",
)
ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL: tuple[str, ...] = (
    (
        "Review only the supplied pre-execution artifacts. Do not use observed "
        "results, invent thresholds, select a repair owner, write implementation "
        "code, or claim proof."
    ),
    (
        "Reconstruct each frozen requirement from its cited scientific target. Check "
        "the estimand and regime, measurement identity, normalization, units, finite-"
        "sample attainability, operator, aggregation, and authority. Independently "
        "recompute every load-bearing constant and finite-run uncertainty claim on the "
        "actual comparison scale, using the optional scratch tool when useful. Put the "
        "decisive calculation in the rationale. Unsupported arithmetic, distributional "
        "claims, or asymptotic-to-finite-sample leaps must be UNCERTAIN or FAIL. Runtime "
        "resource limits are not scientific justification."
    ),
    (
        "For a legacy numeric row, substitute the declared raw metric through its "
        "exact aggregation and gate; runtime applies no hidden centering, absolute "
        "value, or normalization. For a model-owned source acceptance program, "
        "challenge the complete protocol as one preregistered scientific decision, "
        "including its formulas, scenarios, raw diagnostics, multiplicity, and "
        "attainability. Supply one scientifically justified semantic_positive_control "
        "that should pass; runtime checks only its declared boolean-or-numeric ABI."
    ),
    (
        "Judge the portfolio for consistency, redundancy, dependence, multiplicity, "
        "and non-vacuity. Required rows must correspond to distinct upstream claims, "
        "and the joint gate must have a defensible chance to accept a valid pipeline."
    ),
    (
        "Cite exact requirement:... or supplied authority anchor IDs. Mark an actual "
        "defect medium, high, or critical. Reserve low severity for a non-blocking "
        "advisory observation."
    ),
    (
        "Submit one complete judgment through the supplied terminal tool. If runtime "
        "returns validation observations, inspect them in this same reviewer context "
        "and submit a complete corrected judgment. Runtime derives "
        "ACCEPT only when every requirement and the portfolio pass, no prior finding "
        "remains unresolved, and no blocking finding exists."
    ),
)

ARCHITECT_METRIC_SEMANTIC_REVIEW_SUBMIT_TOOL = (
    "submit_architect_metric_semantic_review"
)

_REVIEW_STATUSES = ("PASS", "FAIL", "UNCERTAIN")
_FINDING_SEVERITIES = ("low", "medium", "high", "critical")
_BLOCKING_FINDING_SEVERITIES = frozenset({"medium", "high", "critical"})


@dataclass(frozen=True)
class ArchitectMetricSemanticReviewerConfig:
    model: str = ""
    model_tier: str = "sonnet"
    max_tokens: int = 7000
    client_tool_max_turns: int = 64
    client_tool_max_tool_calls: int = 64
    client_tool_max_no_progress_turns: int = 2
    temperature: float = 0.0
    provider_name: str = "anthropic"


def _requirements(review_material: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in review_material.get("empirical_metric_requirements", []) or []
        if isinstance(row, Mapping)
        and str(row.get("requirement_id", "") or "").strip()
    ]


def _requirement_ids(review_material: Mapping[str, Any]) -> list[str]:
    return [
        str(row.get("requirement_id", "") or "").strip()
        for row in _requirements(review_material)
    ]


def _active_prior_finding_ledger(
    review_material: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in review_material.get("active_prior_finding_ledger", []) or []
        if isinstance(row, Mapping)
        and str(row.get("finding_id", "") or "").strip()
    ]


def _active_prior_finding_ids(
    review_material: Mapping[str, Any],
) -> list[str]:
    return list(
        dict.fromkeys(
            str(row.get("finding_id", "") or "").strip()
            for row in _active_prior_finding_ledger(review_material)
        )
    )


def architect_metric_review_material_with_runtime_evaluator_certificate(
    review_material: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind model-authored requirements to the evaluator the runtime will execute."""

    body = deepcopy(dict(review_material))
    certificate = generated_metric_evaluator_certificate(_requirements(body))
    certificate_ids = [
        str(row.get("certificate_id", "") or "").strip()
        for row in certificate.get("certificates", []) or []
        if isinstance(row, Mapping)
        and str(row.get("certificate_id", "") or "").strip()
    ]
    authority = dict(body.get("runtime_contract_authority", {}) or {})
    authority.update(
        {
            "schema_version": 2,
            "runtime_owned": True,
            "evaluator_certificate_set_id": certificate["certificate_set_id"],
            "alternative_runtime_interpretations_allowed": False,
            "allowed_retraction_evidence_ids": list(
                dict.fromkeys(
                    [
                        *[
                            evidence_id
                            for evidence_id in (
                                ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS
                            )
                            if _static_runtime_evidence_available(
                                body,
                                evidence_id=evidence_id,
                            )
                        ],
                        *certificate_ids,
                    ]
                )
            ),
        }
    )
    body["runtime_contract_authority"] = authority
    body["runtime_evaluator_certificate"] = certificate
    return body


def _static_runtime_evidence_available(
    review_material: Mapping[str, Any],
    *,
    evidence_id: str,
) -> bool:
    if evidence_id.startswith("requirement_schema."):
        return bool(review_material.get("requirement_schema"))
    if evidence_id.startswith("metric_evaluation_semantics."):
        return bool(review_material.get("metric_evaluation_semantics"))
    return False


def _compact_theory_material(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    projected = {
        key: deepcopy(value[key])
        for key in (
            "artifact_kind",
            "source_theory_packet_id",
            "source_theory_packet_hash",
            "execution_results_available",
            "proof_evidence_status",
        )
        if value.get(key) not in (None, "", [], {})
    }
    semantic = value.get("theory_semantic_material", {})
    if not isinstance(semantic, Mapping):
        return projected
    compact_semantic = {
        key: deepcopy(semantic[key])
        for key in (
            "problem_card",
            "estimator_specs",
            "simulation_ademp_spec",
        )
        if semantic.get(key) not in (None, "", [], {})
    }
    derivation = semantic.get("theory_derivation_packet", {})
    if isinstance(derivation, Mapping):
        compact_derivation = {
            key: deepcopy(derivation[key])
            for key in (
                "derivation_summary",
                "assumption_ledger",
            )
            if derivation.get(key) not in (None, "", [], {})
        }
        if compact_derivation:
            compact_semantic["theory_derivation_packet"] = compact_derivation
    projected["theory_semantic_material"] = compact_semantic
    return projected


def _compact_implementation_handoff(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        key: deepcopy(value[key])
        for key in (
            "handoff_id",
            "question_id",
            "theory_packet_id",
            "implementation_interfaces",
            "runtime_selected_semantics",
            "proof_evidence_status",
        )
        if value.get(key) not in (None, "", [], {})
    }


def _compact_evaluator_certificate(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    rows = [
        {
            key: deepcopy(row[key])
            for key in (
                "certificate_id",
                "requirement_id",
                "target_subsystems",
                "metric_value_kind",
                "evaluator_mode",
                "operator",
                "aggregation",
                "required",
                "schema_valid",
                "comparison_stage",
                "aggregation_stage",
            )
            if row.get(key) not in (None, "", [], {})
        }
        for row in value.get("certificates", []) or []
        if isinstance(row, Mapping)
    ]
    for row in rows:
        row["implicit_transformations_applied"] = []
    return {
        "certificate_set_id": value.get("certificate_set_id", ""),
        "requirement_set_id": value.get("requirement_set_id", ""),
        "requirement_set_fingerprint": value.get(
            "requirement_set_fingerprint", ""
        ),
        "all_rows_schema_valid": value.get("all_rows_schema_valid"),
        "certificates": rows,
    }


def _compact_prior_finding_ledger(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in value:
        if not isinstance(raw_row, Mapping):
            continue
        finding_id = str(raw_row.get("finding_id", "") or "").strip()
        if not finding_id:
            continue
        finding = raw_row.get("finding", {})
        finding = finding if isinstance(finding, Mapping) else {}
        rows.append(
            {
                "finding_id": finding_id,
                "status": str(raw_row.get("status", "") or ""),
                "finding": {
                    key: deepcopy(finding[key])
                    for key in (
                        "severity",
                        "category",
                        "summary",
                        "observed_behavior",
                        "expected_behavior",
                        "evidence_refs",
                    )
                    if finding.get(key) not in (None, "", [], {})
                },
            }
        )
    return rows


def _cited_acceptance_catalog(
    review_material: Mapping[str, Any],
) -> list[dict[str, Any]]:
    catalog = [
        dict(row)
        for row in review_material.get("acceptance_authority_catalog", []) or []
        if isinstance(row, Mapping)
        and str(row.get("anchor_id", "") or "").strip()
    ]
    cited_ids = {
        str(anchor).strip()
        for requirement in _requirements(review_material)
        for anchor in requirement.get("source_anchors", []) or []
        if str(anchor).strip()
    }
    for requirement in _requirements(review_material):
        for authority in requirement.get("gate_field_authorities", []) or []:
            if not isinstance(authority, Mapping):
                continue
            cited_ids.update(
                str(anchor).strip()
                for anchor in authority.get("source_anchors", []) or []
                if str(anchor).strip()
            )
    return [
        row
        for row in catalog
        if str(row.get("anchor_id", "") or "").strip() in cited_ids
    ]


def _review_prompt_material(
    review_material: Mapping[str, Any],
) -> dict[str, Any]:
    requirements = _requirements(review_material)
    projected = {
        "review_stage": review_material.get("review_stage"),
        "execution_results_available": review_material.get(
            "execution_results_available"
        ),
        "model_authored_runtime_replicates": review_material.get(
            "model_authored_runtime_replicates"
        ),
        "runtime_execution_capacity": deepcopy(
            review_material.get("runtime_execution_capacity", {})
        ),
        "upstream_research_contract": deepcopy(
            review_material.get("upstream_research_contract", {})
        ),
        "theory_developer_protocol_material": _compact_theory_material(
            review_material.get("theory_developer_protocol_material", {})
        ),
        "accepted_implementation_interface_handoff": (
            _compact_implementation_handoff(
                review_material.get(
                    "accepted_implementation_interface_handoff", {}
                )
            )
        ),
        "empirical_metric_requirements": requirements,
        "runtime_evaluator_certificate": _compact_evaluator_certificate(
            review_material.get("runtime_evaluator_certificate", {})
        ),
        "metric_evaluation_semantics": deepcopy(
            review_material.get("metric_evaluation_semantics", {})
        ),
        "runtime_contract_authority": deepcopy(
            review_material.get("runtime_contract_authority", {})
        ),
        "acceptance_authority_catalog": _cited_acceptance_catalog(
            review_material
        ),
        "active_prior_finding_ledger": _compact_prior_finding_ledger(
            review_material.get("active_prior_finding_ledger", [])
        ),
        "pre_execution_invariants": deepcopy(
            review_material.get("pre_execution_invariants", [])
        ),
    }
    return {
        key: value
        for key, value in projected.items()
        if value not in (None, "", [], {})
    }


def build_architect_metric_semantic_review_prompt(
    *,
    question: OpenResearchQuestion,
    review_material: Mapping[str, Any],
) -> str:
    payload = {
        "review_protocol_version": (
            ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL_VERSION
        ),
        "review_protocol": list(ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL),
        "question": research_question_payload(question),
        "review_material": _review_prompt_material(review_material),
    }
    return (
        "Independently review this frozen empirical protocol before confirmatory "
        "execution. Submit one complete judgment through the terminal tool. The "
        "requirement_reviews object is keyed by the exact frozen requirement ID; "
        "do not repeat that ID inside its value. Use concise but substantive "
        "rationales; do not repeat the protocol or generate a repair recipe.\n\n"
        + json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
    )


def _review_row_schema(
    *,
    include_requirement_id: bool,
    include_semantic_positive_control: bool = False,
) -> dict[str, Any]:
    required = ["status", "rationale", "evidence_refs"]
    properties: dict[str, Any] = {
        "status": {"type": "string", "enum": list(_REVIEW_STATUSES)},
        "rationale": {
            "type": "string",
            "minLength": 1,
        },
        "evidence_refs": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
    }
    if include_requirement_id:
        required.insert(0, "requirement_id")
        properties["requirement_id"] = {"type": "string", "minLength": 1}
    if include_semantic_positive_control:
        required.append("semantic_positive_control")
        properties["semantic_positive_control"] = {
            "type": "object",
            "additionalProperties": False,
            "required": ["raw_comparison_value", "rationale", "evidence_refs"],
            "properties": {
                "raw_comparison_value": {
                    "anyOf": [{"type": "number"}, {"type": "boolean"}]
                },
                "rationale": {
                    "type": "string",
                    "minLength": 1,
                },
                "evidence_refs": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                        "minLength": 1,
                    },
                },
            },
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


_PRIOR_FINDING_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "finding_id",
        "status",
        "runtime_contract_evidence_id",
        "rationale",
    ],
    "properties": {
        "finding_id": {"type": "string", "minLength": 1},
        "status": {
            "type": "string",
            "enum": list(METRIC_PROTOCOL_PRIOR_FINDING_REVIEW_STATUSES),
        },
        "runtime_contract_evidence_id": {"type": "string"},
        "rationale": {
            "type": "string",
            "minLength": 1,
        },
    },
}


_FINDING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "prior_finding_id",
        "new_finding_rationale",
        "severity",
        "category",
        "summary",
        "observed_behavior",
        "expected_behavior",
        "evidence_refs",
    ],
    "properties": {
        "prior_finding_id": {"type": "string"},
        "new_finding_rationale": {"type": "string"},
        "severity": {
            "type": "string",
            "enum": list(_FINDING_SEVERITIES),
        },
        "category": {
            "type": "string",
            "minLength": 1,
        },
        "summary": {
            "type": "string",
            "minLength": 1,
        },
        "observed_behavior": {
            "type": "string",
            "minLength": 1,
        },
        "expected_behavior": {
            "type": "string",
            "minLength": 1,
        },
        "evidence_refs": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
    },
}


ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$defs": {
        "requirement_review": _review_row_schema(
            include_requirement_id=False,
            include_semantic_positive_control=True,
        ),
    },
    "type": "object",
    "additionalProperties": False,
    "required": [
        "requirement_reviews",
        "portfolio_review",
        "prior_finding_reviews",
        "findings",
    ],
    "properties": {
        "requirement_reviews": {
            "type": "object",
            "additionalProperties": False,
            "required": [],
            "properties": {},
        },
        "portfolio_review": _review_row_schema(
            include_requirement_id=False
        ),
        "prior_finding_reviews": {
            "type": "array",
            "items": _PRIOR_FINDING_REVIEW_SCHEMA,
        },
        "findings": {
            "type": "array",
            "items": _FINDING_SCHEMA,
        },
    },
}


def architect_metric_semantic_review_json_schema(
    review_material: Mapping[str, Any],
) -> dict[str, Any]:
    schema = deepcopy(ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA)
    requirement_ids = _requirement_ids(review_material)
    requirement_schema = schema["properties"]["requirement_reviews"]
    requirement_schema["required"] = requirement_ids
    requirement_schema["properties"] = {
        requirement_id: {"$ref": "#/$defs/requirement_review"}
        for requirement_id in requirement_ids
    }
    prior_ids = _active_prior_finding_ids(review_material)
    prior_schema = schema["properties"]["prior_finding_reviews"]
    prior_schema["minItems"] = len(prior_ids)
    prior_schema["maxItems"] = len(prior_ids)
    if prior_ids:
        prior_schema["items"]["properties"]["finding_id"]["enum"] = prior_ids
    finding_prior_schema = schema["properties"]["findings"]["items"][
        "properties"
    ]["prior_finding_id"]
    finding_prior_schema["enum"] = ["", *prior_ids]
    runtime_authority = review_material.get("runtime_contract_authority", {})
    allowed_retractions = [
        str(value).strip()
        for value in (
            runtime_authority.get("allowed_retraction_evidence_ids", [])
            if isinstance(runtime_authority, Mapping)
            else []
        )
        if str(value).strip()
    ]
    prior_schema["items"]["properties"][
        "runtime_contract_evidence_id"
    ]["enum"] = ["", *allowed_retractions]
    return schema


def _normalize_semantic_positive_control(
    value: Any,
    *,
    requirement_id: str,
) -> dict[str, Any]:
    row = dict(value) if isinstance(value, Mapping) else {}
    evidence_refs = list(
        dict.fromkeys(
            [
                f"requirement:{requirement_id}",
                *[
                    str(ref).strip()
                    for ref in row.get("evidence_refs", []) or []
                    if str(ref).strip()
                ],
            ]
        )
    )
    return {
        "raw_comparison_value": deepcopy(row.get("raw_comparison_value")),
        "rationale": str(row.get("rationale", "") or "").strip(),
        "evidence_refs": evidence_refs,
    }


def _normalize_review_rows(
    value: Any,
    *,
    expected_requirement_ids: Sequence[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, Mapping):
        return []
    keyed_rows = {
        str(requirement_id): row
        for requirement_id, row in value.items()
    }
    ordered_ids = [
        *expected_requirement_ids,
        *[
            requirement_id
            for requirement_id in keyed_rows
            if requirement_id not in expected_requirement_ids
        ],
    ]
    rows: list[dict[str, Any]] = []
    for requirement_id in ordered_ids:
        if requirement_id not in keyed_rows:
            continue
        row = keyed_rows[requirement_id]
        if not isinstance(row, Mapping):
            continue
        requirement_id = str(requirement_id or "").strip()
        evidence_refs = list(
            dict.fromkeys(
                [
                    *(
                        [f"requirement:{requirement_id}"]
                        if requirement_id
                        else []
                    ),
                    *[
                        str(ref).strip()
                        for ref in row.get("evidence_refs", []) or []
                        if str(ref).strip()
                    ],
                ]
            )
        )
        rows.append(
            {
                "requirement_id": requirement_id,
                "status": str(
                    row.get("status", "") or ""
                ).strip().upper(),
                "rationale": str(
                    row.get("rationale", "") or ""
                ).strip(),
                "evidence_refs": evidence_refs,
                "runtime_bound_requirement_ref": bool(requirement_id),
                "semantic_positive_control": (
                    _normalize_semantic_positive_control(
                        row.get("semantic_positive_control", {}),
                        requirement_id=requirement_id,
                    )
                ),
            }
        )
    return rows


def _execute_review_semantic_controls(
    requirement_reviews: Sequence[Mapping[str, Any]],
    *,
    review_material: Mapping[str, Any],
) -> list[dict[str, Any]]:
    requirements_by_id = {
        str(row.get("requirement_id", "") or "").strip(): row
        for row in _requirements(review_material)
    }
    rows: list[dict[str, Any]] = []
    for raw_row in requirement_reviews:
        row = deepcopy(dict(raw_row))
        requirement_id = str(row.get("requirement_id", "") or "").strip()
        control = dict(row.get("semantic_positive_control", {}) or {})
        requirement = requirements_by_id.get(requirement_id, {})
        evaluation = evaluate_generated_metric_semantic_control(
            requirement,
            raw_comparison_value=control.get("raw_comparison_value"),
        )
        control["runtime_evaluation"] = evaluation
        row["semantic_positive_control"] = control
        row["semantic_control_status"] = (
            "PASS"
            if evaluation.get("runtime_matches_scientific_expectation") is True
            else "CONTRADICTION"
        )
        rows.append(row)
    return rows


def _normalize_portfolio_review(value: Any) -> dict[str, Any]:
    row = dict(value) if isinstance(value, Mapping) else {}
    return {
        "status": str(row.get("status", "") or "").strip().upper(),
        "rationale": str(row.get("rationale", "") or "").strip(),
        "evidence_refs": list(
            dict.fromkeys(
                str(ref).strip()
                for ref in row.get("evidence_refs", []) or []
                if str(ref).strip()
            )
        ),
    }


def _normalize_prior_reviews(value: Any) -> list[dict[str, Any]]:
    rows = []
    for raw_row in value or []:
        if not isinstance(raw_row, Mapping):
            continue
        status = str(raw_row.get("status", "") or "").strip().upper()
        runtime_evidence_id = str(
            raw_row.get("runtime_contract_evidence_id", "") or ""
        ).strip()
        if status != METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT:
            runtime_evidence_id = ""
        rows.append(
            {
                "finding_id": str(
                    raw_row.get("finding_id", "") or ""
                ).strip(),
                "status": status,
                "runtime_contract_evidence_id": runtime_evidence_id,
                "rationale": str(
                    raw_row.get("rationale", "") or ""
                ).strip(),
            }
        )
    return rows


def _normalize_findings(
    value: Any,
    *,
    question_id: str,
    active_prior_ids: Sequence[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    active = set(active_prior_ids)
    for raw_row in value or []:
        if not isinstance(raw_row, Mapping):
            continue
        row = {
            key: deepcopy(raw_row.get(key))
            for key in (
                "prior_finding_id",
                "new_finding_rationale",
                "severity",
                "category",
                "summary",
                "observed_behavior",
                "expected_behavior",
                "evidence_refs",
            )
        }
        row["prior_finding_id"] = str(
            row.get("prior_finding_id", "") or ""
        ).strip()
        row["new_finding_rationale"] = str(
            row.get("new_finding_rationale", "") or ""
        ).strip()
        row["severity"] = str(row.get("severity", "") or "").strip().lower()
        row["category"] = str(row.get("category", "") or "").strip()
        row["summary"] = str(row.get("summary", "") or "").strip()
        row["observed_behavior"] = str(
            row.get("observed_behavior", "") or ""
        ).strip()
        row["expected_behavior"] = str(
            row.get("expected_behavior", "") or ""
        ).strip()
        row["evidence_refs"] = list(
            dict.fromkeys(
                str(ref).strip()
                for ref in row.get("evidence_refs", []) or []
                if str(ref).strip()
            )
        )
        if row["prior_finding_id"] in active:
            row["finding_id"] = row["prior_finding_id"]
        rows.append(row)
    return normalize_metric_protocol_findings(
        question_id=question_id,
        findings=rows,
        preserve_existing_ids=True,
    )


def _derived_verdict(
    *,
    requirement_reviews: Sequence[Mapping[str, Any]],
    portfolio_review: Mapping[str, Any],
    prior_finding_reviews: Sequence[Mapping[str, Any]],
    findings: Sequence[Mapping[str, Any]],
) -> str:
    return (
        "ACCEPT"
        if requirement_reviews
        and all(
            str(row.get("status", "") or "").upper() == "PASS"
            and str(row.get("semantic_control_status", "") or "").upper()
            == "PASS"
            for row in requirement_reviews
        )
        and str(portfolio_review.get("status", "") or "").upper() == "PASS"
        and all(
            str(row.get("status", "") or "").upper()
            != METRIC_PROTOCOL_FINDING_UNRESOLVED
            for row in prior_finding_reviews
        )
        and not any(
            str(row.get("severity", "") or "").lower()
            in _BLOCKING_FINDING_SEVERITIES
            for row in findings
        )
        else "REVISE"
    )


def _normalize_architect_metric_semantic_review_packet(
    payload: Mapping[str, Any],
    *,
    question: OpenResearchQuestion,
    trusted_lineage: Mapping[str, Any],
    review_material: Mapping[str, Any],
    model: str,
    model_tier: str,
    provider_name: str,
    raw_response: str,
) -> dict[str, Any]:
    requirement_reviews = _execute_review_semantic_controls(
        _normalize_review_rows(
            payload.get("requirement_reviews", {}),
            expected_requirement_ids=_requirement_ids(review_material),
        ),
        review_material=review_material,
    )
    portfolio_review = _normalize_portfolio_review(
        payload.get("portfolio_review", {})
    )
    prior_reviews = _normalize_prior_reviews(
        payload.get("prior_finding_reviews", [])
    )
    active_prior_ids = _active_prior_finding_ids(review_material)
    findings = _normalize_findings(
        payload.get("findings", []),
        question_id=question.id,
        active_prior_ids=active_prior_ids,
    )
    verdict = _derived_verdict(
        requirement_reviews=requirement_reviews,
        portfolio_review=portfolio_review,
        prior_finding_reviews=prior_reviews,
        findings=findings,
    )
    runtime_authority = review_material.get("runtime_contract_authority", {})
    runtime_authority = (
        dict(runtime_authority)
        if isinstance(runtime_authority, Mapping)
        else {}
    )
    certificate = review_material.get("runtime_evaluator_certificate", {})
    certificate = dict(certificate) if isinstance(certificate, Mapping) else {}
    certificate_rows = [
        dict(row)
        for row in certificate.get("certificates", []) or []
        if isinstance(row, Mapping)
    ]
    source_agent = str(
        trusted_lineage.get("source_agent", "") or ""
    ).strip()
    source_model = str(
        trusted_lineage.get("source_model", "") or ""
    ).strip()
    source_model_tier = str(
        trusted_lineage.get("source_model_tier", "") or ""
    ).strip()
    body = {
        "question_id": question.id,
        "authoring_packet_id": str(
            trusted_lineage.get("authoring_packet_id", "") or ""
        ),
        "authoring_packet_hash": str(
            trusted_lineage.get("authoring_packet_hash", "") or ""
        ),
        "reviewed_empirical_metric_requirement_set_id": str(
            trusted_lineage.get(
                "empirical_metric_requirement_set_id", ""
            )
            or ""
        ),
        "source_theory_packet_id": str(
            trusted_lineage.get("source_theory_packet_id", "") or ""
        ),
        "source_theory_packet_hash": str(
            trusted_lineage.get("source_theory_packet_hash", "") or ""
        ),
        "source_agent": source_agent,
        "source_model": source_model,
        "source_model_tier": source_model_tier,
        "acceptance_authority_catalog_id": str(
            trusted_lineage.get("acceptance_authority_catalog_id", "") or ""
        ),
        "acceptance_authority_catalog_fingerprint": str(
            trusted_lineage.get(
                "acceptance_authority_catalog_fingerprint", ""
            )
            or ""
        ),
        "review_input_fingerprint": stable_hash(review_material),
        "review_protocol_version": (
            ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL_VERSION
        ),
        "pre_execution_review": True,
        "execution_results_observed": False,
        "independent_agent": bool(
            source_agent
            and source_agent != "LLMArchitectMetricSemanticReviewerAgent"
        ),
        "independent_invocation": True,
        "independent_model": bool(source_model and source_model != model),
        "independent_model_tier": bool(
            source_model_tier and source_model_tier != model_tier
        ),
        "requirement_reviews": requirement_reviews,
        "portfolio_review": portfolio_review,
        "prior_finding_reviews": prior_reviews,
        "findings": findings,
        "overall_verdict": verdict,
        "reviewed_requirement_ids": _requirement_ids(review_material),
        "expected_prior_finding_ids": active_prior_ids,
        "runtime_contract_retraction_evidence_ids": [
            str(value).strip()
            for value in runtime_authority.get(
                "allowed_retraction_evidence_ids", []
            )
            or []
            if str(value).strip()
        ],
        "runtime_evaluator_certificate_set_id": str(
            certificate.get("certificate_set_id", "") or ""
        ),
        "runtime_evaluator_certificate_requirement_set_id": str(
            certificate.get("requirement_set_id", "") or ""
        ),
        "runtime_evaluator_certificate_requirement_set_fingerprint": str(
            certificate.get("requirement_set_fingerprint", "") or ""
        ),
        "runtime_evaluator_certificate_ids": [
            str(row.get("certificate_id", "") or "").strip()
            for row in certificate_rows
            if str(row.get("certificate_id", "") or "").strip()
        ],
        "runtime_evaluator_certificate_all_rows_schema_valid": bool(
            certificate.get("all_rows_schema_valid") is True
        ),
        "proof_evidence_status": (
            ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE
        ),
        "evidence_boundary": ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY,
    }
    packet_id = "architect_metric_semantic_review:" + stable_hash(
        {
            "question_id": question.id,
            "provider": provider_name,
            "model": model,
            "model_tier": model_tier,
            "body": body,
        }
    )[:24]
    return {
        "schema_version": ARCHITECT_METRIC_SEMANTIC_REVIEW_SCHEMA_VERSION,
        "artifact_kind": "ArchitectMetricSemanticReviewPacket",
        "packet_id": packet_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_agent": "LLMArchitectMetricSemanticReviewerAgent",
        "provider": provider_name,
        "model": model,
        "model_tier": model_tier,
        "raw_response_fingerprint": stable_hash(raw_response),
        **body,
    }


def _requirement_ref_matches(requirement_id: str, evidence_ref: str) -> bool:
    prefix = f"requirement:{requirement_id}"
    return evidence_ref == prefix or evidence_ref.startswith(
        (prefix + ".", prefix + "/", prefix + "#/")
    )


def validate_architect_metric_semantic_review_packet(
    packet: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if packet.get("proof_evidence_status") != (
        ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE
    ):
        errors.append("metric review must preserve the non-proof boundary")
    if packet.get("pre_execution_review") is not True:
        errors.append("metric review must be pre-execution")
    if packet.get("execution_results_observed") is not False:
        errors.append("metric review cannot observe execution results")
    if packet.get("runtime_evaluator_certificate_all_rows_schema_valid") is not True:
        errors.append("metric review requires a schema-valid evaluator certificate")

    expected_ids = [
        str(value).strip()
        for value in packet.get("reviewed_requirement_ids", []) or []
        if str(value).strip()
    ]
    rows = packet.get("requirement_reviews", [])
    if not isinstance(rows, list):
        errors.append("requirement_reviews must be an array")
        rows = []
    observed_ids: list[str] = []
    nonpassing = False
    runtime_semantic_control_contradiction = False
    for index, raw_row in enumerate(rows):
        if not isinstance(raw_row, Mapping):
            errors.append(f"requirement_reviews[{index}] must be an object")
            continue
        requirement_id = str(
            raw_row.get("requirement_id", "") or ""
        ).strip()
        observed_ids.append(requirement_id)
        status = str(raw_row.get("status", "") or "").strip().upper()
        if status not in _REVIEW_STATUSES:
            errors.append(
                f"requirement review {requirement_id or index} has invalid status"
            )
        if status != "PASS":
            nonpassing = True
        control = raw_row.get("semantic_positive_control", {})
        if not isinstance(control, Mapping):
            errors.append(
                f"requirement review {requirement_id or index} missing "
                "semantic_positive_control"
            )
            control = {}
        control_value = control.get("raw_comparison_value")
        if not isinstance(control_value, (bool, int, float)):
            errors.append(
                f"requirement review {requirement_id or index} positive control "
                "must contain one boolean or numeric raw_comparison_value"
            )
        if not str(control.get("rationale", "") or "").strip():
            errors.append(
                f"requirement review {requirement_id or index} positive control "
                "missing rationale"
            )
        control_refs = [
            str(value).strip()
            for value in control.get("evidence_refs", []) or []
            if str(value).strip()
        ]
        if requirement_id and not any(
            _requirement_ref_matches(requirement_id, ref)
            for ref in control_refs
        ):
            errors.append(
                f"requirement review {requirement_id} positive control must cite "
                "its frozen row"
            )
        control_evaluation = control.get("runtime_evaluation", {})
        if not isinstance(control_evaluation, Mapping) or not str(
            control_evaluation.get("control_evaluation_id", "") or ""
        ):
            errors.append(
                f"requirement review {requirement_id or index} missing runtime "
                "semantic-control evaluation"
            )
        semantic_control_status = str(
            raw_row.get("semantic_control_status", "") or ""
        ).upper()
        if semantic_control_status not in {"PASS", "CONTRADICTION"}:
            errors.append(
                f"requirement review {requirement_id or index} has invalid "
                "semantic_control_status"
            )
        if semantic_control_status == "CONTRADICTION":
            nonpassing = True
            runtime_semantic_control_contradiction = True
        if not str(raw_row.get("rationale", "") or "").strip():
            errors.append(
                f"requirement review {requirement_id or index} missing rationale"
            )
        refs = [
            str(value).strip()
            for value in raw_row.get("evidence_refs", []) or []
            if str(value).strip()
        ]
        if not refs:
            errors.append(
                f"requirement review {requirement_id or index} missing evidence_refs"
            )
        elif requirement_id and not any(
            _requirement_ref_matches(requirement_id, ref) for ref in refs
        ):
            errors.append(
                f"requirement review {requirement_id} must cite its frozen row"
            )
    if observed_ids != expected_ids:
        errors.append(
            "requirement_reviews must cover the exact ordered frozen requirement IDs; "
            f"expected={json.dumps(expected_ids)} observed={json.dumps(observed_ids)}"
        )

    portfolio = packet.get("portfolio_review", {})
    if not isinstance(portfolio, Mapping):
        errors.append("portfolio_review must be an object")
        portfolio = {}
    portfolio_status = str(
        portfolio.get("status", "") or ""
    ).strip().upper()
    if portfolio_status not in _REVIEW_STATUSES:
        errors.append("portfolio_review has invalid status")
    if portfolio_status != "PASS":
        nonpassing = True
    if not str(portfolio.get("rationale", "") or "").strip():
        errors.append("portfolio_review missing rationale")
    portfolio_refs = [
        str(value).strip()
        for value in portfolio.get("evidence_refs", []) or []
        if str(value).strip()
    ]
    if not portfolio_refs:
        errors.append("portfolio_review missing evidence_refs")

    expected_prior_ids = [
        str(value).strip()
        for value in packet.get("expected_prior_finding_ids", []) or []
        if str(value).strip()
    ]
    prior_rows = packet.get("prior_finding_reviews", [])
    if not isinstance(prior_rows, list):
        errors.append("prior_finding_reviews must be an array")
        prior_rows = []
    observed_prior_ids: list[str] = []
    allowed_retractions = {
        str(value).strip()
        for value in packet.get(
            "runtime_contract_retraction_evidence_ids", []
        )
        or []
        if str(value).strip()
    }
    for index, raw_row in enumerate(prior_rows):
        if not isinstance(raw_row, Mapping):
            errors.append(f"prior_finding_reviews[{index}] must be an object")
            continue
        finding_id = str(raw_row.get("finding_id", "") or "").strip()
        observed_prior_ids.append(finding_id)
        status = str(raw_row.get("status", "") or "").strip().upper()
        if status not in METRIC_PROTOCOL_PRIOR_FINDING_REVIEW_STATUSES:
            errors.append(f"prior finding {finding_id} has invalid status")
        if status == METRIC_PROTOCOL_FINDING_UNRESOLVED:
            nonpassing = True
        if not str(raw_row.get("rationale", "") or "").strip():
            errors.append(f"prior finding {finding_id} missing rationale")
        runtime_evidence_id = str(
            raw_row.get("runtime_contract_evidence_id", "") or ""
        ).strip()
        if status == METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT:
            if runtime_evidence_id not in allowed_retractions:
                errors.append(
                    f"prior finding {finding_id} has invalid runtime retraction evidence"
                )
        elif runtime_evidence_id:
            errors.append(
                f"prior finding {finding_id} must not cite runtime retraction evidence"
            )
    if observed_prior_ids != expected_prior_ids:
        errors.append(
            "prior_finding_reviews must cover the exact ordered active finding IDs"
        )

    findings = packet.get("findings", [])
    if not isinstance(findings, list):
        errors.append("findings must be an array")
        findings = []
    blocking_findings = 0
    for index, raw_row in enumerate(findings):
        if not isinstance(raw_row, Mapping):
            errors.append(f"findings[{index}] must be an object")
            continue
        severity = str(raw_row.get("severity", "") or "").strip().lower()
        if severity not in _FINDING_SEVERITIES:
            errors.append(f"findings[{index}] has invalid severity")
        if severity in _BLOCKING_FINDING_SEVERITIES:
            blocking_findings += 1
        for field in (
            "category",
            "summary",
            "observed_behavior",
            "expected_behavior",
        ):
            if not str(raw_row.get(field, "") or "").strip():
                errors.append(f"findings[{index}] missing {field}")
        refs = [
            str(value).strip()
            for value in raw_row.get("evidence_refs", []) or []
            if str(value).strip()
        ]
        if not refs:
            errors.append(f"findings[{index}] missing evidence_refs")
        prior_finding_id = str(
            raw_row.get("prior_finding_id", "") or ""
        ).strip()
        if prior_finding_id and prior_finding_id not in expected_prior_ids:
            errors.append(
                f"findings[{index}] references an inactive prior finding"
            )
        if (
            not prior_finding_id
            and expected_prior_ids
            and not str(
                raw_row.get("new_finding_rationale", "") or ""
            ).strip()
        ):
            errors.append(
                f"findings[{index}] new finding missing new_finding_rationale"
            )
    if (
        nonpassing
        and blocking_findings == 0
        and not runtime_semantic_control_contradiction
    ):
        errors.append(
            "a non-passing requirement or portfolio judgment requires one "
            "medium, high, or critical finding"
        )

    expected_verdict = _derived_verdict(
        requirement_reviews=[
            row for row in rows if isinstance(row, Mapping)
        ],
        portfolio_review=portfolio,
        prior_finding_reviews=[
            row for row in prior_rows if isinstance(row, Mapping)
        ],
        findings=[
            row for row in findings if isinstance(row, Mapping)
        ],
    )
    if str(packet.get("overall_verdict", "") or "").upper() != expected_verdict:
        errors.append("overall_verdict does not match the compact review judgments")
    for field in (
        "authoring_packet_id",
        "authoring_packet_hash",
        "reviewed_empirical_metric_requirement_set_id",
        "source_agent",
        "source_model",
        "source_model_tier",
        "review_input_fingerprint",
        "runtime_evaluator_certificate_set_id",
        "runtime_evaluator_certificate_requirement_set_id",
        "runtime_evaluator_certificate_requirement_set_fingerprint",
    ):
        if not str(packet.get(field, "") or "").strip():
            errors.append(f"metric review missing trusted lineage field: {field}")
    if str(
        packet.get("runtime_evaluator_certificate_requirement_set_id", "") or ""
    ) != str(
        packet.get("reviewed_empirical_metric_requirement_set_id", "") or ""
    ):
        errors.append("evaluator certificate and reviewed requirement set differ")
    if expected_verdict == "ACCEPT":
        if packet.get("independent_agent") is not True:
            errors.append("ACCEPT requires an independent reviewer agent")
        if packet.get("independent_invocation") is not True:
            errors.append("ACCEPT requires a separate reviewer invocation")
    return sorted(set(errors))


def _resolve_path(
    root: Any,
    encoded_segments: Sequence[str],
) -> tuple[bool, Any]:
    current = root
    for encoded in encoded_segments:
        segment = str(encoded).replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and segment in current:
            current = current[segment]
        elif (
            isinstance(current, (list, tuple))
            and segment.isdigit()
            and int(segment) < len(current)
        ):
            current = current[int(segment)]
        else:
            return False, None
    return True, deepcopy(current)


def _metric_evidence_value(
    *,
    review_material: Mapping[str, Any],
    evidence_ref: str,
) -> tuple[str, bool, Any, str, list[str]]:
    reference = str(evidence_ref or "").strip()
    for raw_row in review_material.get(
        "acceptance_authority_catalog", []
    ) or []:
        if not isinstance(raw_row, Mapping):
            continue
        if str(raw_row.get("anchor_id", "") or "").strip() == reference:
            root = reference.split("#", 1)[0]
            role = {
                "theory": "source_theory_packet",
                "question": "research_question",
                "runtime_contract": "runtime_contract",
            }.get(root, "acceptance_authority")
            return role, True, deepcopy(raw_row.get("content")), "", []

    requirements = _requirements(review_material)
    for requirement in requirements:
        requirement_id = str(
            requirement.get("requirement_id", "") or ""
        ).strip()
        prefix = f"requirement:{requirement_id}"
        if not requirement_id or not reference.startswith(prefix):
            continue
        suffix = reference[len(prefix) :]
        segments = (
            suffix[2:].split("/")
            if suffix.startswith("#/")
            else suffix[1:].split(".")
            if suffix.startswith(".")
            else suffix[1:].split("/")
            if suffix.startswith("/")
            else []
        )
        if not suffix:
            return (
                "metric_protocol_candidate",
                True,
                deepcopy(requirement),
                requirement_id,
                [],
            )
        exists, value = _resolve_path(requirement, segments)
        return (
            "metric_protocol_candidate",
            exists,
            value,
            requirement_id,
            segments,
        )

    certificate = review_material.get("runtime_evaluator_certificate", {})
    if isinstance(certificate, Mapping):
        for raw_row in certificate.get("certificates", []) or []:
            if (
                isinstance(raw_row, Mapping)
                and str(raw_row.get("certificate_id", "") or "").strip()
                == reference
            ):
                return (
                    "runtime_evaluator_certificate",
                    True,
                    deepcopy(dict(raw_row)),
                    str(raw_row.get("requirement_id", "") or ""),
                    [],
                )
    if reference in ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS:
        return "runtime_contract", True, reference, "", []
    return "unknown", False, None, "", []


def bind_architect_metric_finding_evidence_identities(
    *,
    findings: Any,
    review_material: Mapping[str, Any],
    prior_ledger: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Bind cited values to immutable fingerprints without editing review content."""

    prior_bindings: dict[str, list[dict[str, Any]]] = {}
    for raw_row in prior_ledger:
        if not isinstance(raw_row, Mapping):
            continue
        finding_id = str(raw_row.get("finding_id", "") or "").strip()
        finding = raw_row.get("finding", {})
        if not finding_id or not isinstance(finding, Mapping):
            continue
        prior_bindings[finding_id] = [
            dict(row)
            for row in finding.get("evidence_identity_bindings", []) or []
            if isinstance(row, Mapping)
        ]

    bound: list[dict[str, Any]] = []
    for raw_finding in findings if isinstance(findings, list) else []:
        if not isinstance(raw_finding, Mapping):
            continue
        finding = deepcopy(dict(raw_finding))
        finding_id = str(
            finding.get("finding_id", "")
            or finding.get("prior_finding_id", "")
            or ""
        ).strip()
        bindings = [
            dict(row) for row in prior_bindings.get(finding_id, [])
        ]
        seen = {
            str(row.get("evidence_ref", "") or "").strip()
            for row in bindings
        }
        for raw_ref in finding.get("evidence_refs", []) or []:
            evidence_ref = str(raw_ref or "").strip()
            if not evidence_ref or evidence_ref in seen:
                continue
            (
                role,
                exists,
                value,
                requirement_id,
                segments,
            ) = _metric_evidence_value(
                review_material=review_material,
                evidence_ref=evidence_ref,
            )
            bindings.append(
                {
                    "evidence_ref": evidence_ref,
                    "artifact_role": role,
                    "semantic_identity_bound": bool(exists),
                    "origin_value_fingerprint": (
                        stable_hash(value) if exists else ""
                    ),
                    "requirement_id": requirement_id,
                    "relative_path_segments": segments,
                }
            )
            seen.add(evidence_ref)
        if bindings:
            finding["evidence_identity_bindings"] = bindings
        bound.append(finding)
    return bound


class LLMArchitectMetricSemanticReviewerAgent:
    """Independent compact reviewer for a frozen empirical metric protocol."""

    def __init__(
        self,
        *,
        provider: GeneratorBackend,
        config: ArchitectMetricSemanticReviewerConfig = (
            ArchitectMetricSemanticReviewerConfig()
        ),
        source_retriever: Any = None,
        research_sources: Any = None,
        research_source_discovery: Any = None,
    ) -> None:
        self.provider = provider
        self.config = config
        self.source_retriever = source_retriever
        self.research_sources = research_sources
        self.research_source_discovery = research_source_discovery

    def review_theory_execution_preflight(
        self,
        *,
        question: OpenResearchQuestion,
        theory_protocol_material: Mapping[str, Any],
        upstream_research_contract: Mapping[str, Any],
        prior_finding_ledger: Sequence[Mapping[str, Any]] = (),
        author_scratch_execution_refs: Sequence[Mapping[str, Any]] = (),
        theory_scratchpad: TheoryScratchpadConfig | None = None,
        recovery_checkpoint: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return review_architect_theory_execution_preflight(
            provider=self.provider,
            question=question,
            theory_protocol_material=theory_protocol_material,
            upstream_research_contract=upstream_research_contract,
            model=self.config.model,
            model_tier=self.config.model_tier,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            provider_name=self.config.provider_name,
            prior_finding_ledger=prior_finding_ledger,
            author_scratch_execution_refs=author_scratch_execution_refs,
            source_retriever=self.source_retriever,
            research_sources=self.research_sources,
            research_source_discovery=self.research_source_discovery,
            theory_scratchpad=theory_scratchpad,
            recovery_checkpoint=recovery_checkpoint,
        )

    def review(
        self,
        *,
        question: OpenResearchQuestion,
        review_material: Mapping[str, Any],
        trusted_lineage: Mapping[str, Any],
        theory_scratchpad: TheoryScratchpadConfig | None = None,
    ) -> dict[str, Any]:
        if not callable(getattr(self.provider, "generate_client_tool_turn", None)):
            raise ValueError(
                "metric semantic review requires native client-tool turns; "
                "one-shot full-packet generation is not a canonical fallback"
            )
        review_material = (
            architect_metric_review_material_with_runtime_evaluator_certificate(
                review_material
            )
        )
        request_model = resolve_generator_model(
            provider_name=self.config.provider_name,
            requested_model=self.config.model,
            model_tier=self.config.model_tier,
        )
        prompt = build_architect_metric_semantic_review_prompt(
            question=question,
            review_material=review_material,
        )
        schema = architect_metric_semantic_review_json_schema(review_material)
        schema.pop("$schema", None)
        scratch_refs: list[dict[str, Any]] = []
        validation_history: list[dict[str, Any]] = []
        last_invalid_packet: dict[str, Any] | None = None
        system_prompt = (
            "You are the independent ArchitectMetricSemanticReviewer inside an "
            "AI Statistician AgentRuntime. Reconstruct and review the frozen "
            "empirical protocol rigorously. You may run exploratory scratch "
            "calculations, but do not inspect outcomes, edit authoritative artifacts, "
            "prescribe a repair, or claim proof."
        )
        tools = (
            *((theory_scratchpad_client_tool(),) if theory_scratchpad else ()),
            ClientToolDefinition(
                name=ARCHITECT_METRIC_SEMANTIC_REVIEW_SUBMIT_TOOL,
                description=(
                    "Submit the complete independent pre-execution metric judgment. "
                    "Runtime returns any validation observations to this same reviewer "
                    "session without editing or retaining a partial judgment."
                ),
                input_schema=schema,
                terminal=True,
                strict=True,
            ),
        )
        request = ClientToolTurnRequest(
            system_prompt=(
                system_prompt
            ),
            messages=(
                {
                    "role": "user",
                    "content": (
                        prompt
                        + "\n\nChoose any scratch calculations needed to check the "
                        "scientific arithmetic, then call "
                        + ARCHITECT_METRIC_SEMANTIC_REVIEW_SUBMIT_TOOL
                        + ". Scratch observations are diagnostic only. Prose alone "
                        "cannot submit a review."
                    ),
                },
            ),
            tools=tools,
            model=request_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            tool_choice=(
                "any"
                if theory_scratchpad
                else ARCHITECT_METRIC_SEMANTIC_REVIEW_SUBMIT_TOOL
            ),
            disable_parallel_tool_use=True,
            enable_prompt_caching=True,
            metadata={
                "subsystem": "ArchitectMetricSemanticReviewer",
                "agent": "LLMArchitectMetricSemanticReviewerAgent",
                "provider_name": self.config.provider_name,
                "model_tier": self.config.model_tier,
                "resolved_model": request_model,
                "review_input_fingerprint": stable_hash(review_material),
                "review_protocol_version": (
                    ARCHITECT_METRIC_SEMANTIC_REVIEW_PROTOCOL_VERSION
                ),
                "review_prompt_chars": len(prompt),
                "review_schema_chars": len(
                    json.dumps(schema, separators=(",", ":"))
                ),
                "review_requirement_count": len(
                    _requirement_ids(review_material)
                ),
                "client_tool_transport": True,
                "same_session_validation_feedback": True,
                "scientific_scratch_available": theory_scratchpad is not None,
                "full_packet_regeneration_disabled": True,
                "strict_terminal_tool_schema": True,
                "reviewer_local_retry_budget": False,
            },
        )

        def normalize_submission(
            payload: Mapping[str, Any], *, model: str, provider_name: str
        ) -> dict[str, Any]:
            return _normalize_architect_metric_semantic_review_packet(
                payload,
                question=question,
                trusted_lineage=trusted_lineage,
                review_material=review_material,
                model=model or request_model,
                model_tier=self.config.model_tier,
                provider_name=self.config.provider_name or provider_name,
                raw_response=json.dumps(payload, sort_keys=True, default=str),
            )

        def execute_tool(
            call: ClientToolCall, context: ClientToolExecutionContext
        ) -> ClientToolExecutionResult:
            nonlocal last_invalid_packet
            if call.name == THEORY_SCRATCHPAD_TOOL and theory_scratchpad:
                result, execution_ref = execute_theory_scratchpad_tool(
                    tool_input=call.input,
                    scratchpad=theory_scratchpad,
                    sandbox_binding=(
                        "architect_metric_semantic_review",
                        question.id,
                        stable_hash(review_material),
                    ),
                    artifact_id=(
                        "metric-review-scratch:"
                        + stable_hash([question.id, context.total_calls_before])[:20]
                    ),
                    run_index=len(scratch_refs) + 1,
                    owner_label="ArchitectMetricSemanticReviewer",
                )
                scratch_refs.append(execution_ref)
                return result
            if call.name != ARCHITECT_METRIC_SEMANTIC_REVIEW_SUBMIT_TOOL:
                raise ClientToolInputError("unsupported metric review tool")
            submission = dict(call.input)
            submission_fingerprint = stable_hash(submission)
            packet = normalize_submission(
                submission,
                model=request_model,
                provider_name=str(getattr(self.provider, "provider_name", "") or ""),
            )
            errors = validate_architect_metric_semantic_review_packet(packet)
            validation_history.append(
                {
                    "attempt_index": len(validation_history),
                    "ok": not errors,
                    "errors": list(errors),
                    "submission_fingerprint": submission_fingerprint,
                }
            )
            if errors:
                last_invalid_packet = deepcopy(packet)
                rejection = {
                    "ok": False,
                    "error": "architect_metric_semantic_review_submission_rejected",
                    "submission_saved": False,
                    "submission_fingerprint": submission_fingerprint,
                    "validation_errors": list(errors),
                    "instruction": (
                        "Inspect every validation observation and submit one complete "
                        "corrected judgment. Reviewed artifacts remain immutable."
                    ),
                }
                return ClientToolExecutionResult(
                    content=rejection,
                    is_error=True,
                    state_changed=False,
                    observation_key=(
                        "metric-review-rejected:"
                        + stable_hash([submission_fingerprint, errors])
                    ),
                )
            return ClientToolExecutionResult(
                content={"ok": True, "submitted": True},
                state_changed=False,
                terminal=True,
                terminal_payload={"review_payload": deepcopy(submission)},
                observation_key="metric-review-submitted:" + stable_hash(packet),
            )

        try:
            loop = run_bounded_client_tool_loop(
                backend=self.provider,
                request=request,
                execute_tool=execute_tool,
                max_turns=self.config.client_tool_max_turns,
                max_tool_calls=self.config.client_tool_max_tool_calls,
                max_no_progress_turns=(
                    self.config.client_tool_max_no_progress_turns
                ),
            )
        except ClientToolLoopError as exc:
            raise PacketValidationError(
                validation_label="Architect metric semantic review packet",
                attempts=exc.turns,
                errors=(
                    list(validation_history[-1]["errors"])
                    if validation_history
                    else [exc.reason]
                ),
                history=list(validation_history),
                last_invalid_packet=last_invalid_packet,
            ) from exc
        payload = loop.terminal_payload.get("review_payload", {})
        if not isinstance(payload, Mapping):
            raise PacketValidationError(
                validation_label="Architect metric semantic review packet",
                attempts=loop.turns,
                errors=["accepted client-tool submission payload is malformed"],
                history=list(validation_history),
            )
        packet = normalize_submission(
            payload, model=loop.model, provider_name=loop.provider
        )
        packet["validation_errors"] = []
        packet["ok"] = True
        packet["client_tool_loop"] = {
            "transport": "native_same_reviewer_session_v2",
            "turns": loop.turns,
            "tool_calls": loop.tool_calls,
            "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
            "transcript_fingerprint": loop.transcript_fingerprint,
            "provider_usage": dict(loop.provider_usage),
            "validation_submissions": len(validation_history),
            "validation_feedback_observed": any(
                not row["ok"] for row in validation_history
            ),
            "strict_terminal_tool_schema": True,
            "validation_submission_history": list(validation_history),
            "scratch_execution_refs": scratch_refs,
            "full_packet_regeneration_used": False,
        }
        return packet
