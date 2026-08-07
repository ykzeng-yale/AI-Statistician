from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from ai_statistician.formal_source_hybrid import (
    FormalSourceDependencyHybridRetriever,
)
from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
    FormalSourceRetriever,
)
from ai_statistician.formal_source_prompt_context import (
    compact_formal_source_grounding_hits_for_prompt,
)
from ai_statistician.formal_source_scoped_corpus import (
    LeanJsonlScopedPremiseRetriever,
)
from ai_statistician.lean_agent_providers import (
    CompositeFormalSourceRetriever,
)
from ai_statistician.research_agent_runtime import (
    _proofengineer_formal_source_grounding_hit_groups,
    _proofengineer_formal_source_scope_ids,
)


def _write_corpus(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "path": "SLT/Main.lean",
                "imports": [
                    "SLT/Defs.lean",
                    ".lake/packages/mathlib/Mathlib/MeasureTheory/Integral/Bochner/Basic.lean",
                    ".lake/packages/lean4/src/lean/Init.lean",
                ],
                "premises": [
                    {
                        "full_name": "SLT.target_result",
                        "kind": "commanddeclaration",
                        "code": (
                            "theorem target_result (h : True) : True := by\n"
                            "  have dead : True := by trivial\n"
                            "  exact h\n"
                        ),
                    },
                    {
                        "full_name": "MeasureTheory.helper_integral_mono",
                        "kind": "commanddeclaration",
                        "code": (
                            "lemma helper_integral_mono "
                            "(h : True) : True := by exact h"
                        ),
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _provider(path: Path) -> LeanJsonlScopedPremiseRetriever:
    return LeanJsonlScopedPremiseRetriever(
        path,
        source_id="fixture_premise_corpus",
        anchor_source_ids=("lean_stat_learning_theory",),
        dataset_id="fixture/dataset",
        dataset_revision="fixture-revision",
        toolchain="lean-fixture",
        mathlib_revision="mathlib-fixture",
    )


def test_scoped_corpus_loads_signatures_without_proof_bodies(
    tmp_path: Path,
) -> None:
    provider = _provider(_write_corpus(tmp_path / "corpus.jsonl"))

    assert provider.is_healthy()
    assert provider.metadata.n_files == 1
    assert provider.metadata.n_declarations == 2
    target = next(
        row
        for row in provider.declarations
        if row.name == "SLT.target_result"
    )
    assert target.signature == (
        "theorem target_result (h : True) : True"
    )
    assert ":= by" not in target.signature
    assert "dead" not in target.signature
    assert target.imports == (
        "SLT.Defs",
        "Mathlib.MeasureTheory.Integral.Bochner.Basic",
        "Init",
    )
    assert provider.health_report()["prompt_content_policy"] == (
        "declaration_signatures_only_proof_bodies_removed_at_load"
    )


def test_hybrid_descriptor_exposes_graph_and_scoped_corpus_health(
    tmp_path: Path,
) -> None:
    scoped = _provider(_write_corpus(tmp_path / "corpus.jsonl"))
    declaration = FormalDeclaration(
        source_id="lean_stat_learning_theory",
        source_type="lean_library",
        path="SLT/Main.lean",
        line=1,
        kind="theorem",
        name="SLT.target_result",
        namespace="SLT",
        signature="theorem target_result (h : True) : True",
    )

    class DependencyProvider:
        db_path = tmp_path / "ai4slt.sqlite"
        source_ids = ("lean_stat_learning_theory", "ai4slt")
        auto_discovered = True

        @staticmethod
        def health_report():
            return {"all_ok": True, "source_snapshot_status": "BOUND_MATCH"}

        @staticmethod
        def search(_query: str, *, k: int = 10):
            del k
            return []

        @staticmethod
        def dependency_context(*_args, **_kwargs):
            return None

    retriever = FormalSourceDependencyHybridRetriever(
        [declaration],
        FormalSourceRetriever([declaration]),
        DependencyProvider(),
        scoped_premise_retrievers=(scoped,),
    )

    descriptor = retriever.descriptor()

    assert descriptor["declarations_by_source_id"] == {
        "lean_stat_learning_theory": 1
    }
    graph = descriptor["lean_rag_dependency_graph"]
    assert graph["enabled"] is True
    assert graph["source_ids"] == (
        "lean_stat_learning_theory",
        "ai4slt",
    )
    assert graph["provider_count"] == 1
    assert "paths" not in graph
    assert graph["health"]["source_snapshot_status"] == "BOUND_MATCH"
    corpora = descriptor["source_scoped_premise_corpora"]
    assert corpora["enabled"] is True
    assert corpora["source_ids"] == ("fixture_premise_corpus",)
    assert corpora["anchor_source_ids"] == (
        "lean_stat_learning_theory",
    )
    assert corpora["health"][0]["all_ok"] is True
    assert "corpus_path" not in corpora["health"][0]
    assert descriptor["proof_evidence_status"] == (
        "FORMAL_SOURCE_RETRIEVAL_TOPOLOGY_NOT_PROOF_EVIDENCE"
    )


def test_scoped_corpus_fails_closed_on_checksum_mismatch(
    tmp_path: Path,
) -> None:
    path = _write_corpus(tmp_path / "corpus.jsonl")
    provider = LeanJsonlScopedPremiseRetriever(
        path,
        source_id="fixture_premise_corpus",
        anchor_source_ids=("lean_stat_learning_theory",),
        dataset_id="fixture/dataset",
        dataset_revision="fixture-revision",
        toolchain="lean-fixture",
        mathlib_revision="mathlib-fixture",
        expected_sha256="0" * 64,
    )

    assert not provider.is_healthy()
    assert not provider.health_report()["checksum_ok"]
    assert provider.search("target result", k=3) == []


def test_scoped_corpus_activates_only_for_matching_source_scope(
    tmp_path: Path,
) -> None:
    provider = _provider(_write_corpus(tmp_path / "corpus.jsonl"))
    anchor = FormalDeclaration(
        source_id="lean_stat_learning_theory",
        source_type="lean_library",
        path="SLT/Main.lean",
        line=20,
        kind="theorem",
        name="SLT.target_result",
        namespace="SLT",
        signature="theorem target_result (h : True) : True",
    )
    unrelated = FormalDeclaration(
        source_id="unrelated_corpus",
        source_type="lean_library",
        path="Other/Main.lean",
        line=20,
        kind="theorem",
        name="Other.target_result",
        namespace="Other",
        signature="theorem target_result (h : True) : True",
    )
    current_helper = FormalDeclaration(
        source_id="mathlib_measure_theory",
        source_type="mathlib",
        path="Integral/Bochner/Basic.lean",
        line=100,
        kind="lemma",
        name="MeasureTheory.helper_integral_mono",
        namespace="MeasureTheory",
        signature="lemma helper_integral_mono (h : True) : True",
    )

    class Base:
        def __init__(self, top: FormalDeclaration) -> None:
            self.top = top

        def search(self, query: str, *, k: int):
            return [
                FormalSourceHit(
                    self.top,
                    20.0,
                    ("helper", "target"),
                )
            ]

    scoped = FormalSourceDependencyHybridRetriever(
        [anchor, unrelated, current_helper],
        Base(anchor),
        None,
        scoped_premise_retrievers=(provider,),
    )
    scoped_hits = scoped.search(
        "target result helper integral monotone",
        k=3,
    )
    helper_hit = next(
        hit
        for hit in scoped_hits
        if hit.declaration.name
        == "MeasureTheory.helper_integral_mono"
    )
    assert helper_hit.declaration is current_helper
    assert "source_scoped_premise_corpus" in helper_hit.matched_terms

    unscoped = FormalSourceDependencyHybridRetriever(
        [anchor, unrelated, current_helper],
        Base(unrelated),
        None,
        scoped_premise_retrievers=(provider,),
    )
    assert all(
        "source_scoped_premise_corpus" not in hit.matched_terms
        for hit in unscoped.search(
            "target result helper integral monotone",
            k=3,
        )
    )

    forced_hits = unscoped.search_with_source_scope(
        "target result helper integral monotone",
        source_scope_ids=("lean_stat_learning_theory",),
        k=3,
    )
    assert any(
        hit.declaration.name == "MeasureTheory.helper_integral_mono"
        and "source_scoped_premise_corpus" in hit.matched_terms
        for hit in forced_hits
    )


def test_proofengineer_recovers_source_scope_from_target_provenance() -> None:
    calls: list[tuple[str, tuple[str, ...], int]] = []

    class Retriever:
        scoped_premise_corpus_anchor_source_ids = (
            "lean_stat_learning_theory",
        )

        def search_with_source_scope(
            self,
            query: str,
            *,
            source_scope_ids: tuple[str, ...],
            k: int,
        ):
            calls.append((query, source_scope_ids, k))
            return []

        def search(self, query: str, *, k: int):
            raise AssertionError("source-scoped search should be used")

    retriever = Retriever()
    context = {
        "candidate_rerun_specs": [
            {
                "source_theorem_target_provenance": {
                    "source_id": "lean_stat_learning_theory",
                }
            }
        ],
        "unrelated": {"source_id": "other_corpus"},
    }
    scope_ids = _proofengineer_formal_source_scope_ids(
        context,
    )

    assert scope_ids == ("lean_stat_learning_theory",)
    groups = _proofengineer_formal_source_grounding_hit_groups(
        retriever,
        query_seeds=("integral monotonicity",),
        source_scope_ids=scope_ids,
    )
    assert groups[0]["source_scope_ids"] == [
        "lean_stat_learning_theory"
    ]
    assert calls == [
        (
            "integral monotonicity",
            ("lean_stat_learning_theory",),
            2,
        )
    ]


def test_composite_runtime_preserves_three_book_dependency_context() -> None:
    source_id = "lean_stat_learning_theory"
    vershynin = FormalDeclaration(
        source_id=source_id,
        source_type="lean_library",
        path="CoveringNumber.lean",
        line=610,
        kind="theorem",
        name="coveringNumber_euclideanBall_le",
        namespace="",
        signature=(
            "theorem coveringNumber_euclideanBall_le "
            "(hR : 0 <= R) (heps : 0 < eps) : coveringNumber eps s <= n"
        ),
        reference="Vershynin (2018), Corollary 4.2.13",
        module_group="Metric entropy",
    )
    boucheron = FormalDeclaration(
        source_id=source_id,
        source_type="lean_library",
        path="GaussianLipConcen.lean",
        line=1301,
        kind="theorem",
        name="GaussianLipConcen.gaussian_lipschitz_concentration",
        namespace="GaussianLipConcen",
        signature=(
            "theorem gaussian_lipschitz_concentration "
            "(hf : LipschitzWith L f) : tailProbability f <= bound"
        ),
        reference="Boucheron et al. (2013), Theorem 5.6",
        module_group="Gaussian concentration",
    )
    wainwright = FormalDeclaration(
        source_id=source_id,
        source_type="lean_library",
        path="LeastSquares/MasterErrorBound.lean",
        line=900,
        kind="theorem",
        name="LeastSquares.master_error_bound",
        namespace="LeastSquares",
        signature=(
            "theorem master_error_bound "
            "(hCI : satisfiesCriticalInequality model radius) : "
            "predictionError estimator <= rate"
        ),
        imports=("SLT.CoveringNumber", "SLT.GaussianLipConcen"),
        reference="Wainwright (2019), Theorem 13.5",
        module_group="Least squares",
    )
    scoped_calls: list[tuple[str, tuple[str, ...], int]] = []

    class StructuredProvider:
        name = "structured_ai4slt_fixture"
        declarations = (vershynin, boucheron, wainwright)

        def search(self, query: str, *, k: int = 10):
            del query
            return [
                FormalSourceHit(wainwright, 12.0, ("master", "error", "bound"))
            ][:k]

        def search_with_source_scope(
            self,
            query: str,
            *,
            source_scope_ids: tuple[str, ...],
            k: int = 10,
        ):
            scoped_calls.append((query, source_scope_ids, k))
            return self.search(query, k=k)

        def dependency_context(
            self,
            declaration_name: str,
            *,
            limit: int,
            source_id: str,
            path: str,
        ):
            del limit
            assert declaration_name == wainwright.name
            assert source_id == "lean_stat_learning_theory"
            assert path == wainwright.path
            return SimpleNamespace(
                fan_in=3,
                fan_out=2,
                uses=(vershynin.name, boucheron.name),
                used_by=(),
                statement_uses=(vershynin.name,),
                proof_uses=(boucheron.name,),
                source_id=source_id,
                module="SLT.LeastSquares.MasterErrorBound",
                direct_module_imports=(
                    "SLT.CoveringNumber",
                    "SLT.GaussianLipConcen",
                ),
                module_dependency_route=(
                    (1, "SLT.CoveringNumber"),
                    (1, "SLT.GaussianLipConcen"),
                ),
                module_import_visibility_enforced=True,
                dependency_resolution_policy=(
                    "qualified_name_then_unique_path_bound_short_name"
                ),
            )

    class UnscopedDistractorProvider:
        name = "unscoped_proof_bank_fixture"

        def search(self, _query: str, *, k: int = 10):
            distractor = FormalDeclaration(
                source_id="proof_bank",
                source_type="proof_bank",
                path="ProofBank/Distractor.lean",
                line=1,
                kind="theorem",
                name="ProofBank.master_error_bound_distractor",
                namespace="ProofBank",
                signature="theorem master_error_bound_distractor : True",
            )
            return [FormalSourceHit(distractor, 1000.0, ("master", "error"))][
                :k
            ]

    retriever = CompositeFormalSourceRetriever(
        (StructuredProvider(), UnscopedDistractorProvider())
    )

    groups = _proofengineer_formal_source_grounding_hit_groups(
        retriever,
        query_seeds=("localized least squares master error bound",),
        source_scope_ids=(source_id,),
        k=2,
        max_groups=1,
    )

    assert scoped_calls
    assert groups[0]["source_scope_semantics"] == (
        "main_retrieval_allowlist_with_anchor_scoped_support_corpora"
    )
    hit = groups[0]["hits"][0]
    assert hit["name"] == "LeastSquares.master_error_bound"
    assert all(
        row["source_id"] == source_id for row in groups[0]["hits"]
    )
    context = hit["declaration_source_context"]
    assert context["dependency_context"]["module_import_visibility_enforced"]
    outlines = context["premise_declaration_outlines"]
    assert [row["dependency_scope"] for row in outlines] == [
        "statement",
        "proof",
    ]
    assert {
        hit["reference"],
        *(row["reference"] for row in outlines),
    } == {
        "Vershynin (2018), Corollary 4.2.13",
        "Boucheron et al. (2013), Theorem 5.6",
        "Wainwright (2019), Theorem 13.5",
    }
    assert context["source_architecture_route"] == {
        "target_module": "SLT.LeastSquares.MasterErrorBound",
        "target_layer": "Least squares",
        "upstream_layers": [
            {
                "depth": 1,
                "layer": "Gaussian concentration",
                "modules": ["SLT.GaussianLipConcen"],
            },
            {
                "depth": 1,
                "layer": "Metric entropy",
                "modules": ["SLT.CoveringNumber"],
            },
        ],
        "evidence_status": (
            "SOURCE_IMPORT_GRAPH_AND_SOURCE_AUTHORED_LAYER_CONTEXT_NOT_PROOF_EVIDENCE"
        ),
    }
    initial_groups = [dict(groups[0], query_role="initial_formalization_context")]
    compact = compact_formal_source_grounding_hits_for_prompt(initial_groups)
    compact_context = compact[0]["hits"][0]["declaration_source_context"]
    assert "source_architecture_route" not in compact_context
    assert [
        row["module"]
        for row in compact_context["premise_declaration_outlines"]
    ] == ["SLT.CoveringNumber", "SLT.GaussianLipConcen"]
    assert "module_ancestry" not in compact_context
    assert "direct_module_imports" not in compact_context
    repair = compact_formal_source_grounding_hits_for_prompt(groups)
    repair_context = repair[0]["hits"][0]["declaration_source_context"]
    assert "source_architecture_route" not in repair_context
    distractor_diagnostic = retriever.runtime_diagnostics()[1]
    assert distractor_diagnostic["n_raw_hits"] == 1
    assert distractor_diagnostic["n_hits"] == 0
    assert distractor_diagnostic["n_out_of_scope_hits_dropped"] == 1


def test_runtime_filters_source_scope_when_retriever_has_no_scoped_api() -> None:
    allowed = FormalDeclaration(
        source_id="source_library",
        source_type="lean_library",
        path="Library/Target.lean",
        line=1,
        kind="theorem",
        name="Library.target",
        namespace="Library",
        signature="theorem target : True",
    )
    distractor = FormalDeclaration(
        source_id="proof_bank",
        source_type="proof_bank",
        path="ProofBank/Distractor.lean",
        line=1,
        kind="theorem",
        name="ProofBank.target",
        namespace="ProofBank",
        signature="theorem target : True",
    )

    class UnscopedRetriever:
        def search(self, _query: str, *, k: int = 10):
            return [
                FormalSourceHit(distractor, 100.0, ("target",)),
                FormalSourceHit(allowed, 1.0, ("target",)),
            ][:k]

    groups = _proofengineer_formal_source_grounding_hit_groups(
        UnscopedRetriever(),
        query_seeds=("target",),
        source_scope_ids=("source_library",),
        k=2,
        max_groups=1,
    )

    assert [row["source_id"] for row in groups[0]["hits"]] == [
        "source_library"
    ]
    assert groups[0]["source_scope_enforcement"] == (
        "runtime_unscoped_fallback_filtered_by_source_allowlist"
    )
    assert groups[0]["n_out_of_scope_hits_dropped"] == 1
