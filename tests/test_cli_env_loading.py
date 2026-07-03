from __future__ import annotations

import os
from pathlib import Path

from ai_statistician.cli import _load_dotenv


def test_load_dotenv_accepts_markdown_secret_labels(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / "api_keys.md"
    env_file.write_text(
        "\n".join(
            [
                "# local operator keys",
                "Anthropic API Key: sk-ant-test-value",
                "OpenAI API Key: sk-openai-test-value",
                "Axiom Math AXLE API Key: axle-test-value",
                "export ARISTOTLE_API_KEY=aristotle-test-value",
            ]
        ),
        encoding="utf-8",
    )
    for key in (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "AXLE_API_KEY",
        "ARISTOTLE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    _load_dotenv(env_file)

    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test-value"
    assert os.environ["OPENAI_API_KEY"] == "sk-openai-test-value"
    assert os.environ["AXLE_API_KEY"] == "axle-test-value"
    assert os.environ["ARISTOTLE_API_KEY"] == "aristotle-test-value"


def test_load_dotenv_accepts_raw_provider_secret_without_overriding(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / "api_keys.md"
    env_file.write_text(
        "\n".join(
            [
                "sk-ant-raw-test-value",
                "sk-raw-openai-test-value",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "existing-anthropic")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    _load_dotenv(env_file)

    assert os.environ["ANTHROPIC_API_KEY"] == "existing-anthropic"
    assert os.environ["OPENAI_API_KEY"] == "sk-raw-openai-test-value"
