from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
    FormalSourceRetriever,
    FormalSourceRoot,
    FormalSourceSqliteIndex,
    _cache_covers_configured_roots,
    build_formal_source_index,
    diversify_formal_source_hits,
    search_formal_sources,
)
from ai_statistician.formal_source_hybrid import FormalSourceHybridRetriever
from ai_statistician.formal_source_retrieval_benchmark import (
    audit_formal_source_reference_crosswalk,
)
from ai_statistician.formalizer_llm import (
    build_formalizer_prompt,
    formalizer_proof_construction_strategy_contract,
)
from ai_statistician.research_agent_runtime import _formal_source_hit_to_json
from ai_statistician.research_lab import load_open_research_questions


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
    assert [
        row["name"]
        for row in context["premise_declaration_outlines"]
    ] == [
        "LeastSquares.bad_event_probability_bound",
    ]
    assert [row["name"] for row in context["nearby_declaration_outlines"]] == [
        "LeastSquares.goodEvent",
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
    assert "smallest diagnostic" in contract["repair_cycle"]
    assert "qualified name/namespace/module/signature/import/reference" in contract[
        "specification"
    ]
    assert "direct premise outlines first" in contract["specification"]
    assert "bounded prior fallback" in contract["specification"]
    assert "minimal explicit support-dependency plan" in contract["specification"]
    assert "[] for a direct proof" in contract["specification"]
    assert "no unchanged retry" in contract["repair_cycle"]
    assert "Independently recheck target fidelity" in contract[
        "persistent_failure_route"
    ]
    assert "counterexamples" in contract["persistent_failure_route"]
    assert "quantifiers" in contract["persistent_failure_route"]
    assert "exact active-project artifact" in contract["post_compile_hygiene"]
    assert "stable semantic Lean names" in contract["library_design"]
    assert "source metadata" in contract["library_design"]
    assert "exact compatible imported declaration" in contract["reuse_policy"]
    assert "revalidate every selected declaration" in contract["reuse_policy"]

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
    assert "no unchanged retry" in prompt
    assert "fix the smallest diagnostic" in prompt
    assert "stable semantic Lean names" in prompt
    assert "exact compatible imported declaration" in prompt
