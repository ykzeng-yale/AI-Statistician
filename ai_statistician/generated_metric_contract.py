from __future__ import annotations

from copy import deepcopy
import math
import re
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


GENERATED_METRIC_CONTRACT_SCHEMA_VERSION = 1
GENERATED_METRIC_EVALUATOR_CERTIFICATE_SCHEMA_VERSION = 1
GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES = 80
GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE = (
    "GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE"
)
GENERATED_METRIC_CONTRACT_BOUNDARY = (
    "Typed generated-metric contracts are pre-execution empirical acceptance "
    "controls. Runtime evaluation of them is implementation or simulation "
    "evidence only; it is not theorem proof evidence."
)
GENERATED_METRIC_CONTRACT_OPERATORS: tuple[str, ...] = (
    "<=",
    "<",
    ">=",
    ">",
    "==",
    "between",
)
GENERATED_METRIC_CONTRACT_AGGREGATIONS: tuple[str, ...] = (
    "identity",
    "mean",
    "min",
    "max",
    "all",
    "any",
    "at_least_count",
    "at_least_fraction",
)
GENERATED_METRIC_VALUE_KINDS: tuple[str, ...] = (
    "numeric",
    "boolean",
)
GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS: tuple[str, ...] = (
    "SimulationEngineer",
)
GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS: tuple[str, ...] = (
    "theory_derived",
    "theory_parameter_instantiation",
    "evaluation_mandated",
    "architect_preregistered_design",
    "diagnostic_only",
)
GENERATED_METRIC_ACCEPTANCE_GATING_AUTHORITY_KINDS: tuple[str, ...] = (
    "theory_derived",
    "theory_parameter_instantiation",
    "evaluation_mandated",
    "architect_preregistered_design",
)
GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE = "field_bound_v1"
GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS: tuple[str, ...] = (
    "threshold",
    "lower",
    "upper",
    "tolerance",
    "minimum_pass_count",
    "minimum_pass_fraction",
)
GENERATED_METRIC_THEORY_GATING_AUTHORITY_FIELDS: tuple[str, ...] = (
    "theorem_cards",
    "lemma_cards",
)
GENERATED_METRIC_THEORY_DERIVATION_GATING_AUTHORITY_FIELDS: tuple[str, ...] = (
    "derivation_summary",
    "derivation_steps",
    "equation_chain",
    "assumption_ledger",
    "sanity_checks",
)
GENERATED_METRIC_THEORY_DIAGNOSTIC_AUTHORITY_FIELDS: tuple[str, ...] = (
    "problem_card",
    "estimator_specs",
)
GENERATED_METRIC_EVALUATION_DESIGN_FIELDS: tuple[str, ...] = (
    "dgps",
    "methods",
    "stress_tests",
)
GENERATED_METRIC_NUMERIC_AUTHORITY_ERROR_CODE = (
    "generated_metric_numeric_authority_missing"
)
GENERATED_METRIC_REQUIREMENT_AUTHORITY_REQUIRED = (
    "architect_authored_coding_agent_bound_required"
)
GENERATED_METRIC_REQUIREMENT_AUTHORITY_PREFERRED = (
    "architect_authored_coding_agent_bound_preferred"
)
GENERATED_METRIC_REQUIREMENT_BOUNDARY = (
    "Architect-authored empirical metric requirements are independent acceptance "
    "proposals supplied before coding-agent generation. Coding agents may bind "
    "artifact IDs and result paths but may not invent or weaken required gates. "
    "The requirements and their evaluations are empirical controls, not theorem "
    "proof evidence."
)
GENERATED_METRIC_EVALUATOR_CERTIFICATE_BOUNDARY = (
    "A generated metric evaluator certificate records the exact deterministic "
    "comparison and aggregation dispatch used by the runtime. It is executable "
    "contract evidence, not statistical acceptance or theorem proof evidence."
)
GENERATED_METRIC_AUTHORITY_COPY_FIELDS: tuple[str, ...] = (
    "requirement_id",
    "metric_semantics",
    "metric_value_kind",
    "measurement_protocol",
    "required_runtime_replicates",
    "operator",
    "threshold",
    "lower",
    "upper",
    "tolerance",
    "aggregation",
    "minimum_pass_count",
    "minimum_pass_fraction",
    "required",
    "source_anchors",
    "acceptance_authority_kind",
    "acceptance_authority_rationale",
    "gate_field_authority_mode",
    "gate_field_authorities",
)
GENERATED_METRIC_BINDING_FIELDS: tuple[str, ...] = (
    "contract_id",
    "requirement_id",
    "artifact_id",
    "metric_path",
)


def generated_sandbox_runtime_replicates(n_runs: int) -> int:
    """Return the runtime-owned work budget supplied to generated sandboxes."""

    return max(5, min(int(n_runs), GENERATED_SANDBOX_MAX_RUNTIME_REPLICATES))


def generated_metric_requirement_target_namespace_contract() -> dict[str, Any]:
    """Describe the generated experiment owner for empirical acceptance gates."""

    return {
        "namespace": "generated_empirical_evaluation_subsystems",
        "field": "target_subsystems",
        "allowed_exact_values": list(
            GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
        ),
        "entry_rule": (
            "every array entry must equal one allowed value exactly; do not use "
            "a runtime execution-owner name in this empirical-author namespace"
        ),
        "capability_eval_required_coverage": [
            {"target_subsystems": [target]}
            for target in GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
        ],
        "runtime_execution_owner_by_author_subsystem": {
            "SimulationEngineer": "SimulationEvaluator",
        },
        "algorithm_acceptance_boundary": (
            "AlgorithmEngineer owns executable estimator implementation. Its exact "
            "source and smoke result require independent semantic review, but "
            "finite-sample statistical performance is evaluated only by the "
            "downstream SimulationEngineer experiment that consumes that artifact."
        ),
    }


def generated_metric_evaluation_semantics_contract() -> dict[str, Any]:
    """Describe the evaluator's comparison/aggregation order for LLM authors."""

    return {
        "resolved_value_rule": (
            "metric_path must resolve to raw measurements matching "
            "metric_value_kind; do not pre-threshold a measurable numeric "
            "quantity merely to return pass/fail flags"
        ),
        "metric_value_kinds": {
            "numeric": (
                "raw finite numeric measurements whose comparison constants "
                "remain subject to numeric acceptance authority"
            ),
            "boolean": (
                "an intrinsically boolean predicate returned as bool or exact "
                "0/1; select operator == and do not author threshold or tolerance "
                "gate_fields. The runtime materializes threshold 1 and tolerance 0 "
                "as its truth representation, not as substantive numeric cutoffs. "
                "Only aggregation quorum fields remain model-authored when the "
                "selected aggregation requires them"
            ),
        },
        "scalar_aggregations": {
            "values": ["identity", "mean", "min", "max"],
            "evaluation_order": (
                "aggregate the resolved raw values first, then apply operator and "
                "threshold or bounds once to the aggregate"
            ),
        },
        "elementwise_aggregations": {
            "values": ["all", "any", "at_least_count", "at_least_fraction"],
            "evaluation_order": (
                "apply operator and threshold or bounds independently to every "
                "resolved raw value, then aggregate the resulting booleans"
            ),
        },
        "quorum_rule": (
            "minimum_pass_count and minimum_pass_fraction are quorum fields over "
            "comparison results; they are never the comparison threshold"
        ),
        "boolean_predicate_rule": (
            "only an intrinsically boolean predicate may return bool or 0/1 values; "
            "select operator ==, omit threshold and tolerance from model-authored "
            "gate_fields, and let the runtime materialize == 1 with zero tolerance"
        ),
        "boundary": GENERATED_METRIC_CONTRACT_BOUNDARY,
    }


def generated_metric_evaluator_certificate(
    requirements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Certify the runtime's exact evaluator dispatch for typed requirements."""

    requirement_rows = [dict(row) for row in requirements]
    certificates: list[dict[str, Any]] = []
    for index, requirement in enumerate(requirement_rows):
        requirement_id = str(
            requirement.get("requirement_id", "") or ""
        ).strip()
        aggregation = str(requirement.get("aggregation", "") or "").strip()
        if aggregation in {"identity", "mean", "min", "max"}:
            dispatch_class = "scalar"
            evaluation_order = "aggregate_raw_values_then_compare_once"
            comparison_input = "one_scalar_aggregate"
            aggregation_input = "resolved_raw_values"
        elif aggregation in {
            "all",
            "any",
            "at_least_count",
            "at_least_fraction",
        }:
            dispatch_class = "elementwise"
            evaluation_order = "compare_each_raw_value_then_aggregate_booleans"
            comparison_input = "each_resolved_raw_value"
            aggregation_input = "per_value_comparison_results"
        else:
            dispatch_class = "invalid"
            evaluation_order = "invalid"
            comparison_input = "invalid"
            aggregation_input = "invalid"
        evaluator_shape_errors = _metric_comparison_shape_errors(
            requirement,
            prefix=f"empirical_metric_requirements[{index}]",
        )
        certificate_body = {
            "requirement_id": requirement_id,
            "requirement_fingerprint": stable_hash(requirement),
            "evaluator_shape_valid": not evaluator_shape_errors,
            "evaluator_shape_errors": evaluator_shape_errors,
            "dispatch_field": "aggregation",
            "dispatch_value": aggregation,
            "dispatch_class": dispatch_class,
            "metric_value_kind": _generated_metric_value_kind(requirement),
            "evaluation_order": evaluation_order,
            "comparison_stage": {
                "input": comparison_input,
                "operator": str(requirement.get("operator", "") or ""),
                "threshold": requirement.get("threshold"),
                "lower": requirement.get("lower"),
                "upper": requirement.get("upper"),
                "tolerance": requirement.get("tolerance"),
            },
            "aggregation_stage": {
                "input": aggregation_input,
                "operation": aggregation,
                "minimum_pass_count": requirement.get("minimum_pass_count"),
                "minimum_pass_fraction": requirement.get(
                    "minimum_pass_fraction"
                ),
            },
        }
        certificates.append(
            {
                "certificate_id": "generated_metric_evaluator_certificate:"
                + stable_hash(certificate_body)[:20],
                **certificate_body,
            }
        )
    requirement_schema_errors = validate_generated_metric_requirements(
        requirement_rows
    )
    certificate_set_body = {
        "requirement_set_id": generated_metric_requirement_set_id(
            requirement_rows
        ),
        "requirement_set_fingerprint": stable_hash(requirement_rows),
        "requirement_schema_errors": requirement_schema_errors,
        "dispatch_implementation": (
            "generated_metric_contract._evaluate_generated_metric_contract"
        ),
        "alternative_runtime_interpretations_allowed": False,
        "certificates": certificates,
    }
    return {
        "schema_version": GENERATED_METRIC_EVALUATOR_CERTIFICATE_SCHEMA_VERSION,
        "artifact_kind": "GeneratedMetricEvaluatorCertificateSet",
        "certificate_set_id": "generated_metric_evaluator_certificate_set:"
        + stable_hash(certificate_set_body)[:20],
        **certificate_set_body,
        "all_rows_schema_valid": not requirement_schema_errors,
        "proof_evidence_status": GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
        "boundary": GENERATED_METRIC_EVALUATOR_CERTIFICATE_BOUNDARY,
    }


def generated_metric_acceptance_authority_catalog(
    *,
    question: Mapping[str, Any],
    runtime_contract: Mapping[str, Any],
    theory_protocol_material: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Expose exact current-artifact leaves that may justify empirical gates."""

    theory_semantic_material = theory_protocol_material.get(
        "theory_semantic_material",
        {},
    )
    theory_semantic_material = (
        theory_semantic_material
        if isinstance(theory_semantic_material, Mapping)
        else {}
    )
    theory_gating_authority_material = {
        field: theory_semantic_material[field]
        for field in GENERATED_METRIC_THEORY_GATING_AUTHORITY_FIELDS
        if field in theory_semantic_material
    }
    theory_derivation_packet = theory_semantic_material.get(
        "theory_derivation_packet", {}
    )
    if isinstance(theory_derivation_packet, Mapping):
        derivation_authority = {
            field: theory_derivation_packet[field]
            for field in (
                GENERATED_METRIC_THEORY_DERIVATION_GATING_AUTHORITY_FIELDS
            )
            if field in theory_derivation_packet
        }
        if derivation_authority:
            theory_gating_authority_material["theory_derivation_packet"] = (
                derivation_authority
            )
    theory_diagnostic_authority_material = {
        field: theory_semantic_material[field]
        for field in GENERATED_METRIC_THEORY_DIAGNOSTIC_AUTHORITY_FIELDS
        if field in theory_semantic_material
    }
    simulation_ademp_spec = theory_semantic_material.get(
        "simulation_ademp_spec",
        {},
    )
    simulation_ademp_spec = (
        dict(simulation_ademp_spec)
        if isinstance(simulation_ademp_spec, Mapping)
        else {}
    )
    evaluation_design_material = {
        "simulation_ademp_spec": {
            field: simulation_ademp_spec[field]
            for field in GENERATED_METRIC_EVALUATION_DESIGN_FIELDS
            if field in simulation_ademp_spec
        }
    }
    diagnostic_simulation_material = {
        field: value
        for field, value in simulation_ademp_spec.items()
        if field not in GENERATED_METRIC_EVALUATION_DESIGN_FIELDS
    }
    if diagnostic_simulation_material:
        theory_diagnostic_authority_material["simulation_ademp_spec"] = (
            diagnostic_simulation_material
        )
    question_authority_material = {
        field: question.get(field)
        for field in ("title", "description")
        if str(question.get(field, "") or "").strip()
    }
    runtime_authority_material = {
        "simulation_targets": list(runtime_contract.get("simulation_targets", []) or [])
    }
    rows = [
        *_generated_metric_authority_semantic_rows(
            theory_gating_authority_material,
            root="theory",
            authority_kind="theory_derived",
        ),
        *_generated_metric_authority_semantic_rows(
            theory_diagnostic_authority_material,
            root="theory",
            authority_kind="diagnostic_only",
        ),
        *_generated_metric_authority_semantic_rows(
            evaluation_design_material,
            root="theory",
            authority_kind="evaluation_design",
        ),
        *_generated_metric_authority_leaf_rows(
            theory_gating_authority_material,
            root="theory",
            authority_kind="theory_derived",
        ),
        *_generated_metric_authority_leaf_rows(
            theory_diagnostic_authority_material,
            root="theory",
            authority_kind="diagnostic_only",
        ),
        *_generated_metric_authority_leaf_rows(
            evaluation_design_material,
            root="theory",
            authority_kind="evaluation_design",
        ),
        *_generated_metric_authority_leaf_rows(
            question_authority_material,
            root="question",
            authority_kind="evaluation_mandated",
        ),
        *_generated_metric_authority_leaf_rows(
            runtime_authority_material,
            root="runtime_contract",
            authority_kind="diagnostic_only",
        ),
    ]
    return sorted(rows, key=lambda row: str(row["anchor_id"]))


def generated_metric_acceptance_authority_prompt_catalog(
    catalog: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Prefer complete semantic records over their duplicated scalar leaves."""

    rows = [deepcopy(dict(row)) for row in catalog if isinstance(row, Mapping)]
    semantic_prefixes = [
        (
            str(row.get("anchor_id", "") or "").rstrip("/") + "/",
            str(row.get("authority_kind", "") or ""),
        )
        for row in rows
        if row.get("granularity") == "semantic_node"
        and str(row.get("anchor_id", "") or "").strip()
    ]
    projected = [
        row
        for row in rows
        if row.get("granularity") == "semantic_node"
        or not any(
            str(row.get("anchor_id", "") or "").startswith(prefix)
            and str(row.get("authority_kind", "") or "") == authority_kind
            for prefix, authority_kind in semantic_prefixes
        )
    ]
    return sorted(projected, key=lambda row: str(row.get("anchor_id", "")))


def _generated_metric_authority_semantic_rows(
    value: Any,
    *,
    root: str,
    authority_kind: str,
    path: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Expose each structured list record once instead of repeating every leaf."""

    if isinstance(value, Mapping):
        rows: list[dict[str, Any]] = []
        for key in sorted(value, key=lambda item: str(item)):
            rows.extend(
                _generated_metric_authority_semantic_rows(
                    value[key],
                    root=root,
                    authority_kind=authority_kind,
                    path=(*path, str(key)),
                )
            )
        return rows
    if not isinstance(value, (list, tuple)):
        return []
    rows = []
    for index, item in enumerate(value):
        if not isinstance(item, (Mapping, list, tuple)) or not item:
            continue
        item_path = (*path, str(index))
        pointer = "/".join(_json_pointer_escape(segment) for segment in item_path)
        content = deepcopy(dict(item) if isinstance(item, Mapping) else list(item))
        rows.append(
            {
                "anchor_id": f"{root}#/{pointer}",
                "authority_kind": authority_kind,
                "content": content,
                "explicit_numeric_values": _explicit_numeric_values(content),
                "granularity": "semantic_node",
            }
        )
    return rows


def _generated_metric_authority_leaf_rows(
    value: Any,
    *,
    root: str,
    authority_kind: str,
    path: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        rows: list[dict[str, Any]] = []
        for key in sorted(value, key=lambda item: str(item)):
            rows.extend(
                _generated_metric_authority_leaf_rows(
                    value[key],
                    root=root,
                    authority_kind=authority_kind,
                    path=(*path, str(key)),
                )
            )
        return rows
    if isinstance(value, (list, tuple)):
        rows = []
        for index, item in enumerate(value):
            rows.extend(
                _generated_metric_authority_leaf_rows(
                    item,
                    root=root,
                    authority_kind=authority_kind,
                    path=(*path, str(index)),
                )
            )
        return rows
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, str):
        content: Any = value.strip()
        if not content:
            return []
    elif _finite_number(value):
        content = value
    else:
        return []
    pointer = "/".join(_json_pointer_escape(segment) for segment in path)
    return [
        {
            "anchor_id": f"{root}#/{pointer}",
            "authority_kind": authority_kind,
            "content": content,
            "explicit_numeric_values": _explicit_numeric_values(content),
        }
    ]


def generated_metric_semantic_pointer_locator_id(
    *,
    root: Any,
    encoded_segments: Sequence[str],
    namespace: str,
) -> str:
    """Bind a pointer to stable list-row identities without exposing prompt metadata."""

    current = root
    semantic_path: list[Any] = []
    for encoded_segment in encoded_segments:
        segment = str(encoded_segment).replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and segment in current:
            current = current[segment]
            semantic_path.append(segment)
            continue
        if (
            isinstance(current, (list, tuple))
            and segment.isdigit()
            and int(segment) < len(current)
        ):
            index = int(segment)
            identities = [
                _generated_metric_semantic_list_item_identity(item)
                for item in current
            ]
            identity = identities[index]
            identity_key = stable_hash(identity) if identity else ""
            if not identity_key or sum(
                stable_hash(candidate) == identity_key
                for candidate in identities
                if candidate
            ) != 1:
                return ""
            semantic_path.append({"list_item_identity": identity})
            current = current[index]
            continue
        return ""
    return (
        "generated_metric_semantic_anchor:"
        + stable_hash([str(namespace), semantic_path])[:24]
    )


def _generated_metric_semantic_list_item_identity(value: Any) -> dict[str, Any]:
    """Return a content-independent row identity when the structure supplies one."""

    if isinstance(value, Mapping):
        keys = [str(key) for key in value]
        preferred_keys = [
            key
            for key in keys
            if key == "id" or key.endswith("_id")
        ]
        preferred_keys.extend(
            key
            for key in ("name", "claim_ref", "title", "label")
            if key in value and key not in preferred_keys
        )
        for key in preferred_keys:
            candidate = value.get(key)
            if isinstance(candidate, (str, int, float)) and not isinstance(
                candidate, bool
            ):
                normalized = str(candidate).strip()
                if normalized:
                    return {"field": key, "value": normalized}
        return {"row_fingerprint": stable_hash(dict(value))}
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        normalized = str(value).strip()
        if normalized:
            return {"value_fingerprint": stable_hash(normalized)}
    return {}


def _json_pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


_EXPLICIT_NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.])"
    r"(?P<number>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?P<percent>\s*%)?"
)


def _explicit_numeric_values(value: Any) -> list[int | float]:
    """Return literal numeric values without deriving unstated calibrations."""

    if _finite_number(value):
        return [_normalized_finite_number(value)]
    if isinstance(value, Mapping):
        return _unique_numeric_values(
            [
                candidate
                for child in value.values()
                for candidate in _explicit_numeric_values(child)
            ]
        )
    if isinstance(value, (list, tuple)):
        return _unique_numeric_values(
            [
                candidate
                for child in value
                for candidate in _explicit_numeric_values(child)
            ]
        )
    if not isinstance(value, str):
        return []
    values: list[int | float] = []
    for match in _EXPLICIT_NUMBER_PATTERN.finditer(value):
        try:
            parsed = float(match.group("number"))
        except (TypeError, ValueError):
            continue
        candidates = [parsed]
        if match.group("percent"):
            candidates.append(parsed / 100.0)
        for candidate in candidates:
            normalized = _normalized_finite_number(candidate)
            if not any(_same_finite_number(normalized, prior) for prior in values):
                values.append(normalized)
    return values


def _unique_numeric_values(values: Sequence[Any]) -> list[int | float]:
    unique: list[int | float] = []
    for value in values:
        if not _finite_number(value):
            continue
        normalized = _normalized_finite_number(value)
        if not any(_same_finite_number(normalized, prior) for prior in unique):
            unique.append(normalized)
    return unique


def _normalized_finite_number(value: Any) -> int | float:
    numeric = float(value)
    if numeric.is_integer():
        return int(numeric)
    return numeric


def _same_finite_number(left: Any, right: Any) -> bool:
    return bool(
        _finite_number(left)
        and _finite_number(right)
        and math.isclose(
            float(left),
            float(right),
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
    )


def generated_metric_numeric_authority_error(message: str) -> str:
    """Attach a stable routing code while preserving actionable error text."""

    return f"[{GENERATED_METRIC_NUMERIC_AUTHORITY_ERROR_CODE}] {message}"


def is_generated_metric_numeric_authority_error(value: Any) -> bool:
    return str(value or "").startswith(
        f"[{GENERATED_METRIC_NUMERIC_AUTHORITY_ERROR_CODE}] "
    )


def generated_metric_requirement_json_schema(
    *,
    require_acceptance_authority: bool = False,
    authority_anchor_ids: Sequence[str] = (),
    require_gate_field_authorities: bool = False,
) -> dict[str, Any]:
    """Return the machine-readable domain-neutral requirement schema.

    Keep this schema aligned with ``validate_generated_metric_requirements``.
    The provider sees this contract before generation, so semantic enums and
    scalar shapes belong here rather than only in a post-generation validator.
    """

    required_fields = [
        "requirement_id",
        "target_subsystems",
        "metric_semantics",
        "metric_value_kind",
        "measurement_protocol",
        "required_runtime_replicates",
        "operator",
        "threshold",
        "lower",
        "upper",
        "tolerance",
        "aggregation",
        "minimum_pass_count",
        "minimum_pass_fraction",
        "required",
        "source_anchors",
        "boundary",
    ]
    if require_acceptance_authority:
        required_fields.extend(
            [
                "acceptance_authority_kind",
                "acceptance_authority_rationale",
            ]
        )
    if require_gate_field_authorities:
        required_fields.extend(
            [
                "gate_field_authority_mode",
                "gate_field_authorities",
            ]
        )
    anchor_items: dict[str, Any] = {"type": "string", "minLength": 1}
    exact_anchor_ids = list(
        dict.fromkeys(
            str(value).strip()
            for value in authority_anchor_ids
            if str(value).strip()
        )
    )
    if exact_anchor_ids:
        anchor_items["enum"] = exact_anchor_ids
    schema = {
        "type": "object",
        "additionalProperties": True,
        "required": required_fields,
        "properties": {
            "requirement_id": {"type": "string", "minLength": 1},
            "target_subsystems": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {
                    "type": "string",
                    "enum": list(
                        GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
                    ),
                },
            },
            "metric_semantics": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "The raw scalar quantity returned at metric_path, before any "
                    "runtime comparison or quorum aggregation."
                ),
            },
            "metric_value_kind": {
                "type": "string",
                "enum": list(GENERATED_METRIC_VALUE_KINDS),
                "description": (
                    "Use numeric for measurable finite quantities. Use boolean "
                    "only for an intrinsically true/false predicate returned as "
                    "bool or exact 0/1."
                ),
            },
            "measurement_protocol": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "How raw measurements are produced for the declared runtime "
                    "replicates or scenarios; do not describe a pre-thresholded "
                    "pass-list when the underlying numeric measurement is available."
                ),
            },
            "required_runtime_replicates": {
                "type": "integer",
                "minimum": 1,
            },
            "operator": {
                "type": "string",
                "enum": list(GENERATED_METRIC_CONTRACT_OPERATORS),
                "description": (
                    "For identity/mean/min/max, compare the aggregate once. For "
                    "all/any/at_least_count/at_least_fraction, compare every raw "
                    "resolved value before applying the aggregation."
                ),
            },
            "threshold": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
                "description": (
                    "Numeric comparison boundary for each comparison; never place "
                    "the required pass count or pass fraction here."
                ),
            },
            "lower": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
            },
            "upper": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
            },
            "tolerance": {"type": "number", "minimum": 0},
            "aggregation": {
                "type": "string",
                "enum": list(GENERATED_METRIC_CONTRACT_AGGREGATIONS),
                "description": (
                    "Scalar modes aggregate raw values before comparison; elementwise "
                    "modes compare raw values before aggregating booleans."
                ),
            },
            "minimum_pass_count": {
                "anyOf": [{"type": "integer"}, {"type": "null"}],
                "description": (
                    "Quorum over successful elementwise comparisons for "
                    "at_least_count; separate from threshold."
                ),
            },
            "minimum_pass_fraction": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
                "description": (
                    "Quorum fraction over successful elementwise comparisons for "
                    "at_least_fraction; separate from threshold."
                ),
            },
            "required": {"type": "boolean"},
            "source_anchors": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": anchor_items,
                "description": (
                    "Exact anchor IDs from the current acceptance-authority catalog; "
                    "never free-form citations or paraphrases."
                    if require_acceptance_authority
                    else "Nonempty source, question, or theory reference IDs."
                ),
            },
            "acceptance_authority_kind": {
                "type": "string",
                "enum": list(GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS),
            },
            "acceptance_authority_rationale": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "Explain how exact cited nodes authorize the numeric gate, or, "
                    "for architect_preregistered_design, why each pre-execution "
                    "design choice is statistically meaningful and feasible."
                ),
            },
            "gate_field_authority_mode": {
                "type": "string",
                "enum": [GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE],
                "description": (
                    "Runtime-owned marker for explicit field-level numeric-gate "
                    "authority bindings."
                ),
            },
            "gate_field_authorities": {
                "type": "array",
                "maxItems": len(GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS),
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
                            "uniqueItems": True,
                            "items": anchor_items,
                        },
                        "rationale": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
                "description": (
                    "Exactly one entry for every substantive active numeric gate "
                    "field, in evaluator-field order. Each entry independently owns "
                    "that field's provenance; runtime computes the conservative "
                    "row-level acceptance_authority_kind roll-up. For boolean "
                    "metrics this array must be exactly [], even when threshold=1 "
                    "or tolerance=0 encodes the boolean comparison; those encoding "
                    "constants are not substantive numeric gates."
                ),
            },
            "boundary": {"type": "string", "minLength": 1},
        },
    }
    if not require_acceptance_authority:
        schema["properties"].pop("acceptance_authority_kind")
        schema["properties"].pop("acceptance_authority_rationale")
    if not require_gate_field_authorities:
        schema["properties"].pop("gate_field_authority_mode")
        schema["properties"].pop("gate_field_authorities")
    return schema


def generated_metric_requirement_prompt_schema(
    *,
    target_subsystem: str | None = None,
) -> dict[str, Any]:
    """Return the domain-neutral requirement shape authored upstream."""

    target = target_subsystem or GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS[0]
    if target not in GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS:
        raise ValueError(
            "target_subsystem must be an exact generated-code author subsystem"
        )

    return {
        "requirement_id": f"stable unique string for {target}",
        "target_subsystems": [target],
        "metric_semantics": (
            "exactly one independently compared scalar quantity, or one homogeneous "
            "collection whose members all use this row's single comparison; when a "
            "target varies by scenario, define a scalar deviation or ratio to it"
        ),
        "metric_value_kind": "numeric|boolean",
        "measurement_protocol": (
            "how this one comparison quantity is computed across seeds, scenarios, "
            "or replicates; split quantities with different comparisons into rows"
        ),
        "required_runtime_replicates": (
            "positive integer copied from the runtime-owned generated sandbox budget"
        ),
        "operator": "<=|<|>=|>|==|between",
        "threshold": "finite number for non-between operators; null for between",
        "lower": "finite number for between; null otherwise",
        "upper": "finite number for between; null otherwise",
        "tolerance": "finite nonnegative number; use 0 for an exact boundary",
        "aggregation": (
            "identity|mean|min|max|all|any|at_least_count|at_least_fraction"
        ),
        "minimum_pass_count": (
            "positive integer for at_least_count; null otherwise"
        ),
        "minimum_pass_fraction": (
            "number in [0,1] for at_least_fraction; null otherwise"
        ),
        "required": True,
        "source_anchors": [
            "exact anchor_id copied from acceptance_authority_catalog",
        ],
        "acceptance_authority_kind": (
            "theory_derived|theory_parameter_instantiation|"
            "evaluation_mandated|architect_preregistered_design|diagnostic_only"
        ),
        "acceptance_authority_rationale": (
            "how cited exact nodes authorize the predicate and every substantive "
            "numeric gate field, or why an "
            "architect_preregistered_design choice is meaningful before execution; "
            "a topical or asymptotic mention is not theory authority; "
            "theory_parameter_instantiation needs both the symbolic theory node and "
            "the exact preregistered evaluation-design value"
        ),
        "gate_field_authorities": [
            {
                "field": (
                    "exactly one active substantive field: threshold|lower|upper|"
                    "tolerance|minimum_pass_count|minimum_pass_fraction"
                ),
                "authority_kind": (
                    "theory_derived|theory_parameter_instantiation|"
                    "evaluation_mandated|architect_preregistered_design|"
                    "diagnostic_only"
                ),
                "source_anchors": [
                    "exact anchor_id copied from acceptance_authority_catalog",
                ],
                "rationale": (
                    "field-specific provenance and justification; do not use one "
                    "field's authority to launder another field"
                ),
            }
        ],
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }


def generated_metric_contract_prompt_schema(*, artifact_id_label: str) -> dict[str, Any]:
    """Return the minimal domain-neutral binding exposed to coding agents."""

    label = artifact_id_label.strip() or "artifact id"
    return {
        "contract_id": "stable unique string",
        "requirement_id": (
            "exact upstream empirical_metric_requirements requirement_id"
        ),
        "artifact_id": f"exact {label}; copy unchanged",
        "metric_path": [
            "JSON object key, zero-based list index, or * wildcard",
        ],
    }


def generated_metric_contract_binding_json_schema(
    *,
    requirement_ids: Sequence[str] = (),
    artifact_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Return a strict schema for the coding-agent side of an authority join."""

    requirement_values = list(
        dict.fromkeys(str(value).strip() for value in requirement_ids if str(value).strip())
    )
    artifact_values = list(
        dict.fromkeys(str(value).strip() for value in artifact_ids if str(value).strip())
    )
    requirement_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    artifact_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    if requirement_values:
        requirement_schema["enum"] = requirement_values
    if artifact_values:
        artifact_schema["enum"] = artifact_values
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(GENERATED_METRIC_BINDING_FIELDS),
        "properties": {
            "contract_id": {"type": "string", "minLength": 1},
            "requirement_id": requirement_schema,
            "artifact_id": artifact_schema,
            "metric_path": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "anyOf": [
                        {"type": "string", "minLength": 1},
                        {"type": "integer", "minimum": 0},
                    ]
                },
            },
        },
    }


def generated_metric_authority_context(
    requirements: Sequence[Mapping[str, Any]],
    *,
    target_subsystem: str,
    artifact_id_label: str,
) -> dict[str, Any]:
    """Build the immutable metric-authority facts supplied to the LLM."""

    relevant = generated_metric_requirements_for_subsystem(
        list(requirements),
        target_subsystem=target_subsystem,
    )
    return {
        "target_subsystem": target_subsystem,
        "artifact_id_source": artifact_id_label,
        "authoritative_empirical_metric_requirements": relevant,
        "required_authority_binding_rows": [
            {
                field: requirement.get(field)
                for field in GENERATED_METRIC_AUTHORITY_COPY_FIELDS
            }
            for requirement in relevant
            if requirement.get("required") is True
        ],
        "coding_agent_may_author_only": [
            "contract_id",
            "requirement_id",
            "artifact_id",
            "metric_path",
        ],
        "authority_copy_fields": list(GENERATED_METRIC_AUTHORITY_COPY_FIELDS),
        "authority_materialization_mode": "runtime_joined_frozen_requirement",
        "metric_evaluation_semantics": (
            generated_metric_evaluation_semantics_contract()
        ),
        "boundary": GENERATED_METRIC_REQUIREMENT_BOUNDARY,
    }


def validate_generated_metric_contracts(
    value: Any,
    *,
    expected_artifact_ids: Sequence[str] = (),
    required_artifact_ids: Sequence[str] = (),
    authoritative_requirements: Any = None,
    target_subsystem: str = "",
    require_authoritative_requirements: bool = False,
) -> list[str]:
    """Validate metric contracts without inferring any statistical vocabulary."""

    if not isinstance(value, list):
        return ["metric_contracts must be an array"]
    expected_ids = {str(item).strip() for item in expected_artifact_ids if str(item).strip()}
    required_ids = {str(item).strip() for item in required_artifact_ids if str(item).strip()}
    errors: list[str] = []
    seen_contract_ids: set[str] = set()
    covered_artifact_ids: set[str] = set()
    for index, raw_contract in enumerate(value):
        prefix = f"metric_contracts[{index}]"
        if not isinstance(raw_contract, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        contract_id = str(raw_contract.get("contract_id", "") or "").strip()
        if not contract_id:
            errors.append(f"{prefix}.contract_id must be a nonempty string")
        elif contract_id in seen_contract_ids:
            errors.append(f"duplicate metric contract_id: {contract_id}")
        else:
            seen_contract_ids.add(contract_id)
        artifact_id = str(raw_contract.get("artifact_id", "") or "").strip()
        if not artifact_id:
            errors.append(f"{prefix}.artifact_id must be a nonempty string")
        else:
            covered_artifact_ids.add(artifact_id)
            if expected_ids and artifact_id not in expected_ids:
                errors.append(
                    f"{prefix}.artifact_id is not a supplied task artifact: {artifact_id}"
                )
        metric_path = raw_contract.get("metric_path")
        if not isinstance(metric_path, list) or not metric_path:
            errors.append(f"{prefix}.metric_path must be a nonempty array")
        else:
            for path_index, segment in enumerate(metric_path):
                if isinstance(segment, bool) or not isinstance(segment, (str, int)):
                    errors.append(
                        f"{prefix}.metric_path[{path_index}] must be a string or integer"
                    )
                elif isinstance(segment, str) and not segment.strip():
                    errors.append(
                        f"{prefix}.metric_path[{path_index}] must not be empty"
                    )
                elif isinstance(segment, int) and segment < 0:
                    errors.append(
                        f"{prefix}.metric_path[{path_index}] must be nonnegative"
                    )
        errors.extend(_metric_comparison_shape_errors(raw_contract, prefix=prefix))
        if not isinstance(raw_contract.get("required"), bool):
            errors.append(f"{prefix}.required must be a boolean")
        source_anchors = raw_contract.get("source_anchors")
        if not isinstance(source_anchors, list) or not source_anchors:
            errors.append(f"{prefix}.source_anchors must contain at least one id")
        elif any(
            not isinstance(anchor, str) or not anchor.strip()
            for anchor in source_anchors
        ):
            errors.append(
                f"{prefix}.source_anchors entries must be nonempty strings"
            )
        if "required_runtime_replicates" in raw_contract:
            runtime_replicates = raw_contract.get("required_runtime_replicates")
            if (
                isinstance(runtime_replicates, bool)
                or not isinstance(runtime_replicates, int)
                or runtime_replicates <= 0
            ):
                errors.append(
                    f"{prefix}.required_runtime_replicates must be a positive integer"
                )
    missing_artifact_ids = required_ids - covered_artifact_ids
    if missing_artifact_ids:
        errors.append(
            "metric_contracts must bind every required artifact_id; missing: "
            + ", ".join(sorted(missing_artifact_ids))
        )
    if require_authoritative_requirements or (
        isinstance(authoritative_requirements, list)
        and bool(authoritative_requirements)
    ):
        errors.extend(
            _generated_metric_contract_authority_errors(
                value,
                authoritative_requirements=authoritative_requirements,
                target_subsystem=target_subsystem,
                required_artifact_ids=tuple(sorted(required_ids)),
                require_authoritative_requirements=require_authoritative_requirements,
            )
        )
    return sorted(set(errors))


def validate_generated_metric_requirements(
    value: Any,
    *,
    required_target_subsystems: Sequence[str] = (),
    expected_runtime_replicates: int | None = None,
    require_acceptance_authority: bool = False,
    acceptance_authority_catalog: Sequence[Mapping[str, Any]] = (),
    require_gate_field_authorities: bool = False,
) -> list[str]:
    """Validate upstream requirements without interpreting metric vocabulary."""

    if not isinstance(value, list):
        return ["empirical_metric_requirements must be an array"]
    errors: list[str] = []
    seen_ids: set[str] = set()
    covered_required_targets: set[str] = set()
    authority_row_by_anchor_id = {
        str(row.get("anchor_id", "") or "").strip(): dict(row)
        for row in acceptance_authority_catalog
        if isinstance(row, Mapping)
        and str(row.get("anchor_id", "") or "").strip()
    }
    authority_kind_by_anchor_id = {
        anchor_id: str(row.get("authority_kind", "") or "").strip()
        for anchor_id, row in authority_row_by_anchor_id.items()
    }
    for index, raw_requirement in enumerate(value):
        prefix = f"empirical_metric_requirements[{index}]"
        if not isinstance(raw_requirement, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        requirement_id = str(
            raw_requirement.get("requirement_id", "") or ""
        ).strip()
        if not requirement_id:
            errors.append(f"{prefix}.requirement_id must be a nonempty string")
        elif requirement_id in seen_ids:
            errors.append(f"duplicate empirical metric requirement_id: {requirement_id}")
        else:
            seen_ids.add(requirement_id)
        targets = raw_requirement.get("target_subsystems")
        if not isinstance(targets, list) or not targets:
            errors.append(f"{prefix}.target_subsystems must be a nonempty array")
            target_values: set[str] = set()
        else:
            target_values = {
                str(target).strip() for target in targets if str(target).strip()
            }
            invalid_targets = target_values - set(
                GENERATED_METRIC_REQUIREMENT_TARGET_SUBSYSTEMS
            )
            if invalid_targets:
                errors.append(
                    f"{prefix}.target_subsystems contains unsupported values: "
                    + ", ".join(sorted(invalid_targets))
                )
            if len(target_values) != len(targets):
                errors.append(
                    f"{prefix}.target_subsystems entries must be unique nonempty strings"
                )
        for field in ("metric_semantics", "measurement_protocol"):
            if not str(raw_requirement.get(field, "") or "").strip():
                errors.append(f"{prefix}.{field} must be a nonempty string")
        runtime_replicates = raw_requirement.get("required_runtime_replicates")
        if (
            isinstance(runtime_replicates, bool)
            or not isinstance(runtime_replicates, int)
            or runtime_replicates <= 0
        ):
            errors.append(
                f"{prefix}.required_runtime_replicates must be a positive integer"
            )
        elif (
            expected_runtime_replicates is not None
            and runtime_replicates != expected_runtime_replicates
        ):
            errors.append(
                f"{prefix}.required_runtime_replicates must equal the runtime-owned "
                f"generated sandbox budget {expected_runtime_replicates}"
            )
        errors.extend(_metric_comparison_shape_errors(raw_requirement, prefix=prefix))
        required = raw_requirement.get("required")
        if not isinstance(required, bool):
            errors.append(f"{prefix}.required must be a boolean")
        elif required:
            covered_required_targets.update(target_values)
        errors.extend(_metric_source_anchor_errors(raw_requirement, prefix=prefix))
        gate_field_authorities_present = (
            "gate_field_authorities" in raw_requirement
            or "gate_field_authority_mode" in raw_requirement
        )
        raw_gate_field_authorities = raw_requirement.get(
            "gate_field_authorities"
        )
        gate_field_authority_rows_present = bool(
            isinstance(raw_gate_field_authorities, list)
            and raw_gate_field_authorities
        )
        if require_gate_field_authorities and not gate_field_authorities_present:
            errors.append(
                f"{prefix}.gate_field_authorities are required for fresh "
                "field-bound metric authoring"
            )
        authority_fields_present = any(
            field in raw_requirement
            for field in (
                "acceptance_authority_kind",
                "acceptance_authority_rationale",
                "gate_field_authorities",
            )
        )
        if require_acceptance_authority or authority_fields_present:
            authority_kind = str(
                raw_requirement.get("acceptance_authority_kind", "") or ""
            ).strip()
            if authority_kind not in GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS:
                errors.append(
                    f"{prefix}.acceptance_authority_kind must be one of "
                    + ", ".join(GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS)
                )
            if not str(
                raw_requirement.get("acceptance_authority_rationale", "") or ""
            ).strip():
                errors.append(
                    f"{prefix}.acceptance_authority_rationale must be a nonempty "
                    "string"
                )
            source_anchors = raw_requirement.get("source_anchors", [])
            anchor_ids = (
                [
                    str(anchor).strip()
                    for anchor in source_anchors
                    if isinstance(anchor, str) and str(anchor).strip()
                ]
                if isinstance(source_anchors, list)
                else []
            )
            if require_acceptance_authority:
                unknown_anchor_ids = sorted(
                    set(anchor_ids) - set(authority_kind_by_anchor_id)
                )
                if unknown_anchor_ids:
                    errors.append(
                        f"{prefix}.source_anchors must copy exact current authority "
                        "anchor IDs; unknown: " + ", ".join(unknown_anchor_ids)
                    )
                if len(anchor_ids) != len(set(anchor_ids)):
                    errors.append(f"{prefix}.source_anchors entries must be unique")
                if not gate_field_authority_rows_present:
                    required_catalog_kinds = (
                        _generated_metric_required_catalog_authority_kinds(
                            authority_kind
                        )
                    )
                    for required_catalog_kind in required_catalog_kinds:
                        if not any(
                            authority_kind_by_anchor_id.get(anchor_id)
                            == required_catalog_kind
                            for anchor_id in anchor_ids
                        ):
                            errors.append(
                                generated_metric_numeric_authority_error(
                                    f"{prefix}.source_anchors must include an exact "
                                    f"{required_catalog_kind} authority node"
                                )
                            )
                if (
                    required is True
                    and authority_kind
                    in GENERATED_METRIC_ACCEPTANCE_GATING_AUTHORITY_KINDS
                    and not gate_field_authorities_present
                ):
                    numeric_catalog_kinds = set(
                        _generated_metric_numeric_catalog_authority_kinds(
                            authority_kind
                        )
                    )
                    if numeric_catalog_kinds:
                        cited_numeric_values: list[int | float] = []
                        for anchor_id in anchor_ids:
                            authority_row = authority_row_by_anchor_id.get(
                                anchor_id,
                                {},
                            )
                            if str(
                                authority_row.get("authority_kind", "") or ""
                            ).strip() not in numeric_catalog_kinds:
                                continue
                            raw_values = authority_row.get(
                                "explicit_numeric_values",
                                _explicit_numeric_values(
                                    authority_row.get("content")
                                ),
                            )
                            for value in raw_values or []:
                                if _finite_number(value):
                                    cited_numeric_values.append(
                                        _normalized_finite_number(value)
                                    )
                        for gate_field, gate_value in (
                            _generated_metric_required_gate_numeric_fields(
                                raw_requirement
                            )
                        ):
                            if not any(
                                _same_finite_number(gate_value, cited_value)
                                for cited_value in cited_numeric_values
                            ):
                                errors.append(
                                    generated_metric_numeric_authority_error(
                                        f"{prefix}.{gate_field}={gate_value!r} must be "
                                        "explicitly present in a cited "
                                        + " or ".join(sorted(numeric_catalog_kinds))
                                        + " authority node"
                                    )
                                )
                if gate_field_authorities_present:
                    errors.extend(
                        _generated_metric_gate_field_authority_errors(
                            raw_requirement,
                            prefix=prefix,
                            required=required,
                            authority_row_by_anchor_id=(
                                authority_row_by_anchor_id
                            ),
                        )
                    )
            if authority_kind == "diagnostic_only" and required is not False:
                errors.append(
                    f"{prefix}.diagnostic_only rows must set required=false"
                )
            if (
                required is True
                and authority_kind
                not in GENERATED_METRIC_ACCEPTANCE_GATING_AUTHORITY_KINDS
            ):
                errors.append(
                    f"{prefix}.required acceptance gates need one of: "
                    + ", ".join(
                        GENERATED_METRIC_ACCEPTANCE_GATING_AUTHORITY_KINDS
                    )
                )
    missing_targets = {
        str(target).strip()
        for target in required_target_subsystems
        if str(target).strip()
    } - covered_required_targets
    if missing_targets:
        errors.append(
            "empirical_metric_requirements must include at least one required row "
            "for every requested target subsystem; missing: "
            + ", ".join(sorted(missing_targets))
        )
    return sorted(set(errors))


def _generated_metric_required_catalog_authority_kinds(
    authority_kind: str,
) -> tuple[str, ...]:
    if authority_kind == "theory_parameter_instantiation":
        return ("theory_derived", "evaluation_design")
    if authority_kind in {
        "theory_derived",
        "evaluation_mandated",
    }:
        return (authority_kind,)
    return ()


def _generated_metric_numeric_catalog_authority_kinds(
    authority_kind: str,
) -> tuple[str, ...]:
    if authority_kind == "theory_parameter_instantiation":
        return ("evaluation_design",)
    if authority_kind in {
        "theory_derived",
        "evaluation_mandated",
    }:
        return (authority_kind,)
    return ()


def _generated_metric_required_gate_numeric_fields(
    requirement: Mapping[str, Any],
) -> list[tuple[str, int | float]]:
    """Return substantive numeric constants that determine required acceptance."""

    rows: list[tuple[str, int | float]] = []
    metric_value_kind = _generated_metric_value_kind(requirement)
    if metric_value_kind == "boolean":
        comparison_fields: tuple[str, ...] = ()
    elif str(requirement.get("operator", "") or "") == "between":
        comparison_fields = ("lower", "upper")
    else:
        comparison_fields = ("threshold",)
    for field in comparison_fields:
        value = requirement.get(field)
        if _finite_number(value):
            rows.append((field, _normalized_finite_number(value)))

    tolerance = requirement.get("tolerance")
    if _finite_number(tolerance) and not _same_finite_number(tolerance, 0):
        rows.append(("tolerance", _normalized_finite_number(tolerance)))

    aggregation = str(requirement.get("aggregation", "") or "")
    if aggregation == "at_least_count":
        minimum_pass_count = requirement.get("minimum_pass_count")
        if _finite_number(minimum_pass_count):
            rows.append(
                (
                    "minimum_pass_count",
                    _normalized_finite_number(minimum_pass_count),
                )
            )
    elif aggregation == "at_least_fraction":
        minimum_pass_fraction = requirement.get("minimum_pass_fraction")
        if _finite_number(minimum_pass_fraction):
            rows.append(
                (
                    "minimum_pass_fraction",
                    _normalized_finite_number(minimum_pass_fraction),
                )
            )
    return rows


def _generated_metric_expected_gate_numeric_field_names(
    requirement: Mapping[str, Any],
) -> list[str]:
    """Return gate fields required by the declared comparison shape.

    Unlike ``_generated_metric_required_gate_numeric_fields``, this helper
    retains structurally required fields whose values are currently invalid or
    absent. That lets one validation pass report both the missing value and its
    missing authority binding without inventing either one.
    """

    metric_value_kind = _generated_metric_value_kind(requirement)
    if metric_value_kind == "boolean":
        fields: list[str] = []
    elif str(requirement.get("operator", "") or "") == "between":
        fields = ["lower", "upper"]
    else:
        fields = ["threshold"]

    tolerance = requirement.get("tolerance")
    if _finite_number(tolerance) and not _same_finite_number(tolerance, 0):
        fields.append("tolerance")

    aggregation = str(requirement.get("aggregation", "") or "")
    if aggregation == "at_least_count":
        fields.append("minimum_pass_count")
    elif aggregation == "at_least_fraction":
        fields.append("minimum_pass_fraction")
    return fields


def generated_metric_expected_gate_field_names(
    requirement: Mapping[str, Any],
) -> list[str]:
    """Expose the evaluator-owned canonical field order to typed transports."""

    return _generated_metric_expected_gate_numeric_field_names(requirement)


def generated_metric_gate_field_authority_rollup(
    gate_field_authorities: Sequence[Mapping[str, Any]],
    *,
    fallback: str = "",
) -> str:
    """Return a conservative row summary without erasing field provenance."""

    kinds = {
        str(row.get("authority_kind", "") or "").strip()
        for row in gate_field_authorities
        if isinstance(row, Mapping)
        and str(row.get("authority_kind", "") or "").strip()
    }
    if not kinds:
        return str(fallback or "").strip()
    if len(kinds) == 1:
        return next(iter(kinds))
    if "architect_preregistered_design" in kinds:
        return "architect_preregistered_design"
    if "diagnostic_only" in kinds:
        return "diagnostic_only"
    if kinds <= {"theory_derived", "theory_parameter_instantiation"}:
        return "theory_parameter_instantiation"
    # Combining independently authorized source gates into one executable pass
    # region is itself a preregistered design choice.
    return "architect_preregistered_design"


def materialize_generated_metric_gate_field_authorities(
    requirement: Mapping[str, Any],
) -> dict[str, Any]:
    """Expand and canonicalize explicit field-authority bindings."""

    body = dict(requirement)
    active_fields = [
        field
        for field, _value in _generated_metric_required_gate_numeric_fields(
            body
        )
    ]
    if "gate_field_authorities" in body:
        raw_rows = body.get("gate_field_authorities")
        if not isinstance(raw_rows, list):
            body["gate_field_authority_mode"] = (
                GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE
            )
            return body
        rows = [
            dict(row) if isinstance(row, Mapping) else row
            for row in raw_rows
        ]
        if _generated_metric_value_kind(body) == "boolean":
            runtime_truth_fields = {"operator", "threshold", "tolerance"}
            rows = [
                row
                for row in rows
                if not (
                    isinstance(row, Mapping)
                    and str(row.get("field", "") or "").strip()
                    in runtime_truth_fields
                    and str(row.get("field", "") or "").strip()
                    not in active_fields
                )
            ]
    else:
        authority_kind = str(
            body.get("acceptance_authority_kind", "") or ""
        ).strip()
        source_anchors = [
            str(value).strip()
            for value in body.get("source_anchors", []) or []
            if str(value).strip()
        ]
        rationale = str(
            body.get("acceptance_authority_rationale", "") or ""
        ).strip()
        rows = [
            {
                "field": field,
                "authority_kind": authority_kind,
                "source_anchors": source_anchors,
                "rationale": rationale,
            }
            for field in active_fields
        ]
    body["gate_field_authority_mode"] = (
        GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE
    )
    body["gate_field_authorities"] = rows
    raw_source_anchors = body.get("source_anchors")
    if isinstance(raw_source_anchors, list):
        body["source_anchors"] = list(
            dict.fromkeys(
                [
                    *[
                        str(value).strip()
                        for value in raw_source_anchors
                        if str(value).strip()
                    ],
                    *[
                        str(anchor_id).strip()
                        for row in rows
                        if isinstance(row, Mapping)
                        and isinstance(
                            row.get("source_anchors"), list
                        )
                        for anchor_id in row.get(
                            "source_anchors", []
                        )
                        if str(anchor_id).strip()
                    ],
                ]
            )
        )
    body["acceptance_authority_kind"] = (
        generated_metric_gate_field_authority_rollup(
            rows,
            fallback=str(
                body.get("acceptance_authority_kind", "") or ""
            ),
        )
    )
    return body


def _generated_metric_gate_field_authority_errors(
    requirement: Mapping[str, Any],
    *,
    prefix: str,
    required: Any,
    authority_row_by_anchor_id: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if requirement.get("gate_field_authority_mode") != (
        GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE
    ):
        errors.append(
            f"{prefix}.gate_field_authority_mode must equal "
            f"{GENERATED_METRIC_GATE_FIELD_AUTHORITY_MODE}"
        )
    expected_fields = _generated_metric_expected_gate_numeric_field_names(
        requirement
    )
    expected_values = dict(
        _generated_metric_required_gate_numeric_fields(requirement)
    )
    raw_rows = requirement.get("gate_field_authorities")
    if not isinstance(raw_rows, list):
        return [
            *errors,
            f"{prefix}.gate_field_authorities must be an array",
        ]
    rows = [row for row in raw_rows if isinstance(row, Mapping)]
    if len(rows) != len(raw_rows):
        errors.append(
            f"{prefix}.gate_field_authorities entries must be objects"
        )
    observed_fields = [
        str(row.get("field", "") or "").strip() for row in rows
    ]
    if observed_fields != expected_fields:
        empty_field_guidance = (
            "; this metric declares no substantive numeric gate fields, so "
            "gate_field_authorities must be the empty array [] and must not "
            "contain placeholder rows"
            if not expected_fields
            else ""
        )
        errors.append(
            generated_metric_numeric_authority_error(
                f"{prefix}.gate_field_authorities must bind each declared "
                "substantive numeric field exactly once in order: "
                f"expected={expected_fields!r} observed={observed_fields!r}"
                f"{empty_field_guidance}"
            )
        )

    top_level_anchors = {
        str(value).strip()
        for value in requirement.get("source_anchors", []) or []
        if str(value).strip()
    }
    for index, row in enumerate(rows):
        field = str(row.get("field", "") or "").strip()
        row_prefix = f"{prefix}.gate_field_authorities[{index}]"
        if field not in GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS:
            errors.append(
                f"{row_prefix}.field must be one of "
                + ", ".join(GENERATED_METRIC_GATE_FIELD_AUTHORITY_FIELDS)
            )
            continue
        authority_kind = str(
            row.get("authority_kind", "") or ""
        ).strip()
        if authority_kind not in GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS:
            errors.append(
                f"{row_prefix}.authority_kind must be one of "
                + ", ".join(GENERATED_METRIC_ACCEPTANCE_AUTHORITY_KINDS)
            )
        rationale = str(row.get("rationale", "") or "").strip()
        if not rationale:
            errors.append(f"{row_prefix}.rationale must be a nonempty string")
        raw_anchors = row.get("source_anchors")
        if not isinstance(raw_anchors, list) or not raw_anchors:
            errors.append(
                f"{row_prefix}.source_anchors must contain at least one id"
            )
            anchor_ids: list[str] = []
        else:
            anchor_ids = [
                str(value).strip()
                for value in raw_anchors
                if isinstance(value, str) and str(value).strip()
            ]
            if len(anchor_ids) != len(raw_anchors):
                errors.append(
                    f"{row_prefix}.source_anchors entries must be nonempty strings"
                )
            if len(anchor_ids) != len(set(anchor_ids)):
                errors.append(
                    f"{row_prefix}.source_anchors entries must be unique"
                )
        unknown_anchor_ids = sorted(
            set(anchor_ids) - set(authority_row_by_anchor_id)
        )
        if unknown_anchor_ids:
            errors.append(
                f"{row_prefix}.source_anchors must copy exact current authority "
                "anchor IDs; unknown: " + ", ".join(unknown_anchor_ids)
            )
        anchors_outside_row = sorted(set(anchor_ids) - top_level_anchors)
        if anchors_outside_row:
            errors.append(
                f"{row_prefix}.source_anchors must also occur in the row-level "
                "source_anchors: " + ", ".join(anchors_outside_row)
            )
        numeric_kinds = set(
            _generated_metric_numeric_catalog_authority_kinds(
                authority_kind
            )
        )
        field_value = expected_values.get(field)
        exact_catalog_match_available = bool(
            field in expected_values
            and numeric_kinds
            and any(
                str(authority_row.get("authority_kind", "") or "").strip()
                in numeric_kinds
                and any(
                    _same_finite_number(field_value, candidate)
                    for candidate in authority_row.get(
                        "explicit_numeric_values",
                        _explicit_numeric_values(authority_row.get("content")),
                    )
                    or []
                    if _finite_number(candidate)
                )
                for authority_row in authority_row_by_anchor_id.values()
            )
        )
        source_owner_unavailable = bool(
            field in expected_values
            and numeric_kinds
            and not exact_catalog_match_available
        )
        if source_owner_unavailable:
            errors.append(
                generated_metric_numeric_authority_error(
                    f"{row_prefix}.authority_kind={authority_kind!r} cannot "
                    f"authorize {field}={field_value!r}: no exact "
                    + " or ".join(sorted(numeric_kinds))
                    + " catalog node contains that value. The LLM must choose "
                    "a supported source owner, architect_preregistered_design "
                    "with a pre-execution rationale, diagnostic_only with "
                    "required=false, or remove the row; runtime will not infer "
                    "or map the owner."
                )
            )
        else:
            for required_kind in (
                _generated_metric_required_catalog_authority_kinds(
                    authority_kind
                )
            ):
                if not any(
                    str(
                        authority_row_by_anchor_id.get(anchor_id, {}).get(
                            "authority_kind", ""
                        )
                        or ""
                    ).strip()
                    == required_kind
                    for anchor_id in anchor_ids
                ):
                    errors.append(
                        generated_metric_numeric_authority_error(
                            f"{row_prefix}.source_anchors must include an exact "
                            f"{required_kind} authority node"
                        )
                    )
        if (
            required is True
            and authority_kind
            not in GENERATED_METRIC_ACCEPTANCE_GATING_AUTHORITY_KINDS
        ):
            errors.append(
                f"{row_prefix}.required acceptance field needs one of: "
                + ", ".join(
                    GENERATED_METRIC_ACCEPTANCE_GATING_AUTHORITY_KINDS
                )
            )
        if authority_kind == "diagnostic_only" and required is not False:
            errors.append(
                f"{row_prefix}.diagnostic_only authority requires required=false"
            )
        if (
            field not in expected_values
            or not numeric_kinds
            or source_owner_unavailable
        ):
            continue
        cited_values: list[int | float] = []
        for anchor_id in anchor_ids:
            authority_row = authority_row_by_anchor_id.get(anchor_id, {})
            if str(
                authority_row.get("authority_kind", "") or ""
            ).strip() not in numeric_kinds:
                continue
            raw_values = authority_row.get(
                "explicit_numeric_values",
                _explicit_numeric_values(authority_row.get("content")),
            )
            cited_values.extend(
                _normalized_finite_number(value)
                for value in raw_values or []
                if _finite_number(value)
            )
        field_value = expected_values[field]
        if not any(
            _same_finite_number(field_value, cited_value)
            for cited_value in cited_values
        ):
            errors.append(
                generated_metric_numeric_authority_error(
                    f"{row_prefix}.{field}={field_value!r} must be explicitly "
                    "present in a cited "
                    + " or ".join(sorted(numeric_kinds))
                    + " authority node"
                )
            )

    expected_rollup = generated_metric_gate_field_authority_rollup(
        rows,
        fallback=str(
            requirement.get("acceptance_authority_kind", "") or ""
        ),
    )
    observed_rollup = str(
        requirement.get("acceptance_authority_kind", "") or ""
    ).strip()
    if observed_rollup != expected_rollup:
        errors.append(
            f"{prefix}.acceptance_authority_kind must equal the runtime "
            f"gate-field roll-up {expected_rollup!r}; observed={observed_rollup!r}"
        )
    return errors


def generated_metric_requirement_set_id(
    requirements: Sequence[Mapping[str, Any]],
) -> str:
    if not requirements:
        return ""
    return "generated_metric_requirement_set:" + stable_hash(
        [dict(requirement) for requirement in requirements]
    )[:20]


def generated_metric_requirements_for_subsystem(
    value: Any,
    *,
    target_subsystem: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    target = target_subsystem.strip()
    return [
        dict(requirement)
        for requirement in value
        if isinstance(requirement, Mapping)
        and target
        in {
            str(item).strip()
            for item in requirement.get("target_subsystems", []) or []
        }
    ]


def generated_metric_requirements_from_context(
    value: Any,
    *,
    target_subsystem: str,
) -> list[dict[str, Any]]:
    """Read the first explicit Architect authority set from known context slots."""

    candidates: list[Any] = []
    if isinstance(value, Mapping):
        for key in ("architect_evidence_contract", "runtime_requested_evidence_contract"):
            nested = value.get(key, {})
            if isinstance(nested, Mapping):
                candidates.append(nested.get("empirical_metric_requirements"))
        candidates.append(value.get("empirical_metric_requirements"))
        direct_plan = value.get("architect_runtime_plan", {})
        if isinstance(direct_plan, Mapping):
            direct_contract = direct_plan.get("evidence_contract", {})
            if isinstance(direct_contract, Mapping):
                candidates.append(
                    direct_contract.get("empirical_metric_requirements")
                )
        architect_context = value.get("architect_context", {})
        if isinstance(architect_context, Mapping):
            plan = architect_context.get("architect_runtime_plan", {})
            if isinstance(plan, Mapping):
                contract = plan.get("evidence_contract", {})
                if isinstance(contract, Mapping):
                    candidates.append(contract.get("empirical_metric_requirements"))
    elif isinstance(value, list):
        candidates.append(value)
    for candidate in candidates:
        relevant = generated_metric_requirements_for_subsystem(
            candidate,
            target_subsystem=target_subsystem,
        )
        if relevant:
            return relevant
    return []


def generated_metric_requirement_authority_policy_from_context(value: Any) -> str:
    if not isinstance(value, Mapping):
        return ""
    candidates: list[Mapping[str, Any]] = []
    for key in ("architect_evidence_contract", "runtime_requested_evidence_contract"):
        nested = value.get(key, {})
        if isinstance(nested, Mapping):
            candidates.append(nested)
    candidates.append(value)
    direct_plan = value.get("architect_runtime_plan", {})
    if isinstance(direct_plan, Mapping):
        direct_contract = direct_plan.get("evidence_contract", {})
        if isinstance(direct_contract, Mapping):
            candidates.append(direct_contract)
    architect_context = value.get("architect_context", {})
    if isinstance(architect_context, Mapping):
        plan = architect_context.get("architect_runtime_plan", {})
        if isinstance(plan, Mapping):
            contract = plan.get("evidence_contract", {})
            if isinstance(contract, Mapping):
                candidates.append(contract)
    for candidate in candidates:
        policy = str(
            candidate.get("generated_metric_requirement_authority_policy", "") or ""
        ).strip()
        if policy:
            return policy
    return ""


def bind_generated_metric_contract_authority(
    contracts: Sequence[Mapping[str, Any]],
    *,
    authoritative_requirements: Sequence[Mapping[str, Any]],
    target_subsystem: str,
) -> list[dict[str, Any]]:
    """Attach deterministic lineage only to contracts that exactly preserve authority."""

    requirements = generated_metric_requirements_for_subsystem(
        list(authoritative_requirements),
        target_subsystem=target_subsystem,
    )
    by_id = {
        str(row.get("requirement_id", "") or "").strip(): row
        for row in requirements
        if str(row.get("requirement_id", "") or "").strip()
    }
    set_id = generated_metric_requirement_set_id(requirements)
    bound: list[dict[str, Any]] = []
    for raw_contract in contracts:
        contract = dict(raw_contract)
        requirement = by_id.get(
            str(contract.get("requirement_id", "") or "").strip()
        )
        if requirement is not None and not _metric_authority_mismatches(
            contract,
            requirement,
        ):
            contract["authority_requirement_fingerprint"] = stable_hash(
                dict(requirement)
            )
            contract["authority_requirement_set_id"] = set_id
            contract["authority_source_subsystem"] = "ArchitectCoordinator"
        bound.append(contract)
    return bound


def materialize_generated_metric_contract_bindings(
    bindings: Sequence[Mapping[str, Any]],
    *,
    authoritative_requirements: Sequence[Mapping[str, Any]],
    target_subsystem: str,
) -> list[dict[str, Any]]:
    """Join coding-agent bindings to immutable Architect-authored requirements.

    The coding agent chooses only a requirement foreign key, artifact foreign key,
    and returned metric path. Any attempted authority-field echo is discarded and
    audited before the normal strict authority validator runs.
    """

    requirements = generated_metric_requirements_for_subsystem(
        list(authoritative_requirements),
        target_subsystem=target_subsystem,
    )
    by_id = {
        str(row.get("requirement_id", "") or "").strip(): row
        for row in requirements
        if str(row.get("requirement_id", "") or "").strip()
    }
    materialized: list[dict[str, Any]] = []
    for raw_binding in bindings:
        contract = dict(raw_binding)
        requirement_id = str(contract.get("requirement_id", "") or "").strip()
        requirement = by_id.get(requirement_id)
        if requirement is None:
            materialized.append(contract)
            continue
        submitted_authority_fields = [
            field
            for field in GENERATED_METRIC_AUTHORITY_COPY_FIELDS
            if field != "requirement_id" and field in contract
        ]
        discarded_override_fields = [
            field
            for field in submitted_authority_fields
            if contract.get(field) != requirement.get(field)
        ]
        for field in GENERATED_METRIC_AUTHORITY_COPY_FIELDS:
            contract[field] = requirement.get(field)
        contract["boundary"] = GENERATED_METRIC_CONTRACT_BOUNDARY
        contract["authority_binding_mode"] = "runtime_joined_frozen_requirement"
        contract["coding_agent_submitted_authority_fields"] = (
            submitted_authority_fields
        )
        contract["discarded_authority_override_fields"] = (
            discarded_override_fields
        )
        materialized.append(contract)
    return bind_generated_metric_contract_authority(
        materialized,
        authoritative_requirements=requirements,
        target_subsystem=target_subsystem,
    )


def generated_metric_contracts_for_artifact(
    value: Any,
    *,
    artifact_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    target = artifact_id.strip()
    return [
        dict(contract)
        for contract in value
        if isinstance(contract, Mapping)
        and str(contract.get("artifact_id", "") or "").strip() == target
    ]


def generated_metric_contract_set_id(contracts: Sequence[Mapping[str, Any]]) -> str:
    if not contracts:
        return ""
    return "generated_metric_contract_set:" + stable_hash(
        [dict(contract) for contract in contracts]
    )[:20]


def evaluate_generated_metric_contracts(
    metrics: Any,
    *,
    contracts: Sequence[Mapping[str, Any]],
    artifact_id: str,
    runtime_replicates: int | None = None,
    authoritative_requirements: Any = None,
    target_subsystem: str = "",
    require_authoritative_requirements: bool = False,
) -> dict[str, Any]:
    """Evaluate validated contracts against one generated result artifact."""

    contract_rows = [dict(contract) for contract in contracts]
    schema_errors = validate_generated_metric_contracts(
        contract_rows,
        expected_artifact_ids=(artifact_id,),
        required_artifact_ids=(artifact_id,),
        authoritative_requirements=authoritative_requirements,
        target_subsystem=target_subsystem,
        require_authoritative_requirements=require_authoritative_requirements,
    )
    evaluations: list[dict[str, Any]] = []
    required_failure_errors: list[str] = []
    if schema_errors:
        required_failure_errors.extend(schema_errors)
    else:
        for contract in contract_rows:
            evaluation = _evaluate_generated_metric_contract(
                metrics,
                contract=contract,
            )
            expected_replicates = contract.get("required_runtime_replicates")
            if expected_replicates is not None:
                evaluation["required_runtime_replicates"] = expected_replicates
                evaluation["observed_runtime_replicates"] = runtime_replicates
                if runtime_replicates is None:
                    evaluation["passed"] = False
                    evaluation["errors"].append(
                        f"metric contract {evaluation['contract_id']}: runtime "
                        "replicate count was not recorded"
                    )
                elif int(runtime_replicates) != int(expected_replicates):
                    evaluation["passed"] = False
                    evaluation["errors"].append(
                        f"metric contract {evaluation['contract_id']}: runtime "
                        f"replicates={runtime_replicates}, required="
                        f"{expected_replicates}"
                    )
            evaluations.append(evaluation)
            if contract.get("required") is True and evaluation["passed"] is not True:
                required_failure_errors.extend(evaluation["errors"])
    n_passed = sum(1 for row in evaluations if row.get("passed") is True)
    n_failed = sum(1 for row in evaluations if row.get("passed") is not True)
    return {
        "schema_version": GENERATED_METRIC_CONTRACT_SCHEMA_VERSION,
        "artifact_kind": "GeneratedMetricContractEvaluation",
        "artifact_id": artifact_id,
        "metric_contract_set_id": generated_metric_contract_set_id(contract_rows),
        "metric_requirement_set_id": generated_metric_requirement_set_id(
            generated_metric_requirements_for_subsystem(
                authoritative_requirements,
                target_subsystem=target_subsystem,
            )
        ),
        "metric_requirement_authority_enforced": bool(
            require_authoritative_requirements
        ),
        "metric_requirement_authority_validated": bool(
            require_authoritative_requirements and not schema_errors
        ),
        "metric_contract_schema_valid": not schema_errors,
        "n_contracts": len(contract_rows),
        "n_passed": n_passed,
        "n_failed": n_failed,
        "all_required_passed": not required_failure_errors,
        "required_failure_errors": list(dict.fromkeys(required_failure_errors)),
        "evaluations": evaluations,
        "proof_evidence_status": GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
        "boundary": GENERATED_METRIC_CONTRACT_BOUNDARY,
    }


def _evaluate_generated_metric_contract(
    metrics: Any,
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    contract_id = str(contract.get("contract_id", "") or "")
    path = list(contract.get("metric_path", []) or [])
    values, path_error = _resolve_generated_metric_path(metrics, path)
    numeric_values: list[float] = []
    errors: list[str] = []
    if path_error:
        errors.append(f"metric contract {contract_id}: {path_error}")
    else:
        numeric_values, numeric_error = _metric_numeric_values(
            values,
            metric_value_kind=_generated_metric_value_kind(contract),
        )
        if numeric_error:
            errors.append(f"metric contract {contract_id}: {numeric_error}")
    aggregation = str(contract.get("aggregation", "") or "")
    aggregate_value: float | None = None
    comparison_results: list[bool] = []
    if not errors:
        if aggregation == "identity":
            if len(numeric_values) != 1:
                errors.append(
                    f"metric contract {contract_id}: identity aggregation resolved "
                    f"{len(numeric_values)} numeric values, expected exactly 1"
                )
            else:
                aggregate_value = numeric_values[0]
                comparison_results = [
                    _metric_comparison_passes(aggregate_value, contract)
                ]
        elif aggregation == "mean":
            aggregate_value = sum(numeric_values) / len(numeric_values)
            comparison_results = [_metric_comparison_passes(aggregate_value, contract)]
        elif aggregation == "min":
            aggregate_value = min(numeric_values)
            comparison_results = [_metric_comparison_passes(aggregate_value, contract)]
        elif aggregation == "max":
            aggregate_value = max(numeric_values)
            comparison_results = [_metric_comparison_passes(aggregate_value, contract)]
        elif aggregation in {
            "all",
            "any",
            "at_least_count",
            "at_least_fraction",
        }:
            comparison_results = [
                _metric_comparison_passes(value, contract)
                for value in numeric_values
            ]
        else:  # pragma: no cover - guarded by packet validation
            errors.append(f"metric contract {contract_id}: unsupported aggregation")
    passed = False
    if not errors:
        if aggregation == "any":
            passed = any(comparison_results)
        elif aggregation == "at_least_count":
            passed = sum(comparison_results) >= int(contract["minimum_pass_count"])
            aggregate_value = float(sum(comparison_results))
        elif aggregation == "at_least_fraction":
            aggregate_value = sum(comparison_results) / len(comparison_results)
            passed = aggregate_value >= float(contract["minimum_pass_fraction"])
        else:
            passed = all(comparison_results)
        if not passed:
            errors.append(
                f"metric contract {contract_id} failed: path={_metric_path_text(path)} "
                f"aggregation={aggregation} operator={contract.get('operator')} "
                f"observed={aggregate_value if aggregate_value is not None else numeric_values[:8]}"
            )
    return {
        "contract_id": contract_id,
        "artifact_id": str(contract.get("artifact_id", "") or ""),
        "metric_path": path,
        "operator": str(contract.get("operator", "") or ""),
        "aggregation": aggregation,
        "required": contract.get("required") is True,
        "n_resolved_values": len(numeric_values),
        "resolved_values_preview": numeric_values[:12],
        "aggregate_value": aggregate_value,
        "n_comparisons_passed": sum(comparison_results),
        "n_comparisons": len(comparison_results),
        "passed": passed,
        "errors": errors,
        "source_anchors": list(contract.get("source_anchors", []) or []),
        "acceptance_authority_kind": str(
            contract.get("acceptance_authority_kind", "") or ""
        ),
        "acceptance_authority_rationale": str(
            contract.get("acceptance_authority_rationale", "") or ""
        ),
        "gate_field_authority_mode": str(
            contract.get("gate_field_authority_mode", "") or ""
        ),
        "gate_field_authorities": [
            dict(row)
            for row in contract.get("gate_field_authorities", []) or []
            if isinstance(row, Mapping)
        ],
        "requirement_id": str(contract.get("requirement_id", "") or ""),
        "authority_requirement_fingerprint": str(
            contract.get("authority_requirement_fingerprint", "") or ""
        ),
        "authority_requirement_set_id": str(
            contract.get("authority_requirement_set_id", "") or ""
        ),
        "proof_evidence_status": GENERATED_METRIC_CONTRACT_NOT_PROOF_EVIDENCE,
    }


def _generated_metric_contract_authority_errors(
    contracts: Any,
    *,
    authoritative_requirements: Any,
    target_subsystem: str,
    required_artifact_ids: Sequence[str],
    require_authoritative_requirements: bool,
) -> list[str]:
    errors = validate_generated_metric_requirements(
        authoritative_requirements,
        required_target_subsystems=(target_subsystem,)
        if require_authoritative_requirements and target_subsystem
        else (),
    )
    if not isinstance(contracts, list) or not isinstance(
        authoritative_requirements, list
    ):
        return errors
    relevant = generated_metric_requirements_for_subsystem(
        authoritative_requirements,
        target_subsystem=target_subsystem,
    )
    requirements_by_id = {
        str(row.get("requirement_id", "") or "").strip(): row
        for row in relevant
        if str(row.get("requirement_id", "") or "").strip()
    }
    covered_pairs: set[tuple[str, str]] = set()
    covered_requirements: set[str] = set()
    for index, raw_contract in enumerate(contracts):
        if not isinstance(raw_contract, Mapping):
            continue
        prefix = f"metric_contracts[{index}]"
        requirement_id = str(
            raw_contract.get("requirement_id", "") or ""
        ).strip()
        is_required = raw_contract.get("required") is True
        if not requirement_id:
            if is_required and require_authoritative_requirements:
                errors.append(
                    f"{prefix}.requirement_id must bind a required upstream "
                    "empirical metric requirement"
                )
            continue
        requirement = requirements_by_id.get(requirement_id)
        if requirement is None:
            errors.append(
                f"{prefix}.requirement_id is not an authoritative requirement "
                f"for {target_subsystem or '<missing subsystem>'}: {requirement_id}"
            )
            continue
        mismatches = _metric_authority_mismatches(raw_contract, requirement)
        for field in mismatches:
            errors.append(
                f"{prefix}.{field} must copy authoritative requirement "
                f"{requirement_id} unchanged"
            )
        if not mismatches:
            covered_requirements.add(requirement_id)
            artifact_id = str(raw_contract.get("artifact_id", "") or "").strip()
            if artifact_id:
                covered_pairs.add((artifact_id, requirement_id))
            expected_fingerprint = stable_hash(dict(requirement))
            fingerprint = str(
                raw_contract.get("authority_requirement_fingerprint", "") or ""
            ).strip()
            if fingerprint and fingerprint != expected_fingerprint:
                errors.append(
                    f"{prefix}.authority_requirement_fingerprint does not match "
                    f"authoritative requirement {requirement_id}"
                )
    required_ids = {
        str(row.get("requirement_id", "") or "").strip()
        for row in relevant
        if row.get("required") is True
        and str(row.get("requirement_id", "") or "").strip()
    }
    if require_authoritative_requirements:
        missing_requirements = required_ids - covered_requirements
        if missing_requirements:
            errors.append(
                "metric_contracts must bind every authoritative required metric "
                "requirement; missing: " + ", ".join(sorted(missing_requirements))
            )
        missing_pairs = {
            (artifact_id, requirement_id)
            for artifact_id in required_artifact_ids
            for requirement_id in required_ids
        } - covered_pairs
        if missing_pairs:
            errors.append(
                "metric_contracts must bind every required artifact/requirement "
                "pair; missing: "
                + ", ".join(
                    f"{artifact_id}->{requirement_id}"
                    for artifact_id, requirement_id in sorted(missing_pairs)
                )
            )
    return errors


def _metric_authority_mismatches(
    contract: Mapping[str, Any],
    requirement: Mapping[str, Any],
) -> list[str]:
    mismatches: list[str] = []
    for field in (
        "metric_semantics",
        "measurement_protocol",
        "operator",
        "aggregation",
        "required",
        "source_anchors",
        "acceptance_authority_kind",
        "acceptance_authority_rationale",
        "gate_field_authority_mode",
        "gate_field_authorities",
    ):
        if _normalized_authority_value(contract.get(field)) != (
            _normalized_authority_value(requirement.get(field))
        ):
            mismatches.append(field)
    for field in (
        "threshold",
        "lower",
        "upper",
        "tolerance",
        "minimum_pass_count",
        "minimum_pass_fraction",
        "required_runtime_replicates",
    ):
        if not _authority_numeric_values_equal(
            contract.get(field),
            requirement.get(field),
        ):
            mismatches.append(field)
    return mismatches


def _normalized_authority_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_normalized_authority_value(item) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): _normalized_authority_value(item)
            for key, item in value.items()
        }
    return value


def _authority_numeric_values_equal(left: Any, right: Any) -> bool:
    if left in (None, "") and right in (None, ""):
        return True
    if not _finite_number(left) or not _finite_number(right):
        return left == right
    return float(left) == float(right)


def _metric_comparison_shape_errors(
    value: Mapping[str, Any],
    *,
    prefix: str,
) -> list[str]:
    errors: list[str] = []
    metric_value_kind = _generated_metric_value_kind(value)
    if metric_value_kind not in GENERATED_METRIC_VALUE_KINDS:
        errors.append(
            f"{prefix}.metric_value_kind must be one of "
            + ", ".join(GENERATED_METRIC_VALUE_KINDS)
        )
    operator = str(value.get("operator", "") or "").strip()
    if operator not in GENERATED_METRIC_CONTRACT_OPERATORS:
        errors.append(
            f"{prefix}.operator must be one of "
            + ", ".join(GENERATED_METRIC_CONTRACT_OPERATORS)
        )
    aggregation = str(value.get("aggregation", "") or "").strip()
    if aggregation not in GENERATED_METRIC_CONTRACT_AGGREGATIONS:
        errors.append(
            f"{prefix}.aggregation must be one of "
            + ", ".join(GENERATED_METRIC_CONTRACT_AGGREGATIONS)
        )
    tolerance = value.get("tolerance")
    if not _finite_number(tolerance) or float(tolerance) < 0.0:
        errors.append(f"{prefix}.tolerance must be a finite nonnegative number")
    if operator == "between":
        lower = value.get("lower")
        upper = value.get("upper")
        if not _finite_number(lower):
            errors.append(f"{prefix}.lower must be a finite number for between")
        if not _finite_number(upper):
            errors.append(f"{prefix}.upper must be a finite number for between")
        if (
            _finite_number(lower)
            and _finite_number(upper)
            and float(lower) > float(upper)
        ):
            errors.append(f"{prefix}.lower must be <= upper")
    elif not _finite_number(value.get("threshold")):
        errors.append(
            f"{prefix}.threshold must be a finite number for operator "
            f"{operator or '<missing>'}"
        )
    if aggregation == "at_least_count":
        count = value.get("minimum_pass_count")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            errors.append(
                f"{prefix}.minimum_pass_count must be a positive integer for "
                "at_least_count"
            )
    if aggregation == "at_least_fraction":
        fraction = value.get("minimum_pass_fraction")
        if not _finite_number(fraction) or not 0.0 <= float(fraction) <= 1.0:
            errors.append(
                f"{prefix}.minimum_pass_fraction must be in [0,1] for "
                "at_least_fraction"
            )
    if metric_value_kind == "boolean":
        if operator != "==":
            errors.append(
                f"{prefix}.boolean metric_value_kind requires operator =="
            )
        if not _same_finite_number(value.get("threshold"), 1):
            errors.append(
                f"{prefix}.boolean metric_value_kind requires threshold=1"
            )
        if not _same_finite_number(value.get("tolerance"), 0):
            errors.append(
                f"{prefix}.boolean metric_value_kind requires tolerance=0"
            )
        if value.get("lower") not in (None, "") or value.get("upper") not in (
            None,
            "",
        ):
            errors.append(
                f"{prefix}.boolean metric_value_kind requires null lower/upper"
            )
        if aggregation in {"mean", "min", "max"}:
            errors.append(
                f"{prefix}.boolean metric_value_kind cannot use {aggregation} "
                "aggregation"
            )
    return errors


def _metric_source_anchor_errors(
    value: Mapping[str, Any],
    *,
    prefix: str,
) -> list[str]:
    source_anchors = value.get("source_anchors")
    if not isinstance(source_anchors, list) or not source_anchors:
        return [f"{prefix}.source_anchors must contain at least one id"]
    if any(
        not isinstance(anchor, str) or not anchor.strip()
        for anchor in source_anchors
    ):
        return [f"{prefix}.source_anchors entries must be nonempty strings"]
    return []


def _resolve_generated_metric_path(
    value: Any,
    path: Sequence[Any],
) -> tuple[list[Any], str]:
    current = [value]
    for index, segment in enumerate(path):
        next_values: list[Any] = []
        for item in current:
            if segment == "*":
                if isinstance(item, Mapping):
                    next_values.extend(item.values())
                elif isinstance(item, (list, tuple)):
                    next_values.extend(item)
                continue
            if isinstance(item, Mapping):
                key = str(segment)
                if key in item:
                    next_values.append(item[key])
                continue
            if isinstance(item, (list, tuple)) and isinstance(segment, int):
                if 0 <= segment < len(item):
                    next_values.append(item[segment])
        if not next_values:
            return [], (
                f"metric_path {_metric_path_text(path)} resolved no values at "
                f"segment {index}:{segment}"
            )
        current = next_values
    return current, ""


def _metric_numeric_values(
    values: Sequence[Any],
    *,
    metric_value_kind: str = "numeric",
) -> tuple[list[float], str]:
    numeric: list[float] = []
    stack = list(values)
    while stack:
        value = stack.pop(0)
        if isinstance(value, (list, tuple)):
            stack[0:0] = list(value)
            continue
        if metric_value_kind == "boolean":
            if isinstance(value, bool):
                numeric.append(1.0 if value else 0.0)
                continue
            if _finite_number(value) and float(value) in {0.0, 1.0}:
                numeric.append(float(value))
                continue
            return [], (
                "metric_path resolved a value outside the declared boolean "
                "bool-or-0/1 representation"
            )
        if not _finite_number(value):
            return [], "metric_path resolved a nonnumeric or nonfinite value"
        numeric.append(float(value))
    if not numeric:
        return [], "metric_path resolved no numeric values"
    return numeric, ""


def _generated_metric_value_kind(value: Mapping[str, Any]) -> str:
    """Default legacy packets to numeric while new authoring schemas stay typed."""

    return str(value.get("metric_value_kind", "numeric") or "numeric").strip()


def _metric_comparison_passes(value: float, contract: Mapping[str, Any]) -> bool:
    operator = str(contract.get("operator", "") or "")
    tolerance = float(contract.get("tolerance", 0.0) or 0.0)
    if operator == "between":
        return (
            float(contract["lower"]) - tolerance
            <= value
            <= float(contract["upper"]) + tolerance
        )
    threshold = float(contract["threshold"])
    if operator == "<=":
        return value <= threshold + tolerance
    if operator == "<":
        return value < threshold + tolerance
    if operator == ">=":
        return value >= threshold - tolerance
    if operator == ">":
        return value > threshold - tolerance
    if operator == "==":
        return abs(value - threshold) <= tolerance
    return False


def _metric_path_text(path: Sequence[Any]) -> str:
    return "/" + "/".join(str(segment) for segment in path)


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )
