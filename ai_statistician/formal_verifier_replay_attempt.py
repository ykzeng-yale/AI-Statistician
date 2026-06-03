from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .schema import FormalObligation, ProofCheck, RetrievalHit
from .verifier import ProofVerifier


FORMAL_VERIFIER_REPLAY_ATTEMPT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayAttemptRecord:
    schema_version: int
    attempt_id: str
    replay_id: str
    source_queue_item_id: str
    route_id: str
    task_id: str
    theorem_goal_id: str
    display_name: str
    replay_mode: str
    source_formal_gap_task_id: str
    source_gap_id: str
    formal_statement: str
    proof_body: str
    verifier: str
    verification_strength: str
    kernel_verified: bool
    ok: bool
    reward: float
    elapsed_ms: int
    errors: tuple[str, ...]
    first_error: str
    first_error_category: str
    placeholder_assumption_removed: bool
    placeholder_references_in_candidate: tuple[str, ...]
    retrieval_hits: tuple[RetrievalHit, ...]
    acceptance_gate: str
    proof_evidence_boundary: str


async def export_formal_verifier_replay_attempts(
    formal_verifier_replay_dir: Path,
    out_dir: Path | None,
    *,
    verifier: ProofVerifier,
    formal_gap_tasks_dir: Path | None = None,
    max_tasks: int = 0,
) -> dict[str, object]:
    """Attempt full theorem/bridge replay targets under a verifier.

    This exporter writes attempt feedback for the calibration ledger. It strips
    `h_frontier_missing_*` assumptions from matched formal-gap skeletons before
    verification, so successful placeholder closures cannot become proof
    evidence.
    """

    errors: list[str] = []
    replay_manifest_path = formal_verifier_replay_dir / "formal_verifier_replay_manifest.json"
    replay_payload = _read_json(replay_manifest_path, errors)
    replay_tasks = [row for row in replay_payload.get("tasks", []) if isinstance(row, dict)]
    gap_manifest_path = (
        formal_gap_tasks_dir / "formal_gap_lean_task_manifest.json"
        if formal_gap_tasks_dir is not None
        else Path("__missing__")
    )
    gap_payload = _read_json(gap_manifest_path, errors) if formal_gap_tasks_dir is not None else {}
    gap_tasks = {
        str(row.get("task_id", "")): row
        for row in gap_payload.get("tasks", [])
        if isinstance(row, dict) and str(row.get("task_id", ""))
    }
    selected_tasks = replay_tasks[: max(0, max_tasks)]
    records: list[FormalVerifierReplayAttemptRecord] = []
    for index, task in enumerate(selected_tasks, start=1):
        records.append(
            await _attempt_task(
                task,
                verifier=verifier,
                gap_task=gap_tasks.get(str(task.get("task_id", "")), {}),
                attempt_index=index,
            )
        )
    n_kernel = sum(1 for row in records if row.kernel_verified)
    n_positive = sum(1 for row in records if row.ok)
    n_negative = sum(1 for row in records if not row.ok)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_ATTEMPT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_dir": str(formal_verifier_replay_dir),
        "formal_verifier_replay_manifest": str(replay_manifest_path),
        "formal_gap_tasks_dir": str(formal_gap_tasks_dir or ""),
        "formal_gap_task_manifest": str(gap_manifest_path) if formal_gap_tasks_dir is not None else "",
        "verifier": getattr(verifier, "name", type(verifier).__name__),
        "max_tasks": max_tasks,
        "n_source_replay_tasks": len(replay_tasks),
        "n_attempted": len(records),
        "n_positive": n_positive,
        "n_negative": n_negative,
        "n_kernel_verified": n_kernel,
        "n_non_kernel_positive": sum(1 for row in records if row.ok and not row.kernel_verified),
        "n_placeholder_removed": sum(1 for row in records if row.placeholder_assumption_removed),
        "n_with_formal_gap_task": sum(1 for row in records if row.source_formal_gap_task_id),
        "n_with_placeholder_reference": sum(1 for row in records if row.placeholder_references_in_candidate),
        "all_ok": not errors and all(not row.placeholder_references_in_candidate for row in records),
        "errors": errors,
        "attempt_log": str(out_dir / "formal_verifier_replay_attempts.jsonl") if out_dir is not None else "",
        "attempt_log_fingerprint": stable_hash([asdict(row) for row in records]),
        "rows": [asdict(row) for row in records],
        "limitations": [
            "replay attempts are full-route theorem/bridge attempts, not proof evidence unless kernel_verified=true",
            "matched formal-gap skeletons are stripped of h_frontier_missing placeholders before verification",
            "mock-positive attempts are calibration feedback only and require AXLE/local Lean replay",
            "failed attempts preserve earliest verifier errors for replay repair",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_verifier_replay_attempt_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_attempts.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), default=str, sort_keys=True) for row in records)
            + ("\n" if records else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_attempts.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


async def _attempt_task(
    task: dict[str, Any],
    *,
    verifier: ProofVerifier,
    gap_task: dict[str, Any],
    attempt_index: int,
) -> FormalVerifierReplayAttemptRecord:
    formal_statement, placeholder_removed = _formal_statement_for_task(task, gap_task)
    proof_body = _proof_body_for_task(task)
    retrieval_hits = _retrieval_hits_for_task(task)
    obligation = FormalObligation(
        id=str(task.get("replay_id", "")),
        title=str(task.get("display_name", "")),
        english=(
            "Full-route replay attempt generated from a FormalVerifier replay task. "
            "The target is unproved unless AXLE/local Lean verifies it."
        ),
        formal_statement=formal_statement,
        proof_body="",
        tags=tuple(
            item
            for item in (
                "formal_verifier_replay",
                str(task.get("problem_class", "")),
                str(task.get("theorem_goal_id", "")),
                str(task.get("replay_mode", "")),
            )
            if item
        ),
        expected_lemmas=tuple(
            str(item)
            for item in task.get("subclaim_replay_obligations", [])
            if str(item)
        ),
        source="formal_verifier_replay",
        depends_on=tuple(
            str(item)
            for item in task.get("related_proof_obligations", [])
            if str(item)
        ),
    )
    check = await verifier.verify(obligation, proof_body, retrieval_hits)
    placeholder_refs = _placeholder_references(formal_statement, proof_body)
    errors = tuple(check.errors)
    candidate_hash = stable_hash(
        {
            "replay_id": task.get("replay_id", ""),
            "formal_statement": formal_statement,
            "proof_body": proof_body,
            "verifier": check.verifier,
            "verification_strength": check.verification_strength,
            "kernel_verified": check.kernel_verified,
        }
    )
    return FormalVerifierReplayAttemptRecord(
        schema_version=FORMAL_VERIFIER_REPLAY_ATTEMPT_SCHEMA_VERSION,
        attempt_id=f"{task.get('replay_id', '')}:{attempt_index}:{candidate_hash[:16]}",
        replay_id=str(task.get("replay_id", "")),
        source_queue_item_id=str(task.get("source_queue_item_id", "")),
        route_id=str(task.get("route_id", "")),
        task_id=str(task.get("task_id", "")),
        theorem_goal_id=str(task.get("theorem_goal_id", "")),
        display_name=str(task.get("display_name", "")),
        replay_mode=str(task.get("replay_mode", "")),
        source_formal_gap_task_id=str(gap_task.get("task_id", "")),
        source_gap_id=str(gap_task.get("gap_id", "")),
        formal_statement=formal_statement,
        proof_body=proof_body,
        verifier=check.verifier,
        verification_strength=check.verification_strength,
        kernel_verified=bool(check.kernel_verified) and not placeholder_refs,
        ok=bool(check.ok) and not placeholder_refs,
        reward=1.0 if bool(check.ok) and bool(check.kernel_verified) and not placeholder_refs else 0.0,
        elapsed_ms=int(check.elapsed_ms),
        errors=errors if not placeholder_refs else (*errors, "candidate references h_frontier_missing placeholder"),
        first_error=(errors[0] if errors else "candidate references h_frontier_missing placeholder")
        if (errors or placeholder_refs)
        else "",
        first_error_category=_error_category(
            (errors[0] if errors else "candidate references h_frontier_missing placeholder")
            if (errors or placeholder_refs)
            else ""
        ),
        placeholder_assumption_removed=placeholder_removed,
        placeholder_references_in_candidate=placeholder_refs,
        retrieval_hits=tuple(check.retrieval_hits),
        acceptance_gate=str(task.get("acceptance_gate", "")),
        proof_evidence_boundary=(
            "This replay attempt is proof evidence only when kernel_verified=true "
            "and no h_frontier_missing placeholder is present in the target or proof body."
        ),
    )


def _formal_statement_for_task(task: dict[str, Any], gap_task: dict[str, Any]) -> tuple[str, bool]:
    statement = str(gap_task.get("statement", ""))
    if statement:
        stripped, removed = _strip_frontier_missing_placeholder(statement)
        return stripped, removed
    theorem_name = _lean_identifier(str(task.get("display_name", "")) or str(task.get("replay_id", "")))
    return (
        "\n".join(
            [
                "import Mathlib",
                "namespace AIStatisticianReplayAttempts",
                "",
                f"theorem {theorem_name} : True := by sorry",
                "",
                "end AIStatisticianReplayAttempts",
                "",
            ]
        ),
        False,
    )


def _strip_frontier_missing_placeholder(statement: str) -> tuple[str, bool]:
    lines = statement.splitlines()
    output: list[str] = []
    removed = False
    skip_placeholder = False
    skip_proof = False
    for line in lines:
        stripped = line.strip()
        if skip_proof:
            if re.match(r"\s*end\s+\S+", line):
                skip_proof = False
                output.append(line)
            continue
        if skip_placeholder:
            if ") :" in line:
                output.append(f"{line[: len(line) - len(line.lstrip())]}:")
                skip_placeholder = False
            continue
        if "(h_frontier_missing" in line:
            removed = True
            if ") :" in line:
                output.append(f"{line[: len(line) - len(line.lstrip())]}:")
            else:
                skip_placeholder = True
            continue
        if ":= by" in line:
            prefix = line.split(":= by", 1)[0].rstrip()
            output.append(f"{prefix} := by sorry")
            skip_proof = True
            continue
        if "placeholder assumption named `h_frontier_missing_*`" in line:
            output.append(
                line.replace("placeholder assumption", "removed placeholder assumption").replace(
                    "h_frontier_missing_*",
                    "frontier_missing_placeholder_removed",
                )
            )
            continue
        if stripped.startswith("Status: FORMAL_GAP."):
            output.append("Status: FULL_ROUTE_REPLAY_ATTEMPT.")
            continue
        output.append(line)
    return "\n".join(output).rstrip() + "\n", removed


def _proof_body_for_task(task: dict[str, Any]) -> str:
    return "\n".join(
        [
            "by",
            "  -- Non-placeholder full-route replay probe.",
            "  -- This may fail; the verifier error is calibration feedback.",
            "  first | rfl | simp",
        ]
    )


def _retrieval_hits_for_task(task: dict[str, Any]) -> list[RetrievalHit]:
    hits: list[RetrievalHit] = []
    for index, obligation_id in enumerate(task.get("subclaim_replay_obligations", []) or []):
        if not str(obligation_id):
            continue
        hits.append(
            RetrievalHit(
                obligation_id=str(obligation_id),
                score=max(0.0, 1.0 - index * 0.05),
                source="formal_verifier_replay_subclaim",
                matched_terms=(str(task.get("replay_mode", "")),),
            )
        )
    return hits


def _placeholder_references(formal_statement: str, proof_body: str) -> tuple[str, ...]:
    refs = sorted(set(re.findall(r"\bh_frontier_missing[A-Za-z0-9_']*", formal_statement + "\n" + proof_body)))
    return tuple(refs)


def _lean_identifier(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_") or "replay_attempt"
    if cleaned[0].isdigit():
        cleaned = f"replay_{cleaned}"
    return cleaned


def _error_category(error: str) -> str:
    lowered = error.lower()
    if not lowered:
        return "none"
    if "timeout" in lowered:
        return "timeout"
    if "placeholder" in lowered or "sorry" in lowered or "h_frontier_missing" in lowered:
        return "placeholder_or_gap"
    if "unknown identifier" in lowered or "unknown constant" in lowered or "no declaration" in lowered:
        return "missing_identifier"
    if "type mismatch" in lowered or "has type" in lowered or "expected" in lowered:
        return "type_mismatch"
    if "unsolved goals" in lowered or "unsolved goal" in lowered:
        return "unsolved_goals"
    if "made no progress" in lowered:
        return "tactic_no_progress"
    if "kernel" in lowered:
        return "kernel_error"
    return "other"


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
        "# Formal Verifier Replay Attempts",
        "",
        f"- Replay manifest: `{payload.get('formal_verifier_replay_manifest')}`",
        f"- Formal gap tasks: `{payload.get('formal_gap_task_manifest')}`",
        f"- Verifier: `{payload.get('verifier')}`",
        f"- Attempted: {payload.get('n_attempted')}/{payload.get('n_source_replay_tasks')}",
        f"- Positive: {payload.get('n_positive')}",
        f"- Kernel verified: {payload.get('n_kernel_verified')}",
        f"- Failed: {payload.get('n_negative')}",
        "",
        "Replay attempts are verifier feedback for full theorem/bridge targets.",
        "",
        "## Attempts",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No replay attempts were run.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}`: ok={row.get('ok')} "
                f"kernel={row.get('kernel_verified')} error={row.get('first_error_category')}"
            )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
