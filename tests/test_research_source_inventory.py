from pathlib import Path

from ai_statistician.research_source_inventory import (
    EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT,
    MATHLIB_ROOT,
    SOURCE_INVENTORY_TARGETS,
    STATLIB_ROOT,
    _inventory_target,
    _mathlib_root_candidates,
    _statlib_root_candidates,
)


def test_empirical_process_lake_packages_are_the_preferred_lean_snapshot() -> None:
    project_root = Path("/tmp/empirical-process")

    assert _mathlib_root_candidates(project_root)[0] == (
        project_root / ".lake" / "packages" / "mathlib" / "Mathlib"
    )
    assert _statlib_root_candidates(project_root)[0] == (
        project_root / ".lake" / "packages" / "Statlib"
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
