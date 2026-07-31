from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .formal_source_index import (
    DEFAULT_AUDIT_QUERIES,
    FormalDeclaration,
    FormalSourceRetriever,
    build_formal_source_index,
    formal_source_index_fingerprint,
)


DEFAULT_GRAPH_AUDIT_QUERIES: tuple[tuple[str, str], ...] = (
    ("variance_independence_graph", "variance finite sum independent pairwise estimator average"),
    ("hajek_ratio_graph", "Hajek ratio linearization inverse probability weighting survey mean"),
    ("wald_variance_graph", "Wald standard error positive variance studentized confidence interval"),
    ("rademacher_symmetrization_graph", "Rademacher sign symmetrization support subGaussian"),
    ("backward_martingale_graph", "backward martingale reverse filtration conditional expectation convergence"),
) + DEFAULT_AUDIT_QUERIES[:6]


@dataclass(frozen=True)
class FormalSourceGraphHit:
    declaration: FormalDeclaration
    score: float
    matched_terms: tuple[str, ...]
    graph_symbols: tuple[str, ...]
    base_rank: int | None = None


class FormalSourceGraphRetriever:
    """Graph expansion over the local Lean/stat declaration index.

    The graph is intentionally simple and source-local: declarations connect to
    compressed Lean symbols extracted by `formal_source_index`. Search first
    obtains lexical/shape seeds, then expands through shared symbols. This adds
    a cheap graph-RAG layer without introducing a service or embedding store.
    """

    source = "formal_source_graph"

    def __init__(
        self,
        declarations: list[FormalDeclaration] | None = None,
        *,
        base_retriever: object | None = None,
    ) -> None:
        self.declarations = declarations if declarations is not None else build_formal_source_index()
        self.base_retriever = base_retriever or FormalSourceRetriever(self.declarations)
        self._decl_key_to_idx = {_decl_key(decl): idx for idx, decl in enumerate(self.declarations)}
        self._decl_symbols = [_symbols_for_declaration(decl) for decl in self.declarations]
        self._symbol_to_decl: dict[str, set[int]] = defaultdict(set)
        for idx, symbols in enumerate(self._decl_symbols):
            for symbol in symbols:
                self._symbol_to_decl[symbol].add(idx)

    @property
    def n_symbol_nodes(self) -> int:
        return len(self._symbol_to_decl)

    @property
    def n_edges(self) -> int:
        return sum(len(symbols) for symbols in self._decl_symbols)

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceGraphHit]:
        base_hits = self.base_retriever.search(query, k=max(k * 6, 30))
        if not base_hits:
            return []

        base_rank_by_idx: dict[int, int] = {}
        score_by_idx: dict[int, float] = defaultdict(float)
        graph_symbols_by_idx: dict[int, set[str]] = defaultdict(set)
        seed_symbols: set[str] = set()
        for rank, hit in enumerate(base_hits, start=1):
            idx = self._decl_key_to_idx.get(_decl_key(hit.declaration))
            if idx is None:
                continue
            base_rank_by_idx[idx] = rank
            score_by_idx[idx] += hit.score + 4.0 / rank
            symbols = self._decl_symbols[idx]
            seed_symbols.update(symbols)
            graph_symbols_by_idx[idx].update(symbols & set(hit.matched_terms))

        if not seed_symbols:
            return [
                FormalSourceGraphHit(
                    declaration=hit.declaration,
                    score=hit.score,
                    matched_terms=hit.matched_terms,
                    graph_symbols=(),
                    base_rank=rank,
                )
                for rank, hit in enumerate(base_hits[:k], start=1)
            ]

        # Keep expansion bounded and deterministic. High-degree generic symbols
        # such as `Measure` are still useful, but lower-degree symbols should
        # drive most of the graph lift.
        seed_order = sorted(seed_symbols, key=lambda symbol: (len(self._symbol_to_decl[symbol]), symbol))[:32]
        for symbol in seed_order:
            degree = len(self._symbol_to_decl[symbol])
            if degree == 0:
                continue
            symbol_weight = 1.0 / min(degree, 20)
            for idx in self._symbol_to_decl[symbol]:
                score_by_idx[idx] += symbol_weight
                graph_symbols_by_idx[idx].add(symbol)

        hits: list[FormalSourceGraphHit] = []
        for idx, score in score_by_idx.items():
            decl = self.declarations[idx]
            matched = tuple(sorted(self._decl_symbols[idx] & seed_symbols)[:16])
            graph_symbols = tuple(sorted(graph_symbols_by_idx[idx])[:16])
            hits.append(
                FormalSourceGraphHit(
                    declaration=decl,
                    score=score,
                    matched_terms=matched,
                    graph_symbols=graph_symbols,
                    base_rank=base_rank_by_idx.get(idx),
                )
            )
        return sorted(
            hits,
            key=lambda hit: (
                -hit.score,
                hit.base_rank if hit.base_rank is not None else 10_000,
                hit.declaration.source_id,
                hit.declaration.name,
            ),
        )[:k]


def audit_formal_source_graph(
    out_dir: Path | None = None,
    *,
    declarations: list[FormalDeclaration] | None = None,
    queries: tuple[tuple[str, str], ...] = DEFAULT_GRAPH_AUDIT_QUERIES,
    k: int = 8,
    cache_path: Path | str | None = None,
    refresh_cache: bool = False,
) -> dict[str, object]:
    decls = declarations if declarations is not None else build_formal_source_index()
    cache_info = _graph_cache_info(
        declarations=decls,
        queries=queries,
        k=k,
        cache_path=cache_path,
        refresh_cache=refresh_cache,
    )
    cached_payload = _load_cached_graph_payload(cache_info=cache_info)
    if cached_payload is not None:
        payload = _payload_with_cache_status(cached_payload, cache_info=cache_info, status="hit", stored=False)
        if out_dir is not None:
            _write_graph_outputs(payload, out_dir)
        return payload

    graph = FormalSourceGraphRetriever(decls)
    symbol_counts = Counter(symbol for symbols in graph._decl_symbols for symbol in symbols)
    source_by_symbol: dict[str, set[str]] = defaultdict(set)
    for decl, symbols in zip(decls, graph._decl_symbols, strict=True):
        for symbol in symbols:
            source_by_symbol[symbol].add(decl.source_id)
    cross_source_symbols = {
        symbol: sources for symbol, sources in source_by_symbol.items() if len(sources) >= 2
    }
    query_rows = []
    for query_id, text in queries:
        hits = graph.search(text, k=k)
        query_rows.append(
            {
                "query_id": query_id,
                "query": text,
                "n_hits": len(hits),
                "n_graph_expanded_hits": sum(1 for hit in hits if hit.base_rank is None),
                "top_hits": [_graph_hit_payload(hit) for hit in hits],
                "ok": bool(hits) and any(hit.graph_symbols for hit in hits),
            }
        )
    by_source = Counter(decl.source_id for decl in decls)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "n_declarations": len(decls),
        "n_symbol_nodes": graph.n_symbol_nodes,
        "n_edges": graph.n_edges,
        "n_cross_source_symbols": len(cross_source_symbols),
        "by_source": dict(sorted(by_source.items())),
        "top_symbols": [
            {"symbol": symbol, "degree": count}
            for symbol, count in symbol_counts.most_common(25)
        ],
        "top_cross_source_symbols": [
            {
                "symbol": symbol,
                "n_sources": len(sources),
                "sources": tuple(sorted(sources)),
                "degree": symbol_counts[symbol],
            }
            for symbol, sources in sorted(
                cross_source_symbols.items(),
                key=lambda item: (-symbol_counts[item[0]], item[0]),
            )[:25]
        ],
        "n_queries": len(query_rows),
        "n_query_ok": sum(1 for row in query_rows if row["ok"]),
        "all_queries_ok": all(row["ok"] for row in query_rows),
        "query_rows": query_rows,
    }
    cache_stored = False
    if cache_info["enabled"] and payload["all_queries_ok"]:
        payload = _payload_with_cache_status(payload, cache_info=cache_info, status="miss", stored=True)
        _store_cached_graph_payload(cache_info=cache_info, payload=payload)
        cache_stored = True
    if not cache_stored:
        payload = _payload_with_cache_status(
            payload,
            cache_info=cache_info,
            status="disabled" if not cache_info["enabled"] else "miss",
            stored=False,
        )
    if out_dir is not None:
        _write_graph_outputs(payload, out_dir)
    return payload


def _graph_cache_info(
    *,
    declarations: list[FormalDeclaration],
    queries: tuple[tuple[str, str], ...],
    k: int,
    cache_path: Path | str | None,
    refresh_cache: bool,
) -> dict[str, object]:
    root = Path(cache_path) if cache_path is not None else None
    key = _graph_cache_key(declarations=declarations, queries=queries, k=k)
    return {
        "enabled": root is not None,
        "root": root or Path(),
        "key": key,
        "entry": (root / key) if root is not None else Path(),
        "refresh": refresh_cache,
    }


def _graph_cache_key(
    *,
    declarations: list[FormalDeclaration],
    queries: tuple[tuple[str, str], ...],
    k: int,
) -> str:
    payload = {
        "cache_schema": 1,
        "formal_source_index_fingerprint": formal_source_index_fingerprint(declarations),
        "queries": queries,
        "k": k,
        "engine_fingerprint": _source_file_hash(Path(__file__)),
    }
    return stable_hash(payload)[:24]


def _source_file_hash(path: Path) -> str:
    return stable_hash(path.read_text(encoding="utf-8")) if path.exists() else ""


def _load_cached_graph_payload(*, cache_info: dict[str, object]) -> dict[str, object] | None:
    if not cache_info["enabled"] or cache_info["refresh"]:
        return None
    entry = Path(str(cache_info["entry"]))
    manifest_path = entry / "formal_source_graph_manifest.json"
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not payload.get("all_queries_ok"):
        return None
    return payload


def _store_cached_graph_payload(*, cache_info: dict[str, object], payload: dict[str, object]) -> None:
    if not cache_info["enabled"]:
        return
    entry = Path(str(cache_info["entry"]))
    if entry.exists():
        shutil.rmtree(entry)
    entry.mkdir(parents=True, exist_ok=True)
    (entry / "formal_source_graph_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (entry / "formal_source_graph.md").write_text(_markdown_report(payload), encoding="utf-8")


def _payload_with_cache_status(
    payload: dict[str, object],
    *,
    cache_info: dict[str, object],
    status: str,
    stored: bool,
) -> dict[str, object]:
    updated = dict(payload)
    updated["cache"] = {
        "enabled": bool(cache_info["enabled"]),
        "status": status,
        "cache_key": str(cache_info["key"]),
        "cache_dir": str(cache_info["root"]) if cache_info["enabled"] else "",
        "cache_entry": str(cache_info["entry"]) if cache_info["enabled"] else "",
        "stored": stored,
    }
    return updated


def _write_graph_outputs(payload: dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "formal_source_graph_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "formal_source_graph.md").write_text(_markdown_report(payload), encoding="utf-8")


def _symbols_for_declaration(decl: FormalDeclaration) -> set[str]:
    symbols = set()
    for raw in (
        *decl.premise_heads,
        decl.conclusion_head,
        decl.lhs_head,
        decl.rhs_head,
        *decl.major_symbols,
    ):
        symbol = str(raw).strip()
        if not symbol:
            continue
        symbols.add(symbol)
        symbols.add(symbol.lower())
    for module in decl.imports:
        for part in module.split("."):
            if len(part) >= 3:
                symbols.add(part)
                symbols.add(part.lower())
    name_tail = decl.name.split(".")[-1]
    for part in name_tail.replace("_", " ").split():
        if len(part) >= 3:
            symbols.add(part)
            symbols.add(part.lower())
    return symbols


def _decl_key(decl: FormalDeclaration) -> tuple[str, str, int, str]:
    return (decl.source_id, decl.path, decl.line, decl.name)


def _graph_hit_payload(hit: FormalSourceGraphHit) -> dict[str, object]:
    return {
        "source_id": hit.declaration.source_id,
        "path": hit.declaration.path,
        "line": hit.declaration.line,
        "kind": hit.declaration.kind,
        "name": hit.declaration.name,
        "namespace": hit.declaration.namespace,
        "signature": hit.declaration.signature,
        "reference": hit.declaration.reference,
        "reference_aliases": hit.declaration.reference_aliases,
        "module_summary": hit.declaration.module_summary,
        "score": hit.score,
        "matched_terms": hit.matched_terms,
        "graph_symbols": hit.graph_symbols,
        "base_rank": hit.base_rank,
        "binder_count": hit.declaration.binder_count,
        "premise_heads": hit.declaration.premise_heads,
        "conclusion_head": hit.declaration.conclusion_head,
        "lhs_head": hit.declaration.lhs_head,
        "rhs_head": hit.declaration.rhs_head,
        "imports": hit.declaration.imports,
    }


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Source Graph",
        "",
        f"- Declarations: {payload['n_declarations']}",
        f"- Symbol nodes: {payload['n_symbol_nodes']}",
        f"- Declaration-symbol edges: {payload['n_edges']}",
        f"- Cross-source symbols: {payload['n_cross_source_symbols']}",
        f"- Query coverage: {payload['n_query_ok']}/{payload['n_queries']}",
        f"- Cache: {dict(payload.get('cache', {})).get('status', 'unknown')}",
        "",
        "## Sources",
        "",
        "| Source | Declarations |",
        "|---|---:|",
    ]
    for source_id, count in dict(payload["by_source"]).items():
        lines.append(f"| `{source_id}` | {count} |")
    lines.extend(["", "## Top Cross-Source Symbols", "", "| Symbol | Sources | Degree |", "|---|---:|---:|"])
    for row in payload["top_cross_source_symbols"]:  # type: ignore[index]
        lines.append(f"| `{row['symbol']}` | {row['n_sources']} | {row['degree']} |")
    lines.extend(["", "## Graph Queries", "", "| Query | OK | Top declarations |", "|---|---:|---|"])
    for row in payload["query_rows"]:  # type: ignore[index]
        hits = row["top_hits"][:5]
        summary = "<br>".join(
            f"`{hit['name']}` ({hit['source_id']}:{hit['path']}:{hit['line']}; symbols={', '.join(hit['graph_symbols'][:4])})"
            for hit in hits
        )
        lines.append(f"| `{row['query_id']}` | {row['ok']} | {summary or 'none'} |")
    return "\n".join(lines) + "\n"
