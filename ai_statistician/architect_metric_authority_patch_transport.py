from __future__ import annotations

from copy import deepcopy
from itertools import product
import json
import re
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .llm_json_repair import SemanticPatchTransport


ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND = (
    "architect_metric_authority_exact_key_decision_patch_v1"
)
_METRIC_GATE_AUTHORITY_ERROR_PATH = re.compile(
    r"empirical_metric_requirements\[(?P<requirement_index>\d+)\]\."
    r"gate_field_authorities\[(?P<authority_index>\d+)\]"
)
_MAX_SOURCE_BINDINGS_PER_DECISION = 8


def metric_gate_authority_resolution_decisions(
    numeric_authority_repair_matrix: Sequence[Mapping[str, Any]],
    *,
    validation_errors: Sequence[Any],
) -> dict[str, dict[str, Any]]:
    """Build exact semantic choices without selecting a repair for the model."""

    error_targets: dict[int, set[int]] = {}
    requirement_error_indices: set[int] = set()
    for raw_error in validation_errors:
        error = str(raw_error)
        path_match = _METRIC_GATE_AUTHORITY_ERROR_PATH.search(error)
        if path_match is None:
            continue
        requirement_index = int(path_match.group("requirement_index"))
        authority_index = int(path_match.group("authority_index"))
        requirement_error_indices.add(requirement_index)
        error_targets.setdefault(requirement_index, set()).add(
            authority_index
        )

    decisions: dict[str, dict[str, Any]] = {}
    for matrix_row in numeric_authority_repair_matrix:
        raw_requirement_index = matrix_row.get("requirement_index", -1)
        if not isinstance(raw_requirement_index, int) or isinstance(
            raw_requirement_index, bool
        ):
            continue
        requirement_index = int(raw_requirement_index)
        if (
            requirement_error_indices
            and requirement_index not in requirement_error_indices
        ):
            continue
        requirement_id = str(
            matrix_row.get("requirement_id", "") or ""
        ).strip()
        if not requirement_id:
            continue
        targeted_authority_indices = error_targets.get(
            requirement_index, set()
        )
        for gate_match in matrix_row.get("numeric_gate_matches", []):
            if not isinstance(gate_match, Mapping):
                continue
            raw_authority_index = gate_match.get(
                "gate_field_authority_entry_index", -1
            )
            if not isinstance(raw_authority_index, int) or isinstance(
                raw_authority_index, bool
            ):
                continue
            authority_index = int(raw_authority_index)
            authority_row_exists = authority_index >= 0
            if (
                authority_row_exists
                and targeted_authority_indices
                and authority_index not in targeted_authority_indices
            ):
                continue
            field = str(gate_match.get("field", "") or "").strip()
            if not field:
                continue
            source_bindings = _source_binding_options(
                requirement_id=requirement_id,
                field=field,
                gate_match=gate_match,
            )
            allowed_resolutions = [
                *(["source_binding"] if source_bindings else []),
                "architect_preregistered_design",
                "diagnostic_only",
                "remove_requirement",
            ]
            decision_id = (
                "metric_gate_authority_decision:"
                + stable_hash([requirement_id, field])[:20]
            )
            decisions[decision_id] = {
                "decision_id": decision_id,
                "requirement_index": requirement_index,
                "requirement_id": requirement_id,
                "field": field,
                "gate_field_authority_entry_index": authority_index,
                "gate_field_authority_expected_index": int(
                    gate_match.get(
                        "gate_field_authority_expected_index",
                        authority_index,
                    )
                ),
                "gate_field_authority_row_exists": authority_row_exists,
                "value": gate_match.get("value"),
                "current_owner": str(
                    gate_match.get("current_field_authority_kind", "")
                    or ""
                ),
                "current_source_anchor_ids": list(
                    dict.fromkeys(
                        str(value).strip()
                        for value in gate_match.get(
                            "current_field_source_anchors", []
                        )
                        if str(value).strip()
                    )
                ),
                "allowed_resolutions": allowed_resolutions,
                "source_binding_options": source_bindings,
                "runtime_application_boundary": (
                    "The model chooses one listed resolution. Runtime applies "
                    "only that exact choice to the named existing requirement "
                    "and field, then reruns the unchanged validator."
                ),
            }
    return decisions


def _source_binding_options(
    *,
    requirement_id: str,
    field: str,
    gate_match: Mapping[str, Any],
) -> list[dict[str, Any]]:
    owner = str(
        gate_match.get("current_field_authority_kind", "") or ""
    ).strip()
    required_kinds = list(
        dict.fromkeys(
            str(value).strip()
            for value in gate_match.get(
                "required_field_anchor_kinds", []
            )
            if str(value).strip()
        )
    )
    numeric_kinds = {
        str(value).strip()
        for value in gate_match.get(
            "required_numeric_authority_kinds", []
        )
        if str(value).strip()
    }
    if not owner or not required_kinds:
        return []

    matching_nodes = _unique_authority_nodes(
        gate_match.get("matching_catalog_nodes", [])
    )
    contextual_nodes = _unique_authority_nodes(
        gate_match.get(
            "current_row_candidates_for_missing_field_anchor_kinds", []
        )
    )
    current_anchor_kinds = gate_match.get(
        "current_field_anchor_kinds", {}
    )
    if isinstance(current_anchor_kinds, Mapping):
        contextual_nodes.extend(
            {
                "anchor_id": str(anchor_id).strip(),
                "authority_kind": str(authority_kind).strip(),
                "explicit_numeric_values": [],
                "content_excerpt": "current field source anchor",
            }
            for anchor_id, authority_kind in current_anchor_kinds.items()
            if str(anchor_id).strip() and str(authority_kind).strip()
        )
        contextual_nodes = _unique_authority_nodes(contextual_nodes)

    choices_by_kind: list[list[dict[str, Any]]] = []
    for required_kind in required_kinds:
        source_nodes = (
            matching_nodes
            if required_kind in numeric_kinds
            else [*matching_nodes, *contextual_nodes]
        )
        choices = [
            node
            for node in _unique_authority_nodes(source_nodes)
            if str(node.get("authority_kind", "") or "").strip()
            == required_kind
        ]
        if not choices:
            return []
        choices_by_kind.append(choices)

    bindings: list[dict[str, Any]] = []
    seen_anchor_sets: set[tuple[str, ...]] = set()
    for selected_nodes in product(*choices_by_kind):
        anchor_ids = tuple(
            dict.fromkeys(
                str(node.get("anchor_id", "") or "").strip()
                for node in selected_nodes
                if str(node.get("anchor_id", "") or "").strip()
            )
        )
        if not anchor_ids or anchor_ids in seen_anchor_sets:
            continue
        seen_anchor_sets.add(anchor_ids)
        binding_id = (
            "metric_gate_source_binding:"
            + stable_hash(
                [requirement_id, field, owner, list(anchor_ids)]
            )[:20]
        )
        bindings.append(
            {
                "binding_id": binding_id,
                "authority_kind": owner,
                "source_anchor_ids": list(anchor_ids),
                "source_nodes": [dict(node) for node in selected_nodes],
            }
        )
        if len(bindings) >= _MAX_SOURCE_BINDINGS_PER_DECISION:
            break
    return bindings


def _unique_authority_nodes(value: Any) -> list[dict[str, Any]]:
    rows = value if isinstance(value, list | tuple) else []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_row in rows:
        if not isinstance(raw_row, Mapping):
            continue
        anchor_id = str(raw_row.get("anchor_id", "") or "").strip()
        if not anchor_id or anchor_id in seen:
            continue
        seen.add(anchor_id)
        result.append(
            {
                "anchor_id": anchor_id,
                "authority_kind": str(
                    raw_row.get("authority_kind", "") or ""
                ).strip(),
                "explicit_numeric_values": list(
                    raw_row.get("explicit_numeric_values", []) or []
                ),
                "content_excerpt": str(
                    raw_row.get("content_excerpt", "") or ""
                ),
            }
        )
    return result


def build_metric_authority_semantic_patch_transport(
    *,
    base_payload: Mapping[str, Any],
    base_payload_fingerprint: str,
    repair_context: Mapping[str, Any] | None,
    max_updates: int,
    **_kwargs: Any,
) -> SemanticPatchTransport | None:
    context = repair_context if isinstance(repair_context, Mapping) else {}
    raw_decisions = context.get(
        "gate_field_resolution_decisions_by_id", {}
    )
    if not isinstance(raw_decisions, Mapping) or not raw_decisions:
        return None
    decisions = {
        str(decision_id): dict(decision)
        for decision_id, decision in raw_decisions.items()
        if str(decision_id).strip() and isinstance(decision, Mapping)
    }
    if not decisions:
        return None
    if max_updates <= 0 or len(decisions) > max_updates:
        return None

    decision_properties: dict[str, Any] = {}
    for decision_id, decision in decisions.items():
        binding_ids = [
            str(row.get("binding_id", "") or "")
            for row in decision.get("source_binding_options", [])
            if isinstance(row, Mapping)
            and str(row.get("binding_id", "") or "").strip()
        ]
        decision_properties[decision_id] = {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "resolution",
                "source_binding_id",
                "rationale",
            ],
            "properties": {
                "resolution": {
                    "type": "string",
                    "enum": list(decision.get("allowed_resolutions", [])),
                },
                "source_binding_id": {
                    "type": "string",
                    "enum": ["", *binding_ids],
                },
                "rationale": {"type": "string", "minLength": 1},
            },
        }
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["base_payload_fingerprint", "decisions"],
        "properties": {
            "base_payload_fingerprint": {
                "type": "string",
                "const": base_payload_fingerprint,
            },
            "decisions": {
                "type": "object",
                "additionalProperties": False,
                "required": list(decisions),
                "properties": decision_properties,
            },
        },
    }
    prompt = json.dumps(
        {
            "task": (
                "Choose one semantic authority resolution for every exact "
                "runtime-owned decision key. Return only the structured object."
            ),
            "base_payload_fingerprint": base_payload_fingerprint,
            "gate_field_resolution_decisions_by_id": decisions,
            "hard_requirements": [
                "Return every supplied decision key exactly once.",
                "Choose source_binding only with one listed source_binding_id.",
                "Use an empty source_binding_id for every non-source resolution.",
                "The rationale must explain the semantic choice before execution.",
                "Do not change a numeric gate, invent an anchor, copy a value "
                "into theory, or claim observed/proof evidence.",
                "Runtime applies only the selected listed option and reruns the "
                "unchanged full validator.",
            ],
        },
        separators=(",", ":"),
        default=str,
    )

    def apply_envelope(
        envelope: Mapping[str, Any],
    ) -> tuple[
        dict[str, Any],
        list[list[str | int]],
        list[dict[str, Any]],
    ]:
        return _apply_metric_authority_decision_envelope(
            base_payload=base_payload,
            expected_base_fingerprint=base_payload_fingerprint,
            decisions=decisions,
            envelope=envelope,
        )

    return SemanticPatchTransport(
        kind=ARCHITECT_METRIC_AUTHORITY_PATCH_TRANSPORT_KIND,
        prompt=prompt,
        schema=schema,
        apply_envelope=apply_envelope,
    )


def _apply_metric_authority_decision_envelope(
    *,
    base_payload: Mapping[str, Any],
    expected_base_fingerprint: str,
    decisions: Mapping[str, Mapping[str, Any]],
    envelope: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    list[list[str | int]],
    list[dict[str, Any]],
]:
    observed_fingerprint = str(
        envelope.get("base_payload_fingerprint", "") or ""
    )
    if observed_fingerprint != expected_base_fingerprint:
        raise ValueError(
            "metric authority decision patch base_payload_fingerprint mismatch"
        )
    raw_selected = envelope.get("decisions", {})
    if not isinstance(raw_selected, Mapping):
        raise ValueError("metric authority decision patch decisions must be object")
    expected_ids = set(decisions)
    observed_ids = {str(key) for key in raw_selected}
    if observed_ids != expected_ids:
        raise ValueError(
            "metric authority decision patch keys must exactly match supplied "
            f"decisions; missing={sorted(expected_ids - observed_ids)} "
            f"extra={sorted(observed_ids - expected_ids)}"
        )

    selections: dict[str, dict[str, Any]] = {}
    resolutions_by_requirement: dict[str, list[str]] = {}
    for decision_id, decision in decisions.items():
        raw_selection = raw_selected.get(decision_id, {})
        if not isinstance(raw_selection, Mapping):
            raise ValueError(f"decision {decision_id} must be object")
        resolution = str(raw_selection.get("resolution", "") or "")
        allowed = {
            str(value)
            for value in decision.get("allowed_resolutions", [])
        }
        if resolution not in allowed:
            raise ValueError(
                f"decision {decision_id} resolution must be one of "
                + ", ".join(sorted(allowed))
            )
        source_binding_id = str(
            raw_selection.get("source_binding_id", "") or ""
        )
        binding_by_id = {
            str(row.get("binding_id", "") or ""): dict(row)
            for row in decision.get("source_binding_options", [])
            if isinstance(row, Mapping)
            and str(row.get("binding_id", "") or "").strip()
        }
        if resolution == "source_binding":
            if source_binding_id not in binding_by_id:
                raise ValueError(
                    f"decision {decision_id} must choose a listed source binding"
                )
        elif source_binding_id:
            raise ValueError(
                f"decision {decision_id} non-source resolution requires empty "
                "source_binding_id"
            )
        rationale = str(raw_selection.get("rationale", "") or "").strip()
        if not rationale:
            raise ValueError(f"decision {decision_id} rationale required")
        requirement_id = str(
            decision.get("requirement_id", "") or ""
        )
        resolutions_by_requirement.setdefault(requirement_id, []).append(
            resolution
        )
        selections[decision_id] = {
            "resolution": resolution,
            "source_binding_id": source_binding_id,
            "source_binding": binding_by_id.get(source_binding_id, {}),
            "rationale": rationale,
        }
    for requirement_id, resolutions in resolutions_by_requirement.items():
        if "remove_requirement" in resolutions and set(resolutions) != {
            "remove_requirement"
        }:
            raise ValueError(
                "all decisions for one requirement must choose "
                f"remove_requirement together: {requirement_id}"
            )

    patched = deepcopy(dict(base_payload))
    raw_requirements = patched.get("empirical_metric_requirements", [])
    if not isinstance(raw_requirements, list):
        raise ValueError("base empirical_metric_requirements must be array")
    requirement_indices: dict[str, int] = {}
    for index, raw_requirement in enumerate(raw_requirements):
        if not isinstance(raw_requirement, Mapping):
            continue
        requirement_id = str(
            raw_requirement.get("requirement_id", "") or ""
        ).strip()
        if not requirement_id or requirement_id in requirement_indices:
            raise ValueError(
                "base requirement IDs must be nonempty and unique"
            )
        requirement_indices[requirement_id] = index

    removed_requirement_ids = {
        requirement_id
        for requirement_id, resolutions in resolutions_by_requirement.items()
        if resolutions and set(resolutions) == {"remove_requirement"}
    }
    patched_paths: list[list[str | int]] = []
    application_rows: list[dict[str, Any]] = []
    affected_requirement_ids: set[str] = set()
    for decision_id, decision in decisions.items():
        requirement_id = str(decision.get("requirement_id", "") or "")
        if requirement_id in removed_requirement_ids:
            continue
        affected_requirement_ids.add(requirement_id)
        requirement_index = requirement_indices.get(requirement_id)
        if requirement_index is None:
            raise ValueError(
                f"decision {decision_id} references missing requirement_id"
            )
        requirement = raw_requirements[requirement_index]
        if not isinstance(requirement, dict):
            requirement = dict(requirement)
            raw_requirements[requirement_index] = requirement
        field = str(decision.get("field", "") or "")
        raw_authorities = requirement.get("gate_field_authorities", [])
        if not isinstance(raw_authorities, list):
            raise ValueError(
                f"requirement {requirement_id} gate_field_authorities must be array"
            )
        matching_indices = [
            index
            for index, row in enumerate(raw_authorities)
            if isinstance(row, Mapping)
            and str(row.get("field", "") or "") == field
        ]
        authority_row_created = False
        if not matching_indices and (
            decision.get("gate_field_authority_row_exists") is False
        ):
            raw_expected_index = decision.get(
                "gate_field_authority_expected_index",
                len(raw_authorities),
            )
            if (
                not isinstance(raw_expected_index, int)
                or isinstance(raw_expected_index, bool)
                or raw_expected_index < 0
                or raw_expected_index > len(raw_authorities)
            ):
                raise ValueError(
                    f"decision {decision_id} has invalid authority insertion index"
                )
            authority_index = int(raw_expected_index)
            raw_authorities.insert(
                authority_index,
                {
                    "field": field,
                    "authority_kind": str(
                        decision.get("current_owner", "") or ""
                    ),
                    "source_anchors": list(
                        dict.fromkeys(
                            str(value).strip()
                            for value in decision.get(
                                "current_source_anchor_ids", []
                            )
                            if str(value).strip()
                        )
                    ),
                    "rationale": "",
                },
            )
            matching_indices = [authority_index]
            authority_row_created = True
            patched_paths.append(
                [
                    "empirical_metric_requirements",
                    requirement_index,
                    "gate_field_authorities",
                ]
            )
        if len(matching_indices) != 1:
            raise ValueError(
                f"decision {decision_id} requires one unambiguous field row"
            )
        authority_index = matching_indices[0]
        authority = dict(raw_authorities[authority_index])
        raw_authorities[authority_index] = authority
        selection = selections[decision_id]
        resolution = str(selection["resolution"])
        rationale = str(selection["rationale"])
        if resolution == "source_binding":
            binding = selection["source_binding"]
            authority["authority_kind"] = str(
                binding.get("authority_kind", "") or ""
            )
            authority["source_anchors"] = list(
                binding.get("source_anchor_ids", [])
            )
            authority["rationale"] = rationale
            patched_paths.extend(
                [
                    [
                        "empirical_metric_requirements",
                        requirement_index,
                        "gate_field_authorities",
                        authority_index,
                        "authority_kind",
                    ],
                    [
                        "empirical_metric_requirements",
                        requirement_index,
                        "gate_field_authorities",
                        authority_index,
                        "source_anchors",
                    ],
                    [
                        "empirical_metric_requirements",
                        requirement_index,
                        "gate_field_authorities",
                        authority_index,
                        "rationale",
                    ],
                ]
            )
        else:
            authority["authority_kind"] = resolution
            authority["rationale"] = rationale
            patched_paths.extend(
                [
                    [
                        "empirical_metric_requirements",
                        requirement_index,
                        "gate_field_authorities",
                        authority_index,
                        "authority_kind",
                    ],
                    [
                        "empirical_metric_requirements",
                        requirement_index,
                        "gate_field_authorities",
                        authority_index,
                        "rationale",
                    ],
                ]
            )
            if resolution == "diagnostic_only":
                requirement["required"] = False
                patched_paths.append(
                    [
                        "empirical_metric_requirements",
                        requirement_index,
                        "required",
                    ]
                )
        application_rows.append(
            {
                "decision_id": decision_id,
                "requirement_id": requirement_id,
                "field": field,
                "model_selected_resolution": resolution,
                "model_selected_source_binding_id": str(
                    selection.get("source_binding_id", "") or ""
                ),
                "model_selected_source_authority_kind": str(
                    selection.get("source_binding", {}).get(
                        "authority_kind", ""
                    )
                    or ""
                ),
                "model_selected_source_anchor_ids": list(
                    selection.get("source_binding", {}).get(
                        "source_anchor_ids", []
                    )
                ),
                "runtime_selected_semantics": False,
                "runtime_created_missing_authority_row": (
                    authority_row_created
                ),
            }
        )

    for requirement_id in sorted(affected_requirement_ids):
        requirement_index = requirement_indices[requirement_id]
        requirement = raw_requirements[requirement_index]
        if not isinstance(requirement, dict):
            continue
        authority_rows = requirement.get("gate_field_authorities", [])
        rationale_rows = [
            (
                str(row.get("field", "") or "").strip(),
                str(row.get("rationale", "") or "").strip(),
            )
            for row in authority_rows
            if isinstance(row, Mapping)
            and str(row.get("field", "") or "").strip()
            and str(row.get("rationale", "") or "").strip()
        ]
        if not rationale_rows:
            continue
        requirement["acceptance_authority_rationale"] = (
            rationale_rows[0][1]
            if len(rationale_rows) == 1
            else "; ".join(
                f"{field}: {rationale}"
                for field, rationale in rationale_rows
            )
        )
        patched_paths.append(
            [
                "empirical_metric_requirements",
                requirement_index,
                "acceptance_authority_rationale",
            ]
        )

    if removed_requirement_ids:
        original_indices = {
            requirement_id: requirement_indices[requirement_id]
            for requirement_id in removed_requirement_ids
            if requirement_id in requirement_indices
        }
        patched["empirical_metric_requirements"] = [
            row
            for row in raw_requirements
            if not isinstance(row, Mapping)
            or str(row.get("requirement_id", "") or "")
            not in removed_requirement_ids
        ]
        patched_paths.extend(
            ["empirical_metric_requirements", original_indices[requirement_id]]
            for requirement_id in sorted(removed_requirement_ids)
            if requirement_id in original_indices
        )
        for decision_id, decision in decisions.items():
            requirement_id = str(decision.get("requirement_id", "") or "")
            if requirement_id not in removed_requirement_ids:
                continue
            selection = selections[decision_id]
            application_rows.append(
                {
                    "decision_id": decision_id,
                    "requirement_id": requirement_id,
                    "field": str(decision.get("field", "") or ""),
                    "model_selected_resolution": "remove_requirement",
                    "model_selected_source_binding_id": "",
                    "model_selected_source_authority_kind": "",
                    "model_selected_source_anchor_ids": [],
                    "runtime_selected_semantics": False,
                }
            )
    return patched, patched_paths, application_rows
