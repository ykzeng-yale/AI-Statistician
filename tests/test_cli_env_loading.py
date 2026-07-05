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


def test_load_dotenv_default_path_honors_operator_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / "operator_keys.md"
    env_file.write_text("Anthropic API Key: sk-ant-operator-env-file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AI_STATISTICIAN_ENV_FILE", str(env_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    _load_dotenv(Path(".env"))

    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-operator-env-file"


def test_load_dotenv_keeps_missing_explicit_env_file_explicit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / "operator_keys.md"
    env_file.write_text("Anthropic API Key: sk-ant-operator-env-file\n", encoding="utf-8")
    monkeypatch.setenv("AI_STATISTICIAN_ENV_FILE", str(env_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    _load_dotenv(tmp_path / "missing_explicit.env")

    assert "ANTHROPIC_API_KEY" not in os.environ


def test_load_dotenv_default_path_discovers_operator_download_key_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    downloads = home / "Downloads"
    downloads.mkdir(parents=True)
    key_file = downloads / "api_key_AI_statistician.md"
    key_file.write_text("Anthropic API Key: sk-ant-downloads-key\n", encoding="utf-8")
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("AI_STATISTICIAN_ENV_FILE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    _load_dotenv(Path(".env"))

    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-downloads-key"
