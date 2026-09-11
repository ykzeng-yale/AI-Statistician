from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import ai_statistician.research_source_project as research_source_project_module
from ai_statistician.cli import main
from ai_statistician.research_source_library import (
    RESEARCH_SOURCE_LIST_TOOL,
    execute_research_source_client_tool,
    execute_research_source,
    load_research_source_snapshot,
    load_research_source_execution_spec,
)
from ai_statistician.research_source_project import (
    acquire_public_github_repository_snapshot,
    freeze_git_repository_snapshot,
)


def _git(repository: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment.update({
        "GIT_AUTHOR_DATE": "2025-01-02T03:04:05+00:00",
        "GIT_COMMITTER_DATE": "2025-01-02T03:04:05+00:00",
    })
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    ).stdout.strip()


def test_exact_git_project_snapshot_runs_multifile_source_with_binary_asset(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "upstream"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "fixture@example.org")
    _git(repository, "config", "user.name", "Fixture Author")
    files = {
        "main.py": (
            "import json\n"
            "from pathlib import Path\n"
            "from pkg.compute import total\n\n"
            "rows = [int(value) for value in "
            "Path('data/table.csv').read_text().splitlines()[1:]]\n"
            "payload = Path('assets/payload.bin').read_bytes()\n"
            "license_alias = Path('vendor/LICENSE').read_text().strip()\n"
            "result = {'total': total(rows), 'payload_bytes': len(payload), "
            "'license_alias': license_alias}\n"
            "Path('results.json').write_text(json.dumps(result, sort_keys=True))\n"
            "print(json.dumps(result, sort_keys=True))\n"
        ),
        "pkg/__init__.py": "",
        "pkg/compute.py": "def total(values):\n    return sum(values)\n",
        "data/table.csv": "value\n2\n3\n5\n",
        "environment-lock.txt": "runtime=fixture-python\nDemo=1.0\n",
        "environment_probe.py": (
            "import json\n"
            "print(json.dumps({'runtime_language': 'python', "
            "'runtime_version': 'fixture-python', "
            "'package_versions': {'Demo': '1.0'}}))\n"
        ),
        "tools/helper.sh": "#!/bin/sh\nexit 0\n",
        "vendor/COPYING": "fixture-license\n",
    }
    for relative_path, content in files.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    binary = b"\x00\x01\xffpublished-binary-fixture\n"
    binary_path = repository / "assets" / "payload.bin"
    binary_path.parent.mkdir(parents=True, exist_ok=True)
    binary_path.write_bytes(binary)
    symlink_path = repository / "vendor" / "LICENSE"
    symlink_path.symlink_to("COPYING")
    (repository / "tools" / "helper.sh").chmod(0o755)
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "published fixture")
    commit = _git(repository, "rev-parse", "HEAD")

    with pytest.raises(ValueError, match="after the configured source horizon"):
        freeze_git_repository_snapshot(
            repository_root=repository,
            revision=commit,
            output_dir=tmp_path / "future-snapshot",
            snapshot_id="future-project-v1",
            source_horizon="2000-01-01",
        )

    # The frozen project must come from the commit, not mutable worktree bytes.
    (repository / "main.py").write_text("raise RuntimeError('dirty')\n", encoding="utf-8")
    snapshot = freeze_git_repository_snapshot(
        repository_root=repository,
        revision=commit,
        output_dir=tmp_path / "snapshot",
        snapshot_id="published-project-v1",
        source_horizon="2026-08-31",
        repository_url="https://github.com/example/published-project",
        license_name="MIT",
    )
    assert snapshot.descriptor()["repository_identity"]["git_commit"] == commit

    tampered_snapshot_dir = tmp_path / "tampered-snapshot"
    shutil.copytree(tmp_path / "snapshot", tampered_snapshot_dir, symlinks=True)
    tampered_manifest_path = tampered_snapshot_dir / "sources.json"
    tampered_manifest = json.loads(tampered_manifest_path.read_text(encoding="utf-8"))
    tampered_manifest["repository_identity"]["tree_index_hash"] = "0" * 64
    tampered_manifest_path.write_text(
        json.dumps(tampered_manifest),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="repository tree identity mismatch"):
        load_research_source_snapshot(tampered_manifest_path)

    documents = {document.title: document for document in snapshot.documents}
    assert set(documents) == {*files, "assets/payload.bin", "vendor/LICENSE"}
    assert documents["main.py"].git_commit == commit
    assert "dirty" not in snapshot.document_path(
        documents["main.py"].document_id
    ).read_text(encoding="utf-8")
    assert documents["pkg/__init__.py"].content_mode == "text"
    assert documents["pkg/__init__.py"].byte_size == 0
    root_listing = snapshot.list_directory("", limit=20)
    assert [
        (entry["entry_kind"], entry["name"])
        for entry in root_listing["entries"]
    ] == [
        ("directory", "assets"),
        ("directory", "data"),
        ("directory", "pkg"),
        ("directory", "tools"),
        ("directory", "vendor"),
        ("file", "environment-lock.txt"),
        ("file", "environment_probe.py"),
        ("file", "main.py"),
    ]
    first_page = snapshot.list_directory("", limit=2)
    second_page = snapshot.list_directory("", offset=2, limit=2)
    assert first_page["next_offset"] == 2
    assert [entry["name"] for entry in second_page["entries"]] == ["pkg", "tools"]
    assert first_page["directory_index_hash"] == second_page["directory_index_hash"]
    package_listing = snapshot.list_directory("pkg")
    empty_descriptor = next(
        entry
        for entry in package_listing["entries"]
        if entry["name"] == "__init__.py"
    )
    assert empty_descriptor["content_mode"] == "text"
    assert empty_descriptor["byte_size"] == 0
    asset_listing = snapshot.list_directory("assets")
    assert asset_listing["entries"][0]["content_mode"] == "binary"
    assert asset_listing["entries"][0]["byte_size"] == len(binary)
    listing_observation, listing_ref = execute_research_source_client_tool(
        snapshot,
        tool_name=RESEARCH_SOURCE_LIST_TOOL,
        tool_input={"directory": "assets", "limit": 1},
    )
    assert listing_ref["snapshot_hash"] == snapshot.snapshot_hash
    assert listing_ref["directory_index_hash"] == (
        listing_observation["directory_index_hash"]
    )
    assert "content" not in listing_ref["entries"][0]
    with pytest.raises(ValueError, match="canonical and relative"):
        snapshot.list_directory("../assets")
    with pytest.raises(ValueError, match="unknown or empty"):
        snapshot.list_directory("missing")
    with pytest.raises(ValueError, match="offset exceeds"):
        snapshot.list_directory("assets", offset=2)
    empty_file_hits = snapshot.search("pkg init", top_k=5)["hits"]
    assert documents["pkg/__init__.py"].document_id not in {
        hit["document_id"] for hit in empty_file_hits
    }
    assert all(hit["line_end"] >= hit["line_start"] for hit in empty_file_hits)
    assert documents["assets/payload.bin"].content_mode == "binary"
    assert documents["tools/helper.sh"].file_mode == "100755"
    assert documents["vendor/LICENSE"].file_mode == "120000"
    assert documents["vendor/LICENSE"].symlink_target == "COPYING"
    frozen_symlink = snapshot.document_path(documents["vendor/LICENSE"].document_id)
    assert frozen_symlink.is_symlink()
    assert os.readlink(frozen_symlink) == "COPYING"
    vendor_listing = snapshot.list_directory("vendor")
    license_entry = next(
        entry for entry in vendor_listing["entries"] if entry["name"] == "LICENSE"
    )
    assert license_entry["entry_kind"] == "symlink"
    assert license_entry["symlink_target"] == "COPYING"
    assert snapshot.document_path(
        documents["assets/payload.bin"].document_id
    ).read_bytes() == binary
    with pytest.raises(ValueError, match="descriptor-only binary"):
        snapshot.read(
            documents["assets/payload.bin"].document_id,
            line_start=1,
            line_end=1,
        )
    assert snapshot.identity_errors() == []
    frozen_main = snapshot.document_path(documents["main.py"].document_id)
    frozen_main.chmod(0o755)
    assert any("executable mode changed" in error for error in snapshot.identity_errors())
    frozen_main.chmod(0o644)
    assert snapshot.identity_errors() == []
    frozen_symlink.unlink()
    frozen_symlink.symlink_to("../data/table.csv")
    assert any("symlink" in error for error in snapshot.identity_errors())
    frozen_symlink.unlink()
    frozen_symlink.symlink_to("COPYING")
    assert snapshot.identity_errors() == []
    environment_root = tmp_path / "environment"
    (environment_root / "bin").mkdir(parents=True)
    executable = environment_root / "bin" / "python"
    executable.symlink_to(sys.executable)
    os.chmod(executable, 0o755)
    execution_payload = {
        "schema_version": 3,
        "artifact_kind": "ResearchSourceExecutionSpec",
        "execution_id": "published-project-execution-v1",
        "benchmark_id": "published-project-benchmark-v1",
        "source_snapshot_id": snapshot.snapshot_id,
        "source_snapshot_hash": snapshot.snapshot_hash,
        "source_manifest_sha256": snapshot.manifest_sha256,
        "source_commit": commit,
        "entrypoint_document_id": documents["main.py"].document_id,
        "environment_lock_document_id": documents[
            "environment-lock.txt"
        ].document_id,
        "environment_root": str(environment_root),
        "runtime_language": "python",
        "interpreter_executable_relative_path": "bin/python",
        "interpreter_executable_sha256": hashlib.sha256(
            executable.resolve().read_bytes()
        ).hexdigest(),
        "environment_probe_document_id": documents[
            "environment_probe.py"
        ].document_id,
        "runtime_read_roots": [str(Path(sys.executable).resolve().parent)],
        "working_directory_relative": ".",
        "arguments": [],
        "package_distributions": {"Demo": "demo"},
        "timeout_seconds": 30,
        "max_output_bytes": 8192,
        "execution_workspace_mode": "staged_copy_on_write",
        "result_artifact_paths": ["results.json"],
    }
    execution_path = tmp_path / "execution.json"
    execution_path.write_text(json.dumps(execution_payload), encoding="utf-8")
    execution = load_research_source_execution_spec(
        execution_path,
        research_sources=snapshot,
    )

    def execute_process(**kwargs):
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        python_path_root = kwargs.get("python_path_root")
        if python_path_root is not None:
            environment["PYTHONPATH"] = str(python_path_root)
        completed = subprocess.run(
            kwargs["command"],
            cwd=kwargs["cwd"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=kwargs["timeout_seconds"],
        )
        return {
            "execution_attempted": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "errors": [],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication",
        question_id="published-project-task",
        process_executor=execute_process,
    )

    assert manifest["execution_status"] == "EXECUTED"
    assert manifest["staged_source_inputs_mutated"] is False
    assert manifest["unexpected_workspace_artifacts"] == []
    assert os.access(
        tmp_path / "replication" / "source_workspace" / "tools" / "helper.sh",
        os.X_OK,
    )
    assert manifest["result_artifacts"][0]["relative_path"] == "results.json"
    result_path = tmp_path / "replication" / "source_workspace" / "results.json"
    assert json.loads(result_path.read_text(encoding="utf-8")) == {
        "license_alias": "fixture-license",
        "payload_bytes": len(binary),
        "total": 10,
    }
    staged_symlink = (
        tmp_path / "replication" / "source_workspace" / "vendor" / "LICENSE"
    )
    assert staged_symlink.is_symlink()
    assert os.readlink(staged_symlink) == "COPYING"
    assert snapshot.identity_errors() == []

    def execute_with_changed_symlink(**kwargs):
        source_root = kwargs.get("python_path_root")
        if source_root is not None:
            changed = Path(source_root) / "vendor" / "LICENSE"
            changed.unlink()
            changed.symlink_to("../data/table.csv")
        return execute_process(**kwargs)

    changed_manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "changed-link-replication",
        question_id="changed-link-project-task",
        process_executor=execute_with_changed_symlink,
    )
    assert changed_manifest["execution_status"] == "FAILED"
    assert changed_manifest["staged_source_inputs_mutated"] is True
    assert any(
        "symlink changed" in error or "unsafe or changed symlink" in error
        for error in changed_manifest["errors"]
    )


def test_git_project_snapshot_rejects_escaping_or_chained_symlinks(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "unsafe-upstream"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "fixture@example.org")
    _git(repository, "config", "user.name", "Fixture Author")
    (repository / "target.txt").write_text("target\n", encoding="utf-8")
    (repository / "escaping").symlink_to("../outside")
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "escaping symlink")

    with pytest.raises(ValueError, match="escapes source root"):
        freeze_git_repository_snapshot(
            repository_root=repository,
            revision="HEAD",
            output_dir=tmp_path / "escaping-snapshot",
            snapshot_id="escaping-snapshot",
            source_horizon="2026-08-31",
        )

    (repository / "escaping").unlink()
    (repository / "first").symlink_to("target.txt")
    (repository / "second").symlink_to("first")
    _git(repository, "add", "-A")
    _git(repository, "commit", "-m", "chained symlink")

    with pytest.raises(ValueError, match="regular tracked file"):
        freeze_git_repository_snapshot(
            repository_root=repository,
            revision="HEAD",
            output_dir=tmp_path / "chained-snapshot",
            snapshot_id="chained-snapshot",
            source_horizon="2026-08-31",
        )


def test_git_project_snapshot_does_not_lazy_fetch_missing_blobs(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "promisor-source"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "fixture@example.org")
    _git(repository, "config", "user.name", "Fixture Author")
    (repository / "README.md").write_text(
        "# Promisor fixture\n",
        encoding="utf-8",
    )
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-m", "promisor fixture")

    remote = tmp_path / "promisor-remote.git"
    subprocess.run(
        ["git", "clone", "--quiet", "--bare", str(repository), str(remote)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(remote, "config", "uploadpack.allowFilter", "true")
    partial = tmp_path / "partial"
    subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--filter=blob:none",
            "--no-checkout",
            remote.as_uri(),
            str(partial),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_before = _git(
        partial,
        "rev-list",
        "--objects",
        "--missing=print",
        "HEAD",
    ).splitlines()
    if not any(row.startswith("?") for row in missing_before):
        pytest.skip("Git did not create a blobless promisor clone")

    with pytest.raises(ValueError, match="blob to be available locally"):
        freeze_git_repository_snapshot(
            repository_root=partial,
            revision="HEAD",
            output_dir=tmp_path / "partial-snapshot",
            snapshot_id="partial-snapshot",
            source_horizon="2026-08-31",
        )

    assert _git(
        partial,
        "rev-list",
        "--objects",
        "--missing=print",
        "HEAD",
    ).splitlines() == missing_before
    assert not (tmp_path / "partial-snapshot").exists()


@pytest.mark.parametrize("failure", ["exit", "timeout"])
def test_public_git_failure_preserves_unknown_stdout_and_stderr(tmp_path, monkeypatch, failure):
    stdout, stderr = b"opaque progress\n", b"unfamiliar environment diagnostic\n"

    def fail(command, **_kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 1, output=stdout, stderr=stderr)
        raise subprocess.CalledProcessError(71, command, output=stdout, stderr=stderr)

    monkeypatch.setattr(research_source_project_module.subprocess, "run", fail)
    with pytest.raises(ValueError) as error:
        research_source_project_module._run_public_git(
            ["git", "fetch"], private_home=tmp_path, timeout_seconds=1,
        )
    assert stdout.decode() in str(error.value)
    assert stderr.decode() in str(error.value)


def test_public_github_project_acquisition_fetches_exact_commit_without_credentials(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "public-source"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "fixture@example.org")
    _git(repository, "config", "user.name", "Fixture Author")
    (repository / "README.md").write_text(
        "# Public project\n",
        encoding="utf-8",
    )
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-m", "public fixture")
    commit = _git(repository, "rev-parse", "HEAD")
    remote = tmp_path / "public-remote.git"
    subprocess.run(
        ["git", "clone", "--quiet", "--bare", str(repository), str(remote)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(remote, "config", "uploadpack.allowFilter", "true")

    public_url = "https://github.com/example/public-fixture"
    original_run = subprocess.run
    fetch_environments = []

    def run_with_local_public_remote(command, *args, **kwargs):
        if "fetch" in command and public_url + ".git" in command:
            environment = dict(kwargs["env"])
            fetch_environments.append(environment)
            assert environment["GIT_ALLOW_PROTOCOL"] == "https"
            assert environment["GIT_TERMINAL_PROMPT"] == "0"
            assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
            assert all(
                secret not in environment
                for secret in (
                    "ANTHROPIC_API_KEY",
                    "GH_TOKEN",
                    "GITHUB_TOKEN",
                    "HTTPS_PROXY",
                )
            )
            command = [
                remote.as_uri() if value == public_url + ".git" else value
                for value in command
            ]
            kwargs = {
                **kwargs,
                "env": {**environment, "GIT_ALLOW_PROTOCOL": "file"},
            }
        return original_run(command, *args, **kwargs)

    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-enter-git")
    monkeypatch.setenv("GH_TOKEN", "must-not-enter-git")
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-enter-git")
    monkeypatch.setenv("HTTPS_PROXY", "https://must-not-enter-git.invalid")
    monkeypatch.setattr(
        research_source_project_module.subprocess,
        "run",
        run_with_local_public_remote,
    )
    output_dir = tmp_path / "public-snapshot"

    exit_code = main([
        "acquire-public-research-source-project",
        "--repository-url", public_url + ".git",
        "--revision", commit,
        "--snapshot-id", "public-project-v1",
        "--source-horizon", "2026-08-31",
        "--license", "MIT",
        "--out", str(output_dir),
    ])

    emitted = json.loads(capsys.readouterr().out)
    snapshot = load_research_source_snapshot(output_dir / "sources.json")
    assert exit_code == 0
    assert len(fetch_environments) == 1
    assert emitted["repository_identity"]["git_commit"] == commit
    assert snapshot.documents[0].title == "README.md"
    assert snapshot.document_path(snapshot.documents[0].document_id).read_text(
        encoding="utf-8"
    ) == "# Public project\n"
    assert not list(tmp_path.glob(".research-source-acquisition-*"))


@pytest.mark.parametrize(
    "repository_url",
    [
        "http://github.com/example/project",
        "https://example.com/example/project",
        "https://user@github.com/example/project",
        "https://github.com/example/project?token=secret",
        "file:///tmp/example/project",
    ],
)
def test_public_github_project_acquisition_rejects_noncanonical_urls(
    tmp_path: Path,
    repository_url: str,
) -> None:
    with pytest.raises(ValueError, match="https://github.com/owner/repository"):
        acquire_public_github_repository_snapshot(
            repository_url=repository_url,
            revision="a" * 40,
            output_dir=tmp_path / "invalid-snapshot",
            snapshot_id="invalid-snapshot",
            source_horizon="2026-08-31",
        )


def test_freeze_research_source_project_cli_emits_loadable_snapshot(
    tmp_path: Path,
    capsys,
) -> None:
    repository = tmp_path / "cli-upstream"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "fixture@example.org")
    _git(repository, "config", "user.name", "Fixture Author")
    (repository / "README.md").write_text("# Published project\n", encoding="utf-8")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-m", "published fixture")
    commit = _git(repository, "rev-parse", "HEAD")
    output_dir = tmp_path / "cli-snapshot"

    exit_code = main([
        "freeze-research-source-project",
        "--repository", str(repository),
        "--revision", commit,
        "--snapshot-id", "cli-published-project-v1",
        "--source-horizon", "2026-08-31",
        "--repository-url", "https://github.com/example/cli-project",
        "--license", "MIT",
        "--out", str(output_dir),
    ])

    emitted = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert emitted["snapshot_id"] == "cli-published-project-v1"
    assert emitted["document_count"] == 1
    assert Path(emitted["manifest_path"]) == output_dir / "sources.json"
    assert json.loads((output_dir / "sources.json").read_text())[
        "repository_identity"
    ]["git_commit"] == commit
