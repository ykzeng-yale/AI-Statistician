from __future__ import annotations

from types import SimpleNamespace

import ai_statistician.proof_state_feedback as proof_state_module
from ai_statistician.proof_state_feedback import (
    LeanLspMcpProofStateFeedbackProvider,
    LocalLeanProofStateFeedbackProvider,
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
        ]
    )

    assert observed_sources == [source]
    assert rows[0].attempt_status == "local_lean_accepted"
    assert rows[0].local_lean_checked is True
    assert rows[0].proof_evidence_status.endswith("NOT_PROOF_EVIDENCE")
    assert "import Mathlib" not in observed_sources[0]


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
                        "file_path": "Library/Example.lean",
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
