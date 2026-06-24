from __future__ import annotations

from ai_statistician.formal_source_hybrid import FormalSourceSemanticHybridRetriever
from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceRetriever,
)
from ai_statistician.formal_source_retrieval_benchmark import (
    FormalSourceRetrievalBenchmarkCase,
    run_formal_source_retrieval_benchmark,
)


def _fixture_declarations() -> list[FormalDeclaration]:
    return [
        FormalDeclaration(
            source_id="fixture_lean",
            source_type="lean4",
            path="Fixture/Permutation.lean",
            line=7,
            kind="theorem",
            name="PermutationRankUniformity",
            namespace="Fixture",
            signature=(
                "theorem PermutationRankUniformity : exchangeable "
                "permutation ranks are uniform"
            ),
            binder_count=2,
            premise_heads=("Exchangeable",),
            conclusion_head="UniformRank",
            major_symbols=("Permutation", "UniformRank", "Exchangeable"),
            imports=("Fixture.Probability",),
        ),
        FormalDeclaration(
            source_id="fixture_lean",
            source_type="lean4",
            path="Fixture/Arithmetic.lean",
            line=3,
            kind="lemma",
            name="NatAddCommFixture",
            namespace="Fixture",
            signature="lemma NatAddCommFixture : a + b = b + a",
            conclusion_head="Eq",
            major_symbols=("Nat", "Add", "Eq"),
        ),
    ]


def test_semantic_rerank_recovers_typo_query_without_base_overlap() -> None:
    declarations = _fixture_declarations()
    base = FormalSourceRetriever(declarations)
    query = "permutaton uniformty exchangabl"

    assert base.search(query, k=3) == []

    retriever = FormalSourceSemanticHybridRetriever(
        declarations,
        base,
        semantic_weight=8.0,
    )
    hits = retriever.search(query, k=1)

    assert hits
    assert hits[0].declaration.name == "PermutationRankUniformity"
    assert "local_char_ngram_semantic" in hits[0].matched_terms
    assert retriever.semantic_rerank_enabled is True
    assert retriever.semantic_provider_id == "local_char_ngram"


def test_semantic_rerank_is_reported_in_retrieval_benchmark(tmp_path) -> None:
    declarations = _fixture_declarations()
    retriever = FormalSourceSemanticHybridRetriever(
        declarations,
        FormalSourceRetriever(declarations),
        semantic_weight=8.0,
    )
    case = FormalSourceRetrievalBenchmarkCase(
        query_id="typo_permutation_uniformity",
        query="permutaton uniformty exchangabl",
        expected_name_fragments=("PermutationRankUniformity",),
        expected_source_ids=("fixture_lean",),
        rationale="semantic rerank should recover typo/paraphrase declaration queries",
    )

    payload = run_formal_source_retrieval_benchmark(
        tmp_path,
        retriever=retriever,
        cases=(case,),
        k=1,
    )

    assert payload["all_ok"] is True
    assert payload["semantic_rerank_enabled"] is True
    assert payload["semantic_provider_id"] == "local_char_ngram"
    assert payload["semantic_candidate_multiplier"] == 8
    assert payload["semantic_weight"] == 8.0
