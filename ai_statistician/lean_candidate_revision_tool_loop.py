from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    run_bounded_client_tool_loop,
)
from .fingerprint import stable_hash
from .llm_json_repair import PacketValidationError
from .model_backend import ClientToolDefinition, ClientToolTurnRequest


LeanCandidateCheck = Callable[[str], Mapping[str, Any]]
FormalEnvironmentSearch = Callable[[str, int], Any]


@dataclass(frozen=True)
class LeanCandidateRevisionToolLoopResult:
    lean_source: str
    source_hash: str
    check_result: Mapping[str, Any]
    evidence: Mapping[str, Any]


@dataclass(frozen=True)
class AcceptedLeanCandidateRevisionBinding:
    materialization_id: str
    materialization: Mapping[str, Any]
    parent_packet_id: str
    parent_packet: Mapping[str, Any]
    candidate_id: str
    candidate_lean_declaration: str
    candidate_source_field: str
    candidate_artifact_path: Path
    candidate_source_hash: str
    initial_source: str
    candidate_metadata: Mapping[str, Any]
    repair_context: Mapping[str, Any]


def resolve_accepted_lean_candidate_revision_binding(
    *,
    question_id: str,
    artifacts: Mapping[str, Any],
    environment_feedback: Mapping[str, Any],
    exact_target_statement_hash: Callable[[str], str],
    target_statement_hash_algorithm: str,
) -> AcceptedLeanCandidateRevisionBinding | None:
    """Resolve one exact candidate and its immutable accepted-review lineage."""

    repair_context = environment_feedback.get("proofengineer_repair_context", {})
    if not isinstance(repair_context, Mapping):
        return None
    accepted = bool(
        str(environment_feedback.get("overall_verdict", "") or "").upper()
        == "ACCEPT"
        and str(
            repair_context.get(
                "formalizer_candidate_semantic_review_status",
                "",
            )
            or ""
        )
        == "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
    )
    if not accepted:
        return None

    errors: list[str] = []

    def require_equal(label: str, observed: Any, expected: Any) -> None:
        if str(observed or "") != str(expected or ""):
            errors.append(f"accepted review {label} does not match current lineage")

    materialization_id = str(
        environment_feedback.get("candidate_materialization_id", "")
        or environment_feedback.get("source_manifest_id", "")
        or ""
    ).strip()
    materialization = artifacts.get(materialization_id, {})
    if not isinstance(materialization, Mapping) or str(
        materialization.get("artifact_kind", "") or ""
    ) != "RuntimeFormalizerLeanCandidateMaterialization":
        errors.append("accepted review candidate materialization is missing")
        materialization = {}

    candidate_id = str(
        environment_feedback.get("candidate_id", "") or ""
    ).strip()
    candidate_rows = [
        row
        for row in materialization.get("candidate_rows", []) or []
        if isinstance(row, Mapping)
        and str(row.get("candidate_id", "") or "") == candidate_id
    ]
    if len(candidate_rows) != 1:
        errors.append("accepted review candidate does not resolve uniquely")
        candidate: Mapping[str, Any] = {}
    else:
        candidate = candidate_rows[0]
    declaration = str(
        candidate.get("candidate_lean_declaration", "")
        or candidate.get("target_lean_declaration", "")
        or ""
    ).strip()
    source_field = str(candidate.get("source_field", "") or "").strip()
    artifact_path = Path(str(candidate.get("artifact_path", "") or ""))
    source_hash = str(candidate.get("source_hash", "") or "").strip()
    if not declaration:
        errors.append("accepted review candidate declaration is missing")
    if source_field not in {
        "formal_targets",
        "source_to_bridge_premise_derivation_candidates",
    }:
        errors.append("accepted review candidate source field is unsupported")
    try:
        initial_source = artifact_path.read_text(encoding="utf-8")
    except OSError:
        initial_source = ""
        errors.append("accepted review candidate artifact is unreadable")
    if not source_hash or stable_hash(initial_source) != source_hash:
        errors.append("accepted review candidate artifact hash is stale")

    parent_packet_id = str(
        materialization.get("source_formalizer_packet_id", "") or ""
    ).strip()
    parent_packet = artifacts.get(parent_packet_id, {})
    if not isinstance(parent_packet, Mapping) or str(
        parent_packet.get("packet_id", "") or ""
    ) != parent_packet_id:
        errors.append("accepted review parent Formalizer packet is missing")
        parent_packet = {}

    require_equal(
        "candidate_materialization_id",
        environment_feedback.get("candidate_materialization_id", ""),
        materialization_id,
    )
    require_equal("candidate_id", candidate_id, candidate.get("candidate_id", ""))
    require_equal(
        "candidate_source_hash",
        environment_feedback.get("candidate_source_hash", ""),
        source_hash,
    )
    require_equal(
        "reviewed candidate source hash",
        repair_context.get(
            "formalizer_candidate_semantic_review_candidate_source_hash",
            "",
        ),
        source_hash,
    )
    require_equal(
        "lineage candidate source hash",
        repair_context.get("lineage_candidate_artifact_hash", "")
        or repair_context.get("target_declaration_source_hash", ""),
        source_hash,
    )
    require_equal(
        "candidate artifact path",
        repair_context.get("candidate_artifact_path", "")
        or repair_context.get("source_candidate_artifact_path", ""),
        str(artifact_path),
    )
    require_equal(
        "target Lean declaration",
        repair_context.get("target_lean_declaration", "")
        or repair_context.get("target_theorem_name", ""),
        declaration,
    )

    target_statement = str(
        repair_context.get("target_theorem_statement", "") or ""
    ).strip()
    target_hash = str(
        repair_context.get("target_theorem_statement_hash", "") or ""
    ).strip()
    if (
        not target_statement
        or not target_hash
        or exact_target_statement_hash(target_statement) != target_hash
        or str(
            repair_context.get("target_theorem_statement_hash_algorithm", "")
            or ""
        )
        != target_statement_hash_algorithm
    ):
        errors.append("accepted review target statement identity is missing or stale")
    require_equal(
        "reviewed target statement hash",
        repair_context.get(
            "formalizer_candidate_semantic_review_target_statement_hash",
            "",
        ),
        target_hash,
    )
    require_equal(
        "reviewed target statement hash algorithm",
        repair_context.get(
            "formalizer_candidate_semantic_review_target_statement_hash_algorithm",
            "",
        ),
        target_statement_hash_algorithm,
    )

    review_packet_id = str(
        repair_context.get(
            "formalizer_candidate_semantic_review_packet_id",
            "",
        )
        or environment_feedback.get("semantic_review_packet_id", "")
        or ""
    ).strip()
    review_packet_hash = str(
        repair_context.get(
            "formalizer_candidate_semantic_review_packet_hash",
            "",
        )
        or environment_feedback.get("semantic_review_packet_hash", "")
        or ""
    ).strip()
    review_packet = artifacts.get(review_packet_id, {})
    if (
        not review_packet_id
        or not review_packet_hash
        or not isinstance(review_packet, Mapping)
        or stable_hash(review_packet) != review_packet_hash
    ):
        errors.append("accepted review packet artifact/hash is missing or stale")
    else:
        for label, field, expected in (
            ("packet question", "question_id", question_id),
            ("packet verdict", "overall_verdict", "ACCEPT"),
            ("packet materialization", "candidate_materialization_id", materialization_id),
            (
                "packet materialization hash",
                "candidate_materialization_hash",
                stable_hash(materialization),
            ),
            ("packet proposal", "proposal_packet_id", parent_packet_id),
            ("packet proposal hash", "proposal_packet_hash", stable_hash(parent_packet)),
            ("packet candidate", "candidate_id", candidate_id),
            ("packet candidate hash", "candidate_source_hash", source_hash),
            ("packet target hash", "target_theorem_statement_hash", target_hash),
        ):
            require_equal(label, review_packet.get(field, ""), expected)

    review_execution_id = str(
        repair_context.get(
            "formalizer_candidate_semantic_review_execution_id",
            "",
        )
        or environment_feedback.get("semantic_review_execution_id", "")
        or ""
    ).strip()
    review_execution = artifacts.get(review_execution_id, {})
    if not review_execution_id or not isinstance(review_execution, Mapping):
        errors.append("accepted review execution artifact is missing")
    else:
        for label, field, expected in (
            ("execution question", "question_id", question_id),
            ("execution materialization", "candidate_materialization_id", materialization_id),
            ("execution candidate", "candidate_id", candidate_id),
            ("execution candidate hash", "candidate_source_hash", source_hash),
            ("execution review packet", "review_packet_id", review_packet_id),
            ("execution review packet hash", "review_packet_hash", review_packet_hash),
            ("execution verdict", "overall_verdict", "ACCEPT"),
        ):
            require_equal(label, review_execution.get(field, ""), expected)
        if review_execution.get("semantic_review_accepted") is not True:
            errors.append("accepted review execution is not marked accepted")

    if errors:
        raise PacketValidationError(
            validation_label="Formalizer Lean candidate accepted-review lineage",
            attempts=1,
            errors=sorted(set(errors)),
            history=[],
            recovery_checkpoint={
                "candidate_materialization_id": materialization_id,
                "parent_formalizer_packet_id": parent_packet_id,
                "candidate_id": candidate_id,
                "candidate_source_hash": source_hash,
                "proof_evidence_status": (
                    "STALE_OR_INCOMPLETE_ACCEPTED_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            },
        )
    metadata = candidate.get("candidate_metadata", {})
    return AcceptedLeanCandidateRevisionBinding(
        materialization_id=materialization_id,
        materialization=materialization,
        parent_packet_id=parent_packet_id,
        parent_packet=parent_packet,
        candidate_id=candidate_id,
        candidate_lean_declaration=declaration,
        candidate_source_field=source_field,
        candidate_artifact_path=artifact_path,
        candidate_source_hash=source_hash,
        initial_source=initial_source,
        candidate_metadata=(metadata if isinstance(metadata, Mapping) else {}),
        repair_context=repair_context,
    )


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
    max_checks: int,
    max_no_progress_turns: int,
    candidate_id: str,
    candidate_lean_declaration: str,
    initial_source: str,
    check_candidate: LeanCandidateCheck,
    search_formal_environment: FormalEnvironmentSearch,
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

    parent_source = str(initial_source)
    parent_source_hash = stable_hash(parent_source)
    state: dict[str, Any] = {
        "source": parent_source,
        "source_hash": parent_source_hash,
        "source_updates": 0,
        "searches": 0,
        "checks": 0,
        "last_check": {},
    }
    tools = _lean_candidate_revision_tools()

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
                    "Lean source-update budget is exhausted; check and submit the "
                    "current source or stop this bounded attempt"
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
                    "formal-environment search budget is exhausted; use the returned "
                    "signatures to edit, check, and submit the current source"
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
            return ClientToolExecutionResult(
                content=content,
                is_error=not compiled,
                observation_key="check:"
                + stable_hash(
                    {
                        "source_hash": state["source_hash"],
                        "check_result": check_result,
                    }
                ),
            )

        if call.name == "submit_compiled_source":
            if tool_input:
                raise ClientToolInputError(
                    "submit_compiled_source takes an empty object"
                )
            last_check = state["last_check"]
            checked_hash = str(last_check.get("source_hash", "") or "")
            compiled = bool(last_check.get("compiled", False))
            if checked_hash != state["source_hash"] or not compiled:
                content = {
                    "ok": False,
                    "error": "current_source_has_no_successful_local_lean_check",
                    "current_source_hash": state["source_hash"],
                    "last_checked_source_hash": checked_hash,
                    "last_check_compiled": compiled,
                }
                return ClientToolExecutionResult(
                    content=content,
                    is_error=True,
                    observation_key="submit-rejected:" + stable_hash(content),
                )
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "submitted": True,
                    "source_hash": state["source_hash"],
                    "independent_semantic_review_required": True,
                    "runtime_kernel_promotion_required": True,
                },
                terminal=True,
                terminal_payload={
                    "lean_source": state["source"],
                    "source_hash": state["source_hash"],
                    "check_result": deepcopy(last_check),
                },
                observation_key="submitted:" + state["source_hash"],
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
        metadata={
            **dict(request_metadata or {}),
            "model_tier": model_tier,
            "candidate_id": candidate_id,
            "candidate_lean_declaration": candidate_lean_declaration,
            "parent_source_hash": parent_source_hash,
        },
    )
    max_tool_calls = (
        max_source_updates + max_searches + max_checks + max_turns
    )
    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_tool_calls,
            max_no_progress_turns=max_no_progress_turns,
        )
    except ClientToolLoopError as exc:
        final_runtime_check_performed = False
        last_check = state["last_check"]
        current_check_bound = bool(
            str(last_check.get("source_hash", "") or "") == state["source_hash"]
        )
        current_check_passed = bool(
            current_check_bound and last_check.get("compiled", False)
        )
        if (
            exc.reason == "global client-tool turn budget exhausted"
            and not current_check_bound
            and state["checks"] < max_checks
        ):
            final_runtime_check_performed = True
            try:
                last_check = check_current_source()
            except Exception as final_check_exc:  # pragma: no cover - defensive tool path
                state["checks"] += 1
                last_check = {
                    "source_hash": state["source_hash"],
                    "compiled": False,
                    "checker_error": type(final_check_exc).__name__,
                }
                state["last_check"] = last_check
            current_check_passed = bool(
                str(last_check.get("source_hash", "") or "") == state["source_hash"]
                and last_check.get("compiled", False)
            )
        if (
            exc.reason == "global client-tool turn budget exhausted"
            and current_check_passed
        ):
            return _lean_candidate_revision_success_result(
                source=str(state["source"]),
                check_result=last_check,
                state=state,
                candidate_id=candidate_id,
                candidate_lean_declaration=candidate_lean_declaration,
                parent_source_hash=parent_source_hash,
                tools=tools,
                max_turns=max_turns,
                max_tool_calls=max_tool_calls,
                max_no_progress_turns=max_no_progress_turns,
                turns=exc.turns,
                tool_calls=exc.tool_calls,
                runtime_executed_tool_calls=exc.runtime_executed_tool_calls,
                runtime_verifier_checks=(1 if final_runtime_check_performed else 0),
                provider=exc.provider,
                model=exc.model or model,
                model_tier=model_tier,
                provider_usage=exc.provider_usage,
                response_metadata=exc.final_response_metadata,
                history=exc.history,
                transcript_fingerprint=exc.transcript_fingerprint,
                handoff_mode="turn_budget_runtime_validated_candidate",
                model_explicit_submit=False,
                budget_exhausted=True,
            )
        raise PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool repair",
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
                "checks": state["checks"],
                "last_check": deepcopy(state["last_check"]),
                "turns": exc.turns,
                "tool_calls": exc.tool_calls,
                "transcript_fingerprint": exc.transcript_fingerprint,
                "provider": exc.provider,
                "model": exc.model or model,
                "model_tier": model_tier,
                "final_runtime_check_performed": final_runtime_check_performed,
                "runtime_selected_lean_code": False,
                "model_owned_lean_code": True,
                "kernel_verified": False,
                "proof_evidence_status": "CLIENT_TOOL_REPAIR_CHECKPOINT_NOT_PROOF_EVIDENCE",
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
            validation_label="LLM Formalizer Lean candidate client-tool repair",
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
        runtime_verifier_checks=0,
        provider=loop.provider,
        model=loop.model,
        model_tier=model_tier,
        provider_usage=loop.provider_usage,
        response_metadata=loop.final_response_metadata,
        history=loop.history,
        transcript_fingerprint=loop.transcript_fingerprint,
        handoff_mode="model_submit",
        model_explicit_submit=True,
        budget_exhausted=False,
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
    runtime_verifier_checks: int,
    provider: str,
    model: str,
    model_tier: str,
    provider_usage: Mapping[str, int],
    response_metadata: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]],
    transcript_fingerprint: str,
    handoff_mode: str,
    model_explicit_submit: bool,
    budget_exhausted: bool,
) -> LeanCandidateRevisionToolLoopResult:
    source_hash = stable_hash(source)
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
        "runtime_verifier_checks": runtime_verifier_checks,
        "max_turns": max_turns,
        "max_tool_calls": max_tool_calls,
        "max_no_progress_turns": max_no_progress_turns,
        "tool_names": [tool.name for tool in tools],
        "source_updates": state["source_updates"],
        "formal_environment_searches": state["searches"],
        "local_lean_checks": state["checks"],
        "latest_check_compiled": True,
        "provider": provider,
        "model": model,
        "model_tier": model_tier,
        "provider_usage": dict(provider_usage),
        "history": [deepcopy(dict(row)) for row in history],
        "transcript_fingerprint": transcript_fingerprint,
        "handoff_mode": handoff_mode,
        "model_explicit_submit": model_explicit_submit,
        "budget_exhausted": budget_exhausted,
        "local_candidate_validation_passed": True,
        "tools_executed_by_runtime": bool(
            runtime_executed_tool_calls or runtime_verifier_checks
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


def _lean_candidate_revision_tools() -> tuple[ClientToolDefinition, ...]:
    return (
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
                "return compiler and declaration-identity observations."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {},
            },
        ),
        ClientToolDefinition(
            name="submit_compiled_source",
            description=(
                "Submit only when check_lean_source passed for the exact current source. "
                "Submission remains subject to independent semantic and promotion gates."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {},
            },
            terminal=True,
        ),
    )
