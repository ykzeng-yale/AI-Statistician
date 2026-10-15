"""One deployment check using the product transport; not a scientific evaluation."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from ai_statistician.client_tool_loop import (
    ClientToolExecutionResult,
    ClientToolLoopError,
    persist_client_tool_session,
    run_bounded_client_tool_loop,
)
from ai_statistician.local_model_backend import LocalChatGeneratorBackend
from ai_statistician.model_backend import (
    ClientToolDefinition,
    ClientToolTurnRequest,
    GeneratorRequest,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    backend = LocalChatGeneratorBackend(timeout_s=600)
    schema_request = GeneratorRequest(
        system_prompt="Return the requested JSON value.",
        user_prompt="Return transport_ok true.", model=args.model,
        max_tokens=8192, temperature=1.0,
        schema={"type": "object", "properties": {"transport_ok": {"type": "boolean"}},
                "required": ["transport_ok"], "additionalProperties": False},
    )
    raw_observation = "opaque-feedback-6841\nline 12: fixture failed"
    invoked: list[str] = []

    def execute(call, _context):
        invoked.append(call.name)
        if call.name == "read_observation":
            return ClientToolExecutionResult(content=raw_observation, is_error=True)
        assert call.name == "submit_observation"
        assert call.input["text"] == raw_observation
        return ClientToolExecutionResult(
            content="Received exact observation.", terminal=True,
            terminal_payload={"text": call.input["text"]},
        )

    request = ClientToolTurnRequest(
        system_prompt="First read_observation, then submit_observation with the exact observed text, including newlines. Do not correct the fixture failure.",
        messages=({"role": "user", "content": "Check tool feedback transport."},),
        model=args.model, max_tokens=8192, temperature=1.0,
        disable_parallel_tool_use=True,
        tools=(
            ClientToolDefinition(
                name="read_observation", description="Read a raw fixture failure.",
                input_schema={"type": "object", "properties": {}, "additionalProperties": False}),
            ClientToolDefinition(
                name="submit_observation", description="Submit the exact raw text.", terminal=True,
                input_schema={"type": "object", "properties": {"text": {"type": "string"}},
                              "required": ["text"], "additionalProperties": False}),
        ),
    )
    (args.output / "requests.json").write_text(json.dumps({
        "schema": asdict(schema_request), "tools": asdict(request),
        "scope": "Deployment transport only; no scientific question or acceptance.",
    }, indent=2) + "\n")
    try:
        response = backend.generate(schema_request)
        (args.output / "schema_response.json").write_text(json.dumps(asdict(response), indent=2) + "\n")
        assert json.loads(response.text) == {"transport_ok": True}
        result = run_bounded_client_tool_loop(
            backend=backend, request=request, execute_tool=execute,
            max_turns=4, max_tool_calls=4, max_no_progress_turns=2,
            session_dir=args.output / "session", session_id="deployment-feedback",
        )
        (args.output / "tool_result.json").write_text(json.dumps(asdict(result), indent=2) + "\n")
        persist_client_tool_session(
            session_dir=args.output / "session", session_id="deployment-feedback",
            request=request, messages=result.messages, observation_refs=result.observation_refs,
        )
        assert invoked[0] == "read_observation" and invoked[-1] == "submit_observation"
        assert result.terminal_payload == {"text": raw_observation}
        assert result.provider_usage["input_tokens"] > 0
        assert result.provider_usage["output_tokens"] > 0
    except Exception as exc:
        failure = {"status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)}
        if isinstance(exc, ClientToolLoopError):
            failure.update(history=exc.history, messages=exc.messages,
                           provider_usage=exc.provider_usage,
                           final_response_metadata=exc.final_response_metadata)
        (args.output / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
        raise
    (args.output / "success.json").write_text(json.dumps({
        "status": "TRANSPORT_PASSED", "model": result.model,
        "turns": result.turns, "tool_calls": result.tool_calls,
        "scope": "Native schema and exact failed-tool feedback, not research capability.",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
