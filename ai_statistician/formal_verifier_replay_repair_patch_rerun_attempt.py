from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_ATTEMPT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunAttemptRow:
    schema_version: int
    rerun_attempt_id: str
    rerun_id: str
    response_validation_id: str
    promotion_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    patched_artifact_path: str
    patched_artifact_exists: bool
    patched_artifact_readable: bool
    changed_lean_declarations: tuple[str, ...]
    residual_formal_gaps: tuple[str, ...]
    local_lean_checked: bool
    local_lean_compiled: bool
    local_lean_project: str
    local_lean_errors: tuple[str, ...]
    verification_strength: str
    artifact_placeholder_free: bool
    contains_patch_proposal_marker: bool
    contains_non_evidence_boundary: bool
    rerun_attempt_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    elapsed_ms: int
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_attempts(
    formal_verifier_replay_repair_patch_rerun_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    max_items: int = 0,
) -> dict[str, object]:
    """Verify queued repair patch artifacts as post-patch rerun attempts."""

    errors: list[str] = []
    queue_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_queue_dir
        / "formal_verifier_replay_repair_patch_rerun_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    queue_rows = [row for row in queue_payload.get("rows", []) if isinstance(row, dict)]
    ready_rows = [
        row
        for row in queue_rows
        if str(row.get("rerun_status", "")) == "READY_FOR_PATCH_REPLAY_CALIBRATION"
    ]
    selected_rows = ready_rows[:max_items] if max_items and max_items > 0 else ready_rows
    lean_project_path = Path(lean_project) if lean_project else None
    rows = [
        _attempt_row(
            row,
            queue_dir=formal_verifier_replay_repair_patch_rerun_queue_dir,
            lean_project=lean_project_path,
            lean_timeout=lean_timeout,
        )
        for row in selected_rows
    ]
    by_status = Counter(row.rerun_attempt_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_ATTEMPT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_queue_dir": str(
            formal_verifier_replay_repair_patch_rerun_queue_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_queue_manifest": str(queue_manifest_path),
        "n_source_queue_rows": len(queue_rows),
        "n_ready_queue_rows": len(ready_rows),
        "max_items": max_items,
        "n_rerun_attempt_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_artifact_exists": sum(1 for row in rows if row.patched_artifact_exists),
        "n_artifact_readable": sum(1 for row in rows if row.patched_artifact_readable),
        "local_lean_enabled": lean_project_path is not None,
        "local_lean_project": str(lean_project or ""),
        "local_lean_timeout": lean_timeout,
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "n_artifact_placeholder_free": sum(
            1 for row in rows if row.artifact_placeholder_free
        ),
        "n_with_patch_proposal_marker": sum(
            1 for row in rows if row.contains_patch_proposal_marker
        ),
        "n_with_residual_formal_gaps": sum(1 for row in rows if row.residual_formal_gaps),
        "by_rerun_attempt_status": dict(sorted(by_status.items())),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "rows": [asdict(row) for row in rows],
        "rerun_attempt_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "patch-rerun attempts verify patched artifacts as source files, not theorem proof evidence",
            "a patch artifact that compiles may still be only a patch proposal with residual formal gaps",
            "proof promotion still requires patch rerun calibration to report full_route_kernel_verified",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir / "formal_verifier_replay_repair_patch_rerun_attempt_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "formal_verifier_replay_repair_patch_rerun_attempts.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "formal_verifier_replay_repair_patch_rerun_attempts.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _attempt_row(
    row: dict[str, Any],
    *,
    queue_dir: Path,
    lean_project: Path | None,
    lean_timeout: int,
) -> FormalVerifierReplayRepairPatchRerunAttemptRow:
    errors: list[str] = []
    rerun_id = str(row.get("rerun_id", ""))
    replay_id = str(row.get("replay_id", ""))
    route_id = str(row.get("route_id", ""))
    display_name = str(row.get("display_name", ""))
    changed_declarations = _str_tuple(row.get("changed_lean_declarations", []))
    residual_gaps = _str_tuple(row.get("residual_formal_gaps", []))
    artifact_path = _resolve_artifact_path(str(row.get("patched_artifact_path", "")), queue_dir)
    artifact_exists = artifact_path.exists()
    artifact_readable = False
    content = ""
    if not str(row.get("patched_artifact_path", "")):
        errors.append("patched_artifact_path missing")
    elif not artifact_exists:
        errors.append(f"patched_artifact_path does not exist: {artifact_path}")
    else:
        try:
            content = artifact_path.read_text(encoding="utf-8")
            artifact_readable = True
        except Exception as exc:
            errors.append(f"failed to read patched_artifact_path: {type(exc).__name__}: {exc}")

    if not rerun_id:
        errors.append("rerun_id missing")
    if not replay_id:
        errors.append("replay_id missing")
    if not route_id:
        errors.append("route_id missing")
    if not display_name:
        errors.append("display_name missing")
    if not changed_declarations:
        errors.append("changed_lean_declarations missing")

    artifact_placeholder_free = not bool(
        re.search(r"\bh_frontier_missing[A-Za-z0-9_']*", content)
    )
    contains_patch_marker = "PATCH_PROPOSAL_NOT_PROOF_EVIDENCE" in content
    contains_boundary = (
        "not theorem proof evidence" in content
        or "not proof evidence" in content
        or "not Lean proof evidence" in content
    )
    if artifact_readable and not artifact_placeholder_free:
        errors.append("patched artifact still references h_frontier_missing")
    if artifact_readable and not contains_boundary:
        errors.append("patched artifact non-evidence boundary missing")

    local_checked = False
    local_compiled = False
    local_errors: tuple[str, ...] = ()
    elapsed_ms = 0
    verification_strength = "patch_artifact_static"
    if lean_project is not None and artifact_readable:
        local_checked = True
        local_compiled, local_errors, elapsed_ms = _run_local_lean(
            artifact_path,
            lean_project,
            lean_timeout,
        )
        verification_strength = "local_lean_patch_artifact_kernel"
        if not local_compiled:
            errors.append("local Lean patch artifact compile failed")

    if not artifact_readable:
        status = "PATCH_ARTIFACT_BLOCKED_INPUT"
    elif lean_project is None:
        status = "PATCH_ARTIFACT_AWAITING_LOCAL_LEAN"
    elif local_compiled:
        status = "PATCH_ARTIFACT_COMPILES_NOT_PROOF_EVIDENCE"
    else:
        status = "PATCH_ARTIFACT_COMPILE_FAILED"
    return FormalVerifierReplayRepairPatchRerunAttemptRow(
        schema_version=FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_ATTEMPT_SCHEMA_VERSION,
        rerun_attempt_id=(
            "formal_verifier_replay_repair_patch_rerun_attempt:"
            f"{stable_hash([rerun_id, artifact_path, verification_strength])[:16]}"
        ),
        rerun_id=rerun_id,
        response_validation_id=str(row.get("response_validation_id", "")),
        promotion_id=str(row.get("promotion_id", "")),
        replay_id=replay_id,
        route_id=route_id,
        display_name=display_name,
        target_theorem_name=str(row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(row.get("candidate_bridge_lemma_name", "")),
        patched_artifact_path=str(artifact_path),
        patched_artifact_exists=artifact_exists,
        patched_artifact_readable=artifact_readable,
        changed_lean_declarations=changed_declarations,
        residual_formal_gaps=residual_gaps,
        local_lean_checked=local_checked,
        local_lean_compiled=local_compiled,
        local_lean_project=str(lean_project or ""),
        local_lean_errors=local_errors,
        verification_strength=verification_strength,
        artifact_placeholder_free=artifact_placeholder_free,
        contains_patch_proposal_marker=contains_patch_marker,
        contains_non_evidence_boundary=contains_boundary,
        rerun_attempt_status=status,
        proof_evidence_status="PATCH_RERUN_ATTEMPT_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This row is a patched-artifact rerun attempt. It is not theorem proof "
            "evidence unless the downstream patch-rerun calibration reports "
            "full_route_kernel_verified with no residual formal gaps."
        ),
        elapsed_ms=elapsed_ms,
        ok=not errors and (lean_project is None or local_compiled),
        errors=tuple(errors),
    )


def _resolve_artifact_path(raw: str, queue_dir: Path) -> Path:
    if not raw:
        return Path("__missing__")
    path = Path(raw)
    if path.is_absolute() or path.exists():
        return path
    for base in (queue_dir, queue_dir.parent, queue_dir.parent.parent):
        candidate = base / path
        if candidate.exists():
            return candidate
    return path


def _run_local_lean(lean_file: Path, lean_project: Path, timeout_s: int) -> tuple[bool, tuple[str, ...], int]:
    import time

    start = time.perf_counter()
    if shutil.which("lake") is None:
        return False, ("lake executable not found",), int((time.perf_counter() - start) * 1000)
    if not lean_project.exists():
        return (
            False,
            (f"lean project does not exist: {lean_project}",),
            int((time.perf_counter() - start) * 1000),
        )
    try:
        result = subprocess.run(
            ["lake", "env", "lean", str(lean_file.resolve())],
            cwd=str(lean_project),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return False, (f"local Lean timed out after {timeout_s}s",), int(
            (time.perf_counter() - start) * 1000
        )
    except Exception as exc:
        return False, (f"{type(exc).__name__}: {exc}",), int(
            (time.perf_counter() - start) * 1000
        )
    output = "\n".join(item for item in (result.stdout.strip(), result.stderr.strip()) if item)
    errors = tuple(line for line in output.splitlines() if line.strip())
    return result.returncode == 0, (() if result.returncode == 0 else errors), int(
        (time.perf_counter() - start) * 1000
    )


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


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Repair Patch Rerun Attempts",
        "",
        f"- Queue manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_queue_manifest')}`",
        f"- Attempt rows: {payload.get('n_ok')}/{payload.get('n_rerun_attempt_rows')} audit-clean",
        f"- Local Lean checked: {payload.get('n_local_lean_checked')}",
        f"- Local Lean compiled: {payload.get('n_local_lean_compiled')}",
        f"- Patch proposal markers: {payload.get('n_with_patch_proposal_marker')}",
        "",
        "These rows verify patched artifacts as source files; they are not theorem proof evidence.",
        "",
        "## Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No ready patch-rerun queue rows were attempted.")
    else:
        for row in rows[:30]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` ({row.get('rerun_attempt_status')}): "
                f"compiled={row.get('local_lean_compiled')}, residual_gaps={len(row.get('residual_formal_gaps') or [])}"
            )
            lines.append(f"  artifact: `{row.get('patched_artifact_path')}`")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
