from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.proof_bank_action_export import export_proof_bank_actions


def test_proof_bank_action_export_source_aware_reranks_same_priority_actions(
    tmp_path: Path,
) -> None:
    expansion_dir = tmp_path / "proof_bank_expansion"
    action_dir = tmp_path / "proof_bank_actions"
    expansion_dir.mkdir()
    (expansion_dir / "proof_bank_expansion_manifest.json").write_text(
        json.dumps({"all_ok": True, "n_candidates": 2}),
        encoding="utf-8",
    )
    proposals = [
        {
            "proposal_id": "lemma_proposal:wip",
            "primitive": "wip_reuse",
            "source_gap_ids": ["gap:wip"],
            "source_task_ids": ["task:wip"],
            "action_class": "compose_existing_bridge_chain",
            "priority_score": 100,
            "bridge_readiness": "retrieval_only",
            "expected_premises": ["WIP.sorryCandidate"],
            "bridge_candidate_obligations": [],
            "candidate_declarations": ["WIP.sorryCandidate"],
            "blocked_reasons": [],
            "proof_evidence_boundary": (
                "Proposal metadata is not Lean proof evidence; verify with AXLE/local Lean."
            ),
            "ok": True,
        },
        {
            "proposal_id": "lemma_proposal:trusted",
            "primitive": "trusted_reuse",
            "source_gap_ids": ["gap:trusted"],
            "source_task_ids": ["task:trusted"],
            "action_class": "compose_existing_bridge_chain",
            "priority_score": 100,
            "bridge_readiness": "verified_bridge_chain",
            "expected_premises": ["trusted_verified_bridge"],
            "bridge_candidate_obligations": ["trusted_verified_bridge"],
            "candidate_declarations": ["StatInference.local_verified_candidate"],
            "blocked_reasons": [],
            "proof_evidence_boundary": (
                "Proposal metadata is not Lean proof evidence; verify with AXLE/local Lean."
            ),
            "ok": True,
        },
    ]
    (expansion_dir / "lemma_proposals.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in proposals),
        encoding="utf-8",
    )

    payload = export_proof_bank_actions(expansion_dir, action_dir)

    assert payload["all_ok"]
    assert payload["source_aware_rerank_policy"]["policy_id"] == (
        "proof_bank_action_source_aware_rerank_policy:1"
    )
    assert payload["n_source_aware_rerank_preferred_actions"] == 1
    assert payload["n_source_aware_rerank_penalized_actions"] == 1
    assert payload["by_source_aware_rerank_signal"][
        "preferred_ranked_proof_bank_bridge_obligations"
    ] == 1
    assert payload["by_source_aware_rerank_signal"][
        "preferred_local_importable_declaration_candidate"
    ] == 1
    assert payload["by_source_aware_rerank_signal"][
        "penalized_sorry_admit_axiom_candidate"
    ] == 1
    assert payload["by_source_aware_rerank_signal"][
        "penalized_wip_or_placeholder_candidate"
    ] == 1
    assert payload["actions"][0]["primitive"] == "trusted_reuse"
    assert payload["actions"][1]["primitive"] == "wip_reuse"
    scores = payload["source_aware_rerank_score_by_action_id"]
    assert scores["proof_bank_action:lemma_proposal:trusted"] == 75
    assert scores["proof_bank_action:lemma_proposal:wip"] == -90
    assert (
        action_dir / "proof_bank_action_manifest.json"
    ).exists()
    assert "Source-aware preferred actions" in (
        action_dir / "proof_bank_actions.md"
    ).read_text(encoding="utf-8")
