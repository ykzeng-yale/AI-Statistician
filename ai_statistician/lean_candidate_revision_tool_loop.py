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


LeanCandidateCheck = Callable[[str, str], Mapping[str, Any]]
FormalEnvironmentSearch = Callable[[str, int], Any]
ProofCandidateSearch = Callable[[str, str, int, Mapping[str, Any]], Any]
LeanStateInspection = Callable[[str, Mapping[str, Any]], Any]
LeanDeclarationInspection = Callable[
    [str, str, int, Mapping[str, Any]], Any
]
LEAN_SOURCE_SUBMISSION_TOOL = "submit_lean_source"
LEAN_FORMAL_GAP_TOOL = "report_formal_gap"


@dataclass(frozen=True)
class LeanCandidateRevisionToolLoopResult:
    lean_source: str
    source_hash: str
    candidate_lean_declaration: str
    disposition: str
    formal_gap: Mapping[str, Any]
    check_result: Mapping[str, Any]
    evidence: Mapping[str, Any]


def resolve_lean_workspace_start_source(
    *,
    candidate_id: str,
    candidate_lean_declaration: str,
    parent_source: str,
    environment_feedback: Mapping[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    """Resume an exact model-owned source checkpoint when its hashes still bind."""

    parent_source_hash = stable_hash(parent_source)
    checkpoint = environment_feedback.get("formalizer_recovery_checkpoint", {})
    if not isinstance(checkpoint, Mapping) or not checkpoint:
        return parent_source, candidate_lean_declaration, {
            "resumed_from_model_checkpoint": False,
            "parent_source_hash": parent_source_hash,
        }

    errors: list[str] = []
    if str(checkpoint.get("artifact_kind", "") or "") not in {
        "LeanCandidateWorkspaceRecoveryCheckpoint",
        "LeanCandidateRevisionRecoveryCheckpoint",
    }:
        errors.append("checkpoint artifact kind is not a Lean workspace checkpoint")
    if str(checkpoint.get("candidate_id", "") or "") != candidate_id:
        errors.append("checkpoint candidate id does not match the active workspace")
    checkpoint_declaration = str(
        checkpoint.get("candidate_lean_declaration", "") or ""
    ).strip()
    if (
        candidate_lean_declaration
        and checkpoint_declaration != candidate_lean_declaration
    ):
        errors.append("checkpoint declaration does not match the active workspace")
    if str(checkpoint.get("parent_source_hash", "") or "") != parent_source_hash:
        errors.append("checkpoint parent source hash does not match the active workspace")

    source = str(checkpoint.get("current_source", "") or "")
    source_hash = str(checkpoint.get("current_source_hash", "") or "")
    empty_initial_checkpoint = bool(
        not parent_source.strip()
        and not source.strip()
        and source_hash == stable_hash("")
        and str(checkpoint.get("workspace_phase", "") or "")
        == "initial_authoring"
    )
    if (
        (not source.strip() and not empty_initial_checkpoint)
        or source_hash != stable_hash(source)
    ):
        errors.append("checkpoint current source is empty or hash-stale")
    if len(source) > 20000:
        errors.append("checkpoint current source exceeds the artifact-size boundary")
    if source.strip() and not checkpoint_declaration:
        errors.append("checkpoint source has no model-selected Lean declaration")
    if (
        checkpoint.get("model_owned_lean_code") is not True
        and not empty_initial_checkpoint
    ):
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
    return source, checkpoint_declaration or candidate_lean_declaration, {
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
    max_no_progress_turns: int,
    candidate_id: str,
    candidate_lean_declaration: str,
    initial_source: str,
    check_candidate: LeanCandidateCheck,
    search_formal_environment: FormalEnvironmentSearch,
    search_proof_candidates: ProofCandidateSearch | None = None,
    inspect_lean_state: LeanStateInspection | None = None,
    inspect_lean_declaration: LeanDeclarationInspection | None = None,
    allow_formal_gap: bool = False,
    request_metadata: Mapping[str, Any] | None = None,
) -> LeanCandidateRevisionToolLoopResult:
    """Let the model author or revise one immutable-bound Lean target."""

    if not candidate_id.strip():
        raise ValueError("Lean candidate tool loop requires a bound semantic target id")
    if initial_source.strip() and not candidate_lean_declaration.strip():
        raise ValueError("an existing Lean source requires its declaration identity")
    for value, label in (
        (max_turns, "turn"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"Lean candidate {label} budget must be positive")

    parent_source = str(initial_source)
    parent_source_hash = stable_hash(parent_source)
    workspace_phase = "revision" if parent_source.strip() else "initial_authoring"
    # Lean authoring is one durable coding-agent session. Keep its tool surface
    # stable while carrying current authoritative state outside the rolling history.
    max_retained_tool_turns = min(max_turns, 4)
    max_terminal_recovery_turns = 1
    state: dict[str, Any] = {
        "source": parent_source,
        "source_hash": parent_source_hash,
        "candidate_lean_declaration": candidate_lean_declaration.strip(),
        "source_updates": 0,
        "declaration_updates": 0,
        "searches": 0,
        "proof_searches": 0,
        "state_inspections": 0,
        "declaration_inspections": 0,
        "checks": 0,
        "last_check": {},
        "latest_check_observation": {},
        "latest_formal_environment_search": {},
        "latest_proof_search": {},
        "latest_state_inspection": {},
        "latest_declaration_inspection": {},
    }
    tools = _lean_candidate_revision_tools(
        include_proof_search=search_proof_candidates is not None,
        include_state_inspection=inspect_lean_state is not None,
        include_declaration_inspection=inspect_lean_declaration is not None,
        include_formal_gap=allow_formal_gap,
    )

    def check_current_source() -> dict[str, Any]:
        raw_result = check_candidate(
            str(state["source"]),
            str(state["candidate_lean_declaration"]),
        )
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

    # A resumed source is rechecked in the active project before the first model
    # turn, so the authoritative snapshot carries fresh diagnostics rather than a
    # copied observation from an earlier runtime packet.
    if parent_source.strip():
        check_current_source()

    def current_workspace_observation() -> dict[str, Any]:
        return {
            "current_source_hash": str(state["source_hash"]),
            **(
                {
                    "candidate_lean_declaration": str(
                        state["candidate_lean_declaration"]
                    )
                }
                if state["candidate_lean_declaration"]
                else {}
            ),
        }

    def execute_tool(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == LEAN_SOURCE_SUBMISSION_TOOL:
            if set(tool_input) != {"lean_source", "candidate_declaration_name"}:
                raise ClientToolInputError(
                    "submit_lean_source requires exactly lean_source and "
                    "candidate_declaration_name on every submission"
                )
            source = tool_input.get("lean_source")
            if not isinstance(source, str) or not source.strip():
                raise ClientToolInputError("lean_source must be a nonempty string")
            if len(source) > 20000:
                raise ClientToolInputError(
                    "lean_source exceeds the runtime artifact-size boundary"
                )
            declaration = str(
                tool_input.get("candidate_declaration_name", "") or ""
            ).strip()
            if not declaration:
                raise ClientToolInputError(
                    "every source submission requires the exact globally resolvable "
                    "declaration name"
                )
            source_hash = stable_hash(source)
            changed = source_hash != state["source_hash"]
            declaration_changed = declaration != state["candidate_lean_declaration"]
            already_checked = bool(
                state["last_check"]
                and str(state["last_check"].get("source_hash", "") or "")
                == source_hash
                and not declaration_changed
            )
            if not changed and already_checked:
                raise ClientToolInputError(
                    "submitted source is byte-identical to the current source and "
                    "its deterministic Lean observation is already recorded"
                )
            if changed:
                state["source"] = source
                state["source_hash"] = source_hash
                state["source_updates"] += 1
                state["last_check"] = {}
            if declaration_changed:
                state["candidate_lean_declaration"] = declaration
                state["declaration_updates"] += 1
                state["last_check"] = {}
            check_result = check_current_source()
            compiled = bool(check_result.get("compiled", False))
            content = {
                **check_result,
                "ok": compiled,
                "changed": changed,
                "declaration_changed": declaration_changed,
                "source_hash": source_hash,
                "candidate_lean_declaration": declaration,
                "source_updates": state["source_updates"],
                "declaration_updates": state["declaration_updates"],
                "checks": state["checks"],
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
                state_changed=changed or declaration_changed,
                terminal=compiled,
                terminal_payload=(
                    {
                        "lean_source": state["source"],
                        "source_hash": state["source_hash"],
                        "candidate_lean_declaration": state[
                            "candidate_lean_declaration"
                        ],
                        "check_result": deepcopy(check_result),
                    }
                    if compiled
                    else None
                ),
                observation_key="lean-submission:"
                + stable_hash(
                    {
                        "source_hash": source_hash,
                        "candidate_lean_declaration": declaration,
                        "check_result": check_result,
                    }
                ),
            )

        if call.name == LEAN_FORMAL_GAP_TOOL:
            if not allow_formal_gap:
                raise ClientToolInputError("formal-gap reporting is unavailable")
            if set(tool_input) - {
                "summary",
                "missing_primitives",
                "blocking_observations",
            }:
                raise ClientToolInputError(
                    "report_formal_gap accepts summary, missing_primitives, and "
                    "blocking_observations"
                )
            summary = tool_input.get("summary")
            if not isinstance(summary, str) or not summary.strip():
                raise ClientToolInputError("formal-gap summary must be nonempty")
            missing_primitives = tool_input.get("missing_primitives", [])
            blocking_observations = tool_input.get("blocking_observations", [])
            if not isinstance(missing_primitives, list) or not all(
                isinstance(value, str) and value.strip()
                for value in missing_primitives
            ):
                raise ClientToolInputError(
                    "missing_primitives must be an array of nonempty strings"
                )
            if not isinstance(blocking_observations, list) or not all(
                isinstance(value, str) and value.strip()
                for value in blocking_observations
            ):
                raise ClientToolInputError(
                    "blocking_observations must be an array of nonempty strings"
                )
            formal_gap = {
                "summary": summary.strip(),
                "missing_primitives": [value.strip() for value in missing_primitives],
                "blocking_observations": [
                    value.strip() for value in blocking_observations
                ],
            }
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "disposition": "FORMAL_GAP",
                    "formal_gap": deepcopy(formal_gap),
                    "proof_evidence_status": (
                        "MODEL_REPORTED_FORMAL_GAP_NOT_PROOF_EVIDENCE"
                    ),
                },
                state_changed=True,
                terminal=True,
                terminal_payload={
                    "disposition": "FORMAL_GAP",
                    "formal_gap": formal_gap,
                },
                observation_key="formal-gap:" + stable_hash(formal_gap),
            )

        if call.name == "search_formal_environment":
            if set(tool_input) - {"query", "max_results"}:
                raise ClientToolInputError(
                    "search_formal_environment accepts query and optional max_results"
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
                **current_workspace_observation(),
                "proof_evidence_status": "FORMAL_SOURCE_SEARCH_NOT_PROOF_EVIDENCE",
            }
            state["latest_formal_environment_search"] = deepcopy(content)
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
                **current_workspace_observation(),
                "proof_evidence_status": (
                    "PROOF_SEARCH_RESULT_NOT_PROOF_EVIDENCE"
                ),
                "source_ownership": (
                    "The model must choose and submit the complete next Lean source; "
                    "the runtime does not splice returned proof bodies."
                ),
            }
            state["latest_proof_search"] = deepcopy(content)
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
            if not state["last_check"]:
                raise ClientToolInputError(
                    "submit_lean_source must run before inspect_lean_state so the "
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
                **current_workspace_observation(),
                "observation": deepcopy(result),
                "state_inspections": state["state_inspections"],
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
                **current_workspace_observation(),
                "symbol": symbol.strip(),
                "observation": deepcopy(result),
                "declaration_inspections": state["declaration_inspections"],
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

    def build_workspace_snapshot(turn_index: int) -> dict[str, Any]:
        return {
            "artifact_kind": "LeanCandidateWorkspaceSnapshot",
            "candidate_id": candidate_id,
            "candidate_lean_declaration": state[
                "candidate_lean_declaration"
            ],
            "current_lean_source": state["source"],
            "current_source_hash": state["source_hash"],
            "latest_check_observation": _lean_check_workspace_snapshot(
                state["latest_check_observation"]
            ),
            "usage": {
                "source_updates": state["source_updates"],
                "checks": state["checks"],
                "searches": state["searches"],
                "proof_searches": state["proof_searches"],
                "state_inspections": state["state_inspections"],
                "declaration_inspections": state[
                    "declaration_inspections"
                ],
            },
            "budget": {
                "standard_turn_index": min(turn_index, max_turns),
                "standard_turns_remaining_including_current": max(
                    0,
                    max_turns - turn_index,
                ),
                "terminal_recovery_turn": turn_index >= max_turns,
                "terminal_recovery_turns_available": (
                    max_terminal_recovery_turns
                ),
            },
            "proof_evidence_status": "WORKSPACE_STATE_NOT_PROOF_EVIDENCE",
        }

    max_tool_calls = max_turns + max_terminal_recovery_turns + 1
    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
            max_terminal_recovery_turns=max_terminal_recovery_turns,
            max_retained_tool_turns=max_retained_tool_turns,
            build_workspace_snapshot=build_workspace_snapshot,
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool workspace",
            attempts=exc.turns,
            errors=[exc.reason],
            history=[deepcopy(dict(row)) for row in exc.history],
            recovery_checkpoint={
                "schema_version": 1,
                "artifact_kind": "LeanCandidateWorkspaceRecoveryCheckpoint",
                "candidate_id": candidate_id,
                "candidate_lean_declaration": state[
                    "candidate_lean_declaration"
                ],
                "workspace_phase": workspace_phase,
                "parent_source_hash": parent_source_hash,
                "current_source_hash": state["source_hash"],
                "current_source": state["source"],
                "source_updates": state["source_updates"],
                "declaration_updates": state["declaration_updates"],
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
                "latest_formal_environment_search": deepcopy(
                    state["latest_formal_environment_search"]
                ),
                "latest_proof_search": deepcopy(
                    state["latest_proof_search"]
                ),
                "latest_state_inspection": deepcopy(
                    state["latest_state_inspection"]
                ),
                "latest_declaration_inspection": deepcopy(
                    state["latest_declaration_inspection"]
                ),
                "turns": exc.turns,
                "tool_calls": exc.tool_calls,
                "max_terminal_recovery_turns": max_terminal_recovery_turns,
                "transcript_fingerprint": exc.transcript_fingerprint,
                "provider": exc.provider,
                "model": exc.model or model,
                "model_tier": model_tier,
                "runtime_selected_lean_code": False,
                "model_owned_lean_code": bool(str(state["source"]).strip()),
                "model_owned_workspace_actions": bool(exc.tool_calls),
                "kernel_verified": False,
                "proof_evidence_status": (
                    "CLIENT_TOOL_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
                ),
            },
        ) from exc

    terminal = dict(loop.terminal_payload)
    disposition = str(terminal.get("disposition", "AUTHOR_LEAN") or "AUTHOR_LEAN")
    if disposition == "FORMAL_GAP":
        formal_gap = terminal.get("formal_gap", {})
        if not isinstance(formal_gap, Mapping) or not str(
            formal_gap.get("summary", "") or ""
        ).strip():
            raise PacketValidationError(
                validation_label="LLM Formalizer Lean candidate client-tool workspace",
                attempts=loop.turns,
                errors=["terminal formal-gap payload is incomplete"],
                history=[deepcopy(dict(row)) for row in loop.history],
            )
        return _lean_candidate_revision_success_result(
            source=str(state["source"]),
            check_result=deepcopy(dict(state["last_check"])),
            state=state,
            candidate_id=candidate_id,
            candidate_lean_declaration=str(
                state["candidate_lean_declaration"]
            ),
            disposition=disposition,
            formal_gap=formal_gap,
            parent_source_hash=parent_source_hash,
            tools=tools,
            max_turns=max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
            max_terminal_recovery_turns=max_terminal_recovery_turns,
            max_retained_tool_turns=max_retained_tool_turns,
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
            workspace_phase=workspace_phase,
        )
    source = str(terminal.get("lean_source", "") or "")
    source_hash = str(terminal.get("source_hash", "") or "")
    submitted_declaration = str(
        terminal.get("candidate_lean_declaration", "") or ""
    ).strip()
    check_result = terminal.get("check_result", {})
    if (
        not source.strip()
        or source_hash != stable_hash(source)
        or not submitted_declaration
        or not isinstance(check_result, Mapping)
        or str(check_result.get("source_hash", "") or "") != source_hash
        or not bool(check_result.get("compiled", False))
    ):
        raise PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool workspace",
            attempts=loop.turns,
            errors=["terminal payload was not bound to a compiled current source"],
            history=[deepcopy(dict(row)) for row in loop.history],
        )

    return _lean_candidate_revision_success_result(
        source=source,
        check_result=check_result,
        state=state,
        candidate_id=candidate_id,
        candidate_lean_declaration=submitted_declaration,
        disposition="AUTHOR_LEAN",
        formal_gap={},
        parent_source_hash=parent_source_hash,
        tools=tools,
        max_turns=max_turns,
        max_tool_calls=max_tool_calls,
        max_no_progress_turns=max_no_progress_turns,
        max_terminal_recovery_turns=max_terminal_recovery_turns,
        max_retained_tool_turns=max_retained_tool_turns,
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
        workspace_phase=workspace_phase,
    )


def _lean_candidate_revision_success_result(
    *,
    source: str,
    check_result: Mapping[str, Any],
    state: Mapping[str, Any],
    candidate_id: str,
    candidate_lean_declaration: str,
    disposition: str,
    formal_gap: Mapping[str, Any],
    parent_source_hash: str,
    tools: tuple[ClientToolDefinition, ...],
    max_turns: int,
    max_tool_calls: int,
    max_no_progress_turns: int,
    max_terminal_recovery_turns: int,
    max_retained_tool_turns: int | None,
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
    workspace_phase: str,
) -> LeanCandidateRevisionToolLoopResult:
    source_hash = stable_hash(source)
    accepted_model_source = disposition == "AUTHOR_LEAN"
    model_owned_lean_code = bool(source.strip())
    model_explicit_submit = bool(
        int(state["source_updates"] or 0)
        or int(state["declaration_updates"] or 0)
    )
    latest_check_compiled = bool(
        check_result.get(
            "local_lean_source_compiled",
            check_result.get("compiled", False),
        )
    )
    local_candidate_validation_passed = bool(
        check_result.get("compiled", False)
    )
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
        "artifact_kind": "LeanCandidateClientToolWorkspace",
        "transport": "native_client_tools",
        "candidate_id": candidate_id,
        "candidate_lean_declaration": candidate_lean_declaration,
        "disposition": disposition,
        **({"formal_gap": deepcopy(dict(formal_gap))} if formal_gap else {}),
        "workspace_phase": workspace_phase,
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
        "max_terminal_recovery_turns": max_terminal_recovery_turns,
        "max_retained_tool_turns": max_retained_tool_turns,
        "transcript_policy": "rolling_history_plus_authoritative_snapshot",
        "tool_surface_policy": "stable_for_workspace",
        "submit_and_check_atomic": True,
        "tool_names": [tool.name for tool in tools],
        "source_updates": state["source_updates"],
        "declaration_updates": state["declaration_updates"],
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
        "latest_check_compiled": latest_check_compiled,
        "provider": provider,
        "model": model,
        "model_tier": model_tier,
        "provider_usage": dict(provider_usage),
        "history": [deepcopy(dict(row)) for row in history],
        "transcript_fingerprint": transcript_fingerprint,
        "handoff_mode": (
            "successful_model_source_submission"
            if accepted_model_source
            else "model_reported_formal_gap"
        ),
        "model_explicit_submit": model_explicit_submit,
        "budget_exhausted": False,
        "local_candidate_validation_passed": (
            local_candidate_validation_passed
        ),
        "tools_executed_by_runtime": bool(
            runtime_executed_tool_calls
        ),
        "tools_executed_by_backend": bool(
            response_metadata.get("tools_executed_by_backend", False)
        ),
        "runtime_selected_lean_code": False,
        "model_owned_lean_code": model_owned_lean_code,
        "independent_semantic_review_required": accepted_model_source,
        "runtime_kernel_promotion_required": accepted_model_source,
        "kernel_verified": False,
        "proof_evidence_status": (
            "LEAN_CANDIDATE_CLIENT_TOOL_LOOP_RECORDED_NOT_PROOF_EVIDENCE"
        ),
    }
    if formal_gap:
        evidence["formal_gap_observation"] = {
            "formal_gap": deepcopy(dict(formal_gap)),
            "candidate_id": candidate_id,
            "candidate_lean_declaration": candidate_lean_declaration,
            "current_source": source,
            "current_source_hash": source_hash,
            "parent_source_hash": parent_source_hash,
            "latest_check_observation": deepcopy(dict(check_result)),
            "latest_formal_environment_search": deepcopy(
                dict(state.get("latest_formal_environment_search", {}) or {})
            ),
            "latest_proof_search": deepcopy(
                dict(state.get("latest_proof_search", {}) or {})
            ),
            "latest_state_inspection": deepcopy(
                dict(state.get("latest_state_inspection", {}) or {})
            ),
            "latest_declaration_inspection": deepcopy(
                dict(state.get("latest_declaration_inspection", {}) or {})
            ),
            "model_owned_lean_code": model_owned_lean_code,
            "runtime_selected_lean_code": False,
            "kernel_verified": False,
            "proof_evidence_status": (
                "MODEL_REPORTED_FORMAL_GAP_OBSERVATION_NOT_PROOF_EVIDENCE"
            ),
        }
    return LeanCandidateRevisionToolLoopResult(
        lean_source=source,
        source_hash=source_hash,
        candidate_lean_declaration=candidate_lean_declaration,
        disposition=disposition,
        formal_gap=deepcopy(dict(formal_gap)),
        check_result=deepcopy(dict(check_result)),
        evidence=evidence,
    )


def _lean_check_workspace_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    keys = (
        "source_hash",
        "candidate_lean_declaration",
        "compiled",
        "precheck_errors",
        "blocking_precheck_errors",
        "local_lean_attempted",
        "local_lean_source_compiled",
        "local_lean_exit_status",
        "local_lean_stdout",
        "local_lean_stderr",
        "candidate_identity_lean_checked",
        "candidate_identity_lean_verified",
        "candidate_identity_lean_stdout",
        "candidate_identity_lean_stderr",
    )
    return {key: deepcopy(value[key]) for key in keys if key in value}


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
    include_formal_gap: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    tools = [
        ClientToolDefinition(
            name=LEAN_SOURCE_SUBMISSION_TOOL,
            description=(
                "Submit one complete model-authored Lean source and identify the exact "
                "globally resolvable declaration name to check on every submission. "
                "candidate_declaration_name is only the fully qualified Lean identifier "
                "introduced or checked by the source, not a theorem header or type. The "
                "runtime stores and immediately checks those exact bytes in the "
                "configured Lean project, then returns raw diagnostics to this same model."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["lean_source", "candidate_declaration_name"],
                "properties": {
                    "lean_source": {"type": "string"},
                    "candidate_declaration_name": {"type": "string"},
                },
            },
            terminal=True,
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
    ]
    if include_formal_gap:
        tools.append(
            ClientToolDefinition(
                name=LEAN_FORMAL_GAP_TOOL,
                description=(
                    "Report that the unchanged task-bound target cannot currently be "
                    "formalized in the active Lean environment. Use only after concrete "
                    "search or compiler observations identify a real missing primitive "
                    "or foundation blocker required by that target. Errors caused by "
                    "imports, identifiers, types, or proof terms chosen in the current "
                    "model-authored source are feedback to rewrite the complete source, "
                    "not by themselves formal gaps. Do not claim an attempted revision "
                    "without a corresponding tool observation. This is a non-proof "
                    "terminal result."
                ),
                input_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["summary"],
                    "properties": {
                        "summary": {"type": "string"},
                        "missing_primitives": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "blocking_observations": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                terminal=True,
            )
        )
    if include_proof_search:
        tools.insert(
            2,
            ClientToolDefinition(
                name="search_proof_candidates",
                description=(
                    "Ask the configured prover for candidate proof bodies and raw "
                    "diagnostics for the exact current target. Results are suggestions "
                    "only: choose any useful idea yourself, then submit the complete "
                    "source for an immediate Lean check."
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
                    "identifier selected from formal-environment search or referenced "
                    "by the current checked source. Choose the exact symbol and context "
                    "yourself. This read-only active-project observation can show "
                    "the bounded module prefix, declaration signature, structure "
                    "fields, and nearby declarations needed to reproduce the source "
                    "environment; it never edits or promotes source."
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
