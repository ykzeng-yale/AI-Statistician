import json
from pathlib import Path

from ai_statistician.source_theorem_exact_semantic_definition_source_lookup import (
    run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue,
)
from ai_statistician.source_theorem_exact_semantic_definition_verifier_gate_executor import (
    _runtime_learning_row,
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


def test_verifier_gate_learning_row_normalizes_serialized_false_ready() -> None:
    row = _runtime_learning_row(
        {
            "source_work_order_id": "verifier-gate:string-false",
            "verifier_gate_result_id": "result:string-false",
            "target_theorem_name": "split_conformal_finite_sample_coverage",
            "target_ids": ["split_conformal_finite_sample_coverage"],
            "placeholder_symbol": "good_rank_event",
            "source_theorem_ready_for_exact_proof_body": "false",
            "local_lean_checked": True,
            "local_lean_compiled": True,
            "verifier_gate_status": "VERIFIER_GATE_BLOCKED_SOURCE_SEMANTIC_CONTEXT_INSUFFICIENT",
            "runtime_queue_status": (
                "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_REPAIR"
            ),
        }
    )

    assert row["source_theorem_ready_for_exact_proof_body"] is False
    assert row["source_theorem_kernel_verified"] is False
    assert row["source_theorem_kernel_evidence_eligible"] is False
    assert row["recommended_next_action"] == (
        "repair source-anchor context or semantic gaps before exact "
        "source proof-body recheck"
    )


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
        "source_pseudo_formal_prompt_scaffold_origin": {
            "artifact_kind": "PseudoFormalPromptScaffoldOrigin",
            "scaffold_kind": "pseudo_formalization_required_copy_fragment",
            "source": "FormalizerPrompt",
            "required_output_key": "pseudo_formal_proof_packets",
            "copy_fragment_id": "pseudo_formal_copy_fragment:good_rank",
            "proof_evidence_status": (
                "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
            ),
        },
        "source_prompt_scaffold_kind": (
            "pseudo_formalization_required_copy_fragment"
        ),
        "source_prompt_scaffold_id": "pseudo_formal_copy_fragment:good_rank",
        "source_prompt_scaffold_required_output_key": (
            "pseudo_formal_proof_packets"
        ),
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
    assert manifest["n_work_orders_from_pseudo_formal"] == 1
    assert manifest["n_results_from_pseudo_formal"] == 1
    assert manifest["n_local_lean_checked_from_pseudo_formal"] == 1
    assert manifest["n_local_lean_compiled_from_pseudo_formal"] == 1
    assert manifest["n_verifier_approved_from_pseudo_formal"] == 1
    assert manifest["n_verifier_blocked_from_pseudo_formal"] == 0
    assert manifest["source_pseudo_formal_work_order_ids"] == [
        "pseudo_formal_work_order:good_rank"
    ]
    assert manifest["source_pseudo_formal_block_ids"] == ["pf:block:good_rank_event"]
    assert manifest["source_prompt_scaffold_ids"] == [
        "pseudo_formal_copy_fragment:good_rank"
    ]
    assert manifest["source_prompt_scaffold_kinds"] == [
        "pseudo_formalization_required_copy_fragment"
    ]
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
    assert results[0]["source_pseudo_formal_prompt_scaffold_origin"][
        "scaffold_kind"
    ] == "pseudo_formalization_required_copy_fragment"
    assert results[0]["source_prompt_scaffold_id"] == (
        "pseudo_formal_copy_fragment:good_rank"
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
    assert approved[0]["source_prompt_scaffold_id"] == (
        "pseudo_formal_copy_fragment:good_rank"
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
    assert learning_rows[0]["source_prompt_scaffold_id"] == (
        "pseudo_formal_copy_fragment:good_rank"
    )
    assert learning_rows[0]["source_theorem_kernel_verified"] is False


def test_verifier_gate_executor_tracks_formalizer_pf_component_gate_candidate(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "def coverage_event (covered : Prop) : Prop :=\n"
        "  covered\n",
        encoding="utf-8",
    )
    work_orders = tmp_path / "work_orders.jsonl"
    exact_rows_jsonl = "runs/formalizer_pf/exact_semantic_definition_rows.jsonl"
    row = {
        **_base_work_order(candidate),
        "work_order_id": "verifier-gate:coverage-event",
        "source_review_packet_id": "review:coverage-event",
        "placeholder_symbol": "coverage_event",
        "semantic_primitive": "coverage_event",
        "semantic_primitive_requirements": ["coverage_event"],
        "source_anchors": [
            {
                "kind": "formalizer_component_gate_exact_row",
                "id": "pf-component:coverage_event",
                "excerpt": "coverage event source row",
            }
        ],
        "source_component_gate": "formalizer_pseudo_formal_packet_component_gate",
        "source_component_gate_exact_rows_jsonl": exact_rows_jsonl,
        "component_eval_manifest_path": "runs/formalizer_pf/manifest.json",
        "provider_name": "anthropic",
        "backend_provider_name": "anthropic",
        "source_reference_hints": [{"path": "Source.lean", "symbol": "covered"}],
        "exact_source_theorem_binders": [
            {"name": "covered", "type": "Prop", "role": "coverage event"}
        ],
    }
    _write_jsonl(work_orders, [row])

    manifest = run_source_theorem_exact_semantic_definition_verifier_gate_executor(
        out_dir=tmp_path / "verifier",
        work_orders_jsonl=work_orders,
        local_lean=True,
        lean_command=("true",),
    )

    assert manifest["n_work_orders_from_pseudo_formal"] == 1
    assert manifest["n_work_orders_from_formalizer_pf_component_gate"] == 1
    assert manifest["n_results_from_pseudo_formal"] == 1
    assert manifest["n_results_from_formalizer_pf_component_gate"] == 1
    assert manifest["n_local_lean_checked_from_pseudo_formal"] == 1
    assert manifest["n_local_lean_checked_from_formalizer_pf_component_gate"] == 1
    assert manifest["n_verifier_approved_from_pseudo_formal"] == 1
    assert manifest["n_verifier_approved_from_formalizer_pf_component_gate"] == 1
    assert manifest["formalizer_pf_component_gate_exact_rows_jsonl_paths"] == [
        exact_rows_jsonl
    ]

    approved = [
        json.loads(line)
        for line in Path(manifest["verifier_approved_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert approved[0]["source_component_gate"] == (
        "formalizer_pseudo_formal_packet_component_gate"
    )
    assert approved[0]["source_component_gate_exact_rows_jsonl"] == exact_rows_jsonl
    assert approved[0]["source_theorem_ready_for_exact_proof_body"] is True
    assert approved[0]["source_theorem_kernel_evidence_eligible"] is False
    assert "KERNEL_VERIFIED" not in approved[0]["proof_evidence_status"]


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


def test_verifier_gate_executor_preserves_required_anchor_bindings(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "def good_rank_event (n : Nat) (score : Nat -> Nat) (q : Nat) (hq : Prop) : Prop :=\n"
        "  hq\n",
        encoding="utf-8",
    )
    work_orders = tmp_path / "work_orders.jsonl"
    row = {
        **_base_work_order(candidate),
        "input_summary": {
            "exact_semantic_definition_context": {
                "semantic_primitive": "good_rank_event",
                "candidate_definition_request": {
                    "request_kind": (
                        "source_theorem_exact_semantic_definition_candidate"
                    ),
                    "placeholder_symbol": "good_rank_event",
                    "required_anchor_names": ["n2", "s", "q_hat", "hq"],
                    "available_anchor_names": [
                        "n",
                        "score",
                        "q",
                        "hq",
                        "n2",
                        "s",
                        "q_hat",
                    ],
                    "missing_required_anchor_names": [],
                    "required_anchor_bindings": [
                        {
                            "required_anchor_name": "n2",
                            "actual_anchor_name": "n",
                            "match_kind": "source_anchor_role",
                            "role": "calibration_size_anchor",
                            "binder": {
                                "name": "n",
                                "type": "Nat",
                                "role": "calibration_size_anchor",
                            },
                        },
                        {
                            "required_anchor_name": "s",
                            "actual_anchor_name": "score",
                            "match_kind": "source_anchor_role",
                            "role": "score_process_anchor",
                            "binder": {
                                "name": "score",
                                "type": "Nat -> Nat",
                                "role": "score_process_anchor",
                            },
                        },
                        {
                            "required_anchor_name": "q_hat",
                            "actual_anchor_name": "q",
                            "match_kind": "source_anchor_role",
                            "role": "threshold_function_anchor",
                            "binder": {
                                "name": "q",
                                "type": "Nat",
                                "role": "threshold_function_anchor",
                            },
                        },
                        {
                            "required_anchor_name": "hq",
                            "actual_anchor_name": "hq",
                            "match_kind": "exact_name",
                            "role": "quantile_definition_anchor",
                            "binder": {
                                "name": "hq",
                                "type": "Prop",
                                "role": "quantile_definition_anchor",
                            },
                        },
                    ],
                    "required_binders": [
                        {
                            "name": "n",
                            "type": "Nat",
                            "role": "calibration_size_anchor",
                        },
                        {
                            "name": "score",
                            "type": "Nat -> Nat",
                            "role": "score_process_anchor",
                        },
                        {
                            "name": "q",
                            "type": "Nat",
                            "role": "threshold_function_anchor",
                        },
                        {
                            "name": "hq",
                            "type": "Prop",
                            "role": "quantile_definition_anchor",
                        },
                    ],
                },
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
    binding_rows = [
        item
        for item in results[0]["source_anchor_context"]
        if item.get("kind") == "required_anchor_binding"
    ]
    assert {
        (
            item["required_anchor_name"],
            item["actual_anchor_name"],
            item["name"],
            item["type"],
            item["role"],
        )
        for item in binding_rows
    } >= {
        ("n2", "n", "n", "Nat", "calibration_size_anchor"),
        ("s", "score", "score", "Nat -> Nat", "score_process_anchor"),
        ("q_hat", "q", "q", "Nat", "threshold_function_anchor"),
        ("hq", "hq", "hq", "Prop", "quantile_definition_anchor"),
    }
    assert any(
        item.get("source") == "candidate_definition_request.required_binders"
        and item.get("name") == "q"
        and item.get("type") == "Nat"
        for item in results[0]["source_anchor_context"]
    )
    approved = [
        json.loads(line)
        for line in Path(manifest["verifier_approved_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    approved_binding_rows = [
        item
        for item in approved[0]["source_anchor_context"]
        if item.get("kind") == "required_anchor_binding"
    ]
    assert {
        (item["required_anchor_name"], item["actual_anchor_name"])
        for item in approved_binding_rows
    } >= {("n2", "n"), ("s", "score"), ("q_hat", "q"), ("hq", "hq")}
    assert approved[0]["candidate_definition_request"][
        "required_anchor_bindings"
    ][2]["actual_anchor_name"] == "q"


def test_verifier_gate_executor_blocks_nested_known_gaps(
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
                "source_anchor_context": [
                    {
                        "kind": "proof_body_goal_context",
                        "proof_body_goal_excerpt": [
                            "scores : List Nat",
                            "k : Nat",
                        ],
                    }
                ],
                "definition_contract": {
                    "known_gaps": [
                        "threshold binder still requires verifier check"
                    ]
                },
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

    assert manifest["n_verifier_approved"] == 0
    assert manifest["n_known_gaps_unresolved"] == 1
    assert manifest["n_source_anchor_context_missing"] == 0
    results = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_results_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert results[0]["known_gaps"] == [
        "threshold binder still requires verifier check"
    ]
    assert results[0]["verifier_gate_status"] == (
        "VERIFIER_GATE_BLOCKED_SOURCE_SEMANTIC_CONTEXT_INSUFFICIENT"
    )
    assert "known_gaps_unresolved" in results[0]["verifier_gate_blockers"]
    approved = [
        json.loads(line)
        for line in Path(manifest["verifier_approved_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert approved == []


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
