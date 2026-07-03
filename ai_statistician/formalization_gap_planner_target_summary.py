from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
import re
from typing import Any


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
        target_prover_family = str(fallback_target_prover_family or "").strip()
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
        return str(row.get("target_prover_family", "") or "").strip()
    return str(getattr(row, "target_prover_family", "") or "").strip()


def target_prover_key(value: object) -> str:
    """Normalize target prover family labels for cross-component comparisons."""

    key = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    aliases = {
        "coq": "rocq",
        "coq8": "rocq",
        "coq_8": "rocq",
        "coq_rocq": "rocq",
        "rocq_coq": "rocq",
        "isabelle_hol": "isabelle",
        "lean": "lean4",
        "lean_4": "lean4",
    }
    return aliases.get(key, key)


def is_lean_target_prover(value: object) -> bool:
    """Return whether a target family is a Lean target or Lean adapter."""

    key = target_prover_key(value)
    return key == "lean4" or key.startswith(("lean4_", "lean_"))


def target_prover_family_compatible(requested: object, supported: object) -> bool:
    """Return whether a supported target family can serve the requested target."""

    requested_key = target_prover_key(requested)
    supported_key = target_prover_key(supported)
    if not requested_key or not supported_key:
        return True
    if requested_key == supported_key:
        return True
    return is_lean_target_prover(requested_key) and is_lean_target_prover(
        supported_key
    )
