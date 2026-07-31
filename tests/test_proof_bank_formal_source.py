from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass

import pytest

import ai_statistician.proof_bank_formal_source as proof_bank_formal_source_module
from ai_statistician import cli
from ai_statistician.proof_bank_formal_source import (
    PROOF_BANK_FORMAL_SOURCE_BOUNDARY,
    ProofBankFormalSourceRetriever,
    build_default_formal_source_retriever,
)


def test_proof_bank_formal_source_hit_is_candidate_context_not_proof() -> None:
    retriever = ProofBankFormalSourceRetriever()

    hits = retriever.search("difference_in_means_unbiasedness", k=3)

    assert hits
    hit = hits[0]
    assert hit.declaration.name == "difference_in_means_unbiasedness"
    assert hit.declaration.kind == "proof_obligation"
    assert "theorem differenceInMeans_unbiased" in hit.declaration.signature
    assert hit.provenance["candidate_proof_body"].startswith("by\n")
    assert hit.provenance["proof_evidence_status"] == (
        "PROOF_BANK_RETRIEVAL_NOT_PROOF_EVIDENCE"
    )
    assert hit.provenance["proof_evidence_boundary"] == (
        PROOF_BANK_FORMAL_SOURCE_BOUNDARY
    )
    assert "kernel_verified" not in hit.provenance


@pytest.mark.parametrize(
    ("query", "expected_ids"),
    (
        (
            "randomized experiment fixed potential outcomes difference in means "
            "Neyman conservative design based variance bound",
            {
                "difference_in_means_unbiasedness",
                "randomization_variance_decomposition_bridge",
                "neyman_bound_conservative_of_variance_decomposition",
            },
        ),
        (
            "independent z tests sparse nonnull effects Benjamini Hochberg false "
            "discovery rate control threshold power",
            {
                "bh_threshold_grid_mono",
                "bh_threshold_fixed_point_bridge",
                "independent_null_pvalues_bridge",
            },
        ),
    ),
)
def test_proof_bank_formal_source_recovers_cross_family_assets(
    query: str,
    expected_ids: set[str],
) -> None:
    hits = ProofBankFormalSourceRetriever().search(query, k=12)

    assert expected_ids & {hit.declaration.name for hit in hits}


def test_default_formal_source_topology_fuses_proof_bank_with_other_providers() -> None:
    @dataclass
    class EmptyProvider:
        name: str

        def search(self, _query: str, *, k: int = 10):
            del k
            return []

    retriever = build_default_formal_source_retriever(
        local_retriever=EmptyProvider("local"),
        additional_providers=(EmptyProvider("external"),),
    )

    hits = retriever.search("bh_threshold_grid_mono", k=4)

    assert hits
    assert hits[0].declaration.name == "bh_threshold_grid_mono"
    support = hits[0].provenance["provider_support"]
    assert support[0]["provider"] == "ai_statistician_proof_bank_formal_source"
    proof_bank_provenance = support[0]["provenance"]
    assert proof_bank_provenance["candidate_proof_body"]
    assert proof_bank_provenance["proof_evidence_status"] == (
        "PROOF_BANK_RETRIEVAL_NOT_PROOF_EVIDENCE"
    )
    assert "kernel_verified" not in proof_bank_provenance
    descriptor = retriever.descriptor()
    assert [row["name"] for row in descriptor["providers"]] == [
        "local",
        "ai_statistician_proof_bank_formal_source",
        "external",
    ]
    assert descriptor["boundary"]


def test_default_formal_source_topology_uses_rich_local_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    @dataclass
    class LocalBackend:
        name: str = "rich_local_backend"

        def search(self, _query: str, *, k: int = 10):
            del k
            return []

        def search_with_source_scope(
            self,
            _query: str,
            *,
            source_scope_ids: tuple[str, ...],
            k: int = 10,
        ):
            del source_scope_ids, k
            return []

    local_backend = LocalBackend()
    monkeypatch.setattr(
        proof_bank_formal_source_module,
        "build_formal_source_search_backend",
        lambda: local_backend,
    )

    retriever = build_default_formal_source_retriever()

    assert retriever.providers[0] is local_backend
    assert retriever.descriptor()["source_scoped_search"]


def test_runtime_cli_uses_default_proof_bank_topology_without_external_rag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    monkeypatch.setattr(
        cli,
        "build_default_formal_source_retriever",
        lambda: sentinel,
    )

    retriever = cli._formal_source_retriever_from_runtime_args(
        Namespace(emperical_process_lean_rag_root="")
    )

    assert retriever is sentinel
