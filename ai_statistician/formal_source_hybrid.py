from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass

from .formal_source_graph import FormalSourceGraphRetriever
from .formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
    FormalSourceRetriever,
    FormalSourceSqliteIndex,
    diversify_formal_source_hits,
)


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

    def __init__(
        self,
        declarations: list[FormalDeclaration],
        sqlite_index: FormalSourceSqliteIndex,
        *,
        dependency_retriever: object | None = None,
    ) -> None:
        self.declarations = declarations
        self.sqlite_index = sqlite_index
        self.dependency_retriever = dependency_retriever
        self.fallback_retriever = FormalSourceRetriever(declarations)
        setattr(self, "lean_rag_dependency_graph_enabled", dependency_retriever is not None)
        setattr(
            self,
            "lean_rag_dependency_graph_path",
            str(getattr(dependency_retriever, "db_path", "")) if dependency_retriever is not None else "",
        )
        setattr(
            self,
            "lean_rag_dependency_graph_auto_discovered",
            bool(getattr(dependency_retriever, "auto_discovered", False))
            if dependency_retriever is not None
            else False,
        )
        self._declarations_by_name: dict[str, list[FormalDeclaration]] = defaultdict(list)
        self._declarations_by_short_name: dict[str, list[FormalDeclaration]] = defaultdict(list)
        for declaration in declarations:
            self._declarations_by_name[declaration.name].append(declaration)
            self._declarations_by_short_name[
                declaration.name.rsplit(".", 1)[-1]
            ].append(declaration)
        self.graph_retriever = FormalSourceGraphRetriever(
            declarations,
            base_retriever=sqlite_index,
        )

    def load_declarations(self) -> list[FormalDeclaration]:
        return list(self.declarations)

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        sqlite_candidate_k = max(k * 5, 20)
        try:
            sqlite_hits = self.sqlite_index.search(query, k=sqlite_candidate_k)
            sqlite_error = ""
        except sqlite3.DatabaseError as exc:
            sqlite_hits = self.fallback_retriever.search(query, k=sqlite_candidate_k)
            sqlite_error = f"{type(exc).__name__}: {exc}"
            setattr(self, "last_sqlite_search_error", sqlite_error)
        # The graph retriever expands its own seeds internally. Keep this leg
        # to top-level gap lookups; primitive-level searches ask for k=3 in the
        # research loop and should stay on the faster FTS/shape path.
        try:
            graph_hits = (
                self.graph_retriever.search(query, k=max(k * 2, 10))
                if k >= 5 and not sqlite_error
                else []
            )
        except sqlite3.DatabaseError as exc:
            graph_hits = []
            setattr(self, "last_graph_search_error", f"{type(exc).__name__}: {exc}")
        dependency_hits = []
        if self.dependency_retriever is not None:
            search = getattr(self.dependency_retriever, "search", None)
            if callable(search):
                dependency_hits = search(query, k=max(k * 2, 10))

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

        for rank, hit in enumerate(dependency_hits, start=1):
            local_matches = _local_declarations_for_dependency_hit(
                hit.declaration.name,
                by_name=self._declarations_by_name,
                by_short_name=self._declarations_by_short_name,
            )
            target_declarations = local_matches[:2]
            for declaration in target_declarations:
                key = _decl_key(declaration)
                by_key[key] = declaration
                score_by_key[key] += hit.score + 10.0 / rank
                matched_by_key[key].update(hit.matched_terms)
                matched_by_key[key].add("lean_rag_dependency_graph")

        for rank, hit in enumerate(dependency_hits, start=1):
            if _local_declarations_for_dependency_hit(
                hit.declaration.name,
                by_name=self._declarations_by_name,
                by_short_name=self._declarations_by_short_name,
            ):
                continue
            key = _decl_key(hit.declaration)
            by_key[key] = hit.declaration
            score_by_key[key] += hit.score + 10.0 / rank
            matched_by_key[key].update(hit.matched_terms)
            matched_by_key[key].add("lean_rag_dependency_graph")

        rows = [
            _AccumulatedHit(
                declaration=decl,
                score=score_by_key[key],
                matched_terms=tuple(sorted(matched_by_key[key])[:20]),
            )
            for key, decl in by_key.items()
        ]
        rows.sort(key=lambda row: (-row.score, row.declaration.source_id, row.declaration.name))
        hits = [
            FormalSourceHit(row.declaration, row.score, row.matched_terms)
            for row in rows
        ]
        # Symbol-graph support can multiply a declaration's fused score. Use a
        # wider relevance window so an independently strong source is not hidden
        # solely because one corpus received several graph-support legs.
        return diversify_formal_source_hits(
            hits,
            k=k,
            min_relative_score=0.35,
            preserve_top_n=2,
        )


class FormalSourceDependencyHybridRetriever:
    """Fuse any local declaration retriever with the lean_rag dependency graph.

    The production retriever uses SQLite FTS plus symbol-graph expansion. Some
    smoke tests and fallback paths intentionally use the lighter in-memory
    shape retriever. This adapter keeps the dependency-graph provider active in
    those paths too, so an available lean_rag DB is not silently ignored just
    because the local declaration candidate generator is not SQLite-backed.
    """

    source = "python_shape+lean_rag_dependency"

    def __init__(
        self,
        declarations: list[FormalDeclaration],
        base_retriever: object,
        dependency_retriever: object,
    ) -> None:
        self.declarations = declarations
        self.base_retriever = base_retriever
        self.dependency_retriever = dependency_retriever
        setattr(self, "lean_rag_dependency_graph_enabled", True)
        setattr(
            self,
            "lean_rag_dependency_graph_path",
            str(getattr(dependency_retriever, "db_path", "")),
        )
        setattr(
            self,
            "lean_rag_dependency_graph_auto_discovered",
            bool(getattr(dependency_retriever, "auto_discovered", False)),
        )
        self._declarations_by_name: dict[str, list[FormalDeclaration]] = defaultdict(list)
        self._declarations_by_short_name: dict[str, list[FormalDeclaration]] = defaultdict(list)
        for declaration in declarations:
            self._declarations_by_name[declaration.name].append(declaration)
            self._declarations_by_short_name[
                declaration.name.rsplit(".", 1)[-1]
            ].append(declaration)

    def load_declarations(self) -> list[FormalDeclaration]:
        return list(self.declarations)

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        base_search = getattr(self.base_retriever, "search", None)
        base_hits = base_search(query, k=max(k * 3, 10)) if callable(base_search) else []
        dependency_search = getattr(self.dependency_retriever, "search", None)
        dependency_hits = dependency_search(query, k=max(k * 2, 10)) if callable(dependency_search) else []

        by_key: dict[tuple[str, str, int, str], FormalDeclaration] = {}
        score_by_key: dict[tuple[str, str, int, str], float] = defaultdict(float)
        matched_by_key: dict[tuple[str, str, int, str], set[str]] = defaultdict(set)

        for rank, hit in enumerate(base_hits, start=1):
            key = _decl_key(hit.declaration)
            by_key[key] = hit.declaration
            score_by_key[key] += hit.score + 8.0 / rank
            matched_by_key[key].update(hit.matched_terms)
            matched_by_key[key].add("python_shape")

        for rank, hit in enumerate(dependency_hits, start=1):
            local_matches = _local_declarations_for_dependency_hit(
                hit.declaration.name,
                by_name=self._declarations_by_name,
                by_short_name=self._declarations_by_short_name,
            )
            if local_matches:
                for declaration in local_matches[:2]:
                    key = _decl_key(declaration)
                    by_key[key] = declaration
                    score_by_key[key] += hit.score + 10.0 / rank
                    matched_by_key[key].update(hit.matched_terms)
                    matched_by_key[key].add("lean_rag_dependency_graph")
                continue
            key = _decl_key(hit.declaration)
            by_key[key] = hit.declaration
            score_by_key[key] += hit.score + 10.0 / rank
            matched_by_key[key].update(hit.matched_terms)
            matched_by_key[key].add("lean_rag_dependency_graph")

        rows = [
            _AccumulatedHit(
                declaration=decl,
                score=score_by_key[key],
                matched_terms=tuple(sorted(matched_by_key[key])[:20]),
            )
            for key, decl in by_key.items()
        ]
        rows.sort(key=lambda row: (-row.score, row.declaration.source_id, row.declaration.name))
        hits = [
            FormalSourceHit(row.declaration, row.score, row.matched_terms)
            for row in rows
        ]
        return diversify_formal_source_hits(
            hits,
            k=k,
            preserve_top_n=2,
        )


def _decl_key(decl: FormalDeclaration) -> tuple[str, str, int, str]:
    return (decl.source_id, decl.path, decl.line, decl.name)


def _local_declarations_for_dependency_hit(
    declaration_name: str,
    *,
    by_name: dict[str, list[FormalDeclaration]],
    by_short_name: dict[str, list[FormalDeclaration]],
) -> list[FormalDeclaration]:
    exact = by_name.get(declaration_name, [])
    if exact:
        return exact
    short_matches = by_short_name.get(
        declaration_name.rsplit(".", 1)[-1],
        [],
    )
    return short_matches if len(short_matches) == 1 else []
