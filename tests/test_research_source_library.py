from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from ai_statistician.research_source_library import (
    MAX_SOURCE_RESULT_TEXT_BYTES,
    RESEARCH_SOURCE_LIST_TOOL,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
    RESEARCH_SOURCE_SEARCH_TOOL,
    SOURCE_REPLICATION_NOT_PROOF_EVIDENCE,
    _execute_pinned_process,
    _source_execution_sandbox_profile,
    execute_research_source_client_tool,
    execute_research_source,
    inspect_source_replication_result,
    load_research_source_execution_spec,
    load_research_source_snapshot,
    read_source_replication_result,
    research_source_client_tools,
    source_replication_model_observation,
)


def _source_snapshot(tmp_path, *, document_overrides=None):
    source_root = tmp_path / "public_sources"
    source_root.mkdir(parents=True)
    source_text = (
        "# A published result\n"
        "\n"
        "Assume independent observations with finite fourth moments.\n"
        "The normalized sample mean converges to a centered Gaussian limit.\n"
        "A plug-in variance estimator is consistent under the same assumptions.\n"
    )
    source_path = source_root / "result.md"
    source_path.write_text(source_text, encoding="utf-8")
    document = {
        "document_id": "published-result",
        "title": "A published result",
        "source_kind": "paper",
        "relative_path": "result.md",
        "sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        "model_visible": True,
        "citation": "Author (2025), Example Journal",
        "url": "https://example.org/result",
        "publication_date": "2025-03-01",
        "license": "CC-BY-4.0",
    }
    document.update(document_overrides or {})
    manifest = {
        "schema_version": 1,
        "snapshot_id": "published-statistics-2025",
        "source_horizon": "2025-12-31",
        "source_root": "public_sources",
        "documents": [document],
    }
    manifest_path = tmp_path / "sources.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, source_text


def test_hash_bound_source_snapshot_supports_exact_search_and_read(tmp_path) -> None:
    manifest_path, source_text = _source_snapshot(tmp_path)

    snapshot = load_research_source_snapshot(manifest_path)
    search = snapshot.search("finite fourth moments normalized mean", top_k=3)
    read = snapshot.read("published-result", line_start=3, line_end=5)

    assert search["snapshot_hash"] == snapshot.snapshot_hash
    assert search["hits"][0]["document_id"] == "published-result"
    assert "finite fourth moments" in search["hits"][0]["excerpt"]
    assert search["proof_evidence_status"] == RESEARCH_SOURCE_NOT_PROOF_EVIDENCE
    assert read["content"] == "\n".join(source_text.splitlines()[2:5])
    assert read["sha256"] == hashlib.sha256(
        source_text.encode("utf-8")
    ).hexdigest()
    assert read["line_start"] == 3
    assert read["line_end"] == 5
    assert read["citation_ref"].startswith("research-source-ref:")
    assert read["citation_ref"] == snapshot.read(
        "published-result", line_start=3, line_end=5
    )["citation_ref"]
    descriptor = snapshot.descriptor()
    assert descriptor["document_count"] == 1
    assert descriptor["source_horizon"] == "2025-12-31"
    assert descriptor["model_visible"] is True
    assert "relative_path" not in descriptor


def test_shared_source_client_tools_return_hash_bound_refs(tmp_path) -> None:
    manifest_path, source_text = _source_snapshot(tmp_path)
    snapshot = load_research_source_snapshot(manifest_path)

    assert [tool.name for tool in research_source_client_tools()] == [
        RESEARCH_SOURCE_LIST_TOOL,
        RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
    ]
    listing, listing_ref = execute_research_source_client_tool(
        snapshot,
        tool_name=RESEARCH_SOURCE_LIST_TOOL,
        tool_input={"directory": ""},
    )
    search, search_ref = execute_research_source_client_tool(
        snapshot,
        tool_name=RESEARCH_SOURCE_SEARCH_TOOL,
        tool_input={"query": "finite fourth moments", "top_k": 2},
    )
    read, read_ref = execute_research_source_client_tool(
        snapshot,
        tool_name=RESEARCH_SOURCE_READ_TOOL,
        tool_input={
            "document_id": "published-result",
            "line_start": 3,
            "line_end": 5,
        },
    )

    assert listing["entries"] == [
        {
            "entry_kind": "file",
            "name": "result.md",
            "relative_path": "result.md",
            "document_id": "published-result",
            "source_kind": "paper",
            "sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            "content_mode": "text",
            "media_type": "text/plain",
            "byte_size": len(source_text.encode("utf-8")),
            "line_count": len(source_text.splitlines()),
        }
    ]
    assert listing["content_returned"] is False
    assert listing_ref["directory_index_hash"] == listing["directory_index_hash"]
    assert listing_ref["entries"][0]["document_id"] == "published-result"
    assert search_ref["snapshot_hash"] == snapshot.snapshot_hash
    assert search_ref["hits"][0]["document_id"] == "published-result"
    assert read["content"] == "\n".join(source_text.splitlines()[2:5])
    assert read_ref["snapshot_hash"] == snapshot.snapshot_hash
    assert read_ref["content_sha256"] == read["content_sha256"]
    assert search["proof_evidence_status"] == RESEARCH_SOURCE_NOT_PROOF_EVIDENCE
    with pytest.raises(ValueError, match="accepts query"):
        execute_research_source_client_tool(
            snapshot,
            tool_name=RESEARCH_SOURCE_SEARCH_TOOL,
            tool_input={"query": "mean", "hidden": True},
        )


def test_source_search_returns_distinct_documents_before_repeated_ranges(
    tmp_path,
) -> None:
    source_root = tmp_path / "public_sources"
    source_root.mkdir()
    paper_text = (
        "interactive regression orthogonal score definition\n"
        "filler one\n"
        "filler two\n"
        "filler three\n"
        "filler four\n"
        "filler five\n"
        "filler six\n"
        "interactive regression orthogonal score discussion\n"
    )
    implementation_text = (
        "interactive regression implementation score definition\n"
    )
    (source_root / "paper.md").write_text(paper_text, encoding="utf-8")
    (source_root / "implementation.py").write_text(
        implementation_text,
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "snapshot_id": "document-diverse-source-search",
        "source_horizon": "2025-12-31",
        "source_root": "public_sources",
        "documents": [
            {
                "document_id": "paper",
                "title": "Broad paper",
                "source_kind": "paper",
                "relative_path": "paper.md",
                "sha256": hashlib.sha256(paper_text.encode()).hexdigest(),
                "model_visible": True,
            },
            {
                "document_id": "implementation",
                "title": "Exact implementation",
                "source_kind": "code",
                "relative_path": "implementation.py",
                "sha256": hashlib.sha256(
                    implementation_text.encode()
                ).hexdigest(),
                "model_visible": True,
            },
        ],
    }
    manifest_path = tmp_path / "sources.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = load_research_source_snapshot(manifest_path).search(
        "interactive regression orthogonal score",
        top_k=2,
    )

    assert result["retrieval_policy"] == (
        "document_diverse_then_additional_ranges_v1"
    )
    assert {hit["document_id"] for hit in result["hits"]} == {
        "paper",
        "implementation",
    }


def test_source_snapshot_rejects_hash_mismatch(tmp_path) -> None:
    manifest_path, _ = _source_snapshot(
        tmp_path,
        document_overrides={"sha256": "0" * 64},
    )

    with pytest.raises(ValueError, match="sha256 mismatch"):
        load_research_source_snapshot(manifest_path)


def test_source_snapshot_rejects_empty_text(tmp_path) -> None:
    manifest_path, _ = _source_snapshot(tmp_path)
    source_path = tmp_path / "public_sources" / "result.md"
    source_path.write_text("\n", encoding="utf-8")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["documents"][0]["sha256"] = hashlib.sha256(b"\n").hexdigest()
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="must contain nonempty text"):
        load_research_source_snapshot(manifest_path)


def test_source_snapshot_rejects_nonvisible_or_escaping_documents(tmp_path) -> None:
    nonvisible_path, _ = _source_snapshot(
        tmp_path / "nonvisible",
        document_overrides={"model_visible": False},
    )
    with pytest.raises(ValueError, match="model_visible=true"):
        load_research_source_snapshot(nonvisible_path)

    escaping_root = tmp_path / "escaping"
    escaping_root.mkdir()
    hidden_text = "hidden evaluator content\n"
    (escaping_root / "hidden.md").write_text(hidden_text, encoding="utf-8")
    manifest_path, _ = _source_snapshot(
        escaping_root / "snapshot",
        document_overrides={
            "relative_path": "../hidden.md",
            "sha256": hashlib.sha256(hidden_text.encode("utf-8")).hexdigest(),
        },
    )
    with pytest.raises(ValueError, match="stay inside source_root"):
        load_research_source_snapshot(manifest_path)


def _source_execution_fixture(tmp_path):
    source_root = tmp_path / "public_sources"
    source_root.mkdir(parents=True)
    entrypoint_text = "print('coef std err t P>|t| 2.5 % 97.5 %')\n"
    environment_text = "python=3.test\nDemo=1.2.3\n"
    entrypoint_path = source_root / "published_example.py"
    environment_path = source_root / "environment-lock.txt"
    entrypoint_path.write_text(entrypoint_text, encoding="utf-8")
    environment_path.write_text(environment_text, encoding="utf-8")
    source_manifest = {
        "schema_version": 1,
        "snapshot_id": "published-source-v1",
        "source_horizon": "2025-12-31",
        "source_root": "public_sources",
        "documents": [
            {
                "document_id": "published-example",
                "title": "Published example",
                "source_kind": "published_example_code",
                "relative_path": "published_example.py",
                "sha256": hashlib.sha256(entrypoint_text.encode()).hexdigest(),
                "model_visible": True,
                "git_commit": "abc123",
            },
            {
                "document_id": "environment-lock",
                "title": "Environment lock",
                "source_kind": "replication_provenance",
                "relative_path": "environment-lock.txt",
                "sha256": hashlib.sha256(environment_text.encode()).hexdigest(),
                "model_visible": True,
            },
        ],
    }
    source_manifest_path = tmp_path / "sources.json"
    source_manifest_path.write_text(json.dumps(source_manifest), encoding="utf-8")
    snapshot = load_research_source_snapshot(source_manifest_path)

    environment_root = tmp_path / "environment"
    (environment_root / "bin").mkdir(parents=True)
    executable_path = environment_root / "bin" / "python"
    executable_path.symlink_to(sys.executable)
    os.chmod(executable_path, 0o755)
    executable_sha256 = hashlib.sha256(
        executable_path.resolve().read_bytes()
    ).hexdigest()
    execution_payload = {
        "schema_version": 1,
        "artifact_kind": "ResearchSourceExecutionSpec",
        "execution_id": "published-source-execution-v1",
        "benchmark_id": "published-source-benchmark-v1",
        "source_snapshot_id": snapshot.snapshot_id,
        "source_snapshot_hash": snapshot.snapshot_hash,
        "source_manifest_sha256": snapshot.manifest_sha256,
        "source_commit": "abc123",
        "entrypoint_document_id": "published-example",
        "environment_lock_document_id": "environment-lock",
        "environment_root": str(environment_root),
        "python_executable_relative_path": "bin/python",
        "python_executable_sha256": executable_sha256,
        "runtime_read_roots": [str(Path(sys.executable).resolve().parent)],
        "working_directory_relative": ".",
        "arguments": ["--operator-fixed"],
        "package_distributions": {"Demo": "demo"},
        "timeout_seconds": 30,
        "max_output_bytes": 8192,
    }
    execution_manifest_path = tmp_path / "source-execution.json"
    execution_manifest_path.write_text(
        json.dumps(execution_payload), encoding="utf-8"
    )
    execution = load_research_source_execution_spec(
        execution_manifest_path,
        research_sources=snapshot,
    )
    return snapshot, execution, entrypoint_path, execution_manifest_path


def _staged_source_execution_fixture(tmp_path, *, max_output_bytes=8192):
    source_root = tmp_path / "public_sources"
    source_root.mkdir(parents=True)
    entrypoint_text = (
        "from pathlib import Path\n"
        "Path('results.csv').write_text('method,error\\nrecent,0.1\\n')\n"
    )
    environment_text = "python=3.test\nDemo=1.2.3\n"
    published_result_text = "method,error\ndistant,1.0\n"
    files = {
        "published_example.py": entrypoint_text,
        "environment-lock.txt": environment_text,
        "results.csv": published_result_text,
    }
    for relative_path, content in files.items():
        (source_root / relative_path).write_text(content, encoding="utf-8")
    source_manifest = {
        "schema_version": 1,
        "snapshot_id": "published-source-staged-v1",
        "source_horizon": "2025-12-31",
        "source_root": "public_sources",
        "documents": [
            {
                "document_id": "published-example",
                "title": "Published example",
                "source_kind": "published_example_code",
                "relative_path": "published_example.py",
                "sha256": hashlib.sha256(entrypoint_text.encode()).hexdigest(),
                "model_visible": True,
                "git_commit": "abc123",
            },
            {
                "document_id": "environment-lock",
                "title": "Environment lock",
                "source_kind": "replication_provenance",
                "relative_path": "environment-lock.txt",
                "sha256": hashlib.sha256(environment_text.encode()).hexdigest(),
                "model_visible": True,
            },
            {
                "document_id": "published-results",
                "title": "Published results",
                "source_kind": "published_output",
                "relative_path": "results.csv",
                "sha256": hashlib.sha256(published_result_text.encode()).hexdigest(),
                "model_visible": True,
            },
        ],
    }
    source_manifest_path = tmp_path / "sources.json"
    source_manifest_path.write_text(json.dumps(source_manifest), encoding="utf-8")
    snapshot = load_research_source_snapshot(source_manifest_path)

    environment_root = tmp_path / "environment"
    (environment_root / "bin").mkdir(parents=True)
    executable_path = environment_root / "bin" / "python"
    executable_path.symlink_to(sys.executable)
    os.chmod(executable_path, 0o755)
    execution_payload = {
        "schema_version": 2,
        "artifact_kind": "ResearchSourceExecutionSpec",
        "execution_id": "published-source-staged-execution-v1",
        "benchmark_id": "published-source-staged-benchmark-v1",
        "source_snapshot_id": snapshot.snapshot_id,
        "source_snapshot_hash": snapshot.snapshot_hash,
        "source_manifest_sha256": snapshot.manifest_sha256,
        "source_commit": "abc123",
        "entrypoint_document_id": "published-example",
        "environment_lock_document_id": "environment-lock",
        "environment_root": str(environment_root),
        "python_executable_relative_path": "bin/python",
        "python_executable_sha256": hashlib.sha256(
            executable_path.resolve().read_bytes()
        ).hexdigest(),
        "runtime_read_roots": [str(Path(sys.executable).resolve().parent)],
        "working_directory_relative": ".",
        "arguments": [],
        "package_distributions": {"Demo": "demo"},
        "timeout_seconds": 30,
        "max_output_bytes": max_output_bytes,
        "execution_workspace_mode": "staged_copy_on_write",
        "result_artifact_paths": ["results.csv"],
    }
    execution_manifest_path = tmp_path / "source-execution.json"
    execution_manifest_path.write_text(
        json.dumps(execution_payload), encoding="utf-8"
    )
    execution = load_research_source_execution_spec(
        execution_manifest_path,
        research_sources=snapshot,
    )
    return snapshot, execution, source_root / "results.csv"


def test_staged_source_execution_captures_declared_result_without_mutating_source(
    tmp_path,
) -> None:
    snapshot, execution, original_result_path = _staged_source_execution_fixture(
        tmp_path
    )
    original_result = original_result_path.read_text(encoding="utf-8")
    calls = []

    def fake_executor(**kwargs):
        calls.append(kwargs)
        if str(kwargs["command"][1]).endswith("environment_probe.py"):
            stdout = json.dumps(
                {
                    "python_version": "3.test",
                    "package_versions": {"Demo": "1.2.3"},
                }
            )
        else:
            (kwargs["cwd"] / "results.csv").write_text(
                "method,error\nrecent,0.1\n", encoding="utf-8"
            )
            stdout = "replication complete\n"
        return {
            "execution_attempted": True,
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "errors": [],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication-output",
        question_id="published-source-task",
        process_executor=fake_executor,
    )

    assert len(calls) == 2
    assert calls[1]["command"][1].endswith(
        "replication-output/source_workspace/published_example.py"
    )
    assert calls[1]["python_path_root"] == (
        tmp_path / "replication-output" / "source_workspace"
    )
    assert original_result_path.read_text(encoding="utf-8") == original_result
    assert manifest["execution_status"] == "EXECUTED"
    assert manifest["source_mutated"] is False
    assert manifest["staged_source_inputs_mutated"] is False
    assert manifest["unexpected_workspace_artifacts"] == []
    assert manifest["result_artifacts"] == [
        {
            "relative_path": "results.csv",
            "sha256": hashlib.sha256(
                b"method,error\nrecent,0.1\n"
            ).hexdigest(),
            "size_bytes": len(b"method,error\nrecent,0.1\n"),
            "content_encoding": "utf-8",
            "text_line_count": 2,
            "csv_summary": {
                "format": "csv",
                "columns": ["method", "error"],
                "data_rows": 1,
                "column_summaries": {
                    "method": {
                        "nonempty_count": 1,
                        "missing_count": 0,
                        "unique_count": 1,
                        "unique_values": ["recent"],
                    },
                    "error": {
                        "nonempty_count": 1,
                        "missing_count": 0,
                        "unique_count": 1,
                        "unique_values": ["0.1"],
                        "numeric": {
                            "count": 1,
                            "minimum": 0.1,
                            "maximum": 0.1,
                            "mean": 0.1,
                            "all_integer_valued": False,
                        },
                    },
                },
                "scientific_interpretation_performed": False,
            },
            "raw_text": "method,error\nrecent,0.1\n",
            "text_truncated": False,
        }
    ]

    observation = source_replication_model_observation(manifest)
    assert observation["model_observation_compacted"] is True
    assert observation["full_result_bytes_embedded"] is False
    assert "raw_text" not in observation["result_artifacts"][0]
    assert observation["result_artifacts"][0]["csv_summary"]["data_rows"] == 1

    exact_lines = read_source_replication_result(
        manifest,
        relative_path="results.csv",
        line_start=1,
        line_end=2,
    )
    assert exact_lines["content"] == "method,error\nrecent,0.1"
    assert exact_lines["line_count"] == 2
    assert exact_lines["artifact_sha256"] == manifest["result_artifacts"][0][
        "sha256"
    ]


def test_staged_source_result_exposes_exact_pdf_as_model_content(tmp_path) -> None:
    snapshot, execution, _ = _staged_source_execution_fixture(tmp_path)
    execution = replace(execution, result_artifact_paths=("figure.pdf",))
    pdf_bytes = b"%PDF-1.4\n% exact test figure\n%%EOF\n"

    def fake_executor(**kwargs):
        if str(kwargs["command"][1]).endswith("environment_probe.py"):
            stdout = json.dumps({
                "python_version": "3.test", "package_versions": {"Demo": "1.2.3"}})
        else:
            (kwargs["cwd"] / "figure.pdf").write_bytes(pdf_bytes)
            stdout = "replication complete\n"
        return {"execution_attempted": True, "returncode": 0, "stdout": stdout,
                "stderr": "", "errors": []}

    manifest = execute_research_source(
        execution=execution, research_sources=snapshot,
        output_dir=tmp_path / "replication-output", question_id="pdf-task",
        process_executor=fake_executor,
    )
    observation, block = inspect_source_replication_result(
        manifest, relative_path="figure.pdf"
    )

    assert observation["artifact_sha256"] == hashlib.sha256(pdf_bytes).hexdigest()
    assert observation["media_type"] == "application/pdf"
    assert block["type"] == "document"
    assert base64.b64decode(block["source"]["data"], validate=True) == pdf_bytes
    assert source_replication_model_observation(manifest)["result_artifacts"][0][
        "content_available_via"
    ] == "inspect_research_source_result"


def test_staged_source_execution_bounds_large_text_observation(tmp_path) -> None:
    snapshot, execution, _ = _staged_source_execution_fixture(
        tmp_path,
        max_output_bytes=MAX_SOURCE_RESULT_TEXT_BYTES * 2,
    )
    large_result = "x" * (MAX_SOURCE_RESULT_TEXT_BYTES + 1)

    def fake_executor(**kwargs):
        if str(kwargs["command"][1]).endswith("environment_probe.py"):
            stdout = json.dumps(
                {
                    "python_version": "3.test",
                    "package_versions": {"Demo": "1.2.3"},
                }
            )
        else:
            (kwargs["cwd"] / "results.csv").write_text(
                large_result,
                encoding="utf-8",
            )
            stdout = "replication complete\n"
        return {
            "execution_attempted": True,
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "errors": [],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication-output",
        question_id="published-source-task",
        process_executor=fake_executor,
    )

    artifact = manifest["result_artifacts"][0]
    assert manifest["execution_status"] == "EXECUTED"
    assert artifact["text_truncated"] is True
    assert "raw_text" not in artifact
    assert len(artifact["text_preview"].encode("utf-8")) == (
        MAX_SOURCE_RESULT_TEXT_BYTES
    )


def test_source_result_read_fails_closed_after_artifact_mutation(tmp_path) -> None:
    snapshot, execution, _ = _staged_source_execution_fixture(tmp_path)

    def fake_executor(**kwargs):
        if str(kwargs["command"][1]).endswith("environment_probe.py"):
            stdout = json.dumps(
                {
                    "python_version": "3.test",
                    "package_versions": {"Demo": "1.2.3"},
                }
            )
        else:
            (kwargs["cwd"] / "results.csv").write_text(
                "method,error\nrecent,0.1\n", encoding="utf-8"
            )
            stdout = "replication complete\n"
        return {
            "execution_attempted": True,
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "errors": [],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication-output",
        question_id="published-source-task",
        process_executor=fake_executor,
    )
    staged_result = (
        tmp_path / "replication-output" / "source_workspace" / "results.csv"
    )
    staged_result.write_text("method,error\nrecent,9.9\n", encoding="utf-8")

    with pytest.raises(ValueError, match="changed after execution"):
        read_source_replication_result(
            manifest,
            relative_path="results.csv",
            line_start=1,
            line_end=2,
        )


def test_staged_source_execution_rejects_undeclared_workspace_output(tmp_path) -> None:
    snapshot, execution, _ = _staged_source_execution_fixture(tmp_path)

    def fake_executor(**kwargs):
        if str(kwargs["command"][1]).endswith("environment_probe.py"):
            stdout = json.dumps(
                {
                    "python_version": "3.test",
                    "package_versions": {"Demo": "1.2.3"},
                }
            )
        else:
            (kwargs["cwd"] / "results.csv").write_text("ok\n", encoding="utf-8")
            (kwargs["cwd"] / "undeclared.txt").write_text(
                "unexpected\n", encoding="utf-8"
            )
            stdout = "replication complete\n"
        return {
            "execution_attempted": True,
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "errors": [],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication-output",
        question_id="published-source-task",
        process_executor=fake_executor,
    )

    assert manifest["execution_status"] == "FAILED"
    assert manifest["unexpected_workspace_artifacts"] == ["undeclared.txt"]
    assert any("undeclared workspace artifact" in error for error in manifest["errors"])


def test_immutable_source_execution_uses_only_operator_bound_command(tmp_path) -> None:
    snapshot, execution, _, _ = _source_execution_fixture(tmp_path)
    calls = []

    def fake_executor(**kwargs):
        calls.append(kwargs)
        command = kwargs["command"]
        if str(command[1]).endswith("environment_probe.py"):
            stdout = json.dumps(
                {
                    "python_version": "3.test",
                    "package_versions": {"Demo": "1.2.3"},
                }
            )
        else:
            stdout = "coef std err t P>|t| 2.5 % 97.5 %\n0 0.5 0.1 5 0.0 0.3 0.7\n"
        return {
            "execution_attempted": True,
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "errors": [],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication-output",
        question_id="published-source-task",
        process_executor=fake_executor,
    )

    assert len(calls) == 2
    assert calls[1]["command"] == (
        str(execution.interpreter_executable),
        str(snapshot.document_path("published-example")),
        "--operator-fixed",
    )
    assert calls[1]["source_paths"] == tuple(
        snapshot.document_path(document.document_id)
        for document in snapshot.documents
    )
    assert "source_root" not in calls[1]
    assert calls[1]["runtime_executables"] == execution.runtime_executables
    assert manifest["artifact_kind"] == "SourceReplicationManifest"
    assert manifest["question_id"] == "published-source-task"
    assert manifest["execution_status"] == "EXECUTED"
    assert manifest["package_versions"] == {"Demo": "1.2.3"}
    assert manifest["working_directory_relative"] == "."
    assert manifest["arguments"] == ["--operator-fixed"]
    descriptor = execution.descriptor(snapshot)
    assert descriptor["working_directory_relative"] == "."
    assert descriptor["arguments"] == ["--operator-fixed"]
    assert manifest["source_mutated"] is False
    assert manifest["runtime_edited_source"] is False
    assert manifest["command_owned_by_model"] is False
    assert manifest["network_access"] is False
    assert manifest["raw_stdout"].startswith("coef std err")
    assert manifest["stdout_sha256"] == hashlib.sha256(
        manifest["raw_stdout"].encode()
    ).hexdigest()
    assert manifest["proof_evidence_status"] == (
        SOURCE_REPLICATION_NOT_PROOF_EVIDENCE
    )
    persisted = json.loads(Path(manifest["manifest_path"]).read_text())
    assert persisted == manifest
    observation = source_replication_model_observation(manifest)
    assert observation["working_directory_relative"] == "."
    assert observation["arguments"] == ["--operator-fixed"]


def test_schema_v3_runs_hash_bound_interpreter_and_environment_probe(tmp_path) -> None:
    source_root = tmp_path / "public_sources"
    source_root.mkdir()
    files = {
        "published-example.R": "cat('clustered covariance replication complete\\n')\n",
        "environment-probe.R": "# operator-frozen environment probe\n",
        "environment-lock.txt": "R=test\\nsandwich=3.test\n",
    }
    for relative_path, content in files.items():
        (source_root / relative_path).write_text(content, encoding="utf-8")
    documents = []
    for document_id, relative_path, source_kind in (
        ("published-example", "published-example.R", "published_example_code"),
        ("environment-probe", "environment-probe.R", "replication_provenance"),
        ("environment-lock", "environment-lock.txt", "replication_provenance"),
    ):
        content = files[relative_path]
        documents.append(
            {
                "document_id": document_id,
                "title": document_id,
                "source_kind": source_kind,
                "relative_path": relative_path,
                "sha256": hashlib.sha256(content.encode()).hexdigest(),
                "model_visible": True,
                "git_commit": "r-source-commit" if document_id == "published-example" else "",
            }
        )
    source_manifest_path = tmp_path / "sources.json"
    source_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "snapshot_id": "published-r-source-v1",
                "source_horizon": "2026-08-28",
                "source_root": "public_sources",
                "documents": documents,
            }
        ),
        encoding="utf-8",
    )
    snapshot = load_research_source_snapshot(source_manifest_path)
    environment_root = tmp_path / "r-environment"
    (environment_root / "bin").mkdir(parents=True)
    interpreter = environment_root / "bin" / "Rscript"
    interpreter.symlink_to(sys.executable)
    execution_payload = {
        "schema_version": 3,
        "artifact_kind": "ResearchSourceExecutionSpec",
        "execution_id": "published-r-source-execution-v1",
        "benchmark_id": "published-r-source-benchmark-v1",
        "source_snapshot_id": snapshot.snapshot_id,
        "source_snapshot_hash": snapshot.snapshot_hash,
        "source_manifest_sha256": snapshot.manifest_sha256,
        "source_commit": "r-source-commit",
        "entrypoint_document_id": "published-example",
        "environment_lock_document_id": "environment-lock",
        "environment_root": str(environment_root),
        "runtime_language": "r",
        "interpreter_executable_relative_path": "bin/Rscript",
        "interpreter_executable_sha256": hashlib.sha256(
            interpreter.resolve().read_bytes()
        ).hexdigest(),
        "environment_probe_document_id": "environment-probe",
        "interpreter_arguments": ["--quiet"],
        "runtime_environment": {"R_HOME": "/operator-bound/r-home"},
        "runtime_read_roots": [str(Path(sys.executable).resolve().parent)],
        "working_directory_relative": ".",
        "arguments": [],
        "package_distributions": {"sandwich": "sandwich"},
        "timeout_seconds": 30,
        "max_output_bytes": 8192,
    }
    execution_path = tmp_path / "source-execution.json"
    execution_path.write_text(json.dumps(execution_payload), encoding="utf-8")
    execution = load_research_source_execution_spec(
        execution_path, research_sources=snapshot
    )
    calls = []

    def fake_executor(**kwargs):
        calls.append(kwargs)
        probe = str(kwargs["command"][2]).endswith("environment-probe.R")
        return {
            "execution_attempted": True,
            "returncode": 0,
            "stdout": json.dumps(
                {
                    "runtime_language": "r",
                    "runtime_version": "R version test",
                    "package_versions": {"sandwich": "3.test"},
                }
            )
            if probe
            else "clustered covariance replication complete\n",
            "stderr": "",
            "errors": [],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication-output",
        question_id="published-r-source-task",
        process_executor=fake_executor,
    )

    assert [Path(call["command"][2]).name for call in calls] == [
        "environment-probe.R",
        "published-example.R",
    ]
    assert all(call["command"][0] == str(interpreter) for call in calls)
    assert all(call["command"][1] == "--quiet" for call in calls)
    assert all(
        call["runtime_environment"] == (("R_HOME", "/operator-bound/r-home"),)
        for call in calls
    )
    assert manifest["execution_status"] == "EXECUTED"
    assert manifest["runtime_language"] == "r"
    assert manifest["runtime_version"] == "R version test"
    assert manifest["package_versions"] == {"sandwich": "3.test"}
    assert manifest["environment_probe_document_id"] == "environment-probe"
    assert "python_version" not in manifest
    assert "python_executable_sha256" not in manifest
    descriptor = execution.descriptor(snapshot)
    assert descriptor["runtime_language"] == "r"
    assert descriptor["interpreter_arguments"] == ["--quiet"]
    assert descriptor["runtime_environment"] == {
        "R_HOME": "/operator-bound/r-home"
    }
    assert descriptor["environment_probe_sha256"] == documents[1]["sha256"]
    observation = source_replication_model_observation(manifest)
    assert observation["runtime_language"] == "r"
    assert observation["runtime_version"] == "R version test"

    execution_payload.pop("environment_probe_document_id")
    execution_path.write_text(json.dumps(execution_payload), encoding="utf-8")
    with pytest.raises(ValueError, match="non-Python.*environment probe"):
        load_research_source_execution_spec(
            execution_path,
            research_sources=snapshot,
        )

    execution_payload["environment_probe_document_id"] = "environment-probe"
    execution_payload["runtime_environment"] = {"PATH": "/not-allowed"}
    execution_path.write_text(json.dumps(execution_payload), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid or controlled"):
        load_research_source_execution_spec(execution_path, research_sources=snapshot)


def test_schema_v3_python_can_use_runtime_owned_environment_probe(tmp_path) -> None:
    snapshot, _, _, execution_path = _source_execution_fixture(tmp_path)
    execution_payload = json.loads(execution_path.read_text(encoding="utf-8"))
    execution_payload["schema_version"] = 3
    execution_payload["runtime_language"] = "python"
    execution_payload["interpreter_executable_relative_path"] = (
        execution_payload.pop("python_executable_relative_path")
    )
    execution_payload["interpreter_executable_sha256"] = execution_payload.pop(
        "python_executable_sha256"
    )
    execution_payload["package_distributions"] = {"pip": "pip"}
    execution_path.write_text(json.dumps(execution_payload), encoding="utf-8")
    execution = load_research_source_execution_spec(
        execution_path,
        research_sources=snapshot,
    )
    calls = []

    def execute_process(**kwargs):
        calls.append(kwargs)
        completed = subprocess.run(
            kwargs["command"],
            cwd=kwargs["cwd"],
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
        output_dir=tmp_path / "python-replication-output",
        question_id="published-python-source-task",
        process_executor=execute_process,
    )

    assert len(calls) == 2
    assert Path(calls[0]["command"][-1]).name == "environment_probe.py"
    assert manifest["execution_status"] == "EXECUTED"
    assert manifest["environment_probe_document_id"] == ""
    assert manifest["environment_probe_origin"] == "runtime_owned_python_probe"
    assert manifest["runtime_language"] == "python"
    assert manifest["runtime_version"]
    assert manifest["package_versions"]["pip"]
    assert manifest["raw_stdout"].startswith("coef std err")
    descriptor = execution.descriptor(snapshot)
    assert descriptor["environment_probe_document_id"] == ""
    assert descriptor["environment_probe_origin"] == "runtime_owned_python_probe"
    assert len(descriptor["environment_probe_sha256"]) == 64


def test_failed_environment_probe_returns_raw_observation_to_source_owner(
    tmp_path,
) -> None:
    snapshot, execution, _, _ = _source_execution_fixture(tmp_path)
    calls = []

    def fail_probe(**kwargs):
        calls.append(kwargs)
        return {
            "execution_attempted": True,
            "returncode": 71,
            "stdout": "probe diagnostic output\n",
            "stderr": "interpreter startup failed\n",
            "errors": ["probe transport note"],
        }

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "failed-probe-output",
        question_id="published-source-task",
        process_executor=fail_probe,
    )

    assert len(calls) == 1
    assert manifest["execution_attempted"] is False
    assert manifest["environment_probe_execution_attempted"] is True
    assert manifest["environment_probe_returncode"] == 71
    assert manifest["environment_probe_errors"] == ["probe transport note"]
    assert manifest["environment_probe_raw_stdout"] == "probe diagnostic output\n"
    assert manifest["environment_probe_raw_stderr"] == "interpreter startup failed\n"
    assert manifest["environment_probe_stdout_sha256"] == hashlib.sha256(
        b"probe diagnostic output\n"
    ).hexdigest()
    assert manifest["environment_probe_stderr_sha256"] == hashlib.sha256(
        b"interpreter startup failed\n"
    ).hexdigest()
    assert manifest["raw_stdout"] == ""
    assert manifest["raw_stderr"] == ""
    assert manifest["execution_status"] == "FAILED"
    observation = source_replication_model_observation(manifest)
    assert observation["environment_probe_returncode"] == 71
    assert observation["environment_probe_errors"] == ["probe transport note"]
    assert observation["environment_probe_raw_stdout"] == (
        "probe diagnostic output\n"
    )
    assert observation["environment_probe_raw_stderr"] == (
        "interpreter startup failed\n"
    )


def test_source_execution_fails_closed_when_snapshot_changes(tmp_path) -> None:
    snapshot, execution, entrypoint_path, _ = _source_execution_fixture(tmp_path)
    entrypoint_path.write_text("print('mutated')\n", encoding="utf-8")
    calls = []

    manifest = execute_research_source(
        execution=execution,
        research_sources=snapshot,
        output_dir=tmp_path / "replication-output",
        question_id="published-source-task",
        process_executor=lambda **kwargs: calls.append(kwargs),
    )

    assert calls == []
    assert manifest["execution_attempted"] is False
    assert manifest["source_mutated"] is True
    assert manifest["execution_status"] == "FAILED"
    assert any("changed after snapshot load" in error for error in manifest["errors"])


def test_source_execution_manifest_rejects_model_command_fields(tmp_path) -> None:
    snapshot, _, _, execution_manifest_path = _source_execution_fixture(tmp_path)
    payload = json.loads(execution_manifest_path.read_text())
    payload["command"] = ["sh", "-c", "anything"]
    execution_manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown fields: command"):
        load_research_source_execution_spec(
            execution_manifest_path,
            research_sources=snapshot,
        )


def test_source_sandbox_reads_only_inventory_and_executes_only_allowlist(
    tmp_path,
) -> None:
    environment_root = tmp_path / "environment"
    runtime_root = tmp_path / "runtime"
    source_root = tmp_path / "sources"
    output_dir = tmp_path / "output"
    for path in (environment_root, runtime_root, source_root, output_dir):
        path.mkdir()
    requested_python = environment_root / "python"
    requested_python.write_text("python", encoding="utf-8")
    runtime_executable = runtime_root / "python-app"
    runtime_executable.write_text("runtime", encoding="utf-8")
    listed_source = source_root / "listed.py"
    listed_source.write_text("print('listed')\n", encoding="utf-8")

    profile = _source_execution_sandbox_profile(
        requested_executable=requested_python,
        executable=requested_python,
        environment_root=environment_root,
        runtime_read_roots=(runtime_root,),
        runtime_executables=((runtime_executable, "a" * 64),),
        source_paths=(listed_source,), cwd=source_root,
        output_dir=output_dir,
    )
    process_clause = profile.split("(allow process-exec ", 1)[1].split(
        ") (deny file-read", 1
    )[0]
    read_clause = profile.split("(allow file-read* ", 1)[1].split(
        ") (allow file-read-metadata", 1
    )[0]

    assert f'(literal "{listed_source.resolve()}")' in profile
    assert f'(literal "{source_root.resolve()}")' in profile
    assert f'(subpath "{source_root.resolve()}")' not in profile
    assert f'(literal "{runtime_executable.resolve()}")' in process_clause
    assert f'(literal "{runtime_executable.resolve()}")' in read_clause
    assert "(subpath " not in process_clause
    assert "(deny process-fork)" not in profile


def test_pinned_process_executes_resolved_virtualenv_launcher(
    tmp_path, monkeypatch
) -> None:
    environment_root = tmp_path / "environment"
    runtime_root = tmp_path / "runtime"
    source_root = tmp_path / "sources"
    output_dir = tmp_path / "output"
    for path in (environment_root / "bin", runtime_root, source_root, output_dir):
        path.mkdir(parents=True)
    exact_executable = runtime_root / "python"
    exact_executable.write_text("runtime", encoding="utf-8")
    exact_executable.chmod(0o755)
    requested_executable = environment_root / "bin" / "python"
    requested_executable.symlink_to(exact_executable)
    source_path = source_root / "entrypoint.py"
    source_path.write_text("print('ok')\n", encoding="utf-8")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["environment"] = kwargs["env"]

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr(
        "ai_statistician.research_source_library.shutil.which",
        lambda _: "/usr/bin/sandbox-exec",
    )
    monkeypatch.setattr(
        "ai_statistician.research_source_library.subprocess.run", fake_run
    )

    result = _execute_pinned_process(
        command=(str(requested_executable), str(source_path)),
        cwd=source_root,
        stdout_path=output_dir / "stdout",
        stderr_path=output_dir / "stderr",
        environment_root=environment_root,
        runtime_read_roots=(runtime_root,),
        runtime_executables=(),
        runtime_environment=(),
        source_paths=(source_path,),
        output_dir=output_dir,
        timeout_seconds=30,
        max_output_bytes=8192,
    )

    assert result["returncode"] == 0
    assert captured["command"][3] == str(exact_executable.resolve())
    assert captured["environment"]["__PYVENV_LAUNCHER__"] == str(
        requested_executable.absolute()
    )
