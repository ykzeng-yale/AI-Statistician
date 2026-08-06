from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_APPLICATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairApplicationTask:
    schema_version: int
    application_id: str
    packet_id: str
    replay_id: str
    latest_attempt_id: str
    source_queue_item_id: str
    route_id: str
    task_id: str
    theorem_goal_id: str
    display_name: str
    repair_class: str
    application_mode: str
    priority_score: int
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    imports: tuple[str, ...]
    namespace: str
    source_formal_statement: str
    failed_proof_body: str
    proof_body_template_not_verified: str
    lean_repair_source_not_verified: str
    artifact_path: str
    required_primitives: tuple[str, ...]
    subclaim_replay_obligations: tuple[str, ...]
    retrieval_hit_obligations: tuple[str, ...]
    related_proof_obligations: tuple[str, ...]
    route_specific_repair_steps: tuple[str, ...]
    verification_commands: tuple[str, ...]
    acceptance_gate: str
    proof_evidence_boundary: str
    training_prompt: str
    training_completion: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_application_tasks(
    formal_verifier_replay_repair_dir: Path,
    formal_verifier_replay_attempt_dir: Path,
    out_dir: Path | None = None,
    *,
    max_tasks: int = 20,
) -> dict[str, object]:
    """Export model-regeneration contexts from failed replay candidates."""

    errors: list[str] = []
    repair_manifest_path = (
        formal_verifier_replay_repair_dir / "formal_verifier_replay_repair_manifest.json"
    )
    attempt_manifest_path = (
        formal_verifier_replay_attempt_dir / "formal_verifier_replay_attempt_manifest.json"
    )
    repair_payload = _read_json(repair_manifest_path, errors)
    attempt_payload = _read_json(attempt_manifest_path, errors)
    attempts_by_replay = {
        str(row.get("replay_id", "")): row
        for row in attempt_payload.get("rows", [])
        if isinstance(row, dict) and str(row.get("replay_id", ""))
    }
    source_packets = [
        row
        for row in repair_payload.get("packets", [])
        if isinstance(row, dict) and bool(row.get("ok", True))
    ]
    source_packets = sorted(
        source_packets,
        key=lambda row: (-_safe_int(row.get("priority_score", 0)), str(row.get("packet_id", ""))),
    )[: max(0, max_tasks)]
    tasks = [
        _application_task_from_packet(
            packet,
            attempt=attempts_by_replay.get(str(packet.get("replay_id", "")), {}),
            out_dir=out_dir,
        )
        for packet in source_packets
    ]
    by_mode = Counter(task.application_mode for task in tasks)
    by_repair_class = Counter(task.repair_class for task in tasks)
    training_examples = [
        {
            "example_id": task.application_id,
            "task": "formal_verifier_replay_repair_application",
            "prompt": task.training_prompt,
            "completion": task.training_completion,
            "packet_id": task.packet_id,
            "replay_id": task.replay_id,
            "application_mode": task.application_mode,
            "claim_status": "repair_application_task_not_proof_evidence",
        }
        for task in tasks
    ]
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_APPLICATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_dir": str(formal_verifier_replay_repair_dir),
        "formal_verifier_replay_repair_manifest": str(repair_manifest_path),
        "formal_verifier_replay_attempt_dir": str(formal_verifier_replay_attempt_dir),
        "formal_verifier_replay_attempt_manifest": str(attempt_manifest_path),
        "max_tasks": max_tasks,
        "n_source_repair_packets": len(repair_payload.get("packets", []) or []),
        "n_application_tasks": len(tasks),
        "n_ok": sum(1 for task in tasks if task.ok),
        "all_ok": not errors and all(task.ok for task in tasks),
        "errors": errors,
        "n_bridge_lemma_applications": by_mode.get("bridge_lemma_then_exact_subclaim_composition", 0),
        "n_import_or_declaration_applications": by_mode.get("import_or_declaration_patch_then_replay", 0),
        "n_statement_alignment_applications": by_mode.get("statement_alignment_bridge_patch", 0),
        "n_placeholder_replacement_applications": by_mode.get("placeholder_replacement_bridge_patch", 0),
        "n_tactic_no_progress_applications": by_repair_class.get("route_specific_subclaim_composition", 0),
        "n_with_source_statement": sum(1 for task in tasks if bool(task.source_formal_statement)),
        "n_with_artifact": sum(1 for task in tasks if bool(task.artifact_path)),
        "n_training_examples": len(training_examples),
        "by_application_mode": dict(sorted(by_mode.items())),
        "by_repair_class": dict(sorted(by_repair_class.items())),
        "tasks": [asdict(task) for task in tasks],
        "training_examples": training_examples,
        "application_fingerprint": stable_hash([asdict(task) for task in tasks]),
        "limitations": [
            "regeneration contexts are not Lean proof evidence",
            "lean_repair_source_not_verified contains context only and is not a candidate",
            "the harness does not choose imports, declarations, tactics, or edits",
            "completion requires rerunning formal-verifier-replay-attempts and recalibrating to full_route_kernel_verified",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        lean_dir = out_dir / "lean_repair_tasks"
        lean_dir.mkdir(parents=True, exist_ok=True)
        for task in tasks:
            if task.artifact_path:
                Path(task.artifact_path).write_text(
                    task.lean_repair_source_not_verified,
                    encoding="utf-8",
                )
        (out_dir / "formal_verifier_replay_repair_application_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_application_tasks.jsonl").write_text(
            "\n".join(json.dumps(asdict(task), sort_keys=True) for task in tasks)
            + ("\n" if tasks else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_application_training.jsonl").write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in training_examples)
            + ("\n" if training_examples else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_application.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _application_task_from_packet(
    packet: dict[str, Any],
    *,
    attempt: dict[str, Any],
    out_dir: Path | None,
) -> FormalVerifierReplayRepairApplicationTask:
    errors: list[str] = []
    packet_id = str(packet.get("packet_id", ""))
    replay_id = str(packet.get("replay_id", ""))
    display_name = str(packet.get("display_name", ""))
    repair_class = str(packet.get("repair_class", ""))
    target_name = str(packet.get("target_theorem_name", ""))
    bridge_name = str(packet.get("candidate_bridge_lemma_name", ""))
    source_statement = str(attempt.get("formal_statement", ""))
    failed_proof_body = str(attempt.get("proof_body", ""))
    imports = _imports_from_statement(source_statement)
    namespace = _namespace_from_statement(source_statement) or "AIStatisticianReplayRepair"
    proof_template = str(packet.get("proof_body_template_not_verified", ""))
    application_mode = _application_mode(repair_class)
    source_key = _safe_file_stem(display_name or replay_id or packet_id)
    artifact_path = (
        str((out_dir / "lean_repair_tasks" / f"{source_key}.lean").resolve())
        if out_dir is not None
        else ""
    )
    verification_commands = (
        "python3 -m ai_statistician.cli formal-verifier-replay-attempts --formal-verifier-replay-dir <replay-dir> --formal-gap-tasks-dir <formal-gap-tasks-dir> --local-lean --lean-project <lean-project> --max-tasks <n> --out <attempt-out>",
        "python3 -m ai_statistician.cli formal-verifier-replay-calibration --formal-verifier-replay-dir <replay-dir> --attempt-log <attempt-out>/formal_verifier_replay_attempts.jsonl --out <calibration-out>",
        "accept only if replay_calibration_status is full_route_kernel_verified and no h_frontier_missing placeholder remains",
    )
    lean_source = _lean_repair_source(
        packet=packet,
        attempt=attempt,
        imports=imports,
        namespace=namespace,
        application_mode=application_mode,
    )
    if not packet_id:
        errors.append("packet_id missing")
    if not replay_id:
        errors.append("replay_id missing")
    if not display_name:
        errors.append("display_name missing")
    if not target_name:
        errors.append("target_theorem_name missing")
    if not source_statement:
        errors.append("source formal statement missing")
    application_id = (
        "formal_verifier_replay_repair_application:"
        f"{stable_hash([packet_id, replay_id, application_mode, bridge_name])[:16]}"
    )
    return FormalVerifierReplayRepairApplicationTask(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_APPLICATION_SCHEMA_VERSION,
        application_id=application_id,
        packet_id=packet_id,
        replay_id=replay_id,
        latest_attempt_id=str(packet.get("latest_attempt_id") or attempt.get("attempt_id", "")),
        source_queue_item_id=str(packet.get("source_queue_item_id", "")),
        route_id=str(packet.get("route_id", "")),
        task_id=str(packet.get("task_id", "")),
        theorem_goal_id=str(packet.get("theorem_goal_id", "")),
        display_name=display_name,
        repair_class=repair_class,
        application_mode=application_mode,
        priority_score=_safe_int(packet.get("priority_score", 0)),
        target_theorem_name=target_name,
        candidate_bridge_lemma_name=bridge_name,
        imports=imports,
        namespace=namespace,
        source_formal_statement=source_statement,
        failed_proof_body=failed_proof_body,
        proof_body_template_not_verified=proof_template,
        lean_repair_source_not_verified=lean_source,
        artifact_path=artifact_path,
        required_primitives=_str_tuple(packet.get("required_primitives", [])),
        subclaim_replay_obligations=_str_tuple(packet.get("subclaim_replay_obligations", [])),
        retrieval_hit_obligations=_str_tuple(packet.get("retrieval_hit_obligations", [])),
        related_proof_obligations=_str_tuple(packet.get("related_proof_obligations", [])),
        route_specific_repair_steps=_str_tuple(packet.get("route_specific_repair_steps", [])),
        verification_commands=verification_commands,
        acceptance_gate=str(packet.get("acceptance_gate", "")),
        proof_evidence_boundary=(
            "This repair application task is not proof evidence. It becomes evidence only "
            "after the repaired full-route replay attempt passes AXLE/local Lean and "
            "calibration reports full_route_kernel_verified."
        ),
        training_prompt=_training_prompt(packet, attempt, lean_source, verification_commands),
        training_completion=json.dumps(
            {
                "application_mode": application_mode,
                "candidate_source": "complete revised Lean source supplied by the proof agent",
                "claim_status": "repair_application_task_not_proof_evidence",
                "verification_commands": list(verification_commands),
            },
            sort_keys=True,
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _application_mode(repair_class: str) -> str:
    return "complete_candidate_regeneration"


def _lean_repair_source(
    *,
    packet: dict[str, Any],
    attempt: dict[str, Any],
    imports: tuple[str, ...],
    namespace: str,
    application_mode: str,
) -> str:
    packet_id = str(packet.get("packet_id", ""))
    display_name = str(packet.get("display_name", ""))
    subclaims = _str_tuple(packet.get("subclaim_replay_obligations", []))
    retrieval_hits = _str_tuple(packet.get("retrieval_hit_obligations", []))
    failed_proof_body = str(attempt.get("proof_body", "")).strip()
    return "\n".join(
        [
            "/-",
            "FORMAL VERIFIER REPLAY MODEL REGENERATION CONTEXT",
            f"Packet: {packet_id}",
            f"Route: {display_name}",
            f"Application mode: {application_mode}",
            "",
            "This file is context. It is not proof evidence or a Lean candidate.",
            "The proof agent must return one complete revised candidate for the unchanged target.",
            "",
            "Complete current formal statement:",
            _indent_block(str(attempt.get("formal_statement", "")).strip() or "(missing source statement)"),
            "",
            "Exact verifier diagnostics:",
            _indent_block(str(packet.get("first_error", "")).strip() or "(no diagnostics recorded)"),
            "",
            "Subclaim replay obligations:",
            *[f"- {item}" for item in subclaims],
            "Attempt retrieval hits:",
            *[f"- {item}" for item in retrieval_hits],
            "",
            "Complete current proof body:",
            _indent_block(failed_proof_body or "(missing failed proof body)"),
            "-/",
            "",
        ]
    )


def _training_prompt(
    packet: dict[str, Any],
    attempt: dict[str, Any],
    lean_source: str,
    verification_commands: tuple[str, ...],
) -> str:
    return "\n".join(
        [
            "You are revising a failed FormalVerifier candidate.",
            "Return one complete revised Lean source file for the unchanged theorem target.",
            "Do not claim the theorem is proved.",
            "",
            f"Packet id: {packet.get('packet_id', '')}",
            f"Replay id: {packet.get('replay_id', '')}",
            f"Route: {packet.get('display_name', '')}",
            f"First error: {packet.get('first_error', '')}",
            "",
            "Complete current statement:",
            "```lean",
            str(attempt.get("formal_statement", "")).strip(),
            "```",
            "",
            "Complete regeneration context (not proof evidence):",
            "```lean",
            lean_source.strip(),
            "```",
            "",
            "Verification commands after applying the repair:",
            "\n".join(f"- {command}" for command in verification_commands),
        ]
    )


def _imports_from_statement(statement: str) -> tuple[str, ...]:
    imports: list[str] = []
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


def _safe_file_stem(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.-") or "replay_repair"
    if cleaned[0].isdigit():
        cleaned = f"repair_{cleaned}"
    return cleaned[:120]


def _indent_block(text: str) -> str:
    return "\n".join(f"  {line}" for line in text.splitlines())


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Replay Repair Application Tasks",
        "",
        f"- Repair manifest: `{payload.get('formal_verifier_replay_repair_manifest')}`",
        f"- Attempt manifest: `{payload.get('formal_verifier_replay_attempt_manifest')}`",
        f"- Tasks: {payload.get('n_ok')}/{payload.get('n_application_tasks')} audit-clean",
        f"- Bridge/subclaim applications: {payload.get('n_bridge_lemma_applications')}",
        f"- Import/declaration applications: {payload.get('n_import_or_declaration_applications')}",
        "",
        "Application tasks are Lean repair scaffolds, not proof evidence.",
        "",
        "## Tasks",
        "",
    ]
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        lines.append("No replay repair application tasks were exported.")
    else:
        for task in tasks[:30]:
            if not isinstance(task, dict):
                continue
            lines.append(
                f"- `{task.get('display_name')}` ({task.get('application_mode')}): "
                f"{task.get('candidate_bridge_lemma_name')}"
            )
            lines.append(f"  artifact: `{task.get('artifact_path')}`")
            lines.append(f"  boundary: {task.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
