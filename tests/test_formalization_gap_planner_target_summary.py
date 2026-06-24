from __future__ import annotations

from types import SimpleNamespace

from ai_statistician.formalization_gap_planner_contract import (
    LEGACY_LEAN_TARGET_PROVER_FAMILY,
)
from ai_statistician.formalization_gap_planner_target_summary import (
    target_prover_family_counts,
    target_prover_family_summary,
)


def test_target_prover_family_summary_canonicalizes_legacy_aliases() -> None:
    rows = [
        {"target_prover_family": LEGACY_LEAN_TARGET_PROVER_FAMILY},
        {"target_prover_family": "coq8"},
        SimpleNamespace(target_prover_family="isabelle_hol"),
        SimpleNamespace(target_prover_family="hol_4"),
        {"target_prover_family": ""},
    ]

    assert target_prover_family_counts(rows) == {
        "lean4": 1,
        "rocq": 1,
        "isabelle": 1,
        "hol4": 1,
        "missing": 1,
    }
    assert target_prover_family_summary(rows) == {
        "target_prover_family": "mixed:hol4,isabelle,lean4,rocq",
        "n_target_prover_families": 4,
        "by_target_prover_family": {
            "hol4": 1,
            "isabelle": 1,
            "lean4": 1,
            "missing": 1,
            "rocq": 1,
        },
    }


def test_target_prover_family_summary_normalizes_fallback_manifest_target() -> None:
    assert target_prover_family_summary(
        [],
        fallback_target_prover_family="mixed:coq8,lean4_adapter_with_portable_gap_schema",
    ) == {
        "target_prover_family": "mixed:lean4,rocq",
        "n_target_prover_families": 0,
        "by_target_prover_family": {},
    }
