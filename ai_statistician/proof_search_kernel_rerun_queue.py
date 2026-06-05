from __future__ import annotations

import json
import shlex
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .proof_bank import all_obligations


PROOF_SEARCH_KERNEL_RERUN_QUEUE_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "PROOF_SEARCH_KERNEL_RERUN_QUEUE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Proof-search kernel-rerun queue rows identify mock/static solved proof "
    "bodies that need AXLE/local Lean replay. They are not proof evidence; "
    "proof-search evidence starts only after the selected proof body passes "
    "AXLE or local Lean kernel verification."
)


@dataclass(frozen=True)
class ProofSearchKernelRerunQueueRow:
    schema_version: int
    rerun_queue_id: str
    obligation_id: str
    title: str
    tags: tuple[str, ...]
    selected_candidate_id: str
    selected_source: str
    selected_verifier: str
    selected_verification_strength: str
    selected_kernel_verified: bool
    selected_proof_body: str
    selected_proof_body_hash: str
    selected_search_fingerprint: str
    prior_nodes_expanded: int
    prior_candidates_total: int
    prior_formal_source_candidates_total: int
    status: str
    owner_agent: str
    priority: str
    required_gate: str
    command_plan: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_proof_search_kernel_rerun_queue(
    proof_search_audit_dir: Path,
    out_dir: Path | None = None,
    *,
    local_lean_project: str | Path | None = None,
    local_lean_timeout: int = 90,
    max_rows: int = 50,
) -> dict[str, object]:
    """Queue mock/static proof-search solutions for AXLE/local Lean replay."""

    if max_rows < 0:
        raise ValueError("max_rows must be nonnegative")
    errors: list[str] = []
    manifest_path = proof_search_audit_dir / "proof_search_audit_manifest.json"
    manifest = _read_json(manifest_path, errors)
    results_jsonl = _results_jsonl_path(proof_search_audit_dir, manifest)
    result_rows = _read_jsonl(results_jsonl, errors)
    obligations = {row.id: row for row in all_obligations()}
    rerun_out_dir = _default_rerun_output_dir(out_dir)
    base_command = _batch_rerun_command(
        manifest,
        out_dir=rerun_out_dir,
        local_lean_project=local_lean_project,
        local_lean_timeout=local_lean_timeout,
    )
    rows = [
        _queue_row(
            row,
            obligations=obligations,
            manifest_path=manifest_path,
            results_jsonl=results_jsonl,
            batch_rerun_command=base_command,
        )
        for row in result_rows
        if _needs_kernel_rerun(row)
    ]
    rows = sorted(rows, key=lambda row: (row.priority != "high", row.obligation_id))[:max_rows]
    by_status = Counter(row.status for row in rows)
    proof_status = PROOF_EVIDENCE_STATUS
    payload: dict[str, object] = {
        "schema_version": PROOF_SEARCH_KERNEL_RERUN_QUEUE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_search_audit_dir": str(proof_search_audit_dir),
        "proof_search_audit_manifest": str(manifest_path),
        "proof_search_results_jsonl": str(results_jsonl),
        "source_verifier": str(manifest.get("verifier", "")),
        "source_verifier_requires_kernel": "kernel" in str(manifest.get("verifier", "")).lower(),
        "source_max_obligations": int(manifest.get("max_obligations", 0) or 0),
        "source_max_nodes": int(manifest.get("max_nodes", 0) or 0),
        "source_include_registered_proof": bool(manifest.get("include_registered_proof", True)),
        "source_include_invalid_probe": bool(manifest.get("include_invalid_probe", False)),
        "n_source_result_rows": len(result_rows),
        "n_source_solved": sum(1 for row in result_rows if bool(row.get("solved", False))),
        "n_source_kernel_verified": sum(
            1 for row in result_rows if bool(row.get("kernel_verified", False))
        ),
        "n_source_needs_kernel_rerun": sum(1 for row in result_rows if _needs_kernel_rerun(row)),
        "n_queue_rows": len(rows),
        "n_ready_for_local_lean_or_axle": by_status.get("READY_FOR_LOCAL_LEAN_OR_AXLE_RERUN", 0),
        "n_blocked_missing_selected_proof_body": by_status.get(
            "BLOCKED_SELECTED_PROOF_BODY_MISSING",
            0,
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_status": dict(sorted(by_status.items())),
        "local_lean_project": str(local_lean_project or ""),
        "local_lean_timeout": int(local_lean_timeout),
        "local_lean_rerun_out_dir": str(rerun_out_dir),
        "batch_local_lean_rerun_command": _command_string(base_command),
        "rows": [asdict(row) for row in rows],
        "rerun_queue_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": proof_status,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "queue rows are replay targets, not theorem proof evidence",
            "mock/static proof-search success must not be reported as kernel evidence",
            "the batch rerun command replays the audit frontier; promotion requires AXLE/local Lean success rows",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "proof_search_kernel_rerun_queue_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "proof_search_kernel_rerun_queue.jsonl").write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (out_dir / "proof_search_kernel_rerun_queue.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _queue_row(
    row: dict[str, Any],
    *,
    obligations: dict[str, Any],
    manifest_path: Path,
    results_jsonl: Path,
    batch_rerun_command: tuple[str, ...],
) -> ProofSearchKernelRerunQueueRow:
    errors: list[str] = []
    obligation_id = str(row.get("obligation_id", ""))
    obligation = obligations.get(obligation_id)
    proof_body = str(row.get("selected_proof_body", ""))
    if not obligation_id:
        errors.append("obligation_id missing")
    if obligation is None:
        errors.append(f"unknown proof-bank obligation_id={obligation_id}")
    if not proof_body.strip():
        errors.append("selected_proof_body missing")
    status = (
        "READY_FOR_LOCAL_LEAN_OR_AXLE_RERUN"
        if proof_body.strip()
        else "BLOCKED_SELECTED_PROOF_BODY_MISSING"
    )
    command_plan = (
        _command_string(batch_rerun_command),
        "inspect proof_search_results.jsonl for the same obligation_id and require kernel_verified=true",
        "promote only AXLE/local Lean verified rows into proof-search evidence counts",
    )
    return ProofSearchKernelRerunQueueRow(
        schema_version=PROOF_SEARCH_KERNEL_RERUN_QUEUE_SCHEMA_VERSION,
        rerun_queue_id="proof_search_kernel_rerun_queue:"
        + stable_hash([obligation_id, row.get("selected_candidate_id", ""), proof_body])[:16],
        obligation_id=obligation_id,
        title=str(getattr(obligation, "title", "")),
        tags=tuple(str(tag) for tag in getattr(obligation, "tags", ()) if str(tag)),
        selected_candidate_id=str(row.get("selected_candidate_id", "")),
        selected_source=str(row.get("selected_source", "")),
        selected_verifier=str(row.get("verifier", "")),
        selected_verification_strength=str(row.get("selected_verification_strength", "")),
        selected_kernel_verified=bool(row.get("kernel_verified", False)),
        selected_proof_body=proof_body,
        selected_proof_body_hash=stable_hash(proof_body),
        selected_search_fingerprint=str(row.get("search_fingerprint", "")),
        prior_nodes_expanded=int(row.get("nodes_expanded", 0) or 0),
        prior_candidates_total=int(row.get("candidates_total", 0) or 0),
        prior_formal_source_candidates_total=int(
            row.get("formal_source_candidates_total", 0) or 0
        ),
        status=status,
        owner_agent="formal_verifier",
        priority="high" if status == "READY_FOR_LOCAL_LEAN_OR_AXLE_RERUN" else "blocked",
        required_gate="AXLE/local Lean rerun reports kernel_verified=true for this selected proof body",
        command_plan=command_plan,
        evidence_paths=(str(manifest_path), str(results_jsonl)),
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _needs_kernel_rerun(row: dict[str, Any]) -> bool:
    if not bool(row.get("solved", False)):
        return False
    return not bool(row.get("kernel_verified", False))


def _results_jsonl_path(proof_search_audit_dir: Path, manifest: dict[str, Any]) -> Path:
    path = str(manifest.get("results_jsonl", "")).strip()
    if path:
        candidate = Path(path)
        if candidate.exists():
            return candidate
        if not candidate.is_absolute():
            sibling = proof_search_audit_dir / candidate
            if sibling.exists():
                return sibling
    return proof_search_audit_dir / "proof_search_results.jsonl"


def _batch_rerun_command(
    manifest: dict[str, Any],
    *,
    out_dir: Path,
    local_lean_project: str | Path | None,
    local_lean_timeout: int,
) -> tuple[str, ...]:
    command = [
        "python3",
        "-m",
        "ai_statistician.cli",
        "proof-search-audit",
        "--local-lean",
        "--max-obligations",
        str(int(manifest.get("max_obligations", 12) or 12)),
        "--max-nodes",
        str(int(manifest.get("max_nodes", 8) or 8)),
        "--local-lean-timeout",
        str(int(local_lean_timeout)),
    ]
    if local_lean_project:
        command.extend(["--local-lean-project", str(local_lean_project)])
    if bool(manifest.get("include_invalid_probe", False)):
        command.append("--include-invalid-probe")
    if not bool(manifest.get("include_registered_proof", True)):
        command.append("--no-registered-proof")
    policy_model = str(manifest.get("policy_model_json", "")).strip()
    if policy_model:
        command.extend(["--policy-model-json", policy_model])
    value_model = str(manifest.get("value_model_json", "")).strip()
    if value_model:
        command.extend(["--value-model-json", value_model])
    command.extend(["--out", str(out_dir)])
    return tuple(command)


def _default_rerun_output_dir(out_dir: Path | None) -> Path:
    if out_dir is None:
        return Path("runs/proof_search_kernel_rerun_local_lean")
    return out_dir.parent / "proof_search_kernel_rerun_local_lean"


def _command_string(command: tuple[str, ...]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON file: {path}: {exc}")
    return {}


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"missing JSONL file: {path}")
        return rows
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSONL row {path}:{line_no}: {exc}")
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            errors.append(f"JSONL row is not an object: {path}:{line_no}")
    return rows


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Proof-search kernel rerun queue",
        "",
        f"- rows: `{payload.get('n_queue_rows')}`",
        f"- ready: `{payload.get('n_ready_for_local_lean_or_axle')}`",
        f"- blocked: `{payload.get('n_blocked_missing_selected_proof_body')}`",
        f"- source kernel verified: `{payload.get('n_source_kernel_verified')}`",
        f"- proof evidence status: `{payload.get('proof_evidence_status')}`",
        "",
        "## Batch rerun command",
        "",
        "```bash",
        str(payload.get("batch_local_lean_rerun_command", "")),
        "```",
        "",
        "## Rows",
    ]
    for row in payload.get("rows", [])[:12]:
        if not isinstance(row, dict):
            continue
        lines.extend(
            [
                "",
                f"- `{row.get('obligation_id')}` status=`{row.get('status')}` "
                f"source=`{row.get('selected_source')}` "
                f"strength=`{row.get('selected_verification_strength')}`",
            ]
        )
    lines.extend(["", str(payload.get("proof_evidence_boundary", "")), ""])
    return "\n".join(lines)
