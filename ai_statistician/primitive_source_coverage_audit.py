from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formal_source_index import build_formal_source_search_backend
from .formalization_target_audit import audit_formalization_targets


EXTERNAL_SOURCE_IDS = {
    "formal_slt",
    "lean_rademacher",
    "lean_machine_learning_lml",
    "brownian_motion_lean",
    "kolmogorov_extension_lean",
    "scilean_calculus",
    "atlas_lean_high_dimensional_statistics",
    "atlas_lean_theory_of_probability",
    "atlas_lean_probabilistic_methods",
    "atlas_lean_real_analysis",
    "atlas_lean_functional_analysis",
    "atlas_lean_differential_analysis",
    "atlas_lean_fourier_analysis",
    "atlas_lean_projection_theory",
}


@dataclass(frozen=True)
class PrimitiveSourceCoverageRow:
    primitive: str
    n_gaps: int
    problem_classes: tuple[str, ...]
    theorem_goals: tuple[str, ...]
    classification: str
    proof_bank_bridge_obligations: tuple[str, ...]
    local_candidate_declarations: tuple[str, ...]
    external_candidate_declarations: tuple[str, ...]
    external_source_ids: tuple[str, ...]
    suggested_next_step: str
    ok: bool
    errors: tuple[str, ...] = ()


def audit_primitive_source_coverage(
    run_dir: Path,
    out_dir: Path | None = None,
    *,
    formal_source_retriever: Any | None = None,
    formal_source_index_path: Path | None = None,
    lean_rag_db_path: Path | None = None,
    k: int = 8,
) -> dict[str, object]:
    """Classify missing formal primitives by reusable proof/source support.

    This audit answers a narrower question than proof-bank expansion: given the
    current formal gaps, which missing primitives appear closeable by existing
    verified proof-bank bridges, local StatInference/Mathlib declarations, or
    newly indexed external Lean/statistical-learning sources? Search hits are
    retrieval evidence only; they are not Lean proof evidence.
    """

    target_payload = audit_formalization_targets(run_dir)
    if formal_source_retriever is None and formal_source_index_path is not None:
        formal_source_retriever = build_formal_source_search_backend(
            db_path=formal_source_index_path,
            lean_rag_db_path=lean_rag_db_path,
        )
    retriever_enabled = formal_source_retriever is not None
    rows = tuple(
        _classify_target(row, formal_source_retriever, k=k)
        for row in target_payload.get("rows", [])
        if isinstance(row, dict)
    )
    by_classification = Counter(row.classification for row in rows)
    source_counts = Counter(source_id for row in rows for source_id in row.external_source_ids)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "formal_source_retriever_enabled": retriever_enabled,
        "formal_source_index_path": str(formal_source_index_path or ""),
        "lean_rag_dependency_graph_enabled": bool(
            getattr(formal_source_retriever, "lean_rag_dependency_graph_enabled", False)
        ),
        "lean_rag_dependency_graph_path": str(
            getattr(formal_source_retriever, "lean_rag_dependency_graph_path", "")
        ),
        "n_primitives": len(rows),
        "n_direct_wrapper_possible": by_classification.get("direct_wrapper_possible", 0),
        "n_bridge_lemma_needed": by_classification.get("bridge_lemma_needed", 0),
        "n_source_only_not_importable": by_classification.get("source_only_not_importable", 0),
        "n_no_source_found": by_classification.get("no_source_found", 0),
        "n_external_source_supported": sum(1 for row in rows if row.external_candidate_declarations),
        "by_classification": dict(sorted(by_classification.items())),
        "by_external_source_id": dict(sorted(source_counts.items())),
        "top_direct_wrapper_possible": [
            asdict(row) for row in rows if row.classification == "direct_wrapper_possible"
        ][:10],
        "top_bridge_lemma_needed": [
            asdict(row) for row in rows if row.classification == "bridge_lemma_needed"
        ][:10],
        "top_external_source_only": [
            asdict(row) for row in rows if row.classification == "source_only_not_importable"
        ][:10],
        "all_ok": bool(rows) and all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
        "limitations": [
            "Retrieval hits are not proof evidence; only AXLE/Lean verified obligations are proof evidence.",
            "External source hits may require import/version adaptation before they can become proof-bank obligations.",
            "The classification is a prioritization layer for proof-bank mining, not an autonomous theorem prover.",
        ],
        "audit_fingerprint": stable_hash([asdict(row) for row in rows]),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "primitive_source_coverage_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "primitive_source_coverage.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _classify_target(
    target: dict[str, Any],
    formal_source_retriever: Any | None,
    *,
    k: int,
) -> PrimitiveSourceCoverageRow:
    primitive = str(target.get("primitive", ""))
    proof_bank_bridges = tuple(
        str(item) for item in target.get("bridge_candidate_obligations", []) or [] if str(item)
    )
    local_candidates = tuple(
        str(item) for item in target.get("candidate_declarations", []) or [] if str(item)
    )
    external_hits = _external_hits(primitive, formal_source_retriever, k=k) if primitive else ()
    external_decls = tuple(hit["name"] for hit in external_hits)
    external_source_ids = tuple(sorted({hit["source_id"] for hit in external_hits}))
    if proof_bank_bridges and local_candidates:
        classification = "direct_wrapper_possible"
    elif proof_bank_bridges or local_candidates:
        classification = "bridge_lemma_needed"
    elif external_decls:
        classification = "source_only_not_importable"
    else:
        classification = "no_source_found"
    errors: list[str] = []
    if not primitive:
        errors.append("missing primitive")
    if classification == "no_source_found":
        # This row is still audit-clean: no source found is a valid
        # prioritization result, not a manifest error.
        pass
    return PrimitiveSourceCoverageRow(
        primitive=primitive,
        n_gaps=int(target.get("n_gaps", 0) or 0),
        problem_classes=tuple(str(item) for item in target.get("problem_classes", []) or [] if str(item)),
        theorem_goals=tuple(str(item) for item in target.get("theorem_goals", []) or [] if str(item)),
        classification=classification,
        proof_bank_bridge_obligations=proof_bank_bridges,
        local_candidate_declarations=local_candidates[:8],
        external_candidate_declarations=external_decls[:8],
        external_source_ids=external_source_ids,
        suggested_next_step=_suggest_next_step(primitive, classification, proof_bank_bridges, local_candidates, external_decls),
        ok=not errors,
        errors=tuple(errors),
    )


def _external_hits(
    primitive: str,
    formal_source_retriever: Any | None,
    *,
    k: int,
) -> tuple[dict[str, str], ...]:
    if formal_source_retriever is None:
        return ()
    search = getattr(formal_source_retriever, "search", None)
    if not callable(search):
        return ()
    query = primitive.replace("_", " ")
    hits = search(query, k=max(k * 4, 20))
    rows: list[dict[str, str]] = []
    for hit in hits:
        decl = getattr(hit, "declaration", None)
        source_id = str(getattr(decl, "source_id", ""))
        if source_id not in EXTERNAL_SOURCE_IDS:
            continue
        rows.append(
            {
                "name": str(getattr(decl, "name", "")),
                "source_id": source_id,
                "path": str(getattr(decl, "path", "")),
                "line": str(getattr(decl, "line", "")),
            }
        )
        if len(rows) >= k:
            break
    return tuple(rows)


def _suggest_next_step(
    primitive: str,
    classification: str,
    proof_bank_bridges: tuple[str, ...],
    local_candidates: tuple[str, ...],
    external_decls: tuple[str, ...],
) -> str:
    if classification == "direct_wrapper_possible":
        return (
            f"Try an AXLE-verified wrapper for `{primitive}` using proof-bank bridge "
            f"`{proof_bank_bridges[0]}` and local declaration `{local_candidates[0]}`."
        )
    if classification == "bridge_lemma_needed":
        if proof_bank_bridges:
            return f"Use proof-bank bridge `{proof_bank_bridges[0]}` and add a small interface lemma for `{primitive}`."
        return f"Mine local declaration `{local_candidates[0]}` and add a proof-bank bridge for `{primitive}`."
    if classification == "source_only_not_importable":
        return (
            f"Inspect external declaration `{external_decls[0]}` for `{primitive}`; "
            "port or wrap the compatible theorem before adding proof-bank evidence."
        )
    return f"No useful source hit found for `{primitive}`; design the Lean primitive from first principles."


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Primitive Source Coverage Audit",
        "",
        f"- Run directory: `{payload.get('run_dir')}`",
        f"- Missing primitives classified: {payload.get('n_primitives')}",
        f"- Direct wrappers possible: {payload.get('n_direct_wrapper_possible')}",
        f"- Bridge lemmas needed: {payload.get('n_bridge_lemma_needed')}",
        f"- External-source only: {payload.get('n_source_only_not_importable')}",
        f"- No source found: {payload.get('n_no_source_found')}",
        f"- lean_rag dependency graph active: {payload.get('lean_rag_dependency_graph_enabled')}",
        "",
        "## Classification Counts",
        "",
    ]
    by_class = payload.get("by_classification", {})
    if isinstance(by_class, dict):
        for name, count in by_class.items():
            lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Top Direct Wrapper Candidates", ""])
    for row in payload.get("top_direct_wrapper_possible", []):
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('primitive')}`: bridge={row.get('proof_bank_bridge_obligations', [])[:2]}, "
                f"local={row.get('local_candidate_declarations', [])[:2]}"
            )
    lines.extend(["", "## Top External-Source-Only Candidates", ""])
    for row in payload.get("top_external_source_only", []):
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('primitive')}`: sources={row.get('external_source_ids', [])}, "
                f"decls={row.get('external_candidate_declarations', [])[:3]}"
            )
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
