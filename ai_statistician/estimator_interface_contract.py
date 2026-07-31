from __future__ import annotations

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


def estimator_interface_contract_id(value: Mapping[str, Any]) -> str:
    return "estimator_interface_contract:" + stable_hash(dict(value))[:20]


def estimator_interface_contract_json_schema() -> dict[str, Any]:
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
                    "required": [
                        "name",
                        "meaning",
                        "normalization",
                        "sample_size_order",
                        "derivation_ref",
                    ],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "meaning": {"type": "string", "minLength": 1},
                        "normalization": {"type": "string", "minLength": 1},
                        "sample_size_order": {"type": "string", "minLength": 1},
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
