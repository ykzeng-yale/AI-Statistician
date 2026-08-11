from __future__ import annotations

from types import SimpleNamespace

import ai_statistician.proof_state_feedback as proof_state_module
from ai_statistician.proof_state_feedback import (
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
