from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


QUALITY_CONTROL_FIELDS = (
    "resource_contract_ids",
    "required_quality_signals",
    "quality_gates",
    "response_validation_signals",
    "stop_conditions",
)
PROOF_STATE_RESOURCE_CONTRACT_ID_BY_TARGET = {
    "lean4": "lean_lsp:proof_state_feedback",
    "rocq": "rocq_lsp_serapi:proof_state_feedback",
    "isabelle": "isabelle_sledgehammer_afp:proof_state_feedback",
    "agda": "agda_search_auto:proof_state_feedback",
}
PROVER_RESOURCE_CONTRACT_TARGETS = {
    "lean_lsp": "lean4",
    "lean_lsp_mcp": "lean4",
    "local_lake_lean": "lean4",
    "leandojo_reprover": "lean4",
    "rocq_lsp_serapi": "rocq",
    "isabelle_sledgehammer_afp": "isabelle",
    "agda_search_auto": "agda",
}


def normalize_target_prover_family(value: object) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    aliases = {
        "lean": "lean4",
        "lean_4": "lean4",
        "lean4": "lean4",
        "coq": "rocq",
        "coq8": "rocq",
        "coq_8": "rocq",
        "coq_rocq": "rocq",
        "rocq_coq": "rocq",
        "rocq": "rocq",
        "isabelle": "isabelle",
        "isabelle_hol": "isabelle",
        "agda": "agda",
        "other": "other",
    }
    return aliases.get(key, key)


def quality_control_payload_from_mapping(
    value: Mapping[str, object],
) -> dict[str, tuple[str, ...]]:
    return {
        field_name: _str_tuple(value.get(field_name, ()))
        for field_name in QUALITY_CONTROL_FIELDS
        if _str_tuple(value.get(field_name, ()))
    }


def project_quality_control_payload_to_target(
    payload: Mapping[str, object],
    *,
    target_prover_family: str,
) -> dict[str, tuple[str, ...]]:
    target_key = normalize_target_prover_family(target_prover_family)
    projected = quality_control_payload_from_mapping(payload)
    if not target_key or target_key == "other" or not projected:
        return projected
    resource_contract_ids = projected.get("resource_contract_ids", ())
    if resource_contract_ids:
        projected["resource_contract_ids"] = tuple(
            dict.fromkeys(
                project_resource_contract_id_to_target(
                    contract_id,
                    target_prover_family=target_key,
                )
                for contract_id in resource_contract_ids
            )
        )
    return projected


def project_resource_contract_id_to_target(
    contract_id: str,
    *,
    target_prover_family: str,
) -> str:
    target_key = normalize_target_prover_family(target_prover_family)
    contract_target = resource_contract_target_prover_family(contract_id)
    if not contract_target or contract_target == target_key:
        return contract_id
    if resource_contract_is_proof_state_feedback(contract_id):
        return PROOF_STATE_RESOURCE_CONTRACT_ID_BY_TARGET.get(
            target_key,
            contract_id,
        )
    return contract_id


def resource_contract_target_prover_family(contract_id: str) -> str:
    key = str(contract_id or "").strip().lower()
    if not key:
        return ""
    head = key.split(":", 1)[0]
    if head in PROVER_RESOURCE_CONTRACT_TARGETS:
        return PROVER_RESOURCE_CONTRACT_TARGETS[head]
    for resource_id, target_family in PROVER_RESOURCE_CONTRACT_TARGETS.items():
        if key.startswith(f"{resource_id}:"):
            return target_family
    return ""


def resource_contract_is_proof_state_feedback(contract_id: str) -> bool:
    key = str(contract_id or "").strip().lower()
    return "proof_state_feedback" in key or key in PROVER_RESOURCE_CONTRACT_TARGETS


def quality_control_projection_trace(
    *,
    source_controls: Mapping[str, object],
    projected_controls: Mapping[str, object],
    target_prover_family: str,
) -> dict[str, object]:
    source_contract_ids = _str_tuple(source_controls.get("resource_contract_ids", ()))
    projected_contract_ids = _str_tuple(
        projected_controls.get("resource_contract_ids", ())
    )
    return {
        "projection_kind": "target_prover_quality_control_projection",
        "target_prover_family": normalize_target_prover_family(target_prover_family),
        "source_resource_contract_ids": list(source_contract_ids),
        "projected_resource_contract_ids": list(projected_contract_ids),
        "changed_resource_contract_ids": source_contract_ids != projected_contract_ids,
        "projection_boundary": (
            "Quality-control resource ids are adapter-routing requirements, "
            "not theorem proof evidence; target prover packets must use "
            "target-compatible prover-feedback resources."
        ),
    }


def _str_tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,) if values else tuple()
    if not isinstance(values, (list, tuple, set)):
        return tuple()
    return tuple(dict.fromkeys(str(item) for item in values if str(item)))
