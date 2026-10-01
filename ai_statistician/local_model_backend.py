from __future__ import annotations

import json
import os
import time
import urllib.request
from urllib.error import HTTPError
from typing import Any, Mapping
from urllib.parse import urlsplit

from .model_backend import (
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
    GeneratorRequest,
    GeneratorResponse,
    _live_generator_timeout_seconds,
)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("local model endpoint must not redirect")


def _chat_messages(request: ClientToolTurnRequest) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": request.system_prompt}
    ]
    for message in request.messages:
        role = str(message["role"])
        content = message["content"]
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
            continue
        text: list[str] = []
        calls: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        for block in content:
            kind = block["type"]
            if kind == "text":
                text.append(str(block["text"]))
            elif kind == "tool_use" and role == "assistant":
                calls.append({
                    "id": block["id"], "type": "function",
                    "function": {"name": block["name"], "arguments": json.dumps(block["input"])},
                })
            elif kind == "tool_result" and role == "user":
                value = json.dumps({
                    "content": block["content"],
                    "is_error": bool(block.get("is_error", False)),
                }, ensure_ascii=False)
                results.append({"role": "tool", "tool_call_id": block["tool_use_id"], "content": value})
            else:
                raise ValueError(f"local text backend does not support {role} block {kind!r}")
        if results:
            messages.extend(results)
        if text or calls:
            row: dict[str, Any] = {"role": role, "content": "\n".join(text)}
            if calls:
                row["tool_calls"] = calls
            messages.append(row)
    return messages


class LocalChatGeneratorBackend:
    """Local OpenAI-compatible transport; the existing runtime executes tools."""

    provider_name = "local"

    def __init__(self, *, base_url: str | None = None, timeout_s: float | None = None) -> None:
        self.base_url = (base_url or os.environ.get(
            "AI_STATISTICIAN_LOCAL_BASE_URL", "http://127.0.0.1:8081/v1"
        )).rstrip("/")
        self.timeout_s = timeout_s
        self.validate_environment()

    def validate_environment(self) -> None:
        url = urlsplit(self.base_url)
        if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "::1", "localhost"}
                or url.username or url.password or url.query or url.fragment):
            raise ValueError("local model URL must be an HTTP loopback endpoint without credentials")

    def _complete(self, payload: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        started = time.monotonic()
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        timeout = _live_generator_timeout_seconds(self.timeout_s)
        try:
            with opener.open(request, timeout=timeout) as response:
                raw = json.load(response)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"local model HTTP {exc.code}: {detail}") from exc
        usage = raw.get("usage", {})
        metadata = {
            "generator_only": True, "retry_count": 0,
            "timeout_seconds": timeout, "elapsed_seconds": time.monotonic() - started,
            "requested_model": payload["model"],
            "provider_reported_model": raw.get("model", ""),
            "provider_usage": {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }, "endpoint": self.base_url,
            "finish_reason": raw["choices"][0].get("finish_reason", ""),
            "provider_stop_reason": raw["choices"][0].get("finish_reason", ""),
            "client_tool_transport": "tools" in payload,
            "tools_executed_by_backend": False,
        }
        return raw, metadata

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [{"role": "system", "content": request.system_prompt},
                         {"role": "user", "content": request.user_prompt}],
            "max_tokens": request.max_tokens, "temperature": request.temperature,
        }
        if request.schema is not None:
            payload["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "generator_response", "schema": dict(request.schema), "strict": True,
            }}
        raw, metadata = self._complete(payload)
        return GeneratorResponse(
            text=raw["choices"][0]["message"].get("content") or "",
            provider=self.provider_name, model=raw.get("model") or request.model,
            raw=raw, metadata={**metadata, "tools_available": False},
        )

    def generate_client_tool_turn(self, request: ClientToolTurnRequest) -> ClientToolTurnResponse:
        if request.thinking_budget_tokens:
            raise ValueError("Anthropic thinking settings cannot be applied to a local model")
        names = [tool.name for tool in request.tools]
        if not names or any(not name for name in names) or len(set(names)) != len(names):
            raise ValueError("local client-tool names must be nonempty and unique")
        choice: Any = request.tool_choice
        if choice == "any":
            choice = "required"
        elif choice != "auto":
            if choice not in names:
                raise ValueError("local client-tool choice must name an exposed tool")
            choice = {"type": "function", "function": {"name": choice}}
        raw, metadata = self._complete({
            "model": request.model, "messages": _chat_messages(request),
            "max_tokens": request.max_tokens, "temperature": request.temperature,
            "tool_choice": choice, "parallel_tool_calls": not request.disable_parallel_tool_use,
            "tools": [{"type": "function", "function": {
                "name": tool.name, "description": tool.description,
                "parameters": dict(tool.input_schema), "strict": tool.strict,
            }} for tool in request.tools],
        })
        message = raw["choices"][0]["message"]
        text = message.get("content") or ""
        blocks: list[dict[str, Any]] = [{"type": "text", "text": text}] if text else []
        calls: list[ClientToolCall] = []
        for item in message.get("tool_calls") or []:
            function = item["function"]
            arguments = json.loads(function["arguments"])
            if not isinstance(arguments, dict):
                raise ValueError("local tool arguments must be a JSON object")
            calls.append(ClientToolCall(call_id=item["id"], name=function["name"], input=arguments))
            blocks.append({"type": "tool_use", "id": item["id"],
                           "name": function["name"], "input": arguments})
        return ClientToolTurnResponse(
            content_blocks=tuple(blocks), tool_calls=tuple(calls), text=text,
            provider=self.provider_name, model=raw.get("model") or request.model,
            raw=raw, metadata={**metadata, "tools_available": True},
        )
