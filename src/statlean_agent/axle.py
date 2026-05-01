"""Small client for optional Axiom AXLE Lean Engine integration."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


AXLE_BASE_URL = "https://axle.axiommath.ai"
AXLE_DEFAULT_ENV = "lean-4.29.0"


class AxleError(RuntimeError):
    """Raised when the AXLE service cannot return a usable response."""


@dataclass(frozen=True)
class AxleClient:
    """HTTP client for AXLE tools.

    The API key is optional because AXLE currently supports unauthenticated
    limited calls. When present, it should be provided via environment variable
    rather than checked into the repository.
    """

    base_url: str = AXLE_BASE_URL
    api_key: str | None = None
    timeout_seconds: int = 120

    @classmethod
    def from_env(
        cls,
        *,
        base_url: str = AXLE_BASE_URL,
        timeout_seconds: int = 120,
    ) -> "AxleClient":
        return cls(
            base_url=base_url,
            api_key=os.environ.get("AXLE_API_KEY"),
            timeout_seconds=timeout_seconds,
        )

    def call_tool(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call one AXLE tool endpoint and return the decoded JSON payload."""

        url = f"{self.base_url.rstrip('/')}/api/v1/{tool}"
        encoded = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Request-Source": "statlean-agent",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise AxleError(f"AXLE {tool} failed with HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise AxleError(f"AXLE {tool} request failed: {error}") from error

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as error:
            raise AxleError(f"AXLE {tool} returned non-JSON response") from error
        if not isinstance(decoded, dict):
            raise AxleError(f"AXLE {tool} returned {type(decoded).__name__}, expected object")
        if "internal_error" in decoded:
            raise AxleError(f"AXLE {tool} internal error: {decoded['internal_error']}")
        if "user_error" in decoded:
            raise AxleError(f"AXLE {tool} rejected request: {decoded['user_error']}")
        if "error" in decoded:
            raise AxleError(f"AXLE {tool} runtime error: {decoded['error']}")
        return decoded

    def transform_code(
        self,
        tool: str,
        code: str,
        *,
        env: str = AXLE_DEFAULT_ENV,
        ignore_imports: bool | None = None,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Call a code-to-code or code-to-report AXLE tool."""

        payload: dict[str, Any] = {"content": code, "environment": env}
        if ignore_imports is not None:
            payload["ignore_imports"] = ignore_imports
        if timeout_seconds is not None:
            payload["timeout_seconds"] = timeout_seconds
        return self.call_tool(tool, payload)

    def verify_proof(
        self,
        *,
        formal_statement: str,
        content: str,
        env: str = AXLE_DEFAULT_ENV,
        ignore_imports: bool | None = None,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Validate that `content` proves the declaration shape in `formal_statement`."""

        payload: dict[str, Any] = {
            "formal_statement": formal_statement,
            "content": content,
            "environment": env,
        }
        if ignore_imports is not None:
            payload["ignore_imports"] = ignore_imports
        if timeout_seconds is not None:
            payload["timeout_seconds"] = timeout_seconds
        return self.call_tool("verify_proof", payload)


def read_source(path: Path) -> str:
    """Read a Lean source file as UTF-8 text."""

    return path.read_text(encoding="utf-8")


def render_payload_summary(payload: dict[str, Any]) -> str:
    """Render a compact, stable summary for CLI output."""

    pieces: list[str] = []
    if "okay" in payload:
        pieces.append(f"okay={payload['okay']}")
    if "documents" in payload and isinstance(payload["documents"], list | dict):
        pieces.append(f"documents={len(payload['documents'])}")
    if "failed_declarations" in payload and isinstance(payload["failed_declarations"], list):
        pieces.append(f"failed_declarations={len(payload['failed_declarations'])}")
    lean_messages = payload.get("lean_messages")
    if isinstance(lean_messages, dict):
        for key in ("errors", "warnings", "infos"):
            values = lean_messages.get(key)
            if isinstance(values, list):
                pieces.append(f"lean_{key}={len(values)}")
    tool_messages = payload.get("tool_messages")
    if isinstance(tool_messages, dict):
        errors = tool_messages.get("errors")
        if isinstance(errors, list):
            pieces.append(f"tool_errors={len(errors)}")
    return " ".join(pieces) if pieces else "ok"
