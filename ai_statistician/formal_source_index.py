from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
from collections import Counter
from contextlib import closing
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .research_source_inventory import (
    EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT,
    SOURCE_INVENTORY_TARGETS,
)


LEAN_IDENTIFIER_PATTERN = r"[^\W\d][\w'.]*"
LEAN_IDENTIFIER_END = r"(?![\w'.])"
DECL_RE = re.compile(
    r"^\s*(?:@[^\n]*\s*)*"
    r"(?:(?:private|protected|nonrec|noncomputable|unsafe)\s+)*"
    r"(theorem|lemma|def|abbrev|structure|class|inductive|opaque|instance)\s+"
    rf"({LEAN_IDENTIFIER_PATTERN}){LEAN_IDENTIFIER_END}"
)
ROCQ_DECL_RE = re.compile(
    r"^\s*"
    r"(Theorem|Lemma|Definition|Fixpoint|Inductive|Record|Class|Instance|"
    r"Corollary|Proposition|Remark|Fact)\s+"
    r"([A-Za-z_][A-Za-z0-9_']*)\b"
)
ISABELLE_DECL_RE = re.compile(
    r"^\s*"
    r"(theorem|lemma|corollary|proposition|definition|fun|primrec|inductive)\s+"
    r"([A-Za-z_][A-Za-z0-9_']*)\b"
)
AGDA_DECL_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_'.-]*)\s*:")
NAMESPACE_RE = re.compile(
    rf"^\s*namespace\s+({LEAN_IDENTIFIER_PATTERN}){LEAN_IDENTIFIER_END}"
)
SECTION_RE = re.compile(
    rf"^\s*(?:noncomputable\s+)?section"
    rf"(?:\s+({LEAN_IDENTIFIER_PATTERN}){LEAN_IDENTIFIER_END})?"
)
END_RE = re.compile(
    rf"^\s*end(?:\s+({LEAN_IDENTIFIER_PATTERN}){LEAN_IDENTIFIER_END})?"
)
IMPORT_RE = re.compile(r"^\s*import\s+(.+)$")
ROCQ_NAMESPACE_RE = re.compile(
    r"^\s*(?:Module|Section)\s+([A-Za-z_][A-Za-z0-9_']*)\b"
)
ROCQ_END_RE = re.compile(r"^\s*End\s+([A-Za-z_][A-Za-z0-9_']*)\s*\.")
ROCQ_IMPORT_RE = re.compile(
    r"^\s*(?:From\s+[A-Za-z_][A-Za-z0-9_'.]*\s+)?"
    r"Require\s+(?:Import|Export)?\s*(.+?)\.\s*$"
)
ISABELLE_THEORY_RE = re.compile(r"^\s*theory\s+([A-Za-z_][A-Za-z0-9_']*)\b")
ISABELLE_IMPORTS_RE = re.compile(r"^\s*imports\s+(.+)$")
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
_EMPTY_SEARCH_TOKENS: frozenset[str] = frozenset()
MAX_SQLITE_FTS_QUERY_TOKENS = 24
MODULE_SUMMARY_TOKEN_WEIGHT = 0.25
DECLARATION_DOC_TOKEN_WEIGHT = 1.0
SECTION_SUMMARY_TOKEN_WEIGHT = 0.5
MODULE_GROUP_TOKEN_WEIGHT = 0.25
SOURCE_REFERENCE_PROMINENCE_BONUS = 3.5
SOURCE_OUTLINE_PROMINENCE_BONUS = 0.75
DECLARATION_NAME_CONCEPT_ANCHOR_BONUS = 3.0
DECLARATION_NAME_COVERAGE_BONUS_CAP = 4.0
FORMAL_SOURCE_SQLITE_SCHEMA_VERSION = "4"
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
DEFAULT_AI4SLT_LEAN_RAG_DB_RELATIVE_PATH = Path(
    "runs/current_status_ai4slt_lean_rag_dependency_graph/stat_learning.sqlite"
)
# Tests and downstream orchestration can prepend project-specific candidates
# without changing the global auto-discovery rule.
DEFAULT_LEAN_RAG_DB_CANDIDATES: tuple[Path, ...] = ()
FORMAL_SOURCE_SUFFIXES_BY_TYPE = {
    "lean": (".lean",),
    "lean4": (".lean",),
    "lean_library": (".lean",),
    "mathlib": (".lean",),
    "rocq": (".v",),
    "rocq_library": (".v",),
    "coq": (".v",),
    "coq_library": (".v",),
    "isabelle": (".thy",),
    "isabelle_library": (".thy",),
    "agda": (".agda",),
    "agda_library": (".agda",),
}


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
    reference: str = ""
    reference_aliases: tuple[str, ...] = ()
    module_summary: str = ""
    declaration_doc: str = ""
    section_summary: str = ""
    module_group: str = ""
    module_group_summary: str = ""


@dataclass(frozen=True)
class _FormalModuleGroup:
    name: str
    module_patterns: tuple[str, ...]
    summary: str = ""


@dataclass(frozen=True)
class FormalSourceHit:
    declaration: FormalDeclaration
    score: float
    matched_terms: tuple[str, ...]


class FormalSourceRetriever:
    """Reusable declaration retriever with pre-tokenized formal-source rows."""

    def __init__(self, declarations: list[FormalDeclaration] | None = None) -> None:
        self.declarations = declarations if declarations is not None else build_formal_source_index()
        semantic_tokens_by_text: dict[str, frozenset[str]] = {}

        def cached_tokens(value: str) -> frozenset[str]:
            if not value:
                return _EMPTY_SEARCH_TOKENS
            tokens = semantic_tokens_by_text.get(value)
            if tokens is None:
                tokens = frozenset(_search_tokens(value))
                semantic_tokens_by_text[value] = tokens
            return tokens

        self._rows = []
        for decl in self.declarations:
            module_group_text = " ".join(
                value
                for value in (
                    decl.module_group,
                    decl.module_group_summary,
                )
                if value
            )
            self._rows.append(
                (
                    decl,
                    _search_tokens(_decl_core_search_text(decl)),
                    cached_tokens(decl.module_summary),
                    cached_tokens(decl.declaration_doc),
                    cached_tokens(decl.section_summary),
                    cached_tokens(module_group_text),
                    _search_tokens(decl.name),
                    _search_tokens(
                        " ".join(
                            [
                                decl.conclusion_head,
                                decl.lhs_head,
                                decl.rhs_head,
                                " ".join(decl.premise_heads),
                            ]
                        )
                    ),
                    _search_tokens(" ".join(decl.imports)),
                    (
                        _search_tokens(
                            " ".join((decl.reference, *decl.reference_aliases))
                        )
                        if decl.reference or decl.reference_aliases
                        else _EMPTY_SEARCH_TOKENS
                    ),
                    _source_authored_declaration_prominence_bonus(decl),
                )
            )

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
        q_tokens = _search_tokens(query)
        query_lookup_key = _declaration_lookup_key(query)
        allowed_source_ids = set(source_scope_ids)
        hits: list[FormalSourceHit] = []
        for (
            decl,
            d_tokens,
            module_tokens,
            declaration_doc_tokens,
            section_summary_tokens,
            module_group_tokens,
            name_tokens,
            shape_tokens,
            import_tokens,
            reference_tokens,
            source_prominence_bonus,
        ) in self._rows:
            if allowed_source_ids and decl.source_id not in allowed_source_ids:
                continue
            hit = _score_declaration(
                decl,
                q_tokens,
                query_text=query,
                declaration_tokens=d_tokens,
                module_summary_tokens=module_tokens,
                declaration_doc_tokens=declaration_doc_tokens,
                section_summary_tokens=section_summary_tokens,
                module_group_tokens=module_group_tokens,
                name_tokens=name_tokens,
                shape_tokens=shape_tokens,
                import_tokens=import_tokens,
                reference_tokens=reference_tokens,
                query_lookup_key=query_lookup_key,
                source_prominence_bonus=source_prominence_bonus,
            )
            if hit is not None:
                hits.append(hit)
        ordered = sorted(
            hits,
            key=lambda hit: (
                -hit.score,
                hit.declaration.source_id,
                hit.declaration.name,
            ),
        )
        return diversify_formal_source_hits(ordered, k=k)


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
    def build(
        cls,
        declarations: list[FormalDeclaration],
        db_path: Path | str,
        *,
        source_snapshots: dict[str, object] | None = None,
    ) -> "FormalSourceSqliteIndex":
        index = cls(db_path)
        index.write(declarations, source_snapshots=source_snapshots)
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
                if not {
                    "declarations",
                    "declarations_fts",
                    "metadata",
                }.issubset(tables):
                    return False
                declaration_columns = {
                    row[1]
                    for row in conn.execute(
                        "PRAGMA table_info(declarations)"
                    ).fetchall()
                }
                fts_columns = {
                    row[1]
                    for row in conn.execute(
                        "PRAGMA table_info(declarations_fts)"
                    ).fetchall()
                }
                if not {
                    "reference",
                    "reference_aliases",
                    "module_summary",
                    "declaration_doc",
                    "section_summary",
                    "module_group",
                    "module_group_summary",
                }.issubset(declaration_columns) or not {
                    "reference",
                    "reference_aliases",
                    "module_summary",
                    "declaration_doc",
                    "section_summary",
                    "module_group",
                    "module_group_summary",
                }.issubset(fts_columns):
                    return False
                schema_row = conn.execute(
                    "SELECT value FROM metadata WHERE key = 'schema_version'"
                ).fetchone()
                if not schema_row or schema_row[0] != FORMAL_SOURCE_SQLITE_SCHEMA_VERSION:
                    return False
                conn.execute("SELECT COUNT(*) FROM declarations").fetchone()
                conn.execute("SELECT COUNT(*) FROM declarations_fts").fetchone()
            return True
        except sqlite3.DatabaseError:
            return False

    def write(
        self,
        declarations: list[FormalDeclaration],
        *,
        source_snapshots: dict[str, object] | None = None,
    ) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
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
                    imports TEXT NOT NULL,
                    reference TEXT NOT NULL,
                    reference_aliases TEXT NOT NULL,
                    module_summary TEXT NOT NULL,
                    declaration_doc TEXT NOT NULL,
                    section_summary TEXT NOT NULL,
                    module_group TEXT NOT NULL,
                    module_group_summary TEXT NOT NULL
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
                    imports,
                    reference,
                    reference_aliases,
                    module_summary,
                    declaration_doc,
                    section_summary,
                    module_group,
                    module_group_summary
                )
                """
            )
            for idx, decl in enumerate(declarations, start=1):
                conn.execute(
                    """
                    INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        decl.reference,
                        json.dumps(decl.reference_aliases),
                        decl.module_summary,
                        decl.declaration_doc,
                        decl.section_summary,
                        decl.module_group,
                        decl.module_group_summary,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO declarations_fts (
                        decl_id, name, signature, shape, path, source_id, imports,
                        reference, reference_aliases, module_summary,
                        declaration_doc, section_summary, module_group,
                        module_group_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        _fts_text(decl.reference),
                        _fts_text(" ".join(decl.reference_aliases)),
                        _fts_text(decl.module_summary),
                        _fts_text(decl.declaration_doc),
                        _fts_text(decl.section_summary),
                        _fts_text(decl.module_group),
                        _fts_text(decl.module_group_summary),
                    ),
                )
            conn.execute("CREATE INDEX declarations_name_idx ON declarations(name)")
            metadata = {
                "schema_version": FORMAL_SOURCE_SQLITE_SCHEMA_VERSION,
                "declaration_count": str(len(declarations)),
                "declaration_fingerprint": stable_hash(
                    [
                        {
                            "source_id": declaration.source_id,
                            "path": declaration.path,
                            "line": declaration.line,
                            "name": declaration.name,
                            "signature": declaration.signature,
                            "reference": declaration.reference,
                            "reference_aliases": declaration.reference_aliases,
                            "module_summary": declaration.module_summary,
                            "declaration_doc": declaration.declaration_doc,
                            "section_summary": declaration.section_summary,
                            "module_group": declaration.module_group,
                            "module_group_summary": declaration.module_group_summary,
                        }
                        for declaration in declarations
                    ]
                ),
                "source_snapshots": json.dumps(
                    source_snapshots or {},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
            conn.executemany(
                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                sorted(metadata.items()),
            )
            conn.commit()

    def metadata(self) -> dict[str, str]:
        if not self.db_path.exists():
            return {}
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                return {
                    str(key): str(value)
                    for key, value in conn.execute(
                        "SELECT key, value FROM metadata"
                    ).fetchall()
                }
        except sqlite3.DatabaseError:
            return {}

    def source_snapshots(self) -> dict[str, object]:
        raw = self.metadata().get("source_snapshots", "")
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

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
        fts_query = _fts_query(query)
        if not fts_query:
            return []
        candidate_k = max(k * 12, 80)
        allowed_source_ids = tuple(
            dict.fromkeys(
                str(source_id)
                for source_id in source_scope_ids
                if str(source_id)
            )
        )
        source_clause = ""
        params: list[object] = [fts_query]
        if allowed_source_ids:
            placeholders = ", ".join("?" for _ in allowed_source_ids)
            source_clause = f" AND d.source_id IN ({placeholders})"
            params.extend(allowed_source_ids)
        params.append(candidate_k)
        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(
                f"""
                SELECT d.*, bm25(declarations_fts) AS rank
                FROM declarations_fts
                JOIN declarations d ON d.id = declarations_fts.decl_id
                WHERE declarations_fts MATCH ?
                {source_clause}
                ORDER BY rank
                LIMIT ?
                """,
                params,
            ).fetchall()
        q_tokens = _search_tokens(query)
        query_lookup_key = _declaration_lookup_key(query)
        hits: list[FormalSourceHit] = []
        for row in rows:
            decl = _decl_from_sqlite_row(row)
            hit = _score_declaration(
                decl,
                q_tokens,
                query_text=query,
                query_lookup_key=query_lookup_key,
            )
            if hit is not None:
                hits.append(hit)
        ordered = sorted(
            hits,
            key=lambda hit: (
                -hit.score,
                hit.declaration.source_id,
                hit.declaration.name,
            ),
        )
        return diversify_formal_source_hits(ordered, k=k)

    def load_declarations(self) -> list[FormalDeclaration]:
        """Read all declarations back from the persisted index.

        Downstream graph audits can reuse the already-built SQLite corpus
        instead of rescanning the formal source tree during release-style audits.
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
    """Index declarations from local formal sources.

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
        declaration_references = _declaration_references_from_markdown(location)
        reference_aliases = _reference_aliases_from_markdown(location)
        module_groups = _module_groups_from_markdown(location)
        root_rows: list[FormalDeclaration] = []
        for path in _iter_formal_source_files(
            root,
            location,
            max_file_bytes=max_file_bytes,
            max_files=max_files_per_root,
        ):
            root_rows.extend(_declarations_in_file(root, path, location))
        referenced_rows = _bind_declaration_references(
            root_rows,
            declaration_references,
            reference_aliases=reference_aliases,
        )
        rows.extend(
            _bind_module_groups(
                referenced_rows,
                module_groups,
                source_root_name=location.name,
            )
        )
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
    source_snapshots = (
        _formal_source_root_snapshots(roots)
        if db_path is not None
        else {}
    )
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
                if sqlite_index.source_snapshots() != source_snapshots:
                    raise sqlite3.DatabaseError(
                        "formal-source SQLite cache does not match the configured source snapshots"
                    )
                declarations = sqlite_index.load_declarations()
                if not _cache_covers_configured_roots(declarations, roots):
                    raise sqlite3.DatabaseError(
                        "formal-source SQLite cache is stale for the configured formal source roots"
                    )
                dependency_retriever = _optional_lean_rag_dependency_retriever(lean_rag_db_path)
                scoped_premise_retrievers = (
                    _optional_scoped_premise_retrievers()
                    if include_graph
                    else ()
                )
                if include_graph:
                    from .formal_source_hybrid import FormalSourceHybridRetriever

                    retriever = FormalSourceHybridRetriever(
                        declarations,
                        sqlite_index,
                        dependency_retriever=dependency_retriever,
                        scoped_premise_retrievers=scoped_premise_retrievers,
                    )
                else:
                    retriever = sqlite_index
                setattr(retriever, "cache_status", "hit")
                setattr(retriever, "cache_path", str(cache_file))
                _attach_lean_rag_metadata(retriever, dependency_retriever)
                _attach_scoped_premise_metadata(
                    retriever,
                    scoped_premise_retrievers,
                )
                return retriever
            except Exception:
                # Stale or incompatible cache. Rebuild below and overwrite it.
                if target_db.exists():
                    target_db.unlink()

    declarations = build_formal_source_index(roots=roots)
    if db_path is not None:
        sqlite_index = FormalSourceSqliteIndex.build(
            declarations,
            db_path,
            source_snapshots=source_snapshots,
        )
        if cache_file is not None:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            if Path(db_path).resolve() != cache_file.resolve():
                shutil.copy2(db_path, cache_file)
        dependency_retriever = _optional_lean_rag_dependency_retriever(lean_rag_db_path)
        scoped_premise_retrievers = (
            _optional_scoped_premise_retrievers()
            if include_graph
            else ()
        )
        if include_graph:
            from .formal_source_hybrid import FormalSourceHybridRetriever

            retriever = FormalSourceHybridRetriever(
                declarations,
                sqlite_index,
                dependency_retriever=dependency_retriever,
                scoped_premise_retrievers=scoped_premise_retrievers,
            )
        else:
            retriever = sqlite_index
        setattr(retriever, "cache_status", "miss" if cache_file is not None else "disabled")
        setattr(retriever, "cache_path", str(cache_file) if cache_file is not None else "")
        _attach_lean_rag_metadata(retriever, dependency_retriever)
        _attach_scoped_premise_metadata(
            retriever,
            scoped_premise_retrievers,
        )
        return retriever
    dependency_retriever = _optional_lean_rag_dependency_retriever(lean_rag_db_path)
    scoped_premise_retrievers = (
        _optional_scoped_premise_retrievers()
        if include_graph
        else ()
    )
    retriever: object = FormalSourceRetriever(declarations)
    if dependency_retriever is not None or scoped_premise_retrievers:
        from .formal_source_hybrid import FormalSourceDependencyHybridRetriever

        retriever = FormalSourceDependencyHybridRetriever(
            declarations,
            retriever,
            dependency_retriever,
            scoped_premise_retrievers=scoped_premise_retrievers,
        )
    setattr(retriever, "cache_status", "disabled")
    setattr(retriever, "cache_path", "")
    _attach_lean_rag_metadata(retriever, dependency_retriever)
    _attach_scoped_premise_metadata(
        retriever,
        scoped_premise_retrievers,
    )
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
        from .lean_rag_dependency import (
            LeanRagDependencyMultiRetriever,
            LeanRagDependencyRetriever,
        )

        healthy_retrievers = []
        for candidate in candidate_paths:
            source_id, source_aliases = _lean_rag_dependency_source_identity(
                candidate,
                explicit=bool(explicit_path),
            )
            retriever = LeanRagDependencyRetriever(
                candidate,
                source_id=source_id,
                source_aliases=source_aliases,
            )
            health = retriever.health_report()
            if health.get("all_ok"):
                setattr(retriever, "auto_discovered", not bool(explicit_path))
                setattr(retriever, "health_payload", health)
                healthy_retrievers.append(retriever)
                if explicit_path:
                    break
        if not healthy_retrievers:
            return None
        if len(healthy_retrievers) == 1:
            return healthy_retrievers[0]
        retriever = LeanRagDependencyMultiRetriever(tuple(healthy_retrievers))
        setattr(retriever, "auto_discovered", True)
        setattr(retriever, "health_payload", retriever.health_report())
        return retriever
    except Exception:
        return None


def _optional_scoped_premise_retrievers() -> tuple[object, ...]:
    from .formal_source_scoped_corpus import (
        discover_ai4slt_scoped_premise_retrievers,
    )

    return tuple(discover_ai4slt_scoped_premise_retrievers())


def _auto_lean_rag_db_candidates() -> tuple[Path, ...]:
    if os.environ.get("AI_STATISTICIAN_DISABLE_LEAN_RAG_AUTO", "").lower() in {
        "1",
        "true",
        "yes",
    }:
        return ()
    package_root = Path(__file__).resolve().parents[1]
    search_roots: list[Path] = []
    for root in (Path.cwd(), package_root):
        for candidate_root in (root, *root.parents[:4]):
            if candidate_root not in search_roots:
                search_roots.append(candidate_root)
    candidates = (
        *DEFAULT_LEAN_RAG_DB_CANDIDATES,
        *(root / DEFAULT_LEAN_RAG_DB_RELATIVE_PATH for root in search_roots),
        *(
            root / DEFAULT_AI4SLT_LEAN_RAG_DB_RELATIVE_PATH
            for root in search_roots
        ),
        (
            EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT
            / "build"
            / "ai_statistician_signed_lean_graph"
            / "stat_inference.sqlite"
        ),
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


def _lean_rag_dependency_source_identity(
    path: Path,
    *,
    explicit: bool,
) -> tuple[str, tuple[str, ...]]:
    """Bind an auto-discovered graph to its formal-source corpus."""

    normalized = str(path).replace("\\", "/").lower()
    if (
        path.name == "stat_learning.sqlite"
        or "current_status_ai4slt_lean_rag_dependency_graph" in normalized
    ):
        return "lean_stat_learning_theory", ("ai4slt",)
    if path.name == "stat_inference.sqlite":
        return (
            "empirical_process_lean",
            (
                "local_statinference_repo",
                "legacy_ai_statistician_statinference",
            ),
        )
    if explicit:
        return "lean_rag_dependency_graph", ()
    return "lean_rag_dependency_graph", ()


def _attach_lean_rag_metadata(retriever: object, dependency_retriever: object | None) -> None:
    dependency_paths = tuple(
        str(path)
        for path in (
            getattr(dependency_retriever, "db_paths", ())
            if dependency_retriever is not None
            else ()
        )
        if str(path)
    )
    if not dependency_paths and dependency_retriever is not None:
        dependency_path = str(getattr(dependency_retriever, "db_path", "") or "")
        dependency_paths = (dependency_path,) if dependency_path else ()
    setattr(retriever, "lean_rag_dependency_graph_enabled", dependency_retriever is not None)
    setattr(
        retriever,
        "lean_rag_dependency_graph_path",
        dependency_paths[0] if dependency_paths else "",
    )
    setattr(
        retriever,
        "lean_rag_dependency_graph_paths",
        dependency_paths,
    )
    setattr(
        retriever,
        "lean_rag_dependency_graph_source_ids",
        tuple(getattr(dependency_retriever, "source_ids", ()) or ())
        if dependency_retriever is not None
        else (),
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


def _attach_scoped_premise_metadata(
    retriever: object,
    scoped_premise_retrievers: tuple[object, ...],
) -> None:
    providers = tuple(scoped_premise_retrievers)
    setattr(retriever, "scoped_premise_corpus_enabled", bool(providers))
    setattr(
        retriever,
        "scoped_premise_corpus_source_ids",
        tuple(
            str(getattr(provider, "source_id", "") or "")
            for provider in providers
            if str(getattr(provider, "source_id", "") or "")
        ),
    )
    setattr(
        retriever,
        "scoped_premise_corpus_anchor_source_ids",
        tuple(
            dict.fromkeys(
                str(source_id)
                for provider in providers
                for source_id in (
                    getattr(provider, "anchor_source_ids", ()) or ()
                )
                if str(source_id)
            )
        ),
    )
    setattr(
        retriever,
        "scoped_premise_corpus_health",
        tuple(
            dict(provider.health_report())
            for provider in providers
            if callable(getattr(provider, "health_report", None))
        ),
    )


def _cache_covers_configured_roots(
    declarations: list[FormalDeclaration],
    roots: tuple[FormalSourceRoot, ...],
) -> bool:
    """Return whether a cached index still represents existing configured roots.

    The source inventory can grow as new formal libraries are mirrored locally.
    A syntactically healthy SQLite cache can still be stale if it predates those
    sources. Treat existing roots with at least one indexable formal source file
    as required source ids, so release-style retrieval does not silently ignore
    newly available formal libraries.
    """

    present_source_ids = {declaration.source_id for declaration in declarations}
    required_source_ids = {
        root.id
        for root in roots
        if _root_has_indexable_formal_source_file(root)
    }
    if not required_source_ids.issubset(present_source_ids):
        return False
    references_by_source: dict[str, set[str]] = {}
    reference_aliases_by_source: dict[str, set[str]] = {}
    for declaration in declarations:
        if declaration.reference:
            references_by_source.setdefault(
                declaration.source_id,
                set(),
            ).add(declaration.reference)
        if declaration.reference_aliases:
            reference_aliases_by_source.setdefault(
                declaration.source_id,
                set(),
            ).update(declaration.reference_aliases)
    for root in roots:
        location = Path(root.location).expanduser()
        if not location.exists():
            continue
        expected_references = set(
            _declaration_references_from_markdown(location).values()
        )
        if not expected_references.issubset(
            references_by_source.get(root.id, set())
        ):
            return False
        source_aliases = _reference_aliases_from_markdown(location)
        expected_reference_aliases = {
            alias
            for reference in expected_references
            for alias in _expanded_reference_aliases(
                reference,
                source_aliases,
            )
        }
        if not expected_reference_aliases.issubset(
            reference_aliases_by_source.get(root.id, set())
        ):
            return False
    return True


def _formal_source_root_snapshots(
    roots: tuple[FormalSourceRoot, ...],
) -> dict[str, object]:
    return {
        root.id: _formal_source_root_snapshot(root)
        for root in roots
    }


def _formal_source_root_snapshot(root: FormalSourceRoot) -> dict[str, object]:
    location = Path(root.location).expanduser()
    try:
        resolved = location.resolve()
    except OSError:
        resolved = location.absolute()
    snapshot: dict[str, object] = {
        "location": str(resolved),
        "source_type": root.source_type,
        "exists": location.is_dir(),
    }
    if not location.is_dir():
        return snapshot

    git_snapshot = _git_formal_source_root_snapshot(root, location)
    if git_snapshot is not None:
        snapshot.update(git_snapshot)
    else:
        snapshot.update(
            {
                "mode": "filesystem_inventory",
                "inventory_fingerprint": _formal_source_inventory_fingerprint(
                    root,
                    location,
                ),
            }
        )
    snapshot["support_file_fingerprints"] = _formal_source_support_file_fingerprints(
        location
    )
    return snapshot


def _git_formal_source_root_snapshot(
    root: FormalSourceRoot,
    location: Path,
) -> dict[str, object] | None:
    git_root_text = _run_git(location, "rev-parse", "--show-toplevel")
    if not git_root_text:
        return None
    git_root = Path(git_root_text).resolve()
    try:
        relative = location.resolve().relative_to(git_root)
    except (OSError, ValueError):
        return None
    relative_text = relative.as_posix()
    tree = _run_git(
        git_root,
        "rev-parse",
        "HEAD^{tree}" if not relative.parts else f"HEAD:{relative_text}",
    )
    if not tree:
        return None
    pathspec = relative_text or "."
    status = _run_git(
        git_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        pathspec,
    )
    if status is None:
        return None
    payload: dict[str, object] = {
        "mode": "git_tree",
        "git_root": str(git_root),
        "git_commit": _run_git(git_root, "rev-parse", "HEAD") or "",
        "git_tree": tree,
        "git_dirty": bool(status),
    }
    if status:
        payload["dirty_fingerprint"] = stable_hash(
            {
                "status": status,
                "inventory": _formal_source_inventory_fingerprint(
                    root,
                    location,
                ),
            }
        )
    return payload


def _run_git(cwd: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ("git", *args),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def _formal_source_inventory_fingerprint(
    root: FormalSourceRoot,
    location: Path,
) -> str:
    rows = []
    for path in _iter_formal_source_files(
        root,
        location,
        max_file_bytes=2_000_000,
        max_files=1500,
    ):
        try:
            stat = path.stat()
        except OSError:
            continue
        rows.append(
            (
                str(path.relative_to(location)),
                stat.st_size,
                stat.st_mtime_ns,
            )
        )
    return stable_hash(rows)


def _formal_source_support_file_fingerprints(
    location: Path,
) -> dict[str, str]:
    candidates = set(_source_readme_paths(location))
    for base in (location, location.parent):
        candidates.update(
            path
            for path in (
                base / "lean-toolchain",
                base / "lake-manifest.json",
            )
            if path.is_file()
        )
    fingerprints: dict[str, str] = {}
    for path in sorted(candidates):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        fingerprints[str(path.resolve())] = stable_hash(text)
    return fingerprints


def _root_has_indexable_formal_source_file(root: FormalSourceRoot) -> bool:
    location = Path(root.location).expanduser()
    if not location.exists():
        return False
    suffixes = _formal_source_suffixes(root)
    for dirpath, dirnames, filenames in os.walk(location):
        dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in SKIPPED_PATH_PARTS)
        for filename in filenames:
            if not filename.endswith(suffixes):
                continue
            path = Path(dirpath) / filename
            if _skip_path(path, base=location) or not _file_size_ok(path, 2_000_000):
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
    by_module_group: dict[str, int] = {}
    for decl in declarations:
        by_source[decl.source_id] = by_source.get(decl.source_id, 0) + 1
        by_kind[decl.kind] = by_kind.get(decl.kind, 0) + 1
        if decl.module_group:
            by_module_group[decl.module_group] = (
                by_module_group.get(decl.module_group, 0) + 1
            )
    db_path = out_dir / "formal_source_index.sqlite" if out_dir is not None else None
    if backend == "sqlite" and db_path is not None:
        retriever = FormalSourceSqliteIndex.build(
            declarations,
            db_path,
            source_snapshots=_formal_source_root_snapshots(roots),
        )
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
        "by_module_group": dict(sorted(by_module_group.items())),
        "n_declarations_with_docs": sum(
            1 for decl in declarations if decl.declaration_doc
        ),
        "n_declarations_with_section_summaries": sum(
            1 for decl in declarations if decl.section_summary
        ),
        "n_declarations_with_module_groups": sum(
            1 for decl in declarations if decl.module_group
        ),
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
            "reference": decl.reference,
            "reference_aliases": decl.reference_aliases,
            "module_summary": decl.module_summary,
            "declaration_doc": decl.declaration_doc,
            "section_summary": decl.section_summary,
            "module_group": decl.module_group,
            "module_group_summary": decl.module_group_summary,
        }
        for decl in decls
    ]
    return stable_hash(stable_rows)


def _ordered_search_tokens(text: str) -> list[str]:
    split_text = re.sub(r"[_'.]", " ", text)
    camel_split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", split_text)
    tokens: list[str] = []
    seen: set[str] = set()

    def add_token(token: str) -> None:
        normalized = token.lower()
        if (
            not normalized.strip()
            or normalized in STOP_TOKENS
            or not any(ch.isalnum() for ch in normalized)
            or normalized in seen
        ):
            return
        seen.add(normalized)
        tokens.append(normalized)

    for token in TOKEN_RE.findall(" ".join([split_text, text])):
        add_token(token)
    for token in TOKEN_RE.findall(camel_split):
        if len(token) >= 4 or (len(token) >= 2 and token.isupper()):
            add_token(token)
    return tokens


def _search_tokens(text: str) -> set[str]:
    """Tokenize formal names plus natural-language queries for declaration search."""

    return set(_ordered_search_tokens(text))


def _score_declaration(
    decl: FormalDeclaration,
    q_tokens: set[str],
    *,
    query_text: str = "",
    declaration_tokens: set[str] | None = None,
    module_summary_tokens: set[str] | frozenset[str] | None = None,
    declaration_doc_tokens: set[str] | frozenset[str] | None = None,
    section_summary_tokens: set[str] | frozenset[str] | None = None,
    module_group_tokens: set[str] | frozenset[str] | None = None,
    name_tokens: set[str] | None = None,
    shape_tokens: set[str] | None = None,
    import_tokens: set[str] | None = None,
    reference_tokens: set[str] | None = None,
    query_lookup_key: str = "",
    source_prominence_bonus: float | None = None,
) -> FormalSourceHit | None:
    d_tokens = (
        declaration_tokens
        if declaration_tokens is not None
        else _search_tokens(_decl_core_search_text(decl))
    )
    m_tokens = (
        module_summary_tokens
        if module_summary_tokens is not None
        else (
            _search_tokens(decl.module_summary)
            if decl.module_summary
            else _EMPTY_SEARCH_TOKENS
        )
    )
    ddoc_tokens = (
        declaration_doc_tokens
        if declaration_doc_tokens is not None
        else (
            _search_tokens(decl.declaration_doc)
            if decl.declaration_doc
            else _EMPTY_SEARCH_TOKENS
        )
    )
    section_tokens = (
        section_summary_tokens
        if section_summary_tokens is not None
        else (
            _search_tokens(decl.section_summary)
            if decl.section_summary
            else _EMPTY_SEARCH_TOKENS
        )
    )
    group_tokens = (
        module_group_tokens
        if module_group_tokens is not None
        else _search_tokens(
            " ".join(
                value
                for value in (
                    decl.module_group,
                    decl.module_group_summary,
                )
                if value
            )
        )
    )
    n_tokens = name_tokens if name_tokens is not None else _search_tokens(decl.name)
    s_tokens = (
        shape_tokens
        if shape_tokens is not None
        else _search_tokens(" ".join([decl.conclusion_head, decl.lhs_head, decl.rhs_head, " ".join(decl.premise_heads)]))
    )
    i_tokens = import_tokens if import_tokens is not None else _search_tokens(" ".join(decl.imports))
    r_tokens = (
        reference_tokens
        if reference_tokens is not None
        else (
            _search_tokens(
                " ".join((decl.reference, *decl.reference_aliases))
            )
            if decl.reference or decl.reference_aliases
            else _EMPTY_SEARCH_TOKENS
        )
    )
    core_overlap = q_tokens & d_tokens
    module_overlap = q_tokens & m_tokens
    declaration_doc_overlap = q_tokens & ddoc_tokens
    section_summary_overlap = q_tokens & section_tokens
    module_group_overlap = q_tokens & group_tokens
    reference_overlap = q_tokens & r_tokens
    overlap = (
        core_overlap
        | module_overlap
        | declaration_doc_overlap
        | section_summary_overlap
        | module_group_overlap
        | reference_overlap
    )
    if not overlap:
        return None
    # Repeated prose across docs, sections, and README taxonomy is corroboration,
    # not extra lexical evidence. Credit each metadata token at its strongest tier.
    declaration_doc_only_overlap = declaration_doc_overlap - core_overlap
    section_summary_only_overlap = (
        section_summary_overlap
        - core_overlap
        - declaration_doc_overlap
    )
    module_only_overlap = (
        module_overlap
        - core_overlap
        - declaration_doc_overlap
        - section_summary_overlap
    )
    module_group_only_overlap = (
        module_group_overlap
        - core_overlap
        - declaration_doc_overlap
        - section_summary_overlap
        - module_overlap
    )
    name_bonus = 2.0 * len(q_tokens & n_tokens)
    shape_bonus = 1.5 * len(q_tokens & s_tokens)
    import_bonus = 0.25 * len(q_tokens & i_tokens)
    reference_bonus = 2.5 * len(reference_overlap)
    resolved_query_lookup_key = (
        query_lookup_key or _declaration_lookup_key(query_text)
    )
    exact_name_bonus = _exact_declaration_name_bonus(
        decl.name,
        query_text,
        query_lookup_key=resolved_query_lookup_key,
    )
    semantic_name_bonus = _semantic_declaration_name_bonus(
        decl.name,
        q_tokens=q_tokens,
        name_tokens=n_tokens,
        query_text=query_text,
        query_lookup_key=resolved_query_lookup_key,
    )
    source_authored_prominence_bonus = (
        source_prominence_bonus
        if source_prominence_bonus is not None
        else _source_authored_declaration_prominence_bonus(decl)
    )
    source_bonus = 1.0 if decl.source_id.startswith("mathlib") else 1.5
    score = (
        len(core_overlap)
        + MODULE_SUMMARY_TOKEN_WEIGHT * len(module_only_overlap)
        + DECLARATION_DOC_TOKEN_WEIGHT * len(
            declaration_doc_only_overlap
        )
        + SECTION_SUMMARY_TOKEN_WEIGHT * len(
            section_summary_only_overlap
        )
        + MODULE_GROUP_TOKEN_WEIGHT * len(
            module_group_only_overlap
        )
        + name_bonus
        + shape_bonus
        + import_bonus
        + reference_bonus
        + exact_name_bonus
        + semantic_name_bonus
        + source_authored_prominence_bonus
        + source_bonus
    )
    return FormalSourceHit(decl, score, tuple(sorted(overlap)[:16]))


def _exact_declaration_name_bonus(
    name: str,
    query: str,
    *,
    query_lookup_key: str = "",
) -> float:
    query_key = query_lookup_key or _declaration_lookup_key(query)
    if not query_key:
        return 0.0
    full_key = _declaration_lookup_key(name)
    short_key = _declaration_lookup_key(name.rsplit(".", 1)[-1])
    return 16.0 if query_key in {full_key, short_key} else 0.0


def _semantic_declaration_name_bonus(
    name: str,
    *,
    q_tokens: set[str],
    name_tokens: set[str],
    query_text: str,
    query_lookup_key: str = "",
) -> float:
    """Reward source naming that closely expresses the requested concept."""

    overlap_count = len(q_tokens & name_tokens)
    coverage_bonus = (
        min(
            DECLARATION_NAME_COVERAGE_BONUS_CAP,
            float(overlap_count * overlap_count) / max(len(q_tokens), 1),
        )
        if overlap_count >= 2
        else 0.0
    )
    short_key = _declaration_lookup_key(name.rsplit(".", 1)[-1])
    query_key = query_lookup_key or _declaration_lookup_key(query_text)
    concept_anchor_bonus = (
        DECLARATION_NAME_CONCEPT_ANCHOR_BONUS
        if len(short_key) >= 6 and short_key in query_key
        else 0.0
    )
    return coverage_bonus + concept_anchor_bonus


def _source_authored_declaration_prominence_bonus(
    decl: FormalDeclaration,
) -> float:
    """Use source-authored public-API signals without encoding theorem names."""

    bonus = (
        SOURCE_REFERENCE_PROMINENCE_BONUS
        if decl.reference or decl.reference_aliases
        else 0.0
    )
    short_key = _declaration_lookup_key(decl.name.rsplit(".", 1)[-1])
    module_summary_key = _declaration_lookup_key(decl.module_summary)
    if (
        len(short_key) >= 6
        and module_summary_key
        and short_key in module_summary_key
    ):
        bonus += SOURCE_OUTLINE_PROMINENCE_BONUS
    return bonus


def _declaration_lookup_key(value: str) -> str:
    return "".join(
        character
        for character in str(value or "").strip(" `").casefold()
        if character.isalnum()
    )


def diversify_formal_source_hits(
    hits: list[FormalSourceHit],
    *,
    k: int,
    max_sources: int = 8,
    min_relative_score: float = 0.5,
    preserve_top_n: int = 1,
) -> list[FormalSourceHit]:
    """Preserve the strongest rows before adding relevant corpus diversity."""

    limit = max(int(k), 0)
    if limit == 0 or not hits:
        return []
    if limit == 1:
        return hits[:1]

    def hit_key(hit: FormalSourceHit) -> tuple[str, str, int, str]:
        declaration = hit.declaration
        return (
            declaration.source_id,
            declaration.path,
            declaration.line,
            declaration.name,
        )

    top_score = max(float(hits[0].score), 0.0)
    relevance_floor = top_score * min_relative_score
    preserve_count = min(
        limit,
        len(hits),
        max(1, int(preserve_top_n)),
    )
    selected = list(hits[:preserve_count])
    selected_keys = {hit_key(hit) for hit in selected}
    selected_sources = {hit.declaration.source_id for hit in selected}
    source_candidates: dict[str, tuple[float, int, FormalSourceHit]] = {}
    for rank, hit in enumerate(hits[preserve_count:], start=preserve_count):
        source_id = hit.declaration.source_id
        if source_id in selected_sources or float(hit.score) < relevance_floor:
            continue
        name_anchor_count = len(
            set(hit.matched_terms) & _search_tokens(hit.declaration.name)
        )
        priority = float(hit.score) + 1.5 * name_anchor_count
        if source_id not in source_candidates:
            source_candidates[source_id] = (priority, rank, hit)
    diverse_candidates = sorted(
        source_candidates.values(),
        key=lambda row: (-row[0], row[1], row[2].declaration.source_id),
    )
    diversity_slots = max(
        0,
        min(max_sources, limit) - len(selected_sources),
    )
    for _, _, hit in diverse_candidates[:diversity_slots]:
        selected.append(hit)
        selected_keys.add(hit_key(hit))
        selected_sources.add(hit.declaration.source_id)
    for hit in hits[preserve_count:]:
        if len(selected) >= limit:
            break
        key = hit_key(hit)
        if key in selected_keys:
            continue
        selected.append(hit)
        selected_keys.add(key)
    return selected[:limit]


def _decl_core_search_text(decl: FormalDeclaration) -> str:
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
        ]
    )


def _fts_tokens(text: str) -> list[str]:
    return [
        token
        for token in _ordered_search_tokens(text)
        if len(token) > 1
        and all(character == "_" or character.isalnum() for character in token)
    ]


def _fts_text(text: str) -> str:
    return " ".join(_fts_tokens(text))


def _fts_query(text: str) -> str:
    # FTS only generates a bounded candidate set; the full query token set is
    # still used by _score_declaration for deterministic reranking.
    tokens = _fts_tokens(text)[:MAX_SQLITE_FTS_QUERY_TOKENS]
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
        reference=str(row[16]) if len(row) > 16 else "",
        reference_aliases=(
            tuple(json.loads(row[17])) if len(row) > 17 else ()
        ),
        module_summary=str(row[18]) if len(row) > 18 else "",
        declaration_doc=str(row[19]) if len(row) > 19 else "",
        section_summary=str(row[20]) if len(row) > 20 else "",
        module_group=str(row[21]) if len(row) > 21 else "",
        module_group_summary=str(row[22]) if len(row) > 22 else "",
    )


def _declaration_signature(
    lines: list[str],
    start_idx: int,
    *,
    language: str = "lean",
    max_lines: int = 64,
    max_chars: int = 900,
) -> str:
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
        if offset > 0 and _line_starts_new_formal_item(line):
            break
        code_line = line.split("--", 1)[0] if language == "lean" else line
        body_delimiter = (
            _lean_body_delimiter(code_line)
            if language == "lean"
            else code_line.find(":=")
        )
        body_starts = body_delimiter >= 0
        if body_starts:
            code_line = code_line[:body_delimiter]
        code_line = code_line.strip()
        if language == "lean" and code_line.endswith((" by", " where")):
            code_line = code_line.rsplit(" ", 1)[0].rstrip()
            body_starts = True
        if code_line and code_line not in {"by", "where"}:
            chunks.append(code_line)
        stripped = code_line.strip()
        if body_starts or (
            language != "lean" and stripped.endswith(".")
        ):
            break
    signature = " ".join(chunk for chunk in chunks if chunk)
    signature = re.sub(r"\s+", " ", signature).strip()
    return _bounded_outline(signature, max_chars=max_chars)


def _lean_body_delimiter(code_line: str) -> int:
    proof_match = re.search(r":=\s*by\b", code_line)
    if proof_match:
        return proof_match.start()
    stripped = code_line.lstrip()
    if stripped.startswith(("let ", "letI ")):
        return -1
    return code_line.rfind(":=")


def _bounded_outline(value: str, *, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    marker = " ... "
    available = max(max_chars - len(marker), 2)
    head_chars = available // 2
    tail_chars = available - head_chars
    return value[:head_chars].rstrip() + marker + value[-tail_chars:].lstrip()


def _compress_signature(signature: str) -> dict[str, object]:
    """Extract theorem-shape features for cheap premise retrieval."""

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
    for match in re.finditer(
        rf"[\(\{{\[][^:\]\)\}}]+:\s*({LEAN_IDENTIFIER_PATTERN})",
        signature,
    ):
        heads.append(match.group(1).split(".")[-1])
    return heads


def _head_symbol(text: str) -> str:
    match = re.search(
        rf"{LEAN_IDENTIFIER_PATTERN}|[∀∃∧∨→↔=≤≥<>+*/^]+",
        text,
    )
    if not match:
        return ""
    return match.group(0).split(".")[-1]


def _name_like_symbols(text: str) -> list[str]:
    symbols = []
    for token in re.findall(LEAN_IDENTIFIER_PATTERN, text):
        tail = token.split(".")[-1]
        if len(tail) >= 3 and tail.lower() not in STOP_TOKENS:
            symbols.append(tail)
    return symbols


def _source_readme_paths(root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            {
                path
                for candidate_root in (root, root.parent)
                for path in candidate_root.glob("README*")
                if path.is_file()
                and path.suffix.lower() in {".md", ".markdown"}
            }
        )
    )


def _declaration_references_from_markdown(root: Path) -> dict[str, str]:
    """Extract declaration/source crosswalks from root README tables."""

    references: dict[str, str] = {}
    for path in _source_readme_paths(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx in range(len(lines) - 2):
            headers = _markdown_table_cells(lines[idx])
            separator = _markdown_table_cells(lines[idx + 1])
            if not headers or not _markdown_table_separator(separator, len(headers)):
                continue
            normalized_headers = [
                re.sub(r"[^a-z0-9]+", "", header.lower())
                for header in headers
            ]
            name_index = next(
                (
                    pos
                    for pos, value in enumerate(normalized_headers)
                    if value
                    in {
                        "name",
                        "leanname",
                        "declaration",
                        "leandeclaration",
                    }
                ),
                None,
            )
            reference_index = next(
                (
                    pos
                    for pos, value in enumerate(normalized_headers)
                    if value.startswith("reference")
                ),
                None,
            )
            if name_index is None or reference_index is None:
                continue
            row_index = idx + 2
            while row_index < len(lines):
                cells = _markdown_table_cells(lines[row_index])
                if len(cells) != len(headers):
                    break
                name = _markdown_declaration_name(cells[name_index])
                reference = _markdown_cell_text(cells[reference_index])
                if name and reference:
                    references.setdefault(name, reference)
                row_index += 1
    return references


def _reference_aliases_from_markdown(root: Path) -> dict[str, str]:
    """Extract source-authored abbreviation and bibliography aliases."""

    aliases: dict[str, str] = {}
    bibliography_candidates: dict[str, set[str]] = {}
    alias_pattern = re.compile(
        r"(?:^|[\s*(])([A-Z][A-Z0-9]{1,8})\s*=\s*([^\n)]{3,220})\)"
    )
    for path in _source_readme_paths(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in alias_pattern.finditer(text):
            alias = match.group(1).strip()
            expansion = _markdown_cell_text(match.group(2)).strip(" .")
            if alias and expansion:
                aliases.setdefault(alias, expansion)
        for line in text.splitlines():
            bibliography_row = _markdown_bibliography_alias(line)
            if bibliography_row is None:
                continue
            key, expansion = bibliography_row
            bibliography_candidates.setdefault(key, set()).add(expansion)
    for key, expansions in bibliography_candidates.items():
        if len(expansions) == 1:
            aliases.setdefault(key, next(iter(expansions)))
    return aliases


def _module_groups_from_markdown(root: Path) -> tuple[_FormalModuleGroup, ...]:
    """Extract source-authored module layers from README overview tables.

    The parser is intentionally generic: a formal library can call the first
    column layer, group, or category, and can list files or directory prefixes
    in the modules column. These rows describe organization only; they never
    authorize a declaration or proof.
    """

    groups: list[_FormalModuleGroup] = []
    seen: set[tuple[str, tuple[str, ...], str]] = set()
    for path in _source_readme_paths(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx in range(len(lines) - 2):
            headers = _markdown_table_cells(lines[idx])
            separator = _markdown_table_cells(lines[idx + 1])
            if not headers or not _markdown_table_separator(separator, len(headers)):
                continue
            normalized_headers = [
                re.sub(r"[^a-z0-9]+", "", header.lower())
                for header in headers
            ]
            group_index = next(
                (
                    pos
                    for pos, value in enumerate(normalized_headers)
                    if value in {"layer", "group", "category", "modulegroup"}
                ),
                None,
            )
            modules_index = next(
                (
                    pos
                    for pos, value in enumerate(normalized_headers)
                    if value in {"module", "modules", "files", "paths"}
                ),
                None,
            )
            summary_index = next(
                (
                    pos
                    for pos, value in enumerate(normalized_headers)
                    if value
                    in {
                        "whatsinside",
                        "description",
                        "contents",
                        "role",
                        "summary",
                    }
                ),
                None,
            )
            if group_index is None or modules_index is None:
                continue
            row_index = idx + 2
            while row_index < len(lines):
                cells = _markdown_table_cells(lines[row_index])
                if len(cells) != len(headers):
                    break
                name = _markdown_cell_text(cells[group_index])
                patterns = _markdown_module_patterns(
                    cells[modules_index],
                    source_root_name=root.name,
                )
                summary = (
                    _markdown_cell_text(cells[summary_index])
                    if summary_index is not None
                    else ""
                )
                key = (name, patterns, summary)
                if name and patterns and key not in seen:
                    seen.add(key)
                    groups.append(
                        _FormalModuleGroup(
                            name=name,
                            module_patterns=patterns,
                            summary=summary,
                        )
                    )
                row_index += 1
    return tuple(groups)


def _markdown_module_patterns(
    cell: str,
    *,
    source_root_name: str = "",
) -> tuple[str, ...]:
    code_values = re.findall(r"`([^`]+)`", cell)
    raw_values = code_values or re.split(r"[,;]", _markdown_cell_text(cell))
    patterns = [
        normalized
        for value in raw_values
        if (
            normalized := _normalize_module_pattern(
                value,
                source_root_name=source_root_name,
            )
        )
    ]
    return tuple(dict.fromkeys(patterns))


def _normalize_module_pattern(
    value: str,
    *,
    source_root_name: str = "",
) -> str:
    pattern = str(value or "").strip().replace("\\", "/")
    pattern = re.sub(r"\s+", "", pattern)
    pattern = pattern.removeprefix("./").removesuffix(".lean").strip("` /")
    if "/" not in pattern:
        pattern = pattern.replace(".", "/")
    root_prefix = str(source_root_name or "").strip().replace(".", "/").strip("/")
    if root_prefix and pattern == root_prefix:
        pattern = ""
    elif root_prefix and pattern.startswith(root_prefix + "/"):
        pattern = pattern[len(root_prefix) + 1 :]
    return pattern.strip("` /")


def _bind_module_groups(
    declarations: list[FormalDeclaration],
    groups: tuple[_FormalModuleGroup, ...],
    *,
    source_root_name: str = "",
) -> list[FormalDeclaration]:
    if not groups:
        return declarations
    bound: list[FormalDeclaration] = []
    for declaration in declarations:
        group = _module_group_for_path(
            declaration.path,
            groups,
            source_root_name=source_root_name,
        )
        if group is None:
            bound.append(declaration)
            continue
        bound.append(
            replace(
                declaration,
                module_group=group.name,
                module_group_summary=group.summary,
            )
        )
    return bound


def _module_group_for_path(
    path: str,
    groups: tuple[_FormalModuleGroup, ...],
    *,
    source_root_name: str = "",
) -> _FormalModuleGroup | None:
    path_key = _normalize_module_pattern(
        path,
        source_root_name=source_root_name,
    )
    matches: list[tuple[int, _FormalModuleGroup]] = []
    for group in groups:
        for raw_pattern in group.module_patterns:
            pattern = _normalize_module_pattern(
                raw_pattern,
                source_root_name=source_root_name,
            )
            prefix = pattern.rstrip("/")
            if not prefix:
                continue
            if path_key == prefix or path_key.startswith(prefix + "/"):
                matches.append((len(prefix), group))
    if not matches:
        return None
    matches.sort(key=lambda row: (-row[0], row[1].name))
    return matches[0][1]


def _markdown_bibliography_alias(line: str) -> tuple[str, str] | None:
    """Return an author/year key and title from one Markdown bibliography row."""

    match = re.match(
        r"^\s*[-*]\s+(.+?)\s*\((\d{4}[a-z]?)\)\.\s*(.+)$",
        line,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    authors, year, remainder = match.groups()
    first_author = re.search(r"[A-Za-z][A-Za-z'-]+", authors)
    title_match = re.search(r"(?:\*|_)([^*_]{3,260})(?:\*|_)", remainder)
    if first_author is None or title_match is None:
        return None
    author_key = re.sub(r"[^a-z0-9]+", "", first_author.group(0).lower())
    if not author_key:
        return None
    clean_authors = re.sub(r"\s+", " ", authors).strip(" .")
    title = _markdown_cell_text(title_match.group(1)).strip(" .")
    if not title:
        return None
    key = f"author_year:{author_key}:{year.lower()}"
    return key, f"{clean_authors} ({year}), {title}"[:360]


def _expanded_reference_aliases(
    reference: str,
    aliases: dict[str, str],
) -> tuple[str, ...]:
    expanded_rows: list[str] = []
    abbreviation_match = re.match(
        r"^([A-Z][A-Z0-9]{1,8})(?=$|[\s:-])",
        reference,
    )
    if abbreviation_match is not None:
        abbreviation = abbreviation_match.group(1)
        expansion = aliases.get(abbreviation, "").strip()
        suffix = reference[abbreviation_match.end() :].lstrip(" :-")
        expanded = " ".join(value for value in (expansion, suffix) if value)
        if expansion and expanded and expanded != reference:
            expanded_rows.append(expanded)

    citation_match = re.match(
        r"^([A-Z][A-Za-z'-]+)(?:\s+et\s+al\.)?\s*\((\d{4}[a-z]?)\)",
        reference,
        flags=re.IGNORECASE,
    )
    if citation_match is not None:
        author_key = re.sub(
            r"[^a-z0-9]+",
            "",
            citation_match.group(1).lower(),
        )
        key = f"author_year:{author_key}:{citation_match.group(2).lower()}"
        expansion = aliases.get(key, "").strip()
        suffix = reference[citation_match.end() :].lstrip(" ,:-")
        expanded = " ".join(value for value in (expansion, suffix) if value)
        if expansion and expanded and expanded != reference:
            expanded_rows.append(expanded)
    return tuple(dict.fromkeys(expanded_rows))


def _bind_declaration_references(
    declarations: list[FormalDeclaration],
    references: dict[str, str],
    *,
    reference_aliases: dict[str, str] | None = None,
) -> list[FormalDeclaration]:
    """Bind exact names and globally unique short names to source references."""

    short_name_counts = Counter(
        declaration.name.rsplit(".", 1)[-1] for declaration in declarations
    )
    exact_declaration_names = {
        declaration.name
        for declaration in declarations
    }
    unique_short_names = {
        short_name
        for short_name, count in short_name_counts.items()
        if count == 1
    }
    already_bound_reference_names = {
        reference_name
        for reference_name in references
        if (
            reference_name in exact_declaration_names
            or reference_name in unique_short_names
        )
    }
    renamed_reference_candidates: dict[str, list[str]] = {}
    for reference_name, reference in references.items():
        if reference_name in already_bound_reference_names:
            continue
        reference_key = _declaration_lookup_key(reference_name)
        if len(reference_key) < 8:
            continue
        candidates = [
            declaration
            for declaration in declarations
            if _declaration_lookup_key(
                declaration.name.rsplit(".", 1)[-1]
            ).startswith(reference_key)
        ]
        if len(candidates) == 1:
            renamed_reference_candidates.setdefault(
                candidates[0].name,
                [],
            ).append(reference)
    renamed_references = {
        declaration_name: values[0]
        for declaration_name, values in renamed_reference_candidates.items()
        if len(values) == 1
    }

    bound: list[FormalDeclaration] = []
    for declaration in declarations:
        short_name = declaration.name.rsplit(".", 1)[-1]
        reference = references.get(declaration.name, "")
        if not reference and short_name_counts[short_name] == 1:
            reference = references.get(short_name, "")
        if not reference:
            reference = renamed_references.get(declaration.name, "")
        if reference:
            bound.append(
                replace(
                    declaration,
                    reference=reference,
                    reference_aliases=_expanded_reference_aliases(
                        reference,
                        reference_aliases or {},
                    ),
                )
            )
        else:
            bound.append(declaration)
    return bound


def _markdown_table_cells(line: str) -> list[str]:
    if "|" not in line:
        return []
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _markdown_table_separator(cells: list[str], width: int) -> bool:
    return len(cells) == width and all(
        re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))
        for cell in cells
    )


def _markdown_cell_text(cell: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cell)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text.replace("`", "")).strip()


def _markdown_declaration_name(cell: str) -> str:
    code_name = re.search(r"`([^`]+)`", cell)
    text = _markdown_cell_text(code_name.group(1) if code_name else cell)
    return text.split()[0] if text else ""


def _clean_lean_doc_text(text: str, *, max_chars: int) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s*", "", text)
    text = re.sub(r"```(?:lean4?|text)?", " ", text, flags=re.IGNORECASE)
    text = text.replace("```", " ").replace("`", "")
    text = text.replace("**", "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[: max(0, int(max_chars))]


def _lean_block_doc_from_start(
    lines: list[str],
    start_idx: int,
    *,
    marker: str,
    max_chars: int,
    max_lines: int = 160,
) -> str:
    fragments: list[str] = []
    for offset in range(max(1, int(max_lines))):
        pos = start_idx + offset
        if pos >= len(lines):
            break
        line = lines[pos]
        if offset == 0:
            marker_pos = line.find(marker)
            if marker_pos < 0:
                return ""
            line = line[marker_pos + len(marker) :]
        end = line.find("-/")
        if end >= 0:
            fragments.append(line[:end])
            return _clean_lean_doc_text(
                "\n".join(fragments),
                max_chars=max_chars,
            )
        fragments.append(line)
    return ""


def _lean_declaration_doc(
    lines: list[str],
    start_idx: int,
    *,
    max_chars: int = 1600,
) -> str:
    """Return the bounded `/-- ... -/` doc immediately governing a declaration."""

    pos = start_idx - 1
    while pos >= 0:
        stripped = lines[pos].strip()
        if not stripped or re.match(r"^(?:omit|include)\b.*\bin$", stripped):
            pos -= 1
            continue
        if stripped.startswith("@["):
            pos -= 1
            continue
        break
    if pos < 0 or "-/" not in lines[pos]:
        return ""
    end_idx = pos
    for pos in range(end_idx, max(-1, end_idx - 160), -1):
        line = lines[pos]
        if "/-!" in line:
            return ""
        marker_pos = line.find("/--")
        if marker_pos < 0:
            continue
        raw = "\n".join(lines[pos : end_idx + 1])
        raw = raw[raw.find("/--") + 3 :]
        raw = raw[: raw.rfind("-/")]
        return _clean_lean_doc_text(raw, max_chars=max_chars)
    return ""


def _lean_source_without_comments_preserve_lines(source: str) -> str:
    """Mask nested Lean comments and strings while preserving source lines."""

    output: list[str] = []
    index = 0
    block_depth = 0
    in_string = False
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if block_depth:
            if char == "/" and next_char == "-":
                block_depth += 1
                output.extend("  ")
                index += 2
                continue
            if char == "-" and next_char == "/":
                block_depth -= 1
                output.extend("  ")
                index += 2
                continue
            output.append("\n" if char == "\n" else " ")
            index += 1
            continue
        if in_string:
            output.append("\n" if char == "\n" else " ")
            if char == "\\" and index + 1 < len(source):
                escaped = source[index + 1]
                output.append("\n" if escaped == "\n" else " ")
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue
        if char == "-" and next_char == "-":
            while index < len(source) and source[index] != "\n":
                output.append(" ")
                index += 1
            continue
        if char == "/" and next_char == "-":
            block_depth = 1
            output.extend("  ")
            index += 2
            continue
        if char == '"':
            in_string = True
            output.append(" ")
            index += 1
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _lean_module_summary(
    lines: list[str],
    *,
    max_chars: int = 800,
) -> str:
    """Return the bounded leading `/-! ... -/` module documentation."""

    collecting = False
    fragments: list[str] = []
    for line in lines:
        if not collecting:
            if DECL_RE.match(line):
                break
            marker = line.find("/-!")
            if marker < 0:
                continue
            collecting = True
            line = line[marker + 3 :]
        end = line.find("-/")
        if end >= 0:
            fragments.append(line[:end])
            break
        fragments.append(line)
    if not fragments:
        return ""
    return _clean_lean_doc_text(
        "\n".join(fragments),
        max_chars=max_chars,
    )


def _declarations_in_file(
    root: FormalSourceRoot,
    path: Path,
    base: Path,
) -> list[FormalDeclaration]:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    lines = source.splitlines()
    rel = str(path.relative_to(base))
    language = _formal_source_language(root, path)
    parse_lines = (
        _lean_source_without_comments_preserve_lines(source).splitlines()
        if language == "lean"
        else lines
    )
    module_summary = _lean_module_summary(lines) if language == "lean" else ""
    current_section_summary = ""
    saw_declaration = False
    namespace_stack: list[str] = []
    lean_scope_stack: list[tuple[str, str, tuple[str, ...]]] = []
    imports: list[str] = []
    rows: list[FormalDeclaration] = []
    for idx, line in enumerate(lines, start=1):
        zero_idx = idx - 1
        parse_line = parse_lines[zero_idx] if zero_idx < len(parse_lines) else ""
        if language == "lean":
            module_doc_pos = line.find("/-!")
            if module_doc_pos >= 0 and not line[:module_doc_pos].strip():
                if saw_declaration:
                    current_section_summary = _lean_block_doc_from_start(
                        lines,
                        zero_idx,
                        marker="/-!",
                        max_chars=800,
                    )
        source_line = parse_line if language == "lean" else line
        import_items = _imports_from_line(source_line, language)
        if import_items:
            imports.extend(import_items)
            continue
        namespace_name = _namespace_open_from_line(source_line, language)
        if namespace_name:
            namespace_parts = tuple(namespace_name.split("."))
            namespace_stack.extend(namespace_parts)
            if language == "lean":
                lean_scope_stack.append(
                    ("namespace", namespace_name, namespace_parts)
                )
            continue
        if language == "lean":
            section_match = SECTION_RE.match(source_line)
            if section_match:
                lean_scope_stack.append(
                    ("section", section_match.group(1) or "", ())
                )
                continue
        end_name = _namespace_close_from_line(source_line, language)
        if end_name is not None:
            if language == "lean":
                _close_lean_scope(
                    lean_scope_stack,
                    namespace_stack,
                    end_name=end_name,
                )
            elif namespace_stack:
                _pop_namespace(namespace_stack, end_name)
            continue
        decl = _declaration_from_line(source_line, language)
        if decl is None:
            continue
        kind, raw_name = decl
        active_namespace = ".".join(namespace_stack)
        name = _qualified_declaration_name(
            raw_name,
            active_namespace,
            language=language,
        )
        namespace = name.rsplit(".", 1)[0] if "." in name else ""
        signature = _declaration_signature(
            parse_lines,
            idx - 1,
            language=language,
        )
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
                module_summary=module_summary,
                declaration_doc=(
                    _lean_declaration_doc(lines, zero_idx)
                    if language == "lean"
                    else ""
                ),
                section_summary=current_section_summary,
            )
        )
        saw_declaration = True
    return rows


def _qualified_declaration_name(
    raw_name: str,
    namespace: str,
    *,
    language: str,
) -> str:
    if language == "lean" and raw_name.startswith("_root_."):
        return raw_name.removeprefix("_root_.")
    if language != "lean" and "." in raw_name:
        return raw_name
    return f"{namespace}.{raw_name}" if namespace else raw_name


def _line_starts_new_formal_item(line: str) -> bool:
    return any(
        regex.match(line)
        for regex in (
            DECL_RE,
            ROCQ_DECL_RE,
            ISABELLE_DECL_RE,
            AGDA_DECL_RE,
            NAMESPACE_RE,
            SECTION_RE,
            END_RE,
            ROCQ_NAMESPACE_RE,
            ROCQ_END_RE,
            ISABELLE_THEORY_RE,
        )
    )


def _imports_from_line(line: str, language: str) -> list[str]:
    if language == "rocq":
        match = ROCQ_IMPORT_RE.match(line)
        return _parse_imports(match.group(1)) if match else []
    if language == "isabelle":
        match = ISABELLE_IMPORTS_RE.match(line)
        return _parse_imports(match.group(1)) if match else []
    if language == "agda":
        text = line.strip()
        if text.startswith("open import "):
            return _parse_imports(text.removeprefix("open import "))
        if text.startswith("import "):
            return _parse_imports(text.removeprefix("import "))
        return []
    match = IMPORT_RE.match(line)
    return _parse_imports(match.group(1)) if match else []


def _namespace_open_from_line(line: str, language: str) -> str:
    if language == "rocq":
        match = ROCQ_NAMESPACE_RE.match(line)
        return match.group(1) if match else ""
    if language == "isabelle":
        match = ISABELLE_THEORY_RE.match(line)
        return match.group(1) if match else ""
    if language == "agda":
        module_match = re.match(
            r"^\s*module\s+([A-Za-z_][A-Za-z0-9_'.-]*)\b",
            line,
        )
        return module_match.group(1).replace("-", "_") if module_match else ""
    match = NAMESPACE_RE.match(line)
    return match.group(1) if match else ""


def _namespace_close_from_line(line: str, language: str) -> str | None:
    if language == "rocq":
        match = ROCQ_END_RE.match(line)
        return match.group(1) if match else None
    if language == "isabelle":
        return "" if line.strip() == "end" else None
    if language == "agda":
        return None
    match = END_RE.match(line)
    return (match.group(1) or "") if match else None


def _pop_namespace(namespace_stack: list[str], end_name: str | None) -> None:
    if end_name:
        parts = end_name.split(".")
        if namespace_stack[-len(parts) :] == parts:
            del namespace_stack[-len(parts) :]
            return
    namespace_stack.pop()


def _close_lean_scope(
    scope_stack: list[tuple[str, str, tuple[str, ...]]],
    namespace_stack: list[str],
    *,
    end_name: str,
) -> None:
    if not scope_stack:
        return
    close_from = len(scope_stack) - 1
    if end_name:
        close_from = next(
            (
                idx
                for idx in range(len(scope_stack) - 1, -1, -1)
                if scope_stack[idx][1] == end_name
                or scope_stack[idx][1].rsplit(".", 1)[-1] == end_name
            ),
            -1,
        )
        if close_from < 0:
            return
    closing = scope_stack[close_from:]
    del scope_stack[close_from:]
    for kind, _, namespace_parts in reversed(closing):
        if kind != "namespace" or not namespace_parts:
            continue
        width = len(namespace_parts)
        if tuple(namespace_stack[-width:]) == namespace_parts:
            del namespace_stack[-width:]


def _declaration_from_line(line: str, language: str) -> tuple[str, str] | None:
    if language == "rocq":
        match = ROCQ_DECL_RE.match(line)
        if not match:
            return None
        kind, raw_name = match.groups()
        return kind.lower(), raw_name
    if language == "isabelle":
        match = ISABELLE_DECL_RE.match(line)
        if not match:
            return None
        return match.groups()
    if language == "agda":
        match = AGDA_DECL_RE.match(line)
        if not match:
            return None
        name = match.group(1).replace("-", "_")
        return "signature", name
    match = DECL_RE.match(line)
    return match.groups() if match else None


def _parse_imports(import_tail: str) -> list[str]:
    cleaned = import_tail.split("--", 1)[0].strip()
    cleaned = cleaned.split("(*", 1)[0].strip()
    return [
        item.strip('"')
        for item in cleaned.split()
        if re.match(r"^\"?[A-Za-z_][A-Za-z0-9_'.-]*\"?$", item)
    ]


def _iter_lean_files(location: Path, *, max_file_bytes: int, max_files: int):
    """Yield a capped, deterministic stream of Lean files.

    Kept as a compatibility wrapper around the generic formal-source iterator.
    """

    root = FormalSourceRoot("lean_compat", str(location), "lean_library")
    yield from _iter_formal_source_files(
        root,
        location,
        max_file_bytes=max_file_bytes,
        max_files=max_files,
    )


def _iter_formal_source_files(
    root: FormalSourceRoot,
    location: Path,
    *,
    max_file_bytes: int,
    max_files: int,
):
    """Yield source files for a configured prover family while pruning builds."""

    n_files = 0
    suffixes = _formal_source_suffixes(root)
    for dirpath, dirnames, filenames in os.walk(location):
        dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in SKIPPED_PATH_PARTS)
        for filename in sorted(filenames):
            if not filename.endswith(suffixes):
                continue
            path = Path(dirpath) / filename
            if _skip_path(path, base=location) or not _file_size_ok(path, max_file_bytes):
                continue
            yield path
            n_files += 1
            if n_files >= max_files:
                return


def _formal_source_suffixes(root: FormalSourceRoot) -> tuple[str, ...]:
    key = _source_type_key(root.source_type)
    return FORMAL_SOURCE_SUFFIXES_BY_TYPE.get(
        key,
        (".lean", ".v", ".thy", ".agda"),
    )


def _formal_source_language(root: FormalSourceRoot, path: Path) -> str:
    key = _source_type_key(root.source_type)
    if key.startswith(("rocq", "coq")) or path.suffix == ".v":
        return "rocq"
    if key.startswith("isabelle") or path.suffix == ".thy":
        return "isabelle"
    if key.startswith("agda") or path.suffix == ".agda":
        return "agda"
    return "lean"


def _source_type_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


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
        "namespace": hit.declaration.namespace,
        "signature": hit.declaration.signature,
        "reference": hit.declaration.reference,
        "reference_aliases": hit.declaration.reference_aliases,
        "module_summary": hit.declaration.module_summary,
        "declaration_doc": hit.declaration.declaration_doc,
        "section_summary": hit.declaration.section_summary,
        "module_group": hit.declaration.module_group,
        "module_group_summary": hit.declaration.module_group_summary,
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
