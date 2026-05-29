from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_gap_audit import audit_research_gap_backlog


FORMAL_GAP_TASK_EXPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalGapLeanTask:
    schema_version: int
    task_id: str
    imports: tuple[str, ...]
    namespace: str
    statement: str
    allowed_sorry: bool
    tags: tuple[str, ...]
    dependencies: tuple[str, ...]
    expected_patterns: tuple[str, ...]
    question_id: str
    problem_class: str
    theorem_goal_id: str
    gap_id: str
    priority_hint: str
    artifact_path: str
    required_primitives: tuple[str, ...]
    retrieved_formal_sources: tuple[str, ...]
    primitive_formal_sources: dict[str, tuple[str, ...]]
    proof_strategy: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_gap_lean_tasks(
    run_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export FORMAL_GAP rows as Lean-task work packets.

    The trace/gap audits prove that the gaps are honest. This exporter turns
    those gaps into machine-readable theorem-development tasks compatible with
    the legacy `lean_task.schema.json` shape while preserving richer statistical
    metadata for routing and prioritization.
    """

    backlog = audit_research_gap_backlog(run_dir)
    rows = [_task_for_gap(row, run_dir) for row in backlog.get("rows", []) if isinstance(row, dict)]
    payload = {
        "schema_version": FORMAL_GAP_TASK_EXPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "n_tasks": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": bool(backlog.get("all_ok")) and bool(rows) and all(row.ok for row in rows),
        "source_gap_backlog": {
            "n_gaps": backlog.get("n_gaps"),
            "n_ok": backlog.get("n_ok"),
            "all_ok": backlog.get("all_ok"),
        },
        "task_fingerprint": stable_hash([asdict(row) for row in rows]),
        "tasks": [asdict(row) for row in rows],
        "schema_reference": "legacy_sources/ai_statistician/schemas/lean_task.schema.json",
        "limitations": [
            "FORMAL_GAP tasks are theorem-development work packets, not verified proofs",
            "allowed_sorry=true because each task still needs library/design work",
            "the exported statement is the current Lean skeleton artifact with placeholder assumptions",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        jsonl_path = out_dir / "formal_gap_lean_tasks.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(asdict(row), default=str) + "\n")
        payload["jsonl_path"] = str(jsonl_path)
        (out_dir / "formal_gap_lean_task_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_gap_lean_tasks.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _task_for_gap(raw: dict[str, Any], run_dir: Path) -> FormalGapLeanTask:
    errors: list[str] = []
    gap_id = str(raw.get("gap_id", ""))
    artifact_path = str(raw.get("artifact_path", ""))
    artifact = _resolve_artifact(artifact_path, run_dir)
    statement = ""
    if not artifact.exists():
        errors.append("gap Lean skeleton artifact missing")
    else:
        statement = artifact.read_text(encoding="utf-8", errors="ignore")
    imports = _imports_from_statement(statement)
    namespace = _namespace_from_statement(statement)
    if not imports:
        errors.append("task statement has no Lean imports")
    if not namespace:
        errors.append("task statement has no Lean namespace")
    if "FORMAL_GAP" not in statement:
        errors.append("task statement does not preserve FORMAL_GAP marker")
    if "theorem " not in statement:
        errors.append("task statement has no theorem declaration")
    required_primitives = tuple(str(item) for item in raw.get("required_primitives", []) or [] if str(item))
    retrieved_sources = tuple(str(item) for item in raw.get("retrieved_formal_sources", []) or [] if str(item))
    primitive_sources = {
        str(key): tuple(str(item) for item in value if str(item))
        for key, value in (raw.get("primitive_formal_sources", {}) or {}).items()
        if isinstance(value, (list, tuple))
    }
    if not required_primitives:
        errors.append("task has no required primitives")
    if not retrieved_sources:
        errors.append("task has no retrieved formal sources")
    dependencies = tuple(str(item) for item in raw.get("supporting_proof_obligations", []) or [] if str(item))
    expected_patterns = tuple(
        sorted(
            {
                "FORMAL_GAP",
                *required_primitives,
                *dependencies,
                *retrieved_sources[:5],
            }
        )
    )
    problem_class = str(raw.get("problem_class", ""))
    theorem_goal_id = str(raw.get("theorem_goal_id", ""))
    return FormalGapLeanTask(
        schema_version=FORMAL_GAP_TASK_EXPORT_SCHEMA_VERSION,
        task_id=_task_id(gap_id, problem_class, theorem_goal_id),
        imports=imports,
        namespace=namespace,
        statement=statement,
        allowed_sorry=True,
        tags=tuple(
            item
            for item in (
                "formal_gap",
                "lean_task",
                problem_class,
                theorem_goal_id,
                *required_primitives,
            )
            if item
        ),
        dependencies=dependencies,
        expected_patterns=expected_patterns,
        question_id=str(raw.get("question_id", "")),
        problem_class=problem_class,
        theorem_goal_id=theorem_goal_id,
        gap_id=gap_id,
        priority_hint=_priority_hint(raw),
        artifact_path=artifact_path,
        required_primitives=required_primitives,
        retrieved_formal_sources=retrieved_sources,
        primitive_formal_sources=primitive_sources,
        proof_strategy=str(raw.get("proof_strategy", "")),
        ok=not errors,
        errors=tuple(errors),
    )


def _task_id(gap_id: str, problem_class: str, theorem_goal_id: str) -> str:
    base = gap_id or f"{problem_class}:{theorem_goal_id}"
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "_", base).strip("_")
    return f"formal_gap:{cleaned}"


def _priority_hint(raw: dict[str, Any]) -> str:
    n_primitives = len(raw.get("required_primitives", []) or [])
    n_proofs = len(raw.get("supporting_proof_obligations", []) or [])
    n_sources = len(raw.get("retrieved_formal_sources", []) or [])
    if n_proofs and n_sources and n_primitives <= 3:
        return "bridge_ready_small"
    if n_proofs and n_sources:
        return "bridge_ready"
    if n_sources:
        return "local_source_grounded"
    return "library_design_required"


def _resolve_artifact(artifact_path: str, run_dir: Path) -> Path:
    path = Path(artifact_path)
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return run_dir / path


def _imports_from_statement(statement: str) -> tuple[str, ...]:
    imports = []
    for line in statement.splitlines():
        stripped = line.strip()
        if not stripped.startswith("import "):
            continue
        imports.extend(item for item in stripped.removeprefix("import ").split() if item)
    return tuple(dict.fromkeys(imports))


def _namespace_from_statement(statement: str) -> str:
    for line in statement.splitlines():
        match = re.match(r"\s*namespace\s+([A-Za-z_][A-Za-z0-9_'.]*)\b", line)
        if match:
            return match.group(1)
    return ""


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Gap Lean Tasks",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Tasks: {payload.get('n_ok')}/{payload.get('n_tasks')} audit-clean",
        f"- JSONL: `{payload.get('jsonl_path', '')}`",
        f"- Fingerprint: `{payload.get('task_fingerprint')}`",
        "",
        "## Tasks",
        "",
    ]
    rows = payload.get("tasks", [])
    if not rows:
        lines.append("No formal-gap Lean tasks exported.")
        return "\n".join(lines) + "\n"
    for row in rows:  # type: ignore[assignment]
        if not isinstance(row, dict):
            continue
        status = "OK" if row.get("ok") else "NEEDS_ATTENTION"
        lines.extend(
            [
                f"### `{row.get('task_id')}` [{status}]",
                "",
                f"- Problem class: `{row.get('problem_class')}`",
                f"- Theorem goal: `{row.get('theorem_goal_id')}`",
                f"- Priority hint: `{row.get('priority_hint')}`",
                f"- Imports: {', '.join(f'`{item}`' for item in row.get('imports', [])) or 'none'}",
                f"- Namespace: `{row.get('namespace')}`",
                f"- Required primitives: {', '.join(f'`{item}`' for item in row.get('required_primitives', [])) or 'none'}",
                f"- Dependencies: {', '.join(f'`{item}`' for item in row.get('dependencies', [])) or 'none'}",
                f"- Retrieved formal sources: {', '.join(f'`{item}`' for item in row.get('retrieved_formal_sources', [])[:5]) or 'none'}",
                "",
            ]
        )
        for error in row.get("errors", []) or []:
            lines.append(f"- Error: {error}")
        if row.get("errors"):
            lines.append("")
    return "\n".join(lines) + "\n"
