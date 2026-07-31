from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

from .fingerprint import stable_hash


ESTIMATOR_REQUEST_BINDINGS = (
    "per_replicate_data",
    "fixed_before_all_replicates",
    "derived_once_from_frozen_design",
    "runtime_control",
    "other_explicit",
)
ESTIMATOR_SAMPLE_SIZE_RATE_SCALES = (
    "polynomial_log_n",
    "constant",
    "not_indexed",
    "other",
)


def estimator_interface_contract_id(value: Mapping[str, Any]) -> str:
    return "estimator_interface_contract:" + stable_hash(dict(value))[:20]


def sample_size_rate_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "scale",
            "index_symbol",
            "polynomial_exponent",
            "log_exponent",
            "contributions",
        ],
        "properties": {
            "scale": {
                "type": "string",
                "enum": list(ESTIMATOR_SAMPLE_SIZE_RATE_SCALES),
            },
            "index_symbol": {"type": "string", "minLength": 1},
            "polynomial_exponent": {"type": "number"},
            "log_exponent": {"type": "number"},
            "contributions": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "quantity",
                        "polynomial_exponent",
                        "log_exponent",
                        "justification_ref",
                    ],
                    "properties": {
                        "quantity": {"type": "string", "minLength": 1},
                        "polynomial_exponent": {"type": "number"},
                        "log_exponent": {"type": "number"},
                        "justification_ref": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
            },
        },
    }


def estimator_interface_contract_json_schema(
    *,
    require_typed_rate: bool = False,
) -> dict[str, Any]:
    response_required = [
        "name",
        "meaning",
        "normalization",
        "sample_size_order",
        "derivation_ref",
    ]
    if require_typed_rate:
        response_required.append("sample_size_rate")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["request_fields", "response_fields"],
        "properties": {
            "request_fields": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "meaning", "binding"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "meaning": {"type": "string", "minLength": 1},
                        "binding": {
                            "type": "string",
                            "enum": list(ESTIMATOR_REQUEST_BINDINGS),
                        },
                    },
                },
            },
            "response_fields": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": response_required,
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "meaning": {"type": "string", "minLength": 1},
                        "normalization": {"type": "string", "minLength": 1},
                        "sample_size_order": {"type": "string", "minLength": 1},
                        "sample_size_rate": sample_size_rate_json_schema(),
                        "derivation_ref": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    }


def theory_semantic_reference_ids(theory_packet: Mapping[str, Any]) -> set[str]:
    derivation = theory_packet.get("theory_derivation_packet", {})
    if not isinstance(derivation, Mapping):
        return set()
    references: set[str] = set()
    for collection, field in (
        ("derivation_steps", "id"),
        ("equation_chain", "step_id"),
        ("sanity_checks", "id"),
    ):
        for row in derivation.get(collection, []) or []:
            if not isinstance(row, Mapping):
                continue
            value = str(row.get(field, "") or "").strip()
            if value:
                references.add(value)
    return references


def estimator_interface_contract_errors(
    value: Any,
    *,
    label: str,
    required: bool,
    allowed_derivation_refs: set[str] | None = None,
    require_typed_rate: bool = False,
) -> list[str]:
    if not isinstance(value, Mapping):
        return [f"{label} missing estimator_interface_contract"] if required else []

    errors: list[str] = []
    for collection_name in ("request_fields", "response_fields"):
        rows = value.get(collection_name)
        if not isinstance(rows, list) or not rows:
            errors.append(
                f"{label} estimator_interface_contract {collection_name} "
                "must be a nonempty list"
            )
            continue
        names: list[str] = []
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(
                    f"{label} estimator_interface_contract {collection_name} "
                    "entries must be objects"
                )
                continue
            for field in ("name", "meaning"):
                if not str(row.get(field, "") or "").strip():
                    errors.append(
                        f"{label} estimator_interface_contract {collection_name} "
                        f"entry {index} missing {field}"
                    )
            name = str(row.get("name", "") or "").strip()
            if name:
                names.append(name)

            if collection_name == "request_fields":
                binding = str(row.get("binding", "") or "").strip()
                if binding not in ESTIMATOR_REQUEST_BINDINGS:
                    errors.append(
                        f"{label} estimator_interface_contract request field {index} "
                        "has invalid binding"
                    )
                continue

            for field in ("normalization", "sample_size_order", "derivation_ref"):
                if not str(row.get(field, "") or "").strip():
                    errors.append(
                        f"{label} estimator_interface_contract response field "
                        f"{index} missing {field}"
                    )
            errors.extend(
                sample_size_rate_errors(
                    row.get("sample_size_rate"),
                    label=(
                        f"{label} estimator_interface_contract response field "
                        f"{index} sample_size_rate"
                    ),
                    required=require_typed_rate,
                    allowed_derivation_refs=allowed_derivation_refs,
                )
            )
            derivation_ref = str(row.get("derivation_ref", "") or "").strip()
            if (
                derivation_ref
                and allowed_derivation_refs is not None
                and derivation_ref not in allowed_derivation_refs
            ):
                allowed = sorted(allowed_derivation_refs)
                allowed_preview = ", ".join(allowed[:16]) or "<none>"
                if len(allowed) > 16:
                    allowed_preview += f", ... ({len(allowed)} total)"
                errors.append(
                    f"{label} estimator_interface_contract response field {index} "
                    f"has unresolved derivation_ref {derivation_ref}; choose exactly "
                    f"one allowed reference id from: {allowed_preview}"
                )
        if len(names) != len(set(names)):
            errors.append(
                f"{label} estimator_interface_contract {collection_name} "
                "field names must be unique"
            )
    return errors


def sample_size_rate_errors(
    value: Any,
    *,
    label: str,
    required: bool,
    allowed_derivation_refs: set[str] | None = None,
) -> list[str]:
    if not isinstance(value, Mapping):
        return [f"{label} is required"] if required else []
    errors: list[str] = []
    scale = str(value.get("scale", "") or "").strip()
    if scale not in ESTIMATOR_SAMPLE_SIZE_RATE_SCALES:
        errors.append(f"{label} has invalid scale")
    if not str(value.get("index_symbol", "") or "").strip():
        errors.append(f"{label} missing index_symbol")
    exponents: dict[str, float] = {}
    for field in ("polynomial_exponent", "log_exponent"):
        raw = value.get(field)
        if (
            isinstance(raw, bool)
            or not isinstance(raw, (int, float))
            or not math.isfinite(float(raw))
        ):
            errors.append(f"{label} {field} must be a finite number")
            continue
        exponents[field] = float(raw)
    if scale in {"constant", "not_indexed"} and any(
        abs(exponent) > 1e-12 for exponent in exponents.values()
    ):
        errors.append(f"{label} {scale} scale must have zero exponents")
    contributions = value.get("contributions")
    contribution_exponents: list[tuple[float, float]] = []
    if not isinstance(contributions, list) or not contributions:
        errors.append(f"{label} contributions must be a nonempty list")
        contributions = []
    for index, contribution in enumerate(contributions):
        if not isinstance(contribution, Mapping):
            errors.append(f"{label} contribution {index} must be an object")
            continue
        if not str(contribution.get("quantity", "") or "").strip():
            errors.append(f"{label} contribution {index} missing quantity")
        justification_ref = str(
            contribution.get("justification_ref", "") or ""
        ).strip()
        if not justification_ref:
            errors.append(
                f"{label} contribution {index} missing justification_ref"
            )
        elif (
            allowed_derivation_refs is not None
            and justification_ref not in allowed_derivation_refs
        ):
            errors.append(
                f"{label} contribution {index} has unresolved "
                f"justification_ref {justification_ref}"
            )
        row_exponents: list[float] = []
        for field in ("polynomial_exponent", "log_exponent"):
            raw = contribution.get(field)
            if (
                isinstance(raw, bool)
                or not isinstance(raw, (int, float))
                or not math.isfinite(float(raw))
            ):
                errors.append(
                    f"{label} contribution {index} {field} must be a finite number"
                )
                break
            row_exponents.append(float(raw))
        if len(row_exponents) == 2:
            contribution_exponents.append((row_exponents[0], row_exponents[1]))
    if len(exponents) == 2 and contribution_exponents:
        claimed = (
            exponents["polynomial_exponent"],
            exponents["log_exponent"],
        )
        computed = (
            sum(row[0] for row in contribution_exponents),
            sum(row[1] for row in contribution_exponents),
        )
        if any(
            abs(observed - expected) > 1e-9
            for observed, expected in zip(claimed, computed, strict=True)
        ):
            errors.append(
                f"{label} exponents must equal the sum of signed contributions"
            )
    return errors


def normalize_theory_estimator_interface_contracts(body: dict[str, Any]) -> None:
    raw_specs = body.get("estimator_specs", [])
    if not isinstance(raw_specs, list):
        return
    normalized_specs: list[Any] = []
    for raw_spec in raw_specs:
        if not isinstance(raw_spec, Mapping):
            normalized_specs.append(raw_spec)
            continue
        spec = dict(raw_spec)
        contract = spec.get("estimator_interface_contract")
        if isinstance(contract, Mapping):
            exact_contract = deepcopy(dict(contract))
            spec["estimator_interface_contract"] = exact_contract
            spec["estimator_interface_contract_id"] = (
                estimator_interface_contract_id(exact_contract)
            )
        normalized_specs.append(spec)
    body["estimator_specs"] = normalized_specs


def theory_estimator_interface_contracts(
    theory_packet: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for index, raw_spec in enumerate(theory_packet.get("estimator_specs", []) or []):
        if not isinstance(raw_spec, Mapping):
            continue
        estimator_id = str(raw_spec.get("id", "") or "").strip()
        contract = raw_spec.get("estimator_interface_contract")
        if not estimator_id or not isinstance(contract, Mapping):
            continue
        exact_contract = deepcopy(dict(contract))
        rows[estimator_id] = {
            "estimator_id": estimator_id,
            "contract": exact_contract,
            "contract_id": estimator_interface_contract_id(exact_contract),
            "source_ref": (
                f"theory#/estimator_specs/{index}/estimator_interface_contract"
            ),
        }
    return rows
