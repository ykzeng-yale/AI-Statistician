import json
from pathlib import Path

from ai_statistician.source_theorem_exact_semantic_definition_source_lookup import (
    run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue,
)
from ai_statistician.source_theorem_exact_semantic_definition_verifier_gate_executor import (
    run_source_theorem_exact_semantic_definition_verifier_gate_executor,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _base_work_order(candidate: Path) -> dict:
    return {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedReviewVerifierGateWorkOrder"
        ),
        "work_order_id": "verifier-gate:good-rank",
        "source_review_packet_id": "review:good-rank",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_finite_sample_coverage",
        "target_ids": ["split_conformal_finite_sample_coverage"],
        "placeholder_symbol": "good_rank_event",
        "candidate_artifact_path": str(candidate),
        "definition_only_candidate_artifact_path": str(candidate),
        "local_definition_lean_checked": True,
        "local_definition_lean_compiled": True,
        "semantic_review_decision": "approved_definition_candidate",
        "semantic_review_status": (
            "llm_semantic_review_approved_definition_candidate_not_proof"
        ),
        "semantic_review_evidence": ["reviewed against source anchor hRank"],
        "semantic_review_required_before_proof_body": True,
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_kernel_verified": False,
        "source_theorem_kernel_evidence_eligible": False,
        "proof_evidence_status": (
            "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_WORK_ORDER_NOT_PROOF_EVIDENCE"
        ),
    }


def test_verifier_gate_executor_approves_anchored_typechecked_candidate(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "def good_rank_event (scores : List Nat) (test_score : Nat) (k : Nat) : Prop :=\n"
        "  scores.length + 1 <= k\n",
        encoding="utf-8",
    )
    work_orders = tmp_path / "work_orders.jsonl"
    row = {
        **_base_work_order(candidate),
        "semantic_primitive": "good_rank_event",
        "semantic_primitive_requirements": ["good_rank_event"],
        "source_anchors": [
            {
                "kind": "pseudo_formal_block",
                "id": "pf:block:good_rank_event",
                "excerpt": "rank event source block",
            }
        ],
        "source_pseudo_formal_work_order_id": "pseudo_formal_work_order:good_rank",
        "source_pseudo_formal_block_id": "pf:block:good_rank_event",
        "source_pseudo_formal_packet_id": "pseudo_formal_packet:coverage",
        "source_formalizer_proposal_id": "formalizer_proposal:pf_exact",
        "pseudo_formal_method_contract_id": (
            "pseudo_formalization_block_verification_calibration_v1"
        ),
        "pseudo_formal_pipeline_stage": "pseudo_formal_block_routing",
        "pseudo_formal_proof_evidence_status": (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        ),
        "source_reference_hints": [{"path": "Source.lean", "symbol": "hRank"}],
        "exact_source_theorem_binders": [
            {"name": "scores", "type": "List Nat", "role": "calibration scores"}
        ],
    }
    _write_jsonl(work_orders, [row])

    manifest = run_source_theorem_exact_semantic_definition_verifier_gate_executor(
        out_dir=tmp_path / "verifier",
        work_orders_jsonl=work_orders,
        local_lean=True,
        lean_command=("true",),
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_local_lean_checked"] == 1
    assert manifest["n_local_lean_compiled"] == 1
    assert manifest["n_verifier_approved"] == 1
    assert manifest["n_verifier_blocked"] == 0
    assert manifest["source_theorem_ready_for_exact_proof_body"] is True
    results = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_results_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert results[0]["verifier_gate_status"] == (
        "VERIFIER_APPROVED_FOR_PROOF_BODY_RECHECK"
    )
    assert results[0]["semantic_primitive_requirements"] == ["good_rank_event"]
    assert results[0]["source_anchors"][0]["id"] == "pf:block:good_rank_event"
    assert results[0]["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:good_rank"
    )
    assert results[0]["source_theorem_kernel_verified"] is False
    assert results[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
    )
    approved = [
        json.loads(line)
        for line in Path(manifest["verifier_approved_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert approved[0]["semantic_review_required_before_proof_body"] is False
    assert approved[0]["source_theorem_ready_for_exact_proof_body"] is True
    assert approved[0]["semantic_primitive_requirements"] == ["good_rank_event"]
    assert approved[0]["source_anchors"][0]["id"] == "pf:block:good_rank_event"
    assert approved[0]["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:good_rank"
    )
    assert approved[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_APPROVED_NOT_SOURCE_THEOREM_PROOF"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows[0]["semantic_primitive_requirements"] == [
        "good_rank_event"
    ]
    assert learning_rows[0]["source_anchors"][0]["id"] == (
        "pf:block:good_rank_event"
    )
    assert learning_rows[0]["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:good_rank"
    )
    assert learning_rows[0]["source_theorem_kernel_verified"] is False


def test_verifier_gate_executor_accepts_source_anchor_context(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "def good_rank_event (scores : List Nat) (test_score : Nat) (k : Nat) : Prop :=\n"
        "  scores.length + 1 <= k\n",
        encoding="utf-8",
    )
    work_orders = tmp_path / "work_orders.jsonl"
    row = {
        **_base_work_order(candidate),
        "source_anchor_context": [
            {
                "kind": "proof_body_goal_context",
                "proof_body_goal_excerpt": ["q : Real", "hq : q = q"],
            }
        ],
        "source_anchor_context_rows": 1,
    }
    _write_jsonl(work_orders, [row])

    manifest = run_source_theorem_exact_semantic_definition_verifier_gate_executor(
        out_dir=tmp_path / "verifier",
        work_orders_jsonl=work_orders,
        local_lean=True,
        lean_command=("true",),
    )

    assert manifest["n_verifier_approved"] == 1
    assert manifest["n_source_anchor_context_missing"] == 0
    results = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_results_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert results[0]["source_anchor_context"][0]["kind"] == (
        "proof_body_goal_context"
    )
    approved = [
        json.loads(line)
        for line in Path(manifest["verifier_approved_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert approved[0]["source_anchor_context"][0]["kind"] == (
        "proof_body_goal_context"
    )
    assert approved[0]["source_anchor_context_rows"] == 1


def test_verifier_gate_executor_accepts_nested_exact_semantic_context(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "def good_rank_event (scores : List Nat) (test_score : Nat) (k : Nat) : Prop :=\n"
        "  scores.length + 1 <= k\n",
        encoding="utf-8",
    )
    work_orders = tmp_path / "work_orders.jsonl"
    row = {
        **_base_work_order(candidate),
        "input_summary": {
            "exact_semantic_definition_context": {
                "semantic_primitive": "good_rank_event",
                "semantic_primitive_requirements": [
                    "good_rank_event must use the recovered source rank binder"
                ],
                "source_anchors": [
                    {
                        "kind": "pseudo_formal_block",
                        "id": "pf:block:good_rank_event",
                        "excerpt": "rank event source block",
                    }
                ],
                "source_anchor_context": [
                    {
                        "kind": "proof_body_goal_context",
                        "proof_body_goal_excerpt": [
                            "scores : List Nat",
                            "k : Nat",
                        ],
                    }
                ],
                "exact_source_theorem_binders": [
                    {
                        "name": "k",
                        "type": "Nat",
                        "role": "rank threshold",
                    }
                ],
                "candidate_definition_request": {
                    "required_binders": ["scores", "test_score", "k"],
                    "required_anchor_names": ["hRank"],
                },
                "source_pseudo_formal_work_order_id": (
                    "pseudo_formal_work_order:good_rank"
                ),
                "source_pseudo_formal_block_id": "pf:block:good_rank_event",
                "source_pseudo_formal_packet_id": "pseudo_formal_packet:coverage",
                "pseudo_formal_proof_evidence_status": (
                    "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
                ),
            }
        },
    }
    _write_jsonl(work_orders, [row])

    manifest = run_source_theorem_exact_semantic_definition_verifier_gate_executor(
        out_dir=tmp_path / "verifier",
        work_orders_jsonl=work_orders,
        local_lean=True,
        lean_command=("true",),
    )

    assert manifest["n_verifier_approved"] == 1
    assert manifest["n_source_anchor_context_missing"] == 0
    results = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_results_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert results[0]["source_anchor_context"][0]["kind"] == (
        "proof_body_goal_context"
    )
    assert {
        (row["source"], row.get("name", ""))
        for row in results[0]["source_anchor_context"]
    } >= {
        ("exact_source_theorem_binders", "k"),
        ("candidate_definition_request.required_anchor_names", "hRank"),
    }
    assert results[0]["semantic_primitive_requirements"] == [
        "good_rank_event must use the recovered source rank binder"
    ]
    assert results[0]["source_anchors"][0]["id"] == "pf:block:good_rank_event"
    assert results[0]["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:good_rank"
    )
    approved = [
        json.loads(line)
        for line in Path(manifest["verifier_approved_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert approved[0]["source_anchor_context_rows"] >= 4
    assert approved[0]["semantic_review_required_before_proof_body"] is False
    assert approved[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_APPROVED_NOT_SOURCE_THEOREM_PROOF"
    )


def test_verifier_gate_executor_blocks_missing_source_anchor_context(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "/-\nKnown gaps:\n"
        "[\"No source theorem binders were available for review.\"]\n"
        "-/\n"
        "def good_rank_event (scores : List Nat) (test_score : Nat) (k : Nat) : Prop :=\n"
        "  scores.length + 1 <= k\n",
        encoding="utf-8",
    )
    work_orders = tmp_path / "work_orders.jsonl"
    row = {
        **_base_work_order(candidate),
        "known_gaps": ["No source theorem binders were available for review."],
    }
    _write_jsonl(work_orders, [row])

    manifest = run_source_theorem_exact_semantic_definition_verifier_gate_executor(
        out_dir=tmp_path / "verifier",
        work_orders_jsonl=work_orders,
        local_lean=True,
        lean_command=("true",),
    )

    assert manifest["n_verifier_approved"] == 0
    assert manifest["n_verifier_blocked"] == 1
    assert manifest["source_theorem_ready_for_exact_proof_body"] is False
    assert manifest["n_source_anchor_context_missing"] == 1
    assert manifest["n_known_gaps_unresolved"] == 1
    assert manifest["n_candidate_known_gaps_comment_present"] == 1
    results = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_results_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert results[0]["verifier_gate_status"] == (
        "VERIFIER_GATE_BLOCKED_SOURCE_SEMANTIC_CONTEXT_INSUFFICIENT"
    )
    assert "source_anchor_context_missing" in results[0]["verifier_gate_blockers"]
    assert "known_gaps_unresolved" in results[0]["verifier_gate_blockers"]
    assert results[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR"
    )


def test_typechecked_recheck_verifier_work_order_preserves_semantic_context(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "def good_rank_event (scores : List Nat) (test_score : Nat) (k : Nat) : Prop :=\n"
        "  scores.length + 1 <= k\n",
        encoding="utf-8",
    )
    review_packets = tmp_path / "review_packets.jsonl"
    _write_jsonl(
        review_packets,
        [
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
                ),
                "review_packet_id": "review:good-rank",
                "target_theorem_name": "split_conformal_finite_sample_coverage",
                "target_ids": ["split_conformal_finite_sample_coverage"],
                "placeholder_symbol": "good_rank_event",
                "semantic_primitive": "good_rank_event",
                "semantic_primitive_requirements": ["good_rank_event"],
                "source_anchors": [
                    {
                        "kind": "pseudo_formal_block",
                        "id": "pf:block:good_rank_event",
                        "excerpt": "rank event source block",
                    }
                ],
                "source_pseudo_formal_work_order_id": (
                    "pseudo_formal_work_order:good_rank"
                ),
                "source_pseudo_formal_block_id": "pf:block:good_rank_event",
                "source_pseudo_formal_packet_id": "pseudo_formal_packet:coverage",
                "source_formalizer_proposal_id": "formalizer_proposal:pf_exact",
                "pseudo_formal_method_contract_id": (
                    "pseudo_formalization_block_verification_calibration_v1"
                ),
                "pseudo_formal_pipeline_stage": "pseudo_formal_block_routing",
                "pseudo_formal_proof_evidence_status": (
                    "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
                ),
                "candidate_artifact_path": str(candidate),
                "local_definition_lean_compiled": True,
                "semantic_review_decision": "approved_definition_candidate",
                "semantic_review_status": (
                    "llm_semantic_review_approved_definition_candidate_not_proof"
                ),
                "semantic_review_evidence": ["reviewed source anchor hRank"],
                "semantic_review_required_before_proof_body": True,
                "source_theorem_ready_for_exact_proof_body": False,
                "source_theorem_kernel_verified": False,
                "source_reference_hints": [
                    {"path": "Source.lean", "symbol": "hRank"}
                ],
                "source_anchor_context": [
                    {
                        "kind": "proof_body_goal_context",
                        "proof_body_goal_excerpt": ["q : Real", "hq : q = q"],
                    }
                ],
                "source_anchor_context_rows": 1,
                "semantic_alignment_constraints": [
                    "rank threshold must use the source theorem k binder"
                ],
                "candidate_definition_request": {
                    "required_binders": ["scores", "test_score", "k"],
                    "required_anchor_names": ["hRank"],
                },
                "definition_contract": {
                    "known_gaps": ["threshold binder still requires verifier check"]
                },
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        ],
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
    )
    verifier_gate_rows = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_work_orders_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert verifier_gate_rows[0]["source_reference_hints"] == [
        {"path": "Source.lean", "symbol": "hRank"}
    ]
    assert verifier_gate_rows[0]["source_anchor_context"] == [
        {
            "kind": "proof_body_goal_context",
            "proof_body_goal_excerpt": ["q : Real", "hq : q = q"],
        }
    ]
    assert verifier_gate_rows[0]["source_anchor_context_rows"] == 1
    assert verifier_gate_rows[0]["semantic_alignment_constraints"] == [
        "rank threshold must use the source theorem k binder"
    ]
    assert verifier_gate_rows[0]["candidate_definition_request"][
        "required_anchor_names"
    ] == ["hRank"]
    assert verifier_gate_rows[0]["semantic_primitive_requirements"] == [
        "good_rank_event"
    ]
    assert verifier_gate_rows[0]["source_anchors"][0]["id"] == (
        "pf:block:good_rank_event"
    )
    assert verifier_gate_rows[0]["source_pseudo_formal_work_order_id"] == (
        "pseudo_formal_work_order:good_rank"
    )
    assert verifier_gate_rows[0]["input_summary"][
        "semantic_primitive_requirements"
    ] == ["good_rank_event"]
    assert verifier_gate_rows[0]["input_summary"]["source_anchors"][0]["id"] == (
        "pf:block:good_rank_event"
    )
    assert verifier_gate_rows[0]["known_gaps"] == [
        "threshold binder still requires verifier check"
    ]
