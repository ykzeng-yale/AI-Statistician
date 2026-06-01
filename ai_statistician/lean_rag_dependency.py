from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .formal_source_index import FormalDeclaration, FormalSourceHit


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


class LeanRagDependencyRetriever:
    """Adapter for the shared `lean_rag` SQLite dependency graph.

    The `EmpericalProcessLEAN/lean_rag` package builds a source-derived SQLite
    graph with declaration references, fan-in/fan-out, tactic usage, and
    FTS over declarations. This adapter lets AI-Statistician fuse that graph as
    an optional retrieval provider without vendoring generated indexes.
    """

    source = "lean_rag_dependency_graph"

    def __init__(self, db_path: Path | str, *, source_id: str = "lean_rag_dependency_graph") -> None:
        self.db_path = Path(db_path).expanduser()
        self.source_id = source_id

    def is_healthy(self) -> bool:
        if not self.db_path.exists():
            return False
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
                    ).fetchall()
                }
                return "declarations" in tables and (
                    "decl_fts" in tables or "decl_fts_plain" in tables
                )
        except sqlite3.DatabaseError:
            return False

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        if k <= 0 or not self.is_healthy():
            return []
        candidate_rows = self._search_fts(query, limit=max(k * 8, 40))
        if not candidate_rows:
            candidate_rows = self._search_like(query, limit=max(k * 8, 40))
        q_tokens = _tokens(query)
        hits = []
        for rank, row in enumerate(candidate_rows, start=1):
            hit = self._hit_for_row(row, q_tokens=q_tokens, rank=rank)
            if hit is not None:
                hits.append(hit)
        return sorted(hits, key=lambda hit: (-hit.score, hit.declaration.name))[:k]

    def dependency_context(self, declaration_name: str, *, limit: int = 8) -> LeanRagDependencyContext | None:
        if not self.is_healthy():
            return None
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id
                FROM declarations
                WHERE name = ? OR short_name = ?
                ORDER BY CASE WHEN name = ? THEN 0 ELSE 1 END, length(name), name
                LIMIT 1
                """,
                (declaration_name, declaration_name, declaration_name),
            ).fetchone()
            if row is None:
                return None
            decl_id = int(row["id"])
            fan_in, fan_out = _fan_counts(conn, decl_id)
            uses = _neighbor_names(conn, decl_id, direction="out", limit=limit)
            used_by = _neighbor_names(conn, decl_id, direction="in", limit=limit)
        return LeanRagDependencyContext(fan_in=fan_in, fan_out=fan_out, uses=uses, used_by=used_by)

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
            except sqlite3.OperationalError:
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
            + min(fan_in, 30) / 6.0
            + min(fan_out, 30) / 10.0
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


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'virtual table') AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token and token.lower() not in STOP_TOKENS and any(ch.isalnum() for ch in token)
    }


def _fts_query(text: str) -> str:
    tokens = [token for token in TOKEN_RE.findall(text) if re.match(r"^[A-Za-z0-9_]+$", token)]
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
) -> tuple[str, ...]:
    if direction == "out":
        rows = conn.execute(
            """
            SELECT dst.name
            FROM declaration_edges e
            JOIN declarations dst ON dst.id = e.dst_decl_id
            WHERE e.src_decl_id = ?
            ORDER BY e.scope, e.weight DESC, dst.name
            LIMIT ?
            """,
            (decl_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT src.name
            FROM declaration_edges e
            JOIN declarations src ON src.id = e.src_decl_id
            WHERE e.dst_decl_id = ?
            ORDER BY e.weight DESC, src.name
            LIMIT ?
            """,
            (decl_id, limit),
        ).fetchall()
    return tuple(str(row[0]) for row in rows)
