import subprocess
from argparse import Namespace
from pathlib import Path

import ai_statistician.cli as cli_module
import ai_statistician.research_source_inventory as source_inventory
from ai_statistician.cli import (
    _capability_eval_default_lean_project_candidates,
    _research_agent_runtime_local_lean_preflight_errors,
)
from ai_statistician.research_source_inventory import (
    CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT,
)


def test_capability_eval_has_one_source_controlled_lean_default() -> None:
    assert _capability_eval_default_lean_project_candidates() == (
        CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT,
    )
    assert CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT == (
        Path(__file__).resolve().parents[1]
        / "external"
        / "EmpericalProcessLEAN-main"
    )


def test_capability_eval_fails_before_model_when_lean_project_is_missing() -> None:
    errors = _research_agent_runtime_local_lean_preflight_errors(
        Namespace(
            capability_eval=True,
            local_lean=True,
            formalizer_candidate_local_lean=False,
            formalizer_candidate_lean_lsp_mcp=False,
            formalizer_candidate_lean_project="",
            lean_project="",
        )
    )

    assert len(errors) == 1
    assert "canonical Statlib-founded submodule" in errors[0]
    assert "git submodule update --init --recursive" in errors[0]


def test_capability_eval_rejects_canonical_lean_gitlink_drift(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "lakefile.lean").write_text("package Test\n", encoding="utf-8")
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:stable\n", encoding="utf-8")
    monkeypatch.setattr(
        source_inventory,
        "CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        cli_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="+4cec786 external/EmpericalProcessLEAN-main\n",
            stderr="",
        ),
    )

    errors = _research_agent_runtime_local_lean_preflight_errors(
        Namespace(
            capability_eval=True,
            local_lean=True,
            formalizer_candidate_local_lean=False,
            formalizer_candidate_lean_lsp_mcp=False,
            formalizer_candidate_lean_project=str(tmp_path),
            lean_project="",
        )
    )

    assert len(errors) == 1
    assert "not at the AI-Statistician gitlink" in errors[0]
