from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formal_source_retrieval_benchmark import (
    DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
    FormalSourceRetrievalBenchmarkCase,
    run_formal_source_retrieval_benchmark,
)


FORMAL_SOURCE_RETRIEVAL_ABLATION_SCHEMA_VERSION = 1


def run_formal_source_retrieval_ablation_benchmark(
    out_dir: Path | None = None,
    *,
    baseline_retriever: object,
    enhanced_retriever: object,
    baseline_name: str = "sqlite_fts_shape_symbol_graph",
    enhanced_name: str = "sqlite_fts_shape_symbol_graph_lean_rag_dependency",
    cases: tuple[
        FormalSourceRetrievalBenchmarkCase,
        ...,
    ] = DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
    k: int = 8,
) -> dict[str, object]:
    """Compare formal-source retrieval with and without the strongest provider.

    The ordinary benchmark proves that a configured retriever can recover gold
    theorem families. This ablation records whether adding a dependency-graph
    provider improves rank, discovers otherwise-missed hits, or regresses any
    gold query. It is retrieval evidence only; Lean/AXLE remains the proof
    boundary.
    """

    baseline_dir = out_dir / "baseline" if out_dir is not None else None
    enhanced_dir = out_dir / "enhanced" if out_dir is not None else None
    baseline = run_formal_source_retrieval_benchmark(
        baseline_dir,
        retriever=baseline_retriever,
        cases=cases,
        k=k,
    )
    enhanced = run_formal_source_retrieval_benchmark(
        enhanced_dir,
        retriever=enhanced_retriever,
        cases=cases,
        k=k,
    )
    baseline_rows = {str(row["query_id"]): row for row in baseline["rows"] if isinstance(row, dict)}
    enhanced_rows = {str(row["query_id"]): row for row in enhanced["rows"] if isinstance(row, dict)}
    rows = []
    for case in cases:
        b = baseline_rows.get(case.query_id, {})
        e = enhanced_rows.get(case.query_id, {})
        b_rank = _rank_value(b.get("hit_rank"))
        e_rank = _rank_value(e.get("hit_rank"))
        rows.append(
            {
                "query_id": case.query_id,
                "query": case.query,
                "expected_name_fragments": case.expected_name_fragments,
                "baseline_hit_rank": b.get("hit_rank"),
                "enhanced_hit_rank": e.get("hit_rank"),
                "baseline_top1_name": b.get("top1_name", ""),
                "enhanced_top1_name": e.get("top1_name", ""),
                "baseline_ok": bool(b.get("ok", False)),
                "enhanced_ok": bool(e.get("ok", False)),
                "rank_delta": b_rank - e_rank if b_rank and e_rank else None,
                "new_hit": not bool(b.get("ok", False)) and bool(e.get("ok", False)),
                "lost_hit": bool(b.get("ok", False)) and not bool(e.get("ok", False)),
                "rank_improved": bool(b.get("ok", False)) and bool(e.get("ok", False)) and e_rank < b_rank,
                "rank_regressed": bool(b.get("ok", False)) and bool(e.get("ok", False)) and e_rank > b_rank,
            }
        )
    payload: dict[str, object] = {
        "schema_version": FORMAL_SOURCE_RETRIEVAL_ABLATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "baseline_name": baseline_name,
        "enhanced_name": enhanced_name,
        "baseline": _summary_payload(baseline),
        "enhanced": _summary_payload(enhanced),
        "k": int(k),
        "n_cases": len(rows),
        "n_new_hits": sum(1 for row in rows if row["new_hit"]),
        "n_lost_hits": sum(1 for row in rows if row["lost_hit"]),
        "n_rank_improved": sum(1 for row in rows if row["rank_improved"]),
        "n_rank_regressed": sum(1 for row in rows if row["rank_regressed"]),
        "enhanced_all_ok": bool(enhanced["all_ok"]),
        "no_lost_hits": not any(row["lost_hit"] for row in rows),
        "all_ok": bool(enhanced["all_ok"]) and not any(row["lost_hit"] for row in rows),
        "rows": rows,
        "dataset_fingerprint": stable_hash(
            {
                "baseline": baseline.get("dataset_fingerprint", ""),
                "enhanced": enhanced.get("dataset_fingerprint", ""),
                "rows": rows,
            }
        ),
        "limitations": [
            "retrieval ablation measures premise/source ranking, not Lean proof success",
            "a neutral or negative rank delta is not proof that the provider is useless for other proof states",
            "dependency-graph hits from retrieval-only corpora still require separate AXLE/Lean proof validation before becoming proof claims",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_source_retrieval_ablation_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_source_retrieval_ablation.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _rank_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _summary_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        "retriever_source": payload.get("retriever_source", ""),
        "n_cases": payload.get("n_cases", 0),
        "n_ok": payload.get("n_ok", 0),
        "recall_at_k": payload.get("recall_at_k", 0.0),
        "mean_reciprocal_rank": payload.get("mean_reciprocal_rank", 0.0),
        "all_ok": payload.get("all_ok", False),
    }


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Source Retrieval Ablation",
        "",
        f"- Baseline: `{payload.get('baseline_name')}`",
        f"- Enhanced: `{payload.get('enhanced_name')}`",
        f"- Enhanced all OK: `{payload.get('enhanced_all_ok')}`",
        f"- New hits: {payload.get('n_new_hits')}",
        f"- Lost hits: {payload.get('n_lost_hits')}",
        f"- Rank improved: {payload.get('n_rank_improved')}",
        f"- Rank regressed: {payload.get('n_rank_regressed')}",
        "",
        "## Query Deltas",
        "",
        "| Query | Baseline rank | Enhanced rank | New | Lost | Improved | Regressed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| `{row.get('query_id')}` | {row.get('baseline_hit_rank')} | "
            f"{row.get('enhanced_hit_rank')} | {row.get('new_hit')} | "
            f"{row.get('lost_hit')} | {row.get('rank_improved')} | {row.get('rank_regressed')} |"
        )
    return "\n".join(lines) + "\n"
