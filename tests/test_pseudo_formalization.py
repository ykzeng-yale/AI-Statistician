from __future__ import annotations

from ai_statistician.pseudo_formalization import (
    PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
    PSEUDO_FORMAL_BLOCK_ROUTING_QUEUE_NAME,
    PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES,
    PSEUDO_FORMAL_BLOCK_ROUTING_TRIGGER,
    PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMALIZATION_PROMOTION_GATE,
    PSEUDO_FORMALIZATION_SCHEMA_ID,
    normalize_pseudo_formal_packet,
    pseudo_formal_block_work_order_rows,
    pseudo_formal_packet_json_schema,
    pseudo_formal_work_order_row_json_schema,
    pseudo_formalizer_output_contract,
    validate_pseudo_formal_packet,
)
from ai_statistician.formalizer_llm import (
    _normalize_formalizer_packet,
    build_formalizer_prompt,
    validate_formalizer_packet,
)
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
                "semantic_primitive_requirements": ["rank_uniformity"],
                "lean_feasibility": "lean_now",
                "faithfulness_status": "faithful",
                "block_verification": {"verdict": "accepted"},
            },
            {
                "block_id": "b2",
                "block_type": "claim",
                "dependency_ids": ["b1"],
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

    rows = pseudo_formal_block_work_order_rows(normalized)
    row_kinds = {row["row_kind"] for row in rows}
    assert "pseudo_formal_lean_candidate_seed" in row_kinds
    assert "pseudo_formal_exact_semantic_definition_request" in row_kinds
    assert "pseudo_formal_block_verification_failure" in row_kinds
    assert "pseudo_formal_faithfulness_review" in row_kinds
    assert "pseudo_formal_formal_library_grounding_query" in row_kinds
    assert "pseudo_formal_semantic_primitive_request" in row_kinds
    assert {row["kernel_verified"] for row in rows} == {False}
    assert {row["proof_evidence_status"] for row in rows} == {
        PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    }
    assert {row["promotion_gate"] for row in rows} == {
        PSEUDO_FORMALIZATION_PROMOTION_GATE
    }


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
                "source_anchors": [{"kind": "paper", "id": "source"}],
                "lean_feasibility": "unknown",
                "block_verification": {"verdict": "not_run"},
            },
        ],
    }

    errors = validate_pseudo_formal_packet(raw)

    assert "proof_evidence_status must be pseudo-formal non-proof" in errors
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
    assert "blocks[1] dependency_ids cannot include self" in errors

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


def test_pseudo_formalizer_contract_and_schema_expose_non_proof_boundary() -> None:
    contract = pseudo_formalizer_output_contract()
    schema = pseudo_formal_packet_json_schema()

    assert contract["schema_id"] == PSEUDO_FORMALIZATION_SCHEMA_ID
    assert contract["proof_evidence_status"] == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    assert contract["promotion_gate"] == PSEUDO_FORMALIZATION_PROMOTION_GATE
    assert "source_anchors" in contract["block_contract"]
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
    assert (
        schema["properties"]["proof_evidence_status"]["const"]
        == PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE
    )
    work_order_schema = pseudo_formal_work_order_row_json_schema()
    assert set(work_order_schema["properties"]["target_lane"]["enum"]) == set(
        PSEUDO_FORMAL_BLOCK_ROUTING_TARGET_LANES
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
                            "block_verification": {"verdict": "accepted"},
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
