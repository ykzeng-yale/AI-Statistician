from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .autoform_harness import build_autoform_harness_profile
from .fingerprint import stable_hash
from .formal_gap_task_export import export_formal_gap_lean_tasks


AUTOFORM_TARGET_EXPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class AutoformFormalizationTarget:
    name: str
    description: str
    kind: str
    location: str
    lean_declaration: str
    lean_file: str


def export_autoform_targets(
    run_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export formal-gap work packets in Autoform-Bot's target-list shape.

    `formal-gap-task-export` is our native queue format. Autoform-Bot expects a
    YAML list of targets with `name`, `description`, `kind`, `location`,
    `lean_declaration`, and `lean_file`. This bridge lets the AI Statistician
    hand its audited theorem-development gaps to Autoform-Bot's statement
    extraction/evaluation harness without making Autoform a required runtime
    dependency.
    """

    task_payload = export_formal_gap_lean_tasks(run_dir)
    tasks = [row for row in task_payload.get("tasks", []) if isinstance(row, dict)]
    targets = [_target_for_task(row) for row in tasks]
    harness = build_autoform_harness_profile()
    errors = _errors(targets)
    warnings = _warnings(harness)
    payload = {
        "schema_version": AUTOFORM_TARGET_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "n_targets": len(targets),
        "n_ok": len(targets) if not errors else 0,
        "all_ok": bool(task_payload.get("all_ok")) and bool(targets) and not errors,
        "target_fingerprint": stable_hash([asdict(row) for row in targets]),
        "source_task_fingerprint": task_payload.get("task_fingerprint", ""),
        "autoform_harness": asdict(harness),
        "targets": [asdict(row) for row in targets],
        "command_templates": _command_templates(out_dir),
        "limitations": [
            "Autoform target export does not prove the formal gaps",
            "Lean skeletons still contain FORMAL_GAP markers and placeholder assumptions",
            "Autoform-Bot remains an optional external harness with its own dependency setup",
        ],
        "errors": errors,
        "warnings": warnings,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = out_dir / "autoform_targets.yaml"
        book_dir = out_dir / "autoform_book"
        book_dir.mkdir(parents=True, exist_ok=True)
        book_path = book_dir / "formal_gap_statements.md"
        yaml_path.write_text(_yaml_targets(targets), encoding="utf-8")
        book_path.write_text(_book_markdown(targets), encoding="utf-8")
        payload["autoform_targets_yaml"] = str(yaml_path)
        payload["autoform_book_dir"] = str(book_dir)
        payload["autoform_book_markdown"] = str(book_path)
        payload["command_templates"] = _command_templates(out_dir)
        (out_dir / "autoform_targets_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "autoform_targets.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _target_for_task(task: dict[str, Any]) -> AutoformFormalizationTarget:
    declaration = _lean_declaration(str(task.get("statement", "")))
    task_id = str(task.get("task_id", "formal_gap"))
    required_primitives = ", ".join(str(item) for item in task.get("required_primitives", []) or [])
    dependencies = ", ".join(str(item) for item in task.get("dependencies", []) or [])
    description = (
        f"{task.get('proof_strategy', '')}\n\n"
        f"Problem class: {task.get('problem_class', '')}.\n"
        f"Theorem goal: {task.get('theorem_goal_id', '')}.\n"
        f"Required primitives: {required_primitives or 'none'}.\n"
        f"Verified proof-bank dependencies: {dependencies or 'none'}.\n"
        "This is an AI Statistician FORMAL_GAP target: replace placeholder "
        "assumptions with reusable Lean theorem families, then verify through AXLE/Lean."
    ).strip()
    return AutoformFormalizationTarget(
        name=_safe_name(task_id),
        description=description,
        kind="theorem",
        location=str(task.get("artifact_path", "")),
        lean_declaration=declaration,
        lean_file=str(task.get("artifact_path", "")),
    )


def _lean_declaration(statement: str) -> str:
    uncommented = _strip_lean_comments(statement)
    match = re.search(
        r"^\s*(?:theorem|lemma|def)\s+([A-Za-z_][A-Za-z0-9_'.]*)\b",
        uncommented,
        flags=re.MULTILINE,
    )
    return match.group(1) if match else ""


def _strip_lean_comments(statement: str) -> str:
    without_blocks = re.sub(r"/-.*?-/", "", statement, flags=re.DOTALL)
    lines = []
    for line in without_blocks.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "_", value).strip("_")
    return cleaned or "formal_gap"


def _errors(targets: list[AutoformFormalizationTarget]) -> tuple[str, ...]:
    errors: list[str] = []
    if not targets:
        errors.append("no Autoform targets exported")
    for target in targets:
        if not target.lean_declaration:
            errors.append(f"target {target.name} missing lean_declaration")
        if not target.lean_file:
            errors.append(f"target {target.name} missing lean_file")
        if "FORMAL_GAP" not in target.description:
            errors.append(f"target {target.name} description missing FORMAL_GAP marker")
    return tuple(dict.fromkeys(errors))


def _warnings(harness: Any) -> tuple[str, ...]:
    if bool(getattr(harness, "local_execution_ready", False)):
        return ()
    remote = str(getattr(harness, "remote_url", "") or "")
    root = str(getattr(harness, "root", "") or "")
    return (
        "Autoform-Bot local checkout is not execution-ready; exported targets remain handoff-ready, "
        f"but a runner must clone/setup {remote or 'the configured harness'} at {root or '<configured root>'}.",
    )


def _yaml_targets(targets: list[AutoformFormalizationTarget]) -> str:
    lines: list[str] = []
    for target in targets:
        row = asdict(target)
        lines.append(f"- name: {_yaml_string(row['name'])}")
        lines.append(f"  description: {_yaml_string(row['description'])}")
        lines.append(f"  kind: {_yaml_string(row['kind'])}")
        lines.append(f"  location: {_yaml_string(row['location'])}")
        lines.append(f"  lean_declaration: {_yaml_string(row['lean_declaration'])}")
        lines.append(f"  lean_file: {_yaml_string(row['lean_file'])}")
    return "\n".join(lines) + ("\n" if lines else "")


def _yaml_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _book_markdown(targets: list[AutoformFormalizationTarget]) -> str:
    lines = [
        "# AI Statistician Formal Gap Statements",
        "",
        "These statements are exported from audited AI Statistician FORMAL_GAP tasks.",
        "They are theorem-development targets for Autoform-Bot assessment, not verified proofs.",
        "",
    ]
    for index, target in enumerate(targets, start=1):
        lines.extend(
            [
                f"## {index}. `{target.name}`",
                "",
                f"- Kind: `{target.kind}`",
                f"- Lean declaration: `{target.lean_declaration}`",
                f"- Lean file: `{target.lean_file}`",
                "",
                target.description,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _command_templates(out_dir: Path | None) -> tuple[str, ...]:
    base = str(out_dir) if out_dir is not None else "<out_dir>"
    return (
        "python -m autoform.eval run "
        "--repo_dir <lean_repo> "
        "--code_dir <lean_source_dir> "
        f"--task_file {base}/autoform_targets.yaml "
        f"--book_dir {base}/autoform_book",
        "python -m autoform.visualizer.app "
        f"--runs-dir {base} --port 8003",
    )


def _markdown_report(payload: dict[str, object]) -> str:
    rows = payload.get("targets", [])
    lines = [
        "# Autoform Formalization Targets",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Targets: {payload.get('n_ok')}/{payload.get('n_targets')} export-clean",
        f"- YAML: `{payload.get('autoform_targets_yaml', '')}`",
        f"- Book dir: `{payload.get('autoform_book_dir', '')}`",
        f"- Fingerprint: `{payload.get('target_fingerprint')}`",
        "",
        "## Commands",
        "",
        *(f"- `{cmd}`" for cmd in payload.get("command_templates", []) or []),
        "",
    ]
    warnings = payload.get("warnings", [])
    if warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
    lines.extend(["## Targets", ""])
    if not rows:
        lines.append("No targets exported.")
    for row in rows:  # type: ignore[assignment]
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                f"### `{row.get('name')}`",
                "",
                f"- Kind: `{row.get('kind')}`",
                f"- Declaration: `{row.get('lean_declaration')}`",
                f"- Lean file: `{row.get('lean_file')}`",
                "",
            ]
        )
    errors = payload.get("errors", [])
    if errors:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines).rstrip() + "\n"
