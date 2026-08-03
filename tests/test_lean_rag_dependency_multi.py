from __future__ import annotations

import sqlite3
from pathlib import Path

from ai_statistician import formal_source_index
from ai_statistician import lean_rag_dependency
from ai_statistician.formal_source_hybrid import (
    FormalSourceDependencyHybridRetriever,
)
from ai_statistician.formal_source_prompt_context import (
    _formal_source_dependency_context,
)
from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
)
from ai_statistician.formal_source_topology import (
    fallback_formal_source_topology,
)
from ai_statistician.lean_rag_dependency import (
    LEAN_RAG_CROSS_SOURCE_EVIDENCE_STATUS,
    LEAN_RAG_CROSS_SOURCE_REFERENCE_POLICY,
    LeanRagDependencyMultiRetriever,
    LeanRagDependencyRetriever,
)


def _write_dependency_db(path: Path, *, corpus: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE declarations (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              short_name TEXT NOT NULL,
              kind TEXT NOT NULL,
              module TEXT NOT NULL,
              path TEXT NOT NULL,
              line_start INTEGER NOT NULL,
              line_end INTEGER NOT NULL,
              namespace TEXT NOT NULL,
              attributes TEXT NOT NULL,
              signature TEXT NOT NULL,
              proof TEXT NOT NULL,
              has_proof INTEGER NOT NULL,
              has_sorry INTEGER NOT NULL,
              text_hash TEXT NOT NULL
            );
            CREATE TABLE declaration_edges (
              id INTEGER PRIMARY KEY,
              src_decl_id INTEGER NOT NULL,
              dst_decl_id INTEGER NOT NULL,
              edge_type TEXT NOT NULL,
              match_kind TEXT NOT NULL,
              scope TEXT NOT NULL,
              weight INTEGER NOT NULL
            );
            CREATE VIRTUAL TABLE decl_fts USING fts5(
              name, short_name, kind, module, namespace, signature, proof
            );
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """
        )
        conn.executemany(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            [
                ("schema_version", "4"),
                (
                    "declaration_identity_policy",
                    "unicode_lean_identifier_v1",
                ),
                (
                    "declaration_reference_policy",
                    "comment_string_free_explicit_names_v1",
                ),
            ],
        )
        rows = [
            (
                1,
                "Theory.master_error_bound",
                "master_error_bound",
                "theorem",
                f"{corpus}.Main",
                f"{corpus}/Main.lean",
                30,
                40,
                "Theory",
                "[]",
                "theorem master_error_bound : True",
                "by exact proof_dependency",
                1,
                0,
                f"{corpus}-target",
            ),
            (
                2,
                f"Theory.{corpus}_statement_dependency",
                f"{corpus}_statement_dependency",
                "def",
                f"{corpus}.Defs",
                f"{corpus}/Defs.lean",
                5,
                8,
                "Theory",
                "[]",
                f"def {corpus}_statement_dependency : Prop",
                ":= True",
                1,
                0,
                f"{corpus}-statement",
            ),
            (
                3,
                f"Theory.{corpus}_proof_dependency",
                f"{corpus}_proof_dependency",
                "lemma",
                f"{corpus}.Helpers",
                f"{corpus}/Helpers.lean",
                10,
                12,
                "Theory",
                "[]",
                f"lemma {corpus}_proof_dependency : True",
                "by trivial",
                1,
                0,
                f"{corpus}-proof",
            ),
            (
                4,
                f"Theory.{corpus}_consumer",
                f"{corpus}_consumer",
                "theorem",
                f"{corpus}.Consumer",
                f"{corpus}/Consumer.lean",
                50,
                55,
                "Theory",
                "[]",
                f"theorem {corpus}_consumer : True",
                "by exact master_error_bound",
                1,
                0,
                f"{corpus}-consumer",
            ),
        ]
        conn.executemany(
            "INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.executemany(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[8],
                    row[10],
                    row[11],
                )
                for row in rows
            ],
        )
        conn.executemany(
            """
            INSERT INTO declaration_edges(
              src_decl_id, dst_decl_id, edge_type, match_kind, scope, weight
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (1, 2, "explicit_source", "unique_basename", "statement", 1),
                (1, 3, "explicit_source", "unique_basename", "proof", 1),
                (4, 1, "explicit_source", "unique_basename", "proof", 1),
            ],
        )
    return path


def test_fts_query_preserves_semantic_order_and_drops_formula_noise() -> None:
    query = (
        "Show e_n is a martingale under H0 using E L_i p_i n. "
        "Apply optional stopping and Markov inequality."
    )

    fts_query = lean_rag_dependency._fts_query(query)

    assert '"optional"*' in fts_query
    assert '"stopping"*' in fts_query
    assert '"markov"*' in fts_query
    assert '"e"*' not in fts_query
    assert '"show"*' not in fts_query
    assert '"apply"*' not in fts_query
    assert fts_query.index('"martingale"*') < fts_query.index('"optional"*')
    assert lean_rag_dependency._fts_query("X") == '"x"*'


def _insert_dependency_declaration(
    db_path: Path,
    *,
    row_id: int,
    name: str,
    kind: str = "def",
    signature: str = "",
    proof: str = ":= True",
) -> None:
    short_name = name.rsplit(".", 1)[-1]
    namespace = name.rsplit(".", 1)[0] if "." in name else ""
    row = (
        row_id,
        name,
        short_name,
        kind,
        f"Fixture.{namespace or 'Root'}",
        f"Fixture/{namespace.replace('.', '/') or 'Root'}.lean",
        row_id * 10,
        row_id * 10 + 2,
        namespace,
        "[]",
        signature or f"{kind} {short_name} : Prop",
        proof,
        1,
        0,
        f"fixture-{row_id}-{short_name}",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
        conn.execute(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[8],
                row[10],
                row[11],
            ),
        )


def _topology_bound_retriever(
    db_path: Path,
    *,
    source_id: str,
) -> LeanRagDependencyRetriever:
    topology = fallback_formal_source_topology(source_id)
    assert topology is not None
    return LeanRagDependencyRetriever(
        db_path,
        source_id=source_id,
        source_topology=topology,
    )


def test_cross_source_context_binds_only_declared_direct_dependency(
    tmp_path: Path,
) -> None:
    active_path = _write_dependency_db(tmp_path / "active.sqlite", corpus="Active")
    statlib_path = _write_dependency_db(tmp_path / "statlib.sqlite", corpus="Statlib")
    companion_path = _write_dependency_db(
        tmp_path / "companion.sqlite",
        corpus="Companion",
    )
    with sqlite3.connect(active_path) as conn:
        conn.execute(
            "UPDATE declarations SET signature = ?, proof = ? WHERE id = 1",
            (
                """theorem master_error_bound
                  (h : Canonical.FoundationAssumption) :
                  Canonical.FoundationConclusion""",
                """by
                  have _ := Companion.external_proof
                  have _ := "Canonical.string_only"
                  -- Canonical.comment_only
                  exact h.foundation_proof""",
            ),
        )
    _insert_dependency_declaration(
        statlib_path,
        row_id=5,
        name="Canonical.FoundationAssumption",
    )
    _insert_dependency_declaration(
        statlib_path,
        row_id=6,
        name="Canonical.FoundationConclusion",
    )
    _insert_dependency_declaration(
        statlib_path,
        row_id=7,
        name="Canonical.foundation_proof",
        kind="theorem",
        signature=(
            "theorem foundation_proof : "
            "FoundationAssumption -> FoundationConclusion"
        ),
        proof="by trivial",
    )
    _insert_dependency_declaration(
        statlib_path,
        row_id=8,
        name="Canonical.string_only",
    )
    _insert_dependency_declaration(
        statlib_path,
        row_id=9,
        name="Canonical.comment_only",
    )
    _insert_dependency_declaration(
        companion_path,
        row_id=5,
        name="Companion.external_proof",
        kind="theorem",
        proof="by trivial",
    )
    retriever = LeanRagDependencyMultiRetriever(
        (
            _topology_bound_retriever(
                active_path,
                source_id="empirical_process_lean",
            ),
            _topology_bound_retriever(statlib_path, source_id="statlib"),
            _topology_bound_retriever(
                companion_path,
                source_id="lean_stat_learning_theory",
            ),
        )
    )

    context = retriever.dependency_context(
        "Theory.master_error_bound",
        source_id="empirical_process_lean",
        path="Active/Main.lean",
    )

    assert context is not None
    assert [
        (row.source_id, row.declaration_name, row.match_kind)
        for row in context.cross_source_statement_uses
    ] == [
        ("statlib", "Canonical.FoundationAssumption", "exact_name"),
        ("statlib", "Canonical.FoundationConclusion", "exact_name"),
    ]
    assert [
        (row.source_id, row.declaration_name, row.match_kind)
        for row in context.cross_source_proof_uses
    ] == [
        (
            "statlib",
            "Canonical.foundation_proof",
            "globally_unique_short_name",
        )
    ]
    assert context.cross_source_dependency_policy == (
        LEAN_RAG_CROSS_SOURCE_REFERENCE_POLICY
    )
    assert context.cross_source_evidence_status == (
        LEAN_RAG_CROSS_SOURCE_EVIDENCE_STATUS
    )
    assert "Companion.external_proof" not in {
        row.declaration_name for row in context.cross_source_proof_uses
    }

    payload = _formal_source_dependency_context(
        retriever,
        "Theory.master_error_bound",
        source_id="empirical_process_lean",
        path="Active/Main.lean",
        limit=8,
    )
    assert payload["cross_source_statement_uses"] == [
        {
            "source_id": "statlib",
            "name": "Canonical.FoundationAssumption",
            "match_kind": "exact_name",
        },
        {
            "source_id": "statlib",
            "name": "Canonical.FoundationConclusion",
            "match_kind": "exact_name",
        },
    ]
    assert payload["cross_source_proof_uses"] == [
        {
            "source_id": "statlib",
            "name": "Canonical.foundation_proof",
            "match_kind": "globally_unique_short_name",
        }
    ]
    assert payload["cross_source_evidence_status"] == (
        LEAN_RAG_CROSS_SOURCE_EVIDENCE_STATUS
    )
    assert "by trivial" not in str(payload)
    assert "candidate_proof_body" not in str(payload)


def test_cross_source_short_name_resolution_fails_closed_on_ambiguity(
    tmp_path: Path,
) -> None:
    active_path = _write_dependency_db(tmp_path / "active.sqlite", corpus="Active")
    statlib_path = _write_dependency_db(tmp_path / "statlib.sqlite", corpus="Statlib")
    _insert_dependency_declaration(
        statlib_path,
        row_id=5,
        name="First.shared_bridge",
        kind="theorem",
        proof="by trivial",
    )
    _insert_dependency_declaration(
        statlib_path,
        row_id=6,
        name="Second.shared_bridge",
        kind="theorem",
        proof="by trivial",
    )
    with sqlite3.connect(active_path) as conn:
        conn.execute(
            "UPDATE declarations SET proof = ? WHERE id = 1",
            ("by exact shared_bridge",),
        )
    retriever = LeanRagDependencyMultiRetriever(
        (
            _topology_bound_retriever(
                active_path,
                source_id="empirical_process_lean",
            ),
            _topology_bound_retriever(statlib_path, source_id="statlib"),
        )
    )

    ambiguous = retriever.dependency_context(
        "Theory.master_error_bound",
        source_id="empirical_process_lean",
        path="Active/Main.lean",
    )
    assert ambiguous is not None
    assert ambiguous.cross_source_proof_uses == ()

    with sqlite3.connect(active_path) as conn:
        conn.execute(
            "UPDATE declarations SET proof = ? WHERE id = 1",
            ("by exact First.shared_bridge",),
        )
    qualified = retriever.dependency_context(
        "Theory.master_error_bound",
        source_id="empirical_process_lean",
        path="Active/Main.lean",
    )
    assert qualified is not None
    assert [
        (row.declaration_name, row.match_kind)
        for row in qualified.cross_source_proof_uses
    ] == [("First.shared_bridge", "exact_name")]


def test_cross_source_dependency_lookup_is_not_reversed(
    tmp_path: Path,
) -> None:
    active_path = _write_dependency_db(tmp_path / "active.sqlite", corpus="Active")
    statlib_path = _write_dependency_db(tmp_path / "statlib.sqlite", corpus="Statlib")
    with sqlite3.connect(statlib_path) as conn:
        conn.execute(
            "UPDATE declarations SET proof = ? WHERE id = 1",
            ("by exact Theory.Active_proof_dependency",),
        )
    retriever = LeanRagDependencyMultiRetriever(
        (
            _topology_bound_retriever(
                active_path,
                source_id="empirical_process_lean",
            ),
            _topology_bound_retriever(statlib_path, source_id="statlib"),
        )
    )

    context = retriever.dependency_context(
        "Theory.master_error_bound",
        source_id="statlib",
        path="Statlib/Main.lean",
    )

    assert context is not None
    assert context.cross_source_statement_uses == ()
    assert context.cross_source_proof_uses == ()
    assert context.cross_source_dependency_policy == ""


def test_cross_source_lookup_batches_long_declarations_without_truncation(
    tmp_path: Path,
) -> None:
    active_path = _write_dependency_db(tmp_path / "active.sqlite", corpus="Active")
    statlib_path = _write_dependency_db(tmp_path / "statlib.sqlite", corpus="Statlib")
    fillers = "\n".join(
        f"have filler_{index} := local_{index}"
        for index in range(220)
    )
    with sqlite3.connect(active_path) as conn:
        conn.execute(
            "UPDATE declarations SET proof = ? WHERE id = 1",
            (f"by\n{fillers}\nexact Canonical.late_dependency",),
        )
    _insert_dependency_declaration(
        statlib_path,
        row_id=5,
        name="Canonical.late_dependency",
        kind="theorem",
        proof="by trivial",
    )
    retriever = LeanRagDependencyMultiRetriever(
        (
            _topology_bound_retriever(
                active_path,
                source_id="empirical_process_lean",
            ),
            _topology_bound_retriever(statlib_path, source_id="statlib"),
        )
    )

    context = retriever.dependency_context(
        "Theory.master_error_bound",
        source_id="empirical_process_lean",
        path="Active/Main.lean",
    )

    assert context is not None
    assert [
        row.declaration_name for row in context.cross_source_proof_uses
    ] == ["Canonical.late_dependency"]


def test_multi_retriever_routes_dependency_context_to_requested_corpus(
    tmp_path: Path,
) -> None:
    first = LeanRagDependencyRetriever(
        _write_dependency_db(tmp_path / "first.sqlite", corpus="First"),
        source_id="first_corpus",
    )
    second = LeanRagDependencyRetriever(
        _write_dependency_db(tmp_path / "second.sqlite", corpus="Second"),
        source_id="second_corpus",
    )
    retriever = LeanRagDependencyMultiRetriever((first, second))

    context = retriever.dependency_context(
        "AlternativeNamespace.master_error_bound",
        source_id="second_corpus",
        path="Second/Main.lean",
    )

    assert context is not None
    assert context.source_id == "second_corpus"
    assert context.statement_uses == (
        "Theory.Second_statement_dependency",
    )
    assert context.proof_uses == ("Theory.Second_proof_dependency",)
    assert context.used_by == ("Theory.Second_consumer",)
    assert not context.module_import_visibility_enforced
    assert "without import-visibility filtering" in (
        context.dependency_resolution_policy
    )


def test_dependency_graph_does_not_expose_private_declarations(
    tmp_path: Path,
) -> None:
    db_path = _write_dependency_db(
        tmp_path / "private-declaration.sqlite",
        corpus="Visible",
    )
    private_row = (
        5,
        "Theory.hidden_transport",
        "hidden_transport",
        "lemma",
        "Visible.Helpers",
        "Visible/Helpers.lean",
        14,
        16,
        "Theory",
        "[]",
        "private lemma hidden_transport : True",
        "by trivial",
        1,
        0,
        "private-helper",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            private_row,
        )
        conn.execute(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                private_row[0],
                private_row[1],
                private_row[2],
                private_row[3],
                private_row[4],
                private_row[8],
                private_row[10],
                private_row[11],
            ),
        )
        conn.execute(
            """
            INSERT INTO declaration_edges(
              src_decl_id, dst_decl_id, edge_type, match_kind, scope, weight
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (1, 5, "explicit_source", "unique_basename", "proof", 2),
        )

    retriever = LeanRagDependencyRetriever(db_path)

    assert retriever.search("hidden transport", k=3) == []
    assert retriever.dependency_context("Theory.hidden_transport") is None
    context = retriever.dependency_context("Theory.master_error_bound")
    assert context is not None
    assert "Theory.hidden_transport" not in context.proof_uses
    assert context.proof_uses == ("Theory.Visible_proof_dependency",)


def test_dependency_graph_preserves_unicode_declaration_identity(
    tmp_path: Path,
) -> None:
    db_path = _write_dependency_db(
        tmp_path / "unicode-identity.sqlite",
        corpus="Unicode",
    )
    with sqlite3.connect(db_path) as conn:
        row = (
            5,
            "Theory.linear_δ_star",
            "linear_δ_star",
            "def",
            "Unicode.CriticalRadius",
            "Unicode/CriticalRadius.lean",
            60,
            62,
            "Theory",
            "[]",
            "noncomputable def linear_δ_star (σ : ℝ) : ℝ",
            ":= σ",
            1,
            0,
            "unicode-critical-radius",
        )
        conn.execute(
            "INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
        conn.execute(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (row[0], row[1], row[2], row[3], row[4], row[8], row[10], row[11]),
        )

    retriever = LeanRagDependencyRetriever(db_path)
    hits = retriever.search("Theory.linear_δ_star critical radius", k=3)
    context = retriever.dependency_context(
        "Theory.linear_δ_star",
        path="Unicode/CriticalRadius.lean",
    )

    assert hits
    assert hits[0].declaration.name == "Theory.linear_δ_star"
    assert "δ" in hits[0].declaration.name
    assert context is not None
    assert context.module == "Unicode.CriticalRadius"


def test_dependency_context_rejects_unimported_unique_basename_edges(
    tmp_path: Path,
) -> None:
    db_path = _write_dependency_db(
        tmp_path / "import-aware.sqlite",
        corpus="Scoped",
    )
    false_rows = [
        (
            5,
            "Noise.bounded",
            "bounded",
            "lemma",
            "Noise.Unimported",
            "Noise/Unimported.lean",
            8,
            9,
            "Noise",
            "[]",
            "lemma bounded : True",
            "by trivial",
            1,
            0,
            "noise-dependency",
        ),
        (
            6,
            "Noise.unrelated_consumer",
            "unrelated_consumer",
            "theorem",
            "Noise.Consumer",
            "Noise/Consumer.lean",
            60,
            65,
            "Noise",
            "[]",
            "theorem unrelated_consumer : True",
            "by exact master_error_bound",
            1,
            0,
            "noise-consumer",
        ),
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE module_imports (
              id INTEGER PRIMARY KEY,
              src_module TEXT NOT NULL,
              dst_module TEXT NOT NULL,
              visibility TEXT NOT NULL,
              src_path TEXT NOT NULL,
              line INTEGER NOT NULL,
              is_local_dst INTEGER NOT NULL
            );
            """
        )
        conn.executemany(
            "INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            false_rows,
        )
        conn.executemany(
            """
            INSERT INTO module_imports(
              src_module, dst_module, visibility, src_path, line, is_local_dst
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "Scoped.Main",
                    "Scoped.Defs",
                    "import",
                    "Scoped/Main.lean",
                    1,
                    1,
                ),
                (
                    "Scoped.Main",
                    "Scoped.Helpers",
                    "import",
                    "Scoped/Main.lean",
                    2,
                    1,
                ),
                (
                    "Scoped.Consumer",
                    "Scoped.Main",
                    "import",
                    "Scoped/Consumer.lean",
                    1,
                    1,
                ),
                (
                    "Scoped.Defs",
                    "Scoped.Foundation",
                    "import",
                    "Scoped/Defs.lean",
                    1,
                    1,
                ),
                (
                    "Scoped.Helpers",
                    "Scoped.Foundation",
                    "import",
                    "Scoped/Helpers.lean",
                    1,
                    1,
                ),
                (
                    "Scoped.Foundation",
                    "Scoped.Main",
                    "import",
                    "Scoped/Foundation.lean",
                    1,
                    1,
                ),
                (
                    "Scoped.Main",
                    "External.Library",
                    "import",
                    "Scoped/Main.lean",
                    3,
                    0,
                ),
            ],
        )
        conn.executemany(
            """
            INSERT INTO declaration_edges(
              src_decl_id, dst_decl_id, edge_type, match_kind, scope, weight
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (1, 5, "explicit_source", "unique_basename", "proof", 1),
                (6, 1, "explicit_source", "unique_basename", "proof", 1),
            ],
        )

    context = LeanRagDependencyRetriever(
        db_path,
        source_id="scoped_corpus",
    ).dependency_context(
        "Theory.master_error_bound",
        source_id="scoped_corpus",
        path="Scoped/Main.lean",
    )

    assert context is not None
    assert context.direct_module_imports == (
        "Scoped.Defs",
        "Scoped.Helpers",
    )
    assert context.module_dependency_route == (
        (1, "Scoped.Defs"),
        (1, "Scoped.Helpers"),
        (2, "Scoped.Foundation"),
    )
    assert context.module_import_visibility_enforced
    assert context.statement_uses == (
        "Theory.Scoped_statement_dependency",
    )
    assert context.proof_uses == ("Theory.Scoped_proof_dependency",)
    assert "Noise.bounded" not in context.uses
    assert context.used_by == ("Theory.Scoped_consumer",)
    assert "Noise.unrelated_consumer" not in context.used_by
    assert "transitive local import closure" in (
        context.dependency_resolution_policy
    )


def test_multi_retriever_search_preserves_corpus_provenance(
    tmp_path: Path,
) -> None:
    retriever = LeanRagDependencyMultiRetriever(
        (
            LeanRagDependencyRetriever(
                _write_dependency_db(tmp_path / "first.sqlite", corpus="First"),
                source_id="first_corpus",
            ),
            LeanRagDependencyRetriever(
                _write_dependency_db(tmp_path / "second.sqlite", corpus="Second"),
                source_id="second_corpus",
            ),
        )
    )

    hits = retriever.search("Theorem 13.5 master error bound", k=4)

    assert {
        hit.declaration.source_id for hit in hits
    } == {"first_corpus", "second_corpus"}
    assert all(
        any(
            term == f"dependency_corpus={hit.declaration.source_id}"
            for term in hit.matched_terms
        )
        for hit in hits
    )
    assert all("13" not in hit.matched_terms for hit in hits)


def test_dependency_search_prefers_name_and_signature_over_proof_chatter(
    tmp_path: Path,
) -> None:
    db_path = _write_dependency_db(
        tmp_path / "field-weighted.sqlite",
        corpus="AI4SLT",
    )
    rows = [
        (
            5,
            "GaussianLipConcen.gaussian_lipschitz_concentration",
            "gaussian_lipschitz_concentration",
            "theorem",
            "SLT.GaussianLipConcen",
            "SLT/GaussianLipConcen.lean",
            100,
            110,
            "GaussianLipConcen",
            "[]",
            (
                "theorem gaussian_lipschitz_concentration "
                "(hf : LipschitzWith L f) : tailProbability f ≤ bound"
            ),
            "by exact concentration_helper",
            1,
            0,
            "semantic-result",
        ),
        (
            6,
            "Internal.unrelated_helper",
            "unrelated_helper",
            "lemma",
            "SLT.Internal",
            "SLT/Internal.lean",
            20,
            30,
            "Internal",
            "[]",
            "lemma unrelated_helper : True",
            (
                "by -- gaussian lipschitz concentration "
                "gaussian lipschitz concentration "
                "gaussian lipschitz concentration "
                "gaussian lipschitz concentration "
                "gaussian lipschitz concentration "
                "gaussian lipschitz concentration\ntrivial"
            ),
            1,
            0,
            "proof-chatter",
        ),
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.executemany(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[8],
                    row[10],
                    row[11],
                )
                for row in rows
            ],
        )

    hits = LeanRagDependencyRetriever(db_path).search(
        "gaussian lipschitz concentration",
        k=2,
    )

    assert hits[0].declaration.name == (
        "GaussianLipConcen.gaussian_lipschitz_concentration"
    )
    noisy = next(
        hit
        for hit in hits
        if hit.declaration.name == "Internal.unrelated_helper"
    )
    assert "proof_body_only_match" in noisy.matched_terms


def test_dependency_search_uses_corpus_quality_as_soft_ranking_signal(
    tmp_path: Path,
) -> None:
    db_path = _write_dependency_db(
        tmp_path / "quality-ranked.sqlite",
        corpus="StatInference",
    )
    rows = [
        (
            5,
            "Theory.variance_concentration",
            "variance_concentration",
            "theorem",
            "Theory.Legacy",
            "Theory/Legacy.lean",
            10,
            12,
            "Theory",
            "[]",
            "theorem variance_concentration : True",
            "by trivial",
            1,
            0,
            "legacy",
            0,
            '["generated_surface_name"]',
        ),
        (
            6,
            "Theory.gaussian_variance_concentration_bound",
            "gaussian_variance_concentration_bound",
            "theorem",
            "Theory.Concentration",
            "Theory/Concentration.lean",
            20,
            24,
            "Theory",
            "[]",
            "theorem gaussian_variance_concentration_bound : True",
            "by trivial",
            1,
            0,
            "canonical",
            100,
            "[]",
        ),
    ]
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "ALTER TABLE declarations ADD COLUMN quality_score INTEGER NOT NULL DEFAULT 100"
        )
        conn.execute(
            "ALTER TABLE declarations ADD COLUMN quality_flags TEXT NOT NULL DEFAULT '[]'"
        )
        conn.executemany(
            "INSERT INTO declarations VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.executemany(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[8],
                    row[10],
                    row[11],
                )
                for row in rows
            ],
        )

    hits = LeanRagDependencyRetriever(db_path).search(
        "variance concentration",
        k=2,
    )

    assert hits[0].declaration.name == (
        "Theory.gaussian_variance_concentration_bound"
    )
    assert "declaration_quality=100" in hits[0].matched_terms
    legacy = next(
        hit
        for hit in hits
        if hit.declaration.name == "Theory.variance_concentration"
    )
    assert legacy.score < hits[0].score
    assert (
        "declaration_quality_flags=generated_surface_name"
        in legacy.matched_terms
    )


def test_dependency_search_hides_oversized_names_except_exact_lookup(
    tmp_path: Path,
) -> None:
    db_path = _write_dependency_db(
        tmp_path / "oversized-name-policy.sqlite",
        corpus="StatInference",
    )
    oversized_name = (
        "Theory.variance_concentration_generated_with_every_assumption_"
        "encoded_into_the_public_declaration_identifier"
    )
    rows = [
        (
            5,
            oversized_name,
            oversized_name.rsplit(".", 1)[-1],
            "theorem",
            "Theory.Generated",
            "Theory/Generated.lean",
            10,
            12,
            "Theory",
            "[]",
            "theorem generated_variance_concentration : True",
            "by trivial",
            1,
            0,
            "oversized",
            35,
            '["oversized_name"]',
        ),
        (
            6,
            "Theory.variance_concentration",
            "variance_concentration",
            "theorem",
            "Theory.Concentration",
            "Theory/Concentration.lean",
            20,
            24,
            "Theory",
            "[]",
            "theorem variance_concentration : True",
            "by trivial",
            1,
            0,
            "canonical",
            100,
            "[]",
        ),
    ]
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "ALTER TABLE declarations ADD COLUMN quality_score INTEGER NOT NULL DEFAULT 100"
        )
        conn.execute(
            "ALTER TABLE declarations ADD COLUMN quality_flags TEXT NOT NULL DEFAULT '[]'"
        )
        conn.executemany(
            "INSERT INTO declarations VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.executemany(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[8],
                    row[10],
                    row[11],
                )
                for row in rows
            ],
        )

    retriever = LeanRagDependencyRetriever(db_path)

    semantic_hits = retriever.search("variance concentration", k=10)
    exact_hits = retriever.search(oversized_name, k=10)

    assert oversized_name not in {
        hit.declaration.name for hit in semantic_hits
    }
    exact = next(
        hit for hit in exact_hits if hit.declaration.name == oversized_name
    )
    assert "oversized_name_exact_lookup" in exact.matched_terms


def test_dependency_health_rejects_mismatch_and_exposes_matching_snapshot_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_root = tmp_path / "source"
    (source_root / "SLT").mkdir(parents=True)
    (source_root / "lean-toolchain").write_text(
        "leanprover/lean4:v4.32.0\n",
        encoding="utf-8",
    )
    (source_root / "lake-manifest.json").write_text(
        '{"packages": [{"name": "mathlib", "rev": "' + "c" * 40 + '"}]}',
        encoding="utf-8",
    )
    db_path = _write_dependency_db(
        tmp_path / "snapshot-bound.sqlite",
        corpus="AI4SLT",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM meta")
        conn.executemany(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            [
                ("schema_version", "4"),
                (
                    "declaration_identity_policy",
                    "unicode_lean_identifier_v1",
                ),
                (
                    "declaration_reference_policy",
                    "comment_string_free_explicit_names_v1",
                ),
                ("entry_module", "SLT"),
                ("corpus_scope_policy", "recursive_import_closure_v1"),
                ("project_root", str(source_root)),
                ("source_root", str(source_root / "SLT")),
                ("source_git_commit", "a" * 40),
                ("source_git_tree", "b" * 40),
                ("source_git_dirty", "false"),
                ("lean_toolchain", "leanprover/lean4:v4.32.0"),
                ("mathlib_revision", "c" * 40),
            ],
        )
    monkeypatch.setattr(
        lean_rag_dependency,
        "_command_output",
        lambda args, **_kwargs: (
            str(source_root)
            if "--show-toplevel" in args
            else "e" * 40
            if "rev-parse" in args
            else ""
        ),
    )

    retriever = LeanRagDependencyRetriever(db_path)
    health = retriever.health_report()

    assert health["source_snapshot_bound"] is True
    assert health["source_snapshot_match"] is False
    assert health["source_snapshot_status"] == "BOUND_MISMATCH"
    assert health["entry_module"] == "SLT"
    assert health["corpus_scope_policy"] == "recursive_import_closure_v1"
    assert health["canonical_import_closure"] is True
    assert health["all_ok"] is False
    assert retriever.search("master error bound", k=1) == []

    monkeypatch.setattr(
        lean_rag_dependency,
        "_command_output",
        lambda args, **_kwargs: (
            str(source_root)
            if "--show-toplevel" in args
            else "b" * 40
            if "rev-parse" in args
            else ""
        ),
    )
    matching = LeanRagDependencyRetriever(db_path)
    context = matching.dependency_context(
        "Theory.master_error_bound",
        path="AI4SLT/Main.lean",
    )

    assert context is not None
    assert context.module_ancestry == ("AI4SLT", "AI4SLT.Main")
    assert context.source_snapshot_status == "BOUND_MATCH"
    assert context.source_snapshot_bound is True
    assert context.source_snapshot_match is True
    snapshot = dict(context.source_snapshot_metadata)
    assert snapshot["source_git_commit"] == "a" * 40
    assert snapshot["source_git_tree"] == "b" * 40
    assert snapshot["lean_toolchain"] == "leanprover/lean4:v4.32.0"
    assert snapshot["mathlib_revision"] == "c" * 40
    assert snapshot["entry_module"] == "SLT"
    assert snapshot["corpus_scope_policy"] == "recursive_import_closure_v1"
    assert snapshot["declaration_reference_policy"] == (
        "comment_string_free_explicit_names_v1"
    )
    assert "project_root" not in snapshot
    assert "source_root" not in snapshot


def test_bound_legacy_graph_schema_fails_closed(tmp_path: Path) -> None:
    db_path = _write_dependency_db(
        tmp_path / "legacy-identity.sqlite",
        corpus="Legacy",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM meta")
        conn.executemany(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            [
                ("schema_version", "2"),
                ("source_git_commit", "a" * 40),
                ("source_git_tree", "b" * 40),
            ],
        )

    retriever = LeanRagDependencyRetriever(db_path)
    health = retriever.health_report()

    assert health["graph_schema_version"] == "2"
    assert health["graph_schema_supported"] is False
    assert health["declaration_identity_policy_supported"] is False
    assert health["declaration_reference_policy_supported"] is False
    assert health["all_ok"] is False
    assert retriever.search("master error bound", k=1) == []


def test_graph_without_clean_reference_policy_fails_closed(tmp_path: Path) -> None:
    db_path = _write_dependency_db(
        tmp_path / "legacy-reference-policy.sqlite",
        corpus="LegacyReference",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "DELETE FROM meta WHERE key = 'declaration_reference_policy'"
        )

    retriever = LeanRagDependencyRetriever(db_path)
    health = retriever.health_report()

    assert health["graph_schema_supported"] is True
    assert health["declaration_identity_policy_supported"] is True
    assert health["declaration_reference_policy_supported"] is False
    assert health["all_ok"] is False
    assert retriever.search("master error bound", k=1) == []


def test_unversioned_graph_fails_closed(tmp_path: Path) -> None:
    db_path = _write_dependency_db(
        tmp_path / "unversioned.sqlite",
        corpus="Unversioned",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE meta")

    health = LeanRagDependencyRetriever(db_path).health_report()

    assert health["graph_schema_version"] == ""
    assert health["graph_schema_supported"] is False
    assert health["declaration_identity_policy_supported"] is False
    assert health["declaration_reference_policy_supported"] is False
    assert health["all_ok"] is False


def test_auto_discovery_activates_multiple_healthy_corpus_graphs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ai4slt = _write_dependency_db(
        tmp_path
        / "current_status_ai4slt_lean_rag_dependency_graph"
        / "stat_learning.sqlite",
        corpus="AI4SLT",
    )
    stat_inference = _write_dependency_db(
        tmp_path
        / "current_status_lean_rag_dependency_graph"
        / "stat_inference.sqlite",
        corpus="StatInference",
    )
    statlib = _write_dependency_db(
        tmp_path
        / "current_status_statlib_lean_rag_dependency_graph"
        / "statlib.sqlite",
        corpus="Statlib",
    )
    monkeypatch.setattr(
        formal_source_index,
        "_auto_lean_rag_db_candidates",
        lambda: (ai4slt, stat_inference, statlib),
    )

    retriever = formal_source_index._optional_lean_rag_dependency_retriever(
        None
    )

    assert isinstance(retriever, LeanRagDependencyMultiRetriever)
    assert retriever.db_paths == (ai4slt, stat_inference, statlib)
    assert "lean_stat_learning_theory" in retriever.source_ids
    assert "empirical_process_lean" in retriever.source_ids
    assert "legacy_ai_statistician_statinference" not in retriever.source_ids
    assert "statlib" in retriever.source_ids
    assert "statistical_foundation" in retriever.source_ids


def test_auto_discovery_includes_canonical_active_project_graph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    external_root = tmp_path / "EmpericalProcessLEAN-main"
    canonical_graph = (
        external_root / "build" / "lean_graph" / "stat_inference.sqlite"
    )
    canonical_graph.parent.mkdir(parents=True)
    canonical_graph.touch()
    missing_relative_path = Path("missing") / "graph.sqlite"
    monkeypatch.setattr(
        formal_source_index,
        "EXTERNAL_EMPIRICAL_PROCESS_LEAN_ROOT",
        external_root,
    )
    monkeypatch.setattr(
        formal_source_index,
        "DEFAULT_LEAN_RAG_DB_CANDIDATES",
        (),
    )
    for name in (
        "DEFAULT_LEAN_RAG_DB_RELATIVE_PATH",
        "DEFAULT_AI4SLT_LEAN_RAG_DB_RELATIVE_PATH",
        "DEFAULT_STATLIB_LEAN_RAG_DB_RELATIVE_PATH",
        "DEFAULT_EMPIRICAL_PROCESS_MAIN_LEAN_RAG_DB_RELATIVE_PATH",
    ):
        monkeypatch.setattr(
            formal_source_index,
            name,
            missing_relative_path,
        )

    candidates = formal_source_index._auto_lean_rag_db_candidates()

    assert candidates == (canonical_graph,)


def test_auto_discovery_uses_one_snapshot_per_canonical_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    current = _write_dependency_db(
        tmp_path / "current" / "stat_inference.sqlite",
        corpus="Current",
    )
    stale = _write_dependency_db(
        tmp_path / "stale" / "stat_inference.sqlite",
        corpus="Stale",
    )
    monkeypatch.setattr(
        formal_source_index,
        "_auto_lean_rag_db_candidates",
        lambda: (current, stale),
    )

    retriever = formal_source_index._optional_lean_rag_dependency_retriever(
        None
    )

    assert isinstance(retriever, LeanRagDependencyRetriever)
    assert retriever.db_path == current
    assert retriever.source_id == "empirical_process_lean"


def test_auto_discovery_skips_stale_active_graph_before_canonical_graph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    stale = _write_dependency_db(
        tmp_path / "stale" / "stat_inference.sqlite",
        corpus="Stale",
    )
    canonical = _write_dependency_db(
        tmp_path / "build" / "lean_graph" / "stat_inference.sqlite",
        corpus="Canonical",
    )
    with sqlite3.connect(stale) as conn:
        conn.execute(
            "UPDATE meta SET value = ? WHERE key = 'schema_version'",
            ("unsupported",),
        )
    monkeypatch.setattr(
        formal_source_index,
        "_auto_lean_rag_db_candidates",
        lambda: (stale, canonical),
    )

    retriever = formal_source_index._optional_lean_rag_dependency_retriever(
        None
    )

    assert isinstance(retriever, LeanRagDependencyRetriever)
    assert retriever.db_path == canonical
    assert retriever.source_id == "empirical_process_lean"


def test_explicit_renamed_graph_uses_snapshot_metadata_identity(
    tmp_path: Path,
) -> None:
    graph = _write_dependency_db(
        tmp_path / "renamed-without-corpus-hint.sqlite",
        corpus="StatlibMetadata",
    )
    with sqlite3.connect(graph) as conn:
        conn.executemany(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            [
                ("entry_module", "Statlib"),
                (
                    "source_git_remote",
                    "https://github.com/stat-lib/statlib.git",
                ),
                ("lean_toolchain", "leanprover/lean4:v4.30.0"),
                ("mathlib_revision", "a" * 40),
            ],
        )

    retriever = formal_source_index._optional_lean_rag_dependency_retriever(
        graph
    )

    assert isinstance(retriever, LeanRagDependencyRetriever)
    assert retriever.source_id == "statlib"
    assert retriever.source_topology is not None
    assert retriever.source_topology.identity_basis == (
        "source_git_remote",
        "entry_module",
    )
    assert retriever.health_payload["source_topology"]["role"] == (
        "canonical_statistics_foundation"
    )


def test_unrecognized_remote_cannot_claim_statlib_by_database_name(
    tmp_path: Path,
) -> None:
    graph = _write_dependency_db(
        tmp_path / "statlib.sqlite",
        corpus="UntrustedStatlibFork",
    )
    with sqlite3.connect(graph) as conn:
        conn.executemany(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            [
                ("entry_module", "Statlib"),
                (
                    "source_git_remote",
                    "https://github.com/example/statlib-fork.git",
                ),
            ],
        )

    retriever = formal_source_index._optional_lean_rag_dependency_retriever(
        graph
    )

    assert isinstance(retriever, LeanRagDependencyRetriever)
    assert retriever.source_id == "lean_rag_dependency_graph"
    assert retriever.source_topology is None


def test_source_scoped_dependency_search_queries_only_bound_corpus_graphs(
    tmp_path: Path,
) -> None:
    ai4slt_path = _write_dependency_db(
        tmp_path / "stat_learning.sqlite",
        corpus="AI4SLT",
    )
    stat_path = _write_dependency_db(
        tmp_path / "stat_inference.sqlite",
        corpus="StatInference",
    )
    ai4slt = LeanRagDependencyRetriever(
        ai4slt_path,
        source_id="lean_stat_learning_theory",
    )
    stat = LeanRagDependencyRetriever(
        stat_path,
        source_id="empirical_process_lean",
    )
    retriever = LeanRagDependencyMultiRetriever((ai4slt, stat))

    hits = retriever.search_with_source_scope(
        "master error bound",
        source_scope_ids=("lean_stat_learning_theory",),
        k=4,
    )

    assert hits
    assert {hit.declaration.source_id for hit in hits} == {
        "lean_stat_learning_theory"
    }
    generic = LeanRagDependencyRetriever(ai4slt_path)
    assert generic.search_with_source_scope(
        "master error bound",
        source_scope_ids=("lean_stat_learning_theory",),
        k=4,
    ) == []


def test_active_source_scope_queries_its_statlib_dependency_but_not_companion(
    tmp_path: Path,
) -> None:
    active = LeanRagDependencyRetriever(
        _write_dependency_db(tmp_path / "active.sqlite", corpus="Active"),
        source_id="empirical_process_lean",
    )
    statlib = LeanRagDependencyRetriever(
        _write_dependency_db(tmp_path / "statlib.sqlite", corpus="Statlib"),
        source_id="statlib",
    )
    companion = LeanRagDependencyRetriever(
        _write_dependency_db(tmp_path / "companion.sqlite", corpus="AI4SLT"),
        source_id="lean_stat_learning_theory",
    )
    retriever = LeanRagDependencyMultiRetriever(
        (active, statlib, companion)
    )

    hits = retriever.search_with_source_scope(
        "master error bound",
        source_scope_ids=("empirical_process_lean",),
        k=8,
    )

    assert {hit.declaration.source_id for hit in hits} == {
        "empirical_process_lean",
        "statlib",
    }


def test_short_name_fallback_refuses_ambiguous_declarations(
    tmp_path: Path,
) -> None:
    db_path = _write_dependency_db(
        tmp_path / "ambiguous.sqlite",
        corpus="First",
    )
    duplicate = (
        5,
        "Other.master_error_bound",
        "master_error_bound",
        "theorem",
        "Other.Main",
        "Other/Main.lean",
        20,
        25,
        "Other",
        "[]",
        "theorem master_error_bound : True",
        "by trivial",
        1,
        0,
        "other-target",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            duplicate,
        )
        conn.execute(
            """
            INSERT INTO decl_fts(
              rowid, name, short_name, kind, module, namespace, signature, proof
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                duplicate[0],
                duplicate[1],
                duplicate[2],
                duplicate[3],
                duplicate[4],
                duplicate[8],
                duplicate[10],
                duplicate[11],
            ),
        )
    retriever = LeanRagDependencyRetriever(db_path)

    assert retriever.dependency_context(
        "Unknown.master_error_bound"
    ) is None
    assert retriever.dependency_context(
        "Unknown.master_error_bound",
        path="First/Main.lean",
    ) is not None


def test_dependency_hit_maps_to_unique_local_qualified_declaration() -> None:
    local = FormalDeclaration(
        source_id="lean_stat_learning_theory",
        source_type="lean",
        path="SLT/LeastSquares/MasterErrorBound.lean",
        line=30,
        kind="theorem",
        name="LeastSquares.master_error_bound",
        namespace="LeastSquares",
        signature="theorem master_error_bound : True",
        binder_count=0,
        conclusion_head="True",
        major_symbols=(),
        imports=(),
    )
    graph_declaration = FormalDeclaration(
        source_id="lean_stat_learning_theory",
        source_type="lean_rag_dependency_graph",
        path="SLT/LeastSquares/MasterErrorBound.lean",
        line=30,
        kind="theorem",
        name="master_error_bound",
        namespace="LeastSquares",
        signature=local.signature,
        binder_count=0,
        conclusion_head="True",
        major_symbols=(),
        imports=(),
    )

    class EmptyBaseRetriever:
        def search(self, query: str, *, k: int):
            return []

    class ShortNameDependencyRetriever:
        db_path = Path("fixture.sqlite")
        auto_discovered = False

        def search(self, query: str, *, k: int):
            return [
                FormalSourceHit(
                    declaration=graph_declaration,
                    score=10.0,
                    matched_terms=("dependency_corpus=lean_stat_learning_theory",),
                )
            ]

    retriever = FormalSourceDependencyHybridRetriever(
        [local],
        EmptyBaseRetriever(),
        ShortNameDependencyRetriever(),
    )

    hits = retriever.search("master error bound", k=1)

    assert len(hits) == 1
    assert hits[0].declaration is local
    assert "lean_rag_dependency_graph" in hits[0].matched_terms
