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
FROZEN_ESTIMATOR_EXECUTION_CONTRACT_SCHEMA_VERSION = 1
FROZEN_ESTIMATOR_EXECUTION_FIELD_TEXT_KEYS = (
    "clause_id",
    "name",
    "meaning",
    "json_type",
    "shape",
    "units",
    "indexing",
    "edge_cases",
)


def estimator_interface_contract_id(value: Mapping[str, Any]) -> str:
    return "estimator_interface_contract:" + stable_hash(dict(value))[:20]


def frozen_estimator_execution_contract_id(value: Mapping[str, Any]) -> str:
    return "frozen_estimator_execution_contract:" + stable_hash(dict(value))[:20]


def frozen_estimator_execution_contract_clause_ids(value: Any) -> set[str]:
    if not isinstance(value, Mapping):
        return set()
    clause_ids: set[str] = set()
    for collection in (
        "request_fields",
        "response_fields",
        "invariants",
        "empirical_claims",
    ):
        for row in value.get(collection, []) or []:
            if not isinstance(row, Mapping):
                continue
            clause_id = str(row.get("clause_id", "") or "").strip()
            if clause_id:
                clause_ids.add(clause_id)
    return clause_ids


def frozen_estimator_execution_contract_empirical_claim_ids(
    value: Any,
) -> set[str]:
    if not isinstance(value, Mapping):
        return set()
    claim_ids: set[str] = set()
    for row in value.get("empirical_claims", []) or []:
        if not isinstance(row, Mapping):
            continue
        clause_id = str(row.get("clause_id", "") or "").strip()
        if clause_id:
            claim_ids.add(clause_id)
    return claim_ids


def frozen_estimator_execution_contract_errors(
    value: Any,
    *,
    label: str,
    required: bool,
) -> list[str]:
    """Validate operator-authored ABI semantics without interpreting statistics."""

    if value in (None, "", [], {}):
        return [f"{label} is required"] if required else []
    if not isinstance(value, Mapping):
        return [f"{label} is required"] if required else []
    errors: list[str] = []
    schema_version = value.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or schema_version
        != FROZEN_ESTIMATOR_EXECUTION_CONTRACT_SCHEMA_VERSION
    ):
        errors.append(f"{label} has unsupported schema_version")
    if not str(value.get("estimator_id", "") or "").strip():
        errors.append(f"{label} missing estimator_id")
    if str(value.get("entrypoint", "") or "").strip() != "run_estimator":
        errors.append(f"{label} entrypoint must be run_estimator")

    all_clause_ids: list[str] = []
    for collection in ("request_fields", "response_fields"):
        rows = value.get(collection)
        if not isinstance(rows, list) or not rows:
            errors.append(f"{label} {collection} must be a nonempty list")
            continue
        field_names: list[str] = []
        for index, row in enumerate(rows):
            row_label = f"{label} {collection}[{index}]"
            if not isinstance(row, Mapping):
                errors.append(f"{row_label} must be an object")
                continue
            for field in FROZEN_ESTIMATOR_EXECUTION_FIELD_TEXT_KEYS:
                if not str(row.get(field, "") or "").strip():
                    errors.append(f"{row_label} missing {field}")
            clause_id = str(row.get("clause_id", "") or "").strip()
            name = str(row.get("name", "") or "").strip()
            if clause_id:
                all_clause_ids.append(clause_id)
            if name:
                field_names.append(name)
            if collection == "request_fields":
                binding = str(row.get("binding", "") or "").strip()
                if binding not in ESTIMATOR_REQUEST_BINDINGS:
                    errors.append(f"{row_label} has invalid binding")
            elif not str(row.get("normalization", "") or "").strip():
                errors.append(f"{row_label} missing normalization")
        if len(field_names) != len(set(field_names)):
            errors.append(f"{label} {collection} field names must be unique")

    invariants = value.get("invariants", [])
    if not isinstance(invariants, list):
        errors.append(f"{label} invariants must be a list")
        invariants = []
    for index, row in enumerate(invariants):
        row_label = f"{label} invariants[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{row_label} must be an object")
            continue
        clause_id = str(row.get("clause_id", "") or "").strip()
        if not clause_id:
            errors.append(f"{row_label} missing clause_id")
        else:
            all_clause_ids.append(clause_id)
        if not str(row.get("meaning", "") or "").strip():
            errors.append(f"{row_label} missing meaning")

    empirical_claims = value.get("empirical_claims", [])
    if not isinstance(empirical_claims, list):
        errors.append(f"{label} empirical_claims must be a list")
        empirical_claims = []
    for index, row in enumerate(empirical_claims):
        row_label = f"{label} empirical_claims[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{row_label} must be an object")
            continue
        clause_id = str(row.get("clause_id", "") or "").strip()
        if not clause_id:
            errors.append(f"{row_label} missing clause_id")
        else:
            all_clause_ids.append(clause_id)
        if not str(row.get("meaning", "") or "").strip():
            errors.append(f"{row_label} missing meaning")
    if len(all_clause_ids) != len(set(all_clause_ids)):
        errors.append(f"{label} clause_id values must be unique")
    return errors


def estimator_interface_contract_json_schema() -> dict[str, Any]:
    response_required = [
        "name",
        "meaning",
        "normalization",
        "derivation_ref",
    ]
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
                        "derivation_ref": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    }


def project_executable_estimator_interface_contract(
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Project legacy contracts onto the canonical cross-agent executable ABI.

    This is a field projection only. It does not infer, repair, or restate any
    mathematical content; rates and theorem claims remain in theory documents.
    """

    def project_rows(rows: Any, keys: tuple[str, ...]) -> list[Any]:
        projected: list[Any] = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, Mapping):
                projected.append(deepcopy(row))
                continue
            projected.append(
                {key: deepcopy(row[key]) for key in keys if key in row}
            )
        return projected

    return {
        "request_fields": project_rows(
            contract.get("request_fields"),
            ("name", "meaning", "binding"),
        ),
        "response_fields": project_rows(
            contract.get("response_fields"),
            ("name", "meaning", "normalization", "derivation_ref"),
        ),
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
        ("claim_index", "id"),
        ("sanity_check_index", "id"),
    ):
        for row in derivation.get(collection, []) or []:
            if not isinstance(row, Mapping):
                continue
            value = str(row.get(field, "") or "").strip()
            if value:
                references.add(value)
    for collection in ("theorem_cards", "lemma_cards"):
        for row in theory_packet.get(collection, []) or []:
            if not isinstance(row, Mapping):
                continue
            value = str(row.get("id", "") or "").strip()
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
    """Validate the executable ABI without interpreting statistical rates.

    Legacy packets may still carry rate metadata. The canonical authoring schema
    no longer emits it, and this validator deliberately does not make it runtime
    authority for mathematics.
    """
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

            for field in ("normalization", "derivation_ref"):
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
            exact_contract = normalize_estimator_interface_contract(contract)
            spec["estimator_interface_contract"] = exact_contract
            spec["estimator_interface_contract_id"] = (
                estimator_interface_contract_id(exact_contract)
            )
        normalized_specs.append(spec)
    body["estimator_specs"] = normalized_specs


def normalize_estimator_interface_contract(
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Copy a model-authored contract without changing its mathematics."""

    return deepcopy(dict(contract))


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
        exact_contract = normalize_estimator_interface_contract(contract)
        rows[estimator_id] = {
            "estimator_id": estimator_id,
            "contract": exact_contract,
            "contract_id": estimator_interface_contract_id(exact_contract),
            "source_ref": (
                f"theory#/estimator_specs/{index}/estimator_interface_contract"
            ),
        }
    return rows
