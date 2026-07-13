from __future__ import annotations

from typing import Any, Mapping

from .fingerprint import stable_hash


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def _binding_from_repair_row(row: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(row.get("source_theorem_target_provenance", {}))
    parent_candidate_id = str(
        row.get("parent_candidate_id", "") or row.get("candidate_id", "") or ""
    ).strip()
    parent_source_hash = str(
        row.get("parent_source_hash", "")
        or row.get("source_hash", "")
        or row.get("lineage_candidate_artifact_hash", "")
        or ""
    ).strip()
    parent_artifact_path = str(
        row.get("parent_artifact_path", "")
        or row.get("artifact_path", "")
        or row.get("kernel_check_artifact_path", "")
        or ""
    ).strip()
    expected_declaration = str(
        row.get("expected_target_lean_declaration", "")
        or provenance.get("target_lean_declaration", "")
        or row.get("target_lean_declaration", "")
        or ""
    ).strip()
    expected_target_ids = _text_list(
        row.get("expected_target_ids", []) or row.get("target_ids", [])
    )
    expected_goal_ids = _text_list(
        row.get("expected_target_theorem_goal_ids", [])
        or row.get("target_theorem_goal_ids", [])
    )
    binding_seed = [
        parent_candidate_id,
        parent_source_hash,
        parent_artifact_path,
        expected_declaration,
        expected_target_ids,
        expected_goal_ids,
    ]
    return {
        "binding_id": str(
            row.get("binding_id", "")
            or "repair_target_identity_binding:" + stable_hash(binding_seed)[:20]
        ),
        "parent_candidate_id": parent_candidate_id,
        "parent_source_hash": parent_source_hash,
        "parent_artifact_path": parent_artifact_path,
        "expected_target_lean_declaration": expected_declaration,
        "expected_target_ids": expected_target_ids,
        "expected_target_theorem_goal_ids": expected_goal_ids,
        "expected_target_theorem_name": str(
            row.get("expected_target_theorem_name", "")
            or row.get("target_theorem_name", "")
            or ""
        ).strip(),
        "source_theorem_target_provenance": dict(provenance),
    }


def build_repair_target_identity_contract(
    *,
    task_id: str,
    owner_subsystem: str,
    environment_feedback: Mapping[str, Any],
    schema_version: int,
    proof_evidence_boundary: str,
) -> dict[str, Any]:
    """Build an immutable parent-target contract for one candidate repair task."""

    repair_context = _mapping(
        environment_feedback.get("proofengineer_repair_context", {})
    )
    carried_contract = _mapping(
        repair_context.get("repair_target_identity_contract", {})
    )
    raw_bindings = [
        row
        for row in carried_contract.get("bindings", []) or []
        if isinstance(row, Mapping)
    ]
    if not raw_bindings and not bool(carried_contract.get("required", False)):
        raw_bindings = [
            row
            for row in repair_context.get("candidate_rerun_specs", []) or []
            if isinstance(row, Mapping)
        ]
    bindings = [_binding_from_repair_row(row) for row in raw_bindings]
    feedback_type = str(environment_feedback.get("feedback_type", "") or "")
    required = bool(
        task_id.startswith("formalize-lean-repair:")
        or (
            owner_subsystem == "ProofEngineer"
            and feedback_type == "formalizer_lean_candidate_local_lean_feedback"
        )
        or carried_contract
        or bindings
    )
    return {
        "schema_version": schema_version,
        "contract_kind": "immutable_parent_candidate_target_identity",
        "required": required,
        "bindings": bindings,
        "binding_policy": (
            "Bind a repair candidate to exactly one parent candidate using carried "
            "target IDs or a unique parent lineage. A local kernel check verifies "
            "only the emitted declaration; declaration drift cannot close the "
            "parent source theorem."
        ),
        "proof_evidence_boundary": proof_evidence_boundary,
    }


def evaluate_repair_target_identity(
    *,
    contract: Mapping[str, Any],
    candidate_id: str,
    actual_target_lean_declaration: str,
    target_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind an emitted repair to one parent and classify declaration drift."""

    required = bool(contract.get("required", False))
    bindings = [
        dict(row)
        for row in contract.get("bindings", []) or []
        if isinstance(row, Mapping)
    ]
    if not required:
        return {
            "repair_target_identity_required": False,
            "repair_target_identity_binding_status": "NOT_REQUIRED",
            "target_identity_matches_expected": None,
            "target_identity_mismatch_not_source_theorem": False,
            "target_identity_unbound_not_source_theorem": False,
            "target_identity_errors": [],
        }

    candidate_target_ids = set(_text_list(target_context.get("target_ids", [])))
    candidate_goal_ids = set(
        _text_list(target_context.get("target_theorem_goal_ids", []))
    )
    scored: list[tuple[int, dict[str, Any]]] = []
    for binding in bindings:
        score = 0
        expected_declaration = str(
            binding.get("expected_target_lean_declaration", "") or ""
        ).strip()
        if (
            expected_declaration == actual_target_lean_declaration
            and expected_declaration
        ):
            score += 100
        if candidate_goal_ids & set(
            _text_list(binding.get("expected_target_theorem_goal_ids", []))
        ):
            score += 50
        if candidate_target_ids & set(
            _text_list(binding.get("expected_target_ids", []))
        ):
            score += 25
        parent_id = str(binding.get("parent_candidate_id", "") or "").strip()
        if candidate_id == parent_id:
            score += 10
        elif parent_id and candidate_id.startswith(
            (parent_id + "_", parent_id + "-", parent_id + ":")
        ):
            score += 5
        scored.append((score, binding))

    selected: dict[str, Any] = {}
    binding_status = "UNBOUND"
    if len(bindings) == 1:
        selected, binding_status = bindings[0], "BOUND"
    elif scored:
        top_score = max(score for score, _ in scored)
        best = [row for score, row in scored if score == top_score and score > 0]
        if len(best) == 1:
            selected, binding_status = best[0], "BOUND"
        elif len(best) > 1:
            binding_status = "AMBIGUOUS"

    expected = str(selected.get("expected_target_lean_declaration", "") or "").strip()
    identity_matches = bool(
        selected and expected and actual_target_lean_declaration == expected
    )
    identity_unbound = bool(
        binding_status != "BOUND" or not expected or not actual_target_lean_declaration
    )
    identity_mismatch = bool(
        binding_status == "BOUND"
        and expected
        and actual_target_lean_declaration
        and expected != actual_target_lean_declaration
    )
    errors: list[str] = []
    if identity_mismatch:
        errors.append(
            "repair candidate declaration identity drift: expected "
            f"{expected}, emitted {actual_target_lean_declaration}"
        )
    elif identity_unbound:
        errors.append(
            "repair candidate could not be bound to one immutable parent target "
            "declaration; source-theorem evidence is disabled"
        )
    return {
        "repair_target_identity_required": True,
        "repair_target_identity_binding_status": binding_status,
        "repair_target_identity_binding_id": str(selected.get("binding_id", "") or ""),
        "repair_parent_candidate_id": str(
            selected.get("parent_candidate_id", "") or ""
        ),
        "repair_parent_source_hash": str(selected.get("parent_source_hash", "") or ""),
        "repair_parent_artifact_path": str(
            selected.get("parent_artifact_path", "") or ""
        ),
        "expected_target_lean_declaration": expected,
        "expected_target_ids": list(selected.get("expected_target_ids", []) or []),
        "expected_target_theorem_goal_ids": list(
            selected.get("expected_target_theorem_goal_ids", []) or []
        ),
        "expected_target_theorem_name": str(
            selected.get("expected_target_theorem_name", "") or ""
        ),
        "actual_target_lean_declaration": actual_target_lean_declaration,
        "target_identity_matches_expected": identity_matches,
        "target_identity_mismatch_not_source_theorem": identity_mismatch,
        "target_identity_unbound_not_source_theorem": identity_unbound,
        "target_identity_errors": errors,
        "repair_target_identity_contract": selected,
    }


def repair_target_identity_binding_from_diagnostic(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Preserve the original parent identity while feedback crosses retries."""

    carried = _mapping(row.get("repair_target_identity_contract", {}))
    provenance = _mapping(row.get("source_theorem_target_provenance", {}))
    merged = {
        "binding_id": row.get("repair_target_identity_binding_id", "")
        or carried.get("binding_id", ""),
        "parent_candidate_id": row.get("repair_parent_candidate_id", "")
        or carried.get("parent_candidate_id", "")
        or row.get("candidate_id", ""),
        "parent_source_hash": row.get("repair_parent_source_hash", "")
        or carried.get("parent_source_hash", "")
        or row.get("source_hash", ""),
        "parent_artifact_path": row.get("repair_parent_artifact_path", "")
        or carried.get("parent_artifact_path", "")
        or row.get("artifact_path", "")
        or row.get("kernel_check_artifact_path", ""),
        "expected_target_lean_declaration": row.get(
            "expected_target_lean_declaration", ""
        )
        or carried.get("expected_target_lean_declaration", "")
        or provenance.get("target_lean_declaration", "")
        or row.get("target_lean_declaration", ""),
        "expected_target_ids": carried.get("expected_target_ids", [])
        or row.get("target_ids", []),
        "expected_target_theorem_goal_ids": carried.get(
            "expected_target_theorem_goal_ids", []
        )
        or row.get("target_theorem_goal_ids", []),
        "expected_target_theorem_name": carried.get("expected_target_theorem_name", "")
        or row.get("target_theorem_name", ""),
        "source_theorem_target_provenance": carried.get(
            "source_theorem_target_provenance", {}
        )
        or provenance,
    }
    return _binding_from_repair_row(merged)
