from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .task_family import (
    is_explicit_task_family,
    primary_task_family_from_question,
    task_family_value,
)


CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION = 1
CROSS_FAMILY_EVAL_PROTOCOL_KIND = "CrossFamilyEndToEndEvaluationProtocol"


def load_cross_family_eval_protocol(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_cross_family_eval_protocol(payload)
    if errors:
        raise ValueError("; ".join(errors))
    return dict(payload)


def validate_cross_family_eval_protocol(value: Any) -> list[str]:
    if not isinstance(value, Mapping):
        return ["cross-family evaluation protocol must be a JSON object"]
    errors: list[str] = []
    if value.get("schema_version") != CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION:
        errors.append(
            "cross-family evaluation protocol schema_version must equal "
            f"{CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION}"
        )
    if value.get("artifact_kind") != CROSS_FAMILY_EVAL_PROTOCOL_KIND:
        errors.append(
            f"cross-family evaluation protocol artifact_kind must equal "
            f"{CROSS_FAMILY_EVAL_PROTOCOL_KIND}"
        )
    for field in (
        "protocol_id",
        "split_frozen_at",
        "split_frozen_at_base_commit",
        "question_source",
    ):
        if not str(value.get(field, "") or "").strip():
            errors.append(f"cross-family evaluation protocol {field} is required")
    minimum_families = value.get("minimum_distinct_task_families_per_panel")
    if (
        isinstance(minimum_families, bool)
        or not isinstance(minimum_families, int)
        or minimum_families < 2
    ):
        errors.append(
            "minimum_distinct_task_families_per_panel must be an integer >= 2"
        )
        minimum_families = 2

    run_contract = value.get("run_contract", {})
    if not isinstance(run_contract, Mapping):
        errors.append("run_contract must be an object")
    else:
        required_true_fields = (
            "capability_eval_required",
            "fresh_start_required",
            "resume_forbidden",
            "task_learning_memory_forbidden",
            "component_eval_substitution_forbidden",
            "candidate_gate_independence_required",
        )
        for field in required_true_fields:
            if run_contract.get(field) is not True:
                errors.append(f"run_contract.{field} must be true")
        if str(run_contract.get("capability_eval_preset", "") or "") != "full-live":
            errors.append("run_contract.capability_eval_preset must equal full-live")

    panels = value.get("panels", {})
    if not isinstance(panels, Mapping):
        errors.append("panels must be an object")
        return sorted(set(errors))
    required_panel_ids = {"development", "held_out"}
    missing_panels = required_panel_ids - set(panels)
    if missing_panels:
        errors.append(
            "panels must include development and held_out; missing: "
            + ", ".join(sorted(missing_panels))
        )

    panel_question_ids: dict[str, set[str]] = {}
    panel_task_families: dict[str, set[str]] = {}
    for panel_id, raw_panel in panels.items():
        prefix = f"panels.{panel_id}"
        if not isinstance(raw_panel, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        if str(raw_panel.get("role", "") or "") != str(panel_id):
            errors.append(f"{prefix}.role must equal {panel_id}")
        tasks = raw_panel.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            errors.append(f"{prefix}.tasks must be a nonempty array")
            continue
        question_ids: list[str] = []
        task_families: list[str] = []
        for index, raw_task in enumerate(tasks):
            task_prefix = f"{prefix}.tasks[{index}]"
            if not isinstance(raw_task, Mapping):
                errors.append(f"{task_prefix} must be an object")
                continue
            question_id = str(raw_task.get("question_id", "") or "").strip()
            task_family = task_family_value(raw_task.get("task_family", ""))
            if not question_id:
                errors.append(f"{task_prefix}.question_id is required")
            else:
                question_ids.append(question_id)
            if not is_explicit_task_family(task_family):
                errors.append(f"{task_prefix}.task_family must be explicit")
            else:
                task_families.append(task_family)
        if len(set(question_ids)) != len(question_ids):
            errors.append(f"{prefix}.tasks contains duplicate question_id values")
        if len(set(task_families)) != len(task_families):
            errors.append(f"{prefix}.tasks must use distinct task families")
        if len(set(task_families)) < int(minimum_families):
            errors.append(
                f"{prefix}.tasks must contain at least {minimum_families} "
                "distinct task families"
            )
        panel_question_ids[str(panel_id)] = set(question_ids)
        panel_task_families[str(panel_id)] = set(task_families)

    development_ids = panel_question_ids.get("development", set())
    held_out_ids = panel_question_ids.get("held_out", set())
    if development_ids & held_out_ids:
        errors.append("development and held_out question IDs must be disjoint")
    development_families = panel_task_families.get("development", set())
    held_out_families = panel_task_families.get("held_out", set())
    if development_families & held_out_families:
        errors.append("development and held_out task families must be disjoint")

    required_evidence = value.get("required_per_task_evidence")
    if not isinstance(required_evidence, list) or not required_evidence or any(
        not isinstance(item, str) or not item.strip() for item in required_evidence
    ):
        errors.append("required_per_task_evidence must contain nonempty strings")
    return sorted(set(errors))


def resolve_cross_family_eval_panel(
    protocol: Mapping[str, Any],
    *,
    panel_id: str,
    questions: Sequence[object],
) -> dict[str, Any]:
    errors = validate_cross_family_eval_protocol(protocol)
    if errors:
        raise ValueError("; ".join(errors))
    panel_name = str(panel_id or "").strip()
    panels = protocol["panels"]
    if panel_name not in panels:
        raise ValueError(
            "unknown cross-family evaluation panel: "
            f"{panel_name or '<missing>'}; available={sorted(panels)}"
        )
    panel = panels[panel_name]
    tasks = panel["tasks"]
    by_id = {
        str(getattr(question, "id", "") or ""): question for question in questions
    }
    missing_question_ids: list[str] = []
    family_mismatches: list[str] = []
    question_ids: list[str] = []
    task_families: list[str] = []
    for task in tasks:
        question_id = str(task["question_id"])
        expected_family = task_family_value(task["task_family"])
        question = by_id.get(question_id)
        if question is None:
            missing_question_ids.append(question_id)
            continue
        actual_family = primary_task_family_from_question(question)
        if actual_family != expected_family:
            family_mismatches.append(
                f"{question_id}: expected {expected_family}, got {actual_family}"
            )
        question_ids.append(question_id)
        task_families.append(actual_family)
    if missing_question_ids or family_mismatches:
        details: list[str] = []
        if missing_question_ids:
            details.append("missing question IDs: " + ", ".join(missing_question_ids))
        if family_mismatches:
            details.append("task-family mismatches: " + "; ".join(family_mismatches))
        raise ValueError("; ".join(details))
    minimum_families = int(protocol["minimum_distinct_task_families_per_panel"])
    if len(set(task_families)) < minimum_families:
        raise ValueError(
            f"panel {panel_name} resolved to fewer than {minimum_families} "
            "distinct task families"
        )
    return {
        "schema_version": CROSS_FAMILY_EVAL_PROTOCOL_SCHEMA_VERSION,
        "artifact_kind": "CrossFamilyEndToEndEvaluationPanelSelection",
        "protocol_id": str(protocol["protocol_id"]),
        "protocol_fingerprint": stable_hash(dict(protocol)),
        "protocol_panel": panel_name,
        "split_frozen_at": str(protocol["split_frozen_at"]),
        "split_frozen_at_base_commit": str(
            protocol["split_frozen_at_base_commit"]
        ),
        "question_source": str(protocol["question_source"]),
        "question_ids": question_ids,
        "task_families": task_families,
        "minimum_distinct_task_families": minimum_families,
        "fresh_start_required": True,
        "resume_forbidden": True,
        "task_learning_memory_forbidden": True,
        "component_eval_substitution_forbidden": True,
        "candidate_gate_independence_required": True,
        "required_per_task_evidence": list(protocol["required_per_task_evidence"]),
        "proof_evidence_status": "EVALUATION_PROTOCOL_SELECTION_NOT_PROOF_EVIDENCE",
    }
