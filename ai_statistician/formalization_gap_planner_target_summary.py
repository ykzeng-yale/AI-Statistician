from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from .formalization_gap_planner_contract import (
    normalize_manifest_target_prover_family,
    normalize_target_prover_family,
)


def target_prover_family_summary(
    rows: Iterable[Any],
    *,
    fallback_target_prover_family: object = "",
) -> dict[str, object]:
    """Return a manifest-level target summary computed from row targets."""

    by_target = target_prover_family_counts(rows)
    concrete_targets = sorted(target for target in by_target if target != "missing")
    if len(concrete_targets) == 1:
        target_prover_family = concrete_targets[0]
    elif len(concrete_targets) > 1:
        target_prover_family = "mixed:" + ",".join(concrete_targets)
    else:
        target_prover_family = normalize_manifest_target_prover_family(
            fallback_target_prover_family
        )
    return {
        "target_prover_family": target_prover_family,
        "n_target_prover_families": len(concrete_targets),
        "by_target_prover_family": dict(sorted(by_target.items())),
    }


def target_prover_family_counts(rows: Iterable[Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        target = _row_target_prover_family(row)
        counts[target or "missing"] += 1
    return counts


def _row_target_prover_family(row: Any) -> str:
    if isinstance(row, dict):
        raw_target = row.get("target_prover_family", "")
    else:
        raw_target = getattr(row, "target_prover_family", "")
    return normalize_target_prover_family(raw_target)
