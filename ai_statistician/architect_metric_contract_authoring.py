from __future__ import annotations

import json
import math
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from .agent_runtime import agent_runtime_substage
from .architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_RUNTIME_CONTRACT_RETRACTION_EVIDENCE_IDS,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_BOUNDARY,
    LLMArchitectMetricSemanticReviewerAgent,
    architect_metric_review_material_with_runtime_evaluator_certificate,
    bind_architect_metric_finding_evidence_identities,
)
from .fingerprint import stable_hash
from .generated_metric_contract import (
    GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS,
    GENERATED_METRIC_CONTRACT_AGGREGATIONS,
    GENERATED_METRIC_CONTRACT_OPERATORS,
    GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS,
    GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS,
    GENERATED_METRIC_VALUE_KINDS,
    generated_metric_acceptance_authority_catalog,
    generated_metric_acceptance_authority_prompt_catalog,
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_json_schema,
    generated_metric_requirement_prompt_schema,
    generated_metric_requirement_set_id,
    generated_metric_requirement_target_namespace_contract,
    materialize_generated_metric_gate_field_authorities,
    validate_generated_metric_requirements,
)
from .implementation_metric_handoff import (
    accepted_implementation_interface_handoff_errors,
)
from .structured_output_retry import (
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
from .semantic_review_feedback import model_observations_without_repair_recipes


ARCHITECT_METRIC_REQUIREMENT_AUTHORING_SCHEMA_VERSION = 5
_METRIC_AUTHORING_LARGE_PROMPT_CHARS = 60_000
_METRIC_AUTHORING_LARGE_RESPONSE_TOKENS = 8_000
MAX_CONFIRMATORY_METRIC_REQUIREMENTS = 8
FRESH_METRIC_AUTHORING_AUTHORITY_KIND = "architect_preregistered_design"
FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS = frozenset(
    {
        "source_anchors",
        "acceptance_authority_rationale",
    }
)
FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD = "gate_field_authorities"
FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS = frozenset(
    {"source_anchors", "rationale"}
)


def _frozen_metric_protocol_rebinding_mutable_fields(
    source_rows: Any,
) -> frozenset[str]:
    fields = set(FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS)
    if isinstance(source_rows, list) and any(
        isinstance(row, Mapping)
        and FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in row
        for row in source_rows
    ):
        fields.add(FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD)
    return frozenset(fields)


def _frozen_gate_field_authority_immutable_view(value: Any) -> Any:
    if not isinstance(value, list):
        return value
    return [
        {
            str(key): item
            for key, item in row.items()
            if key not in FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS
        }
        if isinstance(row, Mapping)
        else row
        for row in value
    ]


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
        review_stage = str(last_review.get("review_stage", "") or "")
        failure_summary = (
            "independent theory-to-execution preflight rejected the current "
            "TheoryDeveloper handoff before metric authoring"
            if review_stage == "theory_execution_preflight"
            else "independent semantic reviewer did not accept any metric contract "
            f"candidate after {len(history)} attempt(s)"
        )
        super().__init__(
            validation_label="Architect pre-execution metric semantic review",
            attempts=len(history),
            errors=[
                failure_summary,
                *[
                    str(row.get("summary", "") or "")
                    for row in last_review.get("findings", []) or []
                    if isinstance(row, Mapping)
                    and str(row.get("summary", "") or "").strip()
                ],
            ],
            history=history,
        )


class ArchitectMetricSemanticReviewPacketValidationError(PacketValidationError):
    """Reviewer validation failure bound to its validated author candidate."""

    def __init__(
        self,
        *,
        cause: PacketValidationError,
        authoring_packet: Mapping[str, Any],
        revision_index: int,
        trusted_review_lineage: Mapping[str, Any],
        review_material_fingerprint: str,
        semantic_review_history: list[dict[str, Any]],
    ) -> None:
        self.authoring_packet = deepcopy(dict(authoring_packet))
        self.authoring_packet_hash = stable_hash(self.authoring_packet)
        self.revision_index = int(revision_index)
        self.trusted_review_lineage = deepcopy(dict(trusted_review_lineage))
        self.review_material_fingerprint = str(
            review_material_fingerprint or ""
        )
        self.semantic_review_history = deepcopy(semantic_review_history)
        super().__init__(
            validation_label=cause.validation_label,
            attempts=cause.attempts,
            errors=cause.errors,
            history=cause.history,
            last_invalid_packet=cause.last_invalid_packet,
        )


def _frozen_metric_protocol_rebinding_errors(
    *,
    candidate_requirements: Any,
    rebinding_context: Mapping[str, Any],
) -> list[str]:
    source_rows = rebinding_context.get("source_requirement_rows", [])
    if not isinstance(source_rows, list) or not source_rows:
        return ["frozen metric rebinding source rows are missing"]
    if not isinstance(candidate_requirements, list):
        return ["frozen metric rebinding candidate rows must be a list"]
    source_by_id = {
        str(row.get("requirement_id", "") or ""): dict(row)
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("requirement_id", "") or "").strip()
    }
    candidate_by_id = {
        str(row.get("requirement_id", "") or ""): dict(row)
        for row in candidate_requirements
        if isinstance(row, Mapping)
        and str(row.get("requirement_id", "") or "").strip()
    }
    errors: list[str] = []
    if len(source_by_id) != len(source_rows):
        errors.append(
            "frozen metric rebinding source requirement IDs must be unique and "
            "nonempty"
        )
    if len(candidate_by_id) != len(candidate_requirements):
        errors.append(
            "frozen metric rebinding candidate requirement IDs must be unique and "
            "nonempty"
        )
    source_ids = list(source_by_id)
    candidate_ids = list(candidate_by_id)
    if candidate_ids != source_ids:
        errors.append(
            "frozen metric rebinding must preserve the exact ordered requirement "
            f"IDs: expected={source_ids!r} observed={candidate_ids!r}"
        )
    for requirement_id in source_ids:
        source_row = source_by_id[requirement_id]
        candidate_row = candidate_by_id.get(requirement_id)
        if candidate_row is None:
            continue
        mutable_fields = set(FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS)
        source_has_gate_field_authorities = (
            FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in source_row
        )
        if source_has_gate_field_authorities:
            mutable_fields.add(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
        immutable_fields = (
            set(source_row) | set(candidate_row)
        ) - mutable_fields
        for field in sorted(immutable_fields):
            if candidate_row.get(field) != source_row.get(field):
                errors.append(
                    "frozen metric rebinding may not change "
                    f"{requirement_id}.{field}"
                )
        if source_has_gate_field_authorities and (
            _frozen_gate_field_authority_immutable_view(
                candidate_row.get(
                    FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
                )
            )
            != _frozen_gate_field_authority_immutable_view(
                source_row.get(
                    FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
                )
            )
        ):
            errors.append(
                "frozen metric rebinding may not change "
                f"{requirement_id}."
                f"{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                "field identities or authority kinds"
            )
    return errors


def _reconstruct_frozen_metric_protocol_requirements(
    *,
    binding_rows: Any,
    rebinding_context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    source_rows = rebinding_context.get("source_requirement_rows", [])
    if not isinstance(source_rows, list) or not source_rows:
        return [], ["frozen metric rebinding source rows are missing"]
    if not isinstance(binding_rows, list):
        return [], ["frozen metric rebinding output rows must be a list"]

    source_by_id = {
        str(row.get("requirement_id", "") or ""): dict(row)
        for row in source_rows
        if isinstance(row, Mapping)
        and str(row.get("requirement_id", "") or "").strip()
    }
    source_ids = [
        str(row.get("requirement_id", "") or "")
        for row in source_rows
        if isinstance(row, Mapping)
    ]
    observed_ids: list[str] = []
    reconstructed_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, raw_binding in enumerate(binding_rows):
        prefix = f"empirical_metric_requirements[{index}]"
        if not isinstance(raw_binding, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        binding = dict(raw_binding)
        requirement_id = str(binding.get("requirement_id", "") or "")
        observed_ids.append(requirement_id)
        source_row = source_by_id.get(requirement_id)
        if source_row is None:
            errors.append(
                f"{prefix}.requirement_id is not one of the frozen requirement IDs"
            )
            reconstructed_rows.append(binding)
            continue
        mutable_fields = set(FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS)
        if FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in source_row:
            mutable_fields.add(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
        output_fields = {"requirement_id", *mutable_fields}
        extra_fields = sorted(set(binding) - output_fields)
        if extra_fields:
            errors.append(
                f"{prefix} contains runtime-owned frozen fields: "
                f"{extra_fields!r}"
            )
        missing_fields = sorted(output_fields - set(binding))
        if missing_fields:
            errors.append(
                f"{prefix} is missing required binding fields: "
                f"{missing_fields!r}"
            )
        reconstructed = dict(source_row)
        for field in FROZEN_METRIC_PROTOCOL_REBINDING_MUTABLE_FIELDS:
            if field in binding:
                reconstructed[field] = binding[field]
        if FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in mutable_fields:
            source_gate_rows = source_row.get(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
            binding_gate_rows = binding.get(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
            if not isinstance(source_gate_rows, list):
                errors.append(
                    f"{prefix}.{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                    "source rows must be an array"
                )
            elif not isinstance(binding_gate_rows, list):
                errors.append(
                    f"{prefix}.{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                    "must be an array"
                )
            else:
                if len(binding_gate_rows) != len(source_gate_rows):
                    errors.append(
                        f"{prefix}."
                        f"{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD} "
                        "must preserve the exact number of field bindings"
                    )
                rebound_gate_rows: list[dict[str, Any]] = []
                for gate_index, source_gate_row in enumerate(
                    source_gate_rows
                ):
                    gate_prefix = (
                        f"{prefix}."
                        f"{FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD}"
                        f"[{gate_index}]"
                    )
                    if not isinstance(source_gate_row, Mapping):
                        errors.append(
                            f"{gate_prefix} source binding must be an object"
                        )
                        continue
                    raw_gate_binding = (
                        binding_gate_rows[gate_index]
                        if gate_index < len(binding_gate_rows)
                        else {}
                    )
                    if not isinstance(raw_gate_binding, Mapping):
                        errors.append(f"{gate_prefix} must be an object")
                        raw_gate_binding = {}
                    gate_binding = dict(raw_gate_binding)
                    expected_gate_fields = {
                        "field",
                        "authority_kind",
                        *FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS,
                    }
                    extra_gate_fields = sorted(
                        set(gate_binding) - expected_gate_fields
                    )
                    if extra_gate_fields:
                        errors.append(
                            f"{gate_prefix} contains runtime-owned fields: "
                            f"{extra_gate_fields!r}"
                        )
                    missing_gate_fields = sorted(
                        expected_gate_fields - set(gate_binding)
                    )
                    if missing_gate_fields:
                        errors.append(
                            f"{gate_prefix} is missing required fields: "
                            f"{missing_gate_fields!r}"
                        )
                    for immutable_field in (
                        "field",
                        "authority_kind",
                    ):
                        if gate_binding.get(immutable_field) != (
                            source_gate_row.get(immutable_field)
                        ):
                            errors.append(
                                f"{gate_prefix}.{immutable_field} must "
                                "preserve the frozen value"
                            )
                    rebound_gate_row = dict(source_gate_row)
                    for mutable_field in (
                        FROZEN_METRIC_PROTOCOL_REBINDING_GATE_MUTABLE_FIELDS
                    ):
                        if mutable_field in gate_binding:
                            rebound_gate_row[mutable_field] = (
                                gate_binding[mutable_field]
                            )
                    rebound_gate_rows.append(rebound_gate_row)
                reconstructed[
                    FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
                ] = rebound_gate_rows
        reconstructed_rows.append(reconstructed)

    if observed_ids != source_ids:
        errors.append(
            "frozen metric rebinding output must preserve the exact ordered "
            f"requirement IDs: expected={source_ids!r} observed={observed_ids!r}"
        )
    return reconstructed_rows, errors


@dataclass(frozen=True)
class ArchitectMetricContractAuthoringConfig:
    max_tokens: int = 5000
    model_tier: str = "sonnet"
    provider_name: str = "anthropic"
    max_validation_retries: int = 1
    metric_semantic_reviewer_max_revisions: int = 1


def _metric_authoring_model_support_schema(
    *,
    authority_anchor_ids: list[str],
    include_value: bool,
) -> dict[str, Any]:
    required = ["source_anchors", "rationale"]
    properties: dict[str, Any] = {
        "source_anchors": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {
                "type": "string",
                "enum": list(authority_anchor_ids),
            },
        },
        "rationale": {"type": "string", "minLength": 1},
    }
    if include_value:
        required.insert(0, "value")
        properties = {"value": {"type": "number"}, **properties}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def _metric_authoring_model_requirement_schema(
    *,
    authority_anchor_ids: list[str],
) -> dict[str, Any]:
    """Return the compact model ACI; final evaluator fields are runtime mirrors."""

    predicate_authority = _metric_authoring_model_support_schema(
        authority_anchor_ids=authority_anchor_ids,
        include_value=False,
    )
    gate_authority = _metric_authoring_model_support_schema(
        authority_anchor_ids=authority_anchor_ids,
        include_value=True,
    )
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "requirement_id",
            "metric_semantics",
            "metric_value_kind",
            "measurement_protocol",
            "operator",
            "aggregation",
            "predicate_authority",
            "gate_fields",
        ],
        "properties": {
            "requirement_id": {"type": "string", "minLength": 1},
            "metric_semantics": {"type": "string", "minLength": 1},
            "metric_value_kind": {
                "type": "string",
                "enum": list(GENERATED_METRIC_VALUE_KINDS),
                "description": (
                    "Use numeric for a measured scalar and boolean only for an "
                    "intrinsically boolean predicate. Boolean rows use operator == "
                    "and omit threshold/tolerance gate_fields because the runtime "
                    "materializes the canonical truth comparison."
                ),
            },
            "measurement_protocol": {"type": "string", "minLength": 1},
            "operator": {
                "type": "string",
                "enum": list(GENERATED_METRIC_CONTRACT_OPERATORS),
                "description": (
                    "Boolean rows must use ==. Numeric rows use the comparison "
                    "authorized by their cited acceptance source."
                ),
            },
            "aggregation": {
                "type": "string",
                "enum": list(GENERATED_METRIC_CONTRACT_AGGREGATIONS),
                "description": (
                    "identity/mean/min/max/all/any have no quorum gate field. "
                    "at_least_count requires only minimum_pass_count; "
                    "at_least_fraction requires only minimum_pass_fraction. "
                    "In particular, all already means every comparison passes, "
                    "so never add minimum_pass_count or minimum_pass_fraction to all."
                ),
            },
            "predicate_authority": predicate_authority,
            "gate_fields": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    field: deepcopy(gate_authority)
                    for field in GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS
                },
                "description": (
                    "Key each active substantive model-authored number exactly once "
                    "by evaluator field name. Numeric rows include threshold, or "
                    "lower then upper for between, plus any active tolerance/quorum "
                    "field. Boolean rows omit threshold and tolerance; the runtime "
                    "materializes == 1 with zero tolerance. all and any never take a "
                    "quorum field; only at_least_count takes minimum_pass_count and "
                    "only at_least_fraction takes minimum_pass_fraction."
                ),
            },
        },
    }


def _metric_authoring_model_requirement_prompt_schema() -> dict[str, Any]:
    return {
        "requirement_id": "stable unique acceptance-gate id",
        "metric_semantics": "one independently compared returned quantity",
        "metric_value_kind": (
            "numeric, or boolean only for an intrinsic predicate; boolean uses "
            "operator == and no threshold/tolerance gate_fields"
        ),
        "measurement_protocol": "exact pre-execution measurement procedure",
        "operator": "<=|<|>=|>|==|between",
        "aggregation": (
            "identity|mean|min|max|all|any|at_least_count|at_least_fraction; "
            "all/any have no quorum field, at_least_count alone uses "
            "minimum_pass_count, and at_least_fraction alone uses "
            "minimum_pass_fraction"
        ),
        "predicate_authority": {
            "source_anchors": ["exact acceptance_authority_catalog anchor_id"],
            "rationale": "why the cited context supports this predicate",
        },
        "gate_fields": {
            "<unique field key: threshold|lower|upper|tolerance|"
            "minimum_pass_count|minimum_pass_fraction>": {
                "value": "the substantive numeric value, stated exactly once",
                "source_anchors": [
                    "field-specific exact acceptance_authority_catalog anchor_id; "
                    "predicate_authority anchors are inherited automatically"
                ],
                "rationale": "field-specific pre-execution justification",
            }
        },
    }


def _materialize_metric_authoring_model_requirement(
    value: Mapping[str, Any],
    *,
    requirement_index: int,
) -> tuple[dict[str, Any], list[str]]:
    """Expand one compact model row without selecting any model-owned semantics."""

    row = dict(value)
    prefix = f"empirical_metric_requirements[{requirement_index}]"
    errors: list[str] = []
    predicate_authority = row.get("predicate_authority", {})
    if not isinstance(predicate_authority, Mapping):
        predicate_authority = {}
        errors.append(f"{prefix}.predicate_authority must be an object")
    predicate_anchors = [
        str(anchor).strip()
        for anchor in predicate_authority.get("source_anchors", []) or []
        if str(anchor).strip()
    ]
    gate_rows = row.get("gate_fields", {})
    if not isinstance(gate_rows, Mapping):
        gate_rows = {}
        errors.append(f"{prefix}.gate_fields must be an object")
    unknown_gate_fields = sorted(
        str(field)
        for field in gate_rows
        if field not in GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS
    )
    if unknown_gate_fields:
        errors.append(
            f"{prefix}.gate_fields contains unsupported fields "
            f"{unknown_gate_fields!r}"
        )

    requirement: dict[str, Any] = {
        "requirement_id": str(row.get("requirement_id", "") or "").strip(),
        "target_subsystems": ["SimulationEngineer"],
        "metric_semantics": str(row.get("metric_semantics", "") or "").strip(),
        "metric_value_kind": str(
            row.get("metric_value_kind", "") or ""
        ).strip(),
        "measurement_protocol": str(
            row.get("measurement_protocol", "") or ""
        ).strip(),
        "operator": str(row.get("operator", "") or "").strip(),
        "threshold": None,
        "lower": None,
        "upper": None,
        "tolerance": 0.0,
        "aggregation": str(row.get("aggregation", "") or "").strip(),
        "minimum_pass_count": None,
        "minimum_pass_fraction": None,
        "required": True,
        "source_anchors": list(dict.fromkeys(predicate_anchors)),
        "acceptance_authority_kind": FRESH_METRIC_AUTHORING_AUTHORITY_KIND,
        "acceptance_authority_rationale": str(
            predicate_authority.get("rationale", "") or ""
        ).strip(),
        "gate_field_authorities": [],
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }
    if requirement["metric_value_kind"] == "boolean":
        requirement["threshold"] = 1

    observed_fields: list[str] = []
    field_rationales: list[tuple[str, str]] = []
    for field in GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS:
        if field not in gate_rows:
            continue
        raw_gate = gate_rows[field]
        gate_prefix = f"{prefix}.gate_fields.{field}"
        if not isinstance(raw_gate, Mapping):
            errors.append(f"{gate_prefix} must be an object")
            continue
        gate = dict(raw_gate)
        observed_fields.append(field)
        numeric_value = gate.get("value")
        if (
            isinstance(numeric_value, bool)
            or not isinstance(numeric_value, (int, float))
            or not math.isfinite(float(numeric_value))
        ):
            errors.append(f"{gate_prefix}.value must be a finite number")
            continue
        requirement[field] = numeric_value
        gate_anchors = [
            str(anchor).strip()
            for anchor in gate.get("source_anchors", []) or []
            if str(anchor).strip()
        ]
        rationale = str(gate.get("rationale", "") or "").strip()
        requirement["gate_field_authorities"].append(
            {
                "field": field,
                "authority_kind": FRESH_METRIC_AUTHORING_AUTHORITY_KIND,
                "source_anchors": list(
                    dict.fromkeys([*predicate_anchors, *gate_anchors])
                ),
                "rationale": rationale,
            }
        )
        requirement["source_anchors"] = list(
            dict.fromkeys([*requirement["source_anchors"], *gate_anchors])
        )
        if rationale:
            field_rationales.append((field, rationale))

    expected_fields: list[str]
    if requirement["metric_value_kind"] == "boolean":
        expected_fields = []
        if requirement["operator"] != "==":
            errors.append(f"{prefix}.boolean metric requires operator ==")
        runtime_truth_fields = [
            field
            for field in observed_fields
            if field in {"threshold", "tolerance"}
        ]
        if runtime_truth_fields:
            errors.append(
                f"{prefix}.boolean metric gate_fields must omit runtime-owned "
                f"truth fields {runtime_truth_fields!r}; use operator == and let "
                "AgentRuntime materialize threshold=1 and tolerance=0"
            )
    elif requirement["operator"] == "between":
        expected_fields = ["lower", "upper"]
    else:
        expected_fields = ["threshold"]
    if (
        requirement["metric_value_kind"] != "boolean"
        and "tolerance" in observed_fields
    ):
        expected_fields.append("tolerance")
    if requirement["aggregation"] == "at_least_count":
        expected_fields.append("minimum_pass_count")
    elif requirement["aggregation"] == "at_least_fraction":
        expected_fields.append("minimum_pass_fraction")
    if set(observed_fields) != set(expected_fields):
        errors.append(
            f"{prefix}.gate_fields must contain exactly the active evaluator fields: "
            f"expected={expected_fields!r} observed={observed_fields!r}"
        )
    if field_rationales:
        predicate_rationale = requirement["acceptance_authority_rationale"]
        requirement["acceptance_authority_rationale"] = "; ".join(
            [
                *([f"predicate: {predicate_rationale}"] if predicate_rationale else []),
                *(f"{field}: {rationale}" for field, rationale in field_rationales),
            ]
        )
    return materialize_generated_metric_gate_field_authorities(requirement), errors


def _compact_metric_authoring_prompt_payload(
    value: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remove duplicated trees while preserving every authority leaf verbatim."""

    payload = deepcopy(dict(value))
    original_chars = len(
        json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
    )
    if original_chars <= _METRIC_AUTHORING_LARGE_PROMPT_CHARS:
        return payload, {
            "applied": False,
            "original_chars": original_chars,
            "projected_chars": original_chars,
            "authority_catalog_rows": len(
                payload.get("acceptance_authority_catalog", []) or []
            ),
        }

    raw_catalog = payload.get("acceptance_authority_catalog", [])
    catalog_rows = [
        [
            str(row.get("anchor_id", "") or ""),
            str(row.get("authority_kind", "") or ""),
            deepcopy(row.get("content")),
            deepcopy(row.get("explicit_numeric_values", [])),
        ]
        for row in raw_catalog
        if isinstance(row, Mapping)
    ]
    payload["acceptance_authority_catalog"] = {
        "transport": "lossless_columnar_authority_leaves_v1",
        "columns": [
            "anchor_id",
            "authority_kind",
            "content",
            "explicit_numeric_values",
        ],
        "rows": catalog_rows,
        "row_count": len(catalog_rows),
        "citation_rule": (
            "source_anchors must copy exact anchor_id cells from these rows"
        ),
    }

    raw_theory = payload.get("theory_developer_protocol_material", {})
    theory = dict(raw_theory) if isinstance(raw_theory, Mapping) else {}
    semantic_material = theory.get("theory_semantic_material", {})
    semantic_material = (
        dict(semantic_material)
        if isinstance(semantic_material, Mapping)
        else {}
    )
    payload["theory_developer_protocol_material"] = {
        field: deepcopy(theory.get(field))
        for field in (
            "artifact_kind",
            "source_theory_packet_id",
            "source_theory_packet_hash",
            "execution_results_available",
            "proof_evidence_status",
            "boundary",
        )
        if field in theory
    }
    non_authority_review_context = {
        field: deepcopy(semantic_material.get(field))
        for field in (
            "critic_findings",
            "proof_evidence_boundary",
        )
        if semantic_material.get(field) not in (None, "", [], {})
    }
    derivation = semantic_material.get("theory_derivation_packet", {})
    if isinstance(derivation, Mapping) and derivation.get("self_critique"):
        non_authority_review_context["theory_self_critique"] = deepcopy(
            derivation["self_critique"]
        )
    simulation_design = semantic_material.get("simulation_ademp_spec", {})
    if isinstance(simulation_design, Mapping):
        projected_design_context = {
            field: deepcopy(simulation_design[field])
            for field in (
                "aim",
                "performance_measures",
                "expected_theoretical_behavior",
            )
            if simulation_design.get(field) not in (None, "", [], {})
        }
        if projected_design_context:
            non_authority_review_context["simulation_design_context"] = (
                projected_design_context
            )
    payload["theory_developer_protocol_material"].update(
        {
            "semantic_transport": (
                "authority-bearing semantic nodes are preserved in the catalog"
            ),
            "non_authority_review_context": non_authority_review_context,
        }
    )
    payload["accepted_implementation_interface_handoff"] = (
        _metric_authoring_interface_prompt_projection(
            payload.get("accepted_implementation_interface_handoff", {})
        )
    )

    requirement_schema = payload.get("requirement_schema", {})
    required_fields = (
        sorted(str(field) for field in requirement_schema)
        if isinstance(requirement_schema, Mapping)
        else []
    )
    payload["requirement_schema"] = {
        "transport": "provider_native_structured_output_schema",
        "required_fields": required_fields,
        "runtime_validator_unchanged": True,
    }
    required_target_subsystems = list(
        dict.fromkeys(
            str(target)
            for row in payload.get("required_target_rows", []) or []
            if isinstance(row, Mapping)
            for target in row.get("target_subsystems", []) or []
            if str(target).strip()
        )
    )
    payload["required_target_rows"] = [
        {
            "target_subsystems": (
                required_target_subsystems
                or list(GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS)
            ),
            "at_least_one_required_row_per_target": True,
        }
    ]
    payload["prompt_projection"] = {
        "transport": "large_metric_authoring_context_v1",
        "duplicated_theory_tree_omitted": True,
        "authority_leaf_content_lossless": True,
        "provider_output_schema_bound_out_of_band": True,
        "original_chars": original_chars,
        "projected_chars": 0,
    }
    projected_chars = len(
        json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
    )
    payload["prompt_projection"]["projected_chars"] = projected_chars
    return payload, {
        "applied": True,
        "original_chars": original_chars,
        "projected_chars": projected_chars,
        "authority_catalog_rows": len(catalog_rows),
    }


def _metric_authoring_interface_prompt_projection(value: Any) -> dict[str, Any]:
    """Keep exact interface identity and callable semantics without rate metadata."""

    if not isinstance(value, Mapping):
        return {}
    projected = {
        field: deepcopy(value[field])
        for field in (
            "artifact_kind",
            "question_id",
            "theory_packet_id",
            "handoff_id",
            "exact_source_included",
            "execution_results_included",
            "runtime_selected_semantics",
            "proof_evidence_status",
        )
        if field in value
    }
    interfaces: list[dict[str, Any]] = []
    for raw_interface in value.get("implementation_interfaces", []) or []:
        if not isinstance(raw_interface, Mapping):
            continue
        contract = raw_interface.get("estimator_interface_contract", {})
        contract = contract if isinstance(contract, Mapping) else {}
        interfaces.append(
            {
                field: deepcopy(raw_interface[field])
                for field in (
                    "estimator_id",
                    "language",
                    "exact_source_hash",
                    "estimator_interface_contract_id",
                )
                if field in raw_interface
            }
            | {
                "request_fields": [
                    {
                        field: deepcopy(row[field])
                        for field in ("name", "meaning", "binding")
                        if field in row
                    }
                    for row in contract.get("request_fields", []) or []
                    if isinstance(row, Mapping)
                ],
                "response_fields": [
                    {
                        field: deepcopy(row[field])
                        for field in (
                            "name",
                            "meaning",
                            "normalization",
                            "derivation_ref",
                        )
                        if field in row
                    }
                    for row in contract.get("response_fields", []) or []
                    if isinstance(row, Mapping)
                ],
            }
        )
    projected["implementation_interfaces"] = interfaces
    return projected


def _confirmatory_metric_requirement_rows(
    requirements: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = [
        dict(row)
        for row in requirements or []
        if isinstance(row, Mapping)
    ]
    kept: list[dict[str, Any]] = []
    omitted: list[dict[str, str]] = []
    for row in rows:
        if row.get("required") is True:
            kept.append(row)
            continue
        omitted.append(
            {
                "requirement_id": str(row.get("requirement_id", "") or ""),
                "reason": "nonrequired_row_is_simulation_telemetry_not_acceptance",
            }
        )
    return kept, omitted


def build_architect_upstream_research_contract(
    runtime_contract: Mapping[str, Any],
) -> dict[str, Any]:
    def upstream_target_rows(field: str) -> list[Any]:
        value = runtime_contract.get(field, [])
        values = value if isinstance(value, (list, tuple)) else [value]
        return [
            deepcopy(row)
            for row in values
            if row not in (None, "", [], {})
        ]

    contract = {
        "formal_targets": upstream_target_rows("formal_targets"),
        "simulation_targets": upstream_target_rows("simulation_targets"),
        "source": "architect_runtime_plan.evidence_contract",
        "proof_evidence_status": (
            "ARCHITECT_UPSTREAM_RESEARCH_CONTRACT_NOT_PROOF_EVIDENCE"
        ),
        "boundary": (
            "These Architect-authored targets define the requested research scope "
            "for independent alignment review. They are proposals, not theorem "
            "proof, implementation, or simulation evidence."
        ),
    }
    contract["contract_fingerprint"] = stable_hash(contract)
    return contract


def _theory_protocol_material_errors(
    theory_material: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if theory_material.get("artifact_kind") != (
        "RuntimeTheoryInformedMetricProtocolMaterial"
    ):
        errors.append("theory protocol material kind mismatch")
    if theory_material.get("execution_results_available") is not False:
        errors.append("theory protocol material must be pre-execution")
    if not str(
        theory_material.get("source_theory_packet_id", "") or ""
    ).strip():
        errors.append("theory protocol material missing source theory packet")
    semantic_material = theory_material.get("theory_semantic_material", {})
    if not isinstance(semantic_material, Mapping) or not semantic_material:
        errors.append("theory protocol material missing semantic handoff")
    return errors


def review_architect_theory_execution_preflight(
    *,
    semantic_reviewer: LLMArchitectMetricSemanticReviewerAgent | None,
    question: OpenResearchQuestion,
    runtime_contract: Mapping[str, Any],
    theory_protocol_material: Mapping[str, Any],
    prior_rejection_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run only the independent source-grounded theory/executability gate."""

    if semantic_reviewer is None:
        raise ValueError(
            "theory execution preflight requires an independent semantic reviewer"
        )
    theory_material = dict(theory_protocol_material)
    material_errors = _theory_protocol_material_errors(theory_material)
    if material_errors:
        raise ValueError("; ".join(material_errors))
    prior_rejection = (
        dict(prior_rejection_context)
        if isinstance(prior_rejection_context, Mapping)
        else {}
    )
    prior_finding_ledger: list[dict[str, Any]] = []
    if (
        str(prior_rejection.get("current_source_theory_packet_id", "") or "")
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(
            prior_rejection.get("current_source_theory_packet_hash", "") or ""
        )
        == str(theory_material.get("source_theory_packet_hash", "") or "")
    ):
        prior_finding_ledger = [
            dict(row)
            for row in prior_rejection.get("cumulative_finding_ledger", []) or []
            if isinstance(row, Mapping)
        ]
        if not prior_finding_ledger:
            prior_finding_ledger = (
                metric_protocol_finding_ledger_from_review_history(
                    question_id=question.id,
                    semantic_review_history=prior_rejection.get(
                        "semantic_review_history", []
                    ),
                )
            )
    preflight = getattr(
        semantic_reviewer,
        "review_theory_execution_preflight",
        None,
    )
    if not callable(preflight):
        raise ValueError(
            "semantic reviewer does not support theory execution preflight"
        )
    with agent_runtime_substage(
        "architect_theory_execution_preflight",
        metadata={
            "model_tier": str(
                getattr(
                    getattr(semantic_reviewer, "config", None),
                    "model_tier",
                    "",
                )
                or ""
            ),
            "source_theory_packet_id": str(
                theory_material.get("source_theory_packet_id", "") or ""
            ),
            "execution_results_available": False,
            "full_metric_authoring_deferred": True,
        },
    ):
        packet = preflight(
            question=question,
            theory_protocol_material=theory_material,
            upstream_research_contract=(
                build_architect_upstream_research_contract(runtime_contract)
            ),
            prior_finding_ledger=prior_finding_ledger,
        )
    if packet.get("overall_verdict") == "ACCEPT":
        return dict(packet)

    packet_hash = stable_hash(packet)
    raise ArchitectMetricSemanticReviewRejected(
        question_id=question.id,
        semantic_review_history=[
            {
                "revision_index": 0,
                "review_stage": "theory_execution_preflight",
                "authoring_packet_id": "",
                "authoring_packet_hash": "",
                "empirical_metric_requirement_set_id": "",
                "source_theory_packet_id": str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
                "source_theory_packet_hash": str(
                    theory_material.get("source_theory_packet_hash", "") or ""
                ),
                "semantic_review_packet_id": str(
                    packet.get("packet_id", "") or ""
                ),
                "semantic_review_packet_hash": packet_hash,
                "semantic_review_model": str(packet.get("model", "") or ""),
                "semantic_review_model_tier": str(
                    packet.get("model_tier", "") or ""
                ),
                "independent_agent": bool(packet.get("independent_agent")),
                "independent_invocation": bool(
                    packet.get("independent_invocation")
                ),
                "overall_verdict": "REVISE",
                "dimension_reviews": [
                    dict(row)
                    for row in packet.get("dimension_reviews", []) or []
                    if isinstance(row, Mapping)
                ],
                "estimator_execution_checks": [
                    dict(row)
                    for row in packet.get("estimator_execution_checks", []) or []
                    if isinstance(row, Mapping)
                ],
                "prior_finding_reviews": [
                    dict(row)
                    for row in packet.get("prior_finding_reviews", []) or []
                    if isinstance(row, Mapping)
                ],
                "cumulative_finding_ledger": [
                    dict(row)
                    for row in packet.get("cumulative_finding_ledger", []) or []
                    if isinstance(row, Mapping)
                ],
                "cumulative_finding_ledger_fingerprint": str(
                    packet.get("cumulative_finding_ledger_fingerprint", "") or ""
                ),
                "active_unresolved_finding_ids": [
                    str(value)
                    for value in packet.get("active_unresolved_finding_ids", []) or []
                    if str(value).strip()
                ],
                "prior_finding_resolution_summary": deepcopy(
                    packet.get("prior_finding_resolution_summary", {})
                ),
                "theory_execution_preflight_packet": deepcopy(packet),
                "findings": [
                    dict(row)
                    for row in packet.get("findings", []) or []
                    if isinstance(row, Mapping)
                ],
                "execution_authorized": False,
                "proof_evidence_status": str(
                    packet.get("proof_evidence_status", "") or ""
                ),
            }
        ],
        source_theory_packet_id=str(
            theory_material.get("source_theory_packet_id", "") or ""
        ),
        source_theory_packet_hash=str(
            theory_material.get("source_theory_packet_hash", "") or ""
        ),
    )


def _accepted_theory_preflight_packet(
    context: Mapping[str, Any] | None,
    *,
    theory_material: Mapping[str, Any],
) -> dict[str, Any]:
    accepted = dict(context) if isinstance(context, Mapping) else {}
    packet = accepted.get("theory_execution_preflight_packet", {})
    packet = dict(packet) if isinstance(packet, Mapping) else {}
    if not accepted:
        return {}
    acceptance_identity_payload = dict(accepted)
    acceptance_identity_payload.pop("acceptance_id", None)
    expected_acceptance_id = (
        "architect_theory_execution_preflight_acceptance:"
        + stable_hash(acceptance_identity_payload)[:20]
    )
    valid = bool(
        accepted.get("artifact_kind")
        == "RuntimeArchitectTheoryExecutionPreflightAcceptance"
        and str(accepted.get("acceptance_id", "") or "")
        == expected_acceptance_id
        and accepted.get("execution_results_observed") is False
        and accepted.get("full_metric_authoring_completed") is False
        and str(accepted.get("source_theory_packet_id", "") or "")
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(accepted.get("source_theory_packet_hash", "") or "")
        == str(theory_material.get("source_theory_packet_hash", "") or "")
        and packet.get("overall_verdict") == "ACCEPT"
        and str(accepted.get("preflight_packet_id", "") or "")
        == str(packet.get("packet_id", "") or "")
        and str(accepted.get("preflight_packet_hash", "") or "")
        == stable_hash(packet)
    )
    if not valid:
        raise ValueError(
            "accepted theory preflight context is missing, stale, or hash-inconsistent"
        )
    return packet


def author_reviewed_architect_metric_requirements(
    *,
    provider: GeneratorBackend,
    config: ArchitectMetricContractAuthoringConfig,
    request_model: str,
    semantic_reviewer: LLMArchitectMetricSemanticReviewerAgent | None,
    question: OpenResearchQuestion,
    runtime_contract: Mapping[str, Any],
    theory_protocol_material: Mapping[str, Any] | None = None,
    prior_rejection_context: Mapping[str, Any] | None = None,
    frozen_requirement_rebinding_context: Mapping[str, Any] | None = None,
    accepted_theory_preflight_context: Mapping[str, Any] | None = None,
    accepted_implementation_interface_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if (
        runtime_contract.get("research_evaluation_requires_typed_metric_contracts")
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
    theory_material_errors = _theory_protocol_material_errors(theory_material)
    if theory_material_errors:
        raise ValueError(
            "theory-informed metric authoring requires a structured, pre-execution "
            "TheoryDeveloper semantic handoff: "
            + "; ".join(theory_material_errors)
        )
    implementation_interface = (
        dict(accepted_implementation_interface_context)
        if isinstance(accepted_implementation_interface_context, Mapping)
        else {}
    )
    if implementation_interface:
        implementation_errors = (
            accepted_implementation_interface_handoff_errors(
                implementation_interface,
                question_id=question.id,
                theory_packet_id=str(
                    theory_material.get("source_theory_packet_id", "") or ""
                ),
            )
        )
        if implementation_errors:
            raise ValueError("; ".join(implementation_errors))
    frozen_rebinding = (
        dict(frozen_requirement_rebinding_context)
        if isinstance(frozen_requirement_rebinding_context, Mapping)
        else {}
    )
    if frozen_rebinding and not (
        frozen_rebinding.get("artifact_kind")
        == "RuntimeFrozenMetricProtocolTheoryRebindingContext"
        and frozen_rebinding.get("raw_execution_artifacts_included") is False
        and frozen_rebinding.get("post_result_gate_changes_allowed") is False
        and str(
            frozen_rebinding.get("source_requirement_set_id", "") or ""
        ).strip()
        and isinstance(
            frozen_rebinding.get("source_requirement_rows"), list
        )
        and frozen_rebinding.get("source_requirement_rows")
        and str(
            frozen_rebinding.get("current_source_theory_packet_id", "") or ""
        )
        == str(theory_material.get("source_theory_packet_id", "") or "")
        and str(
            frozen_rebinding.get("current_source_theory_packet_hash", "") or ""
        )
        == str(theory_material.get("source_theory_packet_hash", "") or "")
        and set(
            frozen_rebinding.get(
                "allowed_mutable_requirement_fields", []
            )
            or []
        )
        == _frozen_metric_protocol_rebinding_mutable_fields(
            frozen_rebinding.get("source_requirement_rows", [])
        )
    ):
        raise ValueError(
            "frozen metric protocol rebinding requires sanitized, theory-bound "
            "lineage with exact immutable gate rows"
        )

    runtime_replicates = int(
        runtime_contract.get("generated_sandbox_runtime_replicates", 0) or 0
    )
    confirmatory_required_rows_only = True
    question_material = {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": list(question.tags),
    }
    upstream_research_contract = build_architect_upstream_research_contract(
        runtime_contract
    )
    theory_execution_preflight_packet = (
        _accepted_theory_preflight_packet(
            accepted_theory_preflight_context,
            theory_material=theory_material,
        )
        if accepted_theory_preflight_context
        else review_architect_theory_execution_preflight(
            semantic_reviewer=semantic_reviewer,
            question=question,
            runtime_contract=runtime_contract,
            theory_protocol_material=theory_material,
            prior_rejection_context=prior_rejection_context,
        )
    )
    acceptance_authority_catalog = generated_metric_acceptance_authority_catalog(
        question=question_material,
        runtime_contract=runtime_contract,
        theory_protocol_material=theory_material,
    )
    acceptance_authority_prompt_catalog = (
        generated_metric_acceptance_authority_prompt_catalog(
            acceptance_authority_catalog
        )
    )
    if confirmatory_required_rows_only:
        acceptance_authority_prompt_catalog = [
            row
            for row in acceptance_authority_prompt_catalog
            if row.get("authority_kind") != "diagnostic_only"
        ]
    acceptance_authority_anchor_ids = [
        str(row["anchor_id"])
        for row in acceptance_authority_prompt_catalog
        if str(row.get("anchor_id", "") or "").strip()
    ]
    acceptance_authority_catalog_id = (
        "generated_metric_acceptance_authority_catalog:"
        + stable_hash(acceptance_authority_catalog)[:20]
    )
    response_requirement_schema = generated_metric_requirement_json_schema(
        require_acceptance_authority=True,
        authority_anchor_ids=acceptance_authority_anchor_ids,
        require_gate_field_authorities=True,
    )
    response_requirement_schema["required"] = [
        field
        for field in response_requirement_schema.get("required", [])
        if field
        not in {
            "required_runtime_replicates",
            "gate_field_authority_mode",
        }
    ]
    for runtime_owned_field in (
        "required_runtime_replicates",
        "gate_field_authority_mode",
    ):
        response_requirement_schema.get("properties", {}).pop(
            runtime_owned_field,
            None,
        )
    if frozen_rebinding:
        frozen_source_rows = [
            dict(row)
            for row in frozen_rebinding.get(
                "source_requirement_rows", []
            )
            if isinstance(row, Mapping)
        ]
        source_requirement_ids = [
            str(row.get("requirement_id", "") or "")
            for row in frozen_source_rows
        ]
        frozen_field_bound = any(
            FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in row
            for row in frozen_source_rows
        )
        all_frozen_rows_field_bound = bool(frozen_source_rows) and all(
            FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD in row
            for row in frozen_source_rows
        )
        frozen_required_fields = [
            "requirement_id",
            "source_anchors",
            "acceptance_authority_rationale",
        ]
        if all_frozen_rows_field_bound:
            frozen_required_fields.append(
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            )
        frozen_properties: dict[str, Any] = {
            "requirement_id": {
                "type": "string",
                "enum": source_requirement_ids,
            },
            "source_anchors": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "string",
                    "enum": acceptance_authority_anchor_ids,
                },
            },
            "acceptance_authority_rationale": {
                "type": "string",
                "minLength": 1,
            },
        }
        if frozen_field_bound:
            frozen_properties[
                FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            ] = {
                "type": "array",
                "maxItems": len(
                    GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS
                ),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "field",
                        "authority_kind",
                        "source_anchors",
                        "rationale",
                    ],
                    "properties": {
                        "field": {
                            "type": "string",
                            "enum": list(
                                GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS
                            ),
                        },
                        "authority_kind": {
                            "type": "string",
                            "enum": list(
                                GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS
                            ),
                        },
                        "source_anchors": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "string",
                                "enum": acceptance_authority_anchor_ids,
                            },
                        },
                        "rationale": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
            }
        response_requirement_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": frozen_required_fields,
            "properties": frozen_properties,
        }
    else:
        response_requirement_schema = (
            _metric_authoring_model_requirement_schema(
                authority_anchor_ids=acceptance_authority_anchor_ids,
            )
        )
    response_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["empirical_metric_requirements"],
        "properties": {
            "empirical_metric_requirements": {
                "type": "array",
                "minItems": 1,
                "maxItems": MAX_CONFIRMATORY_METRIC_REQUIREMENTS,
                "items": response_requirement_schema,
            }
        },
    }
    if frozen_rebinding:
        frozen_row_count = len(
            frozen_rebinding.get("source_requirement_rows", []) or []
        )
        response_schema["properties"]["empirical_metric_requirements"].update(
            {
                "minItems": frozen_row_count,
                "maxItems": frozen_row_count,
            }
        )
    requirement_prompt_schema = (
        generated_metric_requirement_prompt_schema()
        if frozen_rebinding
        else _metric_authoring_model_requirement_prompt_schema()
    )
    requirement_prompt_schema.pop("required_runtime_replicates", None)
    required_target_rows = (
        []
        if frozen_rebinding
        else [
            {
                "target_subsystems": list(
                    GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                ),
                "runtime_bound": True,
                "at_least_one_required_acceptance_gate": True,
            }
        ]
    )
    prompt_payload = {
        "task": (
            "Rebind the exact frozen empirical acceptance requirements to the "
            "current revised theory without changing any gate semantics."
            if frozen_rebinding
            else "Author the pre-execution empirical acceptance requirements used "
            "by the AI Statistician confirmatory simulation agent."
        ),
        "question": question_material,
        "upstream_research_contract": upstream_research_contract,
        "theory_developer_protocol_material": theory_material,
        "accepted_implementation_interface_handoff": (
            implementation_interface
        ),
        "acceptance_authority_catalog_id": acceptance_authority_catalog_id,
        "acceptance_authority_catalog": acceptance_authority_prompt_catalog,
        "runtime_owned_replicates": runtime_replicates,
        "confirmatory_portfolio_row_budget": (
            MAX_CONFIRMATORY_METRIC_REQUIREMENTS
        ),
        "confirmatory_required_rows_only": confirmatory_required_rows_only,
        "runtime_owned_field_bindings": {
            "target_subsystems": {
                "source": "generated_metric_target_namespace",
                "value": list(GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS),
                "model_authored": False,
                "binding_stage": "before_hash_validation_and_review",
            },
            "required": {
                "source": "confirmatory_acceptance_portfolio",
                "value": True,
                "model_authored": False,
                "binding_stage": "before_hash_validation_and_review",
            },
            "required_runtime_replicates": {
                "source": (
                    "runtime_contract.generated_sandbox_runtime_replicates"
                ),
                "value": runtime_replicates,
                "model_authored": False,
                "binding_stage": "before_hash_validation_and_review",
            },
            "acceptance_authority_kind": {
                "source": "preexecution_architect_authorship",
                "value": FRESH_METRIC_AUTHORING_AUTHORITY_KIND,
                "model_authored": False,
                "binding_stage": "before_hash_validation_and_review",
            },
            "gate_field_authority_mode": {
                "source": "runtime_field_authority_abi",
                "model_authored": False,
                "binding_stage": "before_hash_validation_and_review",
            },
            "flat_gate_values_and_authorities": {
                "source": "model_gate_fields",
                "model_authored_once": True,
                "runtime_expands_evaluator_abi": True,
                "runtime_selected_semantics": False,
                "binding_stage": "before_hash_validation_and_review",
            },
            "source_anchors": {
                "source": (
                    "model_semantic_context_plus_gate_field_anchor_union"
                ),
                "model_authored": True,
                "runtime_augmented": True,
                "binding_stage": "before_hash_validation_and_review",
            },
        },
        "target_namespace": generated_metric_requirement_target_namespace_contract(),
        "metric_evaluation_semantics": (
            generated_metric_evaluation_semantics_contract()
        ),
        "requirement_schema": requirement_prompt_schema,
        "required_target_rows": required_target_rows,
        "hard_requirements": [
            (
                "Return the smallest nonredundant pre-execution acceptance portfolio "
                "that covers the requested generated empirical-evaluation subsystem. "
                "Each row must govern one independently comparable returned quantity. "
                "Represent repeated DGP, sample-size, or stress scenarios as one "
                "returned vector with an explicit aggregation instead of creating one "
                "required row per scenario. The row budget is an execution/review "
                "budget, not a statistical threshold."
            ),
            (
                "Author the complete measurement semantics, operator, aggregation, "
                "active gate_fields, numeric values, source anchors, and rationales. "
                "gate_fields is an object keyed by each unique active evaluator "
                "field, so do not repeat the field name inside its value. For numeric "
                "rows, it contains the active comparison and "
                "optional quorum numbers. For intrinsically boolean rows, use "
                "operator == and omit threshold/tolerance gate_fields; AgentRuntime "
                "materializes the canonical == 1 truth comparison with zero "
                "tolerance. aggregation=all or any has no quorum gate field; all "
                "already requires every elementwise comparison to pass. Only "
                "at_least_count may emit minimum_pass_count and only "
                "at_least_fraction may emit minimum_pass_fraction. AgentRuntime only "
                "expands those choices into the "
                "evaluator ABI; it does not select their statistical semantics."
            ),
            (
                "Keep every gate in the same numeric coordinates as the declared "
                "returned metric. AgentRuntime applies the operator and active numeric "
                "gate fields directly to that returned metric after the declared "
                "aggregation; it does not implicitly subtract a target, center, take "
                "an absolute value, or normalize. If the intended predicate is a "
                "deviation from a target, either declare and return that deviation (or "
                "absolute deviation) or place absolute bounds around the target. Never "
                "pair a raw level with bounds expressed only as offsets from an "
                "unstated target."
            ),
            (
                "Copy every source anchor exactly from acceptance_authority_catalog. "
                "Use those anchors to identify the statistical context supporting each "
                "predicate and numeric choice. Fresh rows are recorded by AgentRuntime "
                "as architect_preregistered_design because this Architect authors and "
                "freezes them before execution; do not emit provenance labels yourself. "
                "Diagnostic-only material is excluded because this packet contains "
                "required confirmatory rows only."
            ),
            (
                "When a necessary finite-sample decision is not fixed upstream, the "
                "Architect may preregister it as architect_preregistered_design and "
                "must justify it from decision relevance, attainable behavior, the "
                "fixed runtime budget, and Monte Carlo uncertainty. "
                "Every stochastic gate must measure the target statistic at the declared "
                "transformation and aggregation, with a tolerance attainable under its "
                "replicate budget, uncertainty, and tail behavior. Compute the joint "
                "acceptance behavior of the whole required portfolio, including dependence, "
                "multiplicity, aggregation, and the probability of accepting a valid "
                "candidate under the fixed budget. A DGP assumption imposed by construction "
                "should be audited from that construction unless the objective explicitly "
                "asks for a calibrated empirical diagnostic. An analytic identity need not "
                "be a finite-run equality gate."
            ),
            (
                "Use theory_developer_protocol_material for the estimand, DGP, method, "
                "assumptions, and guarantees. The accepted implementation handoff is "
                "only an invocation/output ABI and supplies no statistical authority."
            ),
            (
                "Follow requirement_schema and metric_evaluation_semantics exactly. "
                "Return raw numeric measurements when available; use a boolean metric "
                "only for an intrinsically boolean predicate."
            ),
            (
                "Do not emit runtime-owned fields, diagnostics that cannot affect the "
                "acceptance decision, execution claims, or unsupported thresholds."
            ),
            (
                "The candidate is frozen before confirmatory execution and is empirical "
                "control evidence only, never theorem or kernel-proof evidence."
            ),
        ],
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }
    if frozen_rebinding:
        frozen_rebinding_includes_field_authorities = (
            FROZEN_METRIC_PROTOCOL_REBINDING_GATE_FIELD
            in _frozen_metric_protocol_rebinding_mutable_fields(
                frozen_rebinding.get("source_requirement_rows", [])
            )
        )
        prompt_payload["frozen_metric_protocol_theory_rebinding"] = (
            frozen_rebinding
        )
        prompt_payload["hard_requirements"] = [
            (
                "Return the exact same ordered requirement_id values from "
                "frozen_metric_protocol_theory_rebinding.source_requirement_rows. "
                "Each output row must contain only requirement_id, source_anchors, "
                "and acceptance_authority_rationale"
                + (
                    ", plus gate_field_authorities for field-bound source rows"
                    if frozen_rebinding_includes_field_authorities
                    else ""
                )
                + "."
            ),
            (
                "Rebind source_anchors and acceptance_authority_rationale to the "
                "current revised theory. "
                + (
                    "For each gate_field_authorities entry, preserve its exact "
                    "ordered field and authority_kind and update only source_anchors "
                    "and rationale. "
                    if frozen_rebinding_includes_field_authorities
                    else ""
                )
                + "Runtime owns and reconstructs every omitted field from the "
                "frozen rows, including target_subsystems, semantics, protocol, "
                "replicates, operator, thresholds, bounds, tolerance, aggregation, "
                "quorum, required, authority kind, and boundary."
            ),
            (
                "Use only exact current anchor IDs from "
                "acceptance_authority_catalog. Rebinding authority does not permit "
                "adding, deleting, relaxing, or reinterpreting any empirical gate."
            ),
            (
                "Do not use prior execution values or outcomes. This packet will "
                "undergo a fresh independent semantic review against the revised "
                "theory before any new descendant execution."
            ),
            (
                "These rows remain empirical controls and are never theorem proof "
                "evidence."
            ),
        ]
        prompt_payload["requirement_schema"] = response_requirement_schema
        prompt_payload["required_target_rows"] = []
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
        cumulative_finding_ledger = [
            dict(row)
            for row in carry_forward.get("cumulative_finding_ledger", []) or []
            if isinstance(row, Mapping)
        ]
        if not cumulative_finding_ledger:
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
            "requirement_reviews": [
                dict(row)
                for row in carried_review.get("requirement_reviews", []) or []
                if isinstance(row, Mapping)
            ],
            "portfolio_review": dict(
                carried_review.get("portfolio_review", {}) or {}
            ),
            "findings": [
                dict(row)
                for row in carried_review.get("findings", []) or []
                if isinstance(row, Mapping)
            ],
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
            candidate_prompt_payload["independent_semantic_review_feedback"] = (
                model_observations_without_repair_recipes(
                    {
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
                        "requirement_reviews": list(
                            prior_review_packet.get("requirement_reviews", []) or []
                        ),
                        "portfolio_review": dict(
                            prior_review_packet.get("portfolio_review", {}) or {}
                        ),
                        "findings": list(
                            prior_review_packet.get("findings", []) or []
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
                                    theory_material.get(
                                        "source_theory_packet_id", ""
                                    )
                                    or ""
                                ),
                                "current_source_theory_packet_hash": str(
                                    theory_material.get(
                                        "source_theory_packet_hash", ""
                                    )
                                    or ""
                                ),
                                "boundary": str(
                                    carry_forward.get("boundary", "") or ""
                                ),
                            }
                            if carry_forward
                            else {}
                        ),
                    },
                    preserve_exact_keys=(
                        "rejected_empirical_metric_requirements",
                    ),
                )
            )
        (
            model_prompt_payload,
            prompt_projection,
        ) = _compact_metric_authoring_prompt_payload(
            candidate_prompt_payload
        )
        request_user_prompt = json.dumps(
            model_prompt_payload,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )
        request_max_tokens = min(
            _METRIC_AUTHORING_LARGE_RESPONSE_TOKENS,
            max(
                1,
                int(config.max_tokens),
                (
                    _METRIC_AUTHORING_LARGE_RESPONSE_TOKENS
                    if prompt_projection["applied"]
                    else 1
                ),
            ),
        )
        request = GeneratorRequest(
            system_prompt=(
                "You are the ArchitectMetricContractPlanner inside the AI Statistician. "
                "Author domain-appropriate, executable empirical gates before either "
                "coding agent sees the task. Return JSON only."
            ),
            user_prompt=request_user_prompt,
            model=request_model,
            max_tokens=request_max_tokens,
            temperature=0.0,
            schema=response_schema,
            metadata={
                "subsystem": "ArchitectMetricContractPlanner",
                "agent": "LLMArchitectCoordinatorAgent",
                "provider_name": config.provider_name,
                "model_tier": config.model_tier,
                "resolved_model": request_model,
                "provider_structured_output": True,
                "user_prompt_chars": len(request_user_prompt),
                "metric_authoring_prompt_projection": dict(
                    prompt_projection
                ),
                "semantic_review_revision_index": revision_index,
                "semantic_review_feedback_packet_id": str(
                    prior_review_packet.get("packet_id", "") or ""
                ),
                "active_prior_finding_count": len(active_finding_ids),
                "active_prior_finding_ledger_fingerprint": (
                    active_finding_ledger_fingerprint
                ),
                "frozen_metric_protocol_rebinding": bool(frozen_rebinding),
                "source_requirement_set_id": str(
                    frozen_rebinding.get("source_requirement_set_id", "")
                    or ""
                ),
            },
        )

        def extract_authoring_payload(raw_text: str) -> dict[str, Any]:
            payload = extract_json_object(
                raw_text,
                label="LLM Architect metric-requirement packet",
            )
            if frozen_rebinding:
                return payload
            materialized_rows: list[dict[str, Any]] = []
            model_aci_errors: list[str] = []
            for requirement_index, row in enumerate(
                payload.get("empirical_metric_requirements", []) or []
            ):
                if not isinstance(row, Mapping):
                    model_aci_errors.append(
                        f"empirical_metric_requirements[{requirement_index}] "
                        "must be an object"
                    )
                    continue
                materialized, row_errors = (
                    _materialize_metric_authoring_model_requirement(
                        row,
                        requirement_index=requirement_index,
                    )
                )
                materialized_rows.append(materialized)
                model_aci_errors.extend(row_errors)
            (
                payload["empirical_metric_requirements"],
                omitted_nonrequired_rows,
            ) = _confirmatory_metric_requirement_rows(
                materialized_rows,
            )
            payload["_runtime_omitted_nonrequired_requirements"] = (
                omitted_nonrequired_rows
            )
            payload["_runtime_model_aci_errors"] = model_aci_errors
            return payload

        def build_packet(
            payload: Mapping[str, Any],
            response: Any,
            _raw_text: str,
        ) -> dict[str, Any]:
            requirements = payload.get("empirical_metric_requirements", [])
            omitted_nonrequired_rows = [
                dict(row)
                for row in payload.get(
                    "_runtime_omitted_nonrequired_requirements", []
                )
                if isinstance(row, Mapping)
            ]
            model_aci_errors = [
                str(error)
                for error in payload.get("_runtime_model_aci_errors", []) or []
                if str(error).strip()
            ]
            frozen_binding_errors: list[str] = []
            if frozen_rebinding:
                (
                    requirement_rows,
                    frozen_binding_errors,
                ) = _reconstruct_frozen_metric_protocol_requirements(
                    binding_rows=requirements,
                    rebinding_context=frozen_rebinding,
                )
                requirement_rows = [
                    (
                        materialize_generated_metric_gate_field_authorities(
                            row
                        )
                        if "gate_field_authorities" in row
                        else dict(row)
                    )
                    for row in requirement_rows
                ]
            else:
                requirement_rows = []
                for row in requirements:
                    if not isinstance(row, Mapping):
                        continue
                    requirement = dict(row)
                    requirement["required_runtime_replicates"] = (
                        runtime_replicates
                    )
                    requirement_rows.append(
                        materialize_generated_metric_gate_field_authorities(
                            requirement
                        )
                    )
                (
                    requirement_rows,
                    newly_omitted_nonrequired_rows,
                ) = _confirmatory_metric_requirement_rows(
                    requirement_rows,
                )
                omitted_nonrequired_rows.extend(
                    newly_omitted_nonrequired_rows
                )
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
                            implementation_interface.get("handoff_id", ""),
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
                "theory_execution_preflight_packet_id": str(
                    theory_execution_preflight_packet.get("packet_id", "") or ""
                ),
                "theory_execution_preflight_packet_hash": (
                    stable_hash(theory_execution_preflight_packet)
                    if theory_execution_preflight_packet
                    else ""
                ),
                "theory_execution_preflight_model": str(
                    theory_execution_preflight_packet.get("model", "") or ""
                ),
                "theory_execution_preflight_model_tier": str(
                    theory_execution_preflight_packet.get("model_tier", "")
                    or ""
                ),
                "theory_execution_preflight_retry_attempts": int(
                    theory_execution_preflight_packet.get(
                        "structured_output_retry_attempts", 0
                    )
                    or 0
                ),
                "theory_execution_preflight_proof_evidence_status": str(
                    theory_execution_preflight_packet.get(
                        "proof_evidence_status", ""
                    )
                    or ""
                ),
                "accepted_implementation_interface_handoff_id": str(
                    implementation_interface.get("handoff_id", "") or ""
                ),
                "accepted_implementation_interface_handoff_hash": (
                    stable_hash(implementation_interface)
                    if implementation_interface
                    else ""
                ),
                "accepted_implementation_execution_results_observed": False,
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
                "revision_target_finding_ids": active_finding_ids,
                "revision_target_finding_ledger_fingerprint": (
                    active_finding_ledger_fingerprint
                ),
                "runtime_owned_requirement_bindings": {
                    "target_subsystems": {
                        "source": "generated_metric_target_namespace",
                        "value": list(
                            GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                        ),
                        "model_authored": False,
                        "binding_stage": (
                            "before_hash_validation_and_review"
                        ),
                    },
                    "required": {
                        "source": "confirmatory_acceptance_portfolio",
                        "value": True,
                        "model_authored": False,
                        "binding_stage": (
                            "before_hash_validation_and_review"
                        ),
                    },
                    "required_runtime_replicates": {
                        "source": (
                            "runtime_contract."
                            "generated_sandbox_runtime_replicates"
                        ),
                        "value": runtime_replicates,
                        "model_authored": False,
                        "binding_stage": (
                            "before_hash_validation_and_review"
                        ),
                    },
                    "acceptance_authority_kind": {
                        "source": "preexecution_architect_authorship",
                        "value": FRESH_METRIC_AUTHORING_AUTHORITY_KIND,
                        "model_authored": False,
                        "binding_stage": (
                            "before_hash_validation_and_review"
                        ),
                    },
                    "gate_field_authority_mode": {
                        "source": "runtime_field_authority_abi",
                        "model_authored": False,
                        "binding_stage": (
                            "before_hash_validation_and_review"
                        ),
                    },
                    "flat_gate_values_and_authorities": {
                        "source": "model_gate_fields",
                        "model_authored_once": True,
                        "runtime_expands_evaluator_abi": True,
                        "runtime_selected_semantics": False,
                        "binding_stage": (
                            "before_hash_validation_and_review"
                        ),
                    },
                    "source_anchors": {
                        "source": (
                            "model_semantic_context_plus_"
                            "gate_field_anchor_union"
                        ),
                        "model_authored": True,
                        "runtime_augmented": True,
                        "binding_stage": (
                            "before_hash_validation_and_review"
                        ),
                    },
                },
                "confirmatory_required_rows_only": (
                    confirmatory_required_rows_only
                ),
                "model_requirement_transport": (
                    "keyed_gate_fields_runtime_provenance_v3"
                    if not frozen_rebinding
                    else "frozen_authority_rebinding"
                ),
                "model_requirement_transport_errors": model_aci_errors,
                "omitted_nonrequired_requirements": (
                    omitted_nonrequired_rows
                ),
                "empirical_metric_requirements": requirement_rows,
                "empirical_metric_requirement_set_id": (
                    generated_metric_requirement_set_id(requirement_rows)
                ),
                "frozen_metric_protocol_rebinding": bool(
                    frozen_rebinding
                ),
                "frozen_source_requirement_set_id": str(
                    frozen_rebinding.get("source_requirement_set_id", "")
                    or ""
                ),
                "frozen_gate_semantics_preserved": bool(
                    frozen_rebinding
                ),
                "frozen_rebinding_binding_errors": frozen_binding_errors,
                "proof_evidence_status": (
                    "ARCHITECT_METRIC_REQUIREMENT_AUTHORING_NOT_PROOF_EVIDENCE"
                ),
                "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
            }

        def validate_packet(packet: Mapping[str, Any]) -> list[str]:
            errors = [
                str(error)
                for error in packet.get(
                    "frozen_rebinding_binding_errors", []
                )
                if str(error).strip()
            ]
            if (
                not frozen_rebinding
                and len(
                    packet.get("empirical_metric_requirements", []) or []
                )
                > MAX_CONFIRMATORY_METRIC_REQUIREMENTS
            ):
                errors.append(
                    "confirmatory metric portfolio exceeds the shared review "
                    f"budget of {MAX_CONFIRMATORY_METRIC_REQUIREMENTS} rows"
                )
            if implementation_interface:
                if str(
                    packet.get(
                        "accepted_implementation_interface_handoff_id", ""
                    )
                    or ""
                ) != str(implementation_interface.get("handoff_id", "") or ""):
                    errors.append(
                        "accepted implementation interface handoff identity mismatch"
                    )
                if str(
                    packet.get(
                        "accepted_implementation_interface_handoff_hash", ""
                    )
                    or ""
                ) != stable_hash(implementation_interface):
                    errors.append(
                        "accepted implementation interface handoff hash mismatch"
                    )
                if packet.get(
                    "accepted_implementation_execution_results_observed"
                ) is not False:
                    errors.append(
                        "metric authoring cannot observe implementation execution results"
                    )
            errors.extend(
                str(error)
                for error in packet.get(
                    "model_requirement_transport_errors", []
                )
                or []
                if str(error).strip()
            )
            errors.extend(
                validate_generated_metric_requirements(
                    packet.get("empirical_metric_requirements", []),
                    required_target_subsystems=(
                        GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                    ),
                    expected_runtime_replicates=runtime_replicates,
                    require_acceptance_authority=True,
                    acceptance_authority_catalog=acceptance_authority_catalog,
                    require_gate_field_authorities=not bool(
                        frozen_rebinding
                    )
                    or any(
                        isinstance(row, Mapping)
                        and "gate_field_authorities" in row
                        for row in frozen_rebinding.get(
                            "source_requirement_rows", []
                        )
                    ),
                )
            )
            if frozen_rebinding:
                errors.extend(
                    _frozen_metric_protocol_rebinding_errors(
                        candidate_requirements=packet.get(
                            "empirical_metric_requirements", []
                        ),
                        rebinding_context=frozen_rebinding,
                    )
                )
            return errors

        with agent_runtime_substage(
            "architect_metric_requirement_author",
            metadata={
                "revision_index": revision_index,
                "model_tier": config.model_tier,
                "max_packet_regeneration_attempts": config.max_validation_retries,
                "active_prior_finding_count": len(active_finding_ids),
            },
        ):
            authoring_packet = generate_validated_json_packet(
                provider=provider,
                request=request,
                extract_payload=extract_authoring_payload,
                build_packet=build_packet,
                validate_packet=validate_packet,
                validation_label="LLM Architect metric-requirement packet",
                max_validation_retries=config.max_validation_retries,
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
            "upstream_research_contract": upstream_research_contract,
            "accepted_implementation_interface_handoff": (
                implementation_interface
            ),
            "frozen_metric_protocol_theory_rebinding": frozen_rebinding,
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
                (
                    "When frozen_metric_protocol_theory_rebinding is present, every "
                    "gate-defining field is immutable; review only whether the exact "
                    "frozen portfolio is semantically supported by the revised "
                    "theory and current authority bindings."
                ),
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
            "frozen_metric_protocol_rebinding": bool(frozen_rebinding),
            "frozen_source_requirement_set_id": str(
                frozen_rebinding.get("source_requirement_set_id", "")
                or ""
            ),
            "frozen_gate_semantics_preserved": bool(frozen_rebinding),
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
            try:
                semantic_review_packet = semantic_reviewer.review(
                    question=question,
                    review_material=review_material,
                    trusted_lineage=trusted_review_lineage,
                )
            except PacketValidationError as exc:
                raise ArchitectMetricSemanticReviewPacketValidationError(
                    cause=exc,
                    authoring_packet=authoring_packet,
                    revision_index=revision_index,
                    trusted_review_lineage=trusted_review_lineage,
                    review_material_fingerprint=stable_hash(review_material),
                    semantic_review_history=semantic_review_history,
                ) from exc
        review_packet_hash = stable_hash(semantic_review_packet)
        routed_current_findings = [
            dict(row)
            for row in semantic_review_packet.get("findings", []) or []
            if isinstance(row, Mapping)
        ]
        routed_current_findings = (
            bind_architect_metric_finding_evidence_identities(
                findings=routed_current_findings,
                review_material=review_material,
                prior_ledger=cumulative_finding_ledger,
            )
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
        for prior_history_row in semantic_review_history:
            prior_history_row.pop("cumulative_finding_ledger", None)
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
                "empirical_metric_requirement_count": len(
                    authoring_packet.get("empirical_metric_requirements", [])
                    or []
                ),
                "empirical_metric_requirements_fingerprint": stable_hash(
                    [
                        dict(row)
                        for row in authoring_packet.get(
                            "empirical_metric_requirements", []
                        )
                        or []
                        if isinstance(row, Mapping)
                    ]
                ),
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
                "revision_target_finding_ids": list(
                    authoring_packet.get("revision_target_finding_ids", []) or []
                ),
                "revision_target_finding_ledger_fingerprint": str(
                    authoring_packet.get(
                        "revision_target_finding_ledger_fingerprint", ""
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
                "requirement_reviews": [
                    dict(row)
                    for row in semantic_review_packet.get(
                        "requirement_reviews", []
                    )
                    or []
                    if isinstance(row, Mapping)
                ],
                "portfolio_review": dict(
                    semantic_review_packet.get("portfolio_review", {}) or {}
                ),
                "findings": routed_findings,
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
        prior_authoring_packet = authoring_packet
        prior_review_packet = {
            **dict(semantic_review_packet),
            "findings": routed_findings,
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
