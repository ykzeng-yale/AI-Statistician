from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .formal_source_graph import FormalSourceGraphRetriever
from .formal_source_index import FormalDeclaration, FormalSourceHit, FormalSourceSqliteIndex


@dataclass(frozen=True)
class _AccumulatedHit:
    declaration: FormalDeclaration
    score: float
    matched_terms: tuple[str, ...]


class FormalSourceHybridRetriever:
    """Fuse SQLite FTS/Lean-shape retrieval with declaration-symbol graph RAG.

    The SQLite backend is the fast candidate generator for repeated theorem
    mining. The graph backend expands those candidates through compressed Lean
    symbols such as `variance`, `IndepFun`, `limsup`, or `Rademacher`. Returning
    ordinary `FormalSourceHit` rows keeps the rest of the research pipeline
    unchanged while making the stronger retrieval path the default.
    """

    source = "sqlite_fts_shape+symbol_graph"

    def __init__(self, declarations: list[FormalDeclaration], sqlite_index: FormalSourceSqliteIndex) -> None:
        self.declarations = declarations
        self.sqlite_index = sqlite_index
        self.graph_retriever = FormalSourceGraphRetriever(
            declarations,
            base_retriever=sqlite_index,
        )

    def load_declarations(self) -> list[FormalDeclaration]:
        return list(self.declarations)

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        sqlite_candidate_k = max(k * 5, 20)
        sqlite_hits = self.sqlite_index.search(query, k=sqlite_candidate_k)
        # The graph retriever expands its own seeds internally. Keep this leg
        # to top-level gap lookups; primitive-level searches ask for k=3 in the
        # research loop and should stay on the faster FTS/shape path.
        graph_hits = self.graph_retriever.search(query, k=max(k * 2, 10)) if k >= 5 else []

        by_key: dict[tuple[str, str, int, str], FormalDeclaration] = {}
        score_by_key: dict[tuple[str, str, int, str], float] = defaultdict(float)
        matched_by_key: dict[tuple[str, str, int, str], set[str]] = defaultdict(set)

        for rank, hit in enumerate(sqlite_hits, start=1):
            key = _decl_key(hit.declaration)
            by_key[key] = hit.declaration
            score_by_key[key] += hit.score + 12.0 / rank
            matched_by_key[key].update(hit.matched_terms)
            matched_by_key[key].add("sqlite_fts")

        for rank, hit in enumerate(graph_hits, start=1):
            key = _decl_key(hit.declaration)
            by_key[key] = hit.declaration
            score_by_key[key] += hit.score + 8.0 / rank
            matched_by_key[key].update(hit.matched_terms)
            matched_by_key[key].update(hit.graph_symbols[:8])
            matched_by_key[key].add("symbol_graph")

        rows = [
            _AccumulatedHit(
                declaration=decl,
                score=score_by_key[key],
                matched_terms=tuple(sorted(matched_by_key[key])[:20]),
            )
            for key, decl in by_key.items()
        ]
        rows.sort(key=lambda row: (-row.score, row.declaration.source_id, row.declaration.name))
        return [
            FormalSourceHit(row.declaration, row.score, row.matched_terms)
            for row in rows[:k]
        ]


def _decl_key(decl: FormalDeclaration) -> tuple[str, str, int, str]:
    return (decl.source_id, decl.path, decl.line, decl.name)
