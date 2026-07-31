from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
    diversify_formal_source_hits,
)


TOKEN_RE = re.compile(r"[A-Za-z0-9_']+")
STOP_TOKENS = {
    "the",
    "a",
    "an",
    "of",
    "for",
    "and",
    "or",
    "is",
    "to",
    "by",
    "with",
    "theorem",
    "lemma",
    "def",
}


@dataclass(frozen=True)
class LeanRagDependencyContext:
    fan_in: int
    fan_out: int
    uses: tuple[str, ...]
    used_by: tuple[str, ...]
    statement_uses: tuple[str, ...] = ()
    proof_uses: tuple[str, ...] = ()
    source_id: str = ""
    db_path: str = ""
    module: str = ""
    direct_module_imports: tuple[str, ...] = ()
    module_import_visibility_enforced: bool = False
    dependency_resolution_policy: str = ""


class LeanRagDependencyRetriever:
    """Adapter for the shared `lean_rag` SQLite dependency graph.

    The `EmpericalProcessLEAN/lean_rag` package builds a source-derived SQLite
    graph with declaration references, fan-in/fan-out, tactic usage, and
    FTS over declarations. This adapter lets AI-Statistician fuse that graph as
    an optional retrieval provider without vendoring generated indexes.
    """

    source = "lean_rag_dependency_graph"

    def __init__(
        self,
        db_path: Path | str,
        *,
        source_id: str = "lean_rag_dependency_graph",
        source_aliases: tuple[str, ...] = (),
    ) -> None:
        self.db_path = Path(db_path).expanduser()
        self.source_id = source_id
        self.source_aliases = tuple(
            dict.fromkeys(
                value
                for value in (source_id, *source_aliases)
                if str(value).strip()
            )
        )
        self._health_cache: dict[str, object] | None = None

    @property
    def db_paths(self) -> tuple[Path, ...]:
        return (self.db_path,)

    @property
    def source_ids(self) -> tuple[str, ...]:
        return self.source_aliases

    def supports_source_id(self, source_id: str) -> bool:
        requested = str(source_id or "").strip()
        return (
            not requested
            or self.source_id == "lean_rag_dependency_graph"
            or requested in self.source_aliases
        )

    def is_healthy(self) -> bool:
        return bool(self.health_report().get("all_ok", False))

    def health_report(
        self,
        *,
        probe_query: str = "variance independent sum",
        refresh: bool = False,
    ) -> dict[str, object]:
        if self._health_cache is not None and not refresh:
            return dict(self._health_cache)
        report: dict[str, object] = {
            "db_path": str(self.db_path),
            "source_id": self.source_id,
            "source_aliases": self.source_aliases,
            "exists": self.db_path.exists(),
            "schema_has_declarations": False,
            "schema_has_decl_fts": False,
            "schema_has_decl_fts_plain": False,
            "n_declarations": 0,
            "n_decl_fts": 0,
            "integrity_check_ok": False,
            "integrity_check_result": "",
            "fts_probe_ok": False,
            "fts_probe_error": "",
            "like_probe_ok": False,
            "like_probe_error": "",
            "all_ok": False,
        }
        if not self.db_path.exists():
            return report
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
                    ).fetchall()
                }
                report["schema_has_declarations"] = "declarations" in tables
                report["schema_has_decl_fts"] = "decl_fts" in tables
                report["schema_has_decl_fts_plain"] = "decl_fts_plain" in tables
                if report["schema_has_declarations"]:
                    report["n_declarations"] = int(
                        conn.execute("SELECT COUNT(*) FROM declarations").fetchone()[0] or 0
                    )
                if report["schema_has_decl_fts"]:
                    report["n_decl_fts"] = int(
                        conn.execute("SELECT COUNT(*) FROM decl_fts").fetchone()[0] or 0
                    )
                integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0] or "")
                report["integrity_check_result"] = integrity
                report["integrity_check_ok"] = integrity.lower() == "ok"
        except sqlite3.DatabaseError as exc:
            report["integrity_check_result"] = f"{type(exc).__name__}: {exc}"
            return report

        if report["schema_has_decl_fts"]:
            try:
                fts_query = _fts_query(probe_query)
                if fts_query:
                    with closing(sqlite3.connect(self.db_path)) as conn:
                        conn.execute(
                            """
                            SELECT d.id
                            FROM decl_fts f
                            JOIN declarations d ON d.id = f.rowid
                            WHERE decl_fts MATCH ?
                            LIMIT 1
                            """,
                            (fts_query,),
                        ).fetchall()
                    report["fts_probe_ok"] = True
            except sqlite3.DatabaseError as exc:
                report["fts_probe_error"] = f"{type(exc).__name__}: {exc}"
        try:
            self._search_like(probe_query, limit=1)
            report["like_probe_ok"] = True
        except sqlite3.DatabaseError as exc:
            report["like_probe_error"] = f"{type(exc).__name__}: {exc}"
        search_probe_ok = (
            bool(report["fts_probe_ok"])
            if report["schema_has_decl_fts"]
            else bool(report["like_probe_ok"])
        )
        report["all_ok"] = bool(
            report["exists"]
            and report["schema_has_declarations"]
            and (report["schema_has_decl_fts"] or report["schema_has_decl_fts_plain"])
            and report["integrity_check_ok"]
            and search_probe_ok
        )
        self._health_cache = dict(report)
        return report

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        if k <= 0 or not self.is_healthy():
            return []
        try:
            candidate_rows = self._search_fts(query, limit=max(k * 8, 40))
        except sqlite3.DatabaseError:
            candidate_rows = []
        if not candidate_rows:
            try:
                candidate_rows = self._search_like(query, limit=max(k * 8, 40))
            except sqlite3.DatabaseError:
                candidate_rows = []
        q_tokens = _tokens(query)
        hits = []
        for rank, row in enumerate(candidate_rows, start=1):
            hit = self._hit_for_row(row, q_tokens=q_tokens, rank=rank)
            if hit is not None:
                hits.append(hit)
        return sorted(hits, key=lambda hit: (-hit.score, hit.declaration.name))[:k]

    def dependency_context(
        self,
        declaration_name: str,
        *,
        limit: int = 8,
        source_id: str = "",
        path: str = "",
    ) -> LeanRagDependencyContext | None:
        if not self.is_healthy() or not self.supports_source_id(source_id):
            return None
        normalized_path = str(path or "").replace("\\", "/").strip("/")
        short_name = declaration_name.rsplit(".", 1)[-1]
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                candidate_rows = conn.execute(
                    """
                    SELECT id, name, short_name, module, path, line_start
                    FROM declarations
                    WHERE name = ? OR short_name = ?
                    ORDER BY CASE WHEN name = ? THEN 0 ELSE 1 END,
                             length(name),
                             name
                    """,
                    (
                        declaration_name,
                        short_name,
                        declaration_name,
                    ),
                ).fetchall()
                row = _select_declaration_row(
                    candidate_rows,
                    declaration_name=declaration_name,
                    normalized_path=normalized_path,
                )
                if row is None:
                    return None
                decl_id = int(row["id"])
                module = str(row["module"] or "")
                line_start = int(row["line_start"] or 0)
                module_import_visibility_enforced = bool(
                    module and _table_exists(conn, "module_imports")
                )
                fan_in, fan_out = _fan_counts(conn, decl_id)
                direct_module_imports = _direct_local_module_imports(
                    conn,
                    module,
                )
                statement_uses = _neighbor_names(
                    conn,
                    decl_id,
                    direction="out",
                    limit=limit,
                    scopes=("statement", "mixed"),
                    module=module,
                    line_start=line_start,
                )
                proof_uses = _neighbor_names(
                    conn,
                    decl_id,
                    direction="out",
                    limit=limit,
                    scopes=("proof", "mixed"),
                    module=module,
                    line_start=line_start,
                )
                uses = tuple(
                    dict.fromkeys((*statement_uses, *proof_uses))
                )[:limit]
                used_by = _neighbor_names(
                    conn,
                    decl_id,
                    direction="in",
                    limit=limit,
                    module=module,
                    line_start=line_start,
                )
        except sqlite3.DatabaseError:
            return None
        return LeanRagDependencyContext(
            fan_in=fan_in,
            fan_out=fan_out,
            uses=uses,
            used_by=used_by,
            statement_uses=statement_uses,
            proof_uses=proof_uses,
            source_id=self.source_id,
            db_path=str(self.db_path),
            module=module,
            direct_module_imports=direct_module_imports,
            module_import_visibility_enforced=(
                module_import_visibility_enforced
            ),
            dependency_resolution_policy=(
                (
                    "Only declarations in the same earlier source region or in the "
                    "transitive local import closure are exposed as dependencies; "
                    "reverse users must occur later in the same module or import the "
                    "target module transitively."
                )
                if module_import_visibility_enforced
                else (
                    "Legacy dependency graph has no usable module-import relation; "
                    "neighbors are source-derived candidates without import-visibility "
                    "filtering and require active-project validation."
                )
            ),
        )

    def _search_fts(self, query: str, *, limit: int) -> list[sqlite3.Row]:
        fts_query = _fts_query(query)
        if not fts_query:
            return []
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "decl_fts"):
                return []
            try:
                return conn.execute(
                    """
                    SELECT d.id, d.name, d.short_name, d.kind, d.module, d.path,
                           d.line_start, d.line_end, d.namespace, d.signature,
                           d.proof, d.has_proof, d.has_sorry,
                           COALESCE((
                             SELECT sum(e.weight)
                             FROM declaration_edges e
                             WHERE e.dst_decl_id = d.id
                           ), 0) AS fan_in,
                           COALESCE((
                             SELECT sum(e.weight)
                             FROM declaration_edges e
                             WHERE e.src_decl_id = d.id
                           ), 0) AS fan_out
                    FROM decl_fts f
                    JOIN declarations d ON d.id = f.rowid
                    WHERE decl_fts MATCH ?
                    ORDER BY bm25(decl_fts)
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.DatabaseError:
                return []

    def _search_like(self, query: str, *, limit: int) -> list[sqlite3.Row]:
        tokens = _tokens(query)
        if not tokens:
            return []
        clauses = []
        params: list[object] = []
        for token in sorted(tokens)[:8]:
            clauses.append("(name LIKE ? OR signature LIKE ? OR proof LIKE ? OR module LIKE ?)")
            pattern = f"%{token}%"
            params.extend([pattern, pattern, pattern, pattern])
        params.append(limit)
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                return conn.execute(
                    f"""
                    SELECT id, name, short_name, kind, module, path, line_start,
                           line_end, namespace, signature, proof, has_proof,
                           has_sorry,
                           COALESCE((
                             SELECT sum(e.weight)
                             FROM declaration_edges e
                             WHERE e.dst_decl_id = declarations.id
                           ), 0) AS fan_in,
                           COALESCE((
                             SELECT sum(e.weight)
                             FROM declaration_edges e
                             WHERE e.src_decl_id = declarations.id
                           ), 0) AS fan_out
                    FROM declarations
                    WHERE {' OR '.join(clauses)}
                    ORDER BY has_sorry, length(name), name
                    LIMIT ?
                    """,
                    params,
                ).fetchall()
        except sqlite3.DatabaseError:
            return []

    def _hit_for_row(self, row: sqlite3.Row, *, q_tokens: set[str], rank: int) -> FormalSourceHit | None:
        signature = str(row["signature"] or "")
        proof = str(row["proof"] or "")
        name = str(row["name"] or "")
        text_tokens = _tokens(" ".join([name, signature, proof, str(row["module"] or ""), str(row["path"] or "")]))
        overlap = q_tokens & text_tokens
        if not overlap:
            return None
        fan_in = int(row["fan_in"] or 0)
        fan_out = int(row["fan_out"] or 0)
        score = (
            len(overlap)
            + 2.0 * len(q_tokens & _tokens(name))
            + min(fan_in, 10) / 20.0
            + min(fan_out, 10) / 40.0
            + 10.0 / rank
        )
        if int(row["has_sorry"] or 0):
            score -= 3.0
        declaration = FormalDeclaration(
            source_id=self.source_id,
            source_type="lean_rag_dependency_graph",
            path=str(row["path"] or ""),
            line=int(row["line_start"] or 0),
            kind=str(row["kind"] or ""),
            name=name,
            namespace=str(row["namespace"] or ""),
            signature=signature,
            binder_count=signature.count("(") + signature.count("{") + signature.count("["),
            conclusion_head=_conclusion_head(signature),
            major_symbols=tuple(sorted(text_tokens & _symbolish_tokens(signature, name))[:24]),
            imports=(),
        )
        matched_terms = tuple(
            sorted(overlap)[:16]
            + [
                "lean_rag_dependency_graph",
                f"fan_in={fan_in}",
                f"fan_out={fan_out}",
            ]
        )
        return FormalSourceHit(declaration=declaration, score=score, matched_terms=matched_terms)


class LeanRagDependencyMultiRetriever:
    """Fuse independent source-derived dependency graphs without merging DBs."""

    source = "lean_rag_dependency_graph_multi"

    def __init__(
        self,
        retrievers: tuple[LeanRagDependencyRetriever, ...],
    ) -> None:
        if not retrievers:
            raise ValueError("at least one dependency retriever is required")
        self.retrievers = tuple(retrievers)
        self.db_path = self.retrievers[0].db_path
        self.db_paths = tuple(retriever.db_path for retriever in self.retrievers)
        self.source_ids = tuple(
            dict.fromkeys(
                source_id
                for retriever in self.retrievers
                for source_id in retriever.source_ids
            )
        )
        self.auto_discovered = all(
            bool(getattr(retriever, "auto_discovered", False))
            for retriever in self.retrievers
        )

    def is_healthy(self) -> bool:
        return all(retriever.is_healthy() for retriever in self.retrievers)

    def health_report(self, *, refresh: bool = False) -> dict[str, object]:
        providers = [
            retriever.health_report(refresh=refresh)
            for retriever in self.retrievers
        ]
        return {
            "all_ok": bool(providers) and all(
                bool(provider.get("all_ok", False))
                for provider in providers
            ),
            "n_providers": len(providers),
            "db_paths": tuple(str(path) for path in self.db_paths),
            "source_ids": self.source_ids,
            "providers": providers,
        }

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        if k <= 0:
            return []
        by_key: dict[tuple[str, str, int, str], FormalSourceHit] = {}
        scores: dict[tuple[str, str, int, str], float] = {}
        matched: dict[tuple[str, str, int, str], set[str]] = {}
        for retriever in self.retrievers:
            for rank, hit in enumerate(
                retriever.search(query, k=max(k * 2, 10)),
                start=1,
            ):
                declaration = hit.declaration
                key = (
                    declaration.source_id,
                    declaration.path,
                    declaration.line,
                    declaration.name,
                )
                by_key[key] = hit
                scores[key] = scores.get(key, 0.0) + hit.score + 8.0 / rank
                matched.setdefault(key, set()).update(hit.matched_terms)
                matched[key].add(f"dependency_corpus={retriever.source_id}")
        ranked = [
            FormalSourceHit(
                declaration=hit.declaration,
                score=scores[key],
                matched_terms=tuple(sorted(matched[key])[:20]),
            )
            for key, hit in by_key.items()
        ]
        ranked.sort(
            key=lambda hit: (
                -hit.score,
                hit.declaration.source_id,
                hit.declaration.name,
            )
        )
        return diversify_formal_source_hits(
            ranked,
            k=k,
            min_relative_score=0.25,
        )

    def dependency_context(
        self,
        declaration_name: str,
        *,
        limit: int = 8,
        source_id: str = "",
        path: str = "",
    ) -> LeanRagDependencyContext | None:
        preferred = [
            retriever
            for retriever in self.retrievers
            if retriever.supports_source_id(source_id)
        ]
        candidates = preferred or list(self.retrievers)
        for retriever in candidates:
            context = retriever.dependency_context(
                declaration_name,
                limit=limit,
                source_id=source_id if retriever in preferred else "",
                path=path,
            )
            if context is not None:
                return context
        return None


def _select_declaration_row(
    rows: list[sqlite3.Row],
    *,
    declaration_name: str,
    normalized_path: str,
) -> sqlite3.Row | None:
    if not rows:
        return None
    exact = [
        row for row in rows
        if str(row["name"] or "") == declaration_name
    ]
    candidates = exact or rows
    if normalized_path:
        path_matches = [
            row
            for row in candidates
            if _source_paths_match(
                str(row["path"] or ""),
                normalized_path,
            )
        ]
        if len(path_matches) == 1:
            return path_matches[0]
    return candidates[0] if len(candidates) == 1 else None


def _source_paths_match(left: str, right: str) -> bool:
    normalized_left = str(left or "").replace("\\", "/").strip("/")
    normalized_right = str(right or "").replace("\\", "/").strip("/")
    return bool(
        normalized_left
        and normalized_right
        and (
            normalized_left == normalized_right
            or normalized_left.endswith("/" + normalized_right)
            or normalized_right.endswith("/" + normalized_left)
        )
    )


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'virtual table') AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _tokens(text: str) -> set[str]:
    split_text = re.sub(r"[_'.]", " ", text)
    camel_split = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        split_text,
    )
    return {
        token.lower()
        for token in TOKEN_RE.findall(
            " ".join((text, split_text, camel_split))
        )
        if (
            token
            and not token.isdigit()
            and token.lower() not in STOP_TOKENS
            and any(ch.isalnum() for ch in token)
        )
    }


def _fts_query(text: str) -> str:
    tokens = [
        token
        for token in TOKEN_RE.findall(text)
        if (
            not token.isdigit()
            and re.match(r"^[A-Za-z0-9_]+$", token)
            and token.lower() not in STOP_TOKENS
        )
    ]
    if not tokens:
        return ""
    return " OR ".join(f"{token}*" for token in tokens[:16])


def _symbolish_tokens(signature: str, name: str) -> set[str]:
    return {
        token
        for token in _tokens(" ".join([signature, name.replace("_", " ")]))
        if len(token) >= 3
    }


def _conclusion_head(signature: str) -> str:
    if ":" not in signature:
        return ""
    conclusion = signature.rsplit(":", 1)[-1].strip()
    match = TOKEN_RE.search(conclusion)
    return match.group(0) if match else ""


def _fan_counts(conn: sqlite3.Connection, decl_id: int) -> tuple[int, int]:
    fan_in = conn.execute(
        "SELECT COALESCE(sum(weight), 0) FROM declaration_edges WHERE dst_decl_id = ?",
        (decl_id,),
    ).fetchone()[0]
    fan_out = conn.execute(
        "SELECT COALESCE(sum(weight), 0) FROM declaration_edges WHERE src_decl_id = ?",
        (decl_id,),
    ).fetchone()[0]
    return int(fan_in or 0), int(fan_out or 0)


def _neighbor_names(
    conn: sqlite3.Connection,
    decl_id: int,
    *,
    direction: str,
    limit: int,
    scopes: tuple[str, ...] = (),
    module: str = "",
    line_start: int = 0,
) -> tuple[str, ...]:
    scope_clause = ""
    params: list[object] = [decl_id]
    if scopes:
        placeholders = ", ".join("?" for _ in scopes)
        scope_clause = f" AND e.scope IN ({placeholders})"
        params.extend(scopes)
    bounded_limit = max(0, int(limit))
    if bounded_limit <= 0:
        return ()
    import_filter_available = bool(
        module
        and _table_exists(conn, "module_imports")
    )
    if direction == "out":
        if import_filter_available:
            rows = conn.execute(
                f"""
                WITH RECURSIVE reachable(module) AS (
                  SELECT ?
                  UNION
                  SELECT mi.dst_module
                  FROM module_imports mi
                  JOIN reachable r ON mi.src_module = r.module
                  WHERE mi.is_local_dst = 1
                )
                SELECT dst.name
                FROM declaration_edges e
                JOIN declarations dst ON dst.id = e.dst_decl_id
                WHERE e.src_decl_id = ?
                  {scope_clause}
                  AND dst.module IN (SELECT module FROM reachable)
                  AND (dst.module != ? OR dst.line_start < ?)
                ORDER BY e.scope, e.weight DESC, dst.name
                LIMIT ?
                """,
                [
                    module,
                    decl_id,
                    *scopes,
                    module,
                    line_start,
                    bounded_limit,
                ],
            ).fetchall()
            return tuple(str(row[0]) for row in rows)
        params.append(bounded_limit)
        rows = conn.execute(
            f"""
            SELECT dst.name
            FROM declaration_edges e
            JOIN declarations dst ON dst.id = e.dst_decl_id
            WHERE e.src_decl_id = ?
              {scope_clause}
            ORDER BY e.scope, e.weight DESC, dst.name
            LIMIT ?
            """,
            params,
        ).fetchall()
    else:
        if import_filter_available:
            rows = conn.execute(
                f"""
                WITH RECURSIVE consumers(module) AS (
                  SELECT ?
                  UNION
                  SELECT mi.src_module
                  FROM module_imports mi
                  JOIN consumers c ON mi.dst_module = c.module
                  WHERE mi.is_local_dst = 1
                )
                SELECT src.name
                FROM declaration_edges e
                JOIN declarations src ON src.id = e.src_decl_id
                WHERE e.dst_decl_id = ?
                  {scope_clause}
                  AND src.module IN (SELECT module FROM consumers)
                  AND (src.module != ? OR src.line_start > ?)
                ORDER BY e.weight DESC, src.name
                LIMIT ?
                """,
                [
                    module,
                    decl_id,
                    *scopes,
                    module,
                    line_start,
                    bounded_limit,
                ],
            ).fetchall()
            return tuple(str(row[0]) for row in rows)
        params.append(bounded_limit)
        rows = conn.execute(
            f"""
            SELECT src.name
            FROM declaration_edges e
            JOIN declarations src ON src.id = e.src_decl_id
            WHERE e.dst_decl_id = ?
              {scope_clause}
            ORDER BY e.weight DESC, src.name
            LIMIT ?
            """,
            params,
        ).fetchall()
    return tuple(str(row[0]) for row in rows)


def _direct_local_module_imports(
    conn: sqlite3.Connection,
    module: str,
) -> tuple[str, ...]:
    if not module or not _table_exists(conn, "module_imports"):
        return ()
    rows = conn.execute(
        """
        SELECT DISTINCT dst_module
        FROM module_imports
        WHERE src_module = ?
          AND is_local_dst = 1
        ORDER BY dst_module
        """,
        (module,),
    ).fetchall()
    return tuple(str(row[0]) for row in rows)
