from __future__ import annotations

import os
import subprocess

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


@pytest.fixture
def discovered_repository(tmp_path, monkeypatch):
    from ai_statistician import research_source_discovery as discovery_module
    from ai_statistician.research_source_project import freeze_git_repository_snapshot

    repository = tmp_path / "upstream"
    repository.mkdir()
    files = {
        "README.md": "# Fixture project\n",
        "pkg/method.py": "def marker():\n    return 17\n",
        "pkg/__init__.py": "",
        "assets/raw.bin": b"\x00\xff\x10",
    }
    for name, content in files.items():
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())
    environment = {
        **os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.org",
        "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.org",
        "GIT_AUTHOR_DATE": "2025-01-02T00:00:00Z", "GIT_COMMITTER_DATE": "2025-01-02T00:00:00Z",
    }
    for arguments in (["init"], ["add", "."], ["commit", "-m", "fixture"]):
        subprocess.run(["git", "-C", str(repository), *arguments], check=True, capture_output=True, env=environment)
    revision = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, env=environment,
    ).stdout.strip()
    requests, acquisitions = [], []

    def fetch(url, *_args):
        requests.append(url)
        if "/search/repositories?" in url:
            return {"items": [{"full_name": "fixture/project", "created_at": "2020-01-01"}]}
        if "/commits?" in url:
            return [{"sha": revision}]
        if "/contents?" in url:
            return [{"type": "file", "path": "README.md"}, {"type": "dir", "path": "pkg"}]
        pytest.fail("only search and root resolution may use the fixture network: " + url)

    def acquire(**kwargs):
        acquisitions.append(kwargs)
        return freeze_git_repository_snapshot(repository_root=repository, **kwargs)

    monkeypatch.setattr(discovery_module, "acquire_public_github_repository_snapshot", acquire)
    discovery = discovery_module.PublicResearchSourceDiscovery(
        config=discovery_module.PublicResearchSourceDiscoveryConfig(source_horizon="2025-12-31"),
        state_dir=tmp_path / "source-store", json_fetcher=fetch,
    )
    handle = discovery_module._source_handle(
        discovery.provider_name, "repository", "github:fixture/project", "2025-12-31"
    )
    return {
        "discovery": discovery, "handle": handle, "revision": revision,
        "files": files, "repository": repository, "requests": requests, "acquisitions": acquisitions,
    }
