from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .research_source_inventory import SOURCE_INVENTORY_TARGETS


DECL_RE = re.compile(
    r"^\s*(?:@[^\n]*\s*)*"
    r"(?:(?:private|protected|nonrec|noncomputable|unsafe)\s+)*"
    r"(theorem|lemma|def|abbrev|structure|class|inductive)\s+"
    r"([A-Za-z_][A-Za-z0-9_'.]*)"
)
NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z_][A-Za-z0-9_'.]*)\b")
END_RE = re.compile(r"^\s*end(?:\s+([A-Za-z_][A-Za-z0-9_'.]*))?\b")
IMPORT_RE = re.compile(r"^\s*import\s+(.+)$")
TOKEN_RE = re.compile(r"[\w'.]+|[∀∃∧∨→↔=≤≥<>+*/^.-]+", re.UNICODE)
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
    ".",
    ",",
    "-",
    "/",
    "=",
}
SKIPPED_PATH_PARTS = {
    ".git",
    ".lake",
    ".codex_backups",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "WDSM Project Original Doc",
    "Theory Development",
    "Asymtotic Properties Related Literature",
    "Markdown Trans",
}
DEFAULT_LEAN_RAG_DB_RELATIVE_PATH = Path(
    "runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite"
)
# Tests and downstream orchestration can prepend project-specific candidates
# without changing the global auto-discovery rule.
DEFAULT_LEAN_RAG_DB_CANDIDATES: tuple[Path, ...] = ()


@dataclass(frozen=True)
class FormalSourceRoot:
    id: str
    location: str
    source_type: str = "lean_library"


@dataclass(frozen=True)
class FormalDeclaration:
    source_id: str
    source_type: str
    path: str
    line: int
    kind: str
    name: str
    namespace: str
    signature: str
    binder_count: int = 0
    premise_heads: tuple[str, ...] = ()
    conclusion_head: str = ""
    lhs_head: str = ""
    rhs_head: str = ""
    major_symbols: tuple[str, ...] = ()
    imports: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormalSourceHit:
    declaration: FormalDeclaration
    score: float
    matched_terms: tuple[str, ...]


class FormalSourceRetriever:
    """Reusable declaration retriever with pre-tokenized Lean source rows."""

    def __init__(self, declarations: list[FormalDeclaration] | None = None) -> None:
        self.declarations = declarations if declarations is not None else build_formal_source_index()
        self._rows = [
            (
                decl,
                _search_tokens(
                    " ".join(
                        [
                            decl.name,
                            decl.kind,
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
                ),
                _search_tokens(decl.name),
                _search_tokens(
                    " ".join([decl.conclusion_head, decl.lhs_head, decl.rhs_head, " ".join(decl.premise_heads)])
                ),
                _search_tokens(" ".join(decl.imports)),
            )
            for decl in self.declarations
        ]

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        q_tokens = _search_tokens(query)
        hits: list[FormalSourceHit] = []
        for decl, d_tokens, name_tokens, shape_tokens, import_tokens in self._rows:
            hit = _score_declaration(
                decl,
                q_tokens,
                declaration_tokens=d_tokens,
                name_tokens=name_tokens,
                shape_tokens=shape_tokens,
                import_tokens=import_tokens,
            )
            if hit is not None:
                hits.append(hit)
        return sorted(hits, key=lambda hit: (-hit.score, hit.declaration.source_id, hit.declaration.name))[:k]


class FormalSourceSqliteIndex:
    """SQLite FTS-backed declaration retriever.

    This is the persistent/local-first backend for repeated theorem-mining
    queries. The Python retriever remains useful for tests and tiny ad hoc
    indexes; the SQLite backend avoids rescanning tens of thousands of Lean
    declarations for every audit or interactive search session.
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)

    @classmethod
    def build(cls, declarations: list[FormalDeclaration], db_path: Path | str) -> "FormalSourceSqliteIndex":
        index = cls(db_path)
        index.write(declarations)
        return index

    def is_healthy(self) -> bool:
        """Return whether this database has both row storage and FTS tables."""

        if not self.db_path.exists():
            return False
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        """
                        SELECT name
                        FROM sqlite_master
                        WHERE type IN ('table', 'virtual table')
                        """
                    ).fetchall()
                }
                if "declarations" not in tables or "declarations_fts" not in tables:
                    return False
                conn.execute("SELECT COUNT(*) FROM declarations").fetchone()
                conn.execute("SELECT COUNT(*) FROM declarations_fts").fetchone()
            return True
        except sqlite3.DatabaseError:
            return False

    def write(self, declarations: list[FormalDeclaration]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE declarations (
                    id INTEGER PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    line INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    binder_count INTEGER NOT NULL,
                    premise_heads TEXT NOT NULL,
                    conclusion_head TEXT NOT NULL,
                    lhs_head TEXT NOT NULL,
                    rhs_head TEXT NOT NULL,
                    major_symbols TEXT NOT NULL,
                    imports TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE declarations_fts USING fts5(
                    decl_id UNINDEXED,
                    name,
                    signature,
                    shape,
                    path,
                    source_id,
                    imports
                )
                """
            )
            for idx, decl in enumerate(declarations, start=1):
                conn.execute(
                    """
                    INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        idx,
                        decl.source_id,
                        decl.source_type,
                        decl.path,
                        decl.line,
                        decl.kind,
                        decl.name,
                        decl.namespace,
                        decl.signature,
                        decl.binder_count,
                        json.dumps(decl.premise_heads),
                        decl.conclusion_head,
                        decl.lhs_head,
                        decl.rhs_head,
                        json.dumps(decl.major_symbols),
                        json.dumps(decl.imports),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO declarations_fts (decl_id, name, signature, shape, path, source_id, imports)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        idx,
                        _fts_text(decl.name),
                        _fts_text(decl.signature),
                        _fts_text(
                            " ".join(
                                [
                                    decl.conclusion_head,
                                    decl.lhs_head,
                                    decl.rhs_head,
                                    " ".join(decl.premise_heads),
                                    " ".join(decl.major_symbols),
                                ]
                            )
                        ),
                        _fts_text(decl.path),
                        _fts_text(decl.source_id),
                        _fts_text(" ".join(decl.imports)),
                    ),
                )
            conn.execute("CREATE INDEX declarations_name_idx ON declarations(name)")
            conn.commit()

    def search(self, query: str, *, k: int = 10) -> list[FormalSourceHit]:
        fts_query = _fts_query(query)
        if not fts_query:
            return []
        candidate_k = max(k * 12, 80)
        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(
                """
                SELECT d.*, bm25(declarations_fts) AS rank
                FROM declarations_fts
                JOIN declarations d ON d.id = declarations_fts.decl_id
                WHERE declarations_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, candidate_k),
            ).fetchall()
        q_tokens = _search_tokens(query)
        hits: list[FormalSourceHit] = []
        for row in rows:
            decl = _decl_from_sqlite_row(row)
            hit = _score_declaration(decl, q_tokens)
            if hit is not None:
                hits.append(hit)
        return sorted(hits, key=lambda hit: (-hit.score, hit.declaration.source_id, hit.declaration.name))[:k]

    def load_declarations(self) -> list[FormalDeclaration]:
        """Read all declarations back from the persisted index.

        Downstream graph audits can reuse the already-built SQLite corpus
        instead of rescanning the Lean source tree during release-style audits.
        """

        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM declarations
                ORDER BY id
                """
            ).fetchall()
        return [_decl_from_sqlite_row(row) for row in rows]


DEFAULT_FORMAL_SOURCE_ROOTS: tuple[FormalSourceRoot, ...] = tuple(
    FormalSourceRoot(target.id, target.location, target.source_type)
    for target in SOURCE_INVENTORY_TARGETS
    if target.source_type == "lean_library"
)


DEFAULT_AUDIT_QUERIES: tuple[tuple[str, str], ...] = (
    ("finite_sum_variance", "variance finite sum independent pairwise IndepFun variance_sum"),
    ("finite_union_bound", "finite union bound Bonferroni measure biUnion finset le"),
    ("independent_event_intersection", "independent events intersection probability measure product IndepSet measure_inter_eq_mul"),
    ("first_borel_cantelli", "first Borel Cantelli limsup atTop zero finite sum probabilities measure_limsup_atTop_eq_zero"),
    ("second_borel_cantelli", "second Borel Cantelli independent events divergent sum limsup one measure_limsup_eq_one"),
    ("adapted_hitting_time", "adapted process hittingAfter measurable set is stopping time optional stopping"),
    ("theorem_shape_variance_independence", "premise IndepFun conclusion variance equality independent variables"),
    ("chebyshev_tail", "Chebyshev variance probability absolute error meas_ge_le_variance_div_sq"),
    ("clt", "central limit theorem independent identically distributed characteristic function"),
    ("borel_cantelli", "Borel Cantelli independent events limsup probability"),
    ("conditional_expectation", "conditional expectation tower property filtration"),
    ("subgaussian_learning", "subGaussian covering least squares concentration learning theory"),
    ("formal_slt_rademacher_pac", "FormalSLT finite sample Rademacher PAC Bayes ERM VC Azuma stability"),
    ("lean_rademacher_dudley", "Rademacher complexity McDiarmid Dudley entropy integral generalization bound"),
    ("lean_machine_learning_regret", "LeanMachineLearning stochastic bandit regret UCB explore then commit algorithm"),
    ("brownian_motion_gaussian_process", "Brownian motion Gaussian Kolmogorov Chentsov stochastic process continuity"),
    ("kolmogorov_extension_projective", "Kolmogorov extension theorem projective measure family compact system"),
    ("scilean_calculus_optimization", "SciLean derivative gradient jacobian optimization Gaussian probabilistic derivative"),
    ("empirical_process", "empirical process Donsker tightness stochastic equicontinuity"),
    ("godambe_bootstrap", "Godambe bootstrap martingale variance estimator statistical inference"),
    ("aipw_product_rate", "AIPW orthogonal score product rate double robust causal inference"),
    ("ipw_hajek_linearization", "IPW Hajek linearization inverse probability weighting causal estimator"),
    ("asymptotic_normality_bridge", "asymptotic normality estimator bridge influence function CLT"),
    ("glivenko_cantelli_bracketing", "Glivenko Cantelli empirical process bracketing endpoint class"),
    ("weak_convergence_donsker", "Donsker weak convergence probability measures empirical process"),
    ("rademacher_shared_foundation", "Rademacher probability measure support sign symmetrization subGaussian"),
    ("backward_martingale_shared_foundation", "backward martingale reverse filtration conditional expectation convergence"),
    ("atlas_subgaussian_high_dimensional", "Atlas HighDimensionalStatistics IsSubGaussian mgf bound Bernstein concentration"),
    ("atlas_probability_limit_theory", "Atlas TheoryOfProbability CLT Lindeberg Feller Borel Cantelli weak convergence"),
    ("atlas_fourier_characteristic_weak_convergence", "Atlas FourierAnalysis characteristic function Fourier transform weak convergence CLT finite measures"),
    ("atlas_functional_analysis_projection", "Atlas functional analysis Hilbert space orthogonal projection Cauchy Schwarz Riesz representation"),
    ("atlas_differential_analysis_taylor_sobolev", "Atlas differential analysis Frechet Taylor Sobolev Fourier Gaussian"),
    ("atlas_projection_geometry", "Atlas projection theory orthogonal projection large sieve grid projection geometric incidence"),
)


def build_formal_source_index(
    *,
    roots: tuple[FormalSourceRoot, ...] = DEFAULT_FORMAL_SOURCE_ROOTS,
    max_file_bytes: int = 2_000_000,
    max_files_per_root: int = 1500,
) -> list[FormalDeclaration]:
    """Index Lean declarations from local formal sources.

    This is deliberately a lightweight declaration index, not a parser. Its job
    is to make local theorem mining cheap and auditable before we ask an LLM or
    AXLE to prove a new statistical obligation.
    """

    rows: list[FormalDeclaration] = []
    seen_roots: set[Path] = set()
    for root in roots:
        location = Path(root.location).expanduser()
        if not location.exists():
            continue
        try:
            resolved = location.resolve()
        except OSError:
            resolved = location
        if resolved in seen_roots:
            continue
        seen_roots.add(resolved)
        for path in _iter_lean_files(location, max_file_bytes=max_file_bytes, max_files=max_files_per_root):
            rows.extend(_declarations_in_file(root, path, location))
    return rows


def search_formal_sources(
    query: str,
    *,
    declarations: list[FormalDeclaration] | None = None,
    k: int = 10,
) -> list[FormalSourceHit]:
    return FormalSourceRetriever(declarations).search(query, k=k)


def build_formal_source_search_backend(
    *,
    db_path: Path | str | None = None,
    roots: tuple[FormalSourceRoot, ...] = DEFAULT_FORMAL_SOURCE_ROOTS,
    include_graph: bool = True,
    cache_path: Path | str | None = None,
    refresh_cache: bool = False,
    lean_rag_db_path: Path | str | None = None,
) -> object:
    """Build the local formal-source retriever used by research traces.

    Passing a database path gives the production path: scan local Lean/stat
    sources once, persist a SQLite FTS index, then let repeated formal-gap
    searches use FTS candidate generation, Lean-shape reranking, and by default
    declaration-symbol graph expansion. Omitting the path keeps the old
    in-memory backend for small fixtures and tests.
    """

    cache_file = Path(cache_path) if cache_path is not None else None
    if db_path is not None:
        target_db = Path(db_path)
        if cache_file is not None and cache_file.exists() and not refresh_cache:
            try:
                target_db.parent.mkdir(parents=True, exist_ok=True)
                if target_db.resolve() != cache_file.resolve():
                    shutil.copy2(cache_file, target_db)
                sqlite_index = FormalSourceSqliteIndex(target_db)
                if not sqlite_index.is_healthy():
                    raise sqlite3.DatabaseError("formal-source SQLite cache is missing required tables")
                declarations = sqlite_index.load_declarations()
                if not _cache_covers_configured_roots(declarations, roots):
                    raise sqlite3.DatabaseError(
                        "formal-source SQLite cache is stale for the configured Lean source roots"
                    )
                dependency_retriever = _optional_lean_rag_dependency_retriever(lean_rag_db_path)
                if include_graph:
                    from .formal_source_hybrid import FormalSourceHybridRetriever

                    retriever = FormalSourceHybridRetriever(
                        declarations,
                        sqlite_index,
                        dependency_retriever=dependency_retriever,
                    )
                else:
                    retriever = sqlite_index
                setattr(retriever, "cache_status", "hit")
                setattr(retriever, "cache_path", str(cache_file))
                _attach_lean_rag_metadata(retriever, dependency_retriever)
                return retriever
            except Exception:
                # Stale or incompatible cache. Rebuild below and overwrite it.
                if target_db.exists():
                    target_db.unlink()

    declarations = build_formal_source_index(roots=roots)
    if db_path is not None:
        sqlite_index = FormalSourceSqliteIndex.build(declarations, db_path)
        if cache_file is not None:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            if Path(db_path).resolve() != cache_file.resolve():
                shutil.copy2(db_path, cache_file)
        dependency_retriever = _optional_lean_rag_dependency_retriever(lean_rag_db_path)
        if include_graph:
            from .formal_source_hybrid import FormalSourceHybridRetriever

            retriever = FormalSourceHybridRetriever(
                declarations,
                sqlite_index,
                dependency_retriever=dependency_retriever,
            )
        else:
            retriever = sqlite_index
        setattr(retriever, "cache_status", "miss" if cache_file is not None else "disabled")
        setattr(retriever, "cache_path", str(cache_file) if cache_file is not None else "")
        _attach_lean_rag_metadata(retriever, dependency_retriever)
        return retriever
    dependency_retriever = _optional_lean_rag_dependency_retriever(lean_rag_db_path)
    retriever: object = FormalSourceRetriever(declarations)
    if dependency_retriever is not None:
        from .formal_source_hybrid import FormalSourceDependencyHybridRetriever

        retriever = FormalSourceDependencyHybridRetriever(
            declarations,
            retriever,
            dependency_retriever,
        )
    setattr(retriever, "cache_status", "disabled")
    setattr(retriever, "cache_path", "")
    _attach_lean_rag_metadata(retriever, dependency_retriever)
    return retriever


def _optional_lean_rag_dependency_retriever(lean_rag_db_path: Path | str | None) -> object | None:
    explicit_path = lean_rag_db_path or os.environ.get("AI_STATISTICIAN_LEAN_RAG_DB")
    candidate_paths = (
        (Path(explicit_path).expanduser(),)
        if explicit_path
        else _auto_lean_rag_db_candidates()
    )
    if not candidate_paths:
        return None
    try:
        from .lean_rag_dependency import LeanRagDependencyRetriever

        for candidate in candidate_paths:
            retriever = LeanRagDependencyRetriever(candidate)
            health = retriever.health_report()
            if health.get("all_ok"):
                setattr(retriever, "auto_discovered", not bool(explicit_path))
                setattr(retriever, "health_payload", health)
                return retriever
        return None
    except Exception:
        return None


def _auto_lean_rag_db_candidates() -> tuple[Path, ...]:
    if os.environ.get("AI_STATISTICIAN_DISABLE_LEAN_RAG_AUTO", "").lower() in {
        "1",
        "true",
        "yes",
    }:
        return ()
    package_root = Path(__file__).resolve().parents[1]
    candidates = (
        *DEFAULT_LEAN_RAG_DB_CANDIDATES,
        Path.cwd() / DEFAULT_LEAN_RAG_DB_RELATIVE_PATH,
        package_root / DEFAULT_LEAN_RAG_DB_RELATIVE_PATH,
    )
    rows: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        path = Path(candidate).expanduser()
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            rows.append(path)
    return tuple(rows)


def _attach_lean_rag_metadata(retriever: object, dependency_retriever: object | None) -> None:
    setattr(retriever, "lean_rag_dependency_graph_enabled", dependency_retriever is not None)
    setattr(
        retriever,
        "lean_rag_dependency_graph_path",
        str(getattr(dependency_retriever, "db_path", "")) if dependency_retriever is not None else "",
    )
    setattr(
        retriever,
        "lean_rag_dependency_graph_auto_discovered",
        bool(getattr(dependency_retriever, "auto_discovered", False))
        if dependency_retriever is not None
        else False,
    )
    setattr(
        retriever,
        "lean_rag_dependency_graph_health_status",
        "active_healthy" if dependency_retriever is not None else "disabled",
    )
    setattr(
        retriever,
        "lean_rag_dependency_graph_health",
        getattr(dependency_retriever, "health_payload", {}) if dependency_retriever is not None else {},
    )


def _cache_covers_configured_roots(
    declarations: list[FormalDeclaration],
    roots: tuple[FormalSourceRoot, ...],
) -> bool:
    """Return whether a cached index still represents existing configured roots.

    The source inventory can grow as new Lean libraries are mirrored locally.
    A syntactically healthy SQLite cache can still be stale if it predates those
    sources. Treat existing roots with at least one Lean file as required source
    ids, so release-style retrieval does not silently ignore newly available
    formal libraries.
    """

    present_source_ids = {declaration.source_id for declaration in declarations}
    required_source_ids = {
        root.id
        for root in roots
        if _root_has_indexable_lean_file(Path(root.location).expanduser())
    }
    return required_source_ids.issubset(present_source_ids)


def _root_has_indexable_lean_file(root: Path) -> bool:
    if not root.exists():
        return False
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in SKIPPED_PATH_PARTS)
        for filename in filenames:
            if not filename.endswith(".lean"):
                continue
            path = Path(dirpath) / filename
            if _skip_path(path, base=root) or not _file_size_ok(path, 2_000_000):
                continue
            return True
    return False


def audit_formal_source_index(
    out_dir: Path | None = None,
    *,
    roots: tuple[FormalSourceRoot, ...] = DEFAULT_FORMAL_SOURCE_ROOTS,
    queries: tuple[tuple[str, str], ...] = DEFAULT_AUDIT_QUERIES,
    k: int = 8,
    backend: str = "sqlite",
) -> dict[str, object]:
    declarations = build_formal_source_index(roots=roots)
    by_source: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for decl in declarations:
        by_source[decl.source_id] = by_source.get(decl.source_id, 0) + 1
        by_kind[decl.kind] = by_kind.get(decl.kind, 0) + 1
    db_path = out_dir / "formal_source_index.sqlite" if out_dir is not None else None
    if backend == "sqlite" and db_path is not None:
        retriever = FormalSourceSqliteIndex.build(declarations, db_path)
        search_backend = "sqlite_fts_hybrid"
    else:
        retriever = FormalSourceRetriever(declarations)
        search_backend = "python_shape"
    query_rows = []
    for query_id, text in queries:
        hits = retriever.search(text, k=k)
        query_rows.append(
            {
                "query_id": query_id,
                "query": text,
                "n_hits": len(hits),
                "top_hits": [_hit_payload(hit) for hit in hits],
                "ok": bool(hits),
            }
        )
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "index_fingerprint": formal_source_index_fingerprint(declarations),
        "n_sources": len({decl.source_id for decl in declarations}),
        "n_declarations": len(declarations),
        "by_source": dict(sorted(by_source.items())),
        "by_kind": dict(sorted(by_kind.items())),
        "n_queries": len(query_rows),
        "n_query_ok": sum(1 for row in query_rows if row["ok"]),
        "all_queries_ok": all(row["ok"] for row in query_rows),
        "search_backend": search_backend,
        "sqlite_index_path": str(db_path) if db_path is not None and search_backend == "sqlite_fts_hybrid" else "",
        "query_rows": query_rows,
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_source_index_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_source_index.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def formal_source_index_fingerprint(declarations: list[FormalDeclaration] | None = None) -> str:
    decls = declarations if declarations is not None else build_formal_source_index()
    stable_rows = [
        {
            "source_id": decl.source_id,
            "path": decl.path,
            "line": decl.line,
            "kind": decl.kind,
            "name": decl.name,
            "signature": decl.signature,
            "binder_count": decl.binder_count,
            "premise_heads": decl.premise_heads,
            "conclusion_head": decl.conclusion_head,
            "lhs_head": decl.lhs_head,
            "rhs_head": decl.rhs_head,
            "major_symbols": decl.major_symbols,
            "imports": decl.imports,
        }
        for decl in decls
    ]
    return stable_hash(stable_rows)


def _search_tokens(text: str) -> set[str]:
    """Tokenize Lean names plus natural-language queries for local declaration search."""

    split_text = re.sub(r"[_'.]", " ", text)
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", split_text)
    return {
        token.lower()
        for token in TOKEN_RE.findall(" ".join([text, split_text, camel_split]))
        if token.strip()
        and token.lower() not in STOP_TOKENS
        and any(ch.isalnum() for ch in token)
    }


def _score_declaration(
    decl: FormalDeclaration,
    q_tokens: set[str],
    *,
    declaration_tokens: set[str] | None = None,
    name_tokens: set[str] | None = None,
    shape_tokens: set[str] | None = None,
    import_tokens: set[str] | None = None,
) -> FormalSourceHit | None:
    d_tokens = declaration_tokens if declaration_tokens is not None else _search_tokens(_decl_search_text(decl))
    n_tokens = name_tokens if name_tokens is not None else _search_tokens(decl.name)
    s_tokens = (
        shape_tokens
        if shape_tokens is not None
        else _search_tokens(" ".join([decl.conclusion_head, decl.lhs_head, decl.rhs_head, " ".join(decl.premise_heads)]))
    )
    i_tokens = import_tokens if import_tokens is not None else _search_tokens(" ".join(decl.imports))
    overlap = q_tokens & d_tokens
    if not overlap:
        return None
    name_bonus = 2.0 * len(q_tokens & n_tokens)
    shape_bonus = 1.5 * len(q_tokens & s_tokens)
    import_bonus = 0.75 * len(q_tokens & i_tokens)
    source_bonus = 1.0 if decl.source_id.startswith("mathlib") else 1.5
    score = len(overlap) + name_bonus + shape_bonus + import_bonus + source_bonus
    return FormalSourceHit(decl, score, tuple(sorted(overlap)[:16]))


def _decl_search_text(decl: FormalDeclaration) -> str:
    return " ".join(
        [
            decl.name,
            decl.kind,
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


def _fts_tokens(text: str) -> list[str]:
    return sorted(token for token in _search_tokens(text) if re.match(r"^[a-z0-9_]+$", token))


def _fts_text(text: str) -> str:
    return " ".join(_fts_tokens(text))


def _fts_query(text: str) -> str:
    tokens = _fts_tokens(text)
    return " OR ".join(tokens)


def _decl_from_sqlite_row(row) -> FormalDeclaration:
    return FormalDeclaration(
        source_id=row[1],
        source_type=row[2],
        path=row[3],
        line=int(row[4]),
        kind=row[5],
        name=row[6],
        namespace=row[7],
        signature=row[8],
        binder_count=int(row[9]),
        premise_heads=tuple(json.loads(row[10])),
        conclusion_head=row[11],
        lhs_head=row[12],
        rhs_head=row[13],
        major_symbols=tuple(json.loads(row[14])),
        imports=tuple(json.loads(row[15])) if len(row) > 15 else (),
    )


def _declaration_signature(lines: list[str], start_idx: int, *, max_lines: int = 8) -> str:
    """Return a compact multi-line declaration header for retrieval.

    The index is intentionally parser-light, but single-line signatures lose
    most theorem shape information. Capturing the short header block gives the
    retriever access to premise heads, conclusion symbols, and target shape.
    """

    chunks: list[str] = []
    for offset in range(max_lines):
        pos = start_idx + offset
        if pos >= len(lines):
            break
        line = lines[pos]
        if offset > 0 and (
            DECL_RE.match(line)
            or NAMESPACE_RE.match(line)
            or END_RE.match(line)
        ):
            break
        chunks.append(line.strip())
        if ":=" in line or line.strip().endswith("where"):
            break
    return " ".join(chunk for chunk in chunks if chunk)


def _compress_signature(signature: str) -> dict[str, object]:
    """Extract Lean-aware theorem-shape features for cheap premise retrieval."""

    clean = re.sub(r":=.*$", "", signature).strip()
    conclusion = _conclusion_fragment(clean)
    lhs, rhs = _split_conclusion_eq(conclusion)
    premise_heads = tuple(sorted(set(_premise_heads(clean))))
    conclusion_head = _head_symbol(conclusion)
    lhs_head = _head_symbol(lhs)
    rhs_head = _head_symbol(rhs)
    major_symbols = tuple(
        sorted(
            set(
                list(premise_heads)
                + [symbol for symbol in (conclusion_head, lhs_head, rhs_head) if symbol]
                + _name_like_symbols(clean)
            )
        )[:24]
    )
    return {
        "binder_count": clean.count("(") + clean.count("{") + clean.count("["),
        "premise_heads": premise_heads,
        "conclusion_head": conclusion_head,
        "lhs_head": lhs_head,
        "rhs_head": rhs_head,
        "major_symbols": major_symbols,
    }


def _conclusion_fragment(signature: str) -> str:
    parts = signature.rsplit(" : ", 1)
    if len(parts) == 2:
        return parts[1].strip()
    colon = signature.rfind(":")
    return signature[colon + 1 :].strip() if colon >= 0 else signature


def _split_conclusion_eq(conclusion: str) -> tuple[str, str]:
    if "=" not in conclusion:
        return conclusion, ""
    lhs, rhs = conclusion.split("=", 1)
    return lhs.strip(), rhs.strip()


def _premise_heads(signature: str) -> list[str]:
    heads: list[str] = []
    for match in re.finditer(r"[\(\{\[][^:\]\)\}]+:\s*([A-Za-z_][A-Za-z0-9_'.]*)", signature):
        heads.append(match.group(1).split(".")[-1])
    return heads


def _head_symbol(text: str) -> str:
    match = re.search(r"[A-Za-z_][A-Za-z0-9_'.]*|[∀∃∧∨→↔=≤≥<>+*/^]+", text)
    if not match:
        return ""
    return match.group(0).split(".")[-1]


def _name_like_symbols(text: str) -> list[str]:
    symbols = []
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_'.]*", text):
        tail = token.split(".")[-1]
        if len(tail) >= 3 and tail.lower() not in STOP_TOKENS:
            symbols.append(tail)
    return symbols


def _declarations_in_file(root: FormalSourceRoot, path: Path, base: Path) -> list[FormalDeclaration]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    rel = str(path.relative_to(base))
    namespace_stack: list[str] = []
    imports: list[str] = []
    rows: list[FormalDeclaration] = []
    for idx, line in enumerate(lines, start=1):
        import_match = IMPORT_RE.match(line)
        if import_match:
            imports.extend(_parse_imports(import_match.group(1)))
            continue
        ns_match = NAMESPACE_RE.match(line)
        if ns_match:
            namespace_stack.extend(ns_match.group(1).split("."))
            continue
        end_match = END_RE.match(line)
        if end_match and namespace_stack:
            end_name = end_match.group(1)
            if end_name:
                parts = end_name.split(".")
                if namespace_stack[-len(parts) :] == parts:
                    del namespace_stack[-len(parts) :]
                else:
                    namespace_stack.pop()
            else:
                namespace_stack.pop()
            continue
        decl_match = DECL_RE.match(line)
        if not decl_match:
            continue
        kind, raw_name = decl_match.groups()
        namespace = ".".join(namespace_stack)
        name = raw_name if "." in raw_name or not namespace else f"{namespace}.{raw_name}"
        signature = _declaration_signature(lines, idx - 1)
        compressed = _compress_signature(signature)
        rows.append(
            FormalDeclaration(
                source_id=root.id,
                source_type=root.source_type,
                path=rel,
                line=idx,
                kind=kind,
                name=name,
                namespace=namespace,
                signature=signature,
                binder_count=compressed["binder_count"],
                premise_heads=compressed["premise_heads"],
                conclusion_head=compressed["conclusion_head"],
                lhs_head=compressed["lhs_head"],
                rhs_head=compressed["rhs_head"],
                major_symbols=compressed["major_symbols"],
                imports=tuple(imports),
            )
        )
    return rows


def _parse_imports(import_tail: str) -> list[str]:
    cleaned = import_tail.split("--", 1)[0].strip()
    return [item for item in cleaned.split() if re.match(r"^[A-Za-z_][A-Za-z0-9_'.]*$", item)]


def _iter_lean_files(location: Path, *, max_file_bytes: int, max_files: int):
    """Yield a capped, deterministic stream of Lean files while pruning heavy build dirs."""

    n_files = 0
    for dirpath, dirnames, filenames in os.walk(location):
        dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in SKIPPED_PATH_PARTS)
        for filename in sorted(filenames):
            if not filename.endswith(".lean"):
                continue
            path = Path(dirpath) / filename
            if _skip_path(path, base=location) or not _file_size_ok(path, max_file_bytes):
                continue
            yield path
            n_files += 1
            if n_files >= max_files:
                return


def _skip_path(path: Path, *, base: Path | None = None) -> bool:
    if base is None:
        parts = path.parts
    else:
        try:
            parts = path.relative_to(base).parts
        except ValueError:
            parts = path.parts
    return any(part in SKIPPED_PATH_PARTS for part in parts)


def _file_size_ok(path: Path, max_file_bytes: int) -> bool:
    try:
        return path.stat().st_size <= max_file_bytes
    except OSError:
        return False


def _hit_payload(hit: FormalSourceHit) -> dict[str, object]:
    return {
        "source_id": hit.declaration.source_id,
        "path": hit.declaration.path,
        "line": hit.declaration.line,
        "kind": hit.declaration.kind,
        "name": hit.declaration.name,
        "score": hit.score,
        "matched_terms": hit.matched_terms,
        "binder_count": hit.declaration.binder_count,
        "premise_heads": hit.declaration.premise_heads,
        "conclusion_head": hit.declaration.conclusion_head,
        "lhs_head": hit.declaration.lhs_head,
        "rhs_head": hit.declaration.rhs_head,
        "imports": hit.declaration.imports,
    }


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Source Index",
        "",
        f"- Sources indexed: {payload['n_sources']}",
        f"- Declarations indexed: {payload['n_declarations']}",
        f"- Query coverage: {payload['n_query_ok']}/{payload['n_queries']}",
        f"- Search backend: `{payload.get('search_backend', 'unknown')}`",
        f"- SQLite index: `{payload.get('sqlite_index_path', '') or 'not written'}`",
        f"- Fingerprint: `{payload['index_fingerprint']}`",
        "",
        "## Sources",
        "",
        "| Source | Declarations |",
        "|---|---:|",
    ]
    for source_id, count in dict(payload["by_source"]).items():
        lines.append(f"| `{source_id}` | {count} |")
    lines.extend(["", "## Expansion Queries", "", "| Query | OK | Top declarations |", "|---|---:|---|"])
    for row in payload["query_rows"]:  # type: ignore[index]
        hits = row["top_hits"][:5]
        summary = "<br>".join(
            f"`{hit['name']}` ({hit['source_id']}:{hit['path']}:{hit['line']})" for hit in hits
        )
        lines.append(f"| `{row['query_id']}` | {row['ok']} | {summary or 'none'} |")
    return "\n".join(lines) + "\n"
