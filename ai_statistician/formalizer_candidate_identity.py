from __future__ import annotations

from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def _candidate_binding(row: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(row.get("source_theorem_target_provenance", {}))
    candidate_id = str(row.get("candidate_id", "") or "").strip()
    source_hash = str(
        row.get("source_hash", "")
        or row.get("lineage_candidate_artifact_hash", "")
        or row.get("candidate_source_hash", "")
        or ""
    ).strip()
    artifact_path = str(
        row.get("artifact_path", "")
        or row.get("candidate_artifact_path", "")
        or row.get("lineage_candidate_artifact_path", "")
        or ""
    ).strip()
    declaration = str(
        row.get("expected_target_lean_declaration", "")
        or row.get("candidate_lean_declaration", "")
        or row.get("target_lean_declaration", "")
        or provenance.get("target_lean_declaration", "")
        or ""
    ).strip()
    target_ids = _text_list(row.get("target_ids", []))
    goal_ids = _text_list(row.get("target_theorem_goal_ids", []))
    seed = [candidate_id, source_hash, artifact_path, declaration, target_ids, goal_ids]
    return {
        "binding_id": "candidate_lineage:" + stable_hash(seed)[:20],
        "candidate_id": candidate_id,
        "source_hash": source_hash,
        "artifact_path": artifact_path,
        "expected_target_lean_declaration": declaration,
        "expected_target_ids": target_ids,
        "expected_target_theorem_goal_ids": goal_ids,
        "expected_target_theorem_name": str(
            row.get("target_theorem_name", "") or ""
        ).strip(),
        "source_theorem_target_provenance": dict(provenance),
    }


def _candidate_rows(environment_feedback: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    workspace = _mapping(environment_feedback.get("formalizer_workspace_context", {}))
    carried = _mapping(workspace.get("candidate_lineage_contract", {}))
    carried_rows = [
        row for row in carried.get("bindings", []) or [] if isinstance(row, Mapping)
    ]
    if carried_rows:
        return carried_rows
    rows: list[Mapping[str, Any]] = []
    if workspace:
        rows.append(workspace)
    for key in ("candidate_diagnostics", "candidate_rows"):
        rows.extend(
            row
            for row in environment_feedback.get(key, []) or []
            if isinstance(row, Mapping)
        )
    return rows


def build_candidate_lineage_contract(
    *,
    owner_subsystem: str,
    environment_feedback: Mapping[str, Any],
    schema_version: int,
    proof_evidence_boundary: str,
) -> dict[str, Any]:
    """Bind a model revision to the immutable candidate it is replacing."""

    bindings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in _candidate_rows(environment_feedback):
        binding = _candidate_binding(row)
        if not binding["expected_target_lean_declaration"]:
            continue
        binding_id = str(binding["binding_id"])
        if binding_id in seen:
            continue
        seen.add(binding_id)
        bindings.append(binding)
    feedback_type = str(environment_feedback.get("feedback_type", "") or "")
    required = bool(
        owner_subsystem == "FormalizationEvaluator"
        and (bindings or feedback_type.startswith(("formalizer_", "formal_target_")))
    )
    return {
        "schema_version": schema_version,
        "contract_kind": "immutable_candidate_lineage",
        "required": required,
        "bindings": bindings,
        "proof_evidence_boundary": proof_evidence_boundary,
    }


def evaluate_candidate_lineage(
    *,
    contract: Mapping[str, Any],
    candidate_id: str,
    actual_target_lean_declaration: str,
    target_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Check target identity without interpreting Lean grammar or proposing edits."""

    required = bool(contract.get("required", False))
    bindings = [
        dict(row) for row in contract.get("bindings", []) or [] if isinstance(row, Mapping)
    ]
    if not required:
        return {
            "candidate_lineage_required": False,
            "candidate_lineage_binding_status": "NOT_REQUIRED",
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
        expected = str(binding.get("expected_target_lean_declaration", "") or "")
        if candidate_id and candidate_id == str(binding.get("candidate_id", "") or ""):
            score += 100
        if expected and expected == actual_target_lean_declaration:
            score += 50
        if candidate_goal_ids & set(
            _text_list(binding.get("expected_target_theorem_goal_ids", []))
        ):
            score += 20
        if candidate_target_ids & set(_text_list(binding.get("expected_target_ids", []))):
            score += 10
        scored.append((score, binding))

    selected: dict[str, Any] = {}
    status = "UNBOUND"
    if len(bindings) == 1:
        selected, status = bindings[0], "BOUND"
    elif scored:
        top = max(score for score, _ in scored)
        best = [row for score, row in scored if score == top and score > 0]
        if len(best) == 1:
            selected, status = best[0], "BOUND"
        elif len(best) > 1:
            status = "AMBIGUOUS"

    expected = str(selected.get("expected_target_lean_declaration", "") or "").strip()
    mismatch = bool(
        status == "BOUND"
        and expected
        and actual_target_lean_declaration
        and expected != actual_target_lean_declaration
    )
    unbound = bool(status != "BOUND" or not expected or not actual_target_lean_declaration)
    errors: list[str] = []
    if mismatch:
        errors.append(
            "candidate declaration identity drift: expected "
            f"{expected}, emitted {actual_target_lean_declaration}"
        )
    elif unbound:
        errors.append(
            "candidate could not be bound to one immutable target declaration; "
            "source-theorem evidence is disabled"
        )
    return {
        "candidate_lineage_required": True,
        "candidate_lineage_binding_status": status,
        "candidate_lineage_binding_id": str(selected.get("binding_id", "") or ""),
        "parent_candidate_id": str(selected.get("candidate_id", "") or ""),
        "parent_source_hash": str(selected.get("source_hash", "") or ""),
        "parent_artifact_path": str(selected.get("artifact_path", "") or ""),
        "expected_target_lean_declaration": expected,
        "expected_target_ids": list(selected.get("expected_target_ids", []) or []),
        "expected_target_theorem_goal_ids": list(
            selected.get("expected_target_theorem_goal_ids", []) or []
        ),
        "expected_target_theorem_name": str(
            selected.get("expected_target_theorem_name", "") or ""
        ),
        "actual_target_lean_declaration": actual_target_lean_declaration,
        "target_identity_matches_expected": bool(
            selected and expected == actual_target_lean_declaration
        ),
        "target_identity_mismatch_not_source_theorem": mismatch,
        "target_identity_unbound_not_source_theorem": unbound,
        "target_identity_errors": errors,
        "candidate_lineage_binding": selected,
    }
