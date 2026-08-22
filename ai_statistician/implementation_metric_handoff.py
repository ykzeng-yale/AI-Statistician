from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from .estimator_interface_contract import (
    estimator_interface_contract_errors,
    project_executable_estimator_interface_contract,
)
from .fingerprint import stable_hash


ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_KIND = (
    "RuntimeAcceptedImplementationInterfaceHandoff"
)
ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_NOT_EVIDENCE = (
    "ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_NOT_EMPIRICAL_OR_PROOF_EVIDENCE"
)
ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_BOUNDARY = (
    "This handoff records the interface of independently reviewed executable code. "
    "It excludes source text and every execution result so later confirmatory metric "
    "authoring cannot tune gates to observed values. It is implementation lineage, "
    "not confirmatory empirical acceptance or theorem proof evidence."
)

_FORBIDDEN_RESULT_KEYS = frozenset(
    {
        "exact_source_code",
        "exact_smoke_result",
        "exact_result",
        "result",
        "results",
        "returned_metrics",
        "metric_evaluations",
    }
)
_HANDOFF_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "source_accepted_algorithm_handoff_id",
        "source_accepted_algorithm_handoff_hash",
        "question_id",
        "theory_packet_id",
        "algorithm_sandbox_manifest_id",
        "algorithm_sandbox_manifest_hash",
        "semantic_review_execution_id",
        "semantic_review_packet_id",
        "semantic_review_packet_hash",
        "implementation_interfaces",
        "exact_source_included",
        "execution_results_included",
        "raw_execution_artifacts_included",
        "runtime_selected_semantics",
        "proof_evidence_status",
        "boundary",
        "handoff_id",
    }
)
_INTERFACE_ROW_FIELDS = frozenset(
    {
        "estimator_id",
        "language",
        "dependencies",
        "exact_source_hash",
        "source_estimator_interface_contract_id",
        "estimator_interface_contract_id",
        "estimator_interface_contract",
        "estimator_interface_contract_authority",
    }
)


def _nested_forbidden_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        found = {
            str(key)
            for key in value
            if str(key) in _FORBIDDEN_RESULT_KEYS
        }
        for child in value.values():
            found.update(_nested_forbidden_keys(child))
        return found
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        found: set[str] = set()
        for child in value:
            found.update(_nested_forbidden_keys(child))
        return found
    return set()


def _interface_contract_shape_errors(
    contract: Mapping[str, Any],
    *,
    label: str,
) -> list[str]:
    errors: list[str] = []
    unexpected = sorted(set(contract) - {"request_fields", "response_fields"})
    if unexpected:
        errors.append(f"{label} has unexpected fields: {unexpected}")
    for index, row in enumerate(contract.get("request_fields", []) or []):
        if not isinstance(row, Mapping):
            continue
        unexpected = sorted(set(row) - {"name", "meaning", "binding"})
        if unexpected:
            errors.append(
                f"{label} request field {index} has unexpected fields: {unexpected}"
            )
    response_fields = {"name", "meaning", "normalization", "derivation_ref"}
    for index, row in enumerate(contract.get("response_fields", []) or []):
        if not isinstance(row, Mapping):
            continue
        unexpected = sorted(set(row) - response_fields)
        if unexpected:
            errors.append(
                f"{label} response field {index} has unexpected fields: {unexpected}"
            )
    return errors


def build_accepted_implementation_interface_handoff(
    accepted_algorithm_handoff: Mapping[str, Any],
) -> dict[str, Any]:
    """Project an accepted algorithm handoff without source or result leakage."""

    interface_rows: list[dict[str, Any]] = []
    for raw_row in accepted_algorithm_handoff.get(
        "exact_algorithm_artifacts", []
    ) or []:
        if not isinstance(raw_row, Mapping):
            continue
        source_interface_contract = raw_row.get(
            "estimator_interface_contract", {}
        )
        if (
            not isinstance(source_interface_contract, Mapping)
            or not source_interface_contract
        ):
            continue
        interface_contract = project_executable_estimator_interface_contract(
            source_interface_contract
        )
        interface_rows.append(
            {
                "estimator_id": str(raw_row.get("estimator_id", "") or ""),
                "language": str(raw_row.get("language", "") or ""),
                "dependencies": [
                    str(value)
                    for value in raw_row.get("dependencies", []) or []
                    if str(value).strip()
                ],
                "exact_source_hash": str(
                    raw_row.get("exact_source_hash", "") or ""
                ),
                "source_estimator_interface_contract_id": str(
                    raw_row.get("estimator_interface_contract_id", "")
                    or ""
                ),
                "estimator_interface_contract_id": (
                    "estimator_interface_contract:"
                    + stable_hash(interface_contract)[:20]
                ),
                "estimator_interface_contract": deepcopy(
                    dict(interface_contract)
                ),
                "estimator_interface_contract_authority": deepcopy(
                    dict(
                        raw_row.get(
                            "estimator_interface_contract_authority", {}
                        )
                        or {}
                    )
                ),
            }
        )
    payload = {
        "schema_version": 1,
        "artifact_kind": ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_KIND,
        "source_accepted_algorithm_handoff_id": str(
            accepted_algorithm_handoff.get("handoff_id", "") or ""
        ),
        "source_accepted_algorithm_handoff_hash": stable_hash(
            accepted_algorithm_handoff
        ),
        "question_id": str(
            accepted_algorithm_handoff.get("question_id", "") or ""
        ),
        "theory_packet_id": str(
            accepted_algorithm_handoff.get("theory_packet_id", "") or ""
        ),
        "algorithm_sandbox_manifest_id": str(
            accepted_algorithm_handoff.get(
                "algorithm_sandbox_manifest_id", ""
            )
            or ""
        ),
        "algorithm_sandbox_manifest_hash": str(
            accepted_algorithm_handoff.get(
                "algorithm_sandbox_manifest_hash", ""
            )
            or ""
        ),
        "semantic_review_execution_id": str(
            accepted_algorithm_handoff.get(
                "semantic_review_execution_id", ""
            )
            or ""
        ),
        "semantic_review_packet_id": str(
            accepted_algorithm_handoff.get("semantic_review_packet_id", "")
            or ""
        ),
        "semantic_review_packet_hash": str(
            accepted_algorithm_handoff.get(
                "semantic_review_packet_hash", ""
            )
            or ""
        ),
        "implementation_interfaces": interface_rows,
        "exact_source_included": False,
        "execution_results_included": False,
        "raw_execution_artifacts_included": False,
        "runtime_selected_semantics": False,
        "proof_evidence_status": (
            ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_NOT_EVIDENCE
        ),
        "boundary": ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_BOUNDARY,
    }
    payload["handoff_id"] = (
        "accepted_implementation_interface_handoff:"
        + stable_hash(payload)[:20]
    )
    return payload


def accepted_implementation_interface_handoff_errors(
    handoff: Mapping[str, Any],
    *,
    question_id: str,
    theory_packet_id: str,
) -> list[str]:
    errors: list[str] = []
    unexpected_handoff_fields = sorted(set(handoff) - _HANDOFF_FIELDS)
    if unexpected_handoff_fields:
        errors.append(
            "accepted implementation interface has unexpected fields: "
            f"{unexpected_handoff_fields}"
        )
    if handoff.get("schema_version") != 1:
        errors.append("accepted implementation interface schema version mismatch")
    if handoff.get("artifact_kind") != (
        ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_KIND
    ):
        errors.append("accepted implementation interface handoff kind mismatch")
    if str(handoff.get("question_id", "") or "") != str(question_id):
        errors.append("accepted implementation interface question mismatch")
    if str(handoff.get("theory_packet_id", "") or "") != str(
        theory_packet_id
    ):
        errors.append("accepted implementation interface theory mismatch")
    for field in (
        "handoff_id",
        "source_accepted_algorithm_handoff_id",
        "source_accepted_algorithm_handoff_hash",
        "algorithm_sandbox_manifest_id",
        "algorithm_sandbox_manifest_hash",
        "semantic_review_execution_id",
        "semantic_review_packet_id",
        "semantic_review_packet_hash",
    ):
        if not str(handoff.get(field, "") or "").strip():
            errors.append(f"accepted implementation interface missing {field}")
    for field in (
        "exact_source_included",
        "execution_results_included",
        "raw_execution_artifacts_included",
    ):
        if handoff.get(field) is not False:
            errors.append(f"accepted implementation interface requires {field}=false")
    if handoff.get("runtime_selected_semantics") is not False:
        errors.append(
            "accepted implementation interface requires runtime_selected_semantics=false"
        )
    if handoff.get("proof_evidence_status") != (
        ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_NOT_EVIDENCE
    ):
        errors.append(
            "accepted implementation interface proof evidence status mismatch"
        )
    if handoff.get("boundary") != (
        ACCEPTED_IMPLEMENTATION_INTERFACE_HANDOFF_BOUNDARY
    ):
        errors.append("accepted implementation interface boundary mismatch")
    handoff_identity_payload = dict(handoff)
    handoff_identity_payload.pop("handoff_id", None)
    expected_handoff_id = (
        "accepted_implementation_interface_handoff:"
        + stable_hash(handoff_identity_payload)[:20]
    )
    if str(handoff.get("handoff_id", "") or "") != expected_handoff_id:
        errors.append("accepted implementation interface identity hash mismatch")
    rows = handoff.get("implementation_interfaces", [])
    if not isinstance(rows, list) or not rows:
        errors.append("accepted implementation interface requires interface rows")
        rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(
                f"accepted implementation interface row {index} must be an object"
            )
            continue
        unexpected_row_fields = sorted(set(row) - _INTERFACE_ROW_FIELDS)
        if unexpected_row_fields:
            errors.append(
                "accepted implementation interface row "
                f"{index} has unexpected fields: {unexpected_row_fields}"
            )
        for field in (
            "estimator_id",
            "language",
            "exact_source_hash",
            "source_estimator_interface_contract_id",
            "estimator_interface_contract_id",
        ):
            if not str(row.get(field, "") or "").strip():
                errors.append(
                    f"accepted implementation interface row {index} missing {field}"
                )
        contract = row.get("estimator_interface_contract", {})
        if not isinstance(contract, Mapping) or not contract:
            errors.append(
                f"accepted implementation interface row {index} missing contract"
            )
        else:
            errors.extend(
                _interface_contract_shape_errors(
                    contract,
                    label=(
                        "accepted implementation interface row "
                        f"{index} estimator_interface_contract"
                    ),
                )
            )
            errors.extend(
                estimator_interface_contract_errors(
                    contract,
                    label=(
                        "accepted implementation interface row "
                        f"{index}"
                    ),
                    required=True,
                )
            )
            expected_contract_id = (
                "estimator_interface_contract:"
                + stable_hash(contract)[:20]
            )
            if str(
                row.get("estimator_interface_contract_id", "") or ""
            ) != expected_contract_id:
                errors.append(
                    "accepted implementation interface row "
                    f"{index} contract identity hash mismatch"
                )
        authority = row.get("estimator_interface_contract_authority", {})
        if not isinstance(authority, Mapping):
            errors.append(
                f"accepted implementation interface row {index} missing authority"
            )
        else:
            required_authority = {
                "owner_agent",
                "source_theory_packet_id",
                "source_theory_packet_hash",
                "source_estimator_ref",
                "transport_status",
            }
            if set(authority) != required_authority:
                errors.append(
                    "accepted implementation interface row "
                    f"{index} authority fields mismatch"
                )
            if authority.get("owner_agent") != "TheoryDeveloper":
                errors.append(
                    "accepted implementation interface requires "
                    "TheoryDeveloper-owned ABI semantics"
                )
            if str(authority.get("source_theory_packet_id", "") or "") != str(
                theory_packet_id
            ):
                errors.append(
                    "accepted implementation interface authority theory mismatch"
                )
            for field in (
                "source_theory_packet_hash",
                "source_estimator_ref",
                "transport_status",
            ):
                if not str(authority.get(field, "") or "").strip():
                    errors.append(
                        "accepted implementation interface authority missing "
                        + field
                    )
    forbidden = sorted(_nested_forbidden_keys(handoff))
    if forbidden:
        errors.append(
            "accepted implementation interface contains forbidden source/result "
            "fields: " + ", ".join(forbidden)
        )
    return errors
