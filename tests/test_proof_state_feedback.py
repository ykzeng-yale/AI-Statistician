from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import ai_statistician.proof_state_feedback as proof_state_module
from ai_statistician.fingerprint import stable_hash
from ai_statistician.proof_state_feedback import (
    LeanLspMcpProofStateFeedbackProvider,
    LocalLeanProofStateFeedbackProvider,
    bind_candidate_axiom_audit_to_proof_state_feedback,
    build_lean_declaration_inspection_tool,
)
from ai_statistician.research_schema import FormalSubclaim


def test_local_proof_state_provider_executes_exact_model_source(monkeypatch) -> None:
    source = "theorem target : True := by\n  sorry\n"
    observed_sources: list[str] = []

    def fake_run(command, **kwargs):
        del kwargs
        with open(command[-1], encoding="utf-8") as handle:
            observed_sources.append(handle.read())
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(proof_state_module.subprocess, "run", fake_run)
    provider = LocalLeanProofStateFeedbackProvider(lean_command=("lean",))

    rows = provider.inspect(
        [
            FormalSubclaim(
                id="target",
                title="Exact source inspection",
                status="FAILED",
                claim="Inspect the current model source.",
                lean_statement=source,
            )
        ],
        line=1,
        column=1,
    )

    assert observed_sources == [source]
    assert rows[0].attempt_status == "local_lean_accepted"
    assert rows[0].local_lean_checked is True
    assert rows[0].proof_evidence_status.endswith("NOT_PROOF_EVIDENCE")
    assert "import Mathlib" not in observed_sources[0]


def test_axiom_audit_keeps_elaborated_placeholder_feedback_untrusted(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        proof_state_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="declaration uses `sorry`",
        ),
    )
    provider = LocalLeanProofStateFeedbackProvider(lean_command=("lean",))
    rows = provider.inspect(
        [
            FormalSubclaim(
                id="target",
                title="Untrusted source inspection",
                status="FAILED",
                claim="Inspect the current model source.",
                lean_statement="theorem target : True := by\n  sorry\n",
            )
        ],
        line=1,
        column=1,
    )

    bound = bind_candidate_axiom_audit_to_proof_state_feedback(
        rows,
        audit_checked=True,
        audit_clean=False,
        untrusted_axioms=("sorryAx",),
    )

    assert bound[0].attempt_status == "local_lean_untrusted_axioms"
    assert bound[0].route_revision_recommended is True
    assert any("sorryAx" in value for value in bound[0].diagnostics)
    assert bound[0].residual_goals == ()


def test_local_provider_does_not_invent_residual_lean_goals(monkeypatch) -> None:
    monkeypatch.setattr(
        proof_state_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Candidate.lean:2:3: error: unknown identifier 'missing'",
        ),
    )
    provider = LocalLeanProofStateFeedbackProvider(lean_command=("lean",))

    row = provider.inspect(
        [
            FormalSubclaim(
                id="target",
                title="Failed source inspection",
                status="FAILED",
                claim="Inspect the current model source.",
                lean_statement="theorem target : True := by\n  exact missing\n",
                gap_reason="a host-side gap label, not a Lean goal",
                errors=["a prior error, not a Lean goal"],
                proof_dependencies=["Example.helper"],
            )
        ],
        line=2,
        column=3,
    )[0]

    assert row.attempt_status == "local_lean_failed"
    assert row.residual_goals == ()
    assert any("unknown identifier" in value for value in row.diagnostics)


def test_lsp_provider_promotes_only_exact_lean_goal_observations(
    tmp_path,
    monkeypatch,
) -> None:
    project = tmp_path / "LeanProject"
    project.mkdir()
    (project / "lean-toolchain").write_text("leanprover/lean4:test\n")
    artifact = project / "Candidate.lean"
    source = "theorem target (p : Prop) (hp : p) : p := by\n  exact missing\n"
    artifact.write_text(source, encoding="utf-8")
    exact_goal = "p : Prop\nhp : p\n⊢ p"
    collector_calls = []

    monkeypatch.setattr(
        proof_state_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Candidate.lean:2:9: error: unknown identifier 'missing'",
        ),
    )

    def collect_transcript(**kwargs):
        collector_calls.append(dict(kwargs))
        transcript = {
            "events": [
                {
                    "tool_name": "lean_goal",
                    "arguments": {"line": 2, "column": 9},
                    "ok": True,
                    "result": {
                        "text": exact_goal,
                        "structuredContent": {"goals_before": [exact_goal]},
                    },
                },
                {
                    "tool_name": "lean_diagnostic_messages",
                    "arguments": {"start_line": 1, "end_line": 4},
                    "ok": True,
                    "result": {"text": "unknown identifier 'missing'"},
                },
                {
                    "tool_name": "lean_goal",
                    "arguments": {"line": 2, "column": 9},
                    "ok": False,
                    "result": {"text": "stale transport output must not be a goal"},
                    "error": {"message": "transport closed"},
                },
            ]
        }
        Path(kwargs["out"]).write_text(json.dumps(transcript), encoding="utf-8")
        return {
            "trace_collection_mode": "live",
            "mcp_client_restarts": 0,
            "honesty_boundary": "route_evidence_only_not_kernel_verified",
        }

    provider = LeanLspMcpProofStateFeedbackProvider(
        project_root=project,
        lean_command=("lean",),
        mcp_transcript_collector=collect_transcript,
    )
    row = provider.inspect(
        [
            FormalSubclaim(
                id="target",
                title="Exact goal inspection",
                status="FAILED",
                claim="Inspect the current model source.",
                lean_statement=source,
                artifact_path=str(artifact),
                gap_reason="a host-side gap label, not a Lean goal",
                errors=["a prior error, not a Lean goal"],
            )
        ],
        line=2,
        column=9,
    )[0]

    assert collector_calls[0]["line"] == 2
    assert collector_calls[0]["column"] == 9
    assert row.residual_goals == (exact_goal,)
    assert all("host-side" not in value for value in row.residual_goals)
    assert all("stale transport" not in value for value in row.residual_goals)
    goal_trace = next(
        trace
        for trace in row.tool_call_trace
        if trace.get("tool") == "lean_lsp_mcp.lean_goal"
    )
    assert goal_trace["goal_observations"] == [exact_goal]
    assert goal_trace["goal_observations_hash"] == stable_hash([exact_goal])
    assert goal_trace["position_source"] == "model_selected"


def test_indexed_dependency_source_is_inspectable_without_lsp(tmp_path) -> None:
    project = tmp_path / "LeanProject"
    source_root = project / ".lake" / "packages" / "Statlib" / "Statlib"
    source_root.mkdir(parents=True)
    source_file = source_root / "Inference.lean"
    source_file.write_text(
        "namespace InferenceModelofMeasure\n"
        "def IsConsistent : Prop := True\n"
        "end InferenceModelofMeasure\n",
        encoding="utf-8",
    )

    class Retriever:
        source_snapshots = {
            "statlib": {
                "location": str(source_root),
                "entry_modules": ["Statlib"],
            }
        }

        @staticmethod
        def search(symbol: str, *, k: int):
            assert symbol == "InferenceModelofMeasure.IsConsistent"
            assert k == 8
            declaration = SimpleNamespace(
                source_id="statlib",
                path="Inference.lean",
                line=2,
                name=symbol,
                namespace="InferenceModelofMeasure",
                signature="def IsConsistent : Prop := True",
            )
            return [SimpleNamespace(declaration=declaration)]

    tool = build_lean_declaration_inspection_tool(
        formal_source_retriever=Retriever(),
        project_root=project,
        proof_state_provider=None,
    )

    assert tool is not None
    result = tool("", "InferenceModelofMeasure.IsConsistent", 4, {})
    assert result["ok"] is True
    assert result["status"] == "INDEXED_SOURCE_OBSERVED"
    api = result["active_project_api_context"]
    assert api["importable_module"] == "Statlib.Inference"
    assert api["qualified_declaration"] == (
        "InferenceModelofMeasure.IsConsistent"
    )
    assert "def IsConsistent" in api["declaration_source_context"]["content"]
    assert api["declaration_source_context"]["file_path"] == str(source_file)


def test_lsp_provider_returns_exact_model_selected_declaration_source(
    tmp_path,
    monkeypatch,
) -> None:
    project = tmp_path / "LeanProject"
    project.mkdir()
    (project / "lean-toolchain").write_text("leanprover/lean4:test\n")
    artifact = project / "Candidate.lean"
    artifact.write_text(
        "import Mathlib\n#check Example.Source\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, dict]] = []
    clients = []

    class FakeClient:
        def __init__(self, command, **kwargs) -> None:
            self.command = command
            self.kwargs = kwargs
            self.closed = False
            clients.append(self)

        def call_tool(self, name: str, arguments: dict):
            calls.append((name, dict(arguments)))
            return {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "isError": False,
                    "structuredContent": {
                        "file_path": "Library/Source.lean",
                        "start_line": 10,
                        "end_line": 18,
                        "content": (
                            "structure Source where\n"
                            "  field : Nat\n"
                        ),
                    },
                },
            }

        def close(self) -> None:
            self.closed = True

    provider = LeanLspMcpProofStateFeedbackProvider(
        project_root=project,
        timeout_s=37,
        mcp_command=("lean-lsp-mcp",),
    )
    monkeypatch.setattr(
        provider,
        "_load_openprover_mcp_module",
        lambda: SimpleNamespace(LeanLspMcpClient=FakeClient),
    )

    result = provider.inspect_declaration(
        artifact_path=str(artifact),
        symbol="Example.Source",
        context_lines=80,
    )

    assert result["ok"] is True
    assert result["status"] == "OBSERVED"
    assert result["observation"]["content"].startswith("structure Source")
    assert result["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")
    assert calls == [
        (
            "lean_declaration_file",
            {
                "file_path": str(artifact.resolve()),
                "symbol": "Example.Source",
                "context_lines": 40,
                "full_file": False,
            },
        )
    ]
    assert clients[0].kwargs["project"] == project.resolve()
    assert (
        clients[0].kwargs["timeout_s"]
        == provider.mcp_timeout_s
        == provider.timeout_s
        == 37
    )
    assert clients[0].closed is True


def test_lsp_provider_rejects_mislocalized_declaration_context(
    tmp_path,
    monkeypatch,
) -> None:
    project = tmp_path / "LeanProject"
    project.mkdir()
    (project / "lean-toolchain").write_text("leanprover/lean4:test\n")
    artifact = project / "Candidate.lean"
    artifact.write_text("import Mathlib\n", encoding="utf-8")

    class FakeClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        @staticmethod
        def call_tool(_name: str, _arguments: dict):
            return {
                "result": {
                    "isError": False,
                    "structuredContent": {
                        "file_path": "Library/Example.lean",
                        "start_line": 1,
                        "end_line": 2,
                        "content": "module\n\npublic import Mathlib",
                    },
                }
            }

        def close(self) -> None:
            pass

    provider = LeanLspMcpProofStateFeedbackProvider(
        project_root=project,
        mcp_command=("lean-lsp-mcp",),
    )
    monkeypatch.setattr(
        provider,
        "_load_openprover_mcp_module",
        lambda: SimpleNamespace(LeanLspMcpClient=FakeClient),
    )

    result = provider.inspect_declaration(
        artifact_path=str(artifact),
        symbol="Example.Source",
    )

    assert result["ok"] is False
    assert result["status"] == "SYMBOL_CONTEXT_MISSING"
    assert result["symbol_context_observed"] is False
    assert "requested declaration symbol" in result["error"]
