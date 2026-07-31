from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.formal_source_hybrid import (
    FormalSourceDependencyHybridRetriever,
)
from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
)
from ai_statistician.formal_source_scoped_corpus import (
    LeanJsonlScopedPremiseRetriever,
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
        unknown_identifiers=(),
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
