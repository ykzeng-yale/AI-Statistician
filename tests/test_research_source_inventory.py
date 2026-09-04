from pathlib import Path

from ai_statistician.research_source_inventory import (
    CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT,
    EMPIRICAL_PROCESS_LEAN_ROOT_CANDIDATES,
    EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT,
    MATHLIB_ROOT,
    SOURCE_INVENTORY_TARGETS,
    STAT_LEAN_ROOT,
    STATLIB_ROOT,
    STATLIB_UPSTREAM_ROOT,
    _inventory_target,
    _mathlib_root_candidates,
    _statlib_root_candidates,
)


def test_active_lean_inventory_has_one_canonical_foundation() -> None:
    project_root = Path("/tmp/empirical-process")

    assert EMPIRICAL_PROCESS_LEAN_ROOT_CANDIDATES == (
        CANONICAL_EMPIRICAL_PROCESS_LEAN_ROOT,
    )
    assert _mathlib_root_candidates(project_root) == (
        project_root / ".lake" / "packages" / "mathlib" / "Mathlib",
    )
    assert _statlib_root_candidates(project_root) == (
        project_root / ".lake" / "packages" / "Statlib",
    )


def test_inventory_uses_verified_empirical_process_packages_when_available() -> None:
    pinned_mathlib = EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT / ".lake" / "packages" / "mathlib" / "Mathlib"
    pinned_statlib = EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT / ".lake" / "packages" / "Statlib"

    if pinned_mathlib.exists():
        assert MATHLIB_ROOT.resolve() == pinned_mathlib.resolve()
    if pinned_statlib.exists():
        assert STATLIB_ROOT.resolve() == pinned_statlib.resolve()


def test_statlib_inventory_recognizes_the_public_module_layout() -> None:
    target = next(target for target in SOURCE_INVENTORY_TARGETS if target.id == "statlib")
    row = _inventory_target(target)

    if Path(target.location).exists():
        assert row.availability_status == "local_ready"
        assert row.ok is True


def test_upstream_statlib_is_separate_optional_retrieval_inventory() -> None:
    target = next(
        target
        for target in SOURCE_INVENTORY_TARGETS
        if target.id == "statlib_upstream_discovery"
    )

    assert Path(target.location) == STATLIB_UPSTREAM_ROOT / "Statlib"
    assert target.source_type == "lean_library"
    assert target.local_required is False
    assert target.usage_policy == "retrieval_only_no_training_export"
    if Path(target.location).exists():
        row = _inventory_target(target)
        assert row.availability_status == "local_ready"
        assert row.git_commit


def test_stat_lean_is_separate_optional_retrieval_inventory() -> None:
    target = next(
        target for target in SOURCE_INVENTORY_TARGETS if target.id == "stat_lean"
    )

    assert Path(target.location) == STAT_LEAN_ROOT / "StatLean"
    assert target.source_type == "lean_library"
    assert target.local_required is False
    assert target.usage_policy == "retrieval_only_no_training_export"
    if Path(target.location).exists():
        row = _inventory_target(target)
        assert row.availability_status == "local_ready"
        assert row.git_commit


def test_legacy_statinference_is_inventory_not_live_library() -> None:
    target = next(
        target
        for target in SOURCE_INVENTORY_TARGETS
        if target.id == "legacy_ai_statistician_statinference"
    )

    assert target.source_type == "historical_lean_snapshot"
    assert target.usage_policy == (
        "historical_audit_and_training_only_no_live_retrieval"
    )
