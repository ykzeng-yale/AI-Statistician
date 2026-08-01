from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
    FormalSourceRetriever,
    FormalSourceRoot,
    FormalSourceSqliteIndex,
    _cache_covers_configured_roots,
    _search_tokens,
    build_formal_source_index,
    build_formal_source_search_backend,
    diversify_formal_source_hits,
    search_formal_sources,
)
from ai_statistician.formal_source_hybrid import (
    FormalSourceHybridRetriever,
    _FusionAccumulator,
)
from ai_statistician.formal_source_graph import FormalSourceGraphRetriever
from ai_statistician.formal_source_prompt_context import (
    FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS,
    compact_formal_source_grounding_hits_for_prompt,
    formalizer_feedback_with_task_bound_formal_source_queries,
    task_bound_formal_source_query_seeds,
    task_bound_formal_source_scope_ids,
)
from ai_statistician.formal_source_retrieval_benchmark import (
    FormalSourceRetrievalBenchmarkCase,
    audit_formal_source_reference_crosswalk,
    run_formal_source_retrieval_benchmark,
)
from ai_statistician.formalizer_llm import (
    build_formalizer_prompt,
    formalizer_proof_construction_strategy_contract,
)
from ai_statistician.research_agent_runtime import _formal_source_hit_to_json
from ai_statistician.research_lab import load_open_research_questions
from ai_statistician.research_schema import OpenResearchQuestion


def test_task_bound_formal_source_queries_keep_semantics_after_exact_name() -> None:
    queries = task_bound_formal_source_query_seeds(
        question=OpenResearchQuestion(
            id="generic_formal_source_query",
            title="Generic theorem",
            description="Find reusable formal support.",
        ),
        theory_packet={
            "theory_derivation_packet": {
                "formalization_handoff": {
                    "candidate_lean_targets": [
                        "Candidate.one",
                        "Candidate.two",
                        "Candidate.three",
                    ],
                    "required_definitions": ["Support.definition"],
                }
            }
        },
        theorem_goals=[
            {
                "target_lean_declaration": "Exact.target",
                "title": "Semantic title",
                "claim": "semantic mathematical statement",
            }
        ],
        max_queries=3,
    )

    assert queries == [
        "Exact.target",
        "Semantic title semantic mathematical statement",
        "Support.definition",
    ]


def test_task_bound_formal_source_queries_and_scope_use_explicit_provenance() -> None:
    theory_packet = {
        "theory_derivation_packet": {
            "formalization_handoff": {
                "candidate_lean_targets": ["LeastSquares.master_error_bound"],
                "source_references": [
                    {
                        "citation": "Source Book (2026), Theorem 13.5",
                        "title": "Localized least-squares error bound",
                    }
                ],
                "formal_source_scope_ids": ["source_library"],
            }
        }
    }
    theorem_goals = [
        {
            "title": "Master error theorem",
            "claim": "the estimator satisfies a localized error bound",
            "source_theorem_target_provenance": {
                "source_id": "source_library"
            },
        }
    ]

    queries = task_bound_formal_source_query_seeds(
        question=OpenResearchQuestion(
            id="source_grounded_query",
            title="Source-grounded theorem",
            description="Reuse a source theorem.",
        ),
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
        max_queries=3,
    )
    source_scope_ids = task_bound_formal_source_scope_ids(
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
    )

    assert queries == [
        "LeastSquares.master_error_bound",
        "Source Book (2026), Theorem 13.5 Localized least-squares error bound",
        "Master error theorem the estimator satisfies a localized error bound",
    ]
    assert source_scope_ids == ("source_library",)

    feedback = formalizer_feedback_with_task_bound_formal_source_queries(
        {},
        question=OpenResearchQuestion(
            id="source_grounded_query",
            title="Source-grounded theorem",
            description="Reuse a source theorem.",
        ),
        theory_packet=theory_packet,
        theorem_goals=theorem_goals,
    )
    repair_context = feedback["proofengineer_repair_context"]
    assert repair_context["retrieval_query_seeds"][:3] == queries
    assert repair_context["formal_source_scope_ids"] == ["source_library"]


def test_camel_tokenization_keeps_semantics_without_short_fragments() -> None:
    tokens = _search_tokens("subGaussian MGF boolToRademacherSign")

    assert {"subgaussian", "gaussian", "mgf", "bool", "rademacher", "sign"}.issubset(
        tokens
    )
    assert "sub" not in tokens
    assert "to" not in tokens


def test_readme_reference_is_searchable_and_persists_in_sqlite(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "SLT"
    source_root.mkdir()
    (tmp_path / "README.md").write_text(
        "| Lean name | Reference |\n"
        "|---|---|\n"
        "| `dudley` | Boucheron et al. (2013), Corollary 13.2 |\n",
        encoding="utf-8",
    )
    (source_root / "Dudley.lean").write_text(
        "import SLT.SubGaussian\n"
        "/-!\n"
        "# Dudley's Entropy Integral Bound\n"
        "Dependency-first chaining for sub-Gaussian processes.\n"
        "-/\n"
        "namespace SLT\n"
        "theorem dudley_helper : True := by trivial\n"
        "theorem long_dudley_bound : True := by trivial\n"
        "theorem dudley : True := by trivial\n"
        "end SLT\n",
        encoding="utf-8",
    )
    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_slt", str(source_root)),)
    )
    dudley = next(row for row in declarations if row.name == "SLT.dudley")
    assert dudley.reference == "Boucheron et al. (2013), Corollary 13.2"
    assert dudley.module_summary == (
        "Dudley's Entropy Integral Bound Dependency-first chaining for "
        "sub-Gaussian processes."
    )
    assert dudley.signature == "theorem dudley : True"
    assert "trivial" not in dudley.signature

    exact_hits = search_formal_sources("dudley", declarations=declarations, k=3)
    assert exact_hits[0].declaration.name == "SLT.dudley"
    reference_hits = search_formal_sources(
        "Boucheron Corollary 13.2",
        declarations=declarations,
        k=3,
    )
    assert reference_hits[0].declaration.name == "SLT.dudley"
    serialized_hit = _formal_source_hit_to_json(reference_hits[0])
    assert serialized_hit["module_summary"] == dudley.module_summary
    assert serialized_hit["reference_aliases"] == []

    sqlite_index = FormalSourceSqliteIndex.build(
        declarations,
        tmp_path / "formal_source.sqlite",
    )
    assert sqlite_index.is_healthy()
    sqlite_hits = sqlite_index.search("Boucheron Corollary 13.2", k=3)
    assert sqlite_hits[0].declaration.name == "SLT.dudley"
    assert sqlite_hits[0].declaration.reference == dudley.reference
    assert sqlite_hits[0].declaration.module_summary == dudley.module_summary

    crosswalk = audit_formal_source_reference_crosswalk(
        FormalSourceRetriever(declarations),
        k=3,
    )
    assert crosswalk["n_reference_bound_declarations"] == 1
    assert crosswalk["n_reference_queries"] == 1
    assert crosswalk["all_ok"] is True
    assert crosswalk["rows"][0]["hit_rank"] == 1
    assert crosswalk["rows"][0]["reference"] == dudley.reference


def test_source_authored_reference_alias_is_searchable_without_runtime_rule(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "SLT"
    source_root.mkdir()
    (tmp_path / "README.md").write_text(
        "| Lean name | Reference / role |\n"
        "|---|---|\n"
        "| `davisKahan` | HDP Theorem 4.1.15, eigenvector angle bound |\n"
        "\n"
        "*(HDP = Vershynin, 2018, High-Dimensional Probability.)*\n",
        encoding="utf-8",
    )
    (source_root / "Perturb.lean").write_text(
        "/-! # Matrix perturbation theory -/\n"
        "theorem davisKahan : True := by trivial\n",
        encoding="utf-8",
    )
    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_hdp", str(source_root)),)
    )
    declaration = declarations[0]

    assert declaration.reference_aliases == (
        "Vershynin, 2018, High-Dimensional Probability Theorem 4.1.15, "
        "eigenvector angle bound",
    )
    hits = search_formal_sources(
        "Vershynin 2018 High Dimensional Probability Theorem 4.1.15",
        declarations=declarations,
        k=2,
    )
    assert hits[0].declaration.name == "davisKahan"

    crosswalk = audit_formal_source_reference_crosswalk(
        FormalSourceRetriever(declarations),
        k=2,
    )
    alias_crosswalk = crosswalk["reference_alias_crosswalk"]
    assert alias_crosswalk["n_queries"] == 1
    assert alias_crosswalk["n_ok"] == 1
    assert alias_crosswalk["all_ok"] is True
    assert crosswalk["citation_families"] == [
        {
            "citation_family": "Vershynin",
            "n_queries": 1,
            "n_ok": 1,
            "all_ok": True,
        }
    ]


def test_source_bibliography_titles_join_three_book_reference_rows(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "SLT"
    source_root.mkdir()
    (tmp_path / "README.md").write_text(
        "| Lean name | Reference |\n"
        "|---|---|\n"
        "| `coveringBound` | Vershynin (2018), Corollary 4.2.13 |\n"
        "| `masterError` | Wainwright (2019), Theorem 13.5 |\n"
        "| `gaussianConcentration` | Boucheron et al. (2013), Theorem 5.6 |\n"
        "\n"
        "## References\n"
        "\n"
        "- Vershynin, R. (2018). *High-Dimensional Probability: An Introduction "
        "with Applications in Data Science*. Cambridge University Press.\n"
        "- Wainwright, M. J. (2019). *High-Dimensional Statistics: A "
        "Non-Asymptotic Viewpoint*. Cambridge University Press.\n"
        "- Boucheron, S., Lugosi, G., & Massart, P. (2013). *Concentration "
        "Inequalities: A Nonasymptotic Theory of Independence*. Oxford "
        "University Press.\n",
        encoding="utf-8",
    )
    (source_root / "Books.lean").write_text(
        "namespace Textbook\n"
        "theorem coveringBound : True := by trivial\n"
        "theorem masterError : True := by trivial\n"
        "theorem gaussianConcentration : True := by trivial\n"
        "end Textbook\n",
        encoding="utf-8",
    )
    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_books", str(source_root)),)
    )
    by_name = {row.name: row for row in declarations}

    assert "High-Dimensional Probability" in by_name[
        "Textbook.coveringBound"
    ].reference_aliases[0]
    assert "Corollary 4.2.13" in by_name[
        "Textbook.coveringBound"
    ].reference_aliases[0]
    assert "High-Dimensional Statistics" in by_name[
        "Textbook.masterError"
    ].reference_aliases[0]
    assert "Theorem 13.5" in by_name[
        "Textbook.masterError"
    ].reference_aliases[0]
    assert "Concentration Inequalities" in by_name[
        "Textbook.gaussianConcentration"
    ].reference_aliases[0]

    retriever = FormalSourceRetriever(declarations)
    queries = {
        "Textbook.coveringBound": (
            "High-Dimensional Probability Applications in Data Science "
            "chapter 4 covering number"
        ),
        "Textbook.masterError": (
            "High-Dimensional Statistics Non-Asymptotic Viewpoint "
            "chapter 13"
        ),
        "Textbook.gaussianConcentration": (
            "Concentration Inequalities Nonasymptotic Theory Independence "
            "chapter 5"
        ),
    }
    for expected_name, query in queries.items():
        assert retriever.search(query, k=3)[0].declaration.name == expected_name

    crosswalk = audit_formal_source_reference_crosswalk(retriever, k=3)
    assert crosswalk["reference_alias_crosswalk"]["n_queries"] == 3
    assert crosswalk["reference_alias_crosswalk"]["all_ok"] is True


def test_source_docs_sections_and_module_taxonomy_are_searchable_and_persist(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "SLT"
    target_dir = source_root / "GaussianLSI"
    target_dir.mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "| Layer | Modules | What's inside |\n"
        "|---|---|---|\n"
        "| Entropy & log-Sobolev | `GaussianLSI/` | Entropy duality, "
        "tensorization, and Gaussian log-Sobolev inequalities. |\n",
        encoding="utf-8",
    )
    (target_dir / "Tensorization.lean").write_text(
        "/-!\n"
        "# Entropy Tensorization\n"
        "Reusable entropy infrastructure.\n"
        "\n"
        "theorem fakeDeclarationInsideModuleDoc : False := by trivial\n"
        "-/\n"
        "namespace LogSobolev\n"
        "/-- Universal coordinate-resampling transfer used by Fubini and tower "
        "arguments. -/\n"
        "lemma coordinateResamplingTransfer : True := by trivial\n"
        "set_option pp.universes true in /- outer comment\n"
        "  /- nested comment -/\n"
        "  theorem fakeNestedCommentDeclaration : False := by trivial\n"
        "-/\n"
        "/-!\n"
        "## Tensorization bridge\n"
        "Move from one-coordinate entropy control to a product measure.\n"
        "-/\n"
        "/-- Close the product-space inequality by summing conditional entropy "
        "terms. -/\n"
        "theorem entropyTensorization : True := by trivial\n"
        "end LogSobolev\n",
        encoding="utf-8",
    )

    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_taxonomy", str(source_root)),)
    )
    by_name = {row.name: row for row in declarations}

    assert "fakeDeclarationInsideModuleDoc" not in by_name
    assert "LogSobolev.fakeNestedCommentDeclaration" not in by_name
    transfer = by_name["LogSobolev.coordinateResamplingTransfer"]
    tensorization = by_name["LogSobolev.entropyTensorization"]
    assert transfer.declaration_doc == (
        "Universal coordinate-resampling transfer used by Fubini and tower "
        "arguments."
    )
    assert transfer.section_summary == ""
    assert tensorization.declaration_doc == (
        "Close the product-space inequality by summing conditional entropy terms."
    )
    assert tensorization.section_summary == (
        "Tensorization bridge Move from one-coordinate entropy control to a "
        "product measure."
    )
    assert tensorization.module_group == "Entropy & log-Sobolev"
    assert tensorization.module_group_summary == (
        "Entropy duality, tensorization, and Gaussian log-Sobolev inequalities."
    )

    retriever = FormalSourceRetriever(declarations)
    doc_hits = retriever.search(
        "product-space inequality conditional entropy terms",
        k=3,
    )
    assert doc_hits[0].declaration.name == "LogSobolev.entropyTensorization"
    section_hits = retriever.search(
        "one-coordinate entropy control product measure",
        k=3,
    )
    assert section_hits[0].declaration.name == "LogSobolev.entropyTensorization"

    sqlite_index = FormalSourceSqliteIndex.build(
        declarations,
        tmp_path / "formal_source.sqlite",
    )
    assert sqlite_index.is_healthy()
    persisted = sqlite_index.search(
        "product-space inequality conditional entropy terms",
        k=1,
    )[0].declaration
    assert persisted.declaration_doc == tensorization.declaration_doc
    assert persisted.section_summary == tensorization.section_summary
    assert persisted.module_group == tensorization.module_group
    assert persisted.module_group_summary == tensorization.module_group_summary


def test_overlapping_source_roots_index_each_physical_file_once(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "ProbabilityProject"
    library_root = project_root / "ProbabilityLibrary"
    library_root.mkdir(parents=True)
    (library_root / "Bounds.lean").write_text(
        "namespace Probability\n"
        "theorem reusableBound : True := by trivial\n"
        "end Probability\n",
        encoding="utf-8",
    )

    declarations = build_formal_source_index(
        roots=(
            FormalSourceRoot("project_owner", str(project_root)),
            FormalSourceRoot("nested_alias", str(library_root)),
        )
    )

    assert [(row.source_id, row.name) for row in declarations] == [
        ("project_owner", "Probability.reusableBound")
    ]


def test_module_taxonomy_normalization_uses_the_configured_source_root_name(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "ProbabilityLibrary"
    target_dir = source_root / "Concentration"
    target_dir.mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "| Layer | Modules | Description |\n"
        "|---|---|---|\n"
        "| Concentration core | `ProbabilityLibrary.Concentration/` | "
        "Reusable concentration inequalities. |\n",
        encoding="utf-8",
    )
    (target_dir / "Bounds.lean").write_text(
        "namespace Probability\n"
        "theorem reusableBound : True := by trivial\n"
        "end Probability\n",
        encoding="utf-8",
    )

    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("generic_probability", str(source_root)),)
    )

    assert len(declarations) == 1
    assert declarations[0].module_group == "Concentration core"
    assert declarations[0].module_group_summary == (
        "Reusable concentration inequalities."
    )


def test_module_summary_is_a_shared_low_weight_semantic_hint(
    monkeypatch,
) -> None:
    module_summary = (
        "Kolmogorov extension theorem projective family finite dimensional "
        "distributions measure"
    )
    declarations = [
        FormalDeclaration(
            source_id="direct_source",
            source_type="lean_library",
            path="Direct.lean",
            line=1,
            kind="def",
            name="MeasureTheory.projectiveFamilyContent",
            namespace="MeasureTheory",
            signature="def projectiveFamilyContent : True",
        ),
        *[
            FormalDeclaration(
                source_id="summary_source",
                source_type="lean_library",
                path="Summary.lean",
                line=index,
                kind="lemma",
                name=f"Summary.unrelated{index}",
                namespace="Summary",
                signature=f"lemma unrelated{index} : True",
                module_summary=module_summary,
            )
            for index in range(1, 5)
        ],
    ]
    import ai_statistician.formal_source_index as formal_source_index

    original_search_tokens = formal_source_index._search_tokens
    summary_tokenizations = 0

    def counted_search_tokens(text: str):
        nonlocal summary_tokenizations
        if text == module_summary:
            summary_tokenizations += 1
        return original_search_tokens(text)

    monkeypatch.setattr(
        formal_source_index,
        "_search_tokens",
        counted_search_tokens,
    )
    retriever = FormalSourceRetriever(declarations)
    assert summary_tokenizations == 1

    hits = retriever.search(module_summary, k=5)

    assert hits[0].declaration.name == (
        "MeasureTheory.projectiveFamilyContent"
    )


def test_repeated_source_metadata_does_not_multiply_retrieval_score() -> None:
    doc_only = FormalDeclaration(
        source_id="fixture",
        source_type="lean_library",
        path="DocOnly.lean",
        line=1,
        kind="theorem",
        name="Fixture.docOnly",
        namespace="Fixture",
        signature="theorem docOnly : True",
        declaration_doc="entropy tensorization",
    )
    repeated = replace(
        doc_only,
        path="Repeated.lean",
        name="Fixture.repeated",
        signature="theorem repeated : True",
        module_summary="entropy tensorization",
        section_summary="entropy tensorization",
        module_group="entropy tensorization",
        module_group_summary="entropy tensorization",
    )

    hits = FormalSourceRetriever([doc_only, repeated]).search(
        "entropy tensorization",
        k=2,
    )

    scores = {hit.declaration.name: hit.score for hit in hits}
    assert scores["Fixture.docOnly"] == scores["Fixture.repeated"]


def test_source_authored_public_api_and_semantic_name_outrank_helper_prose() -> None:
    public_theorem = FormalDeclaration(
        source_id="fixture",
        source_type="lean_library",
        path="Probability/Tensorized.lean",
        line=90,
        kind="theorem",
        name="Probability.gaussianLogSobolev",
        namespace="Probability",
        signature=(
            "theorem gaussianLogSobolev (f : Real -> Real) : True"
        ),
        reference="Source Book (2026), Theorem 5.4",
        module_summary=(
            "Main results: Probability.gaussianLogSobolev gives the public "
            "dimension-free inequality."
        ),
    )
    helper = FormalDeclaration(
        source_id="fixture",
        source_type="lean_library",
        path="Probability/Density.lean",
        line=12,
        kind="lemma",
        name="Probability.gaussianSobolevNormSq_add_le_of_diff",
        namespace="Probability",
        signature=(
            "lemma gaussianSobolevNormSq_add_le_of_diff : True"
        ),
        declaration_doc=(
            "Technical Gaussian log Sobolev inequality helper for a density "
            "argument."
        ),
    )
    unrelated_public_theorem = replace(
        public_theorem,
        path="Probability/Other.lean",
        name="Probability.matrixBernstein",
        signature="theorem matrixBernstein : True",
        reference="Other Book (2026), Theorem 1",
        module_summary="Main results: Probability.matrixBernstein.",
    )

    hits = FormalSourceRetriever(
        [helper, unrelated_public_theorem, public_theorem]
    ).search("Gaussian log Sobolev inequality", k=3)

    assert hits[0].declaration.name == "Probability.gaussianLogSobolev"
    assert all(
        hit.declaration.name != "Probability.matrixBernstein"
        for hit in hits
    )


def test_sqlite_hybrid_builds_python_fallback_only_after_database_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    declarations = [
        FormalDeclaration(
            source_id="fixture",
            source_type="lean_library",
            path="Demo.lean",
            line=1,
            kind="theorem",
            name="Demo.variance_bound",
            namespace="Demo",
            signature="theorem variance_bound : True",
        )
    ]
    sqlite_index = FormalSourceSqliteIndex.build(
        declarations,
        tmp_path / "formal_source.sqlite",
    )
    retriever = FormalSourceHybridRetriever(declarations, sqlite_index)

    assert retriever.fallback_retriever is None
    assert retriever.search("variance bound", k=1)
    assert retriever.fallback_retriever is None

    def fail_sqlite_search(query: str, *, k: int):
        raise sqlite3.DatabaseError("fixture failure")

    monkeypatch.setattr(sqlite_index, "search", fail_sqlite_search)
    hits = retriever.search("variance bound", k=1)

    assert hits[0].declaration.name == "Demo.variance_bound"
    assert isinstance(retriever.fallback_retriever, FormalSourceRetriever)


def test_readme_reference_does_not_spill_across_duplicate_short_names(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "| Lean name | Reference |\n"
        "|---|---|\n"
        "| `Matrix.shared` | Exact matrix reference |\n"
        "| `ambiguous` | Ambiguous short reference |\n",
        encoding="utf-8",
    )
    (tmp_path / "Matrix.lean").write_text(
        "namespace Matrix\n"
        "theorem shared : True := by trivial\n"
        "theorem ambiguous : True := by trivial\n"
        "end Matrix\n",
        encoding="utf-8",
    )
    (tmp_path / "LinearMap.lean").write_text(
        "namespace LinearMap\n"
        "theorem shared : True := by trivial\n"
        "theorem ambiguous : True := by trivial\n"
        "end LinearMap\n",
        encoding="utf-8",
    )

    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_duplicates", str(tmp_path)),)
    )
    by_name = {row.name: row for row in declarations}

    assert by_name["Matrix.shared"].reference == "Exact matrix reference"
    assert by_name["LinearMap.shared"].reference == ""
    assert by_name["Matrix.ambiguous"].reference == ""
    assert by_name["LinearMap.ambiguous"].reference == ""


def test_readme_reference_resolves_one_unique_renamed_declaration_prefix(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "| Lean name | Reference |\n"
        "|---|---|\n"
        "| `one_step_discretization` | Wainwright (2019), Proposition 5.17 |\n",
        encoding="utf-8",
    )
    (tmp_path / "TDudley.lean").write_text(
        "namespace TDudley\n"
        "lemma one_step_discretization_bound : True := by trivial\n"
        "lemma expectation_one_step_bound : True := by trivial\n"
        "end TDudley\n",
        encoding="utf-8",
    )

    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_rename", str(tmp_path)),)
    )
    by_name = {row.name: row for row in declarations}

    assert by_name["TDudley.one_step_discretization_bound"].reference == (
        "Wainwright (2019), Proposition 5.17"
    )
    assert by_name["TDudley.expectation_one_step_bound"].reference == ""
    hits = search_formal_sources(
        "Wainwright 2019 Proposition 5.17",
        declarations=declarations,
        k=2,
    )
    assert hits[0].declaration.name == (
        "TDudley.one_step_discretization_bound"
    )


def test_cache_coverage_rejects_missing_current_readme_reference(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "| Lean name | Reference |\n"
        "|---|---|\n"
        "| `semantic_result` | Example Book (2026), Theorem 2.1 |\n",
        encoding="utf-8",
    )
    (tmp_path / "Main.lean").write_text(
        "theorem semantic_result : True := by trivial\n",
        encoding="utf-8",
    )
    root = FormalSourceRoot("fixture_cache_reference", str(tmp_path))
    stale = [
        FormalDeclaration(
            source_id=root.id,
            source_type="lean_library",
            path="Main.lean",
            line=1,
            kind="theorem",
            name="semantic_result",
            namespace="",
            signature="theorem semantic_result : True",
        )
    ]

    assert not _cache_covers_configured_roots(stale, (root,))
    current = build_formal_source_index(roots=(root,))
    assert _cache_covers_configured_roots(current, (root,))


def test_readme_reference_does_not_guess_ambiguous_renamed_prefix(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "| Lean name | Reference |\n"
        "|---|---|\n"
        "| `semantic_result` | Example Book, Theorem 1 |\n"
        "| `semantic_result_alt` | Example Book, Theorem 2 |\n",
        encoding="utf-8",
    )
    (tmp_path / "Main.lean").write_text(
        "theorem semantic_result_alternative_bound : True := by trivial\n",
        encoding="utf-8",
    )

    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_rename_collision", str(tmp_path)),)
    )

    assert len(declarations) == 1
    assert declarations[0].reference == ""


def test_sqlite_health_rejects_cache_without_reference_columns(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "stale.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE declarations (id INTEGER PRIMARY KEY, name TEXT)"
        )
        conn.execute(
            "CREATE VIRTUAL TABLE declarations_fts USING fts5(decl_id, name)"
        )

    assert not FormalSourceSqliteIndex(db_path).is_healthy()


def test_formal_source_cache_is_bound_to_current_source_snapshot(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "Source"
    source_root.mkdir()
    source_path = source_root / "Main.lean"
    source_path.write_text(
        "theorem first_cached_result : True := by trivial\n",
        encoding="utf-8",
    )
    root = FormalSourceRoot("snapshot_fixture", str(source_root))
    cache_path = tmp_path / "cache.sqlite"

    first = build_formal_source_search_backend(
        db_path=tmp_path / "first.sqlite",
        roots=(root,),
        cache_path=cache_path,
        include_graph=False,
    )
    assert getattr(first, "cache_status") == "miss"
    assert first.source_snapshots()["snapshot_fixture"]["exists"] is True

    second = build_formal_source_search_backend(
        db_path=tmp_path / "second.sqlite",
        roots=(root,),
        cache_path=cache_path,
        include_graph=False,
    )
    assert getattr(second, "cache_status") == "hit"

    source_path.write_text(
        "theorem replacement_cached_result : True := by trivial\n",
        encoding="utf-8",
    )
    rebuilt = build_formal_source_search_backend(
        db_path=tmp_path / "rebuilt.sqlite",
        roots=(root,),
        cache_path=cache_path,
        include_graph=False,
    )

    assert getattr(rebuilt, "cache_status") == "miss"
    names = {row.name for row in rebuilt.load_declarations()}
    assert "replacement_cached_result" in names
    assert "first_cached_result" not in names


def test_lean_sections_do_not_corrupt_namespace_and_long_outline_keeps_conclusion(
    tmp_path: Path,
) -> None:
    arguments = "\n".join(
        f"    (h{idx} : True) -- explanatory comment {idx}"
        for idx in range(12)
    )
    (tmp_path / "Scoped.lean").write_text(
        "namespace Matrix\n"
        "section Helpers\n"
        "theorem inside_section : True := by trivial\n"
        "end Helpers\n"
        "instance instInhabitedUnit : Inhabited Unit where\n"
        "  default := ()\n"
        "theorem linear_δ_star : True := by trivial\n"
        "noncomputable def avgθ : Nat := 0\n"
        "noncomputable def linear_C₁ : Nat := 1\n"
        "theorem unicode_shape (h : avgθ = linear_C₁) : "
        "avgθ = linear_C₁ := by exact h\n"
        "namespace IsSymmetric\n"
        "theorem Property.bound : True := by trivial\n"
        "end IsSymmetric\n"
        "theorem _root_.global_scoped_result : True := by trivial\n"
        f"theorem after_section\n{arguments}\n"
        "    : True := by trivial\n"
        "end Matrix\n",
        encoding="utf-8",
    )

    declarations = build_formal_source_index(
        roots=(FormalSourceRoot("fixture_scoped", str(tmp_path)),)
    )
    by_name = {row.name: row for row in declarations}

    assert "Matrix.inside_section" in by_name
    assert by_name["Matrix.instInhabitedUnit"].kind == "instance"
    assert by_name["Matrix.instInhabitedUnit"].signature == (
        "instance instInhabitedUnit : Inhabited Unit"
    )
    assert by_name["Matrix.linear_δ_star"].signature == (
        "theorem linear_δ_star : True"
    )
    assert by_name["Matrix.avgθ"].signature == "noncomputable def avgθ : Nat"
    assert by_name["Matrix.linear_C₁"].signature == (
        "noncomputable def linear_C₁ : Nat"
    )
    unicode_shape = by_name["Matrix.unicode_shape"]
    assert unicode_shape.premise_heads == ("avgθ",)
    assert unicode_shape.conclusion_head == "avgθ"
    assert "linear_C₁" in unicode_shape.major_symbols
    nested = by_name["Matrix.IsSymmetric.Property.bound"]
    assert nested.namespace == "Matrix.IsSymmetric.Property"
    assert "global_scoped_result" in by_name
    assert "Matrix.global_scoped_result" not in by_name
    assert by_name["global_scoped_result"].namespace == ""
    assert "Matrix.after_section" in by_name
    outline = by_name["Matrix.after_section"].signature
    assert outline.endswith(": True")
    assert "explanatory comment" not in outline
    assert "trivial" not in outline

    sqlite_index = FormalSourceSqliteIndex.build(
        declarations,
        tmp_path / "unicode-formal-source.sqlite",
    )
    unicode_hits = sqlite_index.search("linear_δ_star", k=3)
    assert unicode_hits[0].declaration.name == "Matrix.linear_δ_star"


def test_import_terms_only_rerank_semantically_grounded_formal_source_hits(
    tmp_path: Path,
) -> None:
    declarations = [
        FormalDeclaration(
            source_id="fixture",
            source_type="lean_library",
            path="Unrelated.lean",
            line=1,
            kind="theorem",
            name="Fixture.noise",
            namespace="Fixture",
            signature="theorem noise : True",
            imports=("SLT.Dudley.Basic",),
        ),
        FormalDeclaration(
            source_id="fixture",
            source_type="lean_library",
            path="Entropy.lean",
            line=1,
            kind="theorem",
            name="Fixture.entropyBound",
            namespace="Fixture",
            signature="theorem entropyBound : True",
            imports=("SLT.Dudley.Basic",),
        ),
    ]

    retriever = FormalSourceRetriever(declarations)
    assert retriever.search("Dudley", k=3) == []
    hits = retriever.search("Dudley entropy", k=3)
    assert hits[0].declaration.name == "Fixture.entropyBound"
    assert hits[0].matched_terms == ("entropy",)

    sqlite_index = FormalSourceSqliteIndex.build(
        declarations,
        tmp_path / "field-aware.sqlite",
    )
    assert sqlite_index.search("Dudley", k=3) == []
    sqlite_hits = sqlite_index.search("Dudley entropy", k=3)
    assert sqlite_hits[0].matched_terms == ("entropy",)

    graph = FormalSourceGraphRetriever(declarations)
    assert graph.search("Dudley", k=3) == []
    graph_hits = graph.search("entropy", k=3)
    assert all(
        hit.declaration.name != "Fixture.noise"
        for hit in graph_hits
    )


def test_source_diversification_preserves_top_hit_and_relevant_corpora() -> None:
    def hit(source_id: str, name: str, score: float) -> FormalSourceHit:
        return FormalSourceHit(
            declaration=FormalDeclaration(
                source_id=source_id,
                source_type="lean_library",
                path=f"{name}.lean",
                line=1,
                kind="theorem",
                name=name,
                namespace="",
                signature=f"theorem {name} : True",
            ),
            score=score,
            matched_terms=("entropy",),
        )

    ranked = [
        hit("formal_slt", "top", 10.0),
        hit("formal_slt", "same_source_second", 9.5),
        hit("lean_stat_learning_theory", "slt_candidate", 8.0),
        hit("lean_rademacher", "rademacher_candidate", 7.0),
        hit("unrelated", "low_score", 2.0),
    ]

    diversified = diversify_formal_source_hits(ranked, k=4)

    assert diversified[0].declaration.name == "top"
    assert [row.declaration.source_id for row in diversified[:3]] == [
        "formal_slt",
        "lean_stat_learning_theory",
        "lean_rademacher",
    ]
    assert "unrelated" not in {
        row.declaration.source_id for row in diversified
    }

    prompt_ranked = diversify_formal_source_hits(
        ranked,
        k=4,
        preserve_top_n=2,
    )
    assert [row.declaration.name for row in prompt_ranked[:2]] == [
        "top",
        "same_source_second",
    ]
    assert prompt_ranked[2].declaration.source_id == (
        "lean_stat_learning_theory"
    )


def test_source_scoped_search_filters_main_index_and_supports_two_stage_eval(
    tmp_path: Path,
) -> None:
    declarations = [
        FormalDeclaration(
            source_id="source_a",
            source_type="lean_library",
            path="A.lean",
            line=1,
            kind="theorem",
            name="A.semantic_bridge",
            namespace="A",
            signature="theorem semantic_bridge : True",
        ),
        FormalDeclaration(
            source_id="source_b",
            source_type="lean_library",
            path="B.lean",
            line=1,
            kind="theorem",
            name="B.semantic_bridge_copy",
            namespace="B",
            signature="theorem semantic_bridge_copy : True",
        ),
        FormalDeclaration(
            source_id="source_a",
            source_type="lean_library",
            path="A.lean",
            line=2,
            kind="theorem",
            name="A.semantic_target",
            namespace="A",
            signature="theorem semantic_target : True",
        ),
    ]
    sqlite_index = FormalSourceSqliteIndex.build(
        declarations,
        tmp_path / "scoped.sqlite",
    )
    retriever = FormalSourceHybridRetriever(declarations, sqlite_index)

    scoped = retriever.search_with_source_scope(
        "semantic",
        source_scope_ids=("source_a",),
        k=2,
    )
    assert [hit.declaration.name for hit in scoped] == [
        "A.semantic_bridge",
        "A.semantic_target"
    ]

    payload = run_formal_source_retrieval_benchmark(
        retriever=retriever,
        cases=(
            FormalSourceRetrievalBenchmarkCase(
                query_id="two_stage",
                query="semantic",
                expected_name_fragments=("semantic_target",),
                expected_source_ids=("source_a",),
            ),
        ),
        k=2,
    )
    row = payload["rows"][0]
    assert row["source_discovery_rank"] == 1
    assert row["direct_hit_rank"] is None
    assert row["scoped_hit_rank"] == 2
    assert row["hit_rank"] == 2
    assert row["scoped_source_id"] == "source_a"
    assert row["scoped_source_ids_attempted"] == ("source_a", "source_b")
    assert row["resolution_mode"] == (
        "global_source_discovery_then_scoped_declaration"
    )
    assert payload["all_ok"] is True


def test_retrieval_benchmark_rejects_source_scoped_prover_context_leakage() -> None:
    target = FormalDeclaration(
        source_id="source_a",
        source_type="lean_library",
        path="A.lean",
        line=1,
        kind="theorem",
        name="A.semantic_target",
        namespace="A",
        signature="theorem semantic_target : True",
    )
    distractor = replace(
        target,
        source_id="unrelated_proof_bank",
        path="Distractor.lean",
        name="Distractor.semantic_target_copy",
        namespace="Distractor",
    )

    class LeakyScopedRetriever:
        declarations = [target, distractor]

        def search(self, _query: str, *, k: int = 10):
            return [
                FormalSourceHit(target, 2.0, ("semantic",)),
                FormalSourceHit(distractor, 1.0, ("semantic",)),
            ][:k]

        def search_with_source_scope(
            self,
            _query: str,
            *,
            source_scope_ids: tuple[str, ...],
            k: int = 10,
        ):
            assert source_scope_ids == ("source_a",)
            return self.search("semantic", k=k)

    payload = run_formal_source_retrieval_benchmark(
        retriever=LeakyScopedRetriever(),
        cases=(
            FormalSourceRetrievalBenchmarkCase(
                query_id="leaky_scope",
                query="semantic target",
                expected_name_fragments=("semantic_target",),
                expected_source_ids=("source_a",),
            ),
        ),
        k=2,
    )

    row = payload["rows"][0]
    assert payload["retrieval_recall_all_ok"] is True
    assert row["source_scoped_context_hit_rank"] == 1
    assert row["source_scoped_context_n_out_of_scope_hits"] == 1
    assert row["source_scoped_context_ok"] is False
    assert payload["source_scoped_context_all_ok"] is False
    assert payload["all_ok"] is False


def test_provider_fusion_deduplicates_mirrors_without_score_multiplication() -> None:
    canonical = FormalDeclaration(
        source_id="current_source",
        source_type="lean_library",
        path="Current.lean",
        line=1,
        kind="theorem",
        name="Demo.semantic_bound",
        namespace="Demo",
        signature="theorem semantic_bound : True",
    )
    mirror = replace(
        canonical,
        source_id="mirror_corpus",
        path="Mirror.lean",
    )
    distinct_signature = replace(
        mirror,
        signature="theorem semantic_bound : False",
    )
    fusion = _FusionAccumulator()
    fusion.add(canonical, score=10.0, matched_terms=("semantic",), provider="sqlite")
    fusion.add(mirror, score=9.0, matched_terms=("bound",), provider="graph")
    fusion.add(
        distinct_signature,
        score=8.0,
        matched_terms=("semantic",),
        provider="premise",
    )

    hits = fusion.hits()

    assert len(hits) == 2
    canonical_hit = next(
        hit for hit in hits if hit.declaration.signature.endswith(": True")
    )
    assert canonical_hit.declaration is canonical
    assert canonical_hit.score == 10.5
    assert {"sqlite", "graph", "semantic", "bound"}.issubset(
        canonical_hit.matched_terms
    )


def test_formal_source_hit_context_keeps_outline_and_nonproof_boundary() -> None:
    declaration = FormalDeclaration(
        source_id="lean_stat_learning_theory",
        source_type="lean_library",
        path="SLT/LeastSquares/MasterErrorBound.lean",
        line=878,
        kind="theorem",
        name="LeastSquares.master_error_bound",
        namespace="LeastSquares",
        signature="theorem master_error_bound : True",
        imports=("SLT.LeastSquares.Localization", "SLT.GaussianLipConcen"),
        reference="Wainwright (2019), Theorem 13.5",
        reference_aliases=("Wainwright, 2019, High-Dimensional Statistics",),
        module_summary=(
            "Master error bound for localized least-squares regression."
        ),
        declaration_doc=(
            "Convert a localized Gaussian complexity bound into prediction error."
        ),
        section_summary="Localized least-squares master theorem.",
        module_group="Least squares",
        module_group_summary=(
            "Localized least-squares framework and sharp regression rates."
        ),
    )
    payload = _formal_source_hit_to_json(
        FormalSourceHit(declaration, 9.0, ("wainwright", "13.5"))
    )

    assert payload["namespace"] == "LeastSquares"
    assert payload["imports"] == [
        "SLT.LeastSquares.Localization",
        "SLT.GaussianLipConcen",
    ]
    assert payload["reference"] == "Wainwright (2019), Theorem 13.5"
    assert payload["reference_aliases"] == [
        "Wainwright, 2019, High-Dimensional Statistics"
    ]
    assert payload["module_summary"] == (
        "Master error bound for localized least-squares regression."
    )
    assert payload["declaration_doc"] == (
        "Convert a localized Gaussian complexity bound into prediction error."
    )
    assert payload["section_summary"] == (
        "Localized least-squares master theorem."
    )
    assert payload["module_group"] == "Least squares"
    assert payload["module_group_summary"] == (
        "Localized least-squares framework and sharp regression rates."
    )
    assert "kernel_verified" not in payload


def test_formal_source_hit_context_adds_bounded_outline_and_dependency_neighbors() -> None:
    declarations = [
        FormalDeclaration(
            source_id="lean_stat_learning_theory",
            source_type="lean_library",
            path="SLT/LeastSquares/MasterErrorBound.lean",
            line=line,
            kind=kind,
            name=name,
            namespace="LeastSquares",
            signature=signature,
            imports=("SLT.LeastSquares.Localization", "SLT.GaussianLipConcen"),
            module_summary=(
                "Master error bound for localized least-squares regression."
            ),
            module_group="Least squares",
            module_group_summary=(
                "Localized least-squares framework and sharp regression rates."
            ),
        )
        for line, kind, name, signature in (
            (640, "theorem", "LeastSquares.bad_event_probability_bound", "theorem bad_event_probability_bound : True"),
            (858, "def", "LeastSquares.goodEvent", "def goodEvent : Set Unit"),
            (878, "theorem", "LeastSquares.master_error_bound", "theorem master_error_bound : True"),
            (930, "lemma", "LeastSquares.master_error_bound_corollary", "lemma master_error_bound_corollary : True"),
        )
    ]
    retriever = FormalSourceRetriever(declarations)

    class DependencyProvider:
        source = "fixture_dependency_graph"

        def dependency_context(
            self,
            declaration_name: str,
            *,
            limit: int,
            source_id: str,
            path: str,
        ):
            assert declaration_name == "LeastSquares.master_error_bound"
            assert limit == 10
            assert source_id == "lean_stat_learning_theory"
            assert path == "SLT/LeastSquares/MasterErrorBound.lean"
            return SimpleNamespace(
                fan_in=8,
                fan_out=3,
                uses=("LeastSquares.bad_event_probability_bound",),
                used_by=("LeastSquares.linear_minimax_rate_rank",),
                statement_uses=("LeastSquares.localizedBall",),
                proof_uses=("LeastSquares.bad_event_probability_bound",),
                source_id="lean_stat_learning_theory",
                module="SLT.LeastSquares.MasterErrorBound",
                module_ancestry=(
                    "SLT",
                    "SLT.LeastSquares",
                    "SLT.LeastSquares.MasterErrorBound",
                ),
                source_snapshot_status="BOUND_MATCH",
                source_snapshot_bound=True,
                source_snapshot_match=True,
                source_snapshot_metadata=(
                    ("source_git_commit", "a" * 40),
                    ("lean_toolchain", "leanprover/lean4:v4.32.0"),
                ),
            )

    retriever.dependency_retriever = DependencyProvider()
    hit = FormalSourceHit(declarations[2], 9.0, ("master", "error"))

    payload = _formal_source_hit_to_json(
        hit,
        formal_source_retriever=retriever,
    )

    context = payload["declaration_source_context"]
    assert context["module"] == "SLT.LeastSquares.MasterErrorBound"
    assert context["module_summary"] == (
        "Master error bound for localized least-squares regression."
    )
    assert context["imports"] == [
        "SLT.LeastSquares.Localization",
        "SLT.GaussianLipConcen",
    ]
    assert context["module_group"] == "Least squares"
    assert context["module_group_summary"] == (
        "Localized least-squares framework and sharp regression rates."
    )
    assert [
        row["name"]
        for row in context["premise_declaration_outlines"]
    ] == [
        "LeastSquares.bad_event_probability_bound",
    ]
    assert [row["name"] for row in context["nearby_declaration_outlines"]] == [
        "LeastSquares.goodEvent",
    ]
    assert [row["name"] for row in context["local_naming_examples"]] == [
        "LeastSquares.goodEvent",
        "LeastSquares.bad_event_probability_bound",
    ]
    assert context["n_same_file_declarations"] == 4
    assert context["n_prior_same_file_declarations"] == 2
    assert context["n_direct_premise_declaration_outlines"] == 1
    assert context["n_prior_same_file_fallback_candidates"] == 1
    assert context["n_downstream_same_file_declarations_omitted"] == 1
    assert context["outline_selection"] == (
        "direct_statement_dependencies_then_direct_proof_dependencies_"
        "then_nearest_prior_same_file_fallback"
    )
    assert context["dependency_context"]["corpus_id"] == (
        "lean_stat_learning_theory"
    )
    assert context["dependency_context"]["module_ancestry"] == [
        "SLT",
        "SLT.LeastSquares",
        "SLT.LeastSquares.MasterErrorBound",
    ]
    assert context["dependency_context"]["source_snapshot"] == {
        "status": "BOUND_MATCH",
        "bound": True,
        "match": True,
        "metadata": {
            "source_git_commit": "a" * 40,
            "lean_toolchain": "leanprover/lean4:v4.32.0",
        },
        "evidence_status": (
            "SOURCE_SNAPSHOT_IDENTITY_NOT_ACTIVE_PROJECT_PROOF_EVIDENCE"
        ),
    }
    assert context["dependency_context"]["statement_uses"] == [
        "LeastSquares.localizedBall"
    ]
    assert context["dependency_context"]["proof_uses"] == [
        "LeastSquares.bad_event_probability_bound"
    ]
    assert context["dependency_context"][
        "n_downstream_declarations_omitted"
    ] == 1
    assert "used_by" not in context["dependency_context"]
    assert "candidate_proof_body" not in str(context)
    assert all(
        ":= by" not in row["signature"]
        for row in (
            context["premise_declaration_outlines"]
            + context["nearby_declaration_outlines"]
        )
    )


def test_formal_source_prompt_payload_omits_full_candidate_proof_body() -> None:
    body = "by\n  exact hp\n"
    declaration = FormalDeclaration(
        source_id="proof_bank",
        source_type="lean_proof_bank_obligation",
        path="proof_bank.py",
        line=1,
        kind="proof_obligation",
        name="identity",
        namespace="",
        signature="theorem identity (p : Prop) (hp : p) : p",
    )
    payload = _formal_source_hit_to_json(
        SimpleNamespace(
            declaration=declaration,
            score=1.0,
            matched_terms=("identity",),
            provenance={
                "provider": "proof_bank",
                "candidate_proof_body": body,
                "provider_support": [
                    {
                        "provenance": {
                            "candidate_proof_body": "by\n  assumption\n"
                        }
                    }
                ],
            },
        )
    )

    provenance = payload["provenance"]
    assert "candidate_proof_body" not in provenance
    assert provenance["candidate_proof_body_chars"] == len(body)
    assert provenance["candidate_proof_body_hash"]
    assert provenance["provider"] == "proof_bank"
    nested = provenance["provider_support"][0]["provenance"]
    assert "candidate_proof_body" not in nested
    assert nested["candidate_proof_body_hash"]


def test_formalizer_prompt_uses_compact_incremental_proof_strategy() -> None:
    contract = formalizer_proof_construction_strategy_contract()
    assert contract["schema_version"] == 10
    assert "smallest diagnostic" in contract["repair_cycle"]
    assert "faithful natural-language statement" in contract["specification"]
    assert "four-part structured specification" in contract[
        "specification"
    ].lower()
    assert "qualified infrastructure pointers" in contract["specification"]
    assert "formalization-oriented lemma/proof plan" in contract[
        "specification"
    ]
    assert "hard evidence" in contract["specification"]
    assert "source-local namespace/module role" in contract["context_policy"]
    assert "source-authored declaration docs" in contract["context_policy"]
    assert "initial API design and declaration placement" in contract[
        "context_policy"
    ]
    assert "live Lean goal or diagnostic" in contract["context_policy"]
    assert "only a few qualified signatures" in contract["context_policy"]
    assert "do not resend taxonomy" in contract["context_policy"]
    assert "active toolchain/version gates" in contract["context_policy"]
    assert "may retain two ranked target signatures" in contract["context_policy"]
    assert "other queries retain one" in contract["context_policy"]
    assert "module/import identity separately" in contract["context_policy"]
    assert "may differ" in contract["context_policy"]
    assert "section/module taxonomy" in contract["context_policy"]
    assert "naming, and citations may rank candidates" in contract["context_policy"]
    assert "direct premise outlines first" in contract["context_policy"]
    assert "bounded prior fallback" in contract["context_policy"]
    assert "no source files or proof bodies" in contract["context_policy"]
    assert "measurability" in contract["assumption_audit"]
    assert "integrability" in contract["assumption_audit"]
    assert "formal gap" in contract["assumption_audit"]
    assert "do not silently invent" in contract["assumption_audit"]
    assert "dependency-ordered lemma dag" in contract["decomposition"].lower()
    assert "one semantic obligation per node" in contract["decomposition"]
    assert "bounded compiler-feedback episode" in contract[
        "decomposition"
    ]
    assert "minimal explicit support-dependency plan" in contract[
        "decomposition"
    ]
    assert "[] for a direct proof" in contract["decomposition"]
    assert "preserve verified ancestors" in contract["decomposition"]
    assert "fix errors one-by-one" in contract["repair_cycle"]
    assert "no unchanged retry" in contract["repair_cycle"]
    assert "wholesale rewrite without evidence" in contract["repair_cycle"]
    assert "Independently recheck target fidelity" in contract[
        "persistent_failure_route"
    ]
    assert "counterexamples" in contract["persistent_failure_route"]
    assert "evolve the specification" in contract[
        "persistent_failure_route"
    ]
    assert "quantifiers" in contract["persistent_failure_route"]
    assert "exact active-project artifact" in contract["post_compile_hygiene"]
    assert "lowest reusable mathematical layer" in contract["library_design"]
    assert "reusable mathematical dependency rather than textbook order" in contract[
        "library_design"
    ]
    assert "infer namespace, module placement, and naming style" in contract[
        "library_design"
    ]
    assert "stable semantic Lean names" in contract["library_design"]
    assert "avoid duplicate wrappers" in contract["library_design"]
    assert "source metadata rather than declaration identity" in contract[
        "library_design"
    ]
    assert "exact compatible imported declaration" in contract["reuse_policy"]
    assert "non-visible-module hits are context only" in contract["reuse_policy"]
    assert "exact active project" in contract["reuse_policy"]
    assert "revalidate every selected declaration" in contract["reuse_policy"]
    assert "opus" not in str(contract).lower()

    question = load_open_research_questions(
        Path("examples/research_questions.json")
    )[0]
    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        registered_problem={},
        theorem_goals=[],
    )

    assert "proof_construction_strategy_contract" in prompt
    assert "direct premise outlines first" in prompt
    assert "dependency-ordered lemma dag" in prompt.lower()
    assert "one semantic obligation per node" in prompt
    assert "no unchanged retry" in prompt
    assert "fix errors one-by-one" in prompt
    assert "stable semantic Lean names" in prompt
    assert "do not silently invent" in prompt
    assert "exact compatible imported declaration" in prompt
    assert "four-part structured specification" in prompt.lower()
    assert "source-authored declaration docs" in prompt


def test_formal_source_prompt_projection_keeps_target_and_dependency_scopes() -> None:
    long_signature = "theorem target_bound " + "(h : True) " * 120 + ": True"
    premise_rows = [
        {
            "dependency_scope": scope,
            "name": name,
            "signature": f"theorem {name.rsplit('.', 1)[-1]} " + "(h : True) " * 40 + ": True",
        }
        for scope, name in (
            ("statement", "Library.TargetObject"),
            ("statement", "Library.TargetDefinition"),
            ("proof", "Library.KeyReduction"),
            ("proof", "Library.ClosingLemma"),
            ("proof", "Library.FinalBound"),
        )
    ]
    groups = [
        {
            "query": "target query " * 80,
            "query_role": "initial_formalization_context",
            "query_fingerprint": "a" * 64,
            "hits": [
                {
                    "source_id": "fixture_library",
                    "source_type": "lean_library",
                    "path": "Library/Target.lean",
                    "line": 101,
                    "kind": "theorem",
                    "name": "Library.target_bound",
                    "namespace": "Library",
                    "signature": long_signature,
                    "declaration_doc": (
                        "Reduce the target to one reusable local concentration lemma "
                        "and close with the imported comparison theorem."
                    ),
                    "section_summary": "Final localized comparison theorem.",
                    "imports": ["Library.Foundation", "Library.Reduction"],
                    "reference": "Source (2026), Theorem 1",
                    "reference_aliases": ["Source Book Full Title Theorem 1"],
                    "declaration_source_context": {
                        "module": "Library.Target",
                        "module_summary": (
                            "Target theorem for the reusable Library reduction layer."
                        ),
                        "module_group": "Localized applications",
                        "module_group_summary": (
                            "Application theorems built from reusable concentration "
                            "and capacity layers."
                        ),
                        "local_naming_examples": [
                            {
                                "kind": "lemma",
                                "name": "Library.target_local_reduction",
                            },
                            {
                                "kind": "theorem",
                                "name": "Library.target_comparison_bound",
                            },
                        ],
                        "imports": ["Library.Foundation", "Library.Reduction"],
                        "premise_declaration_outlines": premise_rows,
                        "dependency_context": {
                            "module_ancestry": ["Library", "Library.Target"],
                            "source_snapshot": {
                                "status": "BOUND_MATCH",
                                "bound": True,
                                "match": True,
                                "metadata": {"source_git_commit": "b" * 40},
                            },
                        },
                    },
                    "candidate_proof_body": "by exact hiddenProof",
                },
                {
                    "source_id": "unrelated",
                    "path": "Other.lean",
                    "line": 1,
                    "kind": "theorem",
                    "name": "Other.large_candidate",
                    "signature": long_signature * 3,
                },
            ],
        },
        {
            "query": "semantic theorem meaning",
            "query_role": "semantic_target",
            "query_fingerprint": "c" * 64,
            "hits": [
                {
                    "source_id": "fixture_library",
                    "path": "Library/Target.lean",
                    "line": 101,
                    "kind": "theorem",
                    "name": "Library.target_bound",
                    "signature": long_signature,
                },
                {
                    "source_id": "fixture_library",
                    "source_type": "lean_library",
                    "path": "Library/Semantic.lean",
                    "line": 44,
                    "kind": "lemma",
                    "name": "Statistics.semantic_reduction",
                    "namespace": "Statistics",
                    "signature": "lemma semantic_reduction (x : Nat) : x = x",
                    "reference": "Source (2026), Lemma 2",
                    "declaration_source_context": {
                        "module": "Library.Semantic",
                        "module_group": "Reusable reductions",
                        "imports": ["Library.Foundation"],
                        "premise_declaration_outlines": [],
                        "dependency_context": {
                            "module_ancestry": ["Library", "Library.Semantic"],
                            "source_snapshot": {
                                "status": "BOUND_MATCH",
                                "bound": True,
                                "match": True,
                                "metadata": {
                                    "lean_toolchain": "leanprover/lean4:v4.32.0"
                                },
                            },
                        },
                    },
                },
            ],
        },
        {
            "query": "support definition",
            "query_role": "support_dependency",
            "query_fingerprint": "d" * 64,
            "source_scope_ids": ["fixture_library"],
            "hits": [
                {
                    "source_id": "fixture_library",
                    "source_type": "lean_library",
                    "path": "Library/Foundation.lean",
                    "line": 12,
                    "kind": "def",
                    "name": "Foundation.supportObject",
                    "namespace": "Foundation",
                    "signature": "def supportObject : Type := Nat",
                    "declaration_source_context": {
                        "module": "Library.Foundation",
                        "module_group": "Foundations",
                        "imports": [],
                        "premise_declaration_outlines": [],
                        "dependency_context": {
                            "module_ancestry": ["Library", "Library.Foundation"]
                        },
                    },
                    "candidate_proof_body": "by exact forbiddenBody",
                }
            ],
        },
    ]

    compact = compact_formal_source_grounding_hits_for_prompt(groups)
    encoded = json.dumps(compact, separators=(",", ":"), ensure_ascii=False)
    target = compact[0]["hits"][0]
    context = target["declaration_source_context"]

    assert len(encoded) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS
    assert len(compact) == 3
    assert [group["query_role"] for group in compact] == [
        "initial_formalization_context",
        "semantic_target",
        "support_dependency",
    ]
    assert [group["hits"][0]["name"] for group in compact] == [
        "Library.target_bound",
        "Statistics.semantic_reduction",
        "Foundation.supportObject",
    ]
    assert target["name"] == "Library.target_bound"
    assert target["source_type"] == "lean_library"
    assert target["line"] == 101
    assert target["namespace"] == "Library"
    assert "reusable local concentration lemma" in target[
        "declaration_doc"
    ]
    assert "section_summary" not in target
    assert "Source Book Full Title" in target["reference_aliases"][0]
    assert context["module"] == "Library.Target"
    assert "module_summary" not in context
    assert "module_group" not in context
    assert "module_group_summary" not in context
    assert "local_naming_examples" not in context
    assert context["module_ancestry"] == ["Library", "Library.Target"]
    assert context["source_snapshot"]["status"] == "BOUND_MATCH"
    assert context["source_snapshot"]["metadata"]["source_git_commit"] == "b" * 40
    assert target["active_project_reuse_status"] == (
        "REQUIRES_IMPORT_VISIBILITY_AND_SIGNATURE_REVALIDATION"
    )
    assert "Library.KeyReduction" in context["premise_names"]
    assert {
        row["dependency_scope"]
        for row in context["premise_declaration_outlines"]
    } == {"statement", "proof"}
    assert "large_candidate" not in encoded
    assert "hiddenProof" not in encoded
    assert "forbiddenBody" not in encoded
    assert compact[1]["hits"][0]["declaration_source_context"]["module"] == (
        "Library.Semantic"
    )
    assert compact[1]["hits"][0]["namespace"] == "Statistics"


def test_source_scoped_prompt_keeps_two_ranked_signatures_without_library_prose() -> None:
    common_context = {
        "module": "Library.Target",
        "module_summary": "Broad repeated module prose that belongs in retrieval only.",
        "module_group": "Application layer",
        "module_group_summary": "Broad README taxonomy.",
        "imports": ["Library.Foundation"],
        "local_naming_examples": [
            {"kind": "lemma", "name": "Library.nearbyHelper"}
        ],
        "premise_declaration_outlines": [
            {
                "dependency_scope": "proof",
                "name": "Library.directPremise",
                "signature": "lemma directPremise : True",
            }
        ],
        "dependency_context": {
            "module_ancestry": ["Library", "Library.Target"],
            "direct_module_imports": ["Library.Foundation"],
            "module_import_visibility_enforced": True,
        },
    }
    hits = [
        {
            "source_id": "fixture_library",
            "source_type": "lean_library",
            "path": f"Library/Candidate{index}.lean",
            "line": index,
            "kind": "theorem",
            "name": name,
            "signature": f"theorem {name.rsplit('.', 1)[-1]} : True",
            "declaration_doc": "A bounded source-authored intent description.",
            "section_summary": "Section prose omitted from the prover packet.",
            "candidate_proof_body": "by exact hiddenProof",
            "declaration_source_context": common_context,
        }
        for index, name in enumerate(
            (
                "Library.bestCandidate",
                "Library.secondCandidate",
                "Library.thirdCandidate",
            ),
            start=1,
        )
    ]

    compact = compact_formal_source_grounding_hits_for_prompt(
        [
            {
                "query_role": "initial_formalization_context",
                "query_fingerprint": "s" * 64,
                "source_scope_ids": ["fixture_library"],
                "hits": hits,
            }
        ]
    )
    encoded = json.dumps(compact, separators=(",", ":"), ensure_ascii=False)

    assert [row["name"] for row in compact[0]["hits"]] == [
        "Library.bestCandidate",
        "Library.secondCandidate",
    ]
    assert all("signature" in row for row in compact[0]["hits"])
    assert compact[0]["source_scope_ids"] == ["fixture_library"]
    assert "thirdCandidate" not in encoded
    assert "hiddenProof" not in encoded
    assert "Section prose" not in encoded
    assert "Broad repeated module prose" not in encoded
    assert "nearbyHelper" not in encoded
    assert len(encoded) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS


def test_formal_source_repair_prompt_keeps_signatures_not_library_prose() -> None:
    hit = {
        "source_id": "lean_stat_learning_theory",
        "source_type": "lean_library",
        "path": "SLT/LeastSquares/MasterErrorBound.lean",
        "line": 88,
        "kind": "theorem",
        "name": "LeastSquares.master_error_bound",
        "namespace": "LeastSquares",
        "signature": (
            "theorem master_error_bound (h : LocalizedCondition betaHat) : "
            "excessRisk betaHat <= rate"
        ),
        "declaration_doc": "Long mathematical explanation for initial authoring.",
        "section_summary": "Localized least-squares application layer.",
        "reference_aliases": ["Book theorem and page metadata"],
        "declaration_source_context": {
            "module": "SLT.LeastSquares.MasterErrorBound",
            "module_group": "Least-squares applications",
            "module_summary": "Long module design prose.",
            "module_group_summary": "Long library taxonomy prose.",
            "imports": ["SLT.LeastSquares.Localization"],
            "local_naming_examples": [
                {
                    "kind": "lemma",
                    "name": "LeastSquares.localized_reduction",
                }
            ],
            "premise_declaration_outlines": [
                {
                    "dependency_scope": "proof",
                    "name": "LeastSquares.localized_reduction",
                    "signature": (
                        "lemma localized_reduction : "
                        "LocalizedCondition betaHat"
                    ),
                }
            ],
            "dependency_context": {
                "module_ancestry": ["SLT", "SLT.LeastSquares"],
                "direct_module_imports": [
                    "SLT.LeastSquares.Localization"
                ],
                "module_import_visibility_enforced": True,
                "source_snapshot": {
                    "status": "BOUND_MATCH",
                    "bound": True,
                    "match": True,
                    "metadata": {
                        "source_git_commit": "a" * 40,
                        "lean_toolchain": "leanprover/lean4:v4.32.0",
                        "mathlib_revision": "b" * 40,
                    },
                },
            },
        },
    }
    initial = compact_formal_source_grounding_hits_for_prompt(
        [
            {
                "query_role": "initial_formalization_context",
                "query_fingerprint": "i" * 64,
                "hits": [hit],
            }
        ]
    )
    repair = compact_formal_source_grounding_hits_for_prompt(
        [
            {
                "query_role": "live_proof_state_or_diagnostic",
                "query_fingerprint": "r" * 64,
                "hits": [hit],
            }
        ]
    )

    initial_hit = initial[0]["hits"][0]
    repair_hit = repair[0]["hits"][0]
    repair_context = repair_hit["declaration_source_context"]
    assert "declaration_doc" in initial_hit
    assert "declaration_doc" not in repair_hit
    assert "section_summary" not in repair_hit
    assert "reference_aliases" not in repair_hit
    assert repair_hit["name"] == "LeastSquares.master_error_bound"
    assert "excessRisk betaHat" in repair_hit["signature"]
    assert repair_context["module"] == (
        "SLT.LeastSquares.MasterErrorBound"
    )
    assert repair_context["imports"] == [
        "SLT.LeastSquares.Localization"
    ]
    assert repair_context["direct_module_imports"] == [
        "SLT.LeastSquares.Localization"
    ]
    assert repair_context["premise_declaration_outlines"][0]["name"] == (
        "LeastSquares.localized_reduction"
    )
    assert "LocalizedCondition betaHat" in repair_context[
        "premise_declaration_outlines"
    ][0]["signature"]
    assert repair_context["module_import_visibility_enforced"] is True
    assert repair_context["source_snapshot"]["metadata"] == {
        "lean_toolchain": "leanprover/lean4:v4.32.0",
        "mathlib_revision": "b" * 40,
    }
    assert "module_group" not in repair_context
    assert "module_summary" not in repair_context
    assert "module_group_summary" not in repair_context
    assert "local_naming_examples" not in repair_context
    assert "module_ancestry" not in repair_context
    assert len(json.dumps(repair, sort_keys=True)) < len(
        json.dumps(initial, sort_keys=True)
    )


def test_formal_source_prompt_projection_has_a_hard_pathological_input_cap() -> None:
    huge = "x" * 100_000
    groups = [
        {
            "query": huge,
            "query_role": "pathological_fixture",
            "query_fingerprint": str(index) * 64,
            "source_scope_ids": [huge, huge, huge],
            "hits": [
                {
                    "source_id": huge,
                    "source_type": huge,
                    "path": huge,
                    "line": index + 1,
                    "kind": "theorem",
                    "name": huge,
                    "namespace": huge,
                    "signature": huge,
                    "declaration_doc": huge,
                    "section_summary": huge,
                    "reference_aliases": [huge],
                    "candidate_proof_body": huge,
                    "declaration_source_context": {
                        "module": huge,
                        "module_summary": huge,
                        "module_group": huge,
                        "module_group_summary": huge,
                        "imports": [huge] * 10,
                        "local_naming_examples": [
                            {"kind": "lemma", "name": huge}
                        ]
                        * 10,
                        "premise_declaration_outlines": [
                            {
                                "dependency_scope": "proof",
                                "name": huge,
                                "signature": huge,
                            }
                        ]
                        * 10,
                        "dependency_context": {
                            "module_ancestry": [huge] * 10,
                            "direct_module_imports": [huge] * 10,
                            "source_snapshot": {
                                "status": "BOUND_MATCH",
                                "bound": True,
                                "match": True,
                                "metadata": {
                                    "source_git_commit": huge,
                                    "source_git_tree": huge,
                                    "lean_toolchain": huge,
                                    "mathlib_revision": huge,
                                },
                            },
                        },
                    },
                }
            ],
        }
        for index in range(3)
    ]

    compact = compact_formal_source_grounding_hits_for_prompt(groups)
    encoded = json.dumps(compact, separators=(",", ":"), ensure_ascii=False)

    assert len(encoded) <= FORMAL_SOURCE_GROUNDING_PROMPT_MAX_CHARS
    assert compact
    assert "candidate_proof_body" not in encoded
