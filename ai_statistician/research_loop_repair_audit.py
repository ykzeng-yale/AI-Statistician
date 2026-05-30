from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


RESEARCH_LOOP_REPAIR_AUDIT_SCHEMA_VERSION = 1

ALLOWED_OWNERS = {
    "formal_verifier",
    "theory_developer",
    "algorithm_engineer",
    "simulator_agent",
    "research_coordinator",
}

ALLOWED_TASK_TYPES = {
    "proof_bank_expansion_from_formal_gap",
    "lean_proof_repair_from_axle_error",
    "theory_revision_from_simulation_failure",
    "algorithm_repair_from_numerical_failure",
    "simulator_environment_extension",
    "coordinator_triage_unknown_trigger",
}


@dataclass(frozen=True)
class ResearchLoopRepairRow:
    task_id: str
    question_id: str
    problem_class: str
    owner_agent: str
    task_type: str
    trigger: str
    priority: str
    output_required_gate: str
    required_fields: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    ok: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchLoopRepairSftExample:
    schema_version: int
    example_id: str
    split: str
    task: str
    prompt: str
    completion: str
    question_id: str
    problem_class: str
    owner_agent: str
    task_type: str
    tags: tuple[str, ...]


def audit_research_loop_repair_tasks(
    loop_dir: Path,
    out_dir: Path | None = None,
    *,
    validation_fraction: float = 0.2,
) -> dict[str, object]:
    """Validate loop repair tasks and export instruction-planning examples.

    This audit does not solve the repair tasks. It checks that the loop produced
    machine-readable next-agent work with enough context, acceptance criteria,
    and output contracts to train or prompt future TheoryDeveloper,
    ProofEngineer, AlgorithmEngineer, and Simulator agents.
    """

    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0.0, 1.0)")
    manifest_path = loop_dir / "research_loop_manifest.json"
    errors: list[str] = []
    manifest = _load_json(manifest_path, errors)
    task_path = Path(str(manifest.get("repair_tasks_jsonl", loop_dir / "research_loop_repair_tasks.jsonl")))
    if not task_path.is_absolute() and not task_path.exists():
        task_path = loop_dir / task_path
    tasks = _load_jsonl(task_path, errors)
    rows = [_row_for_task(task) for task in tasks]
    examples = [_example_for_task(task, validation_fraction) for task in tasks if isinstance(task, dict)]
    by_owner = Counter(row.owner_agent for row in rows)
    by_type = Counter(row.task_type for row in rows)
    by_trigger = Counter(row.trigger for row in rows)
    payload: dict[str, object] = {
        "schema_version": RESEARCH_LOOP_REPAIR_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "loop_dir": str(loop_dir),
        "manifest": str(manifest_path),
        "repair_tasks_jsonl": str(task_path),
        "n_tasks": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and bool(rows) and all(row.ok for row in rows),
        "errors": errors,
        "by_owner": dict(sorted(by_owner.items())),
        "by_type": dict(sorted(by_type.items())),
        "by_trigger": dict(sorted(by_trigger.items())),
        "n_sft_examples": len(examples),
        "n_train": sum(1 for row in examples if row.split == "train"),
        "n_validation": sum(1 for row in examples if row.split == "validation"),
        "rows": [asdict(row) for row in rows],
        "dataset_fingerprint": stable_hash([asdict(row) for row in examples]),
        "limitations": [
            "repair tasks are planning/training records, not completed repairs",
            "proof repair tasks still require AXLE verify_proof before entering the proof bank",
            "theory/algorithm/simulator repair tasks still require implementation and rerun evidence",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        train_path = out_dir / "research_loop_repair_sft_train.jsonl"
        validation_path = out_dir / "research_loop_repair_sft_validation.jsonl"
        all_path = out_dir / "research_loop_repair_sft_all.jsonl"
        _write_jsonl(train_path, [row for row in examples if row.split == "train"])
        _write_jsonl(validation_path, [row for row in examples if row.split == "validation"])
        _write_jsonl(all_path, examples)
        payload.update(
            {
                "train_jsonl": str(train_path),
                "validation_jsonl": str(validation_path),
                "all_jsonl": str(all_path),
            }
        )
        (out_dir / "research_loop_repair_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "research_loop_repair_audit.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"failed to parse JSON {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path}")
        return []
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"failed to parse JSONL {path}:{idx}: {exc}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"JSONL row is not an object: {path}:{idx}")
    return rows


def _row_for_task(task: dict[str, Any]) -> ResearchLoopRepairRow:
    errors: list[str] = []
    task_id = str(task.get("task_id", ""))
    question_id = str(task.get("question_id", ""))
    problem_class = str(task.get("problem_class", ""))
    owner_agent = str(task.get("owner_agent", ""))
    task_type = str(task.get("task_type", ""))
    trigger = str(task.get("trigger", ""))
    priority = str(task.get("priority", ""))
    prompt = str(task.get("prompt", ""))
    evidence = str(task.get("evidence", ""))
    context = task.get("context") if isinstance(task.get("context"), dict) else {}
    output_contract = task.get("output_contract") if isinstance(task.get("output_contract"), dict) else {}
    required_fields = tuple(str(row) for row in output_contract.get("required_fields", []) or [] if str(row))
    required_gate = str(output_contract.get("required_gate", ""))
    acceptance = tuple(str(row) for row in task.get("acceptance_criteria", []) or [] if str(row))

    if int(task.get("schema_version", 0) or 0) != 1:
        errors.append("schema_version must be 1")
    if not task_id:
        errors.append("task_id missing")
    if not question_id:
        errors.append("question_id missing")
    if not problem_class:
        errors.append("problem_class missing")
    if owner_agent not in ALLOWED_OWNERS:
        errors.append("owner_agent invalid")
    if task_type not in ALLOWED_TASK_TYPES:
        errors.append("task_type invalid")
    if priority not in {"high", "medium", "low"}:
        errors.append("priority invalid")
    if not trigger:
        errors.append("trigger missing")
    if not prompt:
        errors.append("prompt missing")
    if not evidence:
        errors.append("evidence missing")
    if not isinstance(context, dict) or not all(context.get(key) for key in ("dgp", "estimand", "assumptions")):
        errors.append("context missing dgp/estimand/assumptions")
    if not acceptance:
        errors.append("acceptance_criteria missing")
    if not required_fields:
        errors.append("output_contract.required_fields missing")
    if not required_gate:
        errors.append("output_contract.required_gate missing")
    if task_type.startswith("proof") or task_type.startswith("lean"):
        if "AXLE" not in required_gate and "verify_proof" not in required_gate:
            errors.append("proof task missing AXLE/verify_proof required gate")
    if task_type == "theory_revision_from_simulation_failure" and "revised_theorem_goals" not in required_fields:
        errors.append("theory repair task missing revised_theorem_goals output field")
    if task_type == "algorithm_repair_from_numerical_failure" and "implementation_hash" not in required_fields:
        errors.append("algorithm repair task missing implementation_hash output field")
    if task_type == "simulator_environment_extension" and "diagnostic_metrics" not in required_fields:
        errors.append("simulator extension task missing diagnostic_metrics output field")

    return ResearchLoopRepairRow(
        task_id=task_id,
        question_id=question_id,
        problem_class=problem_class,
        owner_agent=owner_agent,
        task_type=task_type,
        trigger=trigger,
        priority=priority,
        output_required_gate=required_gate,
        required_fields=required_fields,
        acceptance_criteria=acceptance,
        ok=not errors,
        errors=tuple(errors),
    )


def _example_for_task(task: dict[str, Any], validation_fraction: float) -> ResearchLoopRepairSftExample:
    completion = {
        "owner_agent": task.get("owner_agent"),
        "task_type": task.get("task_type"),
        "acceptance_criteria": task.get("acceptance_criteria", []),
        "output_contract": task.get("output_contract", {}),
    }
    prompt = "\n".join(
        [
            "You are the repair planner for an AI Statistical Theory Lab.",
            "Given a failed proof/simulation loop action, produce the owner, repair task type, acceptance criteria, and output contract.",
            "Return JSON only.",
            "",
            "Repair task record:",
            json.dumps(
                {
                    "source_action_id": task.get("source_action_id"),
                    "question_id": task.get("question_id"),
                    "problem_class": task.get("problem_class"),
                    "trigger": task.get("trigger"),
                    "priority": task.get("priority"),
                    "prompt": task.get("prompt"),
                    "evidence": task.get("evidence"),
                    "context": task.get("context"),
                },
                indent=2,
                default=str,
            ),
        ]
    )
    example_id = f"loop_repair_sft:{task.get('task_id', '')}:{stable_hash([prompt, completion])[:12]}"
    return ResearchLoopRepairSftExample(
        schema_version=RESEARCH_LOOP_REPAIR_AUDIT_SCHEMA_VERSION,
        example_id=example_id,
        split=_split_for_example(example_id, validation_fraction),
        task="research_loop_repair_planning",
        prompt=prompt,
        completion=json.dumps(completion, sort_keys=True),
        question_id=str(task.get("question_id", "")),
        problem_class=str(task.get("problem_class", "")),
        owner_agent=str(task.get("owner_agent", "")),
        task_type=str(task.get("task_type", "")),
        tags=("research_loop", "repair_task", str(task.get("owner_agent", "")), str(task.get("task_type", ""))),
    )


def _split_for_example(example_id: str, validation_fraction: float) -> str:
    if validation_fraction <= 0.0:
        return "train"
    bucket = int(stable_hash(example_id)[:8], 16) / 0xFFFFFFFF
    return "validation" if bucket < validation_fraction else "train"


def _write_jsonl(path: Path, rows: list[ResearchLoopRepairSftExample]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), default=str) + "\n")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Research Loop Repair Task Audit",
        "",
        f"- Loop dir: `{payload.get('loop_dir')}`",
        f"- Tasks: {payload.get('n_ok')}/{payload.get('n_tasks')} valid",
        f"- SFT examples: {payload.get('n_sft_examples')}",
        "",
        "## Owners",
        "",
    ]
    by_owner = payload.get("by_owner", {})
    if isinstance(by_owner, dict) and by_owner:
        for owner, count in sorted(by_owner.items()):
            lines.append(f"- `{owner}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Task Types", ""])
    by_type = payload.get("by_type", {})
    if isinstance(by_type, dict) and by_type:
        for task_type, count in sorted(by_type.items()):
            lines.append(f"- `{task_type}`: {count}")
    else:
        lines.append("- none")
    lines.append("")
    if payload.get("errors"):
        lines.extend(["## Errors", ""])
        for error in payload.get("errors", []):
            lines.append(f"- {error}")
        lines.append("")
    return "\n".join(lines)
