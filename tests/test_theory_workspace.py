from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
    ClientToolInputError,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.scientific_sandbox import ScientificSandboxExecution
from ai_statistician.research_source_library import (
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_RESULT_READ_TOOL,
    RESEARCH_SOURCE_RUN_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceExecutionSpec,
    load_research_source_snapshot,
)
from ai_statistician.research_source_discovery import (
    RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
    ResearchSourceDiscoveryError,
)
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.theory_workspace import (
    SOURCE_REPLICATION_CHECKPOINT_KIND,
    SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL,
    THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    THEORY_SCRATCHPAD_TOOL,
    THEORY_WORKSPACE_CHECKPOINT_KIND,
    THEORY_WORKSPACE_COMMIT_TOOL,
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
    THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
    THEORY_WORKSPACE_GAP_TOOL,
    THEORY_WORKSPACE_HANDOFF_ROLE,
    THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND,
    THEORY_WORKSPACE_PROGRESS_TOOL,
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
    THEORY_WORKSPACE_WRITE_TOOL,
    TheoryScratchpadConfig,
    TheoryWorkspaceGapError,
    TheoryWorkspaceProgressError,
    _replace_theory_workspace_artifacts,
    _theory_workspace_tools,
    load_theory_workspace_documents,
    load_theory_progress_checkpoint_state,
    run_theory_artifact_workspace,
    theory_workspace_manifest_errors,
)


class ScriptedTheoryWorkspaceBackend:
    provider_name = "anthropic"

    def __init__(self, responses: list[ClientToolTurnResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[ClientToolTurnRequest] = []

    def generate_client_tool_turn(
        self,
        request: ClientToolTurnRequest,
    ) -> ClientToolTurnResponse:
        self.requests.append(request)
        return self.responses.pop(0)


def _response(*calls: ClientToolCall) -> ClientToolTurnResponse:
    return ClientToolTurnResponse(
        content_blocks=tuple(
            {
                "type": "tool_use",
                "id": call.call_id,
                "name": call.name,
                "input": dict(call.input),
            }
            for call in calls
        ),
        tool_calls=tuple(calls),
        text="",
        provider="anthropic",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        metadata={"provider_stop_reason": "tool_use"},
    )


def _artifact_writes(artifacts: dict[str, object]) -> dict[str, object]:
    return {
        "writes": [
            {"artifact_name": name, "value": value}
            for name, value in artifacts.items()
        ]
    }


def _commit_checkpoint(
    call_id: str = "commit-theory-checkpoint",
    rationale: str = "The current theory is ready for independent review.",
) -> ClientToolCall:
    return ClientToolCall(
        call_id=call_id,
        name=THEORY_WORKSPACE_COMMIT_TOOL,
        input={"readiness_rationale": rationale},
    )


def _run_workspace(backend, **overrides):
    kwargs = {
        "provider": backend,
        "system_prompt": "Use the theory workspace tools.",
        "user_prompt": "Revise the theory from independent observations.",
        "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "model_tier": "haiku",
        "temperature": 0.0,
        "max_tokens": 1200,
        "max_turns": 4,
        "max_tool_calls": 8,
        "max_no_progress_turns": 2,
        "workspace_id": "theory-workspace:q1",
        "question_id": "q1",
        "authoring_binding_id": "authoring-binding:q1",
        "workspace_operation": "test_authoring",
        "initial_artifacts": {
            "problem_card": {"claim": "parent-private-claim"},
            "lemma_cards": [],
        },
        "build_candidate": lambda artifacts, changed, manifest, changed_documents: {
            "artifacts": dict(artifacts),
            "changed": list(changed),
            "manifest": dict(manifest),
            "changed_documents": list(changed_documents),
        },
        "validate_candidate": lambda packet: (
            []
            if packet.get("artifacts", {}).get("problem_card", {}).get("claim")
            == "revised claim"
            and packet.get("artifacts", {}).get("lemma_cards")
            else ["revised claim and at least one lemma are required"]
        ),
    }
    kwargs.update(overrides)
    return run_theory_artifact_workspace(**kwargs)


def _research_source_snapshot(tmp_path):
    source_root = tmp_path / "public_sources"
    source_root.mkdir()
    source_text = (
        "# Robust location\n"
        "Assume a symmetric distribution with finite variance.\n"
        "The estimating equation has zero expectation at the population center.\n"
        "This identifies the target under the stated symmetry condition.\n"
    )
    (source_root / "location.md").write_text(source_text, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "snapshot_id": "robust-location-sources",
        "source_horizon": "2025-12-31",
        "source_root": "public_sources",
        "documents": [
            {
                "document_id": "robust-location-paper",
                "title": "Robust location",
                "source_kind": "paper",
                "relative_path": "location.md",
                "sha256": hashlib.sha256(
                    source_text.encode("utf-8")
                ).hexdigest(),
                "model_visible": True,
                "citation": "Example (2025)",
            }
        ],
    }
    manifest_path = tmp_path / "sources.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return load_research_source_snapshot(manifest_path), source_text


def test_same_theory_model_searches_and_reads_hash_bound_sources_without_copying_them_to_evidence(
    tmp_path,
) -> None:
    research_sources, source_text = _research_source_snapshot(tmp_path)
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="search-source",
                    name=RESEARCH_SOURCE_SEARCH_TOOL,
                    input={
                        "query": "symmetric estimating equation population center",
                        "top_k": 2,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="read-source",
                    name=RESEARCH_SOURCE_READ_TOOL,
                    input={
                        "document_id": "robust-location-paper",
                        "line_start": 2,
                        "line_end": 4,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-source-grounded-theory",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "source-grounded-lemma"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        research_sources=research_sources,
    )

    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert tool_names == [
        "read_theory_workspace",
        RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
        THEORY_WORKSPACE_WRITE_TOOL,
        THEORY_WORKSPACE_COMMIT_TOOL,
        THEORY_WORKSPACE_GAP_TOOL,
    ]
    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert research_sources.snapshot_hash in initial_prompt
    assert "Cite the exact citation_ref" in initial_prompt
    assert "most specific primary definition or implementation" in initial_prompt
    assert "do not substitute a nearby model family" in initial_prompt
    assert "estimating equation" in str(backend.requests[1].messages)
    read_observation = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert read_observation["content"] == "\n".join(
        source_text.splitlines()[1:4]
    )
    assert read_observation["document_id"] == "robust-location-paper"
    assert result.evidence["research_source_snapshot"]["snapshot_hash"] == (
        research_sources.snapshot_hash
    )
    assert len(result.evidence["source_search_refs"]) == 1
    assert result.evidence["source_search_refs"][0]["retrieval_policy"] == (
        "document_diverse_then_additional_ranges_v1"
    )
    assert len(result.evidence["source_read_refs"]) == 1
    read_ref = result.evidence["source_read_refs"][0]
    assert read_ref["document_id"] == "robust-location-paper"
    assert read_ref["line_start"] == 2
    assert read_ref["line_end"] == 4
    assert read_ref["citation_ref"].startswith("research-source-ref:")
    assert "content" not in read_ref
    persisted_evidence = json.dumps(result.evidence)
    assert "The estimating equation has zero expectation" not in persisted_evidence
    assert "research source text omitted" in persisted_evidence


def test_same_theory_model_discovers_and_reads_public_source_without_a_scout_agent() -> None:
    source_handle = "public-source:" + "a" * 28
    source_content = "# Public result\n\nThe exact asymptotic variance is finite.\n"

    class FakeDiscovery:
        provider_name = "fake_public_source_provider"

        def descriptor(self):
            return {
                "artifact_kind": "PublicResearchSourceDiscoveryDescriptor",
                "provider": self.provider_name,
                "source_horizon": "2025-12-31",
                "strict_historical_benchmark_authority": False,
            }

        def search(self, query, *, source_kind="all", top_k=5):
            assert query == "asymptotic variance reference implementation"
            assert source_kind == "all"
            assert top_k == 3
            return {
                "ok": True,
                "provider": self.provider_name,
                "source_horizon": "2025-12-31",
                "query_hash": stable_hash(query),
                "source_kind": source_kind,
                "results": [
                    {
                        "source_handle": source_handle,
                        "source_kind": "paper",
                        "title": "Public result",
                        "url": "https://doi.org/10.1000/example",
                        "publication_date": "2024-01-01",
                        "citation": "Example (2024)",
                        "summary": "Exact public abstract text.",
                    }
                ],
            }

        def read(self, handle, *, path="", revision=""):
            assert handle == source_handle
            assert path == ""
            assert revision == ""
            return {
                "ok": True,
                "provider": self.provider_name,
                "source_handle": source_handle,
                "source_kind": "paper",
                "title": "Public result",
                "url": "https://doi.org/10.1000/example",
                "publication_date": "2024-01-01",
                "citation": "Example (2024)",
                "revision": "crossref-record:abc",
                "path": "metadata.md",
                "content": source_content,
                "content_sha256": hashlib.sha256(
                    source_content.encode("utf-8")
                ).hexdigest(),
                "content_truncated": False,
                "citation_ref": "public-research-source-ref:abc",
            }

    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="discover-public-source",
                    name=RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
                    input={
                        "query": "asymptotic variance reference implementation",
                        "source_kind": "all",
                        "top_k": 3,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="read-public-source",
                    name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                    input={"source_handle": source_handle},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-public-source-grounded-theory",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "public-source-lemma"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        research_source_discovery=FakeDiscovery(),
    )

    assert [tool.name for tool in backend.requests[0].tools] == [
        "read_theory_workspace",
        RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
        RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
        THEORY_WORKSPACE_WRITE_TOOL,
        THEORY_WORKSPACE_COMMIT_TOOL,
        THEORY_WORKSPACE_GAP_TOOL,
    ]
    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert "2025-12-31" in initial_prompt
    assert "same TheoryDeveloper session" in initial_prompt
    assert "strict historical benchmarks" in initial_prompt.lower()
    assert "Exact public abstract text" in str(backend.requests[1].messages)
    read_observation = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert read_observation["content"] == source_content
    assert len(result.evidence["source_discovery_search_refs"]) == 1
    assert len(result.evidence["source_discovery_read_refs"]) == 1
    read_ref = result.evidence["source_discovery_read_refs"][0]
    assert read_ref["content_sha256"] == hashlib.sha256(
        source_content.encode("utf-8")
    ).hexdigest()
    assert "content" not in read_ref
    persisted_evidence = json.dumps(result.evidence)
    assert "exact asymptotic variance is finite" not in persisted_evidence.lower()
    assert "research source text omitted" in persisted_evidence


def test_public_discovery_failure_returns_to_same_theory_model_without_retry_layer() -> None:
    class UnavailableDiscovery:
        provider_name = "unavailable_public_source_provider"

        def descriptor(self):
            return {
                "provider": self.provider_name,
                "source_horizon": "2025-12-31",
            }

        def search(self, query, *, source_kind="all", top_k=5):
            del query, source_kind, top_k
            raise ResearchSourceDiscoveryError(
                "public research API returned HTTP 503"
            )

        def read(self, source_handle, *, path="", revision=""):
            raise AssertionError((source_handle, path, revision))

    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="discover-unavailable-source",
                    name=RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
                    input={"query": "robust estimator"},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="continue-after-source-failure",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "source-unavailable-lemma"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        research_source_discovery=UnavailableDiscovery(),
    )

    failure = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert failure["ok"] is False
    assert failure["error"] == "public_research_source_discovery_failed"
    assert failure["detail"] == "public research API returned HTTP 503"
    assert failure["model_may_continue_without_this_source"] is True
    assert "_client_tool_budget" not in failure
    assert result.core_packet["artifacts"]["problem_card"]["claim"] == (
        "revised claim"
    )
    assert result.evidence["source_discovery_search_refs"] == []


def test_same_theory_model_runs_operator_bound_source_and_receives_raw_feedback(
    tmp_path,
    monkeypatch,
) -> None:
    research_sources, _ = _research_source_snapshot(tmp_path)
    source_execution = ResearchSourceExecutionSpec(
        execution_id="execution-v1",
        benchmark_id="benchmark-v1",
        manifest_sha256="a" * 64,
        source_snapshot_id=research_sources.snapshot_id,
        source_snapshot_hash=research_sources.snapshot_hash,
        source_manifest_sha256=research_sources.manifest_sha256,
        source_commit="commit-v1",
        entrypoint_document_id="robust-location-paper",
        environment_lock_document_id="robust-location-paper",
        environment_root=tmp_path,
        python_executable=tmp_path / "python",
        python_executable_sha256="b" * 64,
        runtime_read_roots=(),
        working_directory_relative=".",
        arguments=(),
        package_distributions=(("Demo", "demo"),),
        timeout_seconds=30,
        max_output_bytes=8192,
    )
    source_output = tmp_path / "source-output"
    staged_result = source_output / "source_workspace" / "results.csv"
    staged_result.parent.mkdir(parents=True)
    result_text = "method,error\nrecent,0.1\n"
    staged_result.write_text(result_text, encoding="utf-8")
    manifest_body = {
        "schema_version": 2,
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": "source_replication:fixture",
        "question_id": "q1",
        "execution_status": "EXECUTED",
        "raw_stdout": "coef=0.5\n",
        "raw_stderr": "",
        "stdout_sha256": hashlib.sha256(b"coef=0.5\n").hexdigest(),
        "manifest_path": str(source_output / "source_replication_manifest.json"),
        "result_artifacts": [
            {
                "relative_path": "results.csv",
                "sha256": hashlib.sha256(result_text.encode()).hexdigest(),
                "size_bytes": len(result_text.encode()),
                "content_encoding": "utf-8",
                "text_line_count": 2,
                "raw_text": result_text,
                "text_truncated": False,
            }
        ],
        "source_mutated": False,
        "runtime_edited_source": False,
        "runtime_generated": True,
        "model_authored": False,
        "proof_evidence_status": "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE",
    }
    manifest = {**manifest_body, "manifest_hash": stable_hash(manifest_body)}
    calls = []

    def fake_execute_research_source(**kwargs):
        calls.append(kwargs)
        return manifest

    monkeypatch.setattr(
        "ai_statistician.theory_workspace.execute_research_source",
        fake_execute_research_source,
    )
    scratch_calls = []

    def fake_execute_scientific_sandbox(**kwargs):
        scratch_calls.append(kwargs)
        input_hashes = {
            binding.artifact_id: binding.content_sha256
            for binding in kwargs["input_artifacts"]
        }
        return ScientificSandboxExecution(
            status="EXECUTED",
            language="python",
            execution_profile="scientific_wasm",
            backend="pyodide",
            isolation_provider="test-isolation",
            dependencies=(),
            execution_attempted=True,
            returncode=0,
            metrics={"data_rows": 1},
            errors=(),
            stdout_summary="",
            stderr_summary="",
            result_parse_error="",
            code_path=str(tmp_path / "scratch.py"),
            request_path=str(tmp_path / "request.json"),
            result_path=str(tmp_path / "result.json"),
            code_hash=stable_hash(kwargs["code"]),
            request_hash="source-result-scratch-request",
            result_hash=stable_hash({"data_rows": 1}),
            subprocess_environment_keys=("HOME", "PATH"),
            resource_limits={"cpu_seconds": 9},
            input_artifact_hashes=input_hashes,
            input_artifact_binding_hash=stable_hash(input_hashes),
        )

    monkeypatch.setattr(
        "ai_statistician.theory_workspace.execute_scientific_sandbox",
        fake_execute_scientific_sandbox,
    )
    scratch_source = (
        "import csv\nimport io\n\n"
        "def run_sandbox(seed, replicates, artifacts):\n"
        "    rows = list(csv.DictReader(io.StringIO("
        "artifacts['results.csv']['content'])))\n"
        "    return {'data_rows': len(rows)}\n"
    )
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="run-published-source",
                    name=RESEARCH_SOURCE_RUN_TOOL,
                    input={},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="analyze-published-result",
                    name=THEORY_SCRATCHPAD_TOOL,
                    input={
                        "language": "python",
                        "execution_profile": "scientific_wasm",
                        "dependencies": [],
                        "entrypoint": "run_sandbox",
                        "code": scratch_source,
                        "source_result_artifact_paths": ["results.csv"],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="read-published-result",
                    name=RESEARCH_SOURCE_RESULT_READ_TOOL,
                    input={
                        "relative_path": "results.csv",
                        "line_start": 1,
                        "line_end": 2,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-replication-grounded-theory",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "replication-grounded-lemma"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        research_sources=research_sources,
        research_source_execution=source_execution,
        workspace_dir=tmp_path / "theory-workspace",
        scratchpad=TheoryScratchpadConfig(
            sandbox_dir=tmp_path / "scratch",
            seed=17,
            replicates=1,
            max_runs=1,
        ),
    )

    assert len(calls) == 1
    assert calls[0]["execution"] is source_execution
    assert calls[0]["research_sources"] is research_sources
    first_tools = [tool.name for tool in backend.requests[0].tools]
    assert first_tools[:5] == [
        "read_theory_workspace",
        RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
        RESEARCH_SOURCE_RUN_TOOL,
        RESEARCH_SOURCE_RESULT_READ_TOOL,
    ]
    assert "coef=0.5" in str(backend.requests[1].messages)
    assert "raw_text" not in str(backend.requests[1].messages)
    assert "method,error" in str(backend.requests[3].messages)
    assert len(scratch_calls) == 1
    assert scratch_calls[0]["code"] == scratch_source
    assert len(scratch_calls[0]["input_artifacts"]) == 1
    bound_result = scratch_calls[0]["input_artifacts"][0]
    assert bound_result.artifact_id == "results.csv"
    assert bound_result.content == result_text
    assert bound_result.content_sha256 == hashlib.sha256(
        result_text.encode()
    ).hexdigest()
    scratch_observation = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert scratch_observation["metrics"] == {"data_rows": 1}
    assert scratch_observation["input_artifact_hashes"] == {
        "results.csv": hashlib.sha256(result_text.encode()).hexdigest()
    }
    assert result.evidence["source_replication_runs"] == 1
    assert result.evidence["source_replication_manifests"] == [manifest]
    assert result.evidence["source_result_read_refs"] == [
        {
            "artifact_id": "source_replication:fixture",
            "relative_path": "results.csv",
            "artifact_sha256": hashlib.sha256(result_text.encode()).hexdigest(),
            "line_count": 2,
            "line_start": 1,
            "line_end": 2,
            "content_sha256": hashlib.sha256(
                b"method,error\nrecent,0.1"
            ).hexdigest(),
            "proof_evidence_status": (
                "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
            ),
        }
    ]
    assert "coef=0.5" not in json.dumps(result.evidence["history"])
    assert "method,error" not in json.dumps(result.evidence["history"])
    assert "source-replication refs" in json.dumps(result.evidence["history"])


def test_source_only_intent_commits_markdown_report_without_theory_packet(
    tmp_path,
    monkeypatch,
) -> None:
    research_sources, _ = _research_source_snapshot(tmp_path)
    source_execution = ResearchSourceExecutionSpec(
        execution_id="execution-source-only",
        benchmark_id="benchmark-source-only",
        manifest_sha256="a" * 64,
        source_snapshot_id=research_sources.snapshot_id,
        source_snapshot_hash=research_sources.snapshot_hash,
        source_manifest_sha256=research_sources.manifest_sha256,
        source_commit="commit-source-only",
        entrypoint_document_id="robust-location-paper",
        environment_lock_document_id="robust-location-paper",
        environment_root=tmp_path,
        python_executable=tmp_path / "python",
        python_executable_sha256="b" * 64,
        runtime_read_roots=(),
        working_directory_relative=".",
        arguments=(),
        package_distributions=(("Demo", "demo"),),
        timeout_seconds=30,
        max_output_bytes=8192,
    )
    manifest_body = {
        "schema_version": 1,
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": "source_replication:q1",
        "question_id": "q1",
        "execution_status": "EXECUTED",
        "raw_stdout": "coef=0.5\n",
        "raw_stderr": "",
        "stdout_sha256": hashlib.sha256(b"coef=0.5\n").hexdigest(),
        "source_snapshot_hash": research_sources.snapshot_hash,
        "source_mutated": False,
        "runtime_edited_source": False,
        "runtime_generated": True,
        "model_authored": False,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    manifest = {**manifest_body, "manifest_hash": stable_hash(manifest_body)}
    monkeypatch.setattr(
        "ai_statistician.theory_workspace.execute_research_source",
        lambda **_: manifest,
    )
    report_path = "replication/report.md"
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="run-source-only",
                    name=RESEARCH_SOURCE_RUN_TOOL,
                    input={},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-source-report",
                    name=THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                    input={
                        "path": report_path,
                        "content": (
                            "# Replication report\n\nThe immutable run returned "
                            "`coef=0.5`; hidden evaluation remains external.\n"
                        ),
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="commit-source-report-invalid-gap-shape",
                    name=SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL,
                    input={
                        "report_document_path": report_path,
                        "readiness_rationale": (
                            "The exact source run and its interpretation are recorded."
                        ),
                        "unresolved_gaps": [
                            {"gap": "transitive dependency identity is incomplete"}
                        ],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="commit-source-report-corrected",
                    name=SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL,
                    input={
                        "report_document_path": report_path,
                        "readiness_rationale": (
                            "The exact source run and its interpretation are recorded."
                        ),
                        "unresolved_gaps": [
                            "Transitive dependency identity is incomplete."
                        ],
                    },
                )
            ),
        ]
    )
    task_intent = {
        "source_replication": "required",
        "theory": "optional",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "unresolved_gaps": "required",
    }

    result = _run_workspace(
        backend,
        research_sources=research_sources,
        research_source_execution=source_execution,
        allow_source_replication_checkpoint=True,
        task_intent=task_intent,
        workspace_dir=tmp_path / "source-only-workspace",
        require_document_authority=True,
        max_turns=3,
        max_tool_calls=4,
    )

    assert result.core_packet["artifact_kind"] == (
        SOURCE_REPLICATION_CHECKPOINT_KIND
    )
    assert result.core_packet["task_intent"] == task_intent
    assert result.core_packet["report_document"]["relative_path"] == report_path
    assert result.core_packet["unresolved_gaps"] == [
        "Transitive dependency identity is incomplete."
    ]
    assert len(backend.requests) == 4
    invalid_observation = json.loads(
        backend.requests[-1].messages[-1]["content"][0]["content"]
    )
    assert invalid_observation["error"] == "client_tool_input_rejected"
    assert "array of nonempty text" in invalid_observation["detail"]
    assert result.evidence["changed_artifact_names"] == []
    assert result.evidence["changed_document_paths"] == [report_path]
    assert result.evidence["model_owned_theory"] is False
    assert result.evidence["model_owned_source_report"] is True
    assert result.evidence["source_replication_manifests"] == [manifest]
    assert SOURCE_REPLICATION_WORKSPACE_COMMIT_TOOL in {
        tool.name for tool in backend.requests[0].tools
    }


def test_same_model_revises_workspace_after_raw_validator_observation() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-parent",
                    name="read_theory_workspace",
                    input={
                        "artifact_names": ["problem_card", "lemma_cards"]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-incomplete",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": {"claim": "revised claim"}}
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-complete",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"lemma_cards": [{"id": "lemma-1"}]}
                    ),
                )
            ),
            _response(
                _commit_checkpoint(
                    rationale=(
                        "The revised claim and its dependency lemma are now coherent; "
                        "submit them to independent review."
                    )
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"] == {
        "problem_card": {"claim": "revised claim"},
        "lemma_cards": [{"id": "lemma-1"}],
    }
    assert result.evidence["changed_artifact_names"] == [
        "lemma_cards",
        "problem_card",
    ]
    assert result.evidence["reads"] == 1
    assert result.evidence["submissions"] == 2
    assert result.evidence["authoring_binding_id"] == (
        "authoring-binding:q1"
    )
    assert result.evidence["workspace_operation"] == "test_authoring"
    assert result.evidence["model_owned_theory"] is True
    assert result.evidence["runtime_edited_theory"] is False
    assert result.evidence["checkpoint_committed"] is True
    assert "dependency lemma" in result.evidence[
        "checkpoint_readiness_rationale"
    ]
    assert all(request.enable_prompt_caching for request in backend.requests)
    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert "parent-private-claim" not in initial_prompt
    assert "parent-private-claim" in str(backend.requests[1].messages)
    assert "revised claim and at least one lemma are required" in str(
        backend.requests[2].messages
    )
    incomplete_write_block = backend.requests[2].messages[-1]["content"][0]
    incomplete_write_observation = json.loads(
        incomplete_write_block["content"]
    )
    assert incomplete_write_observation["write_accepted"] is True
    assert incomplete_write_observation["workspace_valid"] is False
    assert incomplete_write_observation["omitted_artifacts_retained"] is True
    assert incomplete_write_block["is_error"] is False
    write_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_TOOL
    )
    writes_schema = write_schema["properties"]["writes"]
    item_schema = writes_schema["items"]
    assert write_schema["required"] == ["writes"]
    assert writes_schema["minItems"] == 1
    assert item_schema["required"] == ["artifact_name", "value"]
    assert item_schema["properties"]["artifact_name"] == {
        "type": "string",
        "minLength": 1,
    }
    assert item_schema["properties"]["value"]["anyOf"] == [
        {"type": "object"},
        {"type": "array"},
    ]
    write_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_TOOL
    )
    assert write_tool.strict is False


def test_structurally_valid_write_does_not_end_model_owned_theory_work() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="write-first-valid-candidate",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "initial-lemma"}],
                        }
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="refine-valid-candidate",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"lemma_cards": [{"id": "dependency-audited-lemma"}]}
                    ),
                )
            ),
            _response(
                _commit_checkpoint(
                    rationale=(
                        "The dependency audit changed the lemma and the revised "
                        "candidate is ready for independent review."
                    )
                )
            ),
        ]
    )

    result = _run_workspace(backend)

    first_valid_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert first_valid_observation["workspace_valid"] is True
    assert first_valid_observation["checkpoint_committed"] is False
    assert result.core_packet["artifacts"]["lemma_cards"] == [
        {"id": "dependency-audited-lemma"}
    ]
    assert result.evidence["submissions"] == 2
    assert result.evidence["checkpoint_committed"] is True


def test_workspace_exhaustion_preserves_model_owned_checkpoint() -> None:
    rejected_call = ClientToolCall(
        call_id="edit-rejected",
        name=THEORY_WORKSPACE_WRITE_TOOL,
        input=_artifact_writes(
            {"problem_card": {"claim": "still invalid"}}
        ),
    )
    backend = ScriptedTheoryWorkspaceBackend(
        [_response(rejected_call), _response(), _response()]
    )

    with pytest.raises(PacketValidationError) as exc_info:
        _run_workspace(
            backend,
            max_turns=1,
            max_tool_calls=1,
            max_no_progress_turns=1,
        )

    checkpoint = exc_info.value.recovery_checkpoint
    assert checkpoint["artifact_kind"] == THEORY_WORKSPACE_CHECKPOINT_KIND
    assert checkpoint["authoring_binding_id"] == "authoring-binding:q1"
    assert checkpoint["workspace_operation"] == "test_authoring"
    assert checkpoint["current_artifacts"]["problem_card"] == {
        "claim": "still invalid"
    }
    assert checkpoint["changed_artifact_names"] == ["problem_card"]
    assert checkpoint["last_validation_errors"] == [
        "revised claim and at least one lemma are required"
    ]
    assert checkpoint["model_owned_theory"] is True
    assert checkpoint["runtime_edited_theory"] is False
    assert checkpoint["kernel_verified"] is False
    assert len(backend.requests) == 3
    assert backend.requests[-1].metadata[
        "client_tool_loop_terminal_decision_turn"
    ] is True
    assert backend.requests[-1].metadata[
        "client_tool_loop_max_terminal_recovery_turns"
    ] == 1


def test_workspace_uses_one_shared_read_write_tool_budget() -> None:
    read_calls = [
        ClientToolCall(
            call_id=f"read-context-{index}",
            name="read_theory_workspace",
            input={"artifact_names": [f"context_{index}"]},
        )
        for index in range(1, 6)
    ]
    write_calls = [
        ClientToolCall(
            call_id=f"write-draft-{index}",
            name=THEORY_WORKSPACE_WRITE_TOOL,
            input=_artifact_writes(
                {
                    "problem_card": {"claim": f"draft claim {index}"},
                    **(
                        {"lemma_cards": [{"id": "final-lemma"}]}
                        if index == 6
                        else {}
                    ),
                }
            ),
        )
        for index in range(1, 7)
    ]
    backend = ScriptedTheoryWorkspaceBackend(
        [
            *[_response(call) for call in read_calls],
            *[_response(call) for call in write_calls],
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        max_turns=11,
        max_tool_calls=11,
        read_only_artifacts={
            f"context_{index}": {"value": index} for index in range(1, 6)
        },
        validate_candidate=lambda packet: (
            []
            if packet.get("artifacts", {}).get("problem_card", {}).get("claim")
            == "draft claim 6"
            and packet.get("artifacts", {}).get("lemma_cards")
            == [{"id": "final-lemma"}]
            else ["final draft and lemma are required"]
        ),
    )

    assert result.evidence["reads"] == 5
    assert result.evidence["submissions"] == 6
    assert result.evidence["tool_calls"] == 12
    assert result.evidence["runtime_executed_tool_calls"] == 12
    assert result.evidence["checkpoint_committed"] is True
    final_write_observation = json.loads(
        backend.requests[-1].messages[-3]["content"][0]["content"]
    )
    assert "remaining_reads" not in final_write_observation
    assert "remaining_submissions" not in final_write_observation


def test_model_can_stop_with_an_explicit_unresolved_theory_gap() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-blocked-claim",
                    name="read_theory_workspace",
                    input={"artifact_names": ["problem_card"]},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="report-gap",
                    name=THEORY_WORKSPACE_GAP_TOOL,
                    input={
                        "summary": (
                            "The supplied assumptions do not identify the requested "
                            "estimand."
                        ),
                        "blocking_claims": ["requested identification claim"],
                        "evidence_refs": ["workspace:problem_card"],
                        "next_step": "Request an additional identifying assumption.",
                    },
                )
            ),
        ]
    )

    with pytest.raises(TheoryWorkspaceGapError) as exc_info:
        _run_workspace(backend)

    gap = exc_info.value.theory_gap
    evidence = exc_info.value.evidence
    assert gap["blocking_claims"] == ["requested identification claim"]
    assert gap["evidence_refs"] == ["workspace:problem_card"]
    assert evidence["disposition"] == "THEORY_GAP"
    assert evidence["accepted"] is False
    assert evidence["model_owned_theory"] is True
    assert evidence["runtime_edited_theory"] is False
    assert evidence["kernel_verified"] is False
    assert evidence["proof_evidence_status"] == (
        "MODEL_REPORTED_THEORY_GAP_NOT_PROOF_EVIDENCE"
    )
    assert [tool.name for tool in backend.requests[0].tools] == [
        "read_theory_workspace",
        THEORY_WORKSPACE_WRITE_TOOL,
        THEORY_WORKSPACE_COMMIT_TOOL,
        THEORY_WORKSPACE_GAP_TOOL,
    ]


def test_model_can_checkpoint_document_backed_theory_progress(tmp_path) -> None:
    markdown = (
        "# Partial derivation\n\n"
        "The model has established one intermediate expansion, while the "
        "remainder bound is still open.\n"
    )
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="write-partial-theory",
                    name=THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                    input={"path": "derivations/progress.md", "content": markdown},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-partial-index",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": {"claim": "partial revised claim"}}
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="checkpoint-progress",
                    name=THEORY_WORKSPACE_PROGRESS_TOOL,
                    input={
                        "summary": "Established the first expansion.",
                        "evidence_refs": ["derivations/progress.md#partial-derivation"],
                        "next_step": "Derive and stress-test the remainder bound.",
                    },
                )
            ),
        ]
    )

    with pytest.raises(TheoryWorkspaceProgressError) as exc_info:
        _run_workspace(
            backend,
            workspace_dir=tmp_path / "theory",
            require_document_authority=True,
        )

    checkpoint = exc_info.value.progress_checkpoint
    evidence = exc_info.value.evidence
    assert checkpoint["artifact_kind"] == (
        THEORY_WORKSPACE_PROGRESS_CHECKPOINT_KIND
    )
    assert checkpoint["accepted"] is False
    assert checkpoint["resumable"] is True
    assert checkpoint["changed_artifact_names"] == ["problem_card"]
    assert checkpoint["changed_document_paths"] == [
        "derivations/progress.md"
    ]
    checkpoint_manifest = checkpoint["theory_workspace_manifest"]
    assert ".immutable_checkpoints" in Path(
        checkpoint_manifest["workspace_root"]
    ).parts
    session_ref = checkpoint["client_tool_session_ref"]
    assert session_ref["artifact_kind"] == "ClientToolWorkspaceSessionRef"
    artifacts, documents = load_theory_progress_checkpoint_state(
        checkpoint,
        question_id="q1",
    )
    assert artifacts["problem_card"] == {"claim": "partial revised claim"}
    assert documents == {"derivations/progress.md": markdown}
    assert evidence["disposition"] == "THEORY_PROGRESS_CHECKPOINT"
    assert evidence["accepted"] is False
    assert evidence["kernel_verified"] is False
    assert evidence["proof_evidence_status"] == (
        "THEORY_PROGRESS_CHECKPOINT_NOT_PROOF_EVIDENCE"
    )
    assert THEORY_WORKSPACE_PROGRESS_TOOL in {
        tool.name for tool in backend.requests[0].tools
    }
    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert "an unfinished structured handoff or exhausted write quota is not" in (
        initial_prompt
    )
    assert "use checkpoint_theory_progress for same-owner continuation" in (
        initial_prompt
    )
    final_write_observation = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert "remaining_submissions" not in final_write_observation

    continuation = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-checkpoint-document",
                    name=THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                    input={
                        "path": "derivations/progress.md",
                        "line_start": 1,
                        "line_end": 3,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="finish-theory-index",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "remainder-bound"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint("commit-continued-theory")),
        ]
    )
    result = _run_workspace(
        continuation,
        workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        initial_artifacts=artifacts,
        initial_documents=documents,
        prior_changed_artifact_names=checkpoint["changed_artifact_names"],
        prior_changed_document_paths=checkpoint["changed_document_paths"],
        prior_client_tool_session_ref=session_ref,
    )

    assert result.evidence["client_tool_session_lineage_continued"] is True
    assert result.evidence["resumed_from_client_tool_session_ref"] == session_ref
    window = result.evidence["client_tool_checkpoint_window"]
    assert window["policy"] == CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY
    assert window["parent_message_count"] == session_ref["message_count"]
    assert window["checkpoint_identity"] == stable_hash(
        {"artifacts": artifacts, "documents": documents}
    )
    assert window["prior_transcript_replayed"] is True
    assert result.evidence["transcript_policy"] == CLIENT_TOOL_TRANSCRIPT_POLICY
    continued_messages = continuation.requests[0].messages
    assert len(continued_messages) >= 3
    assert continued_messages[0]["role"] == "user"
    assert "Revise the theory from independent observations" in str(
        continued_messages
    )
    assert "checkpoint-progress" in str(continued_messages)
    assert "derivations/progress.md" in str(continued_messages)
    assert "remainder bound is still open" in str(
        continuation.requests[1].messages[-1]
    )

    document_path = tmp_path / "theory" / "derivations" / "progress.md"
    document_path.write_text(markdown + "tampered\n", encoding="utf-8")
    _, checkpoint_documents = load_theory_progress_checkpoint_state(
        checkpoint,
        question_id="q1",
    )
    assert checkpoint_documents == {"derivations/progress.md": markdown}
    snapshot_path = Path(
        checkpoint["theory_workspace_manifest"]["documents"][0]["path"]
    )
    snapshot_path.write_text(markdown + "tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="document hash mismatch"):
        load_theory_progress_checkpoint_state(
            checkpoint,
            question_id="q1",
        )


def test_rejected_terminal_commit_can_checkpoint_same_owner_progress(tmp_path) -> None:
    markdown = (
        "# Partial theory\n\n"
        "The authoritative derivation exists, but its compact dependency index "
        "still needs one lemma reference.\n"
    )
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="write-partial-document",
                    name=THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                    input={"path": "derivations/partial.md", "content": markdown},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-invalid-index",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": {"claim": "partial revised claim"}}
                    ),
                )
            ),
            _response(_commit_checkpoint("commit-invalid-index")),
            _response(
                ClientToolCall(
                    call_id="checkpoint-after-commit-error",
                    name=THEORY_WORKSPACE_PROGRESS_TOOL,
                    input={
                        "summary": "The derivation is written but the index is invalid.",
                        "evidence_refs": ["derivations/partial.md#partial-theory"],
                        "next_step": "Add the missing lemma reference and revalidate.",
                    },
                )
            ),
        ]
    )

    with pytest.raises(TheoryWorkspaceProgressError) as exc_info:
        _run_workspace(
            backend,
            workspace_dir=tmp_path / "theory",
            require_document_authority=True,
            max_turns=2,
            max_tool_calls=2,
        )

    assert len(backend.requests) == 4
    rejected_commit_request = backend.requests[2]
    recovery_request = backend.requests[3]
    assert rejected_commit_request.metadata[
        "client_tool_loop_terminal_decision_turn"
    ] is True
    assert recovery_request.metadata[
        "client_tool_loop_terminal_decision_turn"
    ] is True
    assert recovery_request.metadata[
        "client_tool_loop_max_terminal_recovery_turns"
    ] == 1
    assert "theory checkpoint is not structurally valid" in str(
        recovery_request.messages[-1]
    )
    assert "revised claim and at least one lemma are required" in str(
        recovery_request.messages[-1]
    )
    checkpoint = exc_info.value.progress_checkpoint
    assert checkpoint["resumable"] is True
    assert checkpoint["current_artifacts"]["problem_card"] == {
        "claim": "partial revised claim"
    }
    assert checkpoint["last_validation_errors"] == [
        "revised claim and at least one lemma are required"
    ]
    assert checkpoint["progress"]["next_step"] == (
        "Add the missing lemma reference and revalidate."
    )


def test_targeted_revision_uses_atomic_model_owned_artifact_writes() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-revision-inputs",
                    name="read_theory_workspace",
                    input={
                        "artifact_names": ["problem_card", "lemma_cards"]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-related-values",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"] == {
        "problem_card": {"claim": "revised claim"},
        "lemma_cards": [{"id": "lemma-1"}],
    }
    assert result.evidence["write_transport"] == (
        THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
    )
    assert result.evidence["n_model_artifact_writes"] == 2
    assert result.evidence["model_artifact_writes"] == [
        {
            "submission_index": 0,
            "artifact_name": "problem_card",
            "value_hash": stable_hash({"claim": "revised claim"}),
        },
        {
            "submission_index": 0,
            "artifact_name": "lemma_cards",
            "value_hash": stable_hash([{"id": "lemma-1"}]),
        },
    ]
    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert tool_names == [
        "read_theory_workspace",
        THEORY_WORKSPACE_WRITE_TOOL,
        THEORY_WORKSPACE_COMMIT_TOOL,
        THEORY_WORKSPACE_GAP_TOOL,
    ]
    prompt = str(backend.requests[0].messages[0]["content"])
    assert "Markdown/LaTeX documents" in prompt
    assert "compatibility workspace" in prompt
    assert "without merging or inventing content" in prompt
    write_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_TOOL
    )
    assert "runtime never merges or infers content" in write_tool.description


def test_same_theory_model_runs_exact_scratch_source_then_revises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'counterexample_gap': 0.25, 'seed': seed}\n"
    )
    captured: dict[str, object] = {}

    def fake_execute_scientific_sandbox(**kwargs):
        captured.update(kwargs)
        return ScientificSandboxExecution(
            status="EXECUTED",
            language="python",
            execution_profile="scientific_wasm",
            backend="pyodide",
            isolation_provider="test-isolation",
            dependencies=("numpy",),
            execution_attempted=True,
            returncode=0,
            metrics={"counterexample_gap": 0.25, "seed": 17},
            errors=(),
            stdout_summary="exact scratch stdout",
            stderr_summary="",
            result_parse_error="",
            code_path=str(tmp_path / "scratch.py"),
            request_path=str(tmp_path / "request.json"),
            result_path=str(tmp_path / "result.json"),
            code_hash=stable_hash(source),
            request_hash="scratch-request-hash",
            result_hash=stable_hash(
                {"counterexample_gap": 0.25, "seed": 17}
            ),
            subprocess_environment_keys=("HOME", "PATH"),
            resource_limits={"cpu_seconds": 9},
        )

    monkeypatch.setattr(
        "ai_statistician.theory_workspace.execute_scientific_sandbox",
        fake_execute_scientific_sandbox,
    )
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="run-counterexample",
                    name=THEORY_SCRATCHPAD_TOOL,
                    input={
                        "language": "python",
                        "execution_profile": "scientific_wasm",
                        "dependencies": ["numpy"],
                        "entrypoint": "run_sandbox",
                        "code": source,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="revise-from-counterexample",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [
                                {"id": "counterexample-qualified-lemma"}
                            ],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        scratchpad=TheoryScratchpadConfig(
            sandbox_dir=tmp_path / "theory-scratch",
            seed=17,
            replicates=12,
            timeout_s=9,
            max_runs=1,
        ),
    )

    assert captured["code"] == source
    assert captured["language"] == "python"
    assert captured["dependencies"] == ["numpy"]
    assert captured["seed"] == 17
    assert captured["replicates"] == 12
    assert captured["timeout_s"] == 9
    assert captured["max_output_bytes"] == 64 * 1024
    assert result.core_packet["artifacts"]["problem_card"]["claim"] == (
        "revised claim"
    )
    assert result.evidence["scratchpad_enabled"] is True
    assert result.evidence["scratch_runs"] == 1
    scratch = result.evidence["scratch_execution_refs"][0]
    assert scratch["metrics_hash"] == stable_hash(
        {"counterexample_gap": 0.25, "seed": 17}
    )
    assert scratch["code_hash"] == stable_hash(source)
    assert scratch["runtime_edited_source"] is False
    assert scratch["runtime_edited_theory"] is False
    assert scratch["proof_evidence_status"] == (
        THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE
    )
    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert tool_names == [
        "read_theory_workspace",
        THEORY_SCRATCHPAD_TOOL,
        THEORY_WORKSPACE_WRITE_TOOL,
        THEORY_WORKSPACE_COMMIT_TOOL,
        THEORY_WORKSPACE_GAP_TOOL,
    ]
    first_prompt = str(backend.requests[0].messages[0]["content"])
    assert "rather than a prewritten conclusion" in first_prompt
    assert "revise, retract, or mark the claim uncertain" in first_prompt
    assert "exact model-chosen SymPy reduction" in first_prompt
    scratch_tool = next(
        tool for tool in backend.requests[0].tools if tool.name == THEORY_SCRATCHPAD_TOOL
    )
    assert "not a prewritten verdict" in scratch_tool.description
    observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert observation["status"] == "EXECUTED"
    assert observation["metrics"]["counterexample_gap"] == 0.25
    assert observation["proof_evidence_status"] == (
        THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE
    )
    assert "not confirmatory simulation" in observation["boundary"]


def test_targeted_revision_retains_valid_edits_across_raw_validator_feedback() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="edit-incomplete",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": {"claim": "revised claim"}}
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-after-observation",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"lemma_cards": [{"id": "lemma-1"}]}
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(backend)

    assert result.evidence["submissions"] == 2
    assert result.evidence["n_model_artifact_writes"] == 2
    assert [
        row["submission_index"]
        for row in result.evidence["model_artifact_writes"]
    ] == [0, 1]
    assert "revised claim and at least one lemma are required" in str(
        backend.requests[1].messages
    )
    observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert observation["write_accepted"] is True
    assert observation["workspace_valid"] is False
    assert observation["write_transport"] == (
        THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
    )


def test_targeted_revision_rejects_noop_edit_then_returns_observation() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="noop-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {
                                "claim": "parent-private-claim"
                            }
                        }
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="substantive-edit-after-noop",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(backend)

    assert result.evidence["submissions"] == 2
    assert result.evidence["n_model_artifact_writes"] == 2
    no_op_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert no_op_observation["state_changed"] is False
    assert no_op_observation["workspace_valid"] is False
    assert no_op_observation["validation_errors"] == [
        "the submitted theory workspace is unchanged from its parent"
    ]


def test_targeted_revision_rejects_invalid_artifact_shape_atomically() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="invalid-atomic-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": ["invalid object replacement"]}
                    ),
                )
            ),
            _response(
                ClientToolCall(
                    call_id="valid-atomic-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"]["problem_card"] == {
        "claim": "revised claim"
    }
    assert result.evidence["submissions"] == 1
    assert result.evidence["n_model_artifact_writes"] == 2
    rejected_observation = backend.requests[1].messages[-1]["content"][0]
    assert rejected_observation["is_error"] is True
    rejected_payload = json.loads(rejected_observation["content"])
    assert rejected_payload["error"] == "client_tool_input_rejected"
    assert "problem_card to remain object" in rejected_payload["detail"]


def test_targeted_revision_rejects_duplicate_artifact_names_atomically() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="duplicate-artifact-edit",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input={
                        "writes": [
                            {
                                "artifact_name": "problem_card",
                                "value": {"claim": "first revision"},
                            },
                            {
                                "artifact_name": "problem_card",
                                "value": {"claim": "second revision"},
                            },
                        ]
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="valid-edit-after-duplicate",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(backend)

    assert result.core_packet["artifacts"]["problem_card"] == {
        "claim": "revised claim"
    }
    assert result.evidence["submissions"] == 1
    rejected_observation = backend.requests[1].messages[-1]["content"][0]
    assert rejected_observation["is_error"] is True
    rejected_payload = json.loads(rejected_observation["content"])
    assert rejected_payload["error"] == "client_tool_input_rejected"
    assert "repeats 'problem_card'" in rejected_payload["detail"]


def test_theory_workspace_accepts_one_coherent_complete_write_batch() -> None:
    tools = _theory_workspace_tools(
        scratchpad_enabled=False,
    )
    write_tool = next(tool for tool in tools if tool.name == THEORY_WORKSPACE_WRITE_TOOL)

    writes_schema = write_tool.input_schema["properties"]["writes"]
    assert "maxItems" not in writes_schema
    assert writes_schema["items"]["properties"]["artifact_name"] == {
        "type": "string",
        "minLength": 1,
    }

    artifacts, writes = _replace_theory_workspace_artifacts(
        {
            "problem_card": {},
            "lemma_cards": [],
            "theorem_cards": [],
        },
        [
            {"artifact_name": "problem_card", "value": {"claim": "x"}},
            {"artifact_name": "lemma_cards", "value": [{"id": "l"}]},
            {"artifact_name": "theorem_cards", "value": [{"id": "t"}]},
        ],
        writable_artifact_shapes={
            "problem_card": "object",
            "lemma_cards": "array",
            "theorem_cards": "array",
        },
    )

    assert artifacts == {
        "problem_card": {"claim": "x"},
        "lemma_cards": [{"id": "l"}],
        "theorem_cards": [{"id": "t"}],
    }
    assert [row["artifact_name"] for row in writes] == [
        "problem_card",
        "lemma_cards",
        "theorem_cards",
    ]
    with pytest.raises(ClientToolInputError, match="unknown writable artifact"):
        _replace_theory_workspace_artifacts(
            artifacts,
            [{"artifact_name": "unbound_artifact", "value": {}}],
            writable_artifact_shapes={"problem_card": "object"},
        )


def test_document_authority_persists_exact_math_and_small_handoff(
    tmp_path,
) -> None:
    markdown = "# Claim C1\n\nFor all n, $a_n = b_n$.\n"
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="reject-legacy-combined-write",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input={
                        "writes": [],
                        "document_writes": [
                            {
                                "path": "derivations/C1.md",
                                "content": markdown,
                            }
                        ],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-authoritative-document",
                    name=THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                    input={
                        "path": "derivations/C1.md",
                        "content": markdown,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-document-index",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "C1"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        max_turns=4,
        build_candidate=lambda artifacts, changed, manifest, changed_documents: {
            "artifacts": dict(artifacts),
            "changed": list(changed),
            "theory_workspace_manifest": dict(manifest),
            "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
            "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
            "changed_documents": list(changed_documents),
        },
    )

    assert backend.requests[0].disable_parallel_tool_use is False
    assert (tmp_path / "theory" / "derivations" / "C1.md").read_text() == markdown
    assert result.evidence["changed_document_paths"] == ["derivations/C1.md"]
    assert result.evidence["n_model_document_writes"] == 1
    assert result.evidence["schema_version"] == 2
    assert result.evidence["document_inspection_refs"] == []
    assert "final_document_inspection_refs" not in result.evidence
    rejected_observation = backend.requests[1].messages[-1]["content"][0]
    assert rejected_observation["is_error"] is True
    rejected_payload = json.loads(rejected_observation["content"])
    assert rejected_payload["error"] == "client_tool_input_rejected"
    assert "accepts only structured writes" in rejected_payload["detail"]
    assert "use write_theory_document" in rejected_payload["detail"]
    valid_write_feedback = json.loads(
        backend.requests[3].messages[-1]["content"][0]["content"]
    )
    assert valid_write_feedback["workspace_valid"] is True
    assert valid_write_feedback["checkpoint_commit_ready"] is True
    assert valid_write_feedback["checkpoint_blockers"] == []
    write_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_TOOL
    )
    document_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL
    )
    assert not {"oneOf", "allOf", "anyOf"}.intersection(write_schema)
    assert write_schema["required"] == ["writes"]
    assert "document_writes" not in write_schema["properties"]
    assert document_tool.strict is True
    assert document_tool.input_schema["required"] == ["path", "content"]
    assert theory_workspace_manifest_errors(result.core_packet, required=True) == []
    manifest = result.core_packet["theory_workspace_manifest"]
    assert ".immutable_checkpoints" in Path(manifest["workspace_root"]).parts
    assert load_theory_workspace_documents(result.core_packet) == {
        "derivations/C1.md": markdown
    }
    (tmp_path / "theory" / "derivations" / "C1.md").write_text(
        markdown + "mutable revision\n",
        encoding="utf-8",
    )
    assert load_theory_workspace_documents(result.core_packet) == {
        "derivations/C1.md": markdown
    }
    outside = tmp_path / "outside.md"
    outside.write_text(markdown, encoding="utf-8")
    tampered = json.loads(json.dumps(result.core_packet))
    tampered["theory_workspace_manifest"]["documents"][0]["path"] = str(
        outside
    )
    with pytest.raises(ValueError, match="document path mismatch"):
        load_theory_workspace_documents(tampered)


def test_theory_workspace_reserves_terminal_call_after_last_valid_write() -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-problem-card",
                    name="read_theory_workspace",
                    input={"artifact_names": ["problem_card"]},
                ),
                ClientToolCall(
                    call_id="read-lemma-cards",
                    name="read_theory_workspace",
                    input={"artifact_names": ["lemma_cards"]},
                ),
            ),
            _response(
                ClientToolCall(
                    call_id="write-valid-final-workspace",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "L1"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        max_turns=3,
        max_tool_calls=3,
    )

    valid_write_feedback = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert valid_write_feedback["workspace_valid"] is True
    assert valid_write_feedback["checkpoint_commit_ready"] is True
    assert "_client_tool_budget" not in valid_write_feedback
    assert result.evidence["checkpoint_committed"] is True
    assert result.evidence["turns"] == 3
    assert result.evidence["tool_calls"] == 4
    assert result.evidence["runtime_executed_tool_calls"] == 4


def test_document_authority_supports_local_edit_without_forced_reread(
    tmp_path,
) -> None:
    parent = "# Claim C1\n\nFor all n, $a_n = b_n$.\n"
    revised = "# Claim C1\n\nFor every admitted n, $a_n = b_n$.\n"
    parent_sha256 = hashlib.sha256(parent.encode("utf-8")).hexdigest()
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-current-document",
                    name="read_theory_workspace",
                    input={"document_paths": ["derivations/C1.md"]},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-current-document",
                    name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                    input={
                        "path": "derivations/C1.md",
                        "expected_sha256": parent_sha256,
                        "edits": [
                            {
                                "old_text": "For all n, $a_n = b_n$.",
                                "new_text": (
                                    "For every admitted n, $a_n = b_n$."
                                ),
                            }
                        ],
                    },
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        initial_artifacts={
            "problem_card": {"claim": "revised claim"},
            "lemma_cards": [{"id": "C1"}],
        },
        initial_documents={"derivations/C1.md": parent},
        max_turns=3,
        build_candidate=lambda artifacts, changed, manifest, changed_documents: {
            "artifacts": dict(artifacts),
            "changed": list(changed),
            "theory_workspace_manifest": dict(manifest),
            "changed_documents": list(changed_documents),
        },
    )

    assert load_theory_workspace_documents(result.core_packet) == {
        "derivations/C1.md": revised
    }
    edit_feedback = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert edit_feedback["checkpoint_commit_ready"] is True
    assert edit_feedback["checkpoint_blockers"] == []
    assert result.evidence["changed_artifact_names"] == []
    assert result.evidence["changed_document_paths"] == ["derivations/C1.md"]
    assert len(backend.requests) == 3
    assert [
        row["document_sha256"]
        for row in result.evidence["document_inspection_refs"]
        if row["tool"] == "read_theory_workspace"
    ] == [parent_sha256]
    assert result.evidence["model_document_writes"] == [
        {
            "submission_index": 0,
            "operation": "atomic_exact_text_replacement_batch",
            "relative_path": "derivations/C1.md",
            "parent_sha256": parent_sha256,
            "edit_count": 1,
            "edits": [
                {
                    "old_text_sha256": hashlib.sha256(
                        b"For all n, $a_n = b_n$."
                    ).hexdigest(),
                    "new_text_sha256": hashlib.sha256(
                        b"For every admitted n, $a_n = b_n$."
                    ).hexdigest(),
                }
            ],
            "sha256": hashlib.sha256(revised.encode("utf-8")).hexdigest(),
            "byte_size": len(revised.encode("utf-8")),
        }
    ]
    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL in tool_names
    prompt = str(backend.requests[0].messages[0]["content"])
    assert "current document SHA-256" in prompt
    assert "ordered batch" in prompt


def test_same_owner_continuation_can_commit_without_forced_document_reread(
    tmp_path,
) -> None:
    document = "# Claim C1\n\nFor every admitted n, $a_n = b_n$.\n"
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="revise-continuation-handoff",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {"problem_card": {"claim": "revised claim"}}
                    ),
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        initial_artifacts={
            "problem_card": {"claim": "parent-private-claim"},
            "lemma_cards": [{"id": "C1"}],
        },
        initial_documents={"derivations/C1.md": document},
        prior_changed_document_paths=["derivations/C1.md"],
        max_turns=2,
    )

    assert len(backend.requests) == 2
    assert result.evidence["reads"] == 0
    assert result.evidence["changed_document_paths"] == ["derivations/C1.md"]


def test_model_chosen_partial_reread_is_evidence_not_checkpoint_authority(
    tmp_path,
) -> None:
    parent = "# Claim C1\n\nFor all n, $a_n = b_n$.\n"
    revised = "# Claim C1\n\nFor every admitted n, $a_n = b_n$.\n"
    parent_sha256 = hashlib.sha256(parent.encode("utf-8")).hexdigest()
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-parent-document",
                    name="read_theory_workspace",
                    input={"document_paths": ["derivations/C1.md"]},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-parent-document",
                    name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                    input={
                        "path": "derivations/C1.md",
                        "expected_sha256": parent_sha256,
                        "edits": [
                            {
                                "old_text": "For all n, $a_n = b_n$.",
                                "new_text": (
                                    "For every admitted n, $a_n = b_n$."
                                ),
                            }
                        ],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="read-only-final-heading",
                    name=THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                    input={
                        "path": "derivations/C1.md",
                        "line_start": 1,
                        "line_end": 1,
                    },
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        initial_artifacts={
            "problem_card": {"claim": "revised claim"},
            "lemma_cards": [{"id": "C1"}],
        },
        initial_documents={"derivations/C1.md": parent},
        max_turns=4,
    )

    assert result.evidence["checkpoint_committed"] is True
    partial_reads = [
        row
        for row in result.evidence["document_inspection_refs"]
        if row["tool"] == THEORY_WORKSPACE_READ_DOCUMENT_TOOL
    ]
    assert [(row["line_start"], row["line_end"]) for row in partial_reads] == [
        (1, 1)
    ]
    assert "final_document_inspection_requirements" not in result.evidence
    assert revised == (tmp_path / "theory" / "derivations" / "C1.md").read_text()


def test_long_theory_document_supports_search_range_read_and_local_edit(
    tmp_path,
) -> None:
    lines = ["# Long theory workspace", ""] + [
        f"Background claim {index}: $a_{{{index}}}=b_{{{index}}}$."
        for index in range(1, 4001)
    ]
    old_text = "For every n, the claimed limit follows without premise P."
    new_text = "For every n satisfying premise P, the claimed limit follows."
    lines[3000:3000] = ["## claim-C-long", old_text, "Depends on claim-C0."]
    parent = "\n".join(lines) + "\n"
    target_line = lines.index("## claim-C-long") + 1
    assert len(parent) > 55_000
    parent_sha256 = hashlib.sha256(parent.encode("utf-8")).hexdigest()
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="search-long-document",
                    name=THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
                    input={
                        "query": "claim-C-long",
                        "document_paths": ["theory/workspace.md"],
                        "max_results": 2,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="read-long-document-range",
                    name=THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                    input={
                        "path": "theory/workspace.md",
                        "line_start": target_line,
                        "line_end": target_line + 2,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-long-document",
                    name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                    input={
                        "path": "theory/workspace.md",
                        "expected_sha256": parent_sha256,
                        "edits": [
                            {"old_text": old_text, "new_text": new_text}
                        ],
                    },
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        initial_artifacts={
            "problem_card": {"claim": "revised claim"},
            "lemma_cards": [{"id": "claim-C-long"}],
        },
        initial_documents={"theory/workspace.md": parent},
        build_candidate=lambda artifacts, changed, manifest, changed_documents: {
            "artifacts": dict(artifacts),
            "changed": list(changed),
            "theory_workspace_manifest": dict(manifest),
            "changed_documents": list(changed_documents),
        },
        max_turns=4,
        max_tool_calls=3,
    )

    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert old_text not in initial_prompt
    assert THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL in initial_prompt
    assert THEORY_WORKSPACE_READ_DOCUMENT_TOOL in initial_prompt
    search_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert search_observation["total_matches"] == 1
    assert search_observation["hits"][0]["line_number"] == target_line
    assert search_observation["document_hashes"] == {
        "theory/workspace.md": parent_sha256
    }
    range_observation = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert range_observation["content"] == "\n".join(
        ["## claim-C-long", old_text, "Depends on claim-C0."]
    )
    assert range_observation["document_sha256"] == parent_sha256
    assert [
        row["tool"] for row in result.evidence["document_inspection_refs"]
    ] == [
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    ]
    assert len(backend.requests) == 4
    assert old_text not in json.dumps(result.evidence)
    assert new_text not in json.dumps(result.evidence)
    documents = load_theory_workspace_documents(result.core_packet)
    assert old_text not in documents["theory/workspace.md"]
    assert new_text in documents["theory/workspace.md"]
    schemas = {
        tool.name: tool.input_schema for tool in backend.requests[0].tools
    }
    assert not {"oneOf", "allOf", "anyOf"}.intersection(
        schemas[THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL]
    )
    assert not {"oneOf", "allOf", "anyOf"}.intersection(
        schemas[THEORY_WORKSPACE_READ_DOCUMENT_TOOL]
    )


def test_local_theory_document_edit_rejects_stale_or_ambiguous_source(
    tmp_path,
) -> None:
    parent = "# Claims\n\nRepeated premise.\n\nRepeated premise.\n"
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-ambiguous-document",
                    name="read_theory_workspace",
                    input={"document_paths": ["workspace.md"]},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="stale-edit",
                    name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                    input={
                        "path": "workspace.md",
                        "expected_sha256": "0" * 64,
                        "edits": [
                            {
                                "old_text": "Repeated premise.",
                                "new_text": "Revised premise.",
                            }
                        ],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="ambiguous-edit",
                    name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                    input={
                        "path": "workspace.md",
                        "expected_sha256": hashlib.sha256(
                            parent.encode("utf-8")
                        ).hexdigest(),
                        "edits": [
                            {
                                "old_text": "Repeated premise.",
                                "new_text": "Revised premise.",
                            }
                        ],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="report-edit-gap",
                    name=THEORY_WORKSPACE_GAP_TOOL,
                    input={
                        "summary": "The requested local edit is not uniquely anchored.",
                        "blocking_claims": ["repeated-premise"],
                        "evidence_refs": ["stale-edit", "ambiguous-edit"],
                        "next_step": "Read and select a unique surrounding span.",
                    },
                )
            ),
        ]
    )

    with pytest.raises(TheoryWorkspaceGapError):
        _run_workspace(
            backend,
            workspace_dir=tmp_path / "theory",
            require_document_authority=True,
            initial_documents={"workspace.md": parent},
        )

    stale = json.loads(backend.requests[2].messages[-1]["content"][0]["content"])
    ambiguous = json.loads(
        backend.requests[3].messages[-1]["content"][0]["content"]
    )
    assert "changed since it was read" in stale["detail"]
    assert "observed 2 matches" in ambiguous["detail"]
    assert "edit index 0" in ambiguous["detail"]


def test_local_theory_document_edit_batch_is_atomic_and_ordered(tmp_path) -> None:
    parent = "# Claims\n\nFirst premise.\n\nSecond conclusion.\n"
    parent_sha256 = hashlib.sha256(parent.encode("utf-8")).hexdigest()
    revised = "# Claims\n\nRevised premise.\n\nRevised conclusion.\n"
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-batch-document",
                    name="read_theory_workspace",
                    input={"document_paths": ["workspace.md"]},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="reject-whole-batch",
                    name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                    input={
                        "path": "workspace.md",
                        "expected_sha256": parent_sha256,
                        "edits": [
                            {
                                "old_text": "First premise.",
                                "new_text": "Revised premise.",
                            },
                            {
                                "old_text": "Missing conclusion.",
                                "new_text": "Revised conclusion.",
                            },
                        ],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="apply-whole-batch",
                    name=THEORY_WORKSPACE_EDIT_DOCUMENT_TOOL,
                    input={
                        "path": "workspace.md",
                        "expected_sha256": parent_sha256,
                        "edits": [
                            {
                                "old_text": "First premise.",
                                "new_text": "Revised premise.",
                            },
                            {
                                "old_text": "Second conclusion.",
                                "new_text": "Revised conclusion.",
                            },
                        ],
                    },
                )
            ),
            _response(_commit_checkpoint()),
        ]
    )

    result = _run_workspace(
        backend,
        workspace_dir=tmp_path / "theory",
        require_document_authority=True,
        initial_artifacts={
            "problem_card": {"claim": "revised claim"},
            "lemma_cards": [{"id": "C1"}],
        },
        initial_documents={"workspace.md": parent},
        build_candidate=lambda artifacts, changed, manifest, changed_documents: {
            "artifacts": dict(artifacts),
            "changed": list(changed),
            "theory_workspace_manifest": dict(manifest),
            "changed_documents": list(changed_documents),
        },
        max_turns=4,
    )

    rejection = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert "observed 0 matches at edit index 1" in rejection["detail"]
    assert (tmp_path / "theory" / "workspace.md").read_text() == revised
    assert load_theory_workspace_documents(result.core_packet) == {
        "workspace.md": revised
    }
    assert result.evidence["model_document_writes"] == [
        {
            "submission_index": 0,
            "operation": "atomic_exact_text_replacement_batch",
            "relative_path": "workspace.md",
            "parent_sha256": parent_sha256,
            "edit_count": 2,
            "edits": [
                {
                    "old_text_sha256": hashlib.sha256(
                        b"First premise."
                    ).hexdigest(),
                    "new_text_sha256": hashlib.sha256(
                        b"Revised premise."
                    ).hexdigest(),
                },
                {
                    "old_text_sha256": hashlib.sha256(
                        b"Second conclusion."
                    ).hexdigest(),
                    "new_text_sha256": hashlib.sha256(
                        b"Revised conclusion."
                    ).hexdigest(),
                },
            ],
            "sha256": hashlib.sha256(revised.encode("utf-8")).hexdigest(),
            "byte_size": len(revised.encode("utf-8")),
        }
    ]


def test_document_authority_rejects_handoff_only_checkpoint(tmp_path) -> None:
    backend = ScriptedTheoryWorkspaceBackend(
        [
            _response(
                ClientToolCall(
                    call_id="write-index-only",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_artifact_writes(
                        {
                            "problem_card": {"claim": "revised claim"},
                            "lemma_cards": [{"id": "lemma-1"}],
                        }
                    ),
                )
            ),
            _response(_commit_checkpoint()),
            _response(
                ClientToolCall(
                    call_id="report-document-gap",
                    name=THEORY_WORKSPACE_GAP_TOOL,
                    input={
                        "summary": "The authoritative document was not revised.",
                        "blocking_claims": ["lemma-1"],
                        "evidence_refs": ["commit observation"],
                        "next_step": "Revise the mathematical document.",
                    },
                )
            ),
        ]
    )

    with pytest.raises(TheoryWorkspaceGapError):
        _run_workspace(
            backend,
            workspace_dir=tmp_path / "theory",
            require_document_authority=True,
            initial_documents={"workspace.md": "# Parent\n\nParent mathematics.\n"},
            build_candidate=lambda artifacts, changed, manifest, changed_documents: {
                "artifacts": dict(artifacts),
                "changed": list(changed),
                "theory_workspace_manifest": dict(manifest),
                "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
                "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
                "changed_documents": list(changed_documents),
            },
        )

    rejected = json.loads(backend.requests[2].messages[-1]["content"][0]["content"])
    assert "requires a changed authoritative" in rejected["detail"]
