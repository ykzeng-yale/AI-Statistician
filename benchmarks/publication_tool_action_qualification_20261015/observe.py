"""Observe server-schema tool actions through the existing retained file fixture."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from jsonschema import ValidationError, validate

from ai_statistician.local_model_backend import _chat_messages
from ai_statistician.model_backend import ClientToolCall, ClientToolTurnResponse
from benchmarks.publication_deployment_qualification_20261003 import observe_retained_session as shared


class SchemaActionBackend(shared.RecordingBackend):
    """Experimental wire adapter only; the existing loop executes every action."""

    def __init__(self, output, **kwargs):
        super().__init__(output, **kwargs)
        shared.write_json(output / "action_protocol.json", {
            "format": "server_json_schema_actions_v1",
            "adapter_sha256": shared.digest(Path(__file__)),
            "shared_observer_sha256": shared.digest(Path(shared.__file__)),
            "backend_executes_tools": False,
            "automatic_fallback": False,
        })

    def generate_client_tool_turn(self, request):
        if request.tool_choice != "any" or request.thinking_budget_tokens:
            raise ValueError("this declared prototype requires any-tool, non-thinking turns")
        definitions = [{"name": tool.name, "description": tool.description,
                        "parameters": dict(tool.input_schema)} for tool in request.tools]
        schema = {
            "type": "object", "additionalProperties": False, "required": ["actions"],
            "properties": {"actions": {
                "type": "array", "minItems": 1,
                **({"maxItems": 1} if request.disable_parallel_tool_use else {}),
                "items": {"oneOf": [{
                    "type": "object", "additionalProperties": False,
                    "required": ["name", "arguments"],
                    "properties": {"name": {"const": tool.name},
                                   "arguments": dict(tool.input_schema)},
                } for tool in request.tools]},
            }},
        }
        messages = _chat_messages(request)
        messages[0]["content"] += (
            "\nReturn a JSON object with an actions array. Each action selects a "
            "tool by name and provides its arguments. Use the supplied terminal "
            "tool to finish. Available tools:\n" + json.dumps(definitions, ensure_ascii=False)
        )
        payload = {
            "model": request.model, "messages": messages,
            "max_tokens": request.max_tokens, "temperature": request.temperature,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "client_tool_actions", "strict": True, "schema": schema,
            }},
        }
        raw, metadata = self._complete(payload)
        content = raw["choices"][0]["message"].get("content") or ""
        calls, blocks = [], []
        parse_error = ""
        if metadata.get("provider_stop_reason") == "max_tokens":
            blocks = [{"type": "text", "text": content}]
        else:
            try:
                value = json.loads(content)
                validate(value, schema)
            except (json.JSONDecodeError, ValidationError) as exc:
                parse_error = f"{type(exc).__name__}: {exc}"
                blocks = [{"type": "text", "text": content}]
            else:
                identity = hashlib.sha256(json.dumps([payload, raw], sort_keys=True).encode()).hexdigest()
                for index, action in enumerate(value["actions"]):
                    call = ClientToolCall(f"schema-action:{identity}:{index}",
                                          action["name"], action["arguments"])
                    calls.append(call)
                    blocks.append({"type": "tool_use", "id": call.call_id,
                                   "name": call.name, "input": dict(call.input)})
        shared.write_json(self.output / f"turn-{self.attempts:03d}.action.json", {
            "format": "server_json_schema_actions_v1", "n_tool_calls": len(calls),
            "parse_error": parse_error, "provider_stop_reason": metadata.get("provider_stop_reason"),
        })
        return ClientToolTurnResponse(
            content_blocks=tuple(blocks), tool_calls=tuple(calls),
            text=content if not calls else "", provider=self.provider_name,
            model=raw["model"], raw=raw,
            metadata={**metadata, "tool_action_format": "server_json_schema_actions_v1",
                      "tool_action_error": parse_error,
                      "tools_available": True, "tools_executed_by_backend": False},
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True):
        raise ValueError("commit the prospective condition before observation")
    shared.RecordingBackend = SchemaActionBackend
    status = shared.main()
    listener = subprocess.run(["lsof", "-nP", "-iTCP:8081", "-sTCP:LISTEN"],
                              capture_output=True, text=True, check=False)
    receipt = {"port": 8081, "listener_absent": listener.returncode == 1,
               "command_returncode": listener.returncode,
               "stdout": listener.stdout, "stderr": listener.stderr}
    output = Path(json.loads(args.plan.read_text())["output"])
    shared.write_json(output / "cleanup_check.json", receipt)
    raise SystemExit(status if receipt["listener_absent"] else 1)
