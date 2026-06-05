from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_ARTIFACT_VERIFIER_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "AGENTIC_ARTIFACT_KERNEL_CHECK_NOT_SOURCE_THEOREM_PROOF"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic proof execution artifact verifier rows are local Lean checks of "
    "materialized worker artifacts. A successful row is kernel evidence for the "
    "artifact file only; it is not proof evidence for the referenced source "
    "statistical theorem or residual gap."
)
FORBIDDEN_ARTIFACT_TOKENS = ("sorry", "admit", "axiom", "unsafe")


@dataclass(frozen=True)
class FormalVerifierAgenticProofExecutionArtifactVerifierRow:
    schema_version: int
    artifact_verification_id: str
    materialization_id: str
    execution_queue_id: str
    display_name: str
    target_theorem_name: str
    candidate_artifact_path: str
    execution_transcript_path: str
    execution_transcript_event_id: str
    execution_transcript_event_written: bool
    target_lean_declaration: str
    target_lean_line: int
    live_proof_state_request_id: str
    live_proof_state_request_valid: bool
    live_proof_state_request_status: str
    live_proof_state_provider_preferences: tuple[str, ...]
    live_proof_state_requested_tools: tuple[str, ...]
    local_lean_checked: bool
    local_lean_compiled: bool
    artifact_kernel_verified: bool
    source_theorem_kernel_verified: bool
    verifier: str
    verification_strength: str
    lean_command: tuple[str, ...]
    lean_project: str
    lean_timeout: int
    returncode: int
    diagnostics: tuple[str, ...]
    forbidden_tokens_found: tuple[str, ...]
    verification_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_execution_artifact_verifier(
    formal_verifier_agentic_proof_execution_materializer_dir: Path,
    out_dir: Path | None = None,
    *,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Run local Lean checks on materialized proof-worker artifacts."""

    errors: list[str] = []
    materializer_manifest_path = (
        formal_verifier_agentic_proof_execution_materializer_dir
        / "formal_verifier_agentic_proof_execution_materializer_manifest.json"
    )
    materializer_payload = _read_json(materializer_manifest_path, errors)
    project_path = Path(lean_project) if lean_project else None
    command = lean_command or _lean_command(project_path)
    rows = [
        _verifier_row(
            row,
            lean_project=project_path,
            lean_timeout=lean_timeout,
            lean_command=command,
        )
        for row in materializer_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    by_status = Counter(row.verification_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_ARTIFACT_VERIFIER_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_execution_materializer_dir": str(
            formal_verifier_agentic_proof_execution_materializer_dir
        ),
        "formal_verifier_agentic_proof_execution_materializer_manifest": str(
            materializer_manifest_path
        ),
        "enabled": True,
        "lean_project": str(lean_project or ""),
        "lean_timeout": lean_timeout,
        "lean_command": list(command),
        "n_materializer_rows": len(materializer_payload.get("rows", []) or []),
        "n_verifier_rows": len(rows),
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "n_artifact_kernel_verified": sum(
            1 for row in rows if row.artifact_kernel_verified
        ),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_forbidden_token_failures": sum(
            1 for row in rows if row.forbidden_tokens_found
        ),
        "n_execution_transcript_paths": sum(
            1 for row in rows if row.execution_transcript_path
        ),
        "n_execution_transcript_events_written": sum(
            1 for row in rows if row.execution_transcript_event_written
        ),
        "n_live_proof_state_requests": sum(
            1 for row in rows if row.live_proof_state_request_id
        ),
        "n_live_proof_state_request_valid": sum(
            1 for row in rows if row.live_proof_state_request_valid
        ),
        "n_lean_lsp_mcp_ready_requests": sum(
            1
            for row in rows
            if row.live_proof_state_request_valid
            and "lean_lsp_mcp" in row.live_proof_state_provider_preferences
        ),
        "n_live_proof_state_request_failures": sum(
            1
            for row in rows
            if row.live_proof_state_request_status
            not in {"", "LIVE_PROOF_STATE_REQUEST_VALID"}
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_artifacts_kernel_verified": bool(rows)
        and all(row.artifact_kernel_verified for row in rows),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_verification_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "artifact_verifier_fingerprint": stable_hash([asdict(row) for row in rows]),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "artifact kernel verification checks the generated route-probe file only",
            "the route-probe theorem is intentionally weaker than the source theorem",
            "source-theorem promotion still requires residual-gap validation and full-route verification",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_agentic_proof_execution_artifact_verifier.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formal_verifier_agentic_proof_execution_artifact_verifier.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _verifier_row(
    row: dict[str, Any],
    *,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
) -> FormalVerifierAgenticProofExecutionArtifactVerifierRow:
    errors: list[str] = []
    materialization_id = str(row.get("materialization_id", ""))
    execution_queue_id = str(row.get("execution_queue_id", ""))
    display_name = str(row.get("display_name", ""))
    target_theorem_name = str(row.get("target_theorem_name", ""))
    artifact_path = Path(str(row.get("candidate_artifact_path", "")))
    execution_transcript_raw = str(row.get("execution_transcript_path", ""))
    execution_transcript_path = Path(execution_transcript_raw) if execution_transcript_raw else None
    target_lean_declaration = str(row.get("target_lean_declaration", ""))
    target_lean_line = _int(row.get("target_lean_line"))
    (
        live_request_id,
        live_request_valid,
        live_request_status,
        live_request_providers,
        live_request_tools,
        live_request_errors,
    ) = _validate_live_proof_state_request(
        row,
        artifact_path=artifact_path,
        target_lean_line=target_lean_line,
        target_lean_declaration=target_lean_declaration,
    )
    errors.extend(live_request_errors)
    source = ""
    forbidden_tokens_found: tuple[str, ...] = ()
    if not materialization_id:
        errors.append("materialization_id missing")
    if not str(row.get("candidate_artifact_path", "")):
        errors.append("candidate_artifact_path missing")
    elif not artifact_path.exists():
        errors.append(f"candidate artifact missing: {artifact_path}")
    else:
        try:
            source = artifact_path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"failed to read artifact: {type(exc).__name__}: {exc}")
    forbidden_tokens_found = tuple(
        token for token in FORBIDDEN_ARTIFACT_TOKENS if token in source
    )
    if forbidden_tokens_found:
        errors.append(
            "candidate artifact contains forbidden tokens: "
            + ", ".join(forbidden_tokens_found)
        )
    checked = False
    compiled = False
    returncode = -1
    diagnostics: tuple[str, ...] = ()
    verifier = "local.lean_artifact"
    verification_strength = "local_lean_artifact_unavailable"
    if not lean_command:
        errors.append("lean executable not found")
        diagnostics = ("lean executable not found",)
        status = "LOCAL_LEAN_UNAVAILABLE"
    elif errors:
        status = "STATIC_ARTIFACT_CHECK_FAILED"
        diagnostics = tuple(errors)
    else:
        checked = True
        compiled, returncode, diagnostics = _run_local_lean(
            artifact_path,
            lean_command=lean_command,
            lean_project=lean_project,
            timeout_s=lean_timeout,
        )
        verification_strength = "local_lean_artifact_kernel"
        status = (
            "ARTIFACT_KERNEL_VERIFIED_NOT_SOURCE_THEOREM"
            if compiled
            else "ARTIFACT_LOCAL_LEAN_FAILED"
        )
        if not compiled:
            errors.append("local Lean artifact check failed")
    artifact_verification_id = (
        "formal_verifier_agentic_proof_execution_artifact_verifier:"
        + stable_hash([materialization_id, artifact_path, lean_command])[:16]
    )
    execution_transcript_event_id = (
        "agentic_artifact_verifier_event:"
        + stable_hash([artifact_verification_id, execution_transcript_path, status])[:16]
    )
    transcript_written = _append_verifier_transcript_event(
        execution_transcript_path,
        event_id=execution_transcript_event_id,
        artifact_verification_id=artifact_verification_id,
        materialization_id=materialization_id,
        execution_queue_id=execution_queue_id,
        candidate_artifact_path=artifact_path,
        target_lean_declaration=target_lean_declaration,
        target_lean_line=target_lean_line,
        verification_status=status,
        live_proof_state_request_id=live_request_id,
        live_proof_state_request_status=live_request_status,
        live_proof_state_requested_tools=live_request_tools,
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        artifact_kernel_verified=compiled,
        source_theorem_kernel_verified=False,
        verifier=verifier,
        verification_strength=verification_strength,
        returncode=returncode,
        diagnostics=diagnostics,
    )
    return FormalVerifierAgenticProofExecutionArtifactVerifierRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_EXECUTION_ARTIFACT_VERIFIER_SCHEMA_VERSION,
        artifact_verification_id=artifact_verification_id,
        materialization_id=materialization_id,
        execution_queue_id=execution_queue_id,
        display_name=display_name,
        target_theorem_name=target_theorem_name,
        candidate_artifact_path=str(artifact_path),
        execution_transcript_path=execution_transcript_raw,
        execution_transcript_event_id=execution_transcript_event_id
        if execution_transcript_raw
        else "",
        execution_transcript_event_written=transcript_written,
        target_lean_declaration=target_lean_declaration,
        target_lean_line=target_lean_line,
        live_proof_state_request_id=live_request_id,
        live_proof_state_request_valid=live_request_valid,
        live_proof_state_request_status=live_request_status,
        live_proof_state_provider_preferences=live_request_providers,
        live_proof_state_requested_tools=live_request_tools,
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        artifact_kernel_verified=compiled,
        source_theorem_kernel_verified=False,
        verifier=verifier,
        verification_strength=verification_strength,
        lean_command=lean_command,
        lean_project=str(lean_project or ""),
        lean_timeout=lean_timeout,
        returncode=returncode,
        diagnostics=diagnostics,
        forbidden_tokens_found=forbidden_tokens_found,
        verification_status=status,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _append_verifier_transcript_event(
    path: Path | None,
    *,
    event_id: str,
    artifact_verification_id: str,
    materialization_id: str,
    execution_queue_id: str,
    candidate_artifact_path: Path,
    target_lean_declaration: str,
    target_lean_line: int,
    verification_status: str,
    live_proof_state_request_id: str,
    live_proof_state_request_status: str,
    live_proof_state_requested_tools: tuple[str, ...],
    local_lean_checked: bool,
    local_lean_compiled: bool,
    artifact_kernel_verified: bool,
    source_theorem_kernel_verified: bool,
    verifier: str,
    verification_strength: str,
    returncode: int,
    diagnostics: tuple[str, ...],
) -> bool:
    if path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict) and payload.get("event_id") == event_id:
                    return False
        event = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "event": "artifact_verifier_result",
            "event_id": event_id,
            "artifact_verification_id": artifact_verification_id,
            "materialization_id": materialization_id,
            "execution_queue_id": execution_queue_id,
            "candidate_artifact_path": str(candidate_artifact_path),
            "target_lean_declaration": target_lean_declaration,
            "target_lean_line": target_lean_line,
            "verification_status": verification_status,
            "live_proof_state_request_id": live_proof_state_request_id,
            "live_proof_state_request_status": live_proof_state_request_status,
            "live_proof_state_requested_tools": live_proof_state_requested_tools,
            "local_lean_checked": local_lean_checked,
            "local_lean_compiled": local_lean_compiled,
            "artifact_kernel_verified": artifact_kernel_verified,
            "source_theorem_kernel_verified": source_theorem_kernel_verified,
            "verifier": verifier,
            "verification_strength": verification_strength,
            "returncode": returncode,
            "diagnostics": diagnostics,
            "proof_evidence_status": PROOF_EVIDENCE_STATUS,
            "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
        return True
    except OSError:
        return False


def _validate_live_proof_state_request(
    row: dict[str, Any],
    *,
    artifact_path: Path,
    target_lean_line: int,
    target_lean_declaration: str,
) -> tuple[str, bool, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    request = row.get("live_proof_state_request", {})
    if not isinstance(request, dict) or not request:
        return (
            "",
            False,
            "MISSING_LIVE_PROOF_STATE_REQUEST",
            (),
            (),
            ("live_proof_state_request missing",),
        )
    request_id = str(request.get("request_id", ""))
    providers = _str_tuple(request.get("provider_preferences", ()))
    tool_rows = request.get("mcp_tool_calls", ())
    if not isinstance(tool_rows, (list, tuple)):
        tool_rows = ()
    tools = tuple(
        str(tool.get("tool", ""))
        for tool in tool_rows
        if isinstance(tool, dict) and str(tool.get("tool", ""))
    )
    errors: list[str] = []
    if not request_id:
        errors.append("live_proof_state_request.request_id missing")
    if "lean_lsp_mcp" not in providers:
        errors.append("live_proof_state_request.provider_preferences lacks lean_lsp_mcp")
    for required_tool in ("lean_goal", "lean_diagnostic_messages"):
        if required_tool not in tools:
            errors.append(f"live_proof_state_request missing {required_tool} call")
    request_file = str(
        request.get("target_lean_file")
        or request.get("candidate_artifact_path")
        or ""
    )
    if request_file != str(artifact_path):
        errors.append(
            "live_proof_state_request target file does not match candidate artifact"
        )
    if _int(request.get("target_lean_line")) != target_lean_line:
        errors.append(
            "live_proof_state_request target line does not match materialized artifact"
        )
    if str(request.get("target_lean_declaration", "")) != target_lean_declaration:
        errors.append(
            "live_proof_state_request target declaration does not match materialized artifact"
        )
    status = (
        "LIVE_PROOF_STATE_REQUEST_VALID"
        if not errors
        else "LIVE_PROOF_STATE_REQUEST_INVALID"
    )
    return request_id, not errors, status, providers, tools, tuple(errors)


def _run_local_lean(
    lean_file: Path,
    *,
    lean_command: tuple[str, ...],
    lean_project: Path | None,
    timeout_s: int,
) -> tuple[bool, int, tuple[str, ...]]:
    try:
        proc = subprocess.run(
            [*lean_command, str(lean_file.resolve())],
            cwd=str(lean_project) if lean_project is not None else None,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return False, -1, (f"local Lean timed out after {timeout_s}s: {exc}",)
    except Exception as exc:
        return False, -1, (f"{type(exc).__name__}: {exc}",)
    diagnostics = tuple(
        line
        for line in (proc.stdout + "\n" + proc.stderr).splitlines()
        if line.strip()
    )
    return proc.returncode == 0, int(proc.returncode), diagnostics


def _lean_command(lean_project: Path | None) -> tuple[str, ...]:
    if lean_project is not None and shutil.which("lake") is not None:
        return ("lake", "env", "lean")
    if shutil.which("lean") is not None:
        return ("lean",)
    return ()


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


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _str_tuple(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return ()
    return tuple(str(item) for item in values if str(item))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Agentic Proof Execution Artifact Verifier",
        "",
        f"- Verifier rows: {payload.get('n_ok')}/{payload.get('n_verifier_rows')}",
        f"- Local Lean checked: {payload.get('n_local_lean_checked')}",
        f"- Local Lean compiled: {payload.get('n_local_lean_compiled')}",
        f"- Artifact kernel verified: {payload.get('n_artifact_kernel_verified')}",
        f"- Source theorem kernel verified: {payload.get('n_source_theorem_kernel_verified')}",
        f"- Transcript events written: {payload.get('n_execution_transcript_events_written')}",
        f"- Live proof-state requests valid: {payload.get('n_live_proof_state_request_valid')}/{payload.get('n_live_proof_state_requests')}",
        f"- Lean-LSP/MCP-ready requests: {payload.get('n_lean_lsp_mcp_ready_requests')}",
        f"- Lean command: `{payload.get('lean_command')}`",
        f"- Fingerprint: `{payload.get('artifact_verifier_fingerprint')}`",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('target_lean_declaration')}` "
            f"{row.get('verification_status')} "
            f"request={row.get('live_proof_state_request_status')} "
            f"transcript={row.get('execution_transcript_event_written')} "
            f"artifact_kernel={row.get('artifact_kernel_verified')} "
            f"source_theorem_kernel={row.get('source_theorem_kernel_verified')}"
        )
        lines.append(f"  artifact: `{row.get('candidate_artifact_path')}`")
        if row.get("errors"):
            lines.append(f"  errors: {row.get('errors')}")
    return "\n".join(lines) + "\n"
