from __future__ import annotations

import json
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
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .scientific_sandbox import (
    PYTHON_SCIENTIFIC_DEPENDENCIES,
    R_SCIENTIFIC_DEPENDENCIES,
    SCIENTIFIC_SANDBOX_LANGUAGES,
    SCIENTIFIC_SANDBOX_PROFILES,
    generated_code_execution_contract_errors,
    normalized_generated_code_language,
    normalized_generated_code_profile,
    normalized_scientific_dependencies,
)
from .structured_output_retry import PacketValidationError


ScientificCodeCheck = Callable[[Mapping[str, Any]], Mapping[str, Any]]

SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS = "native_client_tools"
SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET = "structured_packet"
SCIENTIFIC_SOURCE_SUBMISSION_TOOL = "submit_scientific_source"
SCIENTIFIC_SOURCE_REVISE_CURRENT = "revise_current_source"
SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER = (
    "return_to_bound_dependency_owner"
)
_SCIENTIFIC_PACKAGES = (
    PYTHON_SCIENTIFIC_DEPENDENCIES + R_SCIENTIFIC_DEPENDENCIES
)


@dataclass(frozen=True)
class ScientificCodeWorkspaceResult:
    code_draft: Mapping[str, Any]
    check_result: Mapping[str, Any]
    evidence: Mapping[str, Any]


def scientific_workspace_prototype_observation(
    prototype: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one persisted sandbox result into bounded model feedback."""

    contracts = {
        str(row.get("contract_id", "") or ""): row
        for row in prototype.get("metric_contracts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("contract_id", "") or "").strip()
    }
    evaluation = prototype.get("metric_contract_evaluation", {})
    evaluation_rows = (
        evaluation.get("evaluations", [])
        if isinstance(evaluation, Mapping)
        else []
    )
    failed_contracts: list[dict[str, Any]] = []
    for row in evaluation_rows or []:
        if not isinstance(row, Mapping) or row.get("passed") is True:
            continue
        contract_id = str(row.get("contract_id", "") or "").strip()
        contract = contracts.get(contract_id, {})
        failed_contracts.append(
            {
                key: _bounded_observation_value(value)
                for key, value in {
                    "contract_id": contract_id,
                    "requirement_id": row.get("requirement_id", ""),
                    "metric_path": row.get("metric_path", []),
                    "metric_semantics": contract.get("metric_semantics", ""),
                    "measurement_protocol": contract.get(
                        "measurement_protocol", ""
                    ),
                    "operator": row.get("operator", contract.get("operator", "")),
                    "aggregation": row.get(
                        "aggregation", contract.get("aggregation", "")
                    ),
                    "threshold": contract.get("threshold"),
                    "lower": contract.get("lower"),
                    "upper": contract.get("upper"),
                    "tolerance": contract.get("tolerance"),
                    "observed": row.get("resolved_values_preview", []),
                    "aggregate_value": row.get("aggregate_value"),
                    "errors": row.get("errors", []),
                }.items()
                if value not in (None, "", [], {})
            }
        )
    direct_field_names = [
        "prototype_status",
        "execution_attempted",
        "execution_smoke_passed",
        "smoke_passed",
        "returncode",
        "runtime_errors",
        "safety_errors",
        "estimator_binding_errors",
        "estimator_runtime_failure_ids",
        "estimator_runtime_errors",
        "result_parse_error",
        "stderr_summary",
        "stdout_summary",
        "metric_gate_errors",
        "required_estimator_ids",
        "available_upstream_estimator_ids",
        "estimator_invocation_counts",
        "mechanical_estimator_invocation_verified",
        "script_hash",
        "result_hash",
        "execution_envelope_hash",
    ]
    if (
        prototype.get("mechanical_estimator_invocation_verified") is not True
        or prototype.get("estimator_binding_errors")
        or prototype.get("estimator_runtime_errors")
    ):
        direct_field_names.append("estimator_invocation_samples")
    direct_fields = {
        key: deepcopy(prototype[key])
        for key in direct_field_names
        if prototype.get(key) not in (None, "", [], {})
    }
    return {
        "artifact_kind": "ScientificSandboxWorkspaceObservation",
        **{
            key: _bounded_observation_value(value)
            for key, value in direct_fields.items()
        },
        "failed_metric_contracts": failed_contracts,
        "metrics_preview": _bounded_observation_value(prototype.get("metrics", {})),
        "full_execution_artifact_persisted": True,
        "source_replayed_to_model": False,
        "proof_evidence_status": "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE",
    }


def _bounded_observation_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 8:
        return {"preview": "depth_limit", "type": type(value).__name__}
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= 2_000 else value[:2_000] + "..."
    if isinstance(value, Mapping):
        items = list(value.items())
        preview = {
            str(key): _bounded_observation_value(child, depth=depth + 1)
            for key, child in items[:24]
        }
        if len(items) > 24:
            preview["truncated_key_count"] = len(items) - 24
        return preview
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        rows = list(value)
        if len(rows) <= 12:
            return [
                _bounded_observation_value(row, depth=depth + 1) for row in rows
            ]
        return {
            "preview": "sequence",
            "length": len(rows),
            "head": [
                _bounded_observation_value(row, depth=depth + 1)
                for row in rows[:8]
            ],
            "tail": [
                _bounded_observation_value(row, depth=depth + 1)
                for row in rows[-2:]
            ],
        }
    return str(value)[:2_000]


def run_scientific_code_workspace(
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
    artifact_id: str,
    initial_code_draft: Mapping[str, Any] | None,
    initial_check_result: Mapping[str, Any],
    check_candidate: ScientificCodeCheck,
    workspace_operation: str = "targeted_revision",
    request_metadata: Mapping[str, Any] | None = None,
) -> ScientificCodeWorkspaceResult:
    """Let one model own complete scientific source across raw sandbox feedback."""

    if not str(artifact_id).strip():
        raise ValueError("scientific code workspace requires a bound artifact id")
    for value, label in (
        (max_turns, "turn"),
        (max_no_progress_turns, "no-progress"),
    ):
        if value < 1:
            raise ValueError(f"scientific code workspace {label} budget must be positive")
    if workspace_operation not in {"initial_authoring", "targeted_revision"}:
        raise ValueError("unsupported scientific code workspace operation")

    parent_draft = (
        _complete_code_draft(initial_code_draft)
        if isinstance(initial_code_draft, Mapping) and initial_code_draft
        else {}
    )
    if workspace_operation == "targeted_revision" and not parent_draft:
        raise ValueError("targeted scientific source revision requires parent source")
    parent_hash = stable_hash(parent_draft) if parent_draft else ""
    state: dict[str, Any] = {
        "code_draft": parent_draft,
        "code_draft_hash": parent_hash,
        "source_updates": 0,
        "checks": 0,
        "last_check": deepcopy(dict(initial_check_result)),
    }
    tools = _scientific_code_tools()

    def execute_tool(call, context):
        del context
        tool_input = dict(call.input)
        if call.name == SCIENTIFIC_SOURCE_SUBMISSION_TOOL:
            required_fields = {
                "language",
                "execution_profile",
                "dependencies",
                "entrypoint",
                "code",
            }
            if (
                not required_fields.issubset(tool_input)
                or set(tool_input) - required_fields
            ):
                raise ClientToolInputError(
                    "submit_scientific_source requires the complete language, "
                    "execution_profile, dependencies, entrypoint, and code candidate"
                )
            draft = _complete_code_draft(tool_input)
            draft_hash = stable_hash(draft)
            changed = draft_hash != state["code_draft_hash"]
            if not changed:
                raise ClientToolInputError(
                    "replacement is byte-identical to the current scientific source; "
                    "the deterministic observation is already recorded, so submit a "
                    "changed complete candidate"
                )
            state["code_draft"] = draft
            state["code_draft_hash"] = draft_hash
            state["source_updates"] += 1
            raw = check_candidate(deepcopy(dict(state["code_draft"])))
            if not isinstance(raw, Mapping):
                raise ClientToolInputError("scientific sandbox returned a non-object result")
            check = deepcopy(dict(raw))
            observed_hash = str(check.get("code_draft_hash", "") or "")
            if observed_hash != state["code_draft_hash"]:
                raise ClientToolInputError(
                    "scientific sandbox result is not bound to the current candidate hash"
                )
            state["checks"] += 1
            state["last_check"] = check
            accepted = check.get("accepted") is True
            disposition = str(
                check.get("source_iteration_disposition", "") or ""
            ).strip()
            if not disposition:
                disposition = (
                    "accepted" if accepted else SCIENTIFIC_SOURCE_REVISE_CURRENT
                )
                check["source_iteration_disposition"] = disposition
            if disposition not in {
                "accepted",
                SCIENTIFIC_SOURCE_REVISE_CURRENT,
                SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER,
            }:
                raise ClientToolInputError(
                    "scientific sandbox returned an unsupported source iteration "
                    "disposition"
                )
            if accepted != (disposition == "accepted"):
                raise ClientToolInputError(
                    "scientific sandbox acceptance and source iteration disposition "
                    "disagree"
                )
            terminal = bool(
                accepted
                or disposition == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
            )
            if disposition == SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER:
                source_owner = check.get("source_owner", {})
                if not (
                    isinstance(source_owner, Mapping)
                    and str(source_owner.get("owner_subsystem", "") or "").strip()
                    and str(source_owner.get("source_manifest_id", "") or "").strip()
                    and str(source_owner.get("source_manifest_hash", "") or "").strip()
                    and isinstance(source_owner.get("artifact_ids"), Sequence)
                    and not isinstance(source_owner.get("artifact_ids"), (str, bytes))
                    and source_owner.get("artifact_ids")
                    and isinstance(source_owner.get("artifact_hashes"), Mapping)
                    and all(
                        str(
                            source_owner["artifact_hashes"].get(artifact_id, "")
                            or ""
                        ).strip()
                        for artifact_id in source_owner["artifact_ids"]
                    )
                ):
                    raise ClientToolInputError(
                        "dependency-owner disposition requires bound source owner refs"
                    )
            return ClientToolExecutionResult(
                content={
                    **check,
                    "ok": accepted,
                    "changed": True,
                    "checks": state["checks"],
                    "source_updates": state["source_updates"],
                    "execution_evidence_status": (
                        "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE"
                    ),
                },
                is_error=not accepted,
                state_changed=True,
                terminal=terminal,
                terminal_payload=(
                    {
                        "code_draft": deepcopy(dict(state["code_draft"])),
                        "code_draft_hash": state["code_draft_hash"],
                        "check_result": check,
                    }
                    if terminal
                    else None
                ),
                observation_key="scientific-submission:"
                + stable_hash(
                    {
                        "code_draft_hash": state["code_draft_hash"],
                        "check": check,
                    }
                ),
            )

        raise ClientToolInputError("unsupported scientific code workspace tool")

    request = ClientToolTurnRequest(
        system_prompt=system_prompt,
        messages=(
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\nThis workspace has at most "
                    + str(max_turns)
                    + " total model/tool turns. Retain the observed source hashes, "
                    "sandbox results, and attempted changes across those turns. Do "
                    "not resubmit a previously observed byte-identical candidate."
                )
                + (
                    "\n\nNo scientific source exists yet. Author the complete "
                    "candidate with submit_scientific_source. Each submission is "
                    "executed immediately without runtime source edits."
                    if not parent_draft
                    else "\n\nCurrent complete code candidate:\n"
                    + _compact_json(parent_draft)
                )
                + "\n\nInitial workspace observation:\n"
                + _compact_json(initial_check_result)
                + (
                    "\n\nThe current candidate failed. Diagnose that exact observation, "
                    "then submit a changed complete candidate. Every submission executes "
                    "immediately; identical bytes are not a new attempt."
                    if initial_check_result.get("accepted") is not True
                    and parent_draft
                    else ""
                ),
            },
        ),
        tools=tools,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_choice="any",
        disable_parallel_tool_use=True,
        metadata={
            **dict(request_metadata or {}),
            "model_tier": model_tier,
            "artifact_id": artifact_id,
            "parent_code_draft_hash": parent_hash,
            "workspace_operation": workspace_operation,
        },
    )

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_turns,
            max_no_progress_turns=max_no_progress_turns,
            max_retained_tool_turns=max_turns,
        )
    except ClientToolLoopError as exc:
        raise PacketValidationError(
            validation_label="LLM scientific code workspace",
            attempts=exc.turns,
            errors=[exc.reason],
            history=[deepcopy(dict(row)) for row in exc.history],
            recovery_checkpoint={
                "schema_version": 1,
                "artifact_kind": "ScientificCodeWorkspaceCheckpoint",
                "artifact_id": artifact_id,
                "workspace_operation": workspace_operation,
                "parent_code_draft_hash": parent_hash,
                "current_code_draft_hash": state["code_draft_hash"],
                "current_code_draft": deepcopy(dict(state["code_draft"])),
                "source_updates": state["source_updates"],
                "checks": state["checks"],
                "last_check": deepcopy(dict(state["last_check"])),
                "model_owned_source": True,
                "runtime_edited_source": False,
            },
        ) from exc

    terminal = dict(loop.terminal_payload)
    draft = _complete_code_draft(terminal.get("code_draft", {}))
    check = dict(terminal.get("check_result", {}))
    draft_hash = stable_hash(draft)
    disposition = str(
        check.get("source_iteration_disposition", "") or ""
    ).strip()
    if (
        terminal.get("code_draft_hash") != draft_hash
        or check.get("code_draft_hash") != draft_hash
        or disposition
        not in {"accepted", SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER}
        or (check.get("accepted") is True) != (disposition == "accepted")
    ):
        raise PacketValidationError(
            validation_label="LLM scientific code workspace",
            attempts=loop.turns,
            errors=[
                "terminal payload is not bound to an accepted candidate or exact "
                "dependency source owner"
            ],
            history=[deepcopy(dict(row)) for row in loop.history],
        )

    evidence = {
        "schema_version": 1,
        "artifact_kind": "ScientificCodeWorkspaceResult",
        "artifact_id": artifact_id,
        "transport": "native_client_tools",
        "workspace_operation": workspace_operation,
        "parent_code_draft_hash": parent_hash,
        "initial_check_result_hash": stable_hash(dict(initial_check_result)),
        "initial_check_accepted": initial_check_result.get("accepted") is True,
        "submitted_code_draft_hash": draft_hash,
        "terminal_check_result_hash": stable_hash(check),
        "source_changed": draft_hash != parent_hash,
        "source_updates": state["source_updates"],
        "sandbox_checks": state["checks"],
        "submit_and_execute_atomic": True,
        "max_retained_tool_turns": max_turns,
        "turns": loop.turns,
        "tool_calls": loop.tool_calls,
        "runtime_executed_tool_calls": loop.runtime_executed_tool_calls,
        "provider": loop.provider,
        "model": loop.model,
        "model_tier": model_tier,
        "provider_usage": dict(loop.provider_usage),
        "history": [deepcopy(dict(row)) for row in loop.history],
        "transcript_fingerprint": loop.transcript_fingerprint,
        "model_owned_source": True,
        "runtime_edited_source": False,
        "accepted": check.get("accepted") is True,
        "source_iteration_disposition": disposition,
        "source_owner": deepcopy(dict(check.get("source_owner", {})))
        if isinstance(check.get("source_owner", {}), Mapping)
        else {},
        "proof_evidence_status": "SCIENTIFIC_CODE_EXECUTION_NOT_PROOF_EVIDENCE",
    }
    return ScientificCodeWorkspaceResult(
        code_draft=draft,
        check_result=check,
        evidence=evidence,
    )


def _complete_code_draft(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ClientToolInputError("scientific code candidate must be an object")
    language = normalized_generated_code_language(value.get("language"))
    execution_profile = normalized_generated_code_profile(
        value.get("execution_profile"),
        language=language,
    )
    entrypoint = str(value.get("entrypoint", "") or "").strip()
    code = str(value.get("code", "") or "")
    dependencies = value.get("dependencies", [])
    if not isinstance(dependencies, Sequence) or isinstance(
        dependencies, (str, bytes)
    ):
        raise ClientToolInputError("dependencies must be an array")
    normalized_dependencies = list(
        normalized_scientific_dependencies(dependencies, language=language)
    )
    draft = {
        "language": language,
        "execution_profile": execution_profile,
        "dependencies": normalized_dependencies,
        "entrypoint": entrypoint,
        "code": code,
    }
    contract_errors = generated_code_execution_contract_errors(draft)
    if contract_errors:
        raise ClientToolInputError("; ".join(contract_errors))
    return draft


def _scientific_code_tools() -> tuple[ClientToolDefinition, ...]:
    return (
        ClientToolDefinition(
            name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            description=(
                "Submit one complete Python or R candidate. The runtime stores and "
                "immediately executes the exact source, then returns the raw sandbox "
                "observation to this same model."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "language",
                    "execution_profile",
                    "dependencies",
                    "entrypoint",
                    "code",
                ],
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": list(SCIENTIFIC_SANDBOX_LANGUAGES),
                    },
                    "execution_profile": {
                        "type": "string",
                        "enum": list(SCIENTIFIC_SANDBOX_PROFILES),
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(_SCIENTIFIC_PACKAGES),
                        },
                        "uniqueItems": True,
                    },
                    "entrypoint": {
                        "type": "string",
                        "enum": ["run_sandbox"],
                    },
                    "code": {"type": "string"},
                },
            },
            terminal=True,
        ),
    )


def _compact_json(value: Any, *, max_chars: int = 30_000) -> str:
    encoded = json.dumps(value, separators=(",", ":"), default=str)
    if len(encoded) <= max_chars:
        return encoded
    marker = "\n[observation middle truncated]\n"
    available = max_chars - len(marker)
    head = available // 2
    return encoded[:head] + marker + encoded[-(available - head) :]
