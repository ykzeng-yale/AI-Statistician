from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ai_statistician.lean_project import (
    LeanProjectExecutor,
    canonical_model_authored_lean_project,
    load_model_authored_lean_project,
    model_authored_lean_project,
    persist_model_authored_lean_project,
)
from ai_statistician.research_source_inventory import (
    CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT,
)


def test_model_authored_lean_project_binds_files_order_and_target() -> None:
    target = "import AIStat.B\n\ntheorem target : True := by trivial\n"
    files = [
        {"path": "AIStat/A.lean", "content": "theorem a : True := by trivial\n"},
        {"path": "AIStat/B.lean", "content": "theorem b : True := by trivial\n"},
    ]
    first = model_authored_lean_project(
        target_source=target,
        project_files=files,
        support_build_order=("AIStat/A.lean", "AIStat/B.lean"),
    )
    reordered = model_authored_lean_project(
        target_source=target,
        project_files=files,
        support_build_order=("AIStat/B.lean", "AIStat/A.lean"),
    )

    assert first["project_hash"] != reordered["project_hash"]
    assert canonical_model_authored_lean_project(
        first, target_source=target
    ) == first
    with pytest.raises(ValueError, match="target source hash mismatch"):
        canonical_model_authored_lean_project(
            first,
            target_source=target.replace("True", "False"),
        )


def test_model_authored_lean_project_persists_as_content_addressed_reference(
    tmp_path: Path,
) -> None:
    target = "theorem target : True := by trivial\n"
    project = model_authored_lean_project(
        target_source=target,
        project_files=[
            {
                "path": "AIStat/Support.lean",
                "content": "theorem helper : True := by trivial\n",
            }
        ],
        support_build_order=("AIStat/Support.lean",),
    )

    reference = persist_model_authored_lean_project(
        project,
        target_source=target,
        root=tmp_path,
    )
    rows, order = load_model_authored_lean_project(
        reference,
        target_source=target,
    )

    assert "support_files" not in reference
    assert reference["project_hash"] == project["project_hash"]
    assert rows[0].content == project["support_files"][0]["content"]
    assert order == ("AIStat/Support.lean",)
    persisted = tmp_path / reference["relative_path"]
    persisted.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="reference hash mismatch"):
        load_model_authored_lean_project(reference, target_source=target)


def test_empty_model_authored_lean_project_reference_round_trips(
    tmp_path: Path,
) -> None:
    target = "theorem target : True := by trivial\n"
    reference = persist_model_authored_lean_project(
        model_authored_lean_project(target_source=target),
        target_source=target,
        root=tmp_path,
    )

    rows, order = load_model_authored_lean_project(
        reference,
        target_source=target,
    )

    assert reference["support_file_count"] == 0
    assert rows == ()
    assert order == ()


@pytest.mark.parametrize(
    "path",
    (
        "../Escape.lean",
        "/tmp/Absolute.lean",
        "Main.lean",
        "main.lean",
        "Support.txt",
    ),
)
def test_model_authored_lean_project_rejects_unsafe_support_paths(path: str) -> None:
    with pytest.raises(ValueError):
        model_authored_lean_project(
            target_source="theorem target : True := by trivial\n",
            project_files=[{"path": path, "content": "theorem helper : True := by trivial\n"}],
            support_build_order=(path,),
        )


def test_lean_project_environment_failure_returns_raw_observation(
    tmp_path: Path,
) -> None:
    target = "theorem target : True := by trivial\n"
    executor = LeanProjectExecutor(
        active_project=tmp_path / "missing-project",
        workspace_root=tmp_path / "lean-workspace",
        timeout_s=1,
    )
    result = executor.check_target(
        target_source=target,
        candidate_lean_declaration="target",
        project_files=(),
        support_build_order=(),
    )

    assert result["compiled"] is False
    assert result["local_lean_exit_status"] == "environment_error"
    assert "environment unavailable" in result["local_lean_stderr"]
    assert result["lean_project_hash"] == result["lean_project"]["project_hash"]

    support = executor.check_support_file(
        relative_path="Support.lean",
        project_files=(
            {
                "path": "Support.lean",
                "content": "theorem helper : True := by trivial\n",
            },
        ),
        prior_build_order=(),
    )

    assert support["compiled"] is False
    assert support["local_lean_exit_status"] == "environment_error"
    assert "environment unavailable" in support["local_lean_stderr"]


def test_pinned_statlib_foundation_compiles_model_authored_multifile_project(
    tmp_path: Path,
) -> None:
    project = CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT.resolve()
    if shutil.which("lake") is None or not (project / "lakefile.lean").is_file():
        pytest.skip("pinned Lean foundation is unavailable")
    if not (project / ".lake" / "packages" / "mathlib").exists():
        pytest.skip("pinned Lean foundation is not built")

    base_path = "AIStatWorkspace/Base.lean"
    support_path = "AIStatWorkspace/Support.lean"
    base_source = (
        "namespace AIStatWorkspace\n"
        "theorem base_true : True := by trivial\n"
        "end AIStatWorkspace\n"
    )
    support_source = (
        "import AIStatWorkspace.Base\n\n"
        "namespace AIStatWorkspace\n"
        "theorem support_true : True := by exact base_true\n"
        "end AIStatWorkspace\n"
    )
    target_source = (
        "import AIStatWorkspace.Support\n\n"
        "theorem ai_stat_workspace_target : True := by\n"
        "  exact AIStatWorkspace.support_true\n"
    )
    files = [
        {"path": base_path, "content": base_source},
        {"path": support_path, "content": support_source},
    ]
    executor = LeanProjectExecutor(
        active_project=project,
        workspace_root=tmp_path / "lean-workspace",
        timeout_s=60,
    )

    base = executor.check_support_file(
        relative_path=base_path,
        project_files=files,
        prior_build_order=(),
    )
    support = executor.check_support_file(
        relative_path=support_path,
        project_files=files,
        prior_build_order=(base_path,),
    )
    target = executor.check_target(
        target_source=target_source,
        candidate_lean_declaration="ai_stat_workspace_target",
        project_files=files,
        support_build_order=(base_path, support_path),
    )

    assert base["compiled"] is True, base["local_lean_stderr"]
    assert support["compiled"] is True, support["local_lean_stderr"]
    assert support["compiled_prefix_reused"] is True
    assert len(support["support_build_attempts"]) == 1
    assert target["local_lean_compiled"] is True, target["local_lean_stderr"]
    assert target["candidate_identity_lean_verified"] is True
    assert target["candidate_axiom_audit_clean"] is True
    assert target["lean_project_hash"] == target["lean_project"]["project_hash"]
