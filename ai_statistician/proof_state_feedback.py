from __future__ import annotations

import json
import queue
import re
import shutil
import subprocess
import tempfile
import threading
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .fingerprint import stable_hash
from .research_schema import FormalSubclaim


PROOF_STATE_FEEDBACK_STATUS = "PROOF_STATE_FEEDBACK_NOT_PROOF_EVIDENCE"
PROOF_STATE_FEEDBACK_BOUNDARY = (
    "Proof-state feedback, Lean diagnostics, residual goals, and LSP/MCP tool "
    "requests are diagnostic/search evidence only. They do not prove a theorem "
    "unless the intended formal claim is separately accepted by AXLE or a local "
    "Lean kernel verifier without placeholders."
)

PLACEHOLDER_RE = re.compile(r"\b(sorry|admit|axiom)\b")
FORMAL_GAP_RE = re.compile(r"\bFORMAL_GAP\b|h_frontier_missing")


@dataclass(frozen=True)
class ProofStateFeedbackRow:
    schema_version: int
    feedback_id: str
    subclaim_id: str
    proof_obligation_id: str
    claim_type: str
    provider_name: str
    provider_preferences: tuple[str, ...]
    requested_tools: tuple[str, ...]
    attempt_status: str
    diagnostics: tuple[str, ...]
    residual_goals: tuple[str, ...]
    route_revision_recommended: bool
    subclaim_status: str
    subclaim_kernel_verified: bool
    local_lean_checked: bool
    local_lean_returncode: int | None
    proof_evidence_status: str
    proof_evidence_boundary: str
    created_at: str
    executed_tools: tuple[str, ...] = ()
    tool_call_trace: tuple[dict[str, Any], ...] = ()


class ProofStateFeedbackProvider(Protocol):
    name: str

    def inspect(self, subclaims: Sequence[FormalSubclaim]) -> list[ProofStateFeedbackRow]:
        ...


class LocalLeanProofStateFeedbackProvider:
    """Runtime proof-state feedback via local Lean diagnostics when possible.

    This is not a Lean LSP MCP implementation. It is the local fallback side of
    the same proof-state provider contract: it classifies placeholder/formal-gap
    skeletons without executing them, and runs `lake env lean` only on complete
    non-placeholder Lean text.
    """

    name = "local_lean_proof_state_feedback"

    def __init__(
        self,
        *,
        project_root: str | Path | None = None,
        timeout_s: int = 90,
        lean_command: Sequence[str] | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve() if project_root else None
        self.timeout_s = int(timeout_s)
        self.lean_command = tuple(lean_command) if lean_command is not None else self._default_lean_command()

    def inspect(self, subclaims: Sequence[FormalSubclaim]) -> list[ProofStateFeedbackRow]:
        return [self._inspect_subclaim(row) for row in subclaims]

    def _inspect_subclaim(self, subclaim: FormalSubclaim) -> ProofStateFeedbackRow:
        statement = str(subclaim.lean_statement or "").strip()
        diagnostics: list[str] = []
        residual_goals: list[str] = []
        attempt_status = ""
        checked = False
        returncode: int | None = None
        requested_tools: tuple[str, ...] = ("lean_diagnostic_messages",)
        executed_tools: tuple[str, ...] = ()
        tool_call_trace: tuple[dict[str, Any], ...] = ()
        if subclaim.kernel_verified:
            attempt_status = "already_kernel_verified_subclaim"
            diagnostics.append(
                "subclaim already has kernel_verified=true from the formal verifier; "
                "proof-state feedback is not adding proof evidence"
            )
        elif not statement:
            attempt_status = "missing_lean_statement"
            diagnostics.append("subclaim has no Lean statement to inspect")
            requested_tools = ("lean_diagnostic_messages", "formalizer_author_lean")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "missing Lean statement"))
        elif PLACEHOLDER_RE.search(statement):
            attempt_status = "placeholder_blocked"
            diagnostics.append("Lean statement contains sorry/admit/axiom; proof-state provider did not run it")
            requested_tools = ("lean_diagnostic_messages", "formalizer_author_lean")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "placeholder Lean statement"))
        elif FORMAL_GAP_RE.search(statement):
            attempt_status = "formal_gap_scaffold_blocked"
            diagnostics.append(
                "Lean statement is a formal-gap scaffold with h_frontier_missing/FORMAL_GAP markers; "
                "diagnostic feedback records residual goals instead of treating it as proof"
            )
            requested_tools = ("lean_diagnostic_messages", "formalizer_author_lean")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "formal-gap scaffold"))
        elif not _looks_like_lean_command(statement):
            attempt_status = "non_lean_statement"
            diagnostics.append("subclaim text is not a complete Lean command")
            diagnostics.append(f"statement_excerpt={statement[:160]!r}")
            requested_tools = ("lean_diagnostic_messages", "formalizer_author_lean")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "non-Lean statement"))
        elif not self.lean_command:
            attempt_status = "local_lean_unavailable"
            diagnostics.append("local Lean command unavailable; configure lake/lean before live proof-state diagnostics")
            requested_tools = ("lean_diagnostic_messages", "lean_goal")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "local Lean unavailable"))
        else:
            result = self._run_local_lean(statement)
            checked = True
            returncode = int(result["returncode"])
            executed_tools = ("local.lake_env_lean", "lean_diagnostic_messages")
            tool_call_trace = (
                {
                    "tool": "local.lake_env_lean",
                    "status": str(result["attempt_status"]),
                    "returncode": returncode,
                    "timeout_s": self.timeout_s,
                    "diagnostics_excerpt": tuple(result["diagnostics"][:3]),
                    "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
                },
            )
            diagnostics.extend(result["diagnostics"])
            attempt_status = str(result["attempt_status"])
            if returncode != 0:
                requested_tools = (
                    "lean_diagnostic_messages",
                    "lean_goal",
                    "lean_state_search",
                    "proof_search",
                    "lean_multi_attempt",
                    "local_lean_or_axle_rerun",
                )
                residual_goals.extend(
                    _residual_goals_for_subclaim(
                        subclaim,
                        str(result.get("first_error") or "local Lean failed"),
                    )
                )
            else:
                requested_tools = (
                    "lean_diagnostic_messages",
                    "local_lean_or_axle_rerun",
                )
        residual_goals = sorted(dict.fromkeys(goal for goal in residual_goals if goal))
        return ProofStateFeedbackRow(
            schema_version=1,
            feedback_id="proof_state_feedback:" + stable_hash(
                [
                    subclaim.id,
                    subclaim.proof_obligation_id or "",
                    attempt_status,
                    diagnostics[:3],
                    residual_goals[:5],
                ]
            )[:20],
            subclaim_id=subclaim.id,
            proof_obligation_id=str(subclaim.proof_obligation_id or ""),
            claim_type=str(subclaim.claim_type),
            provider_name=self.name,
            provider_preferences=(
                "lean_lsp_mcp",
                "openprover_or_reprover_premise_search",
                "local_lean_proof_state_adapter",
                "local.lake_env_lean",
            ),
            requested_tools=requested_tools,
            attempt_status=attempt_status,
            diagnostics=tuple(diagnostics or ["no proof-state diagnostic emitted"]),
            residual_goals=tuple(residual_goals),
            route_revision_recommended=attempt_status
            in {
                "formal_gap_scaffold_blocked",
                "local_lean_failed",
                "missing_lean_statement",
                "non_lean_statement",
                "placeholder_blocked",
            },
            subclaim_status=str(subclaim.status),
            subclaim_kernel_verified=bool(subclaim.kernel_verified),
            local_lean_checked=checked,
            local_lean_returncode=returncode,
            proof_evidence_status=PROOF_STATE_FEEDBACK_STATUS,
            proof_evidence_boundary=PROOF_STATE_FEEDBACK_BOUNDARY,
            created_at=datetime.now(timezone.utc).isoformat(),
            executed_tools=executed_tools,
            tool_call_trace=tool_call_trace,
        )

    def _default_lean_command(self) -> tuple[str, ...]:
        if self.project_root is not None and shutil.which("lake") is not None:
            return ("lake", "env", "lean")
        lean = shutil.which("lean")
        return (lean,) if lean else ()

    def _run_local_lean(self, statement: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="ai_stat_proof_state_") as tmp:
            lean_file = Path(tmp) / "ProofStateFeedback.lean"
            lean_file.write_text(_lean_source(statement), encoding="utf-8")
            command = (*self.lean_command, str(lean_file))
            try:
                proc = subprocess.run(
                    command,
                    cwd=str(self.project_root) if self.project_root is not None else None,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout_s,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return {
                    "attempt_status": "local_lean_failed",
                    "returncode": -1,
                    "diagnostics": [f"local Lean proof-state check timed out after {self.timeout_s}s: {exc}"],
                    "first_error": "local Lean timeout",
                }
            except Exception as exc:
                return {
                    "attempt_status": "local_lean_failed",
                    "returncode": -1,
                    "diagnostics": [f"local Lean proof-state invocation failed: {type(exc).__name__}: {exc}"],
                    "first_error": str(exc),
                }
        combined = "\n".join(item for item in (proc.stdout, proc.stderr) if item).strip()
        diagnostics = _diagnostic_lines(combined)
        return {
            "attempt_status": "local_lean_scaffold_accepted" if proc.returncode == 0 else "local_lean_failed",
            "returncode": proc.returncode,
            "diagnostics": diagnostics or [f"local Lean exited with return code {proc.returncode}"],
            "first_error": diagnostics[0] if diagnostics and proc.returncode != 0 else "",
        }


class LeanLspMcpProofStateFeedbackProvider(LocalLeanProofStateFeedbackProvider):
    """Proof-state feedback provider that records a real Lean LSP MCP call.

    MCP observations are diagnostic/search evidence for the LLM ProofEngineer.
    They are not proof evidence and never promote a theorem without a separate
    local Lean/AXLE kernel verification.
    """

    name = "lean_lsp_mcp_proof_state_feedback"

    def __init__(
        self,
        *,
        project_root: str | Path | None = None,
        timeout_s: int = 90,
        lean_command: Sequence[str] | None = None,
        mcp_command: Sequence[str] | None = None,
        mcp_timeout_s: int = 20,
    ) -> None:
        super().__init__(
            project_root=project_root,
            timeout_s=timeout_s,
            lean_command=lean_command,
        )
        self.mcp_command = (
            tuple(mcp_command)
            if mcp_command is not None
            else ("uvx", "lean-lsp-mcp")
        )
        self.mcp_timeout_s = int(mcp_timeout_s)

    def _inspect_subclaim(self, subclaim: FormalSubclaim) -> ProofStateFeedbackRow:
        base = super()._inspect_subclaim(subclaim)
        artifact_path = str(subclaim.artifact_path or "").strip()
        if not artifact_path:
            return replace(
                base,
                provider_name=self.name,
                diagnostics=tuple(
                    [
                        *base.diagnostics,
                        "Lean LSP MCP diagnostic skipped: no materialized artifact_path",
                    ]
                ),
            )
        traces = self._run_mcp_feedback_tools(artifact_path)
        diagnostics = tuple(
            item
            for item in (
                *base.diagnostics,
                *(
                    str(
                        trace.get("diagnostics_excerpt")
                        or trace.get("response_excerpt")
                        or trace.get("error_excerpt")
                        or ""
                    )
                    for trace in traces
                ),
            )
            if item
        )
        return replace(
            base,
            provider_name=self.name,
            provider_preferences=(
                "lean_lsp_mcp",
                "openprover_or_reprover_premise_search",
                "local_lean_proof_state_adapter",
                "local.lake_env_lean",
            ),
            requested_tools=tuple(
                dict.fromkeys(
                    [
                        *base.requested_tools,
                        "lean_goal",
                        "lean_state_search",
                        "lean_multi_attempt",
                    ]
                )
            ),
            diagnostics=diagnostics,
            executed_tools=tuple(
                [
                    *base.executed_tools,
                    *(
                        str(trace.get("tool", ""))
                        for trace in traces
                        if str(trace.get("tool", "")).startswith("lean_lsp_mcp.")
                        and str(trace.get("status", ""))
                        in {
                            "mcp_tool_call_failed",
                            "mcp_tool_call_succeeded",
                            "mcp_tool_call_timeout",
                        }
                    ),
                ]
            ),
            tool_call_trace=tuple([*base.tool_call_trace, *traces]),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _run_mcp_feedback_tools(self, artifact_path: str) -> tuple[dict[str, Any], ...]:
        requested_tool = "lean_lsp_mcp.lean_diagnostic_messages"
        if self.project_root is None:
            return ({
                "tool": requested_tool,
                "status": "mcp_tool_call_skipped",
                "error_excerpt": "Lean LSP MCP skipped: no project_root configured",
                "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
            },)
        if not (self.project_root / "lean-toolchain").exists():
            return ({
                "tool": requested_tool,
                "status": "mcp_tool_call_skipped",
                "project_root": str(self.project_root),
                "error_excerpt": (
                    "Lean LSP MCP skipped: project_root has no lean-toolchain"
                ),
                "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
            },)
        command = (
            *self.mcp_command,
            "--transport",
            "stdio",
            "--lean-project-path",
            str(self.project_root),
        )
        proc: subprocess.Popen[str] | None = None
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(self.project_root),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            assert proc.stdin is not None
            initialize = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "ai-statistician-runtime", "version": "0"},
                },
            }
            initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            for message in (initialize, initialized):
                proc.stdin.write(json.dumps(message) + "\n")
            proc.stdin.flush()
            line_queue = _start_json_rpc_readers(proc)
            traces: list[dict[str, Any]] = []
            for call_id, (tool_name, arguments) in enumerate(
                _mcp_tool_calls_for_artifact(artifact_path),
                start=2,
            ):
                tool_call = {
                    "jsonrpc": "2.0",
                    "id": call_id,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments,
                    },
                }
                proc.stdin.write(json.dumps(tool_call) + "\n")
                proc.stdin.flush()
                response, stderr_excerpt, timed_out = _read_json_rpc_response_from_queue(
                    proc,
                    line_queue,
                    target_id=call_id,
                    timeout_s=self.mcp_timeout_s,
                )
                if timed_out:
                    status = "mcp_tool_call_timeout"
                elif response.get("error"):
                    status = "mcp_tool_call_failed"
                else:
                    status = "mcp_tool_call_succeeded"
                traces.append(
                    {
                        "tool": "lean_lsp_mcp." + tool_name,
                        "status": status,
                        "artifact_path": artifact_path,
                        "project_root": str(self.project_root),
                        "timeout_s": self.mcp_timeout_s,
                        "arguments": arguments,
                        "response_excerpt": _json_excerpt(response),
                        "diagnostics_excerpt": _mcp_text_excerpt(response),
                        "error_excerpt": stderr_excerpt,
                        "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
                    }
                )
            return tuple(traces)
        except Exception as exc:
            return ({
                "tool": requested_tool,
                "status": "mcp_session_failed",
                "artifact_path": artifact_path,
                "project_root": str(self.project_root) if self.project_root else "",
                "error_excerpt": f"{type(exc).__name__}: {exc}",
                "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
            },)
        finally:
            if proc is not None:
                try:
                    if proc.stdin is not None:
                        proc.stdin.close()
                except Exception:
                    pass
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass


def proof_state_feedback_row_to_json(row: ProofStateFeedbackRow) -> dict[str, Any]:
    return asdict(row)


def _residual_goals_for_subclaim(subclaim: FormalSubclaim, reason: str) -> list[str]:
    rows: list[str] = []
    if subclaim.gap_reason:
        rows.append(str(subclaim.gap_reason))
    rows.extend(str(error) for error in subclaim.errors[:3])
    if subclaim.proof_dependencies:
        rows.append("review proof dependencies: " + ", ".join(subclaim.proof_dependencies[:5]))
    if subclaim.primitive_formal_source_hits:
        rows.append(
            "bridge primitives: "
            + ", ".join(sorted(str(key) for key in subclaim.primitive_formal_source_hits.keys())[:8])
        )
    if not rows:
        rows.append(reason)
    return rows


def _looks_like_lean_command(statement: str) -> bool:
    stripped = statement.lstrip()
    if stripped.startswith(("theorem ", "lemma ", "example ", "def ", "abbrev ")):
        return True
    if stripped.startswith("import "):
        return any(
            line.lstrip().startswith(("theorem ", "lemma ", "example ", "def ", "abbrev "))
            for line in stripped.splitlines()
        )
    return False


def _lean_source(statement: str) -> str:
    if statement.lstrip().startswith("import "):
        return statement
    return "import Mathlib\n\n" + statement + "\n"


def _diagnostic_lines(text: str, *, limit: int = 12) -> list[str]:
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    interesting = [
        line
        for line in lines
        if any(
            marker in line.lower()
            for marker in (
                "error",
                "warning",
                "unsolved goals",
                "unknown identifier",
                "failed",
                "type mismatch",
            )
        )
    ]
    return (interesting or lines)[:limit]


def _mcp_tool_calls_for_artifact(
    artifact_path: str,
) -> tuple[tuple[str, dict[str, Any]], ...]:
    position = _lean_lsp_probe_position(artifact_path)
    return (
        ("lean_diagnostic_messages", {"file_path": artifact_path}),
        (
            "lean_goal",
            {
                "file_path": artifact_path,
                "line": position["line"],
                "column": position["column"],
            },
        ),
        (
            "lean_state_search",
            {
                "file_path": artifact_path,
                "line": position["line"],
                "column": position["column"],
                "num_results": 5,
            },
        ),
    )


def _lean_lsp_probe_position(artifact_path: str) -> dict[str, int]:
    """Return a conservative 1-indexed proof-state probe location."""

    try:
        lines = Path(artifact_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"line": 1, "column": 1}
    declaration_line = 1
    for index, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("theorem ", "lemma ", "example ")):
            declaration_line = index
            break
    for index, line in enumerate(lines[declaration_line - 1 :], start=declaration_line):
        stripped = line.strip()
        if index > declaration_line and stripped and not stripped.startswith("--"):
            return {
                "line": index,
                "column": max(1, len(line) - len(line.lstrip()) + 1),
            }
        if ":= by" in line or stripped == "by":
            next_line = min(index + 1, max(index, len(lines)))
            if next_line <= len(lines):
                next_text = lines[next_line - 1]
                return {
                    "line": next_line,
                    "column": max(1, len(next_text) - len(next_text.lstrip()) + 1),
                }
            return {"line": index, "column": max(1, line.find("by") + 1)}
    return {"line": declaration_line, "column": 1}


def _read_json_rpc_response(
    proc: subprocess.Popen[str],
    *,
    target_id: int,
    timeout_s: int,
) -> tuple[dict[str, Any], str, bool]:
    return _read_json_rpc_response_from_queue(
        proc,
        _start_json_rpc_readers(proc),
        target_id=target_id,
        timeout_s=timeout_s,
    )


def _start_json_rpc_readers(
    proc: subprocess.Popen[str],
) -> queue.Queue[tuple[str, str]]:
    line_queue: queue.Queue[tuple[str, str]] = queue.Queue()

    def _reader(name: str, stream: Any) -> None:
        for line in stream:
            line_queue.put((name, str(line).strip()))

    if proc.stdout is not None:
        threading.Thread(
            target=_reader,
            args=("stdout", proc.stdout),
            daemon=True,
        ).start()
    if proc.stderr is not None:
        threading.Thread(
            target=_reader,
            args=("stderr", proc.stderr),
            daemon=True,
        ).start()
    return line_queue


def _read_json_rpc_response_from_queue(
    proc: subprocess.Popen[str],
    line_queue: queue.Queue[tuple[str, str]],
    *,
    target_id: int,
    timeout_s: int,
) -> tuple[dict[str, Any], str, bool]:
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    response: dict[str, Any] = {}
    deadline = datetime.now(timezone.utc).timestamp() + max(1, int(timeout_s))
    while datetime.now(timezone.utc).timestamp() < deadline:
        try:
            name, line = line_queue.get(timeout=0.2)
        except queue.Empty:
            if proc.poll() is not None and not response:
                break
            continue
        if name == "stderr":
            stderr_lines.append(line)
            continue
        stdout_lines.append(line)
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("id") == target_id:
            response = payload
            return response, "\n".join(stderr_lines)[-800:], False
    if not response:
        response = {"stdout_excerpt": "\n".join(stdout_lines)[-1200:]}
    return response, "\n".join(stderr_lines)[-800:], True


def _json_excerpt(payload: Mapping[str, Any] | dict[str, Any]) -> str:
    try:
        return json.dumps(payload, sort_keys=True)[:1200]
    except Exception:
        return str(payload)[:1200]


def _mcp_text_excerpt(payload: Mapping[str, Any] | dict[str, Any]) -> str:
    result = payload.get("result") if isinstance(payload, Mapping) else None
    if not isinstance(result, Mapping):
        return ""
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    texts = [
        str(item.get("text", ""))
        for item in content
        if isinstance(item, Mapping) and str(item.get("text", "")).strip()
    ]
    return "\n".join(texts)[:1200]
