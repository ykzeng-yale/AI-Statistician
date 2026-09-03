from __future__ import annotations

import hashlib
import json

import pytest

from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig
from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
    SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
    SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
    SCIENTIFIC_SOURCE_COMMIT_TOOL,
    SCIENTIFIC_SOURCE_EDIT_TOOL,
    SCIENTIFIC_SOURCE_READ_TOOL,
    SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
    SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER,
    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
    externalize_scientific_workspace_documents,
    load_scientific_code_workspace_checkpoint,
    run_scientific_code_workspace,
    run_source_owner_scientific_workspace,
    scientific_source_candidate_accepted,
    scientific_workspace_prototype_observation,
)
from ai_statistician.scientific_project import scientific_project_hash
from ai_statistician.scientific_sandbox import (
    discover_scientific_sandbox_runtime,
    execute_scientific_sandbox,
)
from ai_statistician.simulation_engineer_llm import SimulationEngineerConfig
from ai_statistician.research_source_library import (
    RESEARCH_SOURCE_LIST_TOOL,
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceDocument,
    ResearchSourceSnapshot,
    load_research_source_snapshot,
)
from ai_statistician.research_source_discovery import (
    RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
)
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
)


class ScriptedScientificBackend:
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


class FakeScientificDiscovery:
    provider_name = "fake_public_sources"

    def __init__(self, source_horizon: str = "2025-12-31") -> None:
        self.source_horizon = source_horizon
        self.searches: list[str] = []
        self.reads: list[str] = []

    def descriptor(self):
        return {
            "provider": self.provider_name,
            "source_horizon": self.source_horizon,
            "proof_evidence_status": "PUBLIC_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE",
        }

    def search(self, query, *, source_kind="all", top_k=5):
        self.searches.append(query)
        return {
            "ok": True,
            "provider": self.provider_name,
            "source_horizon": self.source_horizon,
            "query_hash": stable_hash(query),
            "source_kind": source_kind,
            "results": [{
                "source_handle": "source:published-implementation",
                "source_kind": "repository",
                "title": "Published implementation",
                "url": "https://github.com/example/published",
                "publication_date": "2025-01-02",
            }][:top_k],
        }

    def read(self, source_handle, **kwargs):
        self.reads.append(source_handle)
        path = str(kwargs.get("path", "method.py") or "method.py")
        content = {
            "method.py": "def published_method(x):\n    return sum(x) / len(x)\n",
            "adjust.py": "def adjust(x):\n    return x + 1\n",
        }.get(path, "# inspected repository file\n")
        return {
            "ok": True,
            "provider": self.provider_name,
            "source_handle": source_handle,
            "source_kind": "repository",
            "title": "Published implementation",
            "url": "https://github.com/example/published/blob/abc123/" + path,
            "publication_date": "2025-01-02",
            "revision": "abc123",
            "path": path,
            "content": content,
            "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "content_line_count": 2,
            "content_truncated": False,
            "line_start": 1,
            "line_end": 2,
            "content_range_sha256": "range-sha256",
            "citation_ref": "public:published-implementation:" + path + ":1-2",
        }


def test_model_imports_inspected_pinned_public_source_into_scientific_project() -> None:
    published_source = (
        "def published_method(x):\n"
        "    return sum(x) / len(x)\n"
    )
    published_sha256 = hashlib.sha256(published_source.encode()).hexdigest()
    adjustment_source = "def adjust(x):\n    return x + 1\n"
    adjustment_sha256 = hashlib.sha256(adjustment_source.encode()).hexdigest()
    main_source = (
        "from method import published_method\n\n"
        "from adjust import adjust\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return {'value': adjust(published_method([seed, replicates]))}\n"
    )
    backend = ScriptedScientificBackend([
        _response(ClientToolCall(
            call_id="discover", name=RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
            input={"query": "published implementation", "source_kind": "repository"},
        )),
        _response(ClientToolCall(
            call_id="submit-main", name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            input={
                "language": "python", "execution_profile": "stdlib",
                "dependencies": [], "entrypoint": "run_sandbox", "code": main_source,
            },
        )),
        _response(ClientToolCall(
            call_id="import-before-read",
            name=SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
            input={"imports": [{
                "source_origin": "discovered_repository",
                "source_id": "source:published-implementation",
                "revision": "abc123", "source_path": "method.py",
                "expected_content_sha256": published_sha256,
                "project_path": "method.py",
            }]},
        )),
        _response(
            ClientToolCall(
                call_id="read-method", name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                input={
                    "source_handle": "source:published-implementation",
                    "path": "method.py", "revision": "abc123",
                },
            ),
            ClientToolCall(
                call_id="read-adjust", name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                input={
                    "source_handle": "source:published-implementation",
                    "path": "adjust.py", "revision": "abc123",
                },
            ),
        ),
        _response(ClientToolCall(
            call_id="import-source",
            name=SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
            input={"imports": [
                {
                    "source_origin": "discovered_repository",
                    "source_id": "source:published-implementation",
                    "revision": "abc123", "source_path": "method.py",
                    "expected_content_sha256": published_sha256,
                    "project_path": "method.py",
                },
                {
                    "source_origin": "discovered_repository",
                    "source_id": "source:published-implementation",
                    "revision": "abc123", "source_path": "adjust.py",
                    "expected_content_sha256": adjustment_sha256,
                    "project_path": "adjust.py",
                },
            ]},
        )),
        _run_response(),
        _commit_response(),
    ])

    def check(candidate):
        rows = candidate.get("project_files", []) or []
        accepted = bool(
            candidate.get("code") == main_source
            and {row.get("path"): row.get("content") for row in rows} == {
                "adjust.py": adjustment_source,
                "method.py": published_source,
            }
        )
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": accepted,
            "stderr": "" if accepted else "public source import mismatch",
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Inspect and reuse the pinned public implementation.",
        user_prompt="Build and execute a source-grounded project.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=7,
        max_no_progress_turns=3,
        artifact_id="question:pinned-public-source-import",
        initial_code_draft=None,
        initial_check_result={"accepted": False},
        check_candidate=check,
        workspace_operation="initial_authoring",
        research_source_discovery=FakeScientificDiscovery(),
    )

    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert tool_names[:3] == [
        RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
        RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
        SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
    ]
    early_error = json.loads(
        backend.requests[3].messages[-1]["content"][0]["content"]
    )
    assert "prior complete read" in early_error["detail"]
    assert result.check_result["accepted"] is True
    assert result.code_draft["project_files"] == [
        {
            "path": "adjust.py", "content": adjustment_source,
            "content_sha256": adjustment_sha256,
        },
        {
            "path": "method.py", "content": published_source,
            "content_sha256": published_sha256,
        },
    ]
    import_ref = result.evidence["research_source_refs"][-1]
    assert import_ref["tool"] == SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL
    assert import_ref["source_file_count"] == 2
    assert {
        (row["source_path"], row["source_content_sha256"], row["project_path"])
        for row in import_ref["imports"]
    } == {
        ("method.py", published_sha256, "method.py"),
        ("adjust.py", adjustment_sha256, "adjust.py"),
    }
    assert import_ref["resulting_project_hash"] == scientific_project_hash(
        language="python", code=main_source,
        project_files=result.code_draft["project_files"],
    )
    assert published_source not in str(result.evidence)


def test_public_source_file_batch_is_atomic_when_one_exact_read_drifts() -> None:
    class DriftingDiscovery(FakeScientificDiscovery):
        def __init__(self) -> None:
            super().__init__()
            self.path_reads: dict[str, int] = {}

        def read(self, source_handle, **kwargs):
            observation = super().read(source_handle, **kwargs)
            path = str(kwargs.get("path", "method.py") or "method.py")
            self.path_reads[path] = self.path_reads.get(path, 0) + 1
            if path == "adjust.py" and self.path_reads[path] > 1:
                content = "def adjust(x):\n    return x + 2\n"
                observation.update({
                    "content": content,
                    "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                })
            return observation

    method = "def published_method(x):\n    return sum(x) / len(x)\n"
    adjust = "def adjust(x):\n    return x + 1\n"
    main = "def run_sandbox(seed, replicates):\n    return {'seed': seed}\n"
    imports = [
        {
            "source_origin": "discovered_repository",
            "source_id": "source:published-implementation",
            "revision": "abc123", "source_path": "method.py",
            "expected_content_sha256": hashlib.sha256(method.encode()).hexdigest(),
            "project_path": "method.py",
        },
        {
            "source_origin": "discovered_repository",
            "source_id": "source:published-implementation",
            "revision": "abc123", "source_path": "adjust.py",
            "expected_content_sha256": hashlib.sha256(adjust.encode()).hexdigest(),
            "project_path": "adjust.py",
        },
    ]
    backend = ScriptedScientificBackend([
        _response(ClientToolCall(
            call_id="submit", name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            input={
                "language": "python", "execution_profile": "stdlib",
                "dependencies": [], "entrypoint": "run_sandbox", "code": main,
            },
        )),
        _response(
            ClientToolCall(
                call_id="read-method", name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                input={
                    "source_handle": "source:published-implementation",
                    "path": "method.py", "revision": "abc123",
                },
            ),
            ClientToolCall(
                call_id="read-adjust", name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                input={
                    "source_handle": "source:published-implementation",
                    "path": "adjust.py", "revision": "abc123",
                },
            ),
        ),
        _response(ClientToolCall(
            call_id="import", name=SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
            input={"imports": imports},
        )),
        _run_response(),
        _commit_response(),
    ])

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Inspect exact upstream files before deciding whether to reuse them.",
        user_prompt="Keep the current project when an atomic import fails.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=5,
        max_no_progress_turns=3,
        artifact_id="question:atomic-pinned-source-import",
        initial_code_draft=None,
        initial_check_result={"accepted": False},
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": not candidate.get("project_files"),
        },
        workspace_operation="initial_authoring",
        research_source_discovery=DriftingDiscovery(),
    )

    import_error = json.loads(
        backend.requests[3].messages[-1]["content"][0]["content"]
    )
    assert import_error["error"] == "client_tool_input_rejected"
    assert "import index 1 changed" in import_error["detail"]
    assert result.check_result["accepted"] is True
    assert "project_files" not in result.code_draft
    assert not any(
        ref.get("tool") == SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL
        for ref in result.evidence["research_source_refs"]
    )


def test_model_imports_observed_frozen_project_files_and_executes_them(
    tmp_path,
) -> None:
    source_root = tmp_path / "frozen-project"
    package_root = source_root / "package"
    package_root.mkdir(parents=True)
    init_source = ""
    method_source = "def total(values):\n    return sum(values)\n"
    (package_root / "__init__.py").write_text(init_source, encoding="utf-8")
    (package_root / "method.py").write_text(method_source, encoding="utf-8")
    init_sha256 = hashlib.sha256(init_source.encode()).hexdigest()
    method_sha256 = hashlib.sha256(method_source.encode()).hexdigest()
    manifest = {
        "schema_version": 1,
        "snapshot_id": "frozen-scientific-project",
        "source_horizon": "2025-12-31",
        "source_root": "frozen-project",
        "documents": [
            {
                "document_id": "package-init",
                "title": "package/__init__.py",
                "source_kind": "code",
                "relative_path": "package/__init__.py",
                "sha256": init_sha256,
                "content_mode": "text",
                "media_type": "text/x-python",
                "byte_size": 0,
                "model_visible": True,
            },
            {
                "document_id": "package-method",
                "title": "package/method.py",
                "source_kind": "code",
                "relative_path": "package/method.py",
                "sha256": method_sha256,
                "content_mode": "text",
                "media_type": "text/x-python",
                "byte_size": len(method_source.encode()),
                "model_visible": True,
            },
        ],
    }
    manifest_path = tmp_path / "frozen-project.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    snapshot = load_research_source_snapshot(manifest_path)
    main_source = (
        "from package.method import total\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return {'value': total([seed, replicates])}\n"
    )
    backend = ScriptedScientificBackend([
        _response(ClientToolCall(
            call_id="list-package",
            name=RESEARCH_SOURCE_LIST_TOOL,
            input={"directory": "package"},
        )),
        _response(ClientToolCall(
            call_id="submit-main",
            name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            input={
                "language": "python",
                "execution_profile": "stdlib",
                "dependencies": [],
                "entrypoint": "run_sandbox",
                "code": main_source,
            },
        )),
        _response(ClientToolCall(
            call_id="import-frozen-files",
            name=SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
            input={"imports": [
                {
                    "source_origin": "frozen_snapshot",
                    "source_id": "package-init",
                    "revision": snapshot.snapshot_hash,
                    "source_path": "package/__init__.py",
                    "expected_content_sha256": init_sha256,
                    "project_path": "package/__init__.py",
                },
                {
                    "source_origin": "frozen_snapshot",
                    "source_id": "package-method",
                    "revision": snapshot.snapshot_hash,
                    "source_path": "package/method.py",
                    "expected_content_sha256": method_sha256,
                    "project_path": "package/method.py",
                },
            ]},
        )),
        _run_response(),
        _commit_response(),
    ])
    executions = []

    def check(candidate):
        execution = execute_scientific_sandbox(
            sandbox_dir=tmp_path / "sandbox",
            artifact_id="frozen-project-import",
            language=candidate["language"],
            code=candidate["code"],
            project_files=candidate.get("project_files", []),
            dependencies=candidate["dependencies"],
            seed=2,
            replicates=3,
            timeout_s=30,
        )
        executions.append(execution)
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": execution.status == "EXECUTED"
            and execution.metrics == {"value": 5},
            "execution_status": execution.status,
            "metrics": execution.metrics,
            "errors": list(execution.errors),
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Inspect and reuse exact frozen source when useful.",
        user_prompt="Build and run the selected source-grounded project.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=5,
        max_no_progress_turns=3,
        artifact_id="question:frozen-project-import",
        initial_code_draft=None,
        initial_check_result={"accepted": False},
        check_candidate=check,
        workspace_operation="initial_authoring",
        research_sources=snapshot,
    )

    assert len(executions) == 1
    assert result.check_result["metrics"] == {"value": 5}
    assert result.code_draft["project_files"] == [
        {
            "path": "package/__init__.py",
            "content": "",
            "content_sha256": init_sha256,
        },
        {
            "path": "package/method.py",
            "content": method_source,
            "content_sha256": method_sha256,
        },
    ]
    assert [tool.name for tool in backend.requests[0].tools[:4]] == [
        RESEARCH_SOURCE_LIST_TOOL,
        RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
        SCIENTIFIC_PROJECT_RESEARCH_SOURCE_IMPORT_TOOL,
    ]
    import_ref = result.evidence["research_source_refs"][-1]
    assert [row["source_origin"] for row in import_ref["imports"]] == [
        "frozen_snapshot",
        "frozen_snapshot",
    ]
    assert import_ref["resulting_project_hash"] == scientific_project_hash(
        language="python",
        code=main_source,
        project_files=result.code_draft["project_files"],
    )
    assert method_source not in str(result.evidence)


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


def _commit_response(call_id: str = "commit") -> ClientToolTurnResponse:
    return _response(
        ClientToolCall(
            call_id=call_id,
            name=SCIENTIFIC_SOURCE_COMMIT_TOOL,
            input={},
        )
    )


def _run_response(
    call_id: str = "run-current",
    reason: str = "Execute the exact current model-authored source.",
) -> ClientToolTurnResponse:
    return _response(
        ClientToolCall(
            call_id=call_id,
            name=SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
            input={"reason": reason},
        )
    )


def test_scientific_session_reads_externalized_theory_on_demand() -> None:
    content = "# Claim\n\nFor every admitted sample, $T_n \\to T$.\n"
    sha256 = hashlib.sha256(content.encode()).hexdigest()
    prompt_context, documents = externalize_scientific_workspace_documents(
        {
            "theory_context": {
                "document_authoritative": True,
                "authoritative_theory_documents": [
                    {"path": "derivation.md", "sha256": sha256, "content": content}
                ],
            }
        }
    )
    authored = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'ok': True}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-theory",
                    name=THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                    input={"path": "derivation.md", "line_start": 1, "line_end": 3},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="submit",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=authored,
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )
    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Read theory, then implement.",
        user_prompt=str(prompt_context),
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        artifact_id="question:external-theory",
        initial_code_draft=None,
        initial_check_result={"accepted": False},
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": True,
        },
        workspace_operation="initial_authoring",
        context_documents=documents,
    )

    first_request = backend.requests[0]
    assert content not in str(first_request.messages)
    assert first_request.messages[0]["content"].count(sha256) == 1
    assert [tool.name for tool in first_request.tools] == [
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_EDIT_TOOL,
        SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
        SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
        SCIENTIFIC_SOURCE_READ_TOOL,
        SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
    ]
    read_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert read_observation["content"].strip() == content.strip()
    assert dict(result.code_draft) == authored
    assert content.strip() not in str(result.evidence)
    assert "workspace document content omitted" in str(result.evidence["history"])


def test_scientific_owner_reads_current_source_on_demand() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'marker': 'old'}\n",
    }
    revised = {**initial, "code": initial["code"].replace("'old'", "'new'")}
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="read-current",
                    name=SCIENTIFIC_SOURCE_READ_TOOL,
                    input={"line_start": 1, "line_end": 2},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="submit-revised",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use the exact current source.",
        user_prompt="Revise the source after inspection.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        artifact_id="question:on-demand-source",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == revised,
        },
    )

    opening = str(backend.requests[0].messages)
    assert initial["code"] not in opening
    assert stable_hash(initial["code"]) in opening
    observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert observation["content"] == initial["code"]
    assert observation["source_hash"] == stable_hash(initial["code"])
    assert observation["code_draft_hash"] == stable_hash(initial)
    assert observation["path"] == "main.py"
    assert dict(result.code_draft) == revised
    assert initial["code"] not in str(result.evidence["history"])
    assert "current model-owned source content omitted" in str(
        result.evidence["history"]
    )


def test_scientific_workspace_externalizes_replication_report_without_theory_authority() -> None:
    content = "# Replication report\n\nThe pinned source reproduced metric 0.75.\n"
    sha256 = hashlib.sha256(content.encode()).hexdigest()

    prompt_context, documents = externalize_scientific_workspace_documents(
        {
            "source_replication_context": {
                "checkpoint_id": "source_replication_checkpoint:generic",
                "lineage_verified": True,
                "report_document": {
                    "relative_path": "replication/report.md",
                    "sha256": sha256,
                    "content_loaded": True,
                    "content": content,
                },
                "source_execution": {
                    "execution_status": "EXECUTED",
                    "stdout_sha256": "a" * 64,
                    "raw_stdout": "metric=0.75\n",
                    "raw_stderr": "",
                },
                "author_source_observations": {"observations": ["not copied"]},
                "boundary": "Replication execution is not theory authority.",
            }
        }
    )

    replication = prompt_context["source_replication_context"]
    assert documents == {"replication/report.md": content}
    assert replication["report_document"] == {
        "path": "replication/report.md",
        "sha256": sha256,
        "line_count": 3,
        "byte_size": len(content.encode()),
    }
    assert replication["document_content_transport"] == (
        "hash_bound_read_only_client_tools"
    )
    assert "content" not in replication["report_document"]
    assert content not in json.dumps(prompt_context)
    assert "raw_stdout" not in replication["source_execution"]
    assert "raw_stderr" not in replication["source_execution"]
    assert "author_source_observations" not in replication
    assert "theory_context" not in prompt_context


def test_scientific_source_owner_reads_public_sources_in_same_session(tmp_path) -> None:
    source = "Published method.\nUse a finite sample average.\n"
    document = ResearchSourceDocument(
        document_id="published-method",
        title="Published method",
        source_kind="paper",
        relative_path="published.md",
        sha256=stable_hash(source),
        lines=tuple(source.splitlines()),
    )
    snapshot = ResearchSourceSnapshot(
        snapshot_id="scientific-public-sources",
        source_horizon="2025-12-31",
        snapshot_hash=stable_hash(document.public_descriptor()),
        manifest_sha256="manifest-hash",
        documents=(document,),
        manifest_path=tmp_path / "sources.json",
        source_root=tmp_path,
    )
    authored = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'ok': True}\n",
    }
    backend = ScriptedScientificBackend([
        _response(ClientToolCall(
            call_id="list", name=RESEARCH_SOURCE_LIST_TOOL,
            input={"directory": ""},
        )),
        _response(ClientToolCall(
            call_id="search", name=RESEARCH_SOURCE_SEARCH_TOOL,
            input={"query": "finite sample average"},
        )),
        _response(ClientToolCall(
            call_id="read", name=RESEARCH_SOURCE_READ_TOOL,
            input={"document_id": "published-method", "line_start": 1, "line_end": 2},
        )),
        _response(ClientToolCall(
            call_id="submit", name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL, input=authored,
        )),
        _run_response(),
        _commit_response(),
    ])

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Inspect public sources, then implement.",
        user_prompt="Implement the published method.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=6,
        max_no_progress_turns=2,
        artifact_id="question:public-source",
        initial_code_draft=None,
        initial_check_result={"accepted": False},
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)), "accepted": True,
        },
        workspace_operation="initial_authoring",
        research_sources=snapshot,
    )

    assert [tool.name for tool in backend.requests[0].tools[:3]] == [
        RESEARCH_SOURCE_LIST_TOOL, RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
    ]
    assert [row["tool"] for row in result.evidence["research_source_refs"]] == [
        RESEARCH_SOURCE_LIST_TOOL, RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
    ]
    assert result.evidence["research_source_snapshot"]["snapshot_hash"] == (
        snapshot.snapshot_hash
    )
    assert result.evidence["research_source_ref_fingerprint"] == stable_hash(
        result.evidence["research_source_refs"]
    )
    assert source.strip() not in str(result.evidence["history"])


def test_scientific_source_discovery_survives_same_owner_checkpoint(tmp_path) -> None:
    authored = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'ok': True}\n",
    }
    first_discovery = FakeScientificDiscovery()
    first_backend = ScriptedScientificBackend([
        _response(ClientToolCall(
            call_id="discover", name=RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
            input={"query": "published implementation", "source_kind": "repository"},
        )),
        _response(ClientToolCall(
            call_id="submit", name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL, input=authored,
        )),
    ])
    with pytest.raises(PacketValidationError) as exc_info:
        run_scientific_code_workspace(
            provider=first_backend,
            system_prompt="Find and implement published work.",
            user_prompt="Use public source discovery when useful.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=2,
            max_no_progress_turns=2,
            artifact_id="question:discovered-source",
            initial_code_draft=None,
            initial_check_result={"accepted": False},
            check_candidate=lambda candidate: {
                "code_draft_hash": stable_hash(dict(candidate)), "accepted": True,
            },
            workspace_operation="initial_authoring",
            session_dir=tmp_path / "scientific-discovery-session",
            research_source_discovery=first_discovery,
        )

    checkpoint = exc_info.value.recovery_checkpoint
    source_ref = checkpoint["research_source_refs"][0]
    assert source_ref["results"][0]["source_handle"] == (
        "source:published-implementation"
    )
    assert first_discovery.searches == ["published implementation"]

    checkpoint_draft, checkpoint_observation = (
        load_scientific_code_workspace_checkpoint(
            checkpoint, artifact_id="question:discovered-source"
        )
    )
    with pytest.raises(ValueError, match="requires its public provider"):
        run_scientific_code_workspace(
            provider=ScriptedScientificBackend([]),
            system_prompt="Continue.", user_prompt="Continue.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL, model_tier="haiku",
            temperature=0.0, max_tokens=1200, max_turns=1,
            max_no_progress_turns=1, artifact_id="question:discovered-source",
            initial_code_draft=checkpoint_draft,
            initial_check_result=checkpoint_observation,
            check_candidate=lambda candidate: {}, recovery_checkpoint=checkpoint,
            session_dir=tmp_path / "scientific-discovery-session",
        )
    with pytest.raises(ValueError, match="session reference identity mismatch"):
        run_scientific_code_workspace(
            provider=ScriptedScientificBackend([]),
            system_prompt="Find and implement published work.",
            user_prompt="Use public source discovery when useful.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL, model_tier="haiku",
            temperature=0.0, max_tokens=1200, max_turns=1,
            max_no_progress_turns=1, artifact_id="question:discovered-source",
            initial_code_draft=checkpoint_draft,
            initial_check_result=checkpoint_observation,
            check_candidate=lambda candidate: {}, recovery_checkpoint=checkpoint,
            session_dir=tmp_path / "scientific-discovery-session",
            research_source_discovery=FakeScientificDiscovery("2026-01-01"),
        )

    resumed_discovery = FakeScientificDiscovery()
    second_backend = ScriptedScientificBackend([
        _response(ClientToolCall(
            call_id="read", name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
            input={"source_handle": "source:published-implementation", "path": "method.py"},
        )),
        _run_response(),
        _commit_response(),
    ])
    result = run_scientific_code_workspace(
        provider=second_backend,
        system_prompt="Find and implement published work.",
        user_prompt="Use public source discovery when useful.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL, model_tier="haiku",
        temperature=0.0, max_tokens=1200, max_turns=3,
        max_no_progress_turns=2, artifact_id="question:discovered-source",
        initial_code_draft=checkpoint_draft,
        initial_check_result=checkpoint_observation,
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)), "accepted": True,
        },
        recovery_checkpoint=checkpoint,
        session_dir=tmp_path / "scientific-discovery-session",
        research_source_discovery=resumed_discovery,
    )

    assert resumed_discovery.searches == []
    assert resumed_discovery.reads == ["source:published-implementation"]
    assert [row["tool"] for row in result.evidence["research_source_refs"]] == [
        RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
        RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    ]
    assert "source:published-implementation" in str(second_backend.requests[0].messages)
    assert "published_method" not in str(result.evidence["history"])
    assert "research source text omitted" in str(result.evidence["history"])


def test_same_model_rewrites_complete_source_from_raw_sandbox_observation() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_estimator(data):\n    return missing_name\n",
    }
    revised = {
        **initial,
        "code": "def run_estimator(data):\n    return 0.0\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-1",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                ),
            ),
            _run_response(),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        row = dict(candidate)
        checked.append(row)
        return {
            "code_draft_hash": stable_hash(row),
            "accepted": row == revised,
            "stdout": "{\"estimate\":0.0}",
            "stderr": "",
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Implement the exact estimator.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:estimator",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stdout": "",
            "stderr": "NameError: missing_name",
        },
        check_candidate=check,
    )

    assert dict(result.code_draft) == revised
    assert checked == [revised]
    assert result.evidence["model_owned_source"] is True
    assert result.evidence["runtime_edited_source"] is False
    assert result.evidence["initial_check_accepted"] is False
    assert result.evidence["source_changed"] is True
    assert result.evidence["parent_code_draft_hash"] != result.evidence[
        "submitted_code_draft_hash"
    ]
    assert result.evidence["runtime_executed_tool_calls"] == 3
    assert result.evidence["submit_and_execute_atomic"] is False
    assert result.evidence["source_mutation_and_execution_separated"] is True
    assert result.evidence["explicit_model_commit_required"] is True
    assert result.evidence["model_commit_after_observation"] is True
    assert "NameError: missing_name" in str(backend.requests[0].messages)
    assert all(request.enable_prompt_caching for request in backend.requests)
    assert all(request.disable_parallel_tool_use for request in backend.requests)
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_EDIT_TOOL,
        SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
        SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
        SCIENTIFIC_SOURCE_READ_TOOL,
        SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
    ]
    submission_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == SCIENTIFIC_SOURCE_SUBMISSION_TOOL
    )
    assert "required_estimator_ids" not in submission_schema["properties"]
    assert submission_schema["properties"]["execution_profile"]["enum"] == [
        "stdlib",
        "scientific_wasm",
    ]
    assert "json" not in submission_schema["properties"]["dependencies"][
        "items"
    ]["enum"]
    dependency_description = submission_schema["properties"]["dependencies"][
        "description"
    ]
    assert "language=python" in dependency_description
    assert "numpy, scipy, pandas, scikit-learn, statsmodels, sympy" in (
        dependency_description
    )
    assert "language=r" in dependency_description
    assert "compiler, datasets, grdevices, graphics, grid" in (
        dependency_description
    )


def test_same_model_exact_edits_scientific_source_from_raw_observation() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": (
            "def run_sandbox(seed, replicates):\n"
            "    value = missing_name\n"
            "    return value + missing_name\n"
        ),
    }
    revised = {
        **initial,
        "code": (
            "def run_sandbox(seed, replicates):\n"
            "    value = 1\n"
            "    return value\n"
        ),
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    "ambiguous-edit",
                    SCIENTIFIC_SOURCE_EDIT_TOOL,
                    {
                        "old_text": "missing_name",
                        "new_text": "1",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "edit-first-span",
                    SCIENTIFIC_SOURCE_EDIT_TOOL,
                    {
                        "old_text": "    value = missing_name\n",
                        "new_text": "    value = 1\n",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "edit-second-span",
                    SCIENTIFIC_SOURCE_EDIT_TOOL,
                    {
                        "old_text": "    return value + missing_name\n",
                        "new_text": "    return value\n",
                    },
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        checked.append(dict(candidate))
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == revised,
            "stderr": "" if dict(candidate) == revised else "NameError",
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Fix the exact source from the traceback.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=5,
        max_no_progress_turns=3,
        artifact_id="question:exact-scientific-edit",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "NameError: missing_name",
        },
        check_candidate=check,
    )

    assert dict(result.code_draft) == revised
    assert checked == [revised]
    assert result.evidence["source_updates"] == 2
    assert result.evidence["runtime_edited_source"] is False
    assert "observed 2 matches" in str(backend.requests[1].messages)
    first_applied = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    second_applied = json.loads(
        backend.requests[3].messages[-1]["content"][0]["content"]
    )
    assert first_applied["source_action"] == "atomic_exact_text_edits"
    assert second_applied["source_action"] == "atomic_exact_text_edits"
    assert first_applied["edit_metadata"]["n_edits"] == 1
    assert second_applied["edit_metadata"]["n_edits"] == 1
    assert first_applied["edit_metadata"]["edits"][0]["old_text_chars"] == len(
        "    value = missing_name\n"
    )
    assert second_applied["edit_metadata"]["edits"][0]["old_text_chars"] == len(
        "    return value + missing_name\n"
    )
    edit_schema = next(
        tool.input_schema
        for tool in backend.requests[0].tools
        if tool.name == SCIENTIFIC_SOURCE_EDIT_TOOL
    )
    assert edit_schema["required"] == ["old_text", "new_text"]
    assert set(edit_schema["properties"]) == {
        "old_text",
        "new_text",
        "expected_occurrences",
        "path",
    }
    assert "edits" not in edit_schema["properties"]


def test_r_source_owner_declares_namespace_from_raw_webr_feedback(
    tmp_path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.r_available:
        pytest.skip("pinned WebR runtime is not installed on this host")
    code = (
        "run_sandbox <- function(seed, replicates) {\n"
        "  basis <- splines::bs(c(0, 1, 2, 3), df=3)\n"
        "  list(columns=ncol(basis))\n"
        "}\n"
    )
    initial = {
        "language": "r",
        "execution_profile": "scientific_wasm",
        "dependencies": ["base"],
        "entrypoint": "run_sandbox",
        "code": code,
    }
    revised = {**initial, "dependencies": ["base", "splines"]}

    def execute(candidate, label):
        execution = execute_scientific_sandbox(
            sandbox_dir=tmp_path / label,
            artifact_id=label,
            language=candidate["language"],
            code=candidate["code"],
            dependencies=candidate["dependencies"],
            seed=1,
            replicates=1,
            timeout_s=60,
        )
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": execution.status == "EXECUTED",
            "execution_status": execution.status,
            "errors": list(execution.errors),
            "stderr": execution.stderr_summary,
        }

    initial_check = execute(initial, "initial-r-dependency")
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    "declare-splines",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    revised,
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )
    checked = []

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Use raw execution feedback to revise the current R project.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:r-declared-namespace",
        initial_code_draft=initial,
        initial_check_result=initial_check,
        check_candidate=lambda candidate: (
            checked.append(dict(candidate))
            or execute(dict(candidate), "revised-r-dependency")
        ),
    )

    assert "undeclared package namespace(s): splines" in str(
        backend.requests[0].messages
    )
    assert checked == [revised]
    assert dict(result.code_draft) == revised
    assert result.evidence["runtime_edited_source"] is False


def test_same_model_authors_initial_source_before_sandbox_execution() -> None:
    authored = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": (
            "def run_estimator(request):\n"
            "    return {'estimate': 0.0}\n\n"
            "def run_sandbox(seed, replicates):\n"
            "    return run_estimator({})\n"
        ),
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-1",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=authored,
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Author the estimator from the bound theory contract.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:initial-estimator",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == authored,
            "stdout": "{\"estimate\":0.0}",
            "stderr": "",
        },
        workspace_operation="initial_authoring",
    )

    assert dict(result.code_draft) == authored
    assert result.evidence["workspace_operation"] == "initial_authoring"
    assert result.evidence["parent_code_draft_hash"] == ""
    assert result.evidence["source_updates"] == 1
    assert result.evidence["sandbox_checks"] == 1
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_EDIT_TOOL,
        SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
        SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
        SCIENTIFIC_SOURCE_READ_TOOL,
        SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
    ]
    assert len(backend.requests) == 3


def test_blind_confirmatory_executes_once_after_model_owned_diagnostic_loop() -> None:
    first = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'score': 0.2}\n",
    }
    revised = {
        **first,
        "code": "def run_sandbox(seed, replicates): return {'score': 0.95}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-revised",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )

    class SourceAgent:
        provider = backend

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            return run_scientific_code_workspace(
                provider=cls.provider,
                system_prompt="Use the scientific source tools.",
                user_prompt="Implement and diagnose the current simulation source.",
                model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
                model_tier="haiku",
                temperature=0.0,
                max_tokens=1200,
                max_turns=4,
                max_no_progress_turns=3,
                artifact_id=kwargs["artifact_id"],
                initial_code_draft=kwargs["code_draft"],
                initial_check_result=kwargs["initial_observation"],
                check_candidate=kwargs["check_candidate"],
                workspace_operation=kwargs["workspace_operation"],
            )

    diagnostic_sources: list[str] = []
    confirmatory_sources: list[str] = []

    def diagnostic(candidate):
        source = str(candidate["code"])
        diagnostic_sources.append(source)
        score = 0.95 if candidate == revised else 0.2
        return (
            {
                "script_hash": stable_hash(source),
                "result_hash": stable_hash({"score": score}),
                "runtime_seed": 17,
                "runtime_replicates": 200,
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": score >= 0.9,
                "metrics": {"score": score},
                "metric_gate_errors": (
                    [] if score >= 0.9 else ["diagnostic score below 0.9"]
                ),
                "metric_contract_evaluation": {
                    "evaluations": [
                        {
                            "contract_id": "diagnostic-score",
                            "passed": score >= 0.9,
                            "aggregate_value": score,
                        }
                    ]
                },
            },
            f"diagnostic:{len(diagnostic_sources)}",
        )

    def confirmatory(candidate):
        source = str(candidate["code"])
        confirmatory_sources.append(source)
        return (
            {
                "script_hash": stable_hash(source),
                "result_hash": "confirmatory-secret-result-hash",
                "runtime_seed": 29,
                "runtime_replicates": 2_000,
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": False,
                "metrics": {"score": 0.1},
                "metric_gate_errors": ["confirmatory-secret-failure"],
            },
            "confirmatory",
        )

    prototype, tool_calls = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(),
        question=object(),
        artifact_id="question:blind-simulation",
        code_draft=first,
        source_deferred=False,
        workspace_context={},
        execute_candidate=confirmatory,
        execute_authoring_diagnostic=diagnostic,
        failure_identity={"simulation_id": "blind-simulation"},
        confirmatory_result_blind=True,
    )

    assert diagnostic_sources == [first["code"], revised["code"]]
    assert confirmatory_sources == [revised["code"]]
    assert tool_calls == ["diagnostic:1", "diagnostic:2", "confirmatory"]
    assert prototype["metric_gate_errors"] == ["confirmatory-secret-failure"]
    workspace = prototype["scientific_code_workspace"]
    assert workspace["authoring_execution_phase"] == "exploratory_diagnostic"
    assert workspace["authoring_diagnostic_accepted"] is True
    assert workspace["authoring_diagnostic_runtime_replicates"] == 200
    assert workspace["confirmatory_execution_after_model_commit"] is True
    assert workspace["confirmatory_outcomes_returned_to_source_model"] is False
    transcript = str([request.messages for request in backend.requests])
    assert "diagnostic score below 0.9" not in transcript
    assert '"score":0.95' in transcript
    assert "acceptance_outcomes_withheld" in transcript
    assert "confirmatory-secret" not in transcript
    assert '"accepted":true' in str(backend.requests[0].messages)


def test_blind_authoring_can_defer_confirmation_until_source_review() -> None:
    source = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": (
            "def run_sandbox(seed, replicates):\n"
            "    return {'acceptance_passed': False, "
            "'requested_runtime_replicates': 2000}\n"
        ),
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-source",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=source,
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )

    class SourceAgent:
        provider = backend

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            return run_scientific_code_workspace(
                provider=cls.provider,
                system_prompt="Use the scientific source tools.",
                user_prompt="Author the executable evaluator.",
                model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
                model_tier="haiku",
                temperature=0.0,
                max_tokens=1200,
                max_turns=4,
                max_no_progress_turns=3,
                artifact_id=kwargs["artifact_id"],
                initial_code_draft=None,
                initial_check_result=kwargs["initial_observation"],
                check_candidate=kwargs["check_candidate"],
                workspace_operation=kwargs["workspace_operation"],
            )

    confirmatory_sources: list[str] = []

    def diagnostic(candidate):
        return (
            {
                "script_hash": stable_hash(candidate["code"]),
                "result_hash": "diagnostic-result",
                "runtime_seed": 17,
                "runtime_replicates": 12,
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": False,
                "metrics": {
                    "acceptance_passed": False,
                    "requested_runtime_replicates": 2_000,
                },
                "metric_gate_errors": ["diagnostic outcome is not acceptance"],
            },
            "diagnostic",
        )

    def confirmatory(candidate):
        confirmatory_sources.append(str(candidate["code"]))
        raise AssertionError("confirmation must wait for independent source review")

    prototype, tool_calls = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(),
        question=object(),
        artifact_id="question:evaluator-source",
        code_draft={},
        source_deferred=True,
        workspace_context={},
        execute_candidate=confirmatory,
        execute_authoring_diagnostic=diagnostic,
        failure_identity={"simulation_id": "evaluator-source"},
        confirmatory_result_blind=True,
        defer_confirmatory_execution=True,
    )

    assert confirmatory_sources == []
    assert tool_calls == ["diagnostic"]
    assert prototype["script_hash"] == stable_hash(source["code"])
    workspace = prototype["scientific_code_workspace"]
    assert workspace["confirmatory_execution_after_model_commit"] is False
    assert workspace["confirmatory_execution_deferred_for_independent_review"] is True


def test_uncommitted_workspace_failure_cannot_promote_last_executed_source() -> None:
    candidate = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'score': 1.0}\n",
    }

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source owner controls this workspace")

    class SourceAgent:
        provider = Provider()

        @staticmethod
        def iterate_code_with_tools(**kwargs):
            check = kwargs["check_candidate"](candidate)
            assert check["accepted"] is True
            raise PacketValidationError(
                validation_label="scientific source workspace",
                attempts=1,
                errors=["terminal source was not explicitly committed"],
                history=[],
            )

    def execute(candidate_draft):
        source = str(candidate_draft["code"])
        return (
            {
                "script_hash": stable_hash(source),
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": True,
                "metric_contract_evaluation": {"evaluations": []},
            },
            "sandbox",
        )

    prototype, tool_calls = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(),
        question=object(),
        artifact_id="question:uncommitted-source",
        code_draft={},
        source_deferred=True,
        workspace_context={},
        execute_candidate=execute,
        failure_identity={"simulation_id": "uncommitted-source"},
        confirmatory_result_blind=True,
    )

    assert tool_calls == ["sandbox"]
    assert prototype["execution_smoke_passed"] is True
    assert prototype["scientific_code_workspace_failure"][
        "validation_errors"
    ] == ["terminal source was not explicitly committed"]
    assert scientific_source_candidate_accepted(
        prototype,
        confirmatory_result_blind=True,
    ) is False


def test_unchanged_multifile_release_is_rejected_by_complete_project_identity() -> None:
    candidate = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": (
            "from helper import value\n\n"
            "def run_sandbox(seed, replicates): return {'value': value()}\n"
        ),
        "project_files": [
            {
                "path": "helper.py",
                "content": "def value():\n    return 1\n",
            }
        ],
    }
    release_hash = scientific_project_hash(
        language="python",
        code=candidate["code"],
        project_files=candidate["project_files"],
    )

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source owner controls this workspace")

    class SourceAgent:
        provider = Provider()

        @staticmethod
        def iterate_code_with_tools(**kwargs):
            check = kwargs["check_candidate"](candidate)
            assert check["accepted"] is False
            assert check["prototype"]["prototype_status"] == (
                "UNCHANGED_SOURCE_REJECTED"
            )
            raise PacketValidationError(
                validation_label="scientific source workspace",
                attempts=1,
                errors=["unchanged release rejected"],
                history=[],
            )

    prototype, tool_calls = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(),
        question=object(),
        artifact_id="question:unchanged-project",
        code_draft={},
        source_deferred=True,
        workspace_context={},
        execute_candidate=lambda _candidate: pytest.fail(
            "unchanged project must fail before sandbox execution"
        ),
        failure_identity={"simulation_id": "unchanged-project"},
        disallowed_unchanged_source_hashes=(release_hash,),
    )

    assert tool_calls == []
    assert prototype["prototype_status"] == "UNCHANGED_SOURCE_REJECTED"
    assert prototype["project_hash"] == release_hash


def test_same_model_can_revise_after_technically_successful_execution() -> None:
    first = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'passed': False}\n",
    }
    revised = {
        **first,
        "code": "def run_sandbox(seed, replicates): return {'passed': True}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-first",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=first,
                )
            ),
            _run_response("run-first"),
            _response(
                ClientToolCall(
                    call_id="submit-revised",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                )
            ),
            _run_response("run-revised"),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        candidate = dict(candidate)
        checked.append(candidate)
        return {
            "code_draft_hash": stable_hash(candidate),
            "accepted": True,
            "metrics": {
                "self_diagnostic": {
                    "passed": candidate == revised,
                }
            },
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Inspect execution output before accepting the source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=5,
        max_no_progress_turns=2,
        artifact_id="question:successful-process-failed-diagnostic",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=check,
        workspace_operation="initial_authoring",
    )

    assert checked == [first, revised]
    assert dict(result.code_draft) == revised
    assert '"passed":false' in str(backend.requests[2].messages).lower()
    assert result.evidence["sandbox_checks"] == 2
    assert result.evidence["model_commit_after_observation"] is True


def test_model_cannot_submit_and_commit_before_observing_execution() -> None:
    source = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 1}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=source,
                ),
                ClientToolCall(
                    call_id="premature-commit",
                    name=SCIENTIFIC_SOURCE_COMMIT_TOOL,
                    input={},
                ),
            ),
            _run_response(),
            _commit_response("observed-commit"),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Execute, inspect, then commit.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:observation-before-commit",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": True,
            "stdout": "execution complete",
        },
        workspace_operation="initial_authoring",
    )

    premature = result.evidence["history"][0]["tool_calls"][1]
    assert premature["is_error"] is True
    assert "accepted hash-bound" in premature["result_excerpt"]
    assert dict(result.code_draft) == source
    assert result.evidence["sandbox_checks"] == 1
    assert result.evidence["model_commit_after_observation"] is True


def test_model_selects_dependency_handoff_after_raw_consumer_failure() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 0}\n",
    }
    submitted = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 1}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-1",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=submitted,
                )
            ),
            _run_response(),
            _response(
                ClientToolCall(
                    call_id="report-dependency",
                    name=SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
                    input={
                        "reason": (
                            "The exact bound estimator returned a non-finite response "
                            "for a valid request; the current consumer cannot repair it."
                        )
                    },
                )
            ),
        ]
    )
    source_owner = {
        "owner_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm:accepted",
        "source_manifest_hash": "sha256:manifest",
        "artifact_ids": ["estimator-a"],
        "artifact_hashes": {"estimator-a": "sha256:source"},
    }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise only source owned by this workspace.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:dependency-observation",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "local callback mismatch",
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": False,
            "source_owner": source_owner,
            "prototype": {
                "estimator_runtime_failure_ids": ["estimator-a"],
                "estimator_runtime_errors": [
                    "accepted estimator returned a non-finite response"
                ],
            },
            "stderr": "bound dependency failed in consumer execution",
        },
        allow_dependency_handoff=True,
    )

    assert dict(result.code_draft) == submitted
    assert result.check_result["accepted"] is False
    assert result.evidence["accepted"] is False
    assert result.evidence["source_iteration_disposition"] == (
        SCIENTIFIC_SOURCE_RETURN_TO_DEPENDENCY_OWNER
    )
    assert result.evidence["source_owner"] == source_owner
    assert result.check_result["dependency_failure_report"]["model_selected"] is True
    assert result.evidence["source_updates"] == 1
    assert result.evidence["sandbox_checks"] == 1
    assert len(backend.requests) == 3
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_EDIT_TOOL,
        SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
        SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
        SCIENTIFIC_SOURCE_READ_TOOL,
        SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
        SCIENTIFIC_SOURCE_REPORT_DEPENDENCY_TOOL,
    ]


def test_byte_identical_replacement_is_returned_to_same_model_as_noop() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 0}\n",
    }
    revised = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 1}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="noop-1",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=initial,
                )
            ),
            _response(
                ClientToolCall(
                    call_id="submit-2",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                ),
            ),
            _run_response(),
            _commit_response(),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise the failed source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        artifact_id="question:no-op-replacement",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "assertion failed",
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == revised,
        },
    )

    assert dict(result.code_draft) == revised
    assert result.evidence["source_updates"] == 1
    noop = result.evidence["history"][0]["tool_calls"][0]
    assert noop["is_error"] is True
    assert "byte-identical" in noop["result_excerpt"]
    assert "byte-identical" in str(backend.requests[1].messages)


def test_model_can_run_current_source_in_changed_dependency_environment() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 0}\n",
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="run-current",
                    name=SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                    input={
                        "reason": (
                            "This artifact satisfies its owned interface; another "
                            "bound dependency caused the consumer failure."
                        )
                    },
                )
            ),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        checked.append(dict(candidate))
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": True,
            "stdout": "dependency integration passed",
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Resolve the bound consumer observation.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        artifact_id="question:run-current",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "another dependency failed",
        },
        check_candidate=check,
        allow_current_source_run=True,
    )

    assert dict(result.code_draft) == initial
    assert checked == [initial]
    assert result.evidence["source_changed"] is False
    assert result.evidence["source_updates"] == 0
    assert result.evidence["sandbox_checks"] == 1
    assert result.evidence["current_source_run_requested"] is True
    assert result.evidence["current_source_run_requests"] == 1
    assert result.evidence["accepted"] is True
    assert [tool.name for tool in backend.requests[0].tools] == [
        SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
        SCIENTIFIC_SOURCE_EDIT_TOOL,
        SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
        SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
        SCIENTIFIC_SOURCE_READ_TOOL,
        SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
        SCIENTIFIC_SOURCE_COMMIT_TOOL,
    ]


def test_current_source_runs_at_most_once_per_dependency_environment() -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 0}\n",
    }
    revised = {
        **initial,
        "code": "def run_sandbox(seed, replicates): return {'value': 1}\n",
    }
    run_current_call = {
        "reason": "Another bound dependency owns the observed failure."
    }
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    "run-current-1",
                    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                    run_current_call,
                )
            ),
            _response(
                ClientToolCall(
                    "run-current-2",
                    SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
                    run_current_call,
                )
            ),
            _response(
                ClientToolCall(
                    "submit-revision",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    revised,
                )
            ),
            _run_response("run-revision"),
            _commit_response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        checked.append(dict(candidate))
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == revised,
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Resolve the bound consumer observation.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=5,
        max_no_progress_turns=2,
        artifact_id="question:single-parent-reexecution",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
        },
        check_candidate=check,
        allow_current_source_run=True,
    )

    assert dict(result.code_draft) == revised
    assert checked == [initial, revised]
    repeated = result.evidence["history"][1]["tool_calls"][0]
    assert repeated["is_error"] is True
    assert "current dependency environment" in repeated["result_excerpt"]


def test_scientific_workspace_does_not_reexecute_an_older_source() -> None:
    def draft(value: int) -> dict[str, object]:
        return {
            "language": "python",
            "execution_profile": "stdlib",
            "dependencies": [],
            "entrypoint": "run_sandbox",
            "code": (
                "def run_sandbox(seed, replicates):\n"
                f"    return {{'value': {value}}}\n"
            ),
        }

    initial = draft(0)
    first_revision = draft(1)
    accepted_revision = draft(2)
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    "submit-first",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    first_revision,
                )
            ),
            _run_response("run-first"),
            _response(
                ClientToolCall(
                    "submit-old",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    initial,
                )
            ),
            _response(
                ClientToolCall(
                    "submit-accepted",
                    SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    accepted_revision,
                )
            ),
            _run_response("run-accepted"),
            _commit_response(),
        ]
    )
    executed_hashes: list[str] = []

    def check(candidate):
        candidate_hash = stable_hash(dict(candidate))
        executed_hashes.append(candidate_hash)
        return {
            "code_draft_hash": candidate_hash,
            "accepted": dict(candidate) == accepted_revision,
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise the failed source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=6,
        max_no_progress_turns=2,
        artifact_id="question:no-source-cycling",
        initial_code_draft=initial,
        initial_check_result={
            "code_draft_hash": stable_hash(initial),
            "accepted": False,
            "stderr": "initial failure",
        },
        check_candidate=check,
    )

    assert dict(result.code_draft) == accepted_revision
    assert executed_hashes == [
        stable_hash(first_revision),
        stable_hash(accepted_revision),
    ]
    assert result.evidence["source_updates"] == 2
    old = result.evidence["history"][2]["tool_calls"][0]
    assert old["executed_by_runtime"] is True
    assert old["is_error"] is True
    assert "previously executed" in old["result_excerpt"]


def test_scientific_workspace_retains_complete_bounded_transcript() -> None:
    drafts = [
        {
            "language": "python",
            "execution_profile": "stdlib",
            "dependencies": [],
            "entrypoint": "run_sandbox",
            "code": (
                "def run_sandbox(seed, replicates):\n"
                f"    return {{'attempt': {index}}}\n"
            ),
        }
        for index in range(5)
    ]
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id=f"submit-{index}",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=draft,
                )
            )
            for index, draft in enumerate(drafts)
        ]
        + [_run_response(), _commit_response()]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Batch coherent source revisions, then execute the final source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=7,
        max_no_progress_turns=2,
        artifact_id="question:global-code-budget",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=lambda candidate: {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": dict(candidate) == drafts[-1],
            "stderr": "assertion failed"
            if dict(candidate) != drafts[-1]
            else "",
        },
        workspace_operation="initial_authoring",
    )

    assert dict(result.code_draft) == drafts[-1]
    assert result.evidence["source_updates"] == 5
    assert result.evidence["sandbox_checks"] == 1
    assert result.evidence["transcript_policy"] == CLIENT_TOOL_TRANSCRIPT_POLICY
    assert [len(request.messages) for request in backend.requests] == [
        1,
        3,
        5,
        7,
        9,
        11,
        13,
    ]
    first_prompt = str(backend.requests[0].messages)
    assert AlgorithmEngineerConfig().client_tool_code_max_turns == 48
    assert SimulationEngineerConfig().client_tool_code_max_turns == 48
    assert "at most 5 total model/tool turns" not in first_prompt
    assert "up to 7 model/tool turns" in first_prompt
    assert "retrieval, authoring, execution, and explicit commit" in first_prompt
    assert "Retain observed source hashes and sandbox results" in first_prompt
    assert "attempt': 0" in str(backend.requests[-1].messages)
    assert "attempt': 3" in str(backend.requests[-1].messages)
    assert all(
        [tool.name for tool in request.tools]
        == [
            SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
            SCIENTIFIC_SOURCE_EDIT_TOOL,
            SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
            SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
            SCIENTIFIC_SOURCE_READ_TOOL,
            SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL,
            SCIENTIFIC_SOURCE_COMMIT_TOOL,
        ]
        for request in backend.requests
    )


def test_scientific_workspace_resumes_exact_progress_checkpoint(tmp_path) -> None:
    initial = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return missing\n",
    }
    first_revision = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': missing}\n",
    }
    accepted_revision = {
        **initial,
        "code": "def run_sandbox(seed, replicates):\n    return {'value': 1.0}\n",
    }
    first_backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-first",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=first_revision,
                )
            ),
            _response(),
        ]
    )

    def check(candidate):
        candidate = dict(candidate)
        return {
            "code_draft_hash": stable_hash(candidate),
            "accepted": candidate == accepted_revision,
            "stderr": "" if candidate == accepted_revision else "NameError: missing",
        }

    with pytest.raises(PacketValidationError) as exc_info:
        run_scientific_code_workspace(
            provider=first_backend,
            system_prompt="Use tools.",
            user_prompt="Repair from exact execution feedback.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_no_progress_turns=1,
            artifact_id="question:durable-source",
            initial_code_draft=initial,
            initial_check_result={
                "code_draft_hash": stable_hash(initial),
                "accepted": False,
                "stderr": "NameError: missing",
            },
            check_candidate=check,
            session_dir=tmp_path / "scientific-session",
        )

    checkpoint = exc_info.value.recovery_checkpoint
    checkpoint_draft, checkpoint_observation = (
        load_scientific_code_workspace_checkpoint(
            checkpoint,
            artifact_id="question:durable-source",
        )
    )
    assert checkpoint_draft == first_revision
    assert checkpoint_observation["stderr"] == "NameError: missing"
    assert checkpoint["source_updates"] == 1
    assert checkpoint["checks"] == 0
    assert checkpoint["current_source_executed"] is False
    assert checkpoint["resumable"] is True
    session_ref = checkpoint["client_tool_session_ref"]
    assert session_ref["artifact_kind"] == "ClientToolWorkspaceSessionRef"
    assert session_ref["authorization_fingerprint"]

    second_backend = ScriptedScientificBackend(
        [
            _run_response("run-checkpoint-source"),
            _response(
                ClientToolCall(
                    call_id="submit-accepted",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=accepted_revision,
                )
            ),
            _run_response("run-accepted"),
            _commit_response(),
        ]
    )
    executed: list[dict] = []

    def resumed_check(candidate):
        executed.append(dict(candidate))
        return check(candidate)

    result = run_scientific_code_workspace(
        provider=second_backend,
        system_prompt="Use tools.",
        user_prompt="Continue the exact workspace.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=1,
        artifact_id="question:durable-source",
        initial_code_draft=checkpoint_draft,
        initial_check_result=checkpoint_observation,
        check_candidate=resumed_check,
        recovery_checkpoint=checkpoint,
        session_dir=tmp_path / "scientific-session",
    )

    assert executed == [first_revision, accepted_revision]
    assert dict(result.code_draft) == accepted_revision
    assert result.evidence["resumed_from_checkpoint_id"] == checkpoint[
        "checkpoint_id"
    ]
    assert result.evidence["source_updates"] == 2
    assert result.evidence["sandbox_checks"] == 2
    assert result.evidence["client_tool_session_lineage_continued"] is True
    assert result.evidence["resumed_from_client_tool_session_ref"] == session_ref
    window = result.evidence["client_tool_checkpoint_window"]
    assert window["policy"] == CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY
    assert window["parent_message_count"] == session_ref["message_count"]
    assert window["checkpoint_identity"] == checkpoint["checkpoint_id"]
    assert window["prior_transcript_replayed"] is True
    assert result.evidence["transcript_policy"] == CLIENT_TOOL_TRANSCRIPT_POLICY
    resumed_messages = str(second_backend.requests[0].messages)
    assert checkpoint["checkpoint_id"] in resumed_messages
    assert "submit-first" in resumed_messages
    assert "Continue the exact workspace." in resumed_messages
    assert "Repair from exact execution feedback." not in resumed_messages
    assert len(second_backend.requests[0].messages) >= 3

    tampered = {**checkpoint, "current_code_draft_hash": "tampered"}
    with pytest.raises(ValueError, match="identity mismatch"):
        load_scientific_code_workspace_checkpoint(
            tampered,
            artifact_id="question:durable-source",
        )


def test_scientific_workspace_commits_resumed_accepted_observation_without_rerun(
    tmp_path,
) -> None:
    source = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 1.0}\n",
    }
    first_backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=source,
                )
            ),
            _run_response(),
            _response(),
        ]
    )
    checked: list[dict] = []

    def check(candidate):
        checked.append(dict(candidate))
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": True,
            "stdout": "accepted exact source",
        }

    with pytest.raises(PacketValidationError) as exc_info:
        run_scientific_code_workspace(
            provider=first_backend,
            system_prompt="Use tools.",
            user_prompt="Author and inspect exact source.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=2,
            max_no_progress_turns=2,
            artifact_id="question:resumed-accepted-source",
            initial_code_draft=None,
            initial_check_result={"accepted": False},
            check_candidate=check,
            workspace_operation="initial_authoring",
            session_dir=tmp_path / "accepted-session",
        )

    checkpoint = exc_info.value.recovery_checkpoint
    checkpoint_draft, checkpoint_observation = (
        load_scientific_code_workspace_checkpoint(
            checkpoint,
            artifact_id="question:resumed-accepted-source",
        )
    )
    assert checkpoint_observation["accepted"] is True
    assert checkpoint["current_source_executed"] is True

    result = run_scientific_code_workspace(
        provider=ScriptedScientificBackend([_commit_response()]),
        system_prompt="Use tools.",
        user_prompt="Continue exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=1,
        max_no_progress_turns=1,
        artifact_id="question:resumed-accepted-source",
        initial_code_draft=checkpoint_draft,
        initial_check_result=checkpoint_observation,
        check_candidate=lambda _candidate: pytest.fail(
            "resumed accepted source must not rerun"
        ),
        recovery_checkpoint=checkpoint,
        session_dir=tmp_path / "accepted-session",
    )

    assert checked == [source]
    assert dict(result.code_draft) == source
    assert result.evidence["model_commit_after_observation"] is True
    assert result.evidence["sandbox_checks"] == 1


def test_source_owner_restores_parent_execution_before_checkpoint_commit(
    tmp_path,
) -> None:
    source = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 1.0}\n",
    }

    class SourceAgent:
        def __init__(self, backend):
            self.provider = backend

        def iterate_code_with_tools(self, **kwargs):
            return run_scientific_code_workspace(
                provider=self.provider,
                system_prompt="Use tools.",
                user_prompt="Continue exact source.",
                model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
                model_tier="haiku",
                temperature=0.0,
                max_tokens=1200,
                max_turns=2,
                max_no_progress_turns=2,
                artifact_id=kwargs["artifact_id"],
                initial_code_draft=kwargs["code_draft"],
                initial_check_result=kwargs["initial_observation"],
                check_candidate=kwargs["check_candidate"],
                workspace_operation=kwargs["workspace_operation"],
                recovery_checkpoint=kwargs["recovery_checkpoint"],
                session_dir=kwargs["session_dir"],
            )

    executions: list[dict] = []

    def execute(candidate):
        executions.append(dict(candidate))
        source_text = str(candidate["code"])
        return (
            {
                "source_code": source_text,
                "script_hash": stable_hash(source_text),
                "result_hash": stable_hash({"value": 1.0}),
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": True,
                "returncode": 0,
                "stdout_summary": "accepted exact source",
            },
            "sandbox",
        )

    first_prototype, _ = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(
            ScriptedScientificBackend(
                [
                    _response(
                        ClientToolCall(
                            call_id="submit-source",
                            name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                            input=source,
                        )
                    ),
                    _run_response("run-source"),
                    _response(),
                ]
            )
        ),
        question=object(),
        artifact_id="question:source-owner-resume",
        code_draft={},
        source_deferred=True,
        workspace_context={},
        execute_candidate=execute,
        failure_identity={"estimator_id": "source-owner-resume"},
        session_dir=tmp_path / "source-owner-session",
    )
    checkpoint = first_prototype["scientific_code_workspace_failure"][
        "recovery_checkpoint"
    ]
    assert checkpoint["current_source_executed"] is True
    assert executions == [source]

    resumed_prototype, _ = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(
            ScriptedScientificBackend([_commit_response("commit-restored")])
        ),
        question=object(),
        artifact_id="question:source-owner-resume",
        code_draft=checkpoint["current_code_draft"],
        source_deferred=False,
        workspace_context={},
        execute_candidate=lambda _candidate: pytest.fail(
            "restored accepted source must not rerun"
        ),
        failure_identity={"estimator_id": "source-owner-resume"},
        recovery_checkpoint=checkpoint,
        recovery_prototype=first_prototype,
        session_dir=tmp_path / "source-owner-session",
    )

    assert executions == [source]
    assert "scientific_code_workspace_failure" not in resumed_prototype
    assert resumed_prototype["source_code"] == source["code"]
    assert resumed_prototype["scientific_code_workspace"][
        "resumed_from_checkpoint_id"
    ] == checkpoint["checkpoint_id"]
    assert resumed_prototype["scientific_code_workspace"]["sandbox_checks"] == 1

    tampered_prototype = dict(first_prototype)
    tampered_prototype["source_code"] = source["code"] + "# tampered\n"
    rejected_prototype, _ = run_source_owner_scientific_workspace(
        proposal_agent=SourceAgent(ScriptedScientificBackend([])),
        question=object(),
        artifact_id="question:source-owner-resume",
        code_draft=checkpoint["current_code_draft"],
        source_deferred=False,
        workspace_context={},
        execute_candidate=lambda _candidate: pytest.fail(
            "tampered recovery must fail before sandbox execution"
        ),
        failure_identity={"estimator_id": "source-owner-resume"},
        recovery_checkpoint=checkpoint,
        recovery_prototype=tampered_prototype,
        session_dir=tmp_path / "source-owner-session",
    )
    assert rejected_prototype["prototype_status"] == (
        "SCIENTIFIC_WORKSPACE_RECOVERY_PROTOTYPE_INVALID"
    )
    assert rejected_prototype["scientific_code_workspace_failure"][
        "validation_errors"
    ] == ["recovery prototype is not bound to checkpoint evidence"]


def test_scientific_workspace_commits_within_explicit_turn_budget() -> None:
    source = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 1.0}\n",
    }
    source_hash = stable_hash(source)
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="legacy-encoded-edit-first",
                    name=SCIENTIFIC_SOURCE_EDIT_TOOL,
                    input={"edits": "[]"},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="legacy-encoded-edit-duplicate",
                    name=SCIENTIFIC_SOURCE_EDIT_TOOL,
                    input={"edits": "[]"},
                )
            ),
            _commit_response("reserved-commit"),
        ]
    )

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Continue the accepted exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=5,
        max_no_progress_turns=2,
        artifact_id="question:accepted-no-progress-source",
        initial_code_draft=source,
        initial_check_result={
            "code_draft_hash": source_hash,
            "accepted": True,
            "source_iteration_disposition": "accepted",
            "stdout": "accepted exact source",
        },
        check_candidate=lambda _candidate: pytest.fail(
            "accepted source must not rerun"
        ),
    )

    assert dict(result.code_draft) == source
    assert result.evidence["model_commit_after_observation"] is True
    assert result.evidence["sandbox_checks"] == 0
    assert backend.requests[-1].tool_choice == "any"
    assert "requires top-level old_text and new_text" in str(
        backend.requests[1].messages
    )
    assert "Ordinary actions are complete" not in str(
        backend.requests[-1].messages[-1]
    )


def test_scientific_workspace_does_not_reexecute_checkpoint_in_same_environment(
    tmp_path,
) -> None:
    source = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates): return {'value': 0.0}\n",
    }
    revised = {
        **source,
        "code": "def run_sandbox(seed, replicates): return {'value': 1.0}\n",
    }
    checked: list[dict] = []

    def check(candidate):
        candidate = dict(candidate)
        checked.append(candidate)
        return {
            "code_draft_hash": stable_hash(candidate),
            "accepted": candidate == revised,
            "stderr": "assertion failed" if candidate != revised else "",
        }

    with pytest.raises(PacketValidationError) as exc_info:
        run_scientific_code_workspace(
            provider=ScriptedScientificBackend(
                [
                    _run_response(),
                    _response(),
                ]
            ),
            system_prompt="Use tools.",
            user_prompt="Author and inspect exact source.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_no_progress_turns=2,
            artifact_id="question:no-resumed-reexecution",
            initial_code_draft=source,
            initial_check_result={
                "code_draft_hash": stable_hash(source),
                "accepted": False,
                "stderr": "dependency environment changed",
            },
            check_candidate=check,
            workspace_operation="targeted_revision",
            allow_current_source_run=True,
            session_dir=tmp_path / "failed-session",
        )

    checkpoint = exc_info.value.recovery_checkpoint
    checkpoint_draft, checkpoint_observation = (
        load_scientific_code_workspace_checkpoint(
            checkpoint,
            artifact_id="question:no-resumed-reexecution",
        )
    )
    backend = ScriptedScientificBackend(
        [
            _run_response("rejected-rerun"),
            _response(
                ClientToolCall(
                    call_id="submit-revision",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input=revised,
                )
            ),
            _run_response("run-revision"),
            _commit_response(),
        ]
    )
    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Continue exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        artifact_id="question:no-resumed-reexecution",
        initial_code_draft=checkpoint_draft,
        initial_check_result=checkpoint_observation,
        check_candidate=check,
        allow_current_source_run=True,
        recovery_checkpoint=checkpoint,
        session_dir=tmp_path / "failed-session",
    )

    assert checked == [source, revised]
    rejected = result.evidence["history"][0]["tool_calls"][0]
    assert rejected["is_error"] is True
    assert "already executed" in rejected["result_excerpt"]
    assert dict(result.code_draft) == revised


def test_execution_observation_omits_stale_callback_samples_after_binding_passes() -> None:
    prototype = {
        "execution_phase": "estimator_developer_diagnostic",
        "empirical_evidence_status": (
            "ALGORITHM_DEVELOPER_DIAGNOSTIC_NOT_CONFIRMATORY_EVIDENCE"
        ),
        "execution_attempted": True,
        "execution_smoke_passed": True,
        "mechanical_estimator_invocation_verified": True,
        "estimator_invocation_counts": {"estimator": 100},
        "estimator_invocation_samples": {
            "estimator": [{"request": {"sample": list(range(100))}}]
        },
        "metric_gate_errors": ["coverage failed"],
    }

    compact = scientific_workspace_prototype_observation(prototype)
    failed_binding = scientific_workspace_prototype_observation(
        {
            **prototype,
            "mechanical_estimator_invocation_verified": False,
        }
    )

    assert compact["estimator_invocation_counts"] == {"estimator": 100}
    assert compact["execution_phase"] == "estimator_developer_diagnostic"
    assert compact["empirical_evidence_status"] == (
        "ALGORITHM_DEVELOPER_DIAGNOSTIC_NOT_CONFIRMATORY_EVIDENCE"
    )
    assert "estimator_invocation_samples" not in compact
    assert "estimator_invocation_samples" in failed_binding


def test_confirmatory_source_observation_withholds_realized_outcomes() -> None:
    observation = scientific_workspace_prototype_observation(
        {
            "prototype_status": "FAILED_METRIC_GATE",
            "execution_attempted": True,
            "execution_smoke_passed": True,
            "smoke_passed": False,
            "returncode": 0,
            "stdout_summary": "metric=0.2",
            "stderr_summary": "",
            "script_hash": "source-hash",
            "mechanical_estimator_invocation_verified": False,
            "estimator_runtime_failure_ids": ["candidate"],
            "estimator_runtime_errors": ["AttributeError: incompatible request"],
            "estimator_invocation_samples": {
                "candidate": [
                    {
                        "invocation_index": 1,
                        "request": {"mode": "withheld-realized-value"},
                        "response": {"estimate": 0.2},
                        "request_shape": {
                            "type": "object",
                            "fields": {
                                "mode": {"type": "string", "length": 23}
                            },
                        },
                        "response_status": "ERROR",
                        "error_type": "AttributeError",
                    }
                ]
            },
            "execution_envelope_hash": "outcome-derived-envelope-hash",
            "result_hash": "result-hash",
            "metric_gate_errors": ["observed 0.2 is below 0.9"],
            "metric_contracts": [
                {
                    "contract_id": "frozen-gate",
                    "metric_value_kind": "boolean",
                    "operator": "==",
                    "aggregation": "at_least_fraction",
                    "threshold": 1,
                    "tolerance": 0.0,
                    "minimum_pass_fraction": 0.92,
                    "required_runtime_replicates": 80,
                }
            ],
            "metric_contract_evaluation": {
                "evaluations": [
                    {
                        "contract_id": "frozen-gate",
                        "requirement_id": "frozen-requirement",
                        "metric_path": ["metric"],
                        "passed": False,
                        "resolved_values_preview": [0.2],
                        "aggregate_value": 0.2,
                        "measurement_interface_valid": False,
                        "measurement_interface_status": "VALUE_TYPE_INVALID",
                        "measurement_interface_errors": [
                            "metric contract frozen-gate: metric_path resolved a "
                            "nonnumeric or nonfinite value"
                        ],
                    }
                ]
            },
            "metrics": {"metric": 0.2},
        },
        include_empirical_outcomes=False,
    )

    assert observation["execution_smoke_passed"] is True
    assert observation["empirical_outcomes_withheld"] is True
    assert observation["empirical_outcome_authority"] == "EmpiricalEvaluator"
    assert observation["measurement_interface_failures"] == [
        {
            "contract_id": "frozen-gate",
            "requirement_id": "frozen-requirement",
            "metric_path": ["metric"],
            "metric_value_kind": "boolean",
            "operator": "==",
            "aggregation": "at_least_fraction",
            "threshold": 1,
            "tolerance": 0.0,
            "minimum_pass_fraction": 0.92,
            "required_runtime_replicates": 80,
            "measurement_interface_status": "VALUE_TYPE_INVALID",
            "measurement_interface_errors": [
                "metric contract frozen-gate: metric_path resolved a "
                "nonnumeric or nonfinite value"
            ],
        }
    ]
    invocation = observation["estimator_invocation_samples"]["candidate"][0]
    assert invocation["request_shape"]["fields"]["mode"] == {"type": "string"}
    assert "invocation_index" not in invocation
    assert "request" not in invocation
    assert "response" not in invocation
    for key in (
        "prototype_status",
        "smoke_passed",
        "stdout_summary",
        "result_hash",
        "execution_envelope_hash",
        "metric_gate_errors",
        "failed_metric_contracts",
        "metrics_preview",
    ):
        assert key not in observation
    assert "0.2" not in str(observation)
    assert "withheld-realized-value" not in str(observation)
    assert "23" not in str(observation)


def test_model_owns_multifile_scientific_project_lifecycle() -> None:
    main_source = (
        "from helper import offset\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return {'value': offset(seed), 'n': replicates}\n"
    )
    helper_initial = "def offset(value):\n    return value + 1\n"
    helper_final = "def offset(value):\n    return value + 4\n"
    backend = ScriptedScientificBackend(
        [
            _response(
                ClientToolCall(
                    call_id="submit-main",
                    name=SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
                    input={
                        "language": "python",
                        "execution_profile": "stdlib",
                        "dependencies": [],
                        "entrypoint": "run_sandbox",
                        "code": main_source,
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-helper",
                    name=SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
                    input={"path": "helper.py", "content": helper_initial},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="write-unused",
                    name=SCIENTIFIC_PROJECT_FILE_WRITE_TOOL,
                    input={"path": "unused.py", "content": "VALUE = 1\n"},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="edit-helper",
                    name=SCIENTIFIC_SOURCE_EDIT_TOOL,
                    input={
                        "path": "helper.py",
                        "old_text": "    return value + 1\n",
                        "new_text": "    return value + 4\n",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    call_id="read-helper",
                    name=SCIENTIFIC_SOURCE_READ_TOOL,
                    input={"path": "helper.py", "line_start": 1, "line_end": 2},
                )
            ),
            _response(
                ClientToolCall(
                    call_id="remove-unused",
                    name=SCIENTIFIC_PROJECT_FILE_REMOVE_TOOL,
                    input={"path": "unused.py"},
                )
            ),
            _run_response(),
            _commit_response(),
        ]
    )

    def check(candidate):
        project_files = list(candidate.get("project_files", []) or [])
        accepted = bool(
            candidate.get("code") == main_source
            and len(project_files) == 1
            and project_files[0].get("path") == "helper.py"
            and project_files[0].get("content") == helper_final
        )
        return {
            "code_draft_hash": stable_hash(dict(candidate)),
            "accepted": accepted,
            "stderr": "" if accepted else "project mismatch",
        }

    result = run_scientific_code_workspace(
        provider=backend,
        system_prompt="Use project tools.",
        user_prompt="Implement and execute the complete project.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=8,
        max_no_progress_turns=3,
        artifact_id="question:multifile-project",
        initial_code_draft=None,
        initial_check_result={
            "artifact_kind": "ScientificSourceAuthoringRequired",
            "accepted": False,
            "execution_attempted": False,
        },
        check_candidate=check,
        workspace_operation="initial_authoring",
    )

    assert result.check_result["accepted"] is True
    assert result.code_draft["code"] == main_source
    assert [row["path"] for row in result.code_draft["project_files"]] == [
        "helper.py"
    ]
    assert result.code_draft["project_files"][0]["content"] == helper_final
    assert result.evidence["source_updates"] == 5
    read_observation = json.loads(
        backend.requests[5].messages[-1]["content"][0]["content"]
    )
    assert read_observation["content"].strip() == helper_final.strip()
    assert "unused.py" not in str(result.code_draft)
