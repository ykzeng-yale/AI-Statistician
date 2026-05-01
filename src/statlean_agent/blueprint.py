"""Progress blueprint utilities for the StatLeanAgent loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"done", "in_progress", "pending", "blocked"}


def load_blueprint(path: Path) -> dict[str, Any]:
    """Load a machine-readable phase blueprint."""

    return json.loads(path.read_text(encoding="utf-8"))


def validate_blueprint(blueprint: dict[str, Any]) -> tuple[str, ...]:
    """Return validation errors for a blueprint."""

    errors: list[str] = []
    phase_ids: set[str] = set()
    milestone_ids: set[str] = set()

    if not blueprint.get("id"):
        errors.append("blueprint is missing `id`")
    if not blueprint.get("target"):
        errors.append("blueprint is missing `target`")

    phases = blueprint.get("phases")
    if not isinstance(phases, list) or not phases:
        errors.append("blueprint must contain a nonempty `phases` list")
        return tuple(errors)

    for phase_index, phase in enumerate(phases):
        phase_id = str(phase.get("id", ""))
        if not phase_id:
            errors.append(f"phase[{phase_index}] is missing `id`")
        elif phase_id in phase_ids:
            errors.append(f"duplicate phase id `{phase_id}`")
        phase_ids.add(phase_id)

        status = phase.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"phase `{phase_id}` has invalid status `{status}`")

        milestones = phase.get("milestones", [])
        if not isinstance(milestones, list):
            errors.append(f"phase `{phase_id}` milestones must be a list")
            continue

        for milestone_index, milestone in enumerate(milestones):
            milestone_id = str(milestone.get("id", ""))
            if not milestone_id:
                errors.append(f"phase `{phase_id}` milestone[{milestone_index}] is missing `id`")
            elif milestone_id in milestone_ids:
                errors.append(f"duplicate milestone id `{milestone_id}`")
            milestone_ids.add(milestone_id)

            milestone_status = milestone.get("status")
            if milestone_status not in ALLOWED_STATUSES:
                errors.append(
                    f"milestone `{milestone_id}` has invalid status `{milestone_status}`"
                )

    return tuple(errors)


def blueprint_status(blueprint: dict[str, Any]) -> dict[str, Any]:
    """Compute current phase, milestone, and next-action summary."""

    errors = validate_blueprint(blueprint)
    if errors:
        return {"valid": False, "errors": errors}

    phases = blueprint["phases"]
    done_phases = [phase for phase in phases if phase["status"] == "done"]
    current_phase = next((phase for phase in phases if phase["status"] != "done"), phases[-1])
    current_milestone = next(
        (
            milestone
            for milestone in current_phase.get("milestones", [])
            if milestone["status"] != "done"
        ),
        None,
    )
    next_actions = tuple(current_phase.get("next_actions", ()))

    return {
        "valid": True,
        "blueprint_id": blueprint["id"],
        "title": blueprint.get("title", blueprint["id"]),
        "target": blueprint["target"],
        "phase_count": len(phases),
        "done_phase_count": len(done_phases),
        "current_phase": _phase_row(current_phase),
        "current_milestone": _milestone_row(current_milestone),
        "next_actions": next_actions,
        "loop_contract": tuple(blueprint.get("loop_contract", ())),
        "promotion_gates": tuple(blueprint.get("promotion_gates", ())),
    }


def render_blueprint_status(blueprint: dict[str, Any]) -> str:
    """Render a compact, deterministic status report for heartbeat loops."""

    status = blueprint_status(blueprint)
    if not status["valid"]:
        return "Blueprint invalid:\n" + "\n".join(f"- {error}" for error in status["errors"])

    phase = status["current_phase"]
    milestone = status["current_milestone"]
    lines = [
        f"Blueprint: {status['title']}",
        f"Progress: {status['done_phase_count']}/{status['phase_count']} phases done",
        f"Current phase: {phase['id']} {phase['name']} [{phase['status']}]",
    ]

    if milestone is not None:
        lines.append(
            f"Current milestone: {milestone['id']} {milestone['name']} [{milestone['status']}]"
        )
    else:
        lines.append("Current milestone: none")

    next_actions = status["next_actions"]
    if next_actions:
        lines.append(f"Next action: {next_actions[0]}")
    else:
        lines.append("Next action: update blueprint or select a new phase")

    lines.append("Loop rule: if CI/smoke are green, continue the next unblocked milestone.")
    return "\n".join(lines)


def _phase_row(phase: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(phase.get("id", "")),
        "name": str(phase.get("name", "")),
        "status": str(phase.get("status", "")),
    }


def _milestone_row(milestone: dict[str, Any] | None) -> dict[str, str] | None:
    if milestone is None:
        return None
    return {
        "id": str(milestone.get("id", "")),
        "name": str(milestone.get("name", "")),
        "status": str(milestone.get("status", "")),
    }
