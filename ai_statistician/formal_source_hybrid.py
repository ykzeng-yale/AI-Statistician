from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from math import sqrt

from .formal_source_graph import FormalSourceGraphRetriever
from .formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
    FormalSourceRetriever,
    FormalSourceSqliteIndex,
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
        for declaration in declarations:
            self._declarations_by_name[declaration.name].append(declaration)
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
            local_matches = self._declarations_by_name.get(hit.declaration.name, [])
            target_declarations = local_matches[:2]
            for declaration in target_declarations:
                key = _decl_key(declaration)
                by_key[key] = declaration
                score_by_key[key] += hit.score + 10.0 / rank
                matched_by_key[key].update(hit.matched_terms)
                matched_by_key[key].add("lean_rag_dependency_graph")

        for rank, hit in enumerate(dependency_hits, start=1):
            if hit.declaration.name in self._declarations_by_name:
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
        return [
            FormalSourceHit(row.declaration, row.score, row.matched_terms)
            for row in rows[:k]
        ]


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
        for declaration in declarations:
            self._declarations_by_name[declaration.name].append(declaration)

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
            local_matches = self._declarations_by_name.get(hit.declaration.name, ())
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
        return [
            FormalSourceHit(row.declaration, row.score, row.matched_terms)
            for row in rows[:k]
        ]


class FormalSourceSemanticHybridRetriever:
    """Opt-in local semantic reranker for paraphrase and typo-sensitive queries.

    This is deliberately dependency-free and ablation-gated. It is not an
    embedding model replacement; it gives the planner a reproducible local
    recall layer while external LeanSearch/LeanExplore-style providers remain
    separate evaluation arms.
    """

    semantic_provider_id = "local_char_ngram"

    def __init__(
        self,
        declarations: list[FormalDeclaration],
        base_retriever: object,
        *,
        candidate_multiplier: int = 8,
        semantic_weight: float = 6.0,
        semantic_min_score: float = 0.08,
    ) -> None:
        self.declarations = declarations
        self.base_retriever = base_retriever
        self.candidate_multiplier = max(1, int(candidate_multiplier))
        self.semantic_weight = max(0.0, float(semantic_weight))
        self.semantic_min_score = max(0.0, float(semantic_min_score))
        base_source = str(
            getattr(base_retriever, "source", base_retriever.__class__.__name__)
        )
        self.source = f"{base_source}+local_char_ngram_semantic"
        setattr(self, "semantic_rerank_enabled", True)
        setattr(self, "semantic_provider_id", self.semantic_provider_id)
        setattr(self, "semantic_candidate_multiplier", self.candidate_multiplier)
        setattr(self, "semantic_weight", self.semantic_weight)
        setattr(self, "semantic_min_score", self.semantic_min_score)
        for attr in (
            "cache_status",
            "cache_path",
            "lean_rag_dependency_graph_enabled",
            "lean_rag_dependency_graph_path",
            "lean_rag_dependency_graph_auto_discovered",
        ):
            if hasattr(base_retriever, attr):
                setattr(self, attr, getattr(base_retriever, attr))
        self._vectors = [
            (decl, _char_ngram_vector(_semantic_text(decl)))
            for decl in declarations
        ]

    def load_declarations(self) -> list[FormalDeclaration]:
        return list(self.declarations)

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        limit = max(1, int(k))
        candidate_k = max(limit * self.candidate_multiplier, limit)
        base_search = getattr(self.base_retriever, "search", None)
        try:
            base_hits = (
                list(base_search(query, k=candidate_k))
                if callable(base_search)
                else []
            )
        except Exception as exc:
            base_hits = []
            setattr(self, "last_base_search_error", f"{type(exc).__name__}: {exc}")

        query_vector = _char_ngram_vector(query)
        semantic_candidates: list[tuple[FormalDeclaration, float]] = []
        if query_vector and self.semantic_weight > 0.0:
            for declaration, vector in self._vectors:
                score = _cosine(query_vector, vector)
                if score >= self.semantic_min_score:
                    semantic_candidates.append((declaration, score))
        semantic_candidates.sort(key=lambda item: (-item[1], item[0].source_id, item[0].name))
        semantic_candidates = semantic_candidates[:candidate_k]

        by_key: dict[tuple[str, str, int, str], FormalDeclaration] = {}
        score_by_key: dict[tuple[str, str, int, str], float] = defaultdict(float)
        matched_by_key: dict[tuple[str, str, int, str], set[str]] = defaultdict(set)

        for rank, hit in enumerate(base_hits, start=1):
            key = _decl_key(hit.declaration)
            by_key[key] = hit.declaration
            score_by_key[key] += float(hit.score) + 10.0 / rank
            matched_by_key[key].update(hit.matched_terms)
            matched_by_key[key].add("base_retriever")

        for rank, (declaration, semantic_score) in enumerate(
            semantic_candidates,
            start=1,
        ):
            key = _decl_key(declaration)
            by_key[key] = declaration
            score_by_key[key] += semantic_score * self.semantic_weight + 4.0 / rank
            matched_by_key[key].add("local_char_ngram_semantic")
            matched_by_key[key].add(f"semantic_score_{semantic_score:.3f}")

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
            for row in rows[:limit]
        ]


def _decl_key(decl: FormalDeclaration) -> tuple[str, str, int, str]:
    return (decl.source_id, decl.path, decl.line, decl.name)


def _semantic_text(decl: FormalDeclaration) -> str:
    return " ".join(
        [
            decl.name,
            decl.kind,
            decl.namespace,
            decl.signature,
            decl.path,
            decl.source_id,
            decl.conclusion_head,
            decl.lhs_head,
            decl.rhs_head,
            " ".join(decl.premise_heads),
            " ".join(decl.major_symbols),
            " ".join(decl.imports),
        ]
    )


def _char_ngram_vector(text: str) -> dict[str, float]:
    normalized = " ".join(str(text or "").lower().replace("_", " ").split())
    if not normalized:
        return {}
    compact = f" {normalized} "
    counts: dict[str, float] = defaultdict(float)
    for n in (3, 4):
        if len(compact) < n:
            continue
        for index in range(0, len(compact) - n + 1):
            gram = compact[index : index + n]
            if gram.strip():
                counts[gram] += 1.0
    return dict(counts)


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot = sum(value * right.get(key, 0.0) for key, value in left.items())
    if dot <= 0.0:
        return 0.0
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    if left_norm <= 0.0 or right_norm <= 0.0:
        return 0.0
    return dot / (left_norm * right_norm)
