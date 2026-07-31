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
    build_formal_source_index,
    diversify_formal_source_hits,
    search_formal_sources,
)
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

    sqlite_index = FormalSourceSqliteIndex.build(
        declarations,
        tmp_path / "formal_source.sqlite",
    )
    assert sqlite_index.is_healthy()
    sqlite_hits = sqlite_index.search("Boucheron Corollary 13.2", k=3)
    assert sqlite_hits[0].declaration.name == "SLT.dudley"
    assert sqlite_hits[0].declaration.reference == dudley.reference

    crosswalk = audit_formal_source_reference_crosswalk(
        FormalSourceRetriever(declarations),
        k=3,
    )
    assert crosswalk["n_reference_bound_declarations"] == 1
    assert crosswalk["n_reference_queries"] == 1
    assert crosswalk["all_ok"] is True
    assert crosswalk["rows"][0]["hit_rank"] == 1
    assert crosswalk["rows"][0]["reference"] == dudley.reference


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

        def dependency_context(self, declaration_name: str, *, limit: int):
            assert declaration_name == "LeastSquares.master_error_bound"
            assert limit == 6
            return SimpleNamespace(
                fan_in=8,
                fan_out=3,
                uses=("LeastSquares.bad_event_probability_bound",),
                used_by=("LeastSquares.linear_minimax_rate_rank",),
            )

    retriever.dependency_retriever = DependencyProvider()
    hit = FormalSourceHit(declarations[2], 9.0, ("master", "error"))

    payload = _formal_source_hit_to_json(
        hit,
        formal_source_retriever=retriever,
    )

    context = payload["declaration_source_context"]
    assert context["module"] == "SLT.LeastSquares.MasterErrorBound"
    assert context["imports"] == [
        "SLT.LeastSquares.Localization",
        "SLT.GaussianLipConcen",
    ]
    assert [row["name"] for row in context["nearby_declaration_outlines"]] == [
        "LeastSquares.bad_event_probability_bound",
        "LeastSquares.goodEvent",
    ]
    assert context["n_same_file_declarations"] == 4
    assert context["n_prior_same_file_declarations"] == 2
    assert context["n_downstream_same_file_declarations_omitted"] == 1
    assert context["outline_selection"] == (
        "nearest_prior_same_file_declarations_by_source_line"
    )
    assert context["dependency_context"]["uses"] == [
        "LeastSquares.bad_event_probability_bound"
    ]
    assert context["dependency_context"]["used_by"] == [
        "LeastSquares.linear_minimax_rate_rank"
    ]
    assert "candidate_proof_body" not in str(context)
    assert all(
        ":= by" not in row["signature"]
        for row in context["nearby_declaration_outlines"]
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
    assert "compact declaration outlines" in contract["specification"]
    assert "prior only" in contract["specification"]
    assert "small lemma DAG" in contract["specification"]
    assert "counterexamples" in contract["persistent_failure_route"]
    assert "quantifiers" in contract["persistent_failure_route"]
    assert "exact active-project artifact" in contract["post_compile_hygiene"]

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
    assert "compact declaration outlines" in prompt
    assert "fix the smallest diagnostic" in prompt
