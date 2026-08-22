from __future__ import annotations

import importlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from .fingerprint import stable_hash
from .formal_source_index import resolve_active_project_formal_source_file
from .research_schema import FormalSubclaim
from .structured_output_retry import PacketValidationError


PROOF_STATE_FEEDBACK_STATUS = "PROOF_STATE_FEEDBACK_NOT_PROOF_EVIDENCE"
LEAN_DECLARATION_INSPECTION_STATUS = (
    "LEAN_DECLARATION_INSPECTION_NOT_PROOF_EVIDENCE"
)
DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS = 90
PROOF_STATE_FEEDBACK_BOUNDARY = (
    "Proof-state feedback, Lean diagnostics, residual goals, and LSP/MCP tool "
    "requests are diagnostic/search evidence only. They do not prove a theorem "
    "unless the intended formal claim is separately accepted by AXLE or a local "
    "Lean kernel verifier without placeholders."
)

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
    artifact_path: str = ""


class ProofStateFeedbackProvider(Protocol):
    name: str

    def inspect(self, subclaims: Sequence[FormalSubclaim]) -> list[ProofStateFeedbackRow]:
        ...


def bind_candidate_axiom_audit_to_proof_state_feedback(
    rows: Sequence[ProofStateFeedbackRow],
    *,
    audit_checked: bool,
    audit_clean: bool,
    untrusted_axioms: Sequence[str] = (),
) -> list[ProofStateFeedbackRow]:
    """Keep an elaborated but untrusted declaration from looking proof-complete."""

    if not audit_checked or audit_clean:
        return list(rows)
    names = tuple(
        dict.fromkeys(str(value).strip() for value in untrusted_axioms if str(value).strip())
    )
    detail = (
        "candidate declaration elaborated but the independent axiom audit rejected "
        "untrusted dependencies"
        + (f": {', '.join(names)}" if names else "")
    )
    return [
        replace(
            row,
            attempt_status="local_lean_untrusted_axioms",
            diagnostics=tuple(dict.fromkeys((*row.diagnostics, detail))),
            residual_goals=tuple(dict.fromkeys((*row.residual_goals, detail))),
            route_revision_recommended=True,
        )
        for row in rows
    ]


def build_lean_declaration_inspection_tool(
    *,
    formal_source_retriever: object | None,
    project_root: str | Path,
    proof_state_provider: object | None,
) -> Callable[[str, str, int, Mapping[str, Any]], dict[str, Any]] | None:
    """Build one read-only declaration-source tool for a model-owned Lean session."""

    provider_inspector = getattr(proof_state_provider, "inspect_declaration", None)
    if formal_source_retriever is None and not callable(provider_inspector):
        return None
    active_project = Path(project_root).resolve()

    def active_declaration_location(symbol: str) -> dict[str, Any] | None:
        if formal_source_retriever is None:
            return None
        try:
            hits = formal_source_retriever.search(symbol, k=8)
        except Exception:
            return None
        for hit in hits:
            declaration = getattr(hit, "declaration", None)
            indexed_name = str(getattr(declaration, "name", "") or "").strip()
            if indexed_name != symbol:
                continue
            resolved_source = resolve_active_project_formal_source_file(
                retriever=formal_source_retriever,
                source_id=str(getattr(declaration, "source_id", "") or ""),
                declaration_path=str(getattr(declaration, "path", "") or ""),
                project_root=active_project,
            )
            if resolved_source is None:
                continue
            namespace = str(getattr(declaration, "namespace", "") or "").strip()
            namespace_prefix = f"{namespace}." if namespace else ""
            source_symbol = (
                indexed_name[len(namespace_prefix) :]
                if namespace_prefix and indexed_name.startswith(namespace_prefix)
                else indexed_name
            )
            return {
                "path": Path(str(resolved_source["path"])),
                "qualified_symbol": indexed_name,
                "source_symbol": source_symbol,
                "namespace": namespace,
                "importable_module": str(resolved_source["importable_module"]),
                "source_id": str(resolved_source["source_id"]),
                "line": int(getattr(declaration, "line", 0) or 0),
                "signature": str(getattr(declaration, "signature", "") or "").strip(),
            }
        return None

    def inspect(
        source: str,
        symbol: str,
        context_lines: int,
        last_check: Mapping[str, Any],
    ) -> dict[str, Any]:
        source_hash = stable_hash(source)
        candidate_source_checked = bool(last_check)
        if candidate_source_checked and str(
            last_check.get("source_hash", "") or ""
        ) != source_hash:
            raise PacketValidationError(
                validation_label="Formalizer Lean declaration inspection lineage",
                attempts=1,
                errors=["Lean declaration inspection is not bound to current source hash"],
                history=[],
            )
        active_declaration = active_declaration_location(symbol)
        provider_symbol = symbol
        if active_declaration is not None:
            checked_path = Path(active_declaration["path"])
            provider_symbol = str(active_declaration["source_symbol"])
            inspection_binding = "active_project_declaration_source"
        elif candidate_source_checked and callable(provider_inspector):
            checked_path = Path(
                str(
                    last_check.get("proof_state_artifact_path", "")
                    or last_check.get("artifact_path", "")
                    or ""
                )
            )
            try:
                checked_source = checked_path.read_text(encoding="utf-8")
            except OSError as exc:
                raise PacketValidationError(
                    validation_label="Formalizer Lean declaration inspection lineage",
                    attempts=1,
                    errors=[f"checked Lean artifact is unavailable: {exc}"],
                    history=[],
                ) from exc
            if stable_hash(checked_source) != source_hash:
                raise PacketValidationError(
                    validation_label="Formalizer Lean declaration inspection lineage",
                    attempts=1,
                    errors=["checked Lean artifact is not bound to current source hash"],
                    history=[],
                )
            inspection_binding = "checked_candidate_source"
        else:
            return {
                "ok": False,
                "status": "ACTIVE_PROJECT_DECLARATION_NOT_FOUND",
                "symbol": symbol,
                "error": (
                    "No exact active-project declaration source was found for this "
                    "model-selected symbol. Search the formal environment for its "
                    "qualified name before retrying inspection."
                ),
                "candidate_source_hash": source_hash,
                "candidate_source_checked": candidate_source_checked,
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }
        if callable(provider_inspector):
            raw = provider_inspector(
                artifact_path=str(checked_path),
                symbol=provider_symbol,
                context_lines=context_lines,
            )
            if not isinstance(raw, Mapping):
                return {
                    "ok": False,
                    "status": "PROVIDER_ERROR",
                    "provider": str(
                        getattr(
                            proof_state_provider,
                            "name",
                            type(proof_state_provider).__name__,
                        )
                    ),
                    "error": "declaration inspection provider returned a non-object",
                    "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
                }
            result = deepcopy(dict(raw))
        else:
            result = {
                "ok": False,
                "status": "INDEXED_SOURCE_PROVIDER_UNAVAILABLE",
                "provider": "formal_source_index",
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }
        source_context: dict[str, Any] = {}
        module_prefix_context: dict[str, Any] = {}
        api_context: dict[str, Any] = {}
        if active_declaration is not None:
            indexed_path = Path(active_declaration["path"])
            try:
                indexed_lines = indexed_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                indexed_lines = []
            if indexed_lines:
                prefix_end_line = min(len(indexed_lines), 64)
                prefix_content = "\n".join(indexed_lines[:prefix_end_line])
                module_prefix_context = {
                    "file_path": str(indexed_path),
                    "start_line": 1,
                    "end_line": prefix_end_line,
                    "content": prefix_content[:20_000],
                    "content_truncated": len(prefix_content) > 20_000,
                }
                indexed_line = max(
                    1,
                    min(int(active_declaration["line"] or 1), len(indexed_lines)),
                )
                start_line = max(1, indexed_line - context_lines)
                end_line = min(len(indexed_lines), indexed_line + context_lines)
                indexed_content = "\n".join(
                    indexed_lines[start_line - 1 : end_line]
                )
                source_context = {
                    "file_path": str(indexed_path),
                    "indexed_line": indexed_line,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": indexed_content[:20_000],
                    "content_truncated": len(indexed_content) > 20_000,
                }
            signature = str(active_declaration.get("signature", "") or "")
            source_symbol = str(active_declaration.get("source_symbol", "") or "")
            symbol_observed = bool(
                source_symbol
                and (
                    source_symbol in signature
                    or source_symbol in str(source_context.get("content", "") or "")
                )
            )
            api_context = {
                "context_contract": (
                    "Treat importable_module, qualified_declaration, namespace_path, "
                    "source_module_prefix_reference, and declaration_source_context "
                    "as one active-project API observation. Import importable_module "
                    "when reusing the declaration; do not substitute the source "
                    "module's internal dependency imports or copy unrelated "
                    "declarations from its prefix."
                ),
                "importable_module": str(active_declaration["importable_module"]),
                "qualified_declaration": str(active_declaration["qualified_symbol"]),
                "namespace_path": str(active_declaration["namespace"]),
                "exact_signature": signature,
                "source_module_prefix_reference": module_prefix_context,
                "declaration_source_context": source_context,
            }
            result["provider_observation_ok"] = bool(result.get("ok", False))
            result["active_project_api_context"] = api_context
            result["indexed_declaration_signature"] = signature
            result["indexed_symbol_context_observed"] = symbol_observed
            if symbol_observed:
                result["ok"] = True
                if not result["provider_observation_ok"]:
                    result["status"] = "INDEXED_SOURCE_OBSERVED"
        result.update(
            {
                "inspection_binding": inspection_binding,
                "requested_symbol": symbol,
                "inspected_source_symbol": provider_symbol,
                "candidate_source_hash": source_hash,
                "candidate_source_checked": candidate_source_checked,
                **(
                    {
                        "indexed_declaration_namespace": str(
                            active_declaration["namespace"]
                        ),
                        "indexed_declaration_line": int(active_declaration["line"]),
                    }
                    if active_declaration is not None
                    else {}
                ),
            }
        )
        return result

    return inspect


class LocalLeanProofStateFeedbackProvider:
    """Execute the exact model-owned source and return Lean observations."""

    name = "local_lean_proof_state_feedback"

    def __init__(
        self,
        *,
        project_root: str | Path | None = None,
        timeout_s: int = DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS,
        lean_command: Sequence[str] | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve() if project_root else None
        self.timeout_s = int(timeout_s)
        self.lean_command = tuple(lean_command) if lean_command is not None else self._default_lean_command()

    def inspect(self, subclaims: Sequence[FormalSubclaim]) -> list[ProofStateFeedbackRow]:
        return [self._inspect_subclaim(row) for row in subclaims]

    def _inspect_subclaim(self, subclaim: FormalSubclaim) -> ProofStateFeedbackRow:
        statement = str(subclaim.lean_statement or "")
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
        elif not statement.strip():
            attempt_status = "missing_lean_statement"
            diagnostics.append("subclaim has no Lean statement to inspect")
            requested_tools = ("lean_diagnostic_messages", "formalizer_author_lean")
            residual_goals.extend(_residual_goals_for_subclaim(subclaim, "missing Lean statement"))
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
                "local_lean_failed",
                "missing_lean_statement",
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
            artifact_path=str(subclaim.artifact_path or ""),
        )

    def _default_lean_command(self) -> tuple[str, ...]:
        if self.project_root is not None and shutil.which("lake") is not None:
            return ("lake", "env", "lean")
        lean = shutil.which("lean")
        return (lean,) if lean else ()

    def _run_local_lean(self, statement: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="ai_stat_proof_state_") as tmp:
            lean_file = Path(tmp) / "ProofStateFeedback.lean"
            lean_file.write_text(statement, encoding="utf-8")
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
            "attempt_status": "local_lean_accepted" if proc.returncode == 0 else "local_lean_failed",
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
        timeout_s: int = DEFAULT_LEAN_TOOL_TIMEOUT_SECONDS,
        lean_command: Sequence[str] | None = None,
        mcp_command: Sequence[str] | None = None,
        mcp_timeout_s: int | None = None,
        openprover_root: str | Path | None = None,
        mcp_transcript_collector: Callable[..., Mapping[str, Any]] | None = None,
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
        self.mcp_timeout_s = int(
            timeout_s if mcp_timeout_s is None else mcp_timeout_s
        )
        self.openprover_root = (
            Path(openprover_root).expanduser().resolve()
            if openprover_root
            else None
        )
        self._mcp_transcript_collector = mcp_transcript_collector

    def inspect_declaration(
        self,
        *,
        artifact_path: str,
        symbol: str,
        context_lines: int = 20,
    ) -> dict[str, Any]:
        """Return exact source context selected by Lean's declaration lookup."""

        requested_tool = "lean_lsp_mcp.lean_declaration_file"
        symbol = str(symbol or "").strip()
        if not symbol:
            return {
                "ok": False,
                "status": "INVALID_REQUEST",
                "tool": requested_tool,
                "error": "declaration symbol is empty",
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }
        if self.project_root is None:
            return {
                "ok": False,
                "status": "UNAVAILABLE",
                "tool": requested_tool,
                "symbol": symbol,
                "error": "Lean LSP MCP declaration inspection has no project_root",
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }
        project_root = self.project_root.resolve()
        path = Path(artifact_path).expanduser().resolve()
        if not path.is_file() or project_root not in path.parents:
            return {
                "ok": False,
                "status": "INVALID_ARTIFACT",
                "tool": requested_tool,
                "symbol": symbol,
                "artifact_path": str(path),
                "project_root": str(project_root),
                "error": "artifact must be an existing file inside the active Lean project",
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }
        if not (project_root / "lean-toolchain").is_file():
            return {
                "ok": False,
                "status": "UNAVAILABLE",
                "tool": requested_tool,
                "symbol": symbol,
                "artifact_path": str(path),
                "project_root": str(project_root),
                "error": "active Lean project has no lean-toolchain",
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }
        bounded_context = max(0, min(40, int(context_lines)))
        try:
            module = self._load_openprover_mcp_module()
            client_class = getattr(module, "LeanLspMcpClient", None)
            if not callable(client_class):
                raise RuntimeError(
                    "OpenProver does not expose LeanLspMcpClient"
                )
            client = client_class(
                self.mcp_command,
                project=project_root,
                timeout_s=self.mcp_timeout_s,
            )
            try:
                response = client.call_tool(
                    "lean_declaration_file",
                    {
                        "file_path": str(path),
                        "symbol": symbol,
                        "context_lines": bounded_context,
                        "full_file": False,
                    },
                )
            finally:
                client.close()
            if not isinstance(response, Mapping):
                raise RuntimeError("lean-lsp-mcp returned a non-object response")
            result = response.get("result", {})
            result = dict(result) if isinstance(result, Mapping) else {}
            response_error = response.get("error", {})
            is_error = bool(response_error or result.get("isError", False))
            structured = result.get("structuredContent", {})
            observation = (
                dict(structured)
                if isinstance(structured, Mapping)
                else {"text": _structured_mcp_text(result)}
            )
            observation_text = "\n".join(
                str(observation.get(key, "") or "")
                for key in ("content", "text")
            )
            source_symbol = symbol.rsplit(".", 1)[-1]
            symbol_context_observed = bool(
                source_symbol and source_symbol in observation_text
            )
            is_error = bool(is_error or not symbol_context_observed)
            return {
                "ok": not is_error,
                "status": (
                    "SYMBOL_CONTEXT_MISSING"
                    if not symbol_context_observed and not response_error
                    else "TOOL_ERROR"
                    if is_error
                    else "OBSERVED"
                ),
                "provider": self.name,
                "tool": requested_tool,
                "executed_tools": [requested_tool],
                "symbol": symbol,
                "artifact_path": str(path),
                "project_root": str(project_root),
                "context_lines": bounded_context,
                "observation": observation,
                "symbol_context_observed": symbol_context_observed,
                "error": _json_excerpt(response_error)
                if response_error
                else _structured_mcp_text(result)
                if result.get("isError", False)
                else (
                    "lean-lsp-mcp did not return source context containing the "
                    "requested declaration symbol"
                )
                if not symbol_context_observed
                else "",
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }
        except Exception as exc:
            return {
                "ok": False,
                "status": "PROVIDER_ERROR",
                "provider": self.name,
                "tool": requested_tool,
                "symbol": symbol,
                "artifact_path": str(path),
                "project_root": str(project_root),
                "context_lines": bounded_context,
                "error": f"{type(exc).__name__}: {exc}"[:1200],
                "proof_evidence_status": LEAN_DECLARATION_INSPECTION_STATUS,
            }

    def _inspect_subclaim(self, subclaim: FormalSubclaim) -> ProofStateFeedbackRow:
        base = super()._inspect_subclaim(subclaim)
        artifact_path = str(subclaim.artifact_path or "").strip()
        if not artifact_path:
            skipped_trace = {
                "tool": "lean_lsp_mcp.lean_diagnostic_messages",
                "status": "mcp_tool_call_skipped_no_artifact",
                "error_excerpt": (
                    "Lean LSP MCP skipped: no materialized artifact_path"
                ),
                "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
            }
            return replace(
                base,
                provider_name=self.name,
                diagnostics=tuple(
                    [
                        *base.diagnostics,
                        "Lean LSP MCP diagnostic skipped: no materialized artifact_path",
                    ]
                ),
                tool_call_trace=tuple([*base.tool_call_trace, skipped_trace]),
            )
        traces = self._run_mcp_feedback_tools(
            artifact_path,
            compiler_diagnostics=base.diagnostics,
        )
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

    def _run_mcp_feedback_tools(
        self,
        artifact_path: str,
        *,
        compiler_diagnostics: Sequence[str] = (),
    ) -> tuple[dict[str, Any], ...]:
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
        try:
            collector = self._load_openprover_mcp_collector()
            position = _lean_compiler_diagnostic_position(compiler_diagnostics)
            with tempfile.TemporaryDirectory(
                prefix="ai_stat_openprover_mcp_"
            ) as tmp:
                transcript_path = Path(tmp) / "lean_lsp_mcp_transcript.json"
                summary = collector(
                    file_path=artifact_path,
                    line=position["line"],
                    column=position["column"],
                    out=transcript_path,
                    project=self.project_root,
                    command=self.mcp_command,
                    timeout_s=self.mcp_timeout_s,
                    include_goal=True,
                    include_diagnostics=True,
                    state_search_num_results=5,
                    restart_on_tool_error=True,
                    benchmark="ai-statistician-proof-state-feedback",
                    split="runtime",
                )
                transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
            return tuple(
                _openprover_mcp_event_trace(
                    event,
                    artifact_path=artifact_path,
                    project_root=self.project_root,
                    timeout_s=self.mcp_timeout_s,
                    collector_summary=summary,
                )
                for event in transcript.get("events", []) or []
                if isinstance(event, Mapping)
            )
        except Exception as exc:
            return ({
                "tool": requested_tool,
                "status": "mcp_session_failed",
                "artifact_path": artifact_path,
                "project_root": str(self.project_root) if self.project_root else "",
                "error_excerpt": f"{type(exc).__name__}: {exc}",
                "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
            },)

    def _load_openprover_mcp_collector(self) -> Callable[..., Mapping[str, Any]]:
        if self._mcp_transcript_collector is not None:
            return self._mcp_transcript_collector
        module = self._load_openprover_mcp_module()
        collector = getattr(module, "collect_lean_lsp_mcp_transcript", None)
        if not callable(collector):
            raise RuntimeError(
                "OpenProver does not expose collect_lean_lsp_mcp_transcript"
            )
        self._mcp_transcript_collector = collector
        return collector

    def _load_openprover_mcp_module(self) -> Any:
        if self.openprover_root is not None:
            src = self.openprover_root / "src"
            module_path = src / "openprover" / "lean_lsp_mcp.py"
            if not module_path.is_file():
                raise RuntimeError(
                    f"OpenProver Lean LSP MCP adapter missing at {module_path}"
                )
            src_text = str(src)
            if src_text not in sys.path:
                sys.path.insert(0, src_text)
        try:
            module = importlib.import_module("openprover.lean_lsp_mcp")
        except ImportError as exc:
            raise RuntimeError(
                "OpenProver Lean LSP MCP adapter is unavailable; configure "
                "openprover_root or install the OpenProver package"
            ) from exc
        if self.openprover_root is not None:
            loaded_path = Path(str(getattr(module, "__file__", "") or "")).resolve()
            expected_src = (self.openprover_root / "src").resolve()
            if expected_src not in loaded_path.parents:
                raise RuntimeError(
                    "an OpenProver package from a different checkout is already "
                    f"loaded: {loaded_path}"
                )
        return module


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


def _diagnostic_lines(text: str, *, limit: int = 40) -> list[str]:
    """Bound Lean output without classifying its grammar or error semantics."""

    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) <= limit:
        return lines
    head = max(1, limit // 2)
    tail = max(1, limit - head - 1)
    return [*lines[:head], "[Lean output truncated]", *lines[-tail:]]


_LEAN_DIAGNOSTIC_POSITION_RE = re.compile(
    r"(?:^|\s|/)[^\s:]*:(?P<line>[1-9][0-9]*):(?P<column>[1-9][0-9]*):"
)


def _lean_compiler_diagnostic_position(
    diagnostics: Sequence[str],
) -> dict[str, int]:
    """Use Lean's own diagnostic location, never a Python Lean-source parser."""

    for diagnostic in diagnostics:
        match = _LEAN_DIAGNOSTIC_POSITION_RE.search(str(diagnostic))
        if match:
            return {
                "line": int(match.group("line")),
                "column": int(match.group("column")),
            }
    return {"line": 1, "column": 1}


def _openprover_mcp_event_trace(
    event: Mapping[str, Any],
    *,
    artifact_path: str,
    project_root: Path,
    timeout_s: int,
    collector_summary: Mapping[str, Any],
) -> dict[str, Any]:
    timed_out = bool(event.get("timed_out", False))
    ok = bool(event.get("ok", False))
    status = (
        "mcp_tool_call_timeout"
        if timed_out
        else "mcp_tool_call_succeeded"
        if ok
        else "mcp_tool_call_failed"
    )
    error = event.get("error", {})
    result = event.get("result", {})
    return {
        "tool": "lean_lsp_mcp." + str(event.get("tool_name", "") or ""),
        "status": status,
        "artifact_path": artifact_path,
        "project_root": str(project_root),
        "timeout_s": timeout_s,
        "arguments": dict(event.get("arguments", {}) or {})
        if isinstance(event.get("arguments", {}), Mapping)
        else {},
        "response_excerpt": _json_excerpt(result),
        "diagnostics_excerpt": _structured_mcp_text(result),
        "error_excerpt": _json_excerpt(error) if error else "",
        "openprover_adapter": {
            "trace_collection_mode": str(
                collector_summary.get("trace_collection_mode", "") or ""
            ),
            "mcp_client_restarts": int(
                collector_summary.get("mcp_client_restarts", 0) or 0
            ),
            "honesty_boundary": str(
                collector_summary.get("honesty_boundary", "") or ""
            ),
        },
        "proof_evidence_status": PROOF_STATE_FEEDBACK_STATUS,
    }


def _json_excerpt(payload: Mapping[str, Any] | dict[str, Any]) -> str:
    try:
        return json.dumps(payload, sort_keys=True)[:1200]
    except Exception:
        return str(payload)[:1200]


def _structured_mcp_text(value: Any) -> str:
    texts: list[str] = []

    def visit(item: Any, *, depth: int = 0) -> None:
        if depth > 6 or len(texts) >= 24:
            return
        if isinstance(item, str):
            if item.strip():
                texts.append(item.strip())
            return
        if isinstance(item, Mapping):
            for key in ("text", "message", "goal", "state", "proof_state"):
                child = item.get(key)
                if isinstance(child, str) and child.strip():
                    texts.append(child.strip())
            for key in (
                "items",
                "content",
                "goals",
                "structuredContent",
                "raw_result",
                "result",
            ):
                if key in item:
                    visit(item.get(key), depth=depth + 1)
            return
        if isinstance(item, (list, tuple)):
            for child in item:
                visit(child, depth=depth + 1)

    visit(value)
    return "\n".join(dict.fromkeys(texts))[:1200]
