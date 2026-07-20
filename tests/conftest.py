from __future__ import annotations

import os

import pytest


TEST_CLAUDE_HAIKU_MODEL = "claude-haiku-4-5-20251001"

_LIVE_CREDENTIAL_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "AXLE_API_KEY",
    "ARISTOTLE_API_KEY",
)
_NON_HAIKU_MODEL_OVERRIDE_ENV_VARS = (
    "AI_STATISTICIAN_LLM_MODEL",
    "AI_STATISTICIAN_ANTHROPIC_MODEL",
    "AI_STATISTICIAN_THEORY_MODEL",
    "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
    "AI_STATISTICIAN_ANTHROPIC_SONNET_MODEL",
    "AI_STATISTICIAN_CLAUDE_OPUS_MODEL",
    "AI_STATISTICIAN_ANTHROPIC_OPUS_MODEL",
    "AI_STATISTICIAN_OPENAI_MODEL",
)


def _isolate_test_environment() -> None:
    for name in _LIVE_CREDENTIAL_ENV_VARS:
        os.environ.pop(name, None)
    for name in _NON_HAIKU_MODEL_OVERRIDE_ENV_VARS:
        os.environ.pop(name, None)
    os.environ["AI_STATISTICIAN_ENV_FILE"] = os.devnull
    os.environ["AI_STATISTICIAN_CLAUDE_HAIKU_MODEL"] = TEST_CLAUDE_HAIKU_MODEL
    os.environ["AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL"] = TEST_CLAUDE_HAIKU_MODEL


# Apply before test modules are imported, then restore the invariant before each test.
_isolate_test_environment()


@pytest.fixture(autouse=True)
def isolate_live_credentials_and_pin_test_haiku(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _LIVE_CREDENTIAL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    for name in _NON_HAIKU_MODEL_OVERRIDE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AI_STATISTICIAN_ENV_FILE", os.devnull)
    monkeypatch.setenv(
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        TEST_CLAUDE_HAIKU_MODEL,
    )
    monkeypatch.setenv(
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
        TEST_CLAUDE_HAIKU_MODEL,
    )
