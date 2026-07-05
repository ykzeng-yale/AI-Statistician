from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ai_statistician.pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
    PSEUDO_FORMAL_STRUCTURAL_DECOMPOSITION_REQUEST_ROW_KIND,
    PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME,
    PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES,
    PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER,
    PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
    PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
    PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH,
    PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMALIZATION_PROMOTION_GATE,
    PSEUDO_FORMALIZATION_SCHEMA_ID,
    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
    normalize_pseudo_formal_packet,
    pseudo_formal_block_structural_quality,
    pseudo_formal_block_work_order_rows,
    pseudo_formal_packet_json_schema,
    pseudo_formal_routable_work_order_rows,
    pseudo_formal_verification_method_contract,
    pseudo_formal_work_order_row_json_schema,
    pseudo_formalizer_output_contract,
    pseudo_formalizer_prompt_contract,
    pseudo_formal_validation_issue_summary,
    validate_pseudo_formal_packet,
)
from ai_statistician.pseudo_formal_block_verifier_worker import (
    PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE,
    export_pseudo_formal_block_verifier_llm_responses,
    export_pseudo_formal_block_verifier_prompt_packets,
    export_pseudo_formal_block_verifier_response_validation,
    run_pseudo_formal_block_verifier_component_gate,
)
from ai_statistician.formalizer_llm import (
    FormalizerConfig,
    LLMFormalizerProofEngineerAgent,
    _validate_capability_eval_formalizer_lean_candidate_packet,
    _normalize_formalizer_packet,
    _validate_required_pseudo_formalization_packet,
    build_formalizer_prompt,
    validate_formalizer_packet,
)
from ai_statistician.model_backend import GeneratorRequest, GeneratorResponse
from ai_statistician.research_schema import OpenResearchQuestion


def test_pseudo_formal_packet_normalizes_and_routes_non_kernel_work_orders() -> None:
    packet = {
        "theorem_id": "split_conformal_coverage",
        "source_artifact_id": "theory_packet:split_conformal",
        "blocks": [
            {
                "block_id": "b1",
                "block_type": "lemma",
                "premises": ["exchangeability of calibration and test scores"],
                "conclusion": "the test rank is uniform over n + 1 positions",
                "proof_text": "By exchangeability, every insertion rank is equally likely.",
                "source_anchors": [
                    {
                        "kind": "theory_trace",
                        "id": "equation:rank_uniformity",
                        "excerpt": "rank uniformity step",
                    }
                ],
                "scope_parent_id": "",
                "semantic_primitive_requirements": ["rank_uniformity"],
                "lean_feasibility": "lean_now",
                "faithfulness_status": "faithful",
                "block_verification": {"verdict": "accepted", "rollout_count": 1},
            },
            {
                "block_id": "b2",
                "block_type": "claim",
                "dependency_ids": ["b1"],
                "scope_parent_id": "b1",
                "block_depth": 2,
                "inherited_scope": ["exchangeability setup from b1"],
                "premises": ["b1", "quantile threshold definition"],
                "conclusion": "coverage is at least 1 - alpha",
                "proof_text": "Combine the uniform rank bound with the conformal threshold.",
                "source_anchors": [
                    {
                        "kind": "proof_body",
                        "id": "proof:coverage_step",
                        "excerpt": "coverage lower-bound argument",
                    }
                ],
                "semantic_primitive_requirements": ["quantile_threshold"],
                "lean_feasibility": "needs_semantic_definition",
                "faithfulness_status": "needs_review",
                "block_verification": {
                    "verdict": "failed",
                    "reason": "quantile definition is not declared",
                },
            },
            {
                "block_id": "b3",
                "block_type": "definition",
                "conclusion": "identify a Mathlib declaration for finite rank order statistic",
                "proof_text": "",
                "source_anchors": [
                    {
                        "kind": "paper",
                        "id": "lei-wasserman:definition",
                        "excerpt": "order statistic threshold",
                    }
                ],
                "scope_parent_id": "",
                "lean_feasibility": "needs_rag",
                "faithfulness_status": "unchecked",
                "block_verification": {"verdict": "unknown"},
            },
        ],
    }

    normalized = normalize_pseudo_formal_packet(packet)

    assert normalized["schema_id"] == PSEUDO_FORMALIZATION_SCHEMA_ID
    assert normalized["all_ok"]
    assert normalized["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert normalized["kernel_verified"] is False
    assert normalized["source_theorem_kernel_verified"] is False
    assert normalized["promotion_gate"] == PSEUDO_FORMALIZATION_PROMOTION_GATE
    assert validate_pseudo_formal_packet(normalized) == []
    assert (
        normalized["pseudo_formal_method_contract_id"]
        == PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
    )
    assert (
        PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE
        in normalized["pseudo_formal_pipeline_stages"]
    )
    assert normalized["block_structure_contract"]["max_proof_tree_depth"] == (
        PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH
    )
    assert normalized["bv_calibration"]["strictness_threshold"] == (
        PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS
    )
    assert normalized["bv_calibration"]["aggregation_rule"] == (
        "parallel_pessimistic_aggregation"
    )
    assert normalized["blocks"][0]["block_depth"] == 1
    assert normalized["blocks"][0]["dependency_scope"] == (
        PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE
    )
    assert normalized["blocks"][1]["scope_parent_id"] == "b1"
    assert normalized["blocks"][1]["block_depth"] == 2
    assert normalized["blocks"][1]["inherited_scope"] == [
        "exchangeability setup from b1"
    ]
    assert normalized["blocks"][0]["structural_quality"]["all_ok"] is True
    assert normalized["blocks"][0]["faithfulness_repair"]["status"] == (
        "not_required"
    )
    assert normalized["blocks"][0]["block_verification"][
        "strictness_threshold"
    ] == PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS
    assert normalized["blocks"][1]["faithfulness_repair"]["status"] == (
        "needs_repair"
    )

    rows = pseudo_formal_block_work_order_rows(normalized)
    row_kinds = {row["row_kind"] for row in rows}
    assert "pseudo_formal_lean_candidate_seed" not in row_kinds
    assert "pseudo_formal_lean_candidate_seed_blocked" in row_kinds
    assert PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND in row_kinds
    assert "pseudo_formal_exact_semantic_definition_request" not in row_kinds
    assert (
        "pseudo_formal_exact_semantic_definition_request_blocked_by_faithfulness"
        in row_kinds
    )
    assert "pseudo_formal_block_verification_failure" not in row_kinds
    assert (
        "pseudo_formal_block_verification_failure_blocked_by_faithfulness"
        in row_kinds
    )
    assert "pseudo_formal_faithfulness_review" in row_kinds
    assert "pseudo_formal_formal_library_grounding_query" not in row_kinds
    assert (
        "pseudo_formal_formal_library_grounding_query_blocked_by_faithfulness"
        in row_kinds
    )
    assert "pseudo_formal_semantic_primitive_request" in row_kinds
    assert (
        "pseudo_formal_semantic_primitive_request_blocked_by_faithfulness"
        in row_kinds
    )
    exact_blocked_rows = [
        row
        for row in rows
        if row["row_kind"]
        == "pseudo_formal_exact_semantic_definition_request_blocked_by_faithfulness"
    ]
    assert exact_blocked_rows
    assert {row["target_lane"] for row in exact_blocked_rows} == {"formal_gap"}
    assert {
        row["blocked_target_lane"] for row in exact_blocked_rows
    } == {"source_theorem_exact_semantic_definition"}
    assert {row["blocked_by"] for row in exact_blocked_rows} == {
        "faithfulness_not_established"
    }
    assert {row["kernel_verified"] for row in rows} == {False}
    assert {row["proof_evidence_status"] for row in rows} == {
        PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    }
    assert {row["promotion_gate"] for row in rows} == {
        PSEUDO_FORMALIZATION_PROMOTION_GATE
    }
    assert {row["pseudo_formal_method_contract_id"] for row in rows} == {
        PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
    }
    assert {row["pseudo_formal_pipeline_stage"] for row in rows} == {
        PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE
    }
    assert {row["block_depth"] for row in rows} == {1, 2}
    assert {row["dependency_scope"] for row in rows} == {
        PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE
    }
    assert any(row["scope_parent_id"] == "b1" for row in rows)
    assert any(row["inherited_scope"] == ["exchangeability setup from b1"] for row in rows)
    b2_rows = [row for row in rows if row["source_block_id"] == "b2"]
    assert b2_rows
    assert b2_rows[0]["source_block_premises"] == [
        "b1",
        "quantile threshold definition",
    ]
    assert b2_rows[0]["source_block_proof_text"] == (
        "Combine the uniform rank bound with the conformal threshold."
    )
    assert b2_rows[0]["dependency_statement_context"] == [
        {
            "block_id": "b1",
            "block_type": "lemma",
            "conclusion": "the test rank is uniform over n + 1 positions",
            "dependency_scope": PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
        }
    ]
    assert {row["structural_quality_ok"] for row in rows} == {True}
    assert all(
        row["bv_calibration"]["strictness_threshold"]
        == PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS
        for row in rows
    )


def test_pseudo_formal_block_normalizer_accepts_llm_aliases_without_weakening_anchors() -> None:
    packet = normalize_pseudo_formal_packet(
        {
            "theorem_id": "split_conformal_coverage",
            "source_artifact_id": "theory_packet:split_conformal",
            "blocks": [
                {
                    "block_id": "rank_uniformity_block",
                    "block_type": "lemma",
                    "premises": ["scores are exchangeable"],
                    "claim": "the test rank is uniform",
                    "proof": "Exchangeability makes each labeled rank equally likely.",
                    "anchors": [
                        {
                            "kind": "theory_trace",
                            "source_id": "equation:rank_uniformity",
                            "excerpt": "rank equation",
                        }
                    ],
                    "scope_parent_id": "",
                    "block_depth": 1,
                    "dependency_scope": PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
                    "faithfulness_status": "UNVERIFIED",
                    "block_verification": {
                        "verdict": "accepted",
                        "verifier_provenance": "formalizer_proposed",
                        "rollout_count": 1,
                    },
                    "lean_feasibility": "needs_rag",
                }
            ],
        }
    )

    errors = validate_pseudo_formal_packet(packet)

    assert errors == []
    block = packet["blocks"][0]
    assert block["conclusion"] == "the test rank is uniform"
    assert block["proof_text"].startswith("Exchangeability")
    assert block["source_anchors"][0]["id"] == "equation:rank_uniformity"
    assert block["faithfulness_status"] == "unchecked"


def test_pseudo_formal_validation_issue_summary_classifies_repair_targets() -> None:
    summary = pseudo_formal_validation_issue_summary(
        [
            (
                "pseudo_formalization_required: proof-body/PF activation feedback "
                "requires at least one pseudo_formal_proof_packets entry"
            ),
            "blocks[0] missing conclusion",
            "blocks[0] missing source_anchors",
            "blocks[0] accepted block_verification must record rollout_count >= 1",
            (
                "pseudo_formalization_required: valid PF/BV packet did not produce "
                "lane-routable pseudo-formal work-order rows"
            ),
        ]
    )

    assert summary["n_validation_errors"] == 5
    assert summary["n_missing_required_packet"] == 1
    assert summary["n_missing_conclusion"] == 1
    assert summary["n_missing_source_anchors"] == 1
    assert summary["n_accepted_without_rollout_count"] == 1
    assert summary["n_no_lane_routable_work_order_rows"] == 1
    assert "missing_source_anchors" in summary["blocking_issue_kinds"]
    assert summary["proof_evidence_status"] == (
        PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    )


def test_pseudo_formal_block_normalizer_accepts_decomposition_type_aliases() -> None:
    packet = normalize_pseudo_formal_packet(
        {
            "theorem_id": "split_conformal_coverage",
            "source_artifact_id": "theory_packet:split_conformal",
            "blocks": [
                {
                    "block_id": "b_assumption",
                    "block_type": "assumption_block",
                    "assumptions": ["calibration and test scores are exchangeable"],
                    "statement_text": "the labeled scores are exchangeable",
                    "justification": "This is the source theorem assumption.",
                    "source_anchor_refs": {
                        "kind": "theory_trace",
                        "reference_id": "assumption:exchangeability",
                        "quote": "exchangeable scores",
                    },
                    "faithfulness_status": "faithful",
                    "block_verification": {"verdict": "not_run"},
                    "lean_feasibility": "pseudo_only",
                },
                {
                    "block_id": "b_rank",
                    "block_type": "theorem_step",
                    "dependencies": ["b_assumption"],
                    "conclusion_text": "the test rank is uniform",
                    "proof_step": (
                        "Condition on the multiset; exchangeability makes each "
                        "label position equally likely."
                    ),
                    "source_citations": [
                        {
                            "kind": "proof_body",
                            "anchor_id": "proof:rank-uniformity",
                            "source_excerpt": "rank uniformity step",
                        }
                    ],
                    "faithfulness_status": "FAITHFUL",
                    "block_verification": {"verdict": "accepted", "rollout_count": 1},
                    "lean_feasibility": "needs_rag",
                },
                {
                    "block_id": "b_coverage",
                    "block_type": "conclusion_block",
                    "depends_on": ["b_rank"],
                    "block_statement": "coverage is at least one minus alpha",
                    "explanation": "Combine rank uniformity with the conformal quantile.",
                    "evidence_refs": [
                        {
                            "kind": "theory_trace",
                            "trace_id": "equation:coverage",
                            "text": "coverage lower bound",
                        }
                    ],
                    "faithfulness_status": "needs-review",
                    "block_verification": {"verdict": "unknown"},
                    "lean_feasibility": "needs_semantic_definition",
                },
            ],
        }
    )

    assert validate_pseudo_formal_packet(packet) == []
    assert [block["block_type"] for block in packet["blocks"]] == [
        "fact",
        "lemma",
        "claim",
    ]
    assert packet["blocks"][0]["conclusion"] == "the labeled scores are exchangeable"
    assert packet["blocks"][1]["dependency_ids"] == ["b_assumption"]
    assert packet["blocks"][1]["source_anchors"][0]["id"] == "proof:rank-uniformity"
    assert packet["blocks"][2]["source_anchors"][0]["excerpt"] == (
        "coverage lower bound"
    )
    assert packet["blocks"][2]["faithfulness_status"] == "needs_review"


def test_pseudo_formal_block_normalizer_accepts_live_role_aliases() -> None:
    packet = normalize_pseudo_formal_packet(
        {
            "theorem_id": "split_conformal_coverage",
            "source_artifact_id": "theory_packet:split_conformal",
            "blocks": [
                {
                    "block_id": "b_hyp",
                    "block_type": "hypothesis_introduction",
                    "conclusion": "exchangeability hypothesis is in scope",
                    "proof_text": "This is copied from the theory trace.",
                    "source_anchors": [
                        {"kind": "theory_trace", "id": "assumption:exchangeability"}
                    ],
                },
                {
                    "block_id": "b_app",
                    "block_type": "lemma_application",
                    "conclusion": "rank uniformity follows from exchangeability",
                    "proof_text": "Apply the rank-uniformity argument.",
                    "source_anchors": [
                        {"kind": "proof_body", "id": "proof:rank-uniformity"}
                    ],
                },
                {
                    "block_id": "b_def",
                    "block_type": "definition_instantiation",
                    "conclusion": "C_n is the source quantile threshold",
                    "proof_text": "Instantiate the source definition of the threshold.",
                    "source_anchors": [
                        {"kind": "theory_trace", "id": "definition:C_n"}
                    ],
                },
                {
                    "block_id": "b_conclusion",
                    "block_type": "conclusion_step",
                    "conclusion": "coverage is at least one minus alpha",
                    "proof_text": "Combine the previous blocks.",
                    "source_anchors": [
                        {"kind": "theory_trace", "id": "equation:coverage"}
                    ],
                },
                {
                    "block_id": "b_residual",
                    "block_type": "residual",
                    "conclusion": "the remaining blocked import is a library gap",
                    "proof_text": "The rejected import must be grounded elsewhere.",
                    "source_anchors": [
                        {
                            "kind": "theory_trace",
                            "id": "blocked_import:Mathlib.Data.Int.Order",
                        }
                    ],
                },
            ],
        }
    )

    assert validate_pseudo_formal_packet(packet) == []
    assert [block["block_type"] for block in packet["blocks"]] == [
        "fact",
        "lemma",
        "definition",
        "claim",
        "claim",
    ]


def test_pseudo_formal_block_aliases_still_require_real_source_anchors() -> None:
    packet = normalize_pseudo_formal_packet(
        {
            "theorem_id": "split_conformal_coverage",
            "source_artifact_id": "theory_packet:split_conformal",
            "blocks": [
                {
                    "block_id": "rank_uniformity_block",
                    "block_type": "lemma",
                    "premises": ["scores are exchangeable"],
                    "claim": "the test rank is uniform",
                    "proof": "Exchangeability makes each labeled rank equally likely.",
                    "anchors": [],
                    "scope_parent_id": "",
                    "block_depth": 1,
                    "dependency_scope": PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
                    "faithfulness_status": "UNVERIFIED",
                    "block_verification": {"verdict": "accepted"},
                    "lean_feasibility": "needs_rag",
                }
            ],
        }
    )

    errors = validate_pseudo_formal_packet(packet)

    assert "blocks[0] missing source_anchors" in errors


def test_pseudo_formal_block_empty_anchor_mapping_is_not_real_anchor() -> None:
    packet = normalize_pseudo_formal_packet(
        {
            "theorem_id": "split_conformal_coverage",
            "source_artifact_id": "theory_packet:split_conformal",
            "blocks": [
                {
                    "block_id": "rank_uniformity_block",
                    "block_type": "lemma",
                    "premises": ["scores are exchangeable"],
                    "claim": "the test rank is uniform",
                    "argument": "Exchangeability makes each labeled rank equally likely.",
                    "anchors": {},
                    "scope_parent_id": "",
                    "block_depth": 1,
                    "dependency_scope": PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
                    "faithfulness_status": "UNVERIFIED",
                    "block_verification": {"verdict": "accepted"},
                    "lean_feasibility": "needs_rag",
                }
            ],
        }
    )

    errors = validate_pseudo_formal_packet(packet)

    assert packet["blocks"][0]["source_anchors"] == []
    assert "blocks[0] missing source_anchors" in errors


def test_pseudo_formal_packet_rejects_kernel_claims_and_bad_dag() -> None:
    raw = {
        "schema_version": 1,
        "proof_evidence_status": "CLAIMED_PROOF",
        "kernel_verified": True,
        "source_theorem_kernel_verified": True,
        "promotion_gate": "accept_pseudo_formal_verifier",
        "proof_evidence_boundary": "verified",
        "blocks": [
            {
                "block_id": "b1",
                "block_type": "claim",
                "conclusion": "first block",
                "proof_text": "depends on the future",
                "dependency_ids": ["b2"],
                "scope_parent_id": "b2",
                "source_anchors": [],
                "kernel_verified": True,
                "lean_feasibility": "unknown",
                "block_verification": {"verdict": "not_run"},
            },
            {
                "block_id": "b2",
                "block_type": "claim",
                "conclusion": "second block",
                "proof_text": "self dependency",
                "dependency_ids": ["b2"],
                "scope_parent_id": "b2",
                "source_anchors": [{"kind": "paper", "id": "source"}],
                "lean_feasibility": "unknown",
                "block_verification": {"verdict": "not_run"},
            },
        ],
    }

    errors = validate_pseudo_formal_packet(raw)

    assert "proof_evidence_status must be pseudo-formal non-proof" in errors
    assert "pseudo_formal_method_contract_id must match PF+BV contract" in errors
    assert "kernel_verified must be false for pseudo-formal packets" in errors
    assert (
        "source_theorem_kernel_verified must be false for pseudo-formal packets"
        in errors
    )
    assert "promotion_gate must require target-prover kernel replay" in errors
    assert "proof_evidence_boundary must say not theorem proof evidence" in errors
    assert "blocks[0] missing source_anchors" in errors
    assert "blocks[0] kernel_verified must be false" in errors
    assert "blocks[0] dependency_id must reference an earlier block: b2" in errors
    assert "blocks[0] scope_parent_id must reference an earlier block: b2" in errors
    assert "blocks[1] dependency_ids cannot include self" in errors
    assert "blocks[1] scope_parent_id cannot be self" in errors

    normalized = normalize_pseudo_formal_packet(raw)

    assert normalized["kernel_verified"] is False
    assert normalized["source_theorem_kernel_verified"] is False
    assert normalized["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert normalized["promotion_gate"] == PSEUDO_FORMALIZATION_PROMOTION_GATE
    assert normalized["boundary_corrections"] == [
        "kernel_verified_forced_false",
        "source_theorem_kernel_verified_forced_false",
        "proof_evidence_status_forced_non_proof",
        "promotion_gate_forced_kernel_replay",
    ]
    normalized_errors = validate_pseudo_formal_packet(normalized)
    assert "kernel_verified must be false for pseudo-formal packets" not in (
        normalized_errors
    )
    assert "proof_evidence_status must be pseudo-formal non-proof" not in (
        normalized_errors
    )
    assert "blocks[0] missing source_anchors" in normalized_errors


def test_pseudo_formal_packet_allows_direct_child_forward_dependency_only_without_cycle() -> None:
    packet = {
        "schema_version": 1,
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "promotion_gate": PSEUDO_FORMALIZATION_PROMOTION_GATE,
        "pseudo_formal_method_contract_id": (
            PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
        ),
        "blocks": [
            {
                "block_id": "b_top",
                "block_type": "proposition",
                "block_depth": 1,
                "premises": ["exchangeability setup"],
                "conclusion": "coverage is at least 1 - alpha",
                "proof_text": "Invoke the child rank lemma and then conclude.",
                "dependency_ids": ["b_rank_child"],
                "dependency_scope": "direct_child_or_earlier_statement_only",
                "scope_parent_id": "",
                "source_anchors": [
                    {"kind": "proof_body", "id": "proof:coverage"}
                ],
                "faithfulness_status": "unchecked",
                "faithfulness_repair": {
                    "status": "not_required",
                    "attempts": 0,
                    "flagged_discrepancies": [],
                },
                "lean_feasibility": "unknown",
                "block_verification": {"verdict": "not_run"},
            },
            {
                "block_id": "b_rank_child",
                "block_type": "lemma",
                "block_depth": 2,
                "premises": ["exchangeability setup"],
                "conclusion": "the rank is uniform",
                "proof_text": "Use exchangeability.",
                "dependency_ids": [],
                "dependency_scope": PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
                "scope_parent_id": "b_top",
                "inherited_scope": ["exchangeability setup"],
                "source_anchors": [
                    {"kind": "theory_trace", "id": "equation:rank_uniformity"}
                ],
                "faithfulness_status": "unchecked",
                "faithfulness_repair": {
                    "status": "not_required",
                    "attempts": 0,
                    "flagged_discrepancies": [],
                },
                "lean_feasibility": "unknown",
                "block_verification": {"verdict": "not_run"},
            },
        ],
    }

    assert validate_pseudo_formal_packet(packet) == []

    default_scope_packet = dict(packet)
    default_scope_packet["blocks"] = [dict(row) for row in packet["blocks"]]
    default_scope_packet["blocks"][0]["dependency_scope"] = (
        PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE
    )
    assert (
        "blocks[0] dependency_id must reference an earlier block: b_rank_child"
        in validate_pseudo_formal_packet(default_scope_packet)
    )

    cyclic_packet = dict(packet)
    cyclic_packet["blocks"] = [dict(row) for row in packet["blocks"]]
    cyclic_packet["blocks"][1]["dependency_ids"] = ["b_top"]
    assert (
        "dependency graph must be acyclic; cycle includes: b_rank_child, b_top"
        in validate_pseudo_formal_packet(cyclic_packet)
    )


def test_pseudo_formal_structural_quality_gates_oversized_blocks() -> None:
    packet = {
        "theorem_id": "split_conformal_coverage",
        "source_artifact_id": "theory_packet:split_conformal",
        "blocks": [
            {
                "block_id": "b1",
                "block_type": "lemma",
                "premises": [f"premise {index}" for index in range(13)],
                "conclusion": "rank is uniform",
                "proof_text": "Exchangeability argument. " * 320,
                "source_anchors": [
                    {"kind": "theory_trace", "id": "equation:rank_uniformity"}
                ],
                "lean_feasibility": "lean_now",
                "faithfulness_status": "faithful",
                "block_verification": {"verdict": "accepted", "rollout_count": 1},
            }
        ],
    }

    normalized = normalize_pseudo_formal_packet(packet)
    quality = pseudo_formal_block_structural_quality(normalized["blocks"][0])

    assert quality["all_ok"] is False
    assert "too_many_premises:13>12" in quality["issues"]
    assert any(issue.startswith("proof_text_too_long:") for issue in quality["issues"])
    assert normalized["blocks"][0]["structural_quality"] == quality
    assert normalized["all_ok"] is True
    assert validate_pseudo_formal_packet(normalized) == []

    rows = pseudo_formal_block_work_order_rows(normalized)
    assert [row["row_kind"] for row in rows] == [
        PSEUDO_FORMAL_STRUCTURAL_DECOMPOSITION_REQUEST_ROW_KIND
    ]
    assert rows[0]["target_lane"] == "formal_gap"
    assert rows[0]["requested_owner_subsystem"] == "Formalizer/ProofEngineer"
    assert rows[0]["structural_quality_ok"] is False
    assert "too_many_premises:13>12" in rows[0]["structural_quality_issues"]
    assert [
        row["row_kind"] for row in pseudo_formal_routable_work_order_rows(rows)
    ] == [PSEUDO_FORMAL_STRUCTURAL_DECOMPOSITION_REQUEST_ROW_KIND]


def test_pseudo_formal_packet_gates_lean_seed_on_faithful_bv_acceptance() -> None:
    packet = {
        "theorem_id": "split_conformal_coverage",
        "source_artifact_id": "theory_packet:split_conformal",
        "blocks": [
            {
                "block_id": "b1",
                "block_type": "lemma",
                "conclusion": "rank is uniform",
                "proof_text": "Exchangeability implies rank uniformity.",
                "source_anchors": [
                    {"kind": "theory_trace", "id": "equation:rank_uniformity"}
                ],
                "lean_feasibility": "lean_now",
                "faithfulness_status": "faithful",
                "block_verification": {"verdict": "accepted"},
            }
        ],
    }
    normalized = normalize_pseudo_formal_packet(packet)

    assert normalized["blocks"][0]["block_verification"]["verdict"] == "unknown"
    assert "accepted_without_rollout_count_downgraded_to_unknown" in normalized[
        "blocks"
    ][0]["block_verification"]["normalizer_corrections"]
    assert validate_pseudo_formal_packet(normalized) == []
    row_kinds = {
        row["row_kind"] for row in pseudo_formal_block_work_order_rows(normalized)
    }
    assert "pseudo_formal_lean_candidate_seed" not in row_kinds
    assert "pseudo_formal_lean_candidate_seed_blocked" in row_kinds
    routable_rows = pseudo_formal_routable_work_order_rows(
        pseudo_formal_block_work_order_rows(normalized)
    )
    assert [row["row_kind"] for row in routable_rows] == [
        PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND
    ]
    assert routable_rows[0]["independent_block_verification_required"] is True

    normalized["blocks"][0]["block_verification"]["verdict"] = "accepted"
    normalized["blocks"][0]["block_verification"]["rollout_count"] = 1
    normalized["blocks"][0]["faithfulness_status"] = "unchecked"
    row_kinds = {
        row["row_kind"] for row in pseudo_formal_block_work_order_rows(normalized)
    }
    assert "pseudo_formal_lean_candidate_seed" not in row_kinds
    assert "pseudo_formal_lean_candidate_seed_blocked" in row_kinds
    routable_rows = pseudo_formal_routable_work_order_rows(
        pseudo_formal_block_work_order_rows(normalized)
    )
    assert [row["row_kind"] for row in routable_rows] == [
        "pseudo_formal_faithfulness_review"
    ]

    normalized["blocks"][0]["faithfulness_status"] = "faithful"
    assert validate_pseudo_formal_packet(normalized) == []
    row_kinds = {
        row["row_kind"] for row in pseudo_formal_block_work_order_rows(normalized)
    }
    assert "pseudo_formal_lean_candidate_seed" not in row_kinds
    assert "pseudo_formal_lean_candidate_seed_blocked" in row_kinds
    final_routable_rows = pseudo_formal_routable_work_order_rows(
        pseudo_formal_block_work_order_rows(normalized)
    )
    assert {row["row_kind"] for row in final_routable_rows} == {
        PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND
    }

    normalized["blocks"][0]["block_verification"]["verifier_provenance"] = (
        "independent_block_verifier"
    )
    normalized["blocks"][0]["block_verification"]["independent_verifier"] = True
    independent_row_kinds = {
        row["row_kind"] for row in pseudo_formal_block_work_order_rows(normalized)
    }
    assert "pseudo_formal_lean_candidate_seed" in independent_row_kinds
    assert "pseudo_formal_lean_candidate_seed_blocked" not in independent_row_kinds


def test_pseudo_formal_normalizes_llm_block_verdict_aliases_to_safe_values() -> None:
    packet = normalize_pseudo_formal_packet(
        {
            "theorem_id": "split_conformal_coverage",
            "source_artifact_id": "theory_packet:split_conformal",
            "blocks": [
                {
                    "block_id": "needs_review_alias",
                    "block_type": "lemma",
                    "conclusion": "rank block still needs review",
                    "proof_text": "A model used needs_review as a BV verdict.",
                    "source_anchors": [
                        {"kind": "theory_trace", "id": "rank_block"}
                    ],
                    "faithfulness_status": "faithful",
                    "block_verification": {"verdict": "needs_review"},
                },
                {
                    "block_id": "pending_alias",
                    "block_type": "lemma",
                    "conclusion": "coverage block awaits verifier",
                    "proof_text": "A model used pending as a BV verdict.",
                    "source_anchors": [
                        {"kind": "theory_trace", "id": "coverage_block"}
                    ],
                    "faithfulness_status": "faithful",
                    "block_verification": {"verdict": "pending"},
                },
            ],
        }
    )

    assert [row["block_verification"]["verdict"] for row in packet["blocks"]] == [
        "unknown",
        "not_run",
    ]
    assert "verdict_normalized:needs_review->unknown" in packet["blocks"][0][
        "block_verification"
    ]["normalizer_corrections"]
    assert "verdict_normalized:pending->not_run" in packet["blocks"][1][
        "block_verification"
    ]["normalizer_corrections"]
    assert validate_pseudo_formal_packet(packet) == []


def test_pseudo_formal_block_verification_failure_requires_independent_bv() -> None:
    packet = normalize_pseudo_formal_packet(
        {
            "theorem_id": "split_conformal_coverage",
            "source_artifact_id": "theory_packet:split_conformal",
            "blocks": [
                {
                    "block_id": "b_bad",
                    "block_type": "lemma",
                    "conclusion": "rank is uniform",
                    "proof_text": "A flawed exchangeability argument.",
                    "source_anchors": [
                        {"kind": "theory_trace", "id": "equation:rank_uniformity"}
                    ],
                    "lean_feasibility": "unknown",
                    "faithfulness_status": "faithful",
                    "block_verification": {
                        "verdict": "failed",
                        "reason": "missing exchangeability premise",
                        "rollout_count": 1,
                    },
                }
            ],
        }
    )

    rows = pseudo_formal_block_work_order_rows(packet)
    row_kinds = {row["row_kind"] for row in rows}

    assert "pseudo_formal_block_verification_failure" not in row_kinds
    assert (
        "pseudo_formal_block_verification_failure_blocked_by_independent_bv"
        in row_kinds
    )
    assert {
        row["row_kind"] for row in pseudo_formal_routable_work_order_rows(rows)
    } == {PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND}

    packet["blocks"][0]["block_verification"]["verifier_provenance"] = (
        "independent_block_verifier"
    )
    packet["blocks"][0]["block_verification"]["independent_verifier"] = True
    independent_row_kinds = {
        row["row_kind"] for row in pseudo_formal_block_work_order_rows(packet)
    }
    assert "pseudo_formal_block_verification_failure" in independent_row_kinds
    assert (
        "pseudo_formal_block_verification_failure_blocked_by_independent_bv"
        not in independent_row_kinds
    )


def test_pseudo_formal_block_verifier_prompt_packets_preserve_bounded_context(
    tmp_path,
) -> None:
    learning_path = tmp_path / "runtime_learning_rows.jsonl"
    request_row = _independent_bv_request_learning_row()
    learning_path.write_text(json.dumps(request_row) + "\n", encoding="utf-8")

    manifest = export_pseudo_formal_block_verifier_prompt_packets(
        [learning_path],
        tmp_path / "prompt_packets",
    )

    assert manifest["all_ok"] is True
    assert manifest["n_request_rows"] == 1
    assert manifest["n_ok_prompt_packets"] == 1
    packet = manifest["packets"][0]
    assert packet["artifact_kind"] == "PseudoFormalBlockVerifierPromptPacket"
    assert packet["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:rank_uniform:independent-bv"
    )
    assert packet["dependency_statement_context"][0]["source_block_id"] == (
        "b_exchangeability"
    )
    assert packet["source_block_premises"] == ["scores are exchangeable"]
    assert "every rank position is equally likely" in packet["source_block_proof_text"]
    assert "hidden dependency proof bodies" in packet["system_prompt"]
    assert packet["prompt_packet_id"] in packet["user_prompt"]
    assert packet["source_pseudo_formal_work_order_id"] in packet["user_prompt"]
    assert packet["proof_evidence_status"] == (
        PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE
    )
    assert (
        tmp_path
        / "prompt_packets"
        / "pseudo_formal_block_verifier_prompt_packets_manifest.json"
    ).exists()


def test_pseudo_formal_block_verifier_llm_responses_use_generator_backend(
    tmp_path,
) -> None:
    learning_path = tmp_path / "runtime_learning_rows.jsonl"
    request_row = _independent_bv_request_learning_row()
    learning_path.write_text(json.dumps(request_row) + "\n", encoding="utf-8")
    prompt_manifest = export_pseudo_formal_block_verifier_prompt_packets(
        [learning_path],
        tmp_path / "prompt_packets",
    )
    packet = prompt_manifest["packets"][0]
    provider = _SequenceStaticGeneratorBackend(
        [
            {
                "prompt_packet_id": packet["prompt_packet_id"],
                "source_pseudo_formal_work_order_id": packet[
                    "source_pseudo_formal_work_order_id"
                ],
                "source_block_id": packet["source_block_id"],
                "block_verification": {
                    "verdict": "accepted",
                    "reason": (
                        "The local rank-uniformity step follows from exchangeability."
                    ),
                    "verifier_provenance": "independent_block_verifier",
                    "independent_verifier": True,
                    "strictness_threshold": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
                    "aggregation_rule": "parallel_pessimistic_aggregation",
                    "rollout_count": 1,
                },
            }
        ]
    )

    llm_manifest = export_pseudo_formal_block_verifier_llm_responses(
        tmp_path
        / "prompt_packets"
        / "pseudo_formal_block_verifier_prompt_packets_manifest.json",
        tmp_path / "llm_responses",
        provider=provider,
        provider_name="static",
        model="static",
        model_tier="sonnet",
        max_packets=1,
    )

    assert llm_manifest["all_ok"] is True
    assert llm_manifest["n_ok_responses"] == 1
    assert llm_manifest["provider_name"] == "static"
    response = llm_manifest["responses"][0]
    assert response["prompt_packet_id"] == packet["prompt_packet_id"]
    assert response["block_verification"]["verdict"] == "accepted"
    assert response["proof_evidence_status"] == (
        PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE
    )
    assert (
        tmp_path / "llm_responses" / "pseudo_formal_block_verifier_responses.jsonl"
    ).exists()


def test_pseudo_formal_block_verifier_component_gate_runs_full_static_chain(
    tmp_path,
) -> None:
    learning_path = tmp_path / "runtime_learning_rows.jsonl"
    request_row = _independent_bv_request_learning_row()
    learning_path.write_text(json.dumps(request_row) + "\n", encoding="utf-8")
    prompt_manifest = export_pseudo_formal_block_verifier_prompt_packets(
        [learning_path],
        tmp_path / "preview_prompt_packets",
    )
    packet = prompt_manifest["packets"][0]
    provider = _SequenceStaticGeneratorBackend(
        [
            {
                "prompt_packet_id": packet["prompt_packet_id"],
                "source_pseudo_formal_work_order_id": packet[
                    "source_pseudo_formal_work_order_id"
                ],
                "source_block_id": packet["source_block_id"],
                "block_verification": {
                    "verdict": "accepted",
                    "reason": (
                        "The local rank-uniformity step follows from exchangeability."
                    ),
                    "verifier_provenance": "independent_block_verifier",
                    "independent_verifier": True,
                    "strictness_threshold": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
                    "aggregation_rule": "parallel_pessimistic_aggregation",
                    "rollout_count": 1,
                },
            }
        ]
    )

    manifest = run_pseudo_formal_block_verifier_component_gate(
        [learning_path],
        tmp_path / "component_gate",
        provider=provider,
        provider_name="static",
        model="static",
        max_packets=1,
    )

    assert manifest["artifact_kind"] == "PseudoFormalBlockVerifierComponentGateManifest"
    assert manifest["all_ok"] is True
    assert manifest["fixture_plumbing_ok"] is True
    assert manifest["capability_evidence_ok"] is False
    assert manifest["static_or_fixture_only"] is True
    assert manifest["n_prompt_packets"] == 1
    assert manifest["n_valid_responses"] == 1
    assert manifest["n_runtime_learning_rows"] == 1
    assert manifest["runtime_learning_rows"][0]["block_verification"]["verdict"] == (
        "accepted"
    )
    assert manifest["runtime_learning_rows"][0]["proof_evidence_status"] == (
        PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    )
    assert Path(manifest["artifacts"]["runtime_learning_rows_jsonl"]).exists()
    assert (
        tmp_path
        / "component_gate"
        / "pseudo_formal_block_verifier_component_gate_manifest.json"
    ).exists()


def test_pseudo_formal_block_verifier_component_gate_cli_requires_live_or_opt_in_fixture(
    tmp_path,
) -> None:
    from ai_statistician.cli import build_parser, main

    assert "pseudo-formal-block-verifier-component-gate" in build_parser().format_help()
    learning_path = tmp_path / "runtime_learning_rows.jsonl"
    request_row = _independent_bv_request_learning_row()
    learning_path.write_text(json.dumps(request_row) + "\n", encoding="utf-8")
    prompt_manifest = export_pseudo_formal_block_verifier_prompt_packets(
        [learning_path],
        tmp_path / "preview_prompt_packets",
    )
    packet = prompt_manifest["packets"][0]
    static_response_path = tmp_path / "static_response.json"
    static_response_path.write_text(
        json.dumps(
            {
                "prompt_packet_id": packet["prompt_packet_id"],
                "source_pseudo_formal_work_order_id": packet[
                    "source_pseudo_formal_work_order_id"
                ],
                "source_block_id": packet["source_block_id"],
                "block_verification": {
                    "verdict": "accepted",
                    "reason": (
                        "The block cites exactly the exchangeability premise "
                        "needed for the rank-uniformity conclusion."
                    ),
                    "verifier_provenance": "independent_block_verifier",
                    "independent_verifier": True,
                    "strictness_threshold": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
                    "aggregation_rule": "parallel_pessimistic_aggregation",
                    "rollout_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    base_args = [
        "pseudo-formal-block-verifier-component-gate",
        "--runtime-learning-jsonl",
        str(learning_path),
        "--provider",
        "static",
        "--static-response-file",
        str(static_response_path),
        "--model",
        "static",
        "--max-packets",
        "1",
        "--out",
        str(tmp_path / "cli_component_gate"),
    ]

    assert main(base_args) == 1
    manifest_path = (
        tmp_path
        / "cli_component_gate"
        / "pseudo_formal_block_verifier_component_gate_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["all_ok"] is True
    assert manifest["fixture_plumbing_ok"] is True
    assert manifest["capability_evidence_ok"] is False
    assert manifest["static_or_fixture_only"] is True
    assert manifest["proof_evidence_status"] == (
        "PSEUDO_FORMAL_BLOCK_VERIFIER_COMPONENT_GATE_NOT_PROOF_EVIDENCE"
    )

    fixture_args = [*base_args[:-1], str(tmp_path / "cli_component_gate_fixture_ok")]
    fixture_args.append("--allow-fixture-success")
    assert main(fixture_args) == 0


def test_pseudo_formal_block_verifier_response_validation_exports_learning_rows(
    tmp_path,
) -> None:
    learning_path = tmp_path / "runtime_learning_rows.jsonl"
    request_row = _independent_bv_request_learning_row()
    learning_path.write_text(json.dumps(request_row) + "\n", encoding="utf-8")
    prompt_manifest = export_pseudo_formal_block_verifier_prompt_packets(
        [learning_path],
        tmp_path / "prompt_packets",
    )
    packet = prompt_manifest["packets"][0]
    response_path = tmp_path / "responses.jsonl"
    response = {
        "prompt_packet_id": packet["prompt_packet_id"],
        "source_pseudo_formal_work_order_id": packet[
            "source_pseudo_formal_work_order_id"
        ],
        "source_block_id": packet["source_block_id"],
        "block_verification": {
            "verdict": "accepted",
            "reason": "The local rank-uniformity step follows from exchangeability.",
            "verifier_provenance": "independent_block_verifier",
            "independent_verifier": True,
            "strictness_threshold": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
            "aggregation_rule": "parallel_pessimistic_aggregation",
            "rollout_count": 1,
        },
        "cited_dependency_statement_ids": ["b_exchangeability"],
        "issues": [],
        "proof_evidence_status": (
            PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE
        ),
    }
    response_path.write_text(json.dumps(response) + "\n", encoding="utf-8")

    validation = export_pseudo_formal_block_verifier_response_validation(
        tmp_path
        / "prompt_packets"
        / "pseudo_formal_block_verifier_prompt_packets_manifest.json",
        response_path,
        tmp_path / "response_validation",
    )

    assert validation["all_ok"] is True
    assert validation["n_runtime_learning_rows"] == 1
    row = validation["runtime_learning_rows"][0]
    assert row["learning_task"] == PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK
    assert row["row_kind"] == PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND
    assert row["independent_block_verification_status"] == "completed"
    assert row["block_verification_independent"] is True
    assert row["block_verification"]["verdict"] == "accepted"
    assert row["block_verification_verifier_provenance"] == (
        "independent_block_verifier"
    )
    assert row["dependency_statement_context"][0]["source_block_id"] == (
        "b_exchangeability"
    )
    assert row["source_block_premises"] == ["scores are exchangeable"]
    assert row["structural_quality"]["all_ok"] is True
    assert row["structural_quality_ok"] is True
    assert row["structural_quality_issues"] == []
    worker = row["pseudo_formal_block_verifier_worker"]
    assert (
        "pseudo-formal-block-verifier-component-gate"
        in worker["component_gate_command"]
    )
    assert (
        "pseudo-formal-block-verifier-prompt-packets"
        in worker["prompt_packets_command"]
    )
    assert (
        "pseudo-formal-block-verifier-llm-responses"
        in worker["llm_response_command"]
    )
    assert (
        "pseudo-formal-block-verifier-response-validation"
        in worker["response_validation_command"]
    )
    assert row["kernel_verified"] is False
    assert row["source_theorem_kernel_verified"] is False
    assert row["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert (
        tmp_path / "response_validation" / "runtime_learning_rows.jsonl"
    ).exists()


def test_pseudo_formalizer_contract_and_schema_expose_non_proof_boundary() -> None:
    contract = pseudo_formalizer_output_contract()
    method_contract = pseudo_formal_verification_method_contract()
    schema = pseudo_formal_packet_json_schema()

    assert contract["schema_id"] == PSEUDO_FORMALIZATION_SCHEMA_ID
    assert contract["verification_method_contract"]["contract_id"] == (
        PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
    )
    assert method_contract["source_basis"]["arxiv_id"] == "2605.20531"
    assert method_contract["source_basis"]["reference_repo_url"] == (
        "https://github.com/Slim205/pseudo-formalization"
    )
    assert method_contract["integration_decision"]["adopt_as"] == (
        "formalizer_proofengineer_intermediate_verifier_and_router"
    )
    assert "Lean replacement" in method_contract["integration_decision"]["do_not_adopt_as"]
    assert method_contract["graph_contract"]["dependency_graph"] == (
        "directed_acyclic_graph"
    )
    assert method_contract["graph_contract"]["scope_inheritance_graph"] == "forest"
    assert method_contract["graph_contract"]["scope_parent_field"] == "scope_parent_id"
    assert method_contract["graph_contract"]["dependency_access"] == (
        "statement_only_no_hidden_proof_body_access"
    )
    assert "kernel_verified=true" in method_contract["runtime_activation_policy"][
        "forbidden_outputs"
    ]
    assert "structured rewrite rules" in method_contract["reuse_policy"]["reuse"]
    assert "hardcoded provider/model choices" in method_contract["reuse_policy"][
        "do_not_reuse_directly"
    ]
    assert "GeneratorBackend" in method_contract["reuse_policy"]["adapter_boundary"]
    assert {
        stage["stage_id"] for stage in method_contract["pipeline_stages"]
    } >= {
        "translate_to_pseudo_formal",
        "faithfulness_check_and_repair",
        "independent_block_verification",
        "calibrate_block_reports",
        "parallel_pessimistic_aggregation",
        PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    }
    assert "pessimistic" in method_contract["parallel_aggregation_rule"]
    assert contract["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert contract["promotion_gate"] == PSEUDO_FORMALIZATION_PROMOTION_GATE
    assert "source_anchors" in contract["block_contract"]
    assert contract["block_contract"]["scope_parent_id"] == (
        "empty for a root block, otherwise one earlier block id"
    )
    assert contract["block_contract"]["dependency_scope"] == [
        "earlier_block_statement_only",
        "direct_child_or_earlier_statement_only",
    ]
    prompt_contract = pseudo_formalizer_prompt_contract()
    assert "direct child" in prompt_contract["dependency_rule"]
    assert "same-level dependencies" in prompt_contract["dependency_scope_rule"]
    assert contract["packet_calibration_contract"]["aggregation_rule"] == (
        "parallel_pessimistic_aggregation"
    )
    assert contract["work_order_routing_contract"]["learning_task"] == (
        PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK
    )
    assert contract["work_order_routing_contract"]["trigger"] == (
        PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER
    )
    assert contract["work_order_routing_contract"]["runtime_generated_queue_name"] == (
        PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME
    )
    assert set(contract["work_order_routing_contract"]["target_lanes"]) == set(
        PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES
    )
    assert schema["properties"]["kernel_verified"]["const"] is False
    assert schema["properties"]["source_theorem_kernel_verified"]["const"] is False
    assert schema["properties"]["blocks"]["items"]["properties"]["block_depth"][
        "maximum"
    ] == PSEUDO_FORMAL_MAX_PROOF_TREE_DEPTH
    assert "scope_parent_id" in schema["properties"]["blocks"]["items"]["required"]
    assert (
        schema["properties"]["blocks"]["items"]["properties"]["scope_parent_id"][
            "type"
        ]
        == "string"
    )
    assert (
        schema["properties"]["pseudo_formal_method_contract_id"]["const"]
        == PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
    )
    assert (
        schema["properties"]["proof_evidence_status"]["const"]
        == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    )
    work_order_schema = pseudo_formal_work_order_row_json_schema()
    assert set(work_order_schema["properties"]["target_lane"]["enum"]) == set(
        PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES
    )
    assert work_order_schema["properties"]["dependency_scope"]["enum"] == [
        "earlier_block_statement_only",
        "direct_child_or_earlier_statement_only",
    ]
    assert "dependency_statement_context" in work_order_schema["properties"]
    assert "source_block_premises" in work_order_schema["properties"]
    assert "source_block_proof_text" in work_order_schema["properties"]
    assert "scope_parent_id" in work_order_schema["required"]
    assert work_order_schema["properties"]["pseudo_formal_pipeline_stage"]["const"] == (
        PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE
    )


def test_formalizer_prompt_exposes_pseudo_formalization_contract() -> None:
    question = OpenResearchQuestion(
        id="split_conformal",
        title="Split conformal coverage",
        description="Prove finite sample marginal coverage.",
        tags=("formalization", "conformal"),
    )

    prompt = build_formalizer_prompt(
        question=question,
        theory_packet={
            "packet_id": "theory:split_conformal",
            "theorem_cards": [
                {
                    "id": "theorem:coverage",
                    "claim": "split conformal has coverage at least 1-alpha",
                }
            ],
        },
        simulation_manifest={"manifest_id": "simulation:test"},
        algorithm_manifest={"manifest_id": "algorithm:test"},
        registered_problem={"question_id": question.id, "problem_class": "conformal"},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary={},
        environment_feedback={
            "source_theorem_proof_body_adapter_feedback": {
                "diagnostics": [
                    {
                        "failure_classification": "source_theorem_semantic_alignment_unreviewed"
                    }
                ]
            }
        },
    )

    assert "pseudo_formalization_contract" in prompt
    assert "pseudo_formal_proof_packets" in prompt
    assert PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE in prompt
    assert "do not satisfy the Lean-candidate gate" in prompt


def test_formalizer_normalizes_pseudo_formal_packets_without_proof_promotion() -> None:
    question = OpenResearchQuestion(
        id="split_conformal",
        title="Split conformal coverage",
        description="Prove finite sample marginal coverage.",
        tags=("formalization", "conformal"),
    )
    packet = _normalize_formalizer_packet(
        {
            "formal_targets": [
                {
                    "id": "target:coverage",
                    "informal_source": "source theorem remains a formal gap",
                    "lean_statement_sketch": "",
                    "semantic_alignment_constraints": [],
                    "source_theorem_target_provenance": {
                        "source_theorem_target_known": True,
                        "target_lean_declaration": "split_conformal_coverage",
                        "source_theorem_goal_id": "theorem:coverage",
                    },
                    "expected_status": "FORMAL_GAP",
                }
            ],
            "lemma_dependency_plan": [
                {"from": "b1", "to": "target:coverage", "role": "bridge", "risk": ""}
            ],
            "retrieval_queries": [
                {
                    "query": "Lean rank uniformity finite sample coverage",
                    "target_library": "LeanRAG",
                    "purpose": "ground PF residual block",
                }
            ],
            "proof_search_plan": {
                "preferred_tools": ["local_lean"],
                "tactic_or_certificate_hints": [],
                "kernel_check_plan": ["kernel replay only after Lean candidate exists"],
                "known_blockers": ["semantic definition missing"],
            },
            "pseudo_formal_proof_packets": [
                {
                    "proof_evidence_status": "CLAIMED_PROOF",
                    "kernel_verified": True,
                    "source_theorem_kernel_verified": True,
                    "promotion_gate": "accept_pseudo_formal_verifier",
                    "theorem_id": "theorem:coverage",
                    "source_artifact_id": "theory:split_conformal",
                    "blocks": [
                        {
                            "block_id": "b1",
                            "block_type": "lemma",
                            "conclusion": "rank is uniform",
                            "proof_text": "Exchangeability implies rank uniformity.",
                            "source_anchors": [
                                {
                                    "kind": "theory_trace",
                                    "id": "equation:rank_uniformity",
                                    "excerpt": "rank uniformity",
                                }
                            ],
                            "lean_feasibility": "needs_rag",
                            "faithfulness_status": "faithful",
                            "block_verification": {
                                "verdict": "accepted",
                                "rollout_count": 1,
                            },
                        }
                    ],
                }
            ],
            "gap_taxonomy": [
                {
                    "gap": "semantic definition for coverage event",
                    "kind": "semantic_alignment",
                    "next_owner": "FormalizerProofEngineer",
                }
            ],
            "critic_findings": [
                {
                    "critic": "unit_test",
                    "finding": "PF packet is planning only",
                    "reroute_if_confirmed": "AgentRuntime",
                }
            ],
            "next_actions": [
                {
                    "owner_agent": "AgentRuntime",
                    "action": "route PF residual block to LeanRAG",
                    "acceptance_gate": "target-prover kernel replay required",
                }
            ],
        },
        question=question,
        model="claude-sonnet-test",
        model_tier="sonnet",
        provider_name="anthropic",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet={"packet_id": "theory:split_conformal"},
        proof_bank_runtime_memory_summary={},
        environment_feedback={},
    )

    pf_packet = packet["pseudo_formal_proof_packets"][0]
    assert pf_packet["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert pf_packet["kernel_verified"] is False
    assert pf_packet["source_theorem_kernel_verified"] is False
    assert pf_packet["promotion_gate"] == PSEUDO_FORMALIZATION_PROMOTION_GATE
    assert pf_packet["boundary_corrections"] == [
        "kernel_verified_forced_false",
        "source_theorem_kernel_verified_forced_false",
        "proof_evidence_status_forced_non_proof",
        "promotion_gate_forced_kernel_replay",
    ]
    assert validate_pseudo_formal_packet(pf_packet) == []
    assert validate_formalizer_packet(packet) == []


def test_formalizer_normalizes_pseudo_formal_block_aliases_before_validation() -> None:
    payload = _minimal_formalizer_response(include_pseudo_formal=True)
    block = payload["pseudo_formal_proof_packets"][0]["blocks"][0]
    block.pop("conclusion")
    block.pop("proof_text")
    block.pop("source_anchors")
    block["claim"] = "the test rank is uniform after exchangeable insertion"
    block["argument"] = "The proof body only uses symmetry of the inserted rank."
    block["source_refs"] = {
        "kind": "theory_trace",
        "source_id": "equation:rank_uniformity",
        "excerpt": "rank uniformity equation",
    }
    block["faithfulness_status"] = "UNVERIFIED"
    block["lean_feasibility"] = "needs_rag"
    packet = _normalize_formalizer_packet(
        payload,
        question=_pf_test_question(),
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={},
        environment_feedback={},
    )

    pf_block = packet["pseudo_formal_proof_packets"][0]["blocks"][0]

    assert pf_block["conclusion"] == (
        "the test rank is uniform after exchangeable insertion"
    )
    assert pf_block["proof_text"].startswith("The proof body")
    assert pf_block["source_anchors"][0]["id"] == "equation:rank_uniformity"
    assert pf_block["faithfulness_status"] == "unchecked"
    assert validate_formalizer_packet(packet) == []
    assert (
        _validate_required_pseudo_formalization_packet(
            packet,
            environment_feedback=_pf_required_feedback(),
            proof_bank_runtime_memory_summary={},
        )
        == []
    )
    work_order_rows = pseudo_formal_block_work_order_rows(
        packet["pseudo_formal_proof_packets"][0]
    )
    assert {
        row["row_kind"]
        for row in pseudo_formal_routable_work_order_rows(work_order_rows)
    } == {"pseudo_formal_faithfulness_review"}


def test_required_pf_bv_fail_closes_placeholder_formal_target_to_gap() -> None:
    payload = _minimal_formalizer_response(
        include_pseudo_formal=True,
        pf_block_overrides={
            "semantic_primitive_requirements": ["coverage_event"],
            "lean_feasibility": "needs_semantic_definition",
            "faithfulness_status": "faithful",
            "faithfulness_repair": {
                "status": "not_required",
                "attempts": 0,
                "flagged_discrepancies": [],
            },
            "block_verification": {"verdict": "unknown"},
        },
    )
    payload["formal_targets"] = [
        {
            "id": "split_conformal_source_theorem_placeholder",
            "informal_source": "source theorem placeholder emitted beside PF/BV",
            "lean_statement_sketch": (
                "theorem split_conformal_source_theorem_placeholder "
                "(p : Prop) : p := by\n"
                "  sorry\n"
            ),
            "expected_status": "NEEDS_KERNEL_CHECK",
            "source_theorem_target_provenance": {
                "source_theorem_target_known": True,
                "target_lean_declaration": (
                    "split_conformal_source_theorem_placeholder"
                ),
                "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
            },
        }
    ]
    packet = _normalize_formalizer_packet(
        payload,
        question=_pf_test_question(),
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={
            "pseudo_formalization_required": True,
            "source_theorem_exact_semantic_definition_structural_reformulation_required": True,
        },
        environment_feedback={},
    )

    target = packet["formal_targets"][0]
    assert target["expected_status"] == "FORMAL_GAP"
    assert target["lean_statement_sketch"] == ""
    assert target["normalizer_status"] == (
        "FAIL_CLOSED_PLACEHOLDER_LEAN_SKETCH_TO_FORMAL_GAP"
    )
    assert packet["fail_closed_placeholder_formal_targets"][0][
        "placeholder_error"
    ] == "contains Lean sorry placeholder"
    assert (
        _validate_required_pseudo_formalization_packet(
            packet,
            proof_bank_runtime_memory_summary={
                "pseudo_formalization_required": True
            },
        )
        == []
    )
    assert validate_formalizer_packet(packet) == []


def test_formalizer_alias_normalization_does_not_fake_empty_source_anchor() -> None:
    payload = _minimal_formalizer_response(include_pseudo_formal=True)
    block = payload["pseudo_formal_proof_packets"][0]["blocks"][0]
    block.pop("source_anchors")
    block["anchors"] = {}
    packet = _normalize_formalizer_packet(
        payload,
        question=_pf_test_question(),
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={},
        environment_feedback={},
    )

    errors = validate_formalizer_packet(packet)

    assert packet["pseudo_formal_proof_packets"][0]["blocks"][0]["source_anchors"] == []
    assert (
        "pseudo_formal_proof_packets[0] blocks[0] missing source_anchors"
        in errors
    )
    required_errors = _validate_required_pseudo_formalization_packet(
        packet,
        environment_feedback=_pf_required_feedback(),
        proof_bank_runtime_memory_summary={},
    )
    assert len(required_errors) == 1
    assert required_errors[0].startswith(
        "pseudo_formalization_required: no locally valid "
        "pseudo_formal_proof_packets entry was emitted"
    )
    assert "blocks[0] missing source_anchors" in required_errors[0]


def test_formalizer_repair_loop_requires_pf_packet_for_proof_body_blocker() -> None:
    question = _pf_test_question()
    feedback = _pf_required_feedback()
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=_SequenceStaticGeneratorBackend(
            [
                _minimal_formalizer_response(include_pseudo_formal=False),
                _minimal_formalizer_response(
                    include_pseudo_formal=True,
                    pf_block_overrides={
                        "semantic_primitive_requirements": ["coverage_event"],
                        "lean_feasibility": "needs_semantic_definition",
                        "faithfulness_status": "faithful",
                        "faithfulness_repair": {
                            "status": "not_required",
                            "attempts": 0,
                            "flagged_discrepancies": [],
                        },
                        "block_verification": {"verdict": "unknown"},
                    },
                ),
            ]
        ),
        config=FormalizerConfig(
            provider_name="static",
            model="static-formalizer",
            max_repair_attempts=1,
        ),
    )

    packet = formalizer.propose(
        question=question,
        theory_packet=_pf_theory_packet(),
        simulation_manifest={"manifest_id": "simulation:test"},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1},
        registered_problem={"question_id": question.id, "problem_class": "coverage"},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )

    assert packet["llm_json_repair_attempts"] == 1
    assert packet["llm_json_repair_history"][0]["ok"] is False
    assert any(
        "pseudo_formalization_required" in error
        for error in packet["llm_json_repair_history"][0]["errors"]
    )
    assert packet["llm_json_repair_history"][1]["ok"] is True
    assert len(packet["pseudo_formal_proof_packets"]) == 1
    pf_packet = packet["pseudo_formal_proof_packets"][0]
    assert pf_packet["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert pf_packet["kernel_verified"] is False
    assert pf_packet["source_theorem_kernel_verified"] is False
    assert validate_pseudo_formal_packet(pf_packet) == []
    assert (
        _validate_required_pseudo_formalization_packet(
            packet,
            environment_feedback=feedback,
            proof_bank_runtime_memory_summary={},
        )
        == []
    )
    assert validate_formalizer_packet(packet) == []


def test_required_pf_validator_rejects_independently_verified_but_unrouted_packet() -> None:
    question = _pf_test_question()
    feedback = _pf_required_feedback()
    packet = _normalize_formalizer_packet(
        _minimal_formalizer_response(
            include_pseudo_formal=True,
            pf_block_overrides={
                "lean_feasibility": "unknown",
                "semantic_primitive_requirements": [],
                "faithfulness_status": "faithful",
                "block_verification": {
                    "verdict": "accepted",
                    "rollout_count": 1,
                    "verifier_provenance": "independent_block_verifier",
                    "independent_verifier": True,
                },
            },
        ),
        question=question,
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )

    errors = _validate_required_pseudo_formalization_packet(
        packet,
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
    )

    assert any("did not produce any effective lane-routable" in error for error in errors)


def test_capability_eval_allows_required_pf_bv_route_without_lean_candidate() -> None:
    feedback = _pf_required_feedback()
    packet = _normalize_formalizer_packet(
        _minimal_formalizer_response(include_pseudo_formal=True),
        question=_pf_test_question(),
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )

    assert _validate_required_pseudo_formalization_packet(
        packet,
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
    ) == []
    assert _validate_capability_eval_formalizer_lean_candidate_packet(
        packet,
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
    ) == []


def test_capability_eval_still_requires_lean_candidate_without_pf_bv_route() -> None:
    packet = _normalize_formalizer_packet(
        _minimal_formalizer_response(include_pseudo_formal=False),
        question=_pf_test_question(),
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={},
        environment_feedback={},
    )

    assert _validate_capability_eval_formalizer_lean_candidate_packet(
        packet,
        environment_feedback={},
        proof_bank_runtime_memory_summary={},
    ) == [
        "capability_eval requires at least one Claude/OpenAI-generated "
        "Lean statement sketch in formal_targets or "
        "source_to_bridge_premise_derivation_candidates"
    ]


def test_required_pf_validator_accepts_pending_block_with_independent_bv_request() -> None:
    question = _pf_test_question()
    feedback = _pf_required_feedback()
    packet = _normalize_formalizer_packet(
        _minimal_formalizer_response(
            include_pseudo_formal=True,
            pf_block_overrides={
                "lean_feasibility": "lean_now",
                "semantic_primitive_requirements": [],
                "faithfulness_status": "faithful",
                "block_verification": {"verdict": "unknown"},
            },
        ),
        question=question,
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )

    errors = _validate_required_pseudo_formalization_packet(
        packet,
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
    )

    assert errors == []
    rows = pseudo_formal_block_work_order_rows(packet["pseudo_formal_proof_packets"][0])
    assert {
        row["row_kind"] for row in pseudo_formal_routable_work_order_rows(rows)
    } == {PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND}


def test_structural_exact_semantic_memory_requires_pf_packet() -> None:
    question = _pf_test_question()
    proof_memory_summary = {
        "source_theorem_exact_semantic_definition_structural_reformulation_required": True,
        "source_theorem_exact_semantic_definition_structural_reformulation_target_names": [
            "split_conformal_finite_sample_coverage"
        ],
        "source_theorem_exact_semantic_definition_structural_reformulation_placeholder_symbols": [
            "C_n"
        ],
        "pseudo_formalization_required": True,
        "requires_pseudo_formalization": True,
        "pseudo_formalization_required_reason": (
            "exact_semantic_definition_structural_reformulation_required"
        ),
        "recommended_formalizer_target_mode": (
            "source_theorem_exact_semantic_definition_structural_reformulation"
        ),
        "recommended_source_theorem_integration_action": (
            "structural_reformulate_exact_semantic_definition_with_pf_bv"
        ),
    }
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=_SequenceStaticGeneratorBackend(
            [
                _minimal_formalizer_response(include_pseudo_formal=False),
                _minimal_formalizer_response(
                    include_pseudo_formal=True,
                    pf_block_overrides={
                        "semantic_primitive_requirements": ["coverage_event"],
                        "lean_feasibility": "needs_semantic_definition",
                        "faithfulness_status": "faithful",
                        "faithfulness_repair": {
                            "status": "not_required",
                            "attempts": 0,
                            "flagged_discrepancies": [],
                        },
                        "block_verification": {"verdict": "unknown"},
                    },
                ),
            ]
        ),
        config=FormalizerConfig(
            provider_name="static",
            model="static-formalizer",
            max_repair_attempts=1,
        ),
    )

    packet = formalizer.propose(
        question=question,
        theory_packet=_pf_theory_packet(),
        simulation_manifest={"manifest_id": "simulation:test"},
        algorithm_manifest={"manifest_id": "algorithm:test", "n_executed": 1},
        registered_problem={"question_id": question.id, "problem_class": "coverage"},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary=proof_memory_summary,
        environment_feedback={},
    )

    assert packet["llm_json_repair_attempts"] == 1
    assert packet["llm_json_repair_history"][0]["ok"] is False
    assert any(
        "pseudo_formalization_required" in error
        for error in packet["llm_json_repair_history"][0]["errors"]
    )
    assert packet["llm_json_repair_history"][1]["ok"] is True
    assert len(packet["pseudo_formal_proof_packets"]) == 1
    assert (
        _validate_required_pseudo_formalization_packet(
            packet,
            environment_feedback={},
            proof_bank_runtime_memory_summary=proof_memory_summary,
        )
        == []
    )
    assert validate_formalizer_packet(packet) == []


def test_structural_exact_semantic_memory_rejects_generic_review_only() -> None:
    question = _pf_test_question()
    proof_memory_summary = {
        "source_theorem_exact_semantic_definition_structural_reformulation_required": True,
        "pseudo_formalization_required": True,
        "requires_pseudo_formalization": True,
    }
    packet = _normalize_formalizer_packet(
        _minimal_formalizer_response(include_pseudo_formal=True),
        question=question,
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary=proof_memory_summary,
        environment_feedback={},
    )

    errors = _validate_required_pseudo_formalization_packet(
        packet,
        environment_feedback={},
        proof_bank_runtime_memory_summary=proof_memory_summary,
    )

    assert any("only generic review rows" in error for error in errors)
    assert any("required target lanes" in error for error in errors)
    assert any("lean_feasibility=needs_semantic_definition" in error for error in errors)
    assert any("semantic_primitive_requirements" in error for error in errors)


def test_proof_body_adapter_feedback_does_not_require_pf_without_explicit_gate() -> None:
    question = _pf_test_question()
    feedback = _pf_required_feedback(required=False)
    packet = _normalize_formalizer_packet(
        _minimal_formalizer_response(include_pseudo_formal=False),
        question=question,
        model="static-formalizer",
        model_tier="sonnet",
        provider_name="static",
        backend_provider_name="static",
        raw_response="{}",
        theory_packet=_pf_theory_packet(),
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )

    assert (
        _validate_required_pseudo_formalization_packet(
            packet,
            environment_feedback=feedback,
            proof_bank_runtime_memory_summary={},
        )
        == []
    )


class _SequenceStaticGeneratorBackend:
    provider_name = "static"

    def __init__(self, responses: list[Any]) -> None:
        self._responses = [
            json.dumps(row, indent=2, default=str)
            if isinstance(row, Mapping)
            else str(row)
            for row in responses
        ]
        self._index = 0

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return GeneratorResponse(
            text=response,
            provider=self.provider_name,
            model=request.model,
            metadata={"generator_only": True, "tools_available": False},
        )


def _independent_bv_request_learning_row() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": "RuntimeLearningRow",
        "question_id": "conformal_prediction_coverage",
        "learning_task": PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
        "pseudo_formal_method_contract_id": (
            PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
        ),
        "pseudo_formal_pipeline_stage": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
        "target_theorem_name": "split_conformal_finite_sample_coverage",
        "target_ids": [
            "split_conformal_finite_sample_coverage",
            "b_rank_uniform",
        ],
        "next_owner_subsystem": "BlockVerifier/CalibrationReferee",
        "memory_status": "PSEUDO_FORMAL_BLOCK_ROUTING_MEMORY",
        "source_agenda_id": "pseudo_formal:block_verification:rank_uniform",
        "source_pseudo_formal_work_order_id": (
            "pseudo_formal_work_order:rank_uniform:independent-bv"
        ),
        "source_formalizer_proposal_id": "formalizer_proposal:pseudo",
        "source_formalization_manifest_id": "formalization_manifest:pseudo",
        "source_packet_id": "pseudo_formal_packet:coverage",
        "source_theorem_id": "split_conformal_finite_sample_coverage",
        "source_block_id": "b_rank_uniform",
        "source_block_type": "lemma",
        "source_block_conclusion": "rank is uniform by exchangeability",
        "block_depth": 2,
        "dependency_scope": PSEUDO_FORMAL_DEFAULT_DEPENDENCY_SCOPE,
        "dependency_ids": ["b_exchangeability"],
        "dependency_statement_context": [
            {
                "source_block_id": "b_exchangeability",
                "statement": "calibration/test scores are exchangeable",
            }
        ],
        "scope_parent_id": "b_exchangeability",
        "inherited_scope": ["exchangeability setup"],
        "source_block_premises": ["scores are exchangeable"],
        "source_block_proof_text": (
            "By exchangeability, every rank position is equally likely."
        ),
        "faithfulness_status": "faithful",
        "faithfulness_repair_status": "not_required",
        "block_verification": {"verdict": "unknown"},
        "block_verification_verifier_provenance": "not_run",
        "block_verification_independent": False,
        "independent_block_verification_required": True,
        "bv_calibration": {
            "strictness_threshold": PSEUDO_FORMAL_DEFAULT_CALIBRATION_STRICTNESS,
            "aggregation_rule": "parallel_pessimistic_aggregation",
            "pessimistic_acceptance": True,
            "rollout_count": 0,
        },
        "source_anchors": [{"kind": "theory_trace", "id": "equation:rank_uniformity"}],
        "runtime_generated_queue_name": PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME,
        "runtime_queue_status": "PENDING_FORMAL_GAP_FROM_PSEUDO_FORMAL_BLOCK",
        "row_kind": PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
        "target_lane": "formal_gap",
        "input_summary": {
            "trigger": PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER,
            "row_kind": PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
            "target_lane": "formal_gap",
            "work_order_id": (
                "pseudo_formal_work_order:rank_uniform:independent-bv"
            ),
            "source_theorem_id": "split_conformal_finite_sample_coverage",
            "source_block_id": "b_rank_uniform",
            "dependency_statement_context": [
                {
                    "source_block_id": "b_exchangeability",
                    "statement": "calibration/test scores are exchangeable",
                }
            ],
            "source_block_premises": ["scores are exchangeable"],
            "source_block_proof_text": (
                "By exchangeability, every rank position is equally likely."
            ),
            "block_verification": {"verdict": "unknown"},
            "block_verification_verifier_provenance": "not_run",
            "block_verification_independent": False,
            "independent_block_verification_required": True,
        },
        "target_behavior": (
            "run independent PF/BV block verification for the pseudo-formal block"
        ),
        "acceptance_gate": "independent verifier records accepted/failed feedback",
        "proof_evidence_status": PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
        "proof_evidence_boundary": (
            "Pseudo-formalization and block-verification rows are not theorem "
            "proof evidence."
        ),
    }


def _pf_test_question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="pf_blocker",
        title="PF blocked source theorem",
        description="Route a blocked source theorem proof body through PF/BV.",
        tags=("formalization", "proof_body"),
    )


def _pf_theory_packet() -> dict[str, Any]:
    return {
        "packet_id": "theory:pf-blocker",
        "theorem_cards": [
            {
                "id": "theorem:coverage",
                "claim": "the source theorem coverage statement follows from rank and threshold semantics",
            }
        ],
    }


def _pf_required_feedback(*, required: bool = True) -> dict[str, Any]:
    feedback: dict[str, Any] = {
        "source_theorem_proof_body_adapter_feedback": {
            "diagnostics": [
                {
                    "failure_classification": (
                        "source_theorem_semantic_alignment_unreviewed"
                    ),
                    "message": (
                        "source theorem proof-body repair is blocked until the "
                        "semantic coverage step is decomposed"
                    ),
                }
            ]
        }
    }
    if required:
        feedback["pseudo_formalization_required"] = True
    return feedback


def _minimal_formalizer_response(
    *,
    include_pseudo_formal: bool,
    pf_block_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "formal_targets": [
            {
                "id": "source_theorem_still_gap",
                "informal_source": "full source theorem remains a formal gap",
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
                "from": "pseudo-formal block b_semantic",
                "to": "source theorem",
                "role": "PF/BV decomposition before Lean replay",
                "risk": "semantic definition missing",
            }
        ],
        "retrieval_queries": [
            {
                "query": "coverage event semantic definition Lean source theorem",
                "target_library": "LeanRAG",
                "purpose": "ground PF residual block",
            }
        ],
        "proof_search_plan": {
            "preferred_tools": ["local_lean"],
            "kernel_check_plan": ["replay only after PF residual block is materialized"],
            "known_blockers": ["semantic definition missing"],
        },
        "gap_taxonomy": [
            {
                "gap": "semantic coverage step requires exact definition",
                "kind": "semantic_alignment",
                "next_owner": "FormalizerProofEngineer",
            }
        ],
        "critic_findings": [
            {
                "critic": "pf_validator",
                "finding": "PF/BV output is planning only",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "route PF residual block to exact semantic definition authoring",
                "acceptance_gate": "target-prover kernel replay required after definition",
            }
        ],
        "proof_evidence_status": "LLM_FORMALIZER_PROPOSAL_NOT_PROOF_EVIDENCE",
        "kernel_verified": False,
        "full_frontier_theorem_proved": False,
    }
    if include_pseudo_formal:
        block = {
            "block_id": "b_semantic",
            "block_type": "claim",
            "premises": ["rank threshold event is source-defined"],
            "conclusion": "coverage event follows from the source semantic threshold",
            "proof_text": "The source proof invokes the threshold-to-coverage step.",
            "dependency_ids": [],
            "source_anchors": [
                {
                    "kind": "proof_body",
                    "id": "source-proof:coverage-semantic-step",
                    "excerpt": "coverage follows from the threshold event",
                }
            ],
            "semantic_primitive_requirements": ["coverage_event"],
            "lean_feasibility": "needs_semantic_definition",
            "faithfulness_status": "needs_review",
            "faithfulness_repair": {
                "status": "needs_repair",
                "attempts": 0,
                "flagged_discrepancies": ["semantic definition omitted"],
            },
            "block_verification": {
                "verdict": "failed",
                "reason": "coverage_event is not exactly defined",
            },
        }
        block.update(dict(pf_block_overrides or {}))
        response["pseudo_formal_proof_packets"] = [
            {
                "theorem_id": "theorem:coverage",
                "source_artifact_id": "theory:pf-blocker",
                "blocks": [block],
            }
        ]
    return response
