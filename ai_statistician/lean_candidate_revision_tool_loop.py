from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .structured_output_retry import PacketValidationError
from .model_backend import ClientToolDefinition, ClientToolTurnRequest


LeanCandidateCheck = Callable[[str], Mapping[str, Any]]
FormalEnvironmentSearch = Callable[[str, int], Any]
ProofCandidateSearch = Callable[[str, str, int, Mapping[str, Any]], Any]
LeanStateInspection = Callable[[str, Mapping[str, Any]], Any]
LeanDeclarationInspection = Callable[
    [str, str, int, Mapping[str, Any]], Any
]


@dataclass(frozen=True)
class LeanCandidateRevisionToolLoopResult:
    lean_source: str
    source_hash: str
    check_result: Mapping[str, Any]
    evidence: Mapping[str, Any]


def resolve_lean_workspace_start_source(
    *,
    candidate_id: str,
    candidate_lean_declaration: str,
    parent_source: str,
    environment_feedback: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Resume an exact model-owned source checkpoint when its hashes still bind."""

    parent_source_hash = stable_hash(parent_source)
    checkpoint = environment_feedback.get("formalizer_recovery_checkpoint", {})
    if not isinstance(checkpoint, Mapping) or not checkpoint:
        return parent_source, {
            "resumed_from_model_checkpoint": False,
            "parent_source_hash": parent_source_hash,
        }

    errors: list[str] = []
    if str(checkpoint.get("artifact_kind", "") or "") != (
        "LeanCandidateRevisionRecoveryCheckpoint"
    ):
        errors.append("checkpoint artifact kind is not a Lean workspace checkpoint")
    if str(checkpoint.get("candidate_id", "") or "") != candidate_id:
        errors.append("checkpoint candidate id does not match the active workspace")
    if str(checkpoint.get("candidate_lean_declaration", "") or "") != (
        candidate_lean_declaration
    ):
        errors.append("checkpoint declaration does not match the active workspace")
    if str(checkpoint.get("parent_source_hash", "") or "") != parent_source_hash:
        errors.append("checkpoint parent source hash does not match the active workspace")

    source = str(checkpoint.get("current_source", "") or "")
    source_hash = str(checkpoint.get("current_source_hash", "") or "")
    if not source.strip() or source_hash != stable_hash(source):
        errors.append("checkpoint current source is empty or hash-stale")
    if len(source) > 20000:
        errors.append("checkpoint current source exceeds the artifact-size boundary")
    if checkpoint.get("model_owned_lean_code") is not True:
        errors.append("checkpoint is not marked as model-owned Lean source")
    if checkpoint.get("runtime_selected_lean_code") is not False:
        errors.append("checkpoint permits runtime-selected Lean source")
    if checkpoint.get("kernel_verified") is not False:
        errors.append("checkpoint incorrectly claims kernel verification")
    if errors:
        raise PacketValidationError(
            validation_label="Lean workspace checkpoint lineage",
            attempts=1,
            errors=errors,
            history=[],
            recovery_checkpoint=checkpoint,
        )
    return source, {
        "resumed_from_model_checkpoint": True,
        "parent_source_hash": parent_source_hash,
        "resume_checkpoint_source_hash": source_hash,
        "resume_checkpoint_transcript_fingerprint": str(
            checkpoint.get("transcript_fingerprint", "") or ""
        ),
    }


def run_lean_candidate_revision_tool_loop(
    *,
    provider: Any,
    system_prompt: str,
    user_prompt: str,
    model: str,
    model_tier: str,
    temperature: float,
    max_tokens: int,
    max_turns: int,
    max_source_updates: int,
    max_searches: int,
    max_proof_searches: int = 1,
    max_state_inspections: int = 2,
    max_declaration_inspections: int = 2,
    max_checks: int,
    max_no_progress_turns: int,
    candidate_id: str,
    candidate_lean_declaration: str,
    initial_source: str,
    check_candidate: LeanCandidateCheck,
    search_formal_environment: FormalEnvironmentSearch,
    search_proof_candidates: ProofCandidateSearch | None = None,
    inspect_lean_state: LeanStateInspection | None = None,
    inspect_lean_declaration: LeanDeclarationInspection | None = None,
    request_metadata: Mapping[str, Any] | None = None,
) -> LeanCandidateRevisionToolLoopResult:
    """Let the model edit, search, and compile one immutable-bound Lean target."""

    if not candidate_id.strip() or not candidate_lean_declaration.strip():
        raise ValueError("Lean candidate tool loop requires bound candidate identity")
    if not initial_source.strip():
        raise ValueError("Lean candidate tool loop requires nonempty source")
    for value, label in (
        (max_turns, "turn"),
        (max_source_updates, "source-update"),
        (max_searches, "search"),
        (max_checks, "check"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"Lean candidate {label} budget must be positive")
    if search_proof_candidates is not None and max_proof_searches < 1:
        raise ValueError("Lean candidate proof-search budget must be positive")
    if inspect_lean_state is not None and max_state_inspections < 1:
        raise ValueError("Lean state-inspection budget must be positive")
    if (
        inspect_lean_declaration is not None
        and max_declaration_inspections < 1
    ):
        raise ValueError("Lean declaration-inspection budget must be positive")

    parent_source = str(initial_source)
    parent_source_hash = stable_hash(parent_source)
    state: dict[str, Any] = {
        "source": parent_source,
        "source_hash": parent_source_hash,
        "source_updates": 0,
        "searches": 0,
        "proof_searches": 0,
        "state_inspections": 0,
        "declaration_inspections": 0,
        "checks": 0,
        "last_check": {},
        "latest_check_observation": {},
        "latest_state_inspection": {},
        "latest_declaration_inspection": {},
    }
    tools = _lean_candidate_revision_tools(
        include_proof_search=search_proof_candidates is not None,
        include_state_inspection=inspect_lean_state is not None,
        include_declaration_inspection=inspect_lean_declaration is not None,
    )

    def check_current_source() -> dict[str, Any]:
        if state["checks"] >= max_checks:
            raise ClientToolInputError(
                "local Lean check budget is exhausted; submit only if the current "
                "source already has a successful bound check"
            )
        raw_result = check_candidate(str(state["source"]))
        if not isinstance(raw_result, Mapping):
            raise ClientToolInputError("Lean checker returned a non-object result")
        check_result = deepcopy(dict(raw_result))
        observed_hash = str(check_result.get("source_hash", "") or "")
        if observed_hash != state["source_hash"]:
            raise ClientToolInputError(
                "Lean checker result is not bound to the current source hash"
            )
        state["checks"] += 1
        state["last_check"] = check_result
        state["latest_check_observation"] = check_result
        return check_result

    def execute_tool(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == "replace_lean_source":
            if set(tool_input) != {"lean_source"}:
                raise ClientToolInputError(
                    "replace_lean_source requires exactly lean_source"
                )
            if state["source_updates"] >= max_source_updates:
                raise ClientToolInputError(
                    "Lean source-update budget is exhausted; check the current source "
                    "or stop this bounded attempt"
                )
            source = tool_input.get("lean_source")
            if not isinstance(source, str) or not source.strip():
                raise ClientToolInputError("lean_source must be a nonempty string")
            if len(source) > 20000:
                raise ClientToolInputError(
                    "lean_source exceeds the runtime artifact-size boundary"
                )
            source_hash = stable_hash(source)
            changed = source_hash != state["source_hash"]
            if changed:
                state["source"] = source
                state["source_hash"] = source_hash
                state["source_updates"] += 1
                state["last_check"] = {}
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "changed": changed,
                    "source_hash": source_hash,
                    "source_updates": state["source_updates"],
                    "maximum_source_updates": max_source_updates,
                    "remaining_source_updates": (
                        max_source_updates - state["source_updates"]
                    ),
                },
                state_changed=changed,
                observation_key="source:" + source_hash,
            )

        if call.name == "search_formal_environment":
            if set(tool_input) - {"query", "max_results"}:
                raise ClientToolInputError(
                    "search_formal_environment accepts query and optional max_results"
                )
            if state["searches"] >= max_searches:
                raise ClientToolInputError(
                    "formal-environment search budget is exhausted; choose the next "
                    "source or check action from the observations already returned"
                )
            query = tool_input.get("query")
            if not isinstance(query, str) or not query.strip():
                raise ClientToolInputError("search query must be a nonempty string")
            requested_k = tool_input.get("max_results", 5)
            if isinstance(requested_k, bool) or not isinstance(requested_k, int):
                raise ClientToolInputError("max_results must be an integer")
            k = max(1, min(8, requested_k))
            state["searches"] += 1
            results = search_formal_environment(query.strip(), k)
            content = {
                "ok": True,
                "query": query.strip(),
                "results": deepcopy(results),
                "searches": state["searches"],
                "maximum_searches": max_searches,
                "remaining_searches": max_searches - state["searches"],
                "proof_evidence_status": "FORMAL_SOURCE_SEARCH_NOT_PROOF_EVIDENCE",
            }
            return ClientToolExecutionResult(
                content=content,
                observation_key="search:"
                + stable_hash(
                    {
                        "query": content["query"],
                        "results": content["results"],
                    }
                ),
            )

        if call.name == "search_proof_candidates":
            if search_proof_candidates is None:
                raise ClientToolInputError("proof-candidate search is unavailable")
            if set(tool_input) - {"query", "max_results"}:
                raise ClientToolInputError(
                    "search_proof_candidates accepts query and optional max_results"
                )
            if state["proof_searches"] >= max_proof_searches:
                raise ClientToolInputError(
                    "proof-candidate search budget is exhausted; revise or check the "
                    "current source from the observations already returned"
                )
            query = tool_input.get("query")
            if not isinstance(query, str) or not query.strip():
                raise ClientToolInputError("proof-search query must be a nonempty string")
            requested_k = tool_input.get("max_results", 4)
            if isinstance(requested_k, bool) or not isinstance(requested_k, int):
                raise ClientToolInputError("max_results must be an integer")
            k = max(1, min(8, requested_k))
            state["proof_searches"] += 1
            results = search_proof_candidates(
                str(state["source"]),
                query.strip(),
                k,
                deepcopy(dict(state["last_check"])),
            )
            content = {
                "ok": True,
                "query": query.strip(),
                "results": deepcopy(results),
                "proof_searches": state["proof_searches"],
                "maximum_proof_searches": max_proof_searches,
                "remaining_proof_searches": (
                    max_proof_searches - state["proof_searches"]
                ),
                "proof_evidence_status": (
                    "PROOF_SEARCH_RESULT_NOT_PROOF_EVIDENCE"
                ),
                "source_ownership": (
                    "The model must choose and submit the complete next Lean source; "
                    "the runtime does not splice returned proof bodies."
                ),
            }
            return ClientToolExecutionResult(
                content=content,
                observation_key="proof-search:"
                + stable_hash(
                    {
                        "source_hash": state["source_hash"],
                        "query": content["query"],
                        "results": content["results"],
                    }
                ),
            )

        if call.name == "inspect_lean_state":
            if inspect_lean_state is None:
                raise ClientToolInputError("Lean state inspection is unavailable")
            if tool_input:
                raise ClientToolInputError("inspect_lean_state takes an empty object")
            if state["state_inspections"] >= max_state_inspections:
                raise ClientToolInputError(
                    "Lean state-inspection budget is exhausted; revise or check the "
                    "current source from the observations already returned"
                )
            if not state["last_check"]:
                raise ClientToolInputError(
                    "check_lean_source must run before inspect_lean_state so the "
                    "inspection is bound to the exact current source and diagnostics"
                )
            state["state_inspections"] += 1
            result = inspect_lean_state(
                str(state["source"]),
                deepcopy(dict(state["last_check"])),
            )
            state["latest_state_inspection"] = deepcopy(result)
            content = {
                "ok": True,
                "source_hash": state["source_hash"],
                "observation": deepcopy(result),
                "state_inspections": state["state_inspections"],
                "maximum_state_inspections": max_state_inspections,
                "remaining_state_inspections": (
                    max_state_inspections - state["state_inspections"]
                ),
                "proof_evidence_status": (
                    "LEAN_STATE_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }
            return ClientToolExecutionResult(
                content=content,
                observation_key="lean-state:"
                + stable_hash(
                    {
                        "source_hash": state["source_hash"],
                        "observation": content["observation"],
                    }
                ),
            )

        if call.name == "inspect_lean_declaration":
            if inspect_lean_declaration is None:
                raise ClientToolInputError(
                    "Lean declaration inspection is unavailable"
                )
            if set(tool_input) - {"symbol", "context_lines"}:
                raise ClientToolInputError(
                    "inspect_lean_declaration accepts symbol and optional context_lines"
                )
            if state["declaration_inspections"] >= max_declaration_inspections:
                raise ClientToolInputError(
                    "Lean declaration-inspection budget is exhausted; revise or "
                    "check the current source from observations already returned"
                )
            if not state["last_check"]:
                raise ClientToolInputError(
                    "check_lean_source must run before inspect_lean_declaration so "
                    "the lookup is bound to the exact current source artifact"
                )
            symbol = tool_input.get("symbol")
            if not isinstance(symbol, str) or not symbol.strip():
                raise ClientToolInputError(
                    "declaration symbol must be a nonempty string"
                )
            requested_context = tool_input.get("context_lines", 20)
            if isinstance(requested_context, bool) or not isinstance(
                requested_context, int
            ):
                raise ClientToolInputError("context_lines must be an integer")
            context_lines = max(0, min(40, requested_context))
            state["declaration_inspections"] += 1
            result = inspect_lean_declaration(
                str(state["source"]),
                symbol.strip(),
                context_lines,
                deepcopy(dict(state["last_check"])),
            )
            state["latest_declaration_inspection"] = deepcopy(result)
            content = {
                "ok": bool(result.get("ok", True))
                if isinstance(result, Mapping)
                else True,
                "source_hash": state["source_hash"],
                "symbol": symbol.strip(),
                "observation": deepcopy(result),
                "declaration_inspections": state["declaration_inspections"],
                "maximum_declaration_inspections": max_declaration_inspections,
                "remaining_declaration_inspections": (
                    max_declaration_inspections
                    - state["declaration_inspections"]
                ),
                "proof_evidence_status": (
                    "LEAN_DECLARATION_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }
            return ClientToolExecutionResult(
                content=content,
                is_error=not content["ok"],
                observation_key="lean-declaration:"
                + stable_hash(
                    {
                        "source_hash": state["source_hash"],
                        "symbol": content["symbol"],
                        "observation": content["observation"],
                    }
                ),
            )

        if call.name == "check_lean_source":
            if tool_input:
                raise ClientToolInputError("check_lean_source takes an empty object")
            check_result = check_current_source()
            compiled = bool(check_result.get("compiled", False))
            content = {
                **check_result,
                "ok": compiled,
                "checks": state["checks"],
                "maximum_checks": max_checks,
                "remaining_checks": max_checks - state["checks"],
                "proof_evidence_status": (
                    "LOCAL_LEAN_OBSERVATION_REQUIRES_RUNTIME_PROMOTION_GATE"
                ),
            }
            if compiled:
                content.update(
                    {
                        "handed_off": True,
                        "independent_semantic_review_required": True,
                        "runtime_kernel_promotion_required": True,
                    }
                )
            return ClientToolExecutionResult(
                content=content,
                is_error=not compiled,
                terminal=compiled,
                terminal_payload=(
                    {
                        "lean_source": state["source"],
                        "source_hash": state["source_hash"],
                        "check_result": deepcopy(check_result),
                    }
                    if compiled
                    else None
                ),
                observation_key="check:"
                + stable_hash(
                    {
                        "source_hash": state["source_hash"],
                        "check_result": check_result,
                    }
                ),
            )

        raise ClientToolInputError("unsupported Lean candidate client tool")

    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=({"role": "user", "content": user_prompt},),
        tools=tools,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=True,
        metadata={
            **dict(request_metadata or {}),
            "model_tier": model_tier,
            "candidate_id": candidate_id,
            "candidate_lean_declaration": candidate_lean_declaration,
            "parent_source_hash": parent_source_hash,
        },
    )

    def select_available_tools(
        _turn_index: int,
        available_tools: tuple[ClientToolDefinition, ...],
    ) -> tuple[ClientToolDefinition, ...]:
        remaining = {
            "replace_lean_source": state["source_updates"] < max_source_updates,
            "search_formal_environment": state["searches"] < max_searches,
            "search_proof_candidates": (
                search_proof_candidates is not None
                and state["proof_searches"] < max_proof_searches
            ),
            "inspect_lean_state": (
                inspect_lean_state is not None
                and state["state_inspections"] < max_state_inspections
                and bool(state["last_check"])
            ),
            "inspect_lean_declaration": (
                inspect_lean_declaration is not None
                and state["declaration_inspections"]
                < max_declaration_inspections
                and bool(state["last_check"])
            ),
            "check_lean_source": state["checks"] < max_checks,
        }
        selected = tuple(
            tool for tool in available_tools if remaining.get(tool.name, False)
        )
        if selected:
            return selected
        # Keep one declared action so the generic loop can return a bounded,
        # model-visible exhaustion observation instead of issuing a tool-free turn.
        return tuple(
            tool for tool in available_tools if tool.name == "check_lean_source"
        )

    # Tool-specific counters bound expensive execution. With parallel calls disabled,
    # the turn budget is also a strict bound while leaving room for rejected calls.
    max_tool_calls = max(
        max_turns,
        max_source_updates
        + max_searches
        + (max_proof_searches if search_proof_candidates is not None else 0)
        + (max_state_inspections if inspect_lean_state is not None else 0)
        + (
            max_declaration_inspections
            if inspect_lean_declaration is not None
            else 0
        )
        + max_checks,
    )
    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
            select_tools=select_available_tools,
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool revision",
            attempts=exc.turns,
            errors=[exc.reason],
            history=[deepcopy(dict(row)) for row in exc.history],
            recovery_checkpoint={
                "schema_version": 1,
                "artifact_kind": "LeanCandidateRevisionRecoveryCheckpoint",
                "candidate_id": candidate_id,
                "candidate_lean_declaration": candidate_lean_declaration,
                "parent_source_hash": parent_source_hash,
                "current_source_hash": state["source_hash"],
                "current_source": state["source"],
                "source_updates": state["source_updates"],
                "searches": state["searches"],
                "proof_searches": state["proof_searches"],
                "state_inspections": state["state_inspections"],
                "declaration_inspections": state[
                    "declaration_inspections"
                ],
                "checks": state["checks"],
                "last_check": deepcopy(state["last_check"]),
                "latest_check_observation": deepcopy(
                    state["latest_check_observation"]
                ),
                "latest_state_inspection": deepcopy(
                    state["latest_state_inspection"]
                ),
                "latest_declaration_inspection": deepcopy(
                    state["latest_declaration_inspection"]
                ),
                "turns": exc.turns,
                "tool_calls": exc.tool_calls,
                "transcript_fingerprint": exc.transcript_fingerprint,
                "provider": exc.provider,
                "model": exc.model or model,
                "model_tier": model_tier,
                "runtime_selected_lean_code": False,
                "model_owned_lean_code": True,
                "kernel_verified": False,
                "proof_evidence_status": (
                    "CLIENT_TOOL_REVISION_CHECKPOINT_NOT_PROOF_EVIDENCE"
                ),
            },
        ) from exc

    terminal = dict(loop.terminal_payload)
    source = str(terminal.get("lean_source", "") or "")
    source_hash = str(terminal.get("source_hash", "") or "")
    check_result = terminal.get("check_result", {})
    if (
        not source.strip()
        or source_hash != stable_hash(source)
        or not isinstance(check_result, Mapping)
        or str(check_result.get("source_hash", "") or "") != source_hash
        or not bool(check_result.get("compiled", False))
    ):
        raise PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool revision",
            attempts=loop.turns,
            errors=["terminal payload was not bound to a compiled current source"],
            history=[deepcopy(dict(row)) for row in loop.history],
        )

    return _lean_candidate_revision_success_result(
        source=source,
        check_result=check_result,
        state=state,
        candidate_id=candidate_id,
        candidate_lean_declaration=candidate_lean_declaration,
        parent_source_hash=parent_source_hash,
        tools=tools,
        max_turns=max_turns,
        max_tool_calls=max_tool_calls,
        max_no_progress_turns=max_no_progress_turns,
        turns=loop.turns,
        tool_calls=loop.tool_calls,
        runtime_executed_tool_calls=loop.runtime_executed_tool_calls,
        provider=loop.provider,
        model=loop.model,
        model_tier=model_tier,
        provider_usage=loop.provider_usage,
        response_metadata=loop.final_response_metadata,
        history=loop.history,
        transcript_fingerprint=loop.transcript_fingerprint,
    )


def _lean_candidate_revision_success_result(
    *,
    source: str,
    check_result: Mapping[str, Any],
    state: Mapping[str, Any],
    candidate_id: str,
    candidate_lean_declaration: str,
    parent_source_hash: str,
    tools: tuple[ClientToolDefinition, ...],
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    turns: int,
    tool_calls: int,
    runtime_executed_tool_calls: int,
    provider: str,
    model: str,
    model_tier: str,
    provider_usage: Mapping[str, int],
    response_metadata: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]],
    transcript_fingerprint: str,
) -> LeanCandidateRevisionToolLoopResult:
    source_hash = stable_hash(source)
    state_provider_tools = _lean_state_executed_tools(
        state.get("latest_state_inspection", {})
    )
    declaration_provider_tools = _lean_state_executed_tools(
        state.get("latest_declaration_inspection", {})
    )
    live_provider_tools = tuple(
        dict.fromkeys([*state_provider_tools, *declaration_provider_tools])
    )
    evidence = {
        "schema_version": 1,
        "artifact_kind": "LeanCandidateRevisionClientToolLoop",
        "transport": "native_client_tools",
        "candidate_id": candidate_id,
        "candidate_lean_declaration": candidate_lean_declaration,
        "parent_source_hash": parent_source_hash,
        "submitted_source_hash": source_hash,
        "source_changed": source_hash != parent_source_hash,
        "turns": turns,
        "tool_calls": tool_calls,
        "runtime_executed_tool_calls": runtime_executed_tool_calls,
        "runtime_verifier_checks": 0,
        "max_turns": max_turns,
        "max_tool_calls": max_tool_calls,
        "max_no_progress_turns": max_no_progress_turns,
        "tool_names": [tool.name for tool in tools],
        "source_updates": state["source_updates"],
        "formal_environment_searches": state["searches"],
        "proof_candidate_searches": state["proof_searches"],
        "lean_state_inspections": state["state_inspections"],
        "lean_state_provider_tools": list(state_provider_tools),
        "lean_declaration_inspections": state["declaration_inspections"],
        "lean_declaration_provider_tools": list(
            declaration_provider_tools
        ),
        "lean_lsp_mcp_live_called": any(
            tool.startswith("lean_lsp_mcp.") for tool in live_provider_tools
        ),
        "local_lean_checks": state["checks"],
        "latest_check_compiled": True,
        "provider": provider,
        "model": model,
        "model_tier": model_tier,
        "provider_usage": dict(provider_usage),
        "history": [deepcopy(dict(row)) for row in history],
        "transcript_fingerprint": transcript_fingerprint,
        "handoff_mode": "successful_model_requested_check",
        "model_explicit_submit": False,
        "budget_exhausted": False,
        "local_candidate_validation_passed": True,
        "tools_executed_by_runtime": bool(
            runtime_executed_tool_calls
        ),
        "tools_executed_by_backend": bool(
            response_metadata.get("tools_executed_by_backend", False)
        ),
        "runtime_selected_lean_code": False,
        "model_owned_lean_code": True,
        "independent_semantic_review_required": True,
        "runtime_kernel_promotion_required": True,
        "kernel_verified": False,
        "proof_evidence_status": (
            "LEAN_CANDIDATE_CLIENT_TOOL_LOOP_RECORDED_NOT_PROOF_EVIDENCE"
        ),
    }
    return LeanCandidateRevisionToolLoopResult(
        lean_source=source,
        source_hash=source_hash,
        check_result=deepcopy(dict(check_result)),
        evidence=evidence,
    )


def _lean_state_executed_tools(value: Any) -> tuple[str, ...]:
    tools: list[str] = []

    def visit(item: Any, *, depth: int = 0) -> None:
        if depth > 8:
            return
        if isinstance(item, Mapping):
            executed = item.get("executed_tools", [])
            if isinstance(executed, (list, tuple, set)):
                tools.extend(str(tool) for tool in executed if str(tool).strip())
            trace = item.get("tool_call_trace", [])
            if isinstance(trace, (list, tuple)):
                for row in trace:
                    if isinstance(row, Mapping):
                        tool = str(row.get("tool", "") or "").strip()
                        if tool:
                            tools.append(tool)
            for child in item.values():
                visit(child, depth=depth + 1)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child, depth=depth + 1)

    visit(value)
    return tuple(dict.fromkeys(tools))


def _lean_candidate_revision_tools(
    *,
    include_proof_search: bool = False,
    include_state_inspection: bool = False,
    include_declaration_inspection: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    tools = [
        ClientToolDefinition(
            name="replace_lean_source",
            description=(
                "Replace the complete current Lean source with model-authored source. "
                "The runtime does not edit or repair the supplied Lean code."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["lean_source"],
                "properties": {"lean_source": {"type": "string"}},
            },
        ),
        ClientToolDefinition(
            name="search_formal_environment",
            description=(
                "Search declarations and modules indexed from the active Lean project "
                "and its configured dependency/source scopes. Results are suggestions "
                "and must be checked by Lean."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 8,
                    },
                },
            },
        ),
        ClientToolDefinition(
            name="check_lean_source",
            description=(
                "Run the exact current source in the configured local Lean project and "
                "return compiler and declaration-identity observations. A successful "
                "check hands the exact source to independent semantic review; a failed "
                "check returns raw observations for another model-authored source."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {},
            },
            terminal=True,
        ),
    ]
    if include_proof_search:
        tools.insert(
            2,
            ClientToolDefinition(
                name="search_proof_candidates",
                description=(
                    "Ask the configured prover for candidate proof bodies and raw "
                    "diagnostics for the exact current target. Results are suggestions "
                    "only: choose any useful idea yourself, replace the complete source, "
                    "and check that exact source with Lean."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 8,
                        },
                    },
                },
            ),
        )
    if include_state_inspection:
        tools.insert(
            -1,
            ClientToolDefinition(
                name="inspect_lean_state",
                description=(
                    "Inspect the exact current source through the configured Lean "
                    "LSP/MCP or local proof-state provider after a failed check. "
                    "Returns raw diagnostic and goal observations; it never edits "
                    "or promotes the source."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {},
                },
            ),
        )
    if include_declaration_inspection:
        tools.insert(
            -1,
            ClientToolDefinition(
                name="inspect_lean_declaration",
                description=(
                    "Ask Lean LSP/MCP for the exact source context of a declaration "
                    "identifier present in the current checked source. Choose the "
                    "symbol and context yourself. This read-only observation can show "
                    "structure fields and nearby declarations; it never edits or "
                    "promotes the source."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {"type": "string"},
                        "context_lines": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 40,
                        },
                    },
                },
            ),
        )
    return tuple(tools)
