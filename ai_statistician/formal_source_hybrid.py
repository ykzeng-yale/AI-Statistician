from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Mapping

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
        scoped_premise_retrievers: tuple[object, ...] = (),
    ) -> None:
        self.declarations = declarations
        self.sqlite_index = sqlite_index
        self.dependency_retriever = dependency_retriever
        self.scoped_premise_retrievers = tuple(scoped_premise_retrievers)
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

    def descriptor(self) -> dict[str, object]:
        return _formal_source_hybrid_descriptor(self)

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        return self._search(query, k=k, source_scope_ids=())

    def search_with_source_scope(
        self,
        query: str,
        *,
        source_scope_ids: tuple[str, ...],
        k: int = 10,
    ) -> list[FormalSourceHit]:
        return self._search(
            query,
            k=k,
            source_scope_ids=source_scope_ids,
        )

    def _search(
        self,
        query: str,
        *,
        k: int,
        source_scope_ids: tuple[str, ...],
    ) -> list[FormalSourceHit]:
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
        scoped_premise_hits = _search_scoped_premise_retrievers(
            self.scoped_premise_retrievers,
            query=query,
            base_hits=sqlite_hits,
            source_scope_ids=source_scope_ids,
            k=max(k * 2, 10),
        )

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

        for rank, hit in scoped_premise_hits:
            local_matches = _local_declarations_for_scoped_premise_hit(
                hit.declaration,
                by_name=self._declarations_by_name,
            )
            target_declarations = local_matches[:1] or [hit.declaration]
            for declaration in target_declarations:
                key = _decl_key(declaration)
                by_key[key] = declaration
                score_by_key[key] += hit.score + 4.0 / rank
                matched_by_key[key].update(hit.matched_terms)
                matched_by_key[key].add("source_scoped_premise_corpus")

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
        dependency_retriever: object | None,
        *,
        scoped_premise_retrievers: tuple[object, ...] = (),
    ) -> None:
        self.declarations = declarations
        self.base_retriever = base_retriever
        self.dependency_retriever = dependency_retriever
        self.scoped_premise_retrievers = tuple(scoped_premise_retrievers)
        setattr(
            self,
            "lean_rag_dependency_graph_enabled",
            dependency_retriever is not None,
        )
        setattr(
            self,
            "lean_rag_dependency_graph_path",
            str(getattr(dependency_retriever, "db_path", ""))
            if dependency_retriever is not None
            else "",
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

    def descriptor(self) -> dict[str, object]:
        return _formal_source_hybrid_descriptor(self)

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        return self._search(query, k=k, source_scope_ids=())

    def search_with_source_scope(
        self,
        query: str,
        *,
        source_scope_ids: tuple[str, ...],
        k: int = 10,
    ) -> list[FormalSourceHit]:
        return self._search(
            query,
            k=k,
            source_scope_ids=source_scope_ids,
        )

    def _search(
        self,
        query: str,
        *,
        k: int,
        source_scope_ids: tuple[str, ...],
    ) -> list[FormalSourceHit]:
        base_search = getattr(self.base_retriever, "search", None)
        base_hits = base_search(query, k=max(k * 3, 10)) if callable(base_search) else []
        dependency_search = getattr(self.dependency_retriever, "search", None)
        dependency_hits = dependency_search(query, k=max(k * 2, 10)) if callable(dependency_search) else []
        scoped_premise_hits = _search_scoped_premise_retrievers(
            self.scoped_premise_retrievers,
            query=query,
            base_hits=base_hits,
            source_scope_ids=source_scope_ids,
            k=max(k * 2, 10),
        )

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

        for rank, hit in scoped_premise_hits:
            local_matches = _local_declarations_for_scoped_premise_hit(
                hit.declaration,
                by_name=self._declarations_by_name,
            )
            target_declarations = local_matches[:1] or [hit.declaration]
            for declaration in target_declarations:
                key = _decl_key(declaration)
                by_key[key] = declaration
                score_by_key[key] += hit.score + 4.0 / rank
                matched_by_key[key].update(hit.matched_terms)
                matched_by_key[key].add("source_scoped_premise_corpus")

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


def _formal_source_hybrid_descriptor(retriever: object) -> dict[str, object]:
    """Expose the real declaration, graph, and scoped-corpus topology."""

    declarations = tuple(getattr(retriever, "declarations", ()) or ())
    source_counts = Counter(
        str(row.source_id)
        for row in declarations
        if str(getattr(row, "source_id", "") or "")
    )
    dependency_provider = getattr(retriever, "dependency_retriever", None)
    dependency_source_ids = tuple(
        str(value)
        for value in (
            getattr(
                retriever,
                "lean_rag_dependency_graph_source_ids",
                (),
            )
            or getattr(dependency_provider, "source_ids", ())
            or ()
        )
        if str(value)
    )
    dependency_health = dict(
        getattr(retriever, "lean_rag_dependency_graph_health", {}) or {}
    )
    dependency_health_loader = getattr(
        dependency_provider,
        "health_report",
        None,
    )
    if not dependency_health and callable(dependency_health_loader):
        try:
            dependency_health = dict(dependency_health_loader() or {})
        except Exception:
            dependency_health = {}
    dependency_health = _compact_dependency_health(dependency_health)
    scoped_providers = tuple(
        getattr(retriever, "scoped_premise_retrievers", ()) or ()
    )
    scoped_health = tuple(
        _compact_scoped_corpus_health(row)
        for row in (
            getattr(retriever, "scoped_premise_corpus_health", ()) or ()
        )
        if isinstance(row, Mapping)
    )
    if not scoped_health:
        health_rows: list[dict[str, object]] = []
        for provider in scoped_providers:
            health_loader = getattr(provider, "health_report", None)
            if not callable(health_loader):
                continue
            try:
                health_rows.append(
                    _compact_scoped_corpus_health(health_loader() or {})
                )
            except Exception:
                continue
        scoped_health = tuple(health_rows)
    scoped_source_ids = tuple(
        str(value)
        for value in (
            getattr(retriever, "scoped_premise_corpus_source_ids", ())
            or tuple(
                getattr(provider, "source_id", "")
                for provider in scoped_providers
            )
        )
        if str(value)
    )
    scoped_anchor_source_ids = tuple(
        dict.fromkeys(
            str(value)
            for value in (
                getattr(
                    retriever,
                    "scoped_premise_corpus_anchor_source_ids",
                    (),
                )
                or tuple(
                    source_id
                    for provider in scoped_providers
                    for source_id in (
                        getattr(provider, "anchor_source_ids", ()) or ()
                    )
                )
            )
            if str(value)
        )
    )
    return {
        "name": type(retriever).__name__,
        "type": f"{type(retriever).__module__}.{type(retriever).__name__}",
        "retrieval_backend": str(getattr(retriever, "source", "") or ""),
        "n_declarations": len(declarations),
        "declarations_by_source_id": dict(sorted(source_counts.items())),
        "source_scoped_search": callable(
            getattr(retriever, "search_with_source_scope", None)
        ),
        "declaration_outline_context": True,
        "dependency_context": callable(
            getattr(
                getattr(retriever, "dependency_retriever", None),
                "dependency_context",
                None,
            )
        ),
        "lean_rag_dependency_graph": {
            "enabled": bool(
                getattr(
                    retriever,
                    "lean_rag_dependency_graph_enabled",
                    False,
                )
            ),
            "provider_count": int(
                dependency_health.get("n_providers", 0) or 0
            )
            or len(dependency_health.get("providers", []) or [])
            or int(dependency_provider is not None),
            "source_ids": dependency_source_ids,
            "auto_discovered": bool(
                getattr(
                    retriever,
                    "lean_rag_dependency_graph_auto_discovered",
                    False,
                )
            ),
            "health": dependency_health,
        },
        "source_scoped_premise_corpora": {
            "enabled": bool(
                getattr(retriever, "scoped_premise_corpus_enabled", False)
                or scoped_providers
            ),
            "source_ids": scoped_source_ids,
            "anchor_source_ids": scoped_anchor_source_ids,
            "health": scoped_health,
        },
        "prompt_content_policy": (
            "qualified declaration signatures and dependency-first outlines; "
            "generic RAG omits proof bodies"
        ),
        "proof_evidence_status": (
            "FORMAL_SOURCE_RETRIEVAL_TOPOLOGY_NOT_PROOF_EVIDENCE"
        ),
    }


def _compact_dependency_health(value: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "all_ok",
        "n_providers",
        "source_id",
        "source_aliases",
        "n_declarations",
        "integrity_check_ok",
        "source_snapshot_status",
        "source_snapshot_bound",
        "source_snapshot_match",
        "graph_schema_version",
    )
    compact = {field: value[field] for field in fields if field in value}
    metadata = value.get("source_snapshot_metadata", {})
    if isinstance(metadata, Mapping):
        metadata_fields = (
            "schema_version",
            "source_git_commit",
            "source_git_tree",
            "source_git_dirty",
            "source_git_remote",
            "lean_toolchain",
            "mathlib_revision",
        )
        compact_metadata = {
            field: metadata[field] for field in metadata_fields if field in metadata
        }
        if compact_metadata:
            compact["source_snapshot_metadata"] = compact_metadata
    providers = value.get("providers", [])
    if isinstance(providers, (list, tuple)):
        compact_providers = [
            _compact_dependency_health(row)
            for row in providers
            if isinstance(row, Mapping)
        ]
        if compact_providers:
            compact["providers"] = compact_providers
    return compact


def _compact_scoped_corpus_health(value: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "source_id",
        "anchor_source_ids",
        "dataset_id",
        "dataset_revision",
        "corpus_sha256",
        "expected_sha256",
        "checksum_ok",
        "toolchain",
        "mathlib_revision",
        "n_files",
        "n_declarations",
        "all_ok",
        "prompt_content_policy",
        "proof_evidence_status",
    )
    return {field: value[field] for field in fields if field in value}


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


def _search_scoped_premise_retrievers(
    retrievers: tuple[object, ...],
    *,
    query: str,
    base_hits: list[FormalSourceHit],
    source_scope_ids: tuple[str, ...],
    k: int,
) -> list[tuple[int, FormalSourceHit]]:
    requested_scopes = {
        str(value).strip()
        for value in source_scope_ids
        if str(value).strip()
    }
    if not requested_scopes and base_hits:
        requested_scopes.add(base_hits[0].declaration.source_id)
    rows: list[tuple[int, FormalSourceHit]] = []
    for retriever in retrievers:
        supports = getattr(retriever, "supports_anchor_source_id", None)
        if not callable(supports) or not any(
            supports(source_id)
            for source_id in requested_scopes
        ):
            continue
        search = getattr(retriever, "search", None)
        if not callable(search):
            continue
        for rank, hit in enumerate(search(query, k=k), start=1):
            rows.append((rank, hit))
    return rows


def _local_declarations_for_scoped_premise_hit(
    declaration: FormalDeclaration,
    *,
    by_name: dict[str, list[FormalDeclaration]],
) -> list[FormalDeclaration]:
    exact = list(by_name.get(declaration.name, []))
    if len(exact) <= 1:
        return exact
    normalized_path = declaration.path.replace("\\", "/").strip("/")
    path_matches = [
        row
        for row in exact
        if (
            row.path.replace("\\", "/").strip("/").endswith(normalized_path)
            or normalized_path.endswith(
                row.path.replace("\\", "/").strip("/")
            )
        )
    ]
    if len(path_matches) == 1:
        return path_matches
    return []
