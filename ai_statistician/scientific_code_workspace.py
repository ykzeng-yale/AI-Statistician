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
from .structured_output_retry import PacketValidationError


ScientificCodeCheck = Callable[[Mapping[str, Any]], Mapping[str, Any]]

SCIENTIFIC_SOURCE_TRANSPORT_NATIVE_CLIENT_TOOLS = "native_client_tools"
SCIENTIFIC_SOURCE_TRANSPORT_STRUCTURED_PACKET = "structured_packet"


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
    direct_fields = {
        key: deepcopy(prototype[key])
        for key in (
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
            "estimator_invocation_samples",
            "mechanical_estimator_invocation_verified",
            "script_hash",
            "result_hash",
            "execution_envelope_hash",
        )
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
        if call.name == "replace_scientific_source":
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
                    "replace_scientific_source requires the complete language, "
                    "execution_profile, dependencies, entrypoint, and code candidate"
                )
            draft = _complete_code_draft(tool_input)
            draft_hash = stable_hash(draft)
            changed = draft_hash != state["code_draft_hash"]
            if not changed:
                raise ClientToolInputError(
                    "replacement is byte-identical to the current scientific source; "
                    "run the current source or submit a changed complete candidate"
                )
            state["code_draft"] = draft
            state["code_draft_hash"] = draft_hash
            state["source_updates"] += 1
            state["last_check"] = {}
            return ClientToolExecutionResult(
                content={
                    "ok": True,
                    "changed": True,
                    "code_draft_hash": draft_hash,
                    "source_updates": state["source_updates"],
                },
                state_changed=True,
                observation_key="scientific-source:" + draft_hash,
            )

        if call.name == "run_scientific_source":
            if tool_input:
                raise ClientToolInputError("run_scientific_source takes an empty object")
            if not state["code_draft"]:
                raise ClientToolInputError(
                    "author complete scientific source before requesting execution"
                )
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
            return ClientToolExecutionResult(
                content={
                    **check,
                    "ok": accepted,
                    "checks": state["checks"],
                    "execution_evidence_status": (
                        "SCIENTIFIC_SANDBOX_OBSERVATION_NOT_PROOF_EVIDENCE"
                    ),
                },
                is_error=not accepted,
                terminal=accepted,
                terminal_payload=(
                    {
                        "code_draft": deepcopy(dict(state["code_draft"])),
                        "code_draft_hash": state["code_draft_hash"],
                        "check_result": check,
                    }
                    if accepted
                    else None
                ),
                observation_key="scientific-check:"
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
                "content": user_prompt
                + (
                    "\n\nNo scientific source exists yet. Author the complete "
                    "candidate with replace_scientific_source before requesting "
                    "execution."
                    if not parent_draft
                    else "\n\nCurrent complete code candidate:\n"
                    + _compact_json(parent_draft)
                )
                + "\n\nInitial workspace observation:\n"
                + _compact_json(initial_check_result)
                + (
                    "\n\nThe current candidate failed. Diagnose that exact observation "
                    "before replacing source; resubmitting identical bytes against the "
                    "same observation is not a new attempt."
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

    def select_tools(_turn_index, available_tools):
        return tuple(
            tool
            for tool in available_tools
            if tool.name != "run_scientific_source" or bool(state["code_draft"])
        )

    try:
        loop = run_bounded_client_tool_loop(
            backend=provider,
            request=request,
            execute_tool=execute_tool,
            max_turns=max_turns,
            max_tool_calls=max_turns,
            max_no_progress_turns=max_no_progress_turns,
            select_tools=select_tools,
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
    if (
        terminal.get("code_draft_hash") != draft_hash
        or check.get("code_draft_hash") != draft_hash
        or check.get("accepted") is not True
    ):
        raise PacketValidationError(
            validation_label="LLM scientific code workspace",
            attempts=loop.turns,
            errors=["terminal payload is not bound to an accepted current candidate"],
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
        "accepted": True,
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
    language = str(value.get("language", "") or "").strip().lower()
    execution_profile = str(value.get("execution_profile", "") or "").strip()
    entrypoint = str(value.get("entrypoint", "") or "").strip()
    code = str(value.get("code", "") or "")
    dependencies = value.get("dependencies", [])
    if language not in {"python", "r"}:
        raise ClientToolInputError("language must be python or r")
    if not execution_profile:
        raise ClientToolInputError("execution_profile must be nonempty")
    if entrypoint != "run_sandbox":
        raise ClientToolInputError("entrypoint must be run_sandbox")
    if not isinstance(dependencies, Sequence) or isinstance(
        dependencies, (str, bytes)
    ):
        raise ClientToolInputError("dependencies must be an array")
    if not code.strip():
        raise ClientToolInputError("code must be nonempty")
    if len(code) > 100_000:
        raise ClientToolInputError("code exceeds the workspace artifact-size boundary")
    draft = {
        "language": language,
        "execution_profile": execution_profile,
        "dependencies": [str(item) for item in dependencies],
        "entrypoint": entrypoint,
        "code": code,
    }
    return draft


def _scientific_code_tools() -> tuple[ClientToolDefinition, ...]:
    return (
        ClientToolDefinition(
            name="replace_scientific_source",
            description=(
                "Replace the complete current Python or R candidate. The runtime stores "
                "and executes the source unchanged."
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
                    "language": {"type": "string", "enum": ["python", "r"]},
                    "execution_profile": {"type": "string"},
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "entrypoint": {
                        "type": "string",
                        "enum": ["run_sandbox"],
                    },
                    "code": {"type": "string"},
                },
            },
        ),
        ClientToolDefinition(
            name="run_scientific_source",
            description=(
                "Execute the exact current source in the isolated scientific sandbox. "
                "A failed run returns raw observations to this same model context; an "
                "accepted run submits the unchanged candidate for independent review."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {},
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
