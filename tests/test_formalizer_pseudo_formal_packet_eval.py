from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.formalizer_pseudo_formal_packet_eval import (
    FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE,
    run_formalizer_pseudo_formal_packet_eval,
)
from ai_statistician.pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMALIZATION_PROMOTION_GATE,
    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
)


def _write_static_formalizer_response(path: Path) -> None:
    response = {
        "formal_targets": [
            {
                "id": "source_theorem_gap",
                "informal_source": "Source theorem coverage step needs semantic grounding.",
                "lean_statement_sketch": "",
                "expected_status": "FORMAL_GAP",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "blocked_source_theorem",
                    "source_theorem_goal_id": "theorem:coverage",
                },
            }
        ],
        "lemma_dependency_plan": [
            {
                "from": "pf_block",
                "to": "source theorem semantic-definition lane",
                "role": "route exact semantic definition before Lean replay",
                "risk": "coverage event definition is missing",
            }
        ],
        "retrieval_queries": [
            {
                "query": "rank threshold coverage event semantic definition Lean",
                "target_library": "LeanRAG",
                "purpose": "ground PF residual in exact source definitions",
            }
        ],
        "proof_search_plan": {
            "preferred_tools": ["local_lean"],
            "kernel_check_plan": ["only after PF residuals are grounded"],
            "known_blockers": ["coverage_event exact definition missing"],
        },
        "proof_bank_obligation_requests": [],
        "source_to_bridge_premise_derivation_candidates": [],
        "source_to_bridge_premise_derivation_candidate_requests": [],
        "pseudo_formal_proof_packets": [
            {
                "schema_version": 1,
                "packet_id": "pseudo_formal_packet:coverage_rank_threshold",
                "theorem_id": "theorem:coverage",
                "source_artifact_id": (
                    "theory:formalizer_pseudo_formal_packet_eval"
                ),
                "pseudo_formal_method_contract_id": (
                    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
                ),
                "pseudo_formal_pipeline_stages": [
                    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE
                ],
                "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
                "kernel_verified": False,
                "source_theorem_kernel_verified": False,
                "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
                "proof_evidence_boundary": (
                    "Pseudo-formalization rows are not theorem proof evidence; "
                    "source theorem proof requires target-prover kernel replay."
                ),
                "blocks": [
                    {
                        "block_id": "b_semantic",
                        "block_type": "claim",
                        "block_depth": 1,
                        "dependency_scope": "earlier_block_statement_only",
                        "premises": [
                            "source proof invokes rank-threshold coverage event"
                        ],
                        "conclusion": (
                            "the coverage event depends on the exact "
                            "rank-threshold semantic definition"
                        ),
                        "proof_text": (
                            "The informal step identifies coverage with a rank "
                            "threshold event, so Formalizer must request the exact "
                            "source definition before Lean replay."
                        ),
                        "dependency_ids": [],
                        "scope_parent_id": "",
                        "inherited_scope": [],
                        "source_anchors": [
                            {
                                "kind": "proof_body",
                                "id": "proof_body:rank_threshold_step",
                                "excerpt": "rank-threshold coverage event",
                            }
                        ],
                        "semantic_primitive_requirements": ["coverage_event"],
                        "lean_feasibility": "needs_semantic_definition",
                        "faithfulness_status": "faithful",
                        "faithfulness_repair": {
                            "status": "not_required",
                            "attempts": 0,
                            "flagged_discrepancies": [],
                        },
                        "block_verification": {
                            "verdict": "unknown",
                            "reason": "exact coverage_event definition is pending",
                        },
                        "kernel_verified": False,
                    }
                ],
            }
        ],
        "gap_taxonomy": [
            {
                "gap": "exact coverage event semantic definition",
                "kind": "semantic_alignment",
                "next_owner": "FormalizerProofEngineer",
            }
        ],
        "critic_findings": [
            {"critic": "pf_eval", "finding": "PF/BV packet is routing only"}
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "route PF residual block",
                "acceptance_gate": "target-prover kernel replay required",
            }
        ],
    }
    path.write_text(json.dumps(response), encoding="utf-8")


def test_formalizer_pseudo_formal_packet_eval_static_fixture_routes_rows(
    tmp_path: Path,
) -> None:
    response_file = tmp_path / "formalizer_response.json"
    _write_static_formalizer_response(response_file)

    manifest = run_formalizer_pseudo_formal_packet_eval(
        out_dir=tmp_path / "out",
        provider_name="static",
        static_response_file=response_file,
    )

    assert manifest["artifact_kind"] == "FormalizerPseudoFormalPacketEvalManifest"
    assert manifest["result_status"] == "OK"
    assert manifest["live_generator"] is False
    assert manifest["static_or_fixture_only"] is True
    assert manifest["capability_evidence_ok"] is False
    assert manifest["fixture_plumbing_ok"] is True
    assert manifest["capability_evidence_requirements"]["live_generator"] is False
    assert all(manifest["fixture_plumbing_requirements"].values())
    assert manifest["n_pseudo_formal_packets"] == 1
    assert manifest["n_pseudo_formal_routable_work_order_rows"] >= 3
    assert "source_theorem_exact_semantic_definition" in (
        manifest["pseudo_formal_routable_target_lanes"]
    )
    assert "source_to_bridge" in manifest["pseudo_formal_routable_target_lanes"]
    assert "pseudo_formal_exact_semantic_definition_request" in (
        manifest["pseudo_formal_routable_row_kinds"]
    )
    assert "pseudo_formal_independent_block_verification_request" in (
        manifest["pseudo_formal_routable_row_kinds"]
    )
    assert manifest["raw_model_output_written"] is False
    assert manifest["proof_evidence_status"] == (
        FORMALIZER_PSEUDO_FORMAL_PACKET_EVAL_NOT_PROOF_EVIDENCE
    )
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["full_frontier_theorem_proved"] is False
    assert "not theorem proof evidence" in manifest["boundary"]
    assert Path(manifest["artifacts"]["manifest_json"]).exists()
    assert Path(manifest["artifacts"]["result_json"]).exists()


def test_formalizer_pseudo_formal_packet_eval_cli_fixture_gate(
    tmp_path: Path,
) -> None:
    response_file = tmp_path / "formalizer_response.json"
    _write_static_formalizer_response(response_file)

    base_args = [
        "formalizer-pseudo-formal-packet-eval",
        "--provider",
        "static",
        "--static-response-file",
        str(response_file),
        "--env-file",
        str(tmp_path / "missing.env"),
    ]

    assert main([*base_args, "--out", str(tmp_path / "strict")]) == 1
    assert (
        main(
            [
                *base_args,
                "--out",
                str(tmp_path / "fixture_ok"),
                "--allow-fixture-success",
            ]
        )
        == 0
    )
