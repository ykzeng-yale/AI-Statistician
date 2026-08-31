from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ai_statistician.cli import main
from ai_statistician.research_source_library import (
    execute_research_source,
    load_research_source_snapshot,
    load_research_source_execution_spec,
)
from ai_statistician.research_source_project import (
    freeze_git_repository_snapshot,
)


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
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
            "result = {'total': total(rows), 'payload_bytes': len(payload)}\n"
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
    }
    for relative_path, content in files.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    binary = b"\x00\x01\xffpublished-binary-fixture\n"
    binary_path = repository / "assets" / "payload.bin"
    binary_path.parent.mkdir(parents=True, exist_ok=True)
    binary_path.write_bytes(binary)
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
    shutil.copytree(tmp_path / "snapshot", tampered_snapshot_dir)
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
    assert set(documents) == {*files, "assets/payload.bin"}
    assert documents["main.py"].git_commit == commit
    assert "dirty" not in snapshot.document_path(
        documents["main.py"].document_id
    ).read_text(encoding="utf-8")
    assert documents["pkg/__init__.py"].content_mode == "text"
    assert documents["pkg/__init__.py"].byte_size == 0
    empty_file_hits = snapshot.search("pkg init", top_k=5)["hits"]
    assert documents["pkg/__init__.py"].document_id not in {
        hit["document_id"] for hit in empty_file_hits
    }
    assert all(hit["line_end"] >= hit["line_start"] for hit in empty_file_hits)
    assert documents["assets/payload.bin"].content_mode == "binary"
    assert documents["tools/helper.sh"].file_mode == "100755"
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
        "payload_bytes": len(binary),
        "total": 10,
    }
    assert snapshot.identity_errors() == []


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
