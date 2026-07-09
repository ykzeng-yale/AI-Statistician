from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.cli import _load_runtime_learning_memory
from ai_statistician.research_agent_runtime import (
    _runtime_learning_memory_source_theorem_exact_candidate_repairs,
)
from ai_statistician.exact_semantic_definition_policy import (
    exact_semantic_definition_fallback_source_anchor_role,
    exact_semantic_definition_placeholder_policy,
    exact_semantic_definition_source_anchor_role_rules,
)
from ai_statistician.source_theorem_exact_semantic_definition_source_lookup import (
    exact_semantic_definition_source_binders_from_context,
    run_source_theorem_exact_semantic_definition_candidate_synthesis,
    run_source_theorem_exact_semantic_definition_closure_review,
    run_source_theorem_exact_semantic_definition_source_lookup,
    run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue,
)


def _write_work_order(
    path: Path,
    *,
    placeholder_symbol: str,
    extra: dict[str, object] | None = None,
) -> None:
    row = {
        "schema_version": 1,
        "artifact_kind": (
            "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
        ),
        "work_order_id": (
            "source_theorem_exact_semantic_definition_work_order:"
            + placeholder_symbol
        ),
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": placeholder_symbol,
        "replacement_strategy": (
            "formalize or import a reviewed exact semantic definition"
        ),
        "search_targets": [placeholder_symbol],
        "candidate_registered_obligation_ids": [
            "split_conformal_good_rank_set_inclusion_bridge"
        ],
        "kernel_verified_source_theorem_semantic_support_obligation_ids": [
            "split_conformal_good_rank_set_inclusion_bridge"
        ],
        "kernel_verified_source_theorem_semantic_definition_ids": [],
        "semantic_closure_status": (
            "REGISTERED_SUPPORT_VERIFIED_PLACEHOLDER_DEFINITION_OPEN"
        ),
        "placeholder_definition_status": (
            "OPEN_REQUIRES_REVIEWED_FORMAL_DEFINITION"
        ),
        "source_theorem_ready_for_exact_proof_body": False,
        "source_theorem_semantic_support_only": True,
        "source_semantic_alignment_review_required": True,
        "source_theorem_target_identity_status": (
            "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
        ),
        "source_theorem_target_provenance": {
            "source_theorem_question_id": "conformal_prediction_coverage",
            "target_lean_declaration": "split_conformal_coverage",
        },
        "semantic_alignment_constraints": [
            "reviewed order statistic semantics must preserve rank k"
        ],
        "semantic_alignment_blockers": [
            "unreviewed synthesized definition semantic risk: "
            "draft finite maximum ignores rank k"
        ],
        "source_theorem_exact_semantic_definition_typechecked_candidate": {
            "definition_only_candidate_artifact_path": (
                "runs/candidate_artifacts/defs_only.lean"
            ),
            "local_definition_lean_compiled": True,
            "semantic_definition_typecheck_evidence_status": (
                "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
            ),
        },
        "definition_only_candidate_artifact_path": (
            "runs/candidate_artifacts/defs_only.lean"
        ),
        "candidate_artifact_path": "runs/candidate_artifacts/full.lean",
        "local_definition_lean_checked": True,
        "local_definition_lean_compiled": True,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
        ),
        "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
    }
    if extra:
        row.update(extra)
    path.write_text(
        json.dumps(row)
        + "\n",
        encoding="utf-8",
    )


def _write_exact_proof_body_queue_manifest(path: Path, *, candidate: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:split",
                        "source_work_order_id": "exact_source_work_order:split",
                        "target_theorem_name": "split_conformal_coverage",
                        "target_lean_declaration": "split_conformal_coverage",
                        "expected_target_lean_declaration": (
                            "split_conformal_coverage"
                        ),
                        "source_theorem_target_known": True,
                        "source_theorem_target_identity_status": (
                            "SOURCE_THEOREM_TARGET_KNOWN"
                        ),
                        "source_theorem_target_provenance": {
                            "source_theorem_question_id": (
                                "conformal_prediction_coverage"
                            ),
                            "target_lean_declaration": (
                                "split_conformal_coverage"
                            ),
                        },
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "target_identity_errors": [],
                        "signature_probe_artifact_path": str(candidate),
                        "candidate_artifact_path": str(candidate),
                        "execution_transcript_path": str(
                            path.parent / "transcript.jsonl"
                        ),
                        "semantic_alignment_constraints": [
                            "original source theorem alignment constraint"
                        ],
                        "semantic_alignment_blockers": [],
                        "proof_body_goal_excerpt": [
                            "Ω : Type u_1",
                            "P : MeasureTheory.Measure Ω",
                            "score : Fin (n + 1) → Ω → ℝ",
                            "hq : ∀ᵐ (ω : Ω) ∂P, True",
                            "hC : covered = {ω | score (Fin.last n) ω ≤ q}",
                            "⊢ True",
                        ],
                        "live_goal_location_ready": True,
                        "live_proof_state_request": {
                            "request_id": "live_goal:split",
                            "mcp_tool_calls": [],
                        },
                        "already_repaired_environment": {
                            "missing_formal_symbols": [],
                            "typeclass_blockers": [],
                            "signature_typecheck_reached_proof_body": True,
                        },
                        "execution_status": (
                            "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_source_binder_roles_prefer_placeholder_policy_pack() -> None:
    source_context = {
        "exact_source_theorem_binders": [
            {"name": "P", "type": "MeasureTheory.Measure Ω"},
            {"name": "n2", "type": "Nat"},
            {"name": "alpha", "type": "Fin (n2 + 1) -> ℝ"},
            {"name": "s", "type": "Fin (n2 + 1) -> Ω -> ℝ"},
            {"name": "hexch", "type": "Exchangeable P s"},
        ]
    }

    generic_roles = {
        row["name"]: row["role"]
        for row in exact_semantic_definition_source_binders_from_context(
            source_context
        )
    }
    policy_roles = {
        row["name"]: row["role"]
        for row in exact_semantic_definition_source_binders_from_context(
            source_context,
            placeholder_policy=exact_semantic_definition_placeholder_policy("alpha"),
        )
    }

    assert generic_roles["P"] == "source_parameter"
    assert policy_roles["P"] == "probability_measure_anchor"
    assert policy_roles["alpha"] == "miscoverage_level_anchor"


def test_source_anchor_fallback_roles_are_policy_driven() -> None:
    rule_roles = {
        rule.role for rule in exact_semantic_definition_source_anchor_role_rules()
    }

    assert "coverage_event_anchor" in rule_roles
    assert exact_semantic_definition_fallback_source_anchor_role(
        name="hC",
        binder_type="covered = {ω | score ω ≤ q_hat ω}",
    ) == "coverage_event_anchor"
    assert exact_semantic_definition_fallback_source_anchor_role(
        name="candidate_order_threshold",
        binder_type="q_hat = fun ω => orderStat s k ω",
    ) == "quantile_definition_anchor"
    assert exact_semantic_definition_fallback_source_anchor_role(
        name="hexch",
        binder_type="Exchangeable P s",
    ) == "exchangeability_anchor"
    assert exact_semantic_definition_fallback_source_anchor_role(
        name="arbitrary_parameter",
        binder_type="Nat",
    ) == "source_parameter"

    recovered_roles = {
        row["name"]: row["role"]
        for row in exact_semantic_definition_source_binders_from_context(
            {
                "exact_source_theorem_binders": [
                    {
                        "name": "hC",
                        "type": "covered = {ω | score ω ≤ q_hat ω}",
                    },
                    {
                        "name": "candidate_order_threshold",
                        "type": "q_hat = fun ω => orderStat s k ω",
                    },
                ]
            }
        )
    }
    assert recovered_roles["hC"] == "coverage_event_anchor"
    assert (
        recovered_roles["candidate_order_threshold"]
        == "quantile_definition_anchor"
    )


def test_exact_semantic_definition_source_lookup_exports_learning_hits(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Conformal.lean").write_text(
        "def orderStat (s : Nat) (k : Nat) := s + k\n",
        encoding="utf-8",
    )
    signature_probe_path = (
        "runs/signature_probes/split_conformal_coverage_signature_probe.lean"
    )
    _write_work_order(
        queue,
        placeholder_symbol="orderStat",
        extra={
            "proof_body_signature_probe_artifact_path": signature_probe_path,
            "candidate_definition_request": {
                "semantic_intent": "recover exact order statistic threshold"
            },
        },
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_rows_with_source_hits"] == 1
    assert manifest["n_definition_closure_review_packets_with_placeholder_policy_lineage"] == 1
    assert manifest["placeholder_policy_lineage_complete"] is True
    assert manifest["proof_evidence_status"] == "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE"
    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_DECLARATIONS_FOUND"
    assert lookup_rows[0]["placeholder_policy_id"] == (
        "split_conformal_coverage.order_statistic_threshold"
    )
    assert lookup_rows[0]["placeholder_policy_scope"] == "split_conformal_coverage"
    assert lookup_rows[0]["source_lookup_hits"][0]["candidate_kind"] == (
        "lean_declaration"
    )
    assert lookup_rows[0]["candidate_source_declarations"] == (
        lookup_rows[0]["source_lookup_hits"]
    )
    assert lookup_rows[0]["candidate_source_references"] == []
    assert lookup_rows[0]["source_semantic_alignment_review_required"] is True
    assert lookup_rows[0]["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert lookup_rows[0]["semantic_alignment_blockers"] == [
        "unreviewed synthesized definition semantic risk: "
        "draft finite maximum ignores rank k"
    ]
    assert lookup_rows[0]["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/defs_only.lean"
    )
    assert lookup_rows[0]["local_definition_lean_compiled"] is True
    assert lookup_rows[0]["semantic_definition_typecheck_evidence_status"] == (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    )
    assert lookup_rows[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert lookup_rows[0]["signature_probe_artifact_path"] == signature_probe_path
    assert lookup_rows[0]["source_theorem_signature_probe_artifact_path"] == (
        signature_probe_path
    )
    assert lookup_rows[0]["proof_body_signature_probe_artifact_path"] == (
        signature_probe_path
    )
    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    assert closure_rows[0]["artifact_kind"] == (
        "RuntimeSourceTheoremExactSemanticDefinitionClosureWorkOrder"
    )

    assert closure_rows[0]["next_step_kind"] == (
        "REVIEW_IMPORT_CANDIDATE_SOURCE_DECLARATION"
    )
    assert closure_rows[0]["source_semantic_alignment_review_required"] is True
    assert closure_rows[0]["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert closure_rows[0]["semantic_alignment_blockers"] == [
        "unreviewed synthesized definition semantic risk: "
        "draft finite maximum ignores rank k"
    ]
    assert closure_rows[0]["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/defs_only.lean"
    )
    assert closure_rows[0]["local_definition_lean_compiled"] is True
    assert closure_rows[0]["signature_probe_artifact_path"] == signature_probe_path
    assert closure_rows[0]["source_theorem_signature_probe_artifact_path"] == (
        signature_probe_path
    )
    assert closure_rows[0]["proof_body_signature_probe_artifact_path"] == (
        signature_probe_path
    )
    assert closure_rows[0]["proof_evidence_status"] == (
        "DEFINITION_CLOSURE_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert manifest["n_definition_closure_review_packets"] == 1
    assert review_packets[0]["artifact_kind"] == (
        "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewPacket"
    )
    assert review_packets[0]["definition_candidate_status"] == (
        "REQUIRES_REVIEWED_LEAN_DEFINITION"
    )
    assert review_packets[0]["source_semantic_alignment_review_required"] is True
    assert review_packets[0]["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert review_packets[0]["semantic_alignment_blockers"] == [
        "unreviewed synthesized definition semantic risk: "
        "draft finite maximum ignores rank k"
    ]
    assert review_packets[0]["definition_only_candidate_artifact_path"] == (
        "runs/candidate_artifacts/defs_only.lean"
    )
    assert review_packets[0]["local_definition_lean_compiled"] is True
    assert review_packets[0]["semantic_definition_typecheck_evidence_status"] == (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    )
    assert review_packets[0]["placeholder_policy_id"] == (
        "split_conformal_coverage.order_statistic_threshold"
    )
    assert review_packets[0]["placeholder_policy_scope"] == (
        "split_conformal_coverage"
    )
    assert review_packets[0]["signature_probe_artifact_path"] == signature_probe_path
    assert review_packets[0]["source_theorem_signature_probe_artifact_path"] == (
        signature_probe_path
    )
    assert review_packets[0]["proof_body_signature_probe_artifact_path"] == (
        signature_probe_path
    )
    assert review_packets[0]["candidate_definition_request"][
        "signature_probe_artifact_path"
    ] == signature_probe_path
    assert review_packets[0]["candidate_definition_request"][
        "source_theorem_signature_probe_artifact_path"
    ] == signature_probe_path
    assert review_packets[0]["candidate_definition_request"][
        "proof_body_signature_probe_artifact_path"
    ] == signature_probe_path
    assert "finite order statistic" in review_packets[0]["definition_contract"][
        "semantic_intent"
    ]
    assert review_packets[0]["proof_evidence_status"] == (
        "DEFINITION_CLOSURE_REVIEW_PACKET_NOT_PROOF_EVIDENCE"
    )

    memory = _load_runtime_learning_memory(
        [Path(manifest["runtime_learning_rows_jsonl"])]
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert all(
        row["placeholder_policy_id"]
        == "split_conformal_coverage.order_statistic_threshold"
        for row in learning_rows
    )
    assert all(
        row["signature_probe_artifact_path"] == signature_probe_path
        for row in learning_rows
    )
    repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {"runtime_learning_memory": memory}
    )
    assert repairs[0]["trigger"] == "EXACT_SOURCE_SEMANTIC_DEFINITION_SOURCE_LOOKUP"
    assert repairs[0]["missing_formal_symbols"] == ["orderStat"]
    assert repairs[0]["recommended_repair_tasks"] == [
        "formalize or import a reviewed exact semantic definition"
    ]
    assert repairs[0]["diagnostics"][0] == (
        "source_lookup_status=CANDIDATE_SOURCE_DECLARATIONS_FOUND"
    )
    assert repairs[0]["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert repairs[0]["semantic_alignment_blockers"] == [
        "unreviewed synthesized definition semantic risk: "
        "draft finite maximum ignores rank k"
    ]
    assert (
        "semantic_definition_typecheck="
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
        in repairs[0]["diagnostics"]
    )
    assert any(
        repair["trigger"] == "EXACT_SOURCE_SEMANTIC_DEFINITION_CLOSURE_WORK_ORDER"
        and "next_step_kind=REVIEW_IMPORT_CANDIDATE_SOURCE_DECLARATION"
        in repair["diagnostics"]
        and repair["source_theorem_target_identity_status"]
        == "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
        and repair["semantic_alignment_blockers"]
        for repair in repairs
    )
    assert any(
        repair["trigger"] == "EXACT_SOURCE_SEMANTIC_DEFINITION_CLOSURE_REVIEW_PACKET"
        and repair["definition_contract"]["semantic_intent"].startswith(
            "finite order statistic"
        )
        and repair["definition_only_candidate_artifact_path"]
        == "runs/candidate_artifacts/defs_only.lean"
        for repair in repairs
    )


def test_exact_semantic_definition_source_lookup_preserves_nested_anchor_bindings(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Conformal.lean").write_text(
        "def orderStat (score : Nat) (k : Nat) := score + k\n",
        encoding="utf-8",
    )
    nested_context = {
        "semantic_primitive": "orderStat",
        "source_anchors": [
            {
                "kind": "pseudo_formal_block",
                "id": "pf:block:order_stat",
                "excerpt": "source rank threshold block",
            }
        ],
        "source_anchor_context": [
            {
                "source": "candidate_definition_request.required_anchor_bindings",
                "kind": "required_anchor_binding",
                "required_anchor_name": "scores",
                "actual_anchor_name": "score",
                "semantic_anchor_name": "scores",
                "name": "score",
                "type": "Nat",
                "role": "score_process_anchor",
                "binder": {
                    "name": "score",
                    "type": "Nat",
                    "role": "score_process_anchor",
                },
            }
        ],
        "source_anchor_context_rows": 1,
        "candidate_definition_request": {
            "request_kind": "source_theorem_exact_semantic_definition_candidate",
            "placeholder_symbol": "orderStat",
            "required_anchor_names": ["scores"],
            "available_anchor_names": ["score", "scores"],
            "missing_required_anchor_names": [],
            "required_anchor_bindings": [
                {
                    "required_anchor_name": "scores",
                    "actual_anchor_name": "score",
                    "match_kind": "source_anchor_role",
                    "role": "score_process_anchor",
                    "binder": {
                        "name": "score",
                        "type": "Nat",
                        "role": "score_process_anchor",
                    },
                }
            ],
            "required_binders": [
                {
                    "name": "score",
                    "type": "Nat",
                    "role": "score_process_anchor",
                }
            ],
        },
    }
    _write_work_order(
        queue,
        placeholder_symbol="orderStat",
        extra={
            "input_summary": {
                "exact_semantic_definition_context": nested_context,
            },
        },
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["source_anchor_context"][0]["actual_anchor_name"] == "score"
    assert lookup_rows[0]["candidate_definition_request"][
        "required_anchor_bindings"
    ][0]["actual_anchor_name"] == "score"
    assert lookup_rows[0]["source_anchors"][0]["id"] == "pf:block:order_stat"

    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    assert closure_rows[0]["source_anchor_context"][0]["name"] == "score"
    assert closure_rows[0]["candidate_definition_request"]["required_binders"][0][
        "name"
    ] == "score"

    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert review_packets[0]["source_anchor_context_rows"] == 1
    assert review_packets[0]["source_anchor_context"][0]["actual_anchor_name"] == (
        "score"
    )
    assert review_packets[0]["candidate_definition_request"][
        "required_anchor_bindings"
    ][0]["actual_anchor_name"] == "score"


def test_exact_semantic_definition_source_lookup_uses_policy_aliases(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "AlphaBudget.lean").write_text(
        "def alphaBudget (BadRanks : Nat) (alpha : Nat) := alpha + BadRanks\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="\u03b1_total")

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    row = lookup_rows[0]

    assert row["placeholder_policy_id"] == "split_conformal_coverage.alpha_total"
    assert "alpha" in row["search_terms"]
    assert row["lookup_status"] == "CANDIDATE_SOURCE_DECLARATIONS_FOUND"
    assert row["candidate_source_declarations"][0]["match_term"] == "alpha"
    assert row["candidate_source_declarations"][0]["source_lookup_rank_reason"] == (
        "declaration_name_matches_placeholder_policy_alias"
    )


def test_exact_semantic_definition_source_lookup_preserves_placeholder_policy_lineage(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Rank.lean").write_text(
        "def rank (s : Nat) (q_hat : Nat) := s + q_hat\n",
        encoding="utf-8",
    )
    _write_work_order(
        queue,
        placeholder_symbol="rank",
        extra={
            "premise_semantic_anchor_binder_names": ["n2", "s", "q_hat", "hq"],
        },
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]

    assert manifest["n_lookup_rows_with_placeholder_policy_lineage"] == 1
    assert manifest["n_definition_closure_work_orders_with_placeholder_policy_lineage"] == 1
    assert manifest["n_definition_closure_review_packets_with_placeholder_policy_lineage"] == 1
    assert manifest["n_runtime_learning_rows_with_placeholder_policy_lineage"] == 3
    assert manifest["placeholder_policy_lineage_complete"] is True

    for row in (lookup_rows[0], closure_rows[0], review_packets[0]):
        assert row["placeholder_policy_id"] == "split_conformal_coverage.rank"
        assert row["placeholder_policy_scope"] == "split_conformal_coverage"

    for learning_task in (
        "source_theorem_exact_semantic_definition_source_lookup",
        "source_theorem_exact_semantic_definition_closure_work_order",
        "source_theorem_exact_semantic_definition_closure_review_packet",
    ):
        learning_row = next(
            row for row in learning_rows if row["learning_task"] == learning_task
        )
        assert learning_row["placeholder_policy_id"] == (
            "split_conformal_coverage.rank"
        )
        assert learning_row["input_summary"]["placeholder_policy_id"] == (
            "split_conformal_coverage.rank"
        )


def test_exact_semantic_definition_source_lookup_preserves_pseudo_formal_origin(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Blocks.lean").write_text(
        "def blk_exchangeable_setup : Prop := True\n",
        encoding="utf-8",
    )
    pseudo_formal_origin = {
        "source_materialization_seed_id": (
            "pseudo_formal_work_order:35f0c7e436caf8c7"
        ),
        "source_pseudo_formal_work_order_id": (
            "pseudo_formal_work_order:35f0c7e436caf8c7"
        ),
        "source_pseudo_formal_block_id": "blk_exchangeable_setup",
        "source_pseudo_formal_packet_id": "pseudo_formal_packet:split",
        "source_pseudo_formal_prompt_scaffold_origin": {
            "artifact_kind": "PseudoFormalPromptScaffoldOrigin",
            "scaffold_kind": "pseudo_formalization_required_copy_fragment",
            "source": "FormalizerPrompt",
            "required_output_key": "pseudo_formal_proof_packets",
            "copy_fragment_id": "pseudo_formal_copy_fragment:exchangeable",
            "proof_evidence_status": (
                "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
            ),
        },
        "source_prompt_scaffold_kind": (
            "pseudo_formalization_required_copy_fragment"
        ),
        "source_prompt_scaffold_id": "pseudo_formal_copy_fragment:exchangeable",
        "source_prompt_scaffold_required_output_key": (
            "pseudo_formal_proof_packets"
        ),
        "source_formalizer_proposal_id": "formalizer_proposal:split",
        "source_formalizer_proposal_without_formalization_manifest": True,
        "pseudo_formal_method_contract_id": (
            "pseudo_formalization_block_verification_calibration_v1"
        ),
        "pseudo_formal_pipeline_stage": "pseudo_formal_block_routing",
        "pseudo_formal_proof_evidence_status": (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        ),
        "proof_evidence_status": (
            "WORK_ORDER_FROM_PSEUDO_FORMAL_NOT_PROOF_EVIDENCE"
        ),
        "semantic_primitive": "exchangeable_setup",
        "semantic_primitive_requirements": ["exchangeable_setup"],
        "source_block_semantic_primitive_requirements": [
            "exchangeable_setup",
            "rank_uniformity",
        ],
        "source_anchors": [
            {
                "kind": "pseudo_formal_block",
                "id": "blk_exchangeable_setup",
                "excerpt": "exchangeable setup",
            }
        ],
    }
    _write_work_order(
        queue,
        placeholder_symbol="blk_exchangeable_setup",
        extra=pseudo_formal_origin,
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]

    assert manifest["n_definition_closure_review_packets"] == 1
    assert manifest["n_work_orders_from_pseudo_formal"] == 1
    assert manifest["n_lookup_rows_from_pseudo_formal"] == 1
    assert manifest["n_definition_closure_work_orders_from_pseudo_formal"] == 1
    assert manifest["n_definition_closure_review_packets_from_pseudo_formal"] == 1
    assert manifest["n_runtime_learning_rows_from_pseudo_formal"] == 3
    assert manifest["source_pseudo_formal_work_order_ids"] == [
        "pseudo_formal_work_order:35f0c7e436caf8c7"
    ]
    assert manifest["source_pseudo_formal_block_ids"] == [
        "blk_exchangeable_setup"
    ]
    assert manifest["source_prompt_scaffold_ids"] == [
        "pseudo_formal_copy_fragment:exchangeable"
    ]
    assert manifest["source_prompt_scaffold_kinds"] == [
        "pseudo_formalization_required_copy_fragment"
    ]
    assert manifest["source_pseudo_formal_placeholder_symbols"] == [
        "blk_exchangeable_setup"
    ]
    assert manifest["source_pseudo_formal_semantic_primitives"] == [
        "exchangeable_setup"
    ]
    assert manifest["source_pseudo_formal_semantic_primitive_requirements"] == [
        "exchangeable_setup",
        "rank_uniformity",
    ]
    assert manifest["pseudo_formal_origin_lineage_complete"] is True
    for row in [lookup_rows[0], closure_rows[0], review_packets[0], *learning_rows]:
        assert row["source_pseudo_formal_work_order_id"] == (
            "pseudo_formal_work_order:35f0c7e436caf8c7"
        )
        assert row["source_pseudo_formal_block_id"] == "blk_exchangeable_setup"
        assert row["source_pseudo_formal_packet_id"] == "pseudo_formal_packet:split"
        assert row["source_pseudo_formal_prompt_scaffold_origin"][
            "scaffold_kind"
        ] == "pseudo_formalization_required_copy_fragment"
        assert row["source_prompt_scaffold_id"] == (
            "pseudo_formal_copy_fragment:exchangeable"
        )
        assert row["source_prompt_scaffold_required_output_key"] == (
            "pseudo_formal_proof_packets"
        )
        assert row["source_formalizer_proposal_id"] == "formalizer_proposal:split"
        assert row["pseudo_formal_method_contract_id"] == (
            "pseudo_formalization_block_verification_calibration_v1"
        )
        assert row["pseudo_formal_pipeline_stage"] == "pseudo_formal_block_routing"
        assert row["pseudo_formal_proof_evidence_status"] == (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        )
        assert row["semantic_primitive"] == "exchangeable_setup"
        assert row["semantic_primitive_requirements"] == ["exchangeable_setup"]
        assert row["source_block_semantic_primitive_requirements"] == [
            "exchangeable_setup",
            "rank_uniformity",
        ]
        assert row["source_anchors"] == [
            {
                "kind": "pseudo_formal_block",
                "id": "blk_exchangeable_setup",
                "excerpt": "exchangeable setup",
            }
        ]
        assert "KERNEL_VERIFIED" not in row["proof_evidence_status"]
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, dict) and input_summary:
            assert input_summary["source_pseudo_formal_work_order_id"] == (
                "pseudo_formal_work_order:35f0c7e436caf8c7"
            )
            assert input_summary["source_pseudo_formal_block_id"] == (
                "blk_exchangeable_setup"
            )
            assert input_summary["source_prompt_scaffold_id"] == (
                "pseudo_formal_copy_fragment:exchangeable"
            )
            assert input_summary[
                "source_prompt_scaffold_required_output_key"
            ] == "pseudo_formal_proof_packets"
            assert input_summary["semantic_primitive"] == "exchangeable_setup"
            assert input_summary["semantic_primitive_requirements"] == [
                "exchangeable_setup"
            ]
            assert input_summary["source_block_semantic_primitive_requirements"] == [
                "exchangeable_setup",
                "rank_uniformity",
            ]


def test_exact_semantic_definition_source_lookup_preserves_formalizer_pf_component_gate_origin(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Coverage.lean").write_text(
        "def coverage_event : Prop := True\n",
        encoding="utf-8",
    )
    exact_rows_jsonl = "runs/formalizer_pf/exact_semantic_definition_rows.jsonl"
    _write_work_order(
        queue,
        placeholder_symbol="coverage_event",
        extra={
            "source_component_gate": (
                "formalizer_pseudo_formal_packet_component_gate"
            ),
            "source_component_gate_exact_rows_jsonl": exact_rows_jsonl,
            "component_eval_manifest_path": "runs/formalizer_pf/manifest.json",
            "provider_name": "anthropic",
            "backend_provider_name": "anthropic",
            "proof_evidence_status": (
                "WORK_ORDER_FROM_FORMALIZER_PF_COMPONENT_GATE_NOT_PROOF_EVIDENCE"
            ),
            "semantic_primitive": "coverage_event",
            "semantic_primitive_requirements": ["coverage_event"],
        },
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]

    assert manifest["n_work_orders_from_pseudo_formal"] == 1
    assert manifest["n_work_orders_from_formalizer_pf_component_gate"] == 1
    assert manifest["n_lookup_rows_from_pseudo_formal"] == 1
    assert manifest["n_lookup_rows_from_formalizer_pf_component_gate"] == 1
    assert manifest[
        "n_definition_closure_work_orders_from_formalizer_pf_component_gate"
    ] == 1
    assert manifest[
        "n_definition_closure_review_packets_from_formalizer_pf_component_gate"
    ] == 1
    assert manifest["n_runtime_learning_rows_from_pseudo_formal"] == 3
    assert manifest[
        "n_runtime_learning_rows_from_formalizer_pf_component_gate"
    ] == 3
    assert manifest["pseudo_formal_origin_lineage_complete"] is True
    assert manifest["formalizer_pf_component_gate_exact_rows_jsonl_paths"] == [
        exact_rows_jsonl
    ]
    assert manifest["source_pseudo_formal_placeholder_symbols"] == [
        "coverage_event"
    ]
    assert manifest["source_pseudo_formal_semantic_primitives"] == [
        "coverage_event"
    ]

    for row in [lookup_rows[0], closure_rows[0], review_packets[0], *learning_rows]:
        assert (
            row["source_component_gate"]
            == "formalizer_pseudo_formal_packet_component_gate"
        )
        assert row["source_component_gate_exact_rows_jsonl"] == exact_rows_jsonl
        assert row["component_eval_manifest_path"] == (
            "runs/formalizer_pf/manifest.json"
        )
        assert row["semantic_primitive"] == "coverage_event"
        assert row["semantic_primitive_requirements"] == ["coverage_event"]
        assert "KERNEL_VERIFIED" not in row["proof_evidence_status"]
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, dict) and input_summary:
            assert input_summary["source_component_gate"] == (
                "formalizer_pseudo_formal_packet_component_gate"
            )
            assert (
                input_summary["source_component_gate_exact_rows_jsonl"]
                == exact_rows_jsonl
            )


def test_exact_semantic_definition_source_lookup_ignores_generated_cache_dirs(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Repo"
    stale_root = source_root / ".tmp_publish" / "legacy_sources"
    current_root = source_root / "StatInference"
    stale_root.mkdir(parents=True)
    current_root.mkdir(parents=True)
    (stale_root / "Stale.lean").write_text(
        "def orderStat (s : Nat) (k : Nat) := 0\n",
        encoding="utf-8",
    )
    (current_root / "Current.lean").write_text(
        "def orderStatReviewed (s : Nat) (k : Nat) := s + k\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="orderStat")

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    assert manifest["n_rows_with_source_hits"] == 1
    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    hit_paths = [hit["path"] for hit in lookup_rows[0]["source_lookup_hits"]]
    assert any("StatInference/Current.lean" in path for path in hit_paths)
    assert all(".tmp_publish" not in path for path in hit_paths)


def test_exact_semantic_definition_source_lookup_keeps_sample_mean_as_reference_not_import(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    asymptotic_root = source_root / "AsymptoticStatistics"
    asymptotic_root.mkdir(parents=True)
    (asymptotic_root / "Bootstrap.lean").write_text(
        "def vaart1998_quantileConfidenceIntervalEvent := True\n",
        encoding="utf-8",
    )
    (asymptotic_root / "LStatistics.lean").write_text(
        "def vaart1998_orderStatisticSampleMean (n i : Nat) := n + i\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="orderStat")

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=1,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_REFERENCES_FOUND"
    assert lookup_rows[0]["candidate_source_declarations"] == []
    assert len(lookup_rows[0]["candidate_source_references"]) == 1
    hit = lookup_rows[0]["candidate_source_references"][0]
    assert hit["path"].endswith("StatInference/AsymptoticStatistics/LStatistics.lean")
    assert hit["match_term"] == "orderstat"
    assert hit["source_lookup_rank"] == 1
    assert hit["source_lookup_rank_reason"] == (
        "declaration_name_matches_primary_placeholder"
    )
    assert hit["semantic_import_candidate_allowed"] is False
    assert hit["source_semantic_review_status"] == (
        "SEMANTIC_MISMATCH_NOT_EXACT_ORDER_STATISTIC"
    )


def test_exact_semantic_definition_source_lookup_prefers_rank_quantile_import_over_bootstrap(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    asymptotic_root = source_root / "AsymptoticStatistics"
    asymptotic_root.mkdir(parents=True)
    (asymptotic_root / "Bootstrap.lean").write_text(
        "def vaart1998_quantileConfidenceIntervalEvent := True\n",
        encoding="utf-8",
    )
    (asymptotic_root / "ConformalQuantile.lean").write_text(
        "def conformalQuantile (scores : Nat) (k : Nat) := scores + k\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="orderStat")

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=1,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_DECLARATIONS_FOUND"
    assert len(lookup_rows[0]["candidate_source_declarations"]) == 1
    hit = lookup_rows[0]["candidate_source_declarations"][0]
    assert hit["path"].endswith(
        "StatInference/AsymptoticStatistics/ConformalQuantile.lean"
    )
    assert hit["semantic_import_candidate_allowed"] is True
    assert hit["source_semantic_review_status"] == (
        "SEMANTIC_IMPORT_CANDIDATE_REQUIRES_REVIEW"
    )


def test_exact_semantic_definition_source_lookup_demotes_weak_contextual_declarations(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    source_root.mkdir()
    (source_root / "FiniteCellCoverage.lean").write_text(
        "\n".join(
            [
                "-- split coverage sample context from an unrelated Wald module",
                "theorem finiteScoreCellWeightedSampleCoverage : True := by trivial",
                "def PATEFiniteScoreCellWaldBridgeOfAbsoluteCoverage := True",
            ]
        ),
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                ),
                "work_order_id": (
                    "source_theorem_exact_semantic_definition_work_order:"
                    "rank_uniformity_block"
                ),
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_finite_sample_coverage",
                "placeholder_symbol": "rank_uniformity_block",
                "replacement_strategy": (
                    "review_or_author_exact_semantic_definition_from_pseudo_formal_block"
                ),
                "search_targets": [
                    "rank",
                    "uniformity",
                    "split",
                    "conformal",
                    "finite",
                    "sample",
                    "coverage",
                    "exchangeable",
                ],
                "semantic_alignment_blockers": [
                    "rank uniformity under exchangeability is still unlocated"
                ],
                "proof_evidence_status": (
                    "WORK_ORDER_FROM_PSEUDO_FORMAL_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=3,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_REFERENCES_FOUND"
    assert lookup_rows[0]["candidate_source_declarations"] == []
    assert lookup_rows[0]["candidate_source_references"]
    declaration_references = [
        hit
        for hit in lookup_rows[0]["candidate_source_references"]
        if hit["candidate_kind"] == "lean_declaration"
    ]
    assert declaration_references
    assert {
        hit["source_semantic_review_status"]
        for hit in declaration_references
    } == {"SEMANTIC_REVIEW_REQUIRED_WEAK_CONTEXTUAL_DECLARATION_MATCH"}
    assert all(
        hit["semantic_import_candidate_allowed"] is False
        for hit in declaration_references
    )


def test_exact_semantic_definition_source_lookup_allows_exact_target_alias_declaration(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    source_root.mkdir()
    (source_root / "SplitConformal.lean").write_text(
        "theorem split_conformal_finite_sample_coverage : True := by trivial\n",
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                ),
                "work_order_id": (
                    "source_theorem_exact_semantic_definition_work_order:"
                    "coverage_event_bridge_block"
                ),
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_finite_sample_coverage",
                "placeholder_symbol": "coverage_event_bridge_block",
                "replacement_strategy": (
                    "review_or_author_exact_semantic_definition_from_pseudo_formal_block"
                ),
                "search_targets": [
                    "coverage",
                    "event",
                    "bridge",
                    "split_conformal_finite_sample_coverage",
                ],
                "proof_evidence_status": (
                    "WORK_ORDER_FROM_PSEUDO_FORMAL_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=1,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_DECLARATIONS_FOUND"
    assert len(lookup_rows[0]["candidate_source_declarations"]) == 1
    assert lookup_rows[0]["candidate_source_declarations"][0][
        "semantic_import_candidate_allowed"
    ] is True


def test_typechecked_candidate_lookup_exports_review_candidate_next_step(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    source_root.mkdir()
    queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                ),
                "work_order_id": "exact-semantic-definition:orderStat",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "orderStat",
                "definition_only_candidate_artifact_path": (
                    "runs/materialized_orderStat_definition.lean"
                ),
                "local_definition_lean_compiled": True,
                "semantic_definition_typecheck_evidence_status": (
                    "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                ),
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=1,
    )

    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    assert closure_rows[0]["next_step_kind"] == (
        "REVIEW_TYPECHECKED_EXACT_DEFINITION_CANDIDATE"
    )
    assert closure_rows[0]["definition_only_candidate_artifact_path"] == (
        "runs/materialized_orderStat_definition.lean"
    )
    assert closure_rows[0]["local_definition_lean_compiled"] is True
    assert closure_rows[0]["semantic_definition_typecheck_evidence_status"] == (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    )
    assert closure_rows[0]["proof_evidence_status"] == (
        "DEFINITION_CLOSURE_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )


def test_source_to_bridge_adapter_object_lookup_keeps_declarations_as_references(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    source_root.mkdir()
    (source_root / "AdapterNoise.lean").write_text(
        "\n".join(
            [
                "def alphaBudgetNoise (alpha : Nat) := alpha",
                "def coveredNoise (x : Nat) := x",
            ]
        ),
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                ),
                "work_order_id": (
                    "source_to_bridge_adapter_object_semantic_definition_work_order:"
                    "covered"
                ),
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "replacement_strategy": (
                    "instantiate_source_to_bridge_adapter_object_from_exact_source_binders"
                ),
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION"
                ),
                "source_to_bridge_adapter_instantiation_group_id": (
                    "source_to_bridge_adapter_instantiation_group:test"
                ),
                "search_targets": ["covered", "alpha", "hC"],
                "proof_evidence_status": (
                    "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=2,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_REFERENCES_FOUND"
    assert lookup_rows[0]["candidate_source_declarations"] == []
    assert len(lookup_rows[0]["candidate_source_references"]) == 2
    assert {
        hit["source_semantic_review_status"]
        for hit in lookup_rows[0]["candidate_source_references"]
    } == {"SOURCE_TO_BRIDGE_ADAPTER_OBJECT_REQUIRES_SYNTHESIS"}
    closure_work_orders = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    assert closure_work_orders[0]["next_step_kind"] == (
        "SYNTHESIZE_REVIEWED_DEFINITION_FROM_SOURCE_REFERENCES"
    )


def test_source_to_bridge_adapter_object_lookup_prefers_contextual_source(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    source_root.mkdir()
    (source_root / "GenericCoverage.lean").write_text(
        "\n".join(
            [
                "def coveredNoise (x : Nat) := x",
                "def alphaBudgetNoise (alpha : Nat) := alpha",
            ]
        ),
        encoding="utf-8",
    )
    (source_root / "SplitConformalAdapterObjects.lean").write_text(
        "\n".join(
            [
                "theorem split_conformal_coverage : True := by trivial",
                "-- hGoodCovered hRank hC identify source-to-bridge premises.",
                "def coveredFromSplitConformal (x : Nat) := x",
            ]
        ),
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                ),
                "work_order_id": (
                    "source_to_bridge_adapter_object_semantic_definition_work_order:"
                    "covered"
                ),
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "replacement_strategy": (
                    "instantiate_source_to_bridge_adapter_object_from_exact_source_binders"
                ),
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION"
                ),
                "source_to_bridge_adapter_instantiation_group_id": (
                    "source_to_bridge_adapter_instantiation_group:test"
                ),
                "search_targets": [
                    "covered",
                    "split_conformal_coverage",
                    "hGoodCovered",
                    "hRank",
                    "hC",
                ],
                "proof_evidence_status": (
                    "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=2,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_REFERENCES_FOUND"
    assert lookup_rows[0]["candidate_source_declarations"] == []
    top_hit = lookup_rows[0]["candidate_source_references"][0]
    assert top_hit["path"].endswith("SplitConformalAdapterObjects.lean")
    assert top_hit["source_lookup_context_score"] > 0
    assert "split_conformal_coverage" in top_hit["file_matched_terms"]
    assert "hgoodcovered" in top_hit["file_matched_terms"]
    assert top_hit["semantic_import_candidate_allowed"] is False
    assert top_hit["source_semantic_review_status"] == (
        "SOURCE_TO_BRIDGE_ADAPTER_OBJECT_REQUIRES_SYNTHESIS"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["proof_evidence_status"] == (
        "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE"
    )


def test_source_to_bridge_adapter_object_lookup_filters_generic_binder_noise(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    source_root.mkdir()
    (source_root / "GenericAlphaOnly.lean").write_text(
        "\n".join(
            [
                "-- recovered from an unrelated optimization theorem.",
                "def unrelatedAlphaBound (hn2 : Nat) (alpha halpha : Nat) := alpha",
                "lemma unrelatedEndpointCorrection (alpha : Nat) : True := by trivial",
            ]
        ),
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                ),
                "work_order_id": (
                    "source_to_bridge_adapter_object_semantic_definition_work_order:"
                    "covered"
                ),
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "replacement_strategy": (
                    "instantiate_source_to_bridge_adapter_object_from_exact_source_binders"
                ),
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION"
                ),
                "source_to_bridge_adapter_instantiation_group_id": (
                    "source_to_bridge_adapter_instantiation_group:test"
                ),
                "search_targets": [
                    "covered",
                    "split_conformal_coverage",
                    "hGoodCovered",
                    "hRank",
                    "n2",
                    "hn2",
                    "alpha",
                    "halpha",
                ],
                "proof_evidence_status": (
                    "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=4,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "NO_REVIEWED_FORMAL_DEFINITION_FOUND"
    assert lookup_rows[0]["source_lookup_hits"] == []
    assert manifest["n_rows_with_source_hits"] == 0
    assert manifest["proof_evidence_status"] == "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE"


def test_source_to_bridge_adapter_object_source_text_hit_uses_adapter_status(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "StatInference"
    source_root.mkdir()
    (source_root / "CoveringPrimitive.lean").write_text(
        "-- covered event context for split_conformal_coverage.\n",
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                ),
                "work_order_id": (
                    "source_to_bridge_adapter_object_semantic_definition_work_order:"
                    "covered"
                ),
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "replacement_strategy": (
                    "instantiate_source_to_bridge_adapter_object_from_exact_source_binders"
                ),
                "runtime_queue_status": (
                    "PENDING_SOURCE_TO_BRIDGE_ADAPTER_OBJECT_SEMANTIC_DEFINITION"
                ),
                "source_to_bridge_adapter_instantiation_group_id": (
                    "source_to_bridge_adapter_instantiation_group:test"
                ),
                "search_targets": ["covered", "split_conformal_coverage"],
                "proof_evidence_status": (
                    "ADAPTER_OBJECT_SEMANTIC_DEFINITION_WORK_ORDER_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
        max_hits_per_work_order=1,
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    hit = lookup_rows[0]["candidate_source_references"][0]
    assert hit["candidate_kind"] == "lean_source_text_match"
    assert hit["source_semantic_review_status"] == (
        "SOURCE_TO_BRIDGE_ADAPTER_OBJECT_REQUIRES_SYNTHESIS"
    )
    assert hit["semantic_import_candidate_allowed"] is False


def test_exact_semantic_definition_source_lookup_keeps_no_hit_nonproof(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Other.lean").write_text(
        "def unrelatedPrimitive := True\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="Exchangeable")

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    assert manifest["n_rows_with_source_hits"] == 0
    assert manifest["lookup_status_counts"] == {
        "NO_REVIEWED_FORMAL_DEFINITION_FOUND": 1
    }
    assert manifest["n_definition_closure_work_orders"] == 1
    assert manifest["n_definition_closure_review_packets"] == 1
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["lookup_status"] == "NO_REVIEWED_FORMAL_DEFINITION_FOUND"
    assert learning_rows[0]["proof_evidence_status"] == (
        "SOURCE_LOOKUP_NOT_PROOF_EVIDENCE"
    )
    assert learning_rows[0]["source_theorem_semantic_support_only"] is True
    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    assert closure_rows[0]["next_step_kind"] == (
        "SYNTHESIZE_MINIMAL_EXACT_DEFINITION_WITH_SOURCE_REVIEW"
    )
    assert closure_rows[0]["proof_evidence_status"] == (
        "DEFINITION_CLOSURE_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert review_packets[0]["definition_contract"]["forbidden_shortcuts"] == [
        "do not define Exchangeable as True",
        "do not add axiom/sorry/admit/unsafe",
        "do not assume the split_conformal_coverage target theorem",
    ]


def test_exact_semantic_definition_source_lookup_separates_source_references(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Conformal.lean").write_text(
        "-- Exchangeability assumption used by the conformal coverage proof.\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="Exchangeable")

    manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )

    lookup_rows = [
        json.loads(line)
        for line in Path(manifest["lookup_rows_jsonl"]).read_text().splitlines()
    ]
    assert lookup_rows[0]["lookup_status"] == "CANDIDATE_SOURCE_REFERENCES_FOUND"
    assert lookup_rows[0]["candidate_source_declarations"] == []
    assert lookup_rows[0]["candidate_source_references"][0]["candidate_kind"] == (
        "lean_source_text_match"
    )
    closure_rows = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_work_orders_jsonl"]
        ).read_text().splitlines()
    ]
    assert closure_rows[0]["next_step_kind"] == (
        "SYNTHESIZE_REVIEWED_DEFINITION_FROM_SOURCE_REFERENCES"
    )
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["definition_closure_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert review_packets[0]["required_next_checks"][1] == (
        "write or import the exact Lean definition that replaces the placeholder"
    )


def test_exact_semantic_definition_closure_review_rejects_forbidden_placeholders(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Conformal.lean").write_text(
        "-- Exchangeability assumption used by the conformal coverage proof.\n"
        "-- quantile construction will be reviewed later.\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="Exchangeable")
    with queue.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "schema_version": 1,
                    "artifact_kind": (
                        "RuntimeSourceTheoremExactSemanticDefinitionWorkOrder"
                    ),
                    "work_order_id": (
                        "source_theorem_exact_semantic_definition_work_order:"
                        "orderStat"
                    ),
                    "question_id": "conformal_prediction_coverage",
                    "target_theorem_name": "split_conformal_coverage",
                    "placeholder_symbol": "orderStat",
                    "replacement_strategy": (
                        "formalize or import a reviewed exact semantic definition"
                    ),
                    "search_targets": ["quantile"],
                    "candidate_registered_obligation_ids": [
                        "split_conformal_good_rank_set_inclusion_bridge"
                    ],
                    "kernel_verified_source_theorem_semantic_support_obligation_ids": [
                        "split_conformal_good_rank_set_inclusion_bridge"
                    ],
                    "kernel_verified_source_theorem_semantic_definition_ids": [],
                    "semantic_closure_status": (
                        "REGISTERED_SUPPORT_VERIFIED_PLACEHOLDER_DEFINITION_OPEN"
                    ),
                    "placeholder_definition_status": (
                        "OPEN_REQUIRES_REVIEWED_FORMAL_DEFINITION"
                    ),
                    "source_theorem_ready_for_exact_proof_body": False,
                    "source_theorem_semantic_support_only": True,
                    "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
                }
            )
            + "\n"
        )
    lookup_manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "def Exchangeable {Ω : Type} (P : Sort _) (s : Nat -> Ω -> Nat) : Prop := True\n"
        "def orderStat {Ω : Type} (s : Nat -> Ω -> Nat) (k : Nat) (ω : Ω) : Nat := 0\n",
        encoding="utf-8",
    )

    review_manifest = run_source_theorem_exact_semantic_definition_closure_review(
        out_dir=tmp_path / "review",
        lookup_manifest=Path(lookup_manifest["manifest_path"]),
        candidate_artifact_path=candidate,
    )

    assert review_manifest["n_review_packets"] == 2
    assert review_manifest["n_forbidden_placeholder_definitions"] == 2
    assert review_manifest["n_ready_for_definition_lean_check"] == 0
    assert review_manifest["proof_evidence_status"] == (
        "DEFINITION_CLOSURE_REVIEW_RESULT_NOT_PROOF_EVIDENCE"
    )
    rows = [
        json.loads(line)
        for line in Path(review_manifest["review_results_jsonl"]).read_text().splitlines()
    ]
    assert {row["placeholder_symbol"] for row in rows} == {
        "Exchangeable",
        "orderStat",
    }
    assert all(
        row["review_status"] == "FORBIDDEN_PLACEHOLDER_DEFINITION_FOUND"
        for row in rows
    )
    assert all(row["forbidden_placeholder_detected"] is True for row in rows)
    matches_by_symbol = {
        row["placeholder_symbol"]: [
            match["kind"] for match in row["forbidden_placeholder_matches"]
        ]
        for row in rows
    }
    assert matches_by_symbol == {
        "Exchangeable": ["defined_as_true"],
        "orderStat": ["defined_as_zero"],
    }
    exchangeability_row = next(
        row for row in rows if row["placeholder_symbol"] == "Exchangeable"
    )
    assert exchangeability_row["source_semantic_alignment_review_required"] is True
    assert exchangeability_row["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert exchangeability_row["semantic_alignment_blockers"] == [
        "unreviewed synthesized definition semantic risk: "
        "draft finite maximum ignores rank k"
    ]
    assert any(
        "replace forbidden `Exchangeable` placeholder definition"
        in row["recommended_repair_tasks"][0]
        for row in rows
    )
    memory = _load_runtime_learning_memory(
        [Path(review_manifest["runtime_learning_rows_jsonl"])]
    )
    repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {"runtime_learning_memory": memory}
    )
    assert any(
        repair["trigger"]
        == "EXACT_SOURCE_SEMANTIC_DEFINITION_CLOSURE_REVIEW_RESULT"
        and "forbidden_placeholder_definition_detected=true"
        in repair["diagnostics"]
        and repair["source_theorem_target_identity_status"]
        == "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
        and repair["semantic_alignment_blockers"]
        for repair in repairs
    )


def test_exact_semantic_definition_closure_review_flags_semantic_risk(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Conformal.lean").write_text(
        "-- Exchangeability and conformal quantile source references.\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="Exchangeable")
    with queue.open("a", encoding="utf-8") as handle:
        order_stat_row = json.loads(queue.read_text(encoding="utf-8").splitlines()[0])
        order_stat_row["work_order_id"] = (
            "source_theorem_exact_semantic_definition_work_order:orderStat"
        )
        order_stat_row["placeholder_symbol"] = "orderStat"
        order_stat_row["search_targets"] = ["quantile"]
        handle.write(json.dumps(order_stat_row) + "\n")
    lookup_manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n"
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fin.Basic\n"
        "import Mathlib.Data.Finset.Basic\n"
        "def Exchangeable {Ω : Type _} [MeasurableSpace Ω] {ι : Type _}\n"
        "    (P : MeasureTheory.Measure Ω) (s : ι → Ω → ℝ) : Prop :=\n"
        "  ∀ i j : ι, P.real {ω | s i ω ≤ s j ω} = P.real {ω | s j ω ≤ s i ω}\n"
        "def orderStat {Ω : Type _} {m : ℕ}\n"
        "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ :=\n"
        "  (Finset.univ.image (fun i : Fin (m + 1) => s i ω)).max' (by\n"
        "    classical\n"
        "    simp)\n",
        encoding="utf-8",
    )

    review_manifest = run_source_theorem_exact_semantic_definition_closure_review(
        out_dir=tmp_path / "review",
        lookup_manifest=Path(lookup_manifest["manifest_path"]),
        candidate_artifact_path=candidate,
    )

    assert review_manifest["n_review_results"] == 2
    assert review_manifest["n_forbidden_placeholder_definitions"] == 0
    assert review_manifest["n_ready_for_definition_lean_check"] == 0
    assert review_manifest["review_status_counts"] == {
        "CANDIDATE_DEFINITION_SEMANTIC_RISK_FOUND": 2
    }
    rows = [
        json.loads(line)
        for line in Path(review_manifest["review_results_jsonl"]).read_text().splitlines()
    ]
    risks_by_symbol = {
        row["placeholder_symbol"]: row["semantic_definition_risks"]
        for row in rows
    }
    assert any("pairwise" in risk for risk in risks_by_symbol["Exchangeable"])
    assert any("finite maximum" in risk for risk in risks_by_symbol["orderStat"])
    assert all(row["semantic_definition_risk_detected"] is True for row in rows)
    assert all(row["ready_for_definition_lean_check"] is False for row in rows)
    assert all(
        row["review_status"] == "CANDIDATE_DEFINITION_SEMANTIC_RISK_FOUND"
        for row in rows
    )
    assert all(
        "replace or import reviewed exact" in row["recommended_repair_tasks"][0]
        for row in rows
    )
    memory = _load_runtime_learning_memory(
        [Path(review_manifest["runtime_learning_rows_jsonl"])]
    )
    repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {"runtime_learning_memory": memory}
    )
    assert any(
        repair["trigger"]
        == "EXACT_SOURCE_SEMANTIC_DEFINITION_CLOSURE_REVIEW_RESULT"
        and any("semantic_definition_risk=" in value for value in repair["diagnostics"])
        and repair["semantic_definition_risks"]
        for repair in repairs
    )
    proof_body_queue_manifest = tmp_path / "proof_body_queue_manifest.json"
    proof_body_queue_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:semantic_risk",
                        "source_work_order_id": "proof_body_work_order:semantic_risk",
                        "target_theorem_name": "split_conformal_coverage",
                        "target_lean_declaration": "split_conformal_coverage",
                        "expected_target_lean_declaration": "split_conformal_coverage",
                        "source_theorem_target_known": True,
                        "source_candidate_artifact_path": str(candidate),
                        "signature_probe_artifact_path": str(candidate),
                        "candidate_artifact_path": str(tmp_path / "attempt.lean"),
                        "execution_transcript_path": str(tmp_path / "attempt.jsonl"),
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "target_identity_errors": [],
                        "live_goal_location_ready": True,
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    synthesis_manifest = run_source_theorem_exact_semantic_definition_candidate_synthesis(
        out_dir=tmp_path / "synthesis",
        review_manifest=Path(review_manifest["manifest_path"]),
        candidate_artifact_path=candidate,
        proof_body_queue_manifest=proof_body_queue_manifest,
        lean_project=tmp_path / "lean_project",
    )

    assert synthesis_manifest["n_replacements_applied"] == 0
    assert synthesis_manifest["n_proof_body_recheck_queue_rows"] == 0
    assert synthesis_manifest["n_semantic_definition_repair_queue_rows"] == 2
    assert synthesis_manifest["semantic_definition_repair_queue_proof_evidence_status"] == (
        "SEMANTIC_DEFINITION_REPAIR_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert synthesis_manifest["synthesis_status_counts"] == {
        "DEFINITION_REVIEW_SEMANTIC_RISK_BLOCKED": 2
    }
    repair_queue_manifest = json.loads(
        Path(str(synthesis_manifest["semantic_definition_repair_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert repair_queue_manifest["n_repair_queue_rows"] == 2
    assert repair_queue_manifest["n_ready"] == 2
    assert repair_queue_manifest["source_theorem_kernel_evidence_eligible"] is False
    assert repair_queue_manifest["proof_evidence_status"] == (
        "SEMANTIC_DEFINITION_REPAIR_QUEUE_NOT_PROOF_EVIDENCE"
    )
    repair_rows = [
        json.loads(line)
        for line in Path(
            str(synthesis_manifest["semantic_definition_repair_queue_jsonl"])
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert {row["placeholder_symbol"] for row in repair_rows} == {
        "Exchangeable",
        "orderStat",
    }
    assert all(
        row["action_type"] == "repair_reviewed_exact_semantic_definition"
        for row in repair_rows
    )
    assert all(
        row["repair_status"]
        == "READY_FOR_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR"
        for row in repair_rows
    )
    assert all(row["source_theorem_kernel_evidence_eligible"] is False for row in repair_rows)
    assert all(
        row["proof_evidence_status"]
        == "SEMANTIC_DEFINITION_REPAIR_QUEUE_NOT_PROOF_EVIDENCE"
        for row in repair_rows
    )
    assert any(
        "pairwise" in risk
        for row in repair_rows
        for risk in row["semantic_definition_risks"]
    )
    assert any(
        "finite maximum" in risk
        for row in repair_rows
        for risk in row["semantic_definition_risks"]
    )
    recheck_manifest = json.loads(
        Path(str(synthesis_manifest["proof_body_recheck_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert recheck_manifest["proof_body_recheck_blocked"] is True
    assert recheck_manifest["proof_body_recheck_blocker"] == (
        "semantic_definition_review_blocked"
    )
    assert recheck_manifest["n_execution_queue_rows"] == 0
    assert recheck_manifest["n_ready"] == 0
    assert recheck_manifest["n_semantic_definition_review_blocked_rows"] == 2
    assert recheck_manifest["definition_candidate_review_modes"] == [
        "semantic_review_blocked_existing_candidate"
    ]
    assert any(
        "finite maximum" in risk for risk in recheck_manifest["semantic_definition_risks"]
    )
    assert any(
        "Finset.image" in risk for risk in recheck_manifest["semantic_definition_risks"]
    )
    synthesis_memory = _load_runtime_learning_memory(
        [Path(synthesis_manifest["runtime_learning_rows_jsonl"])]
    )
    synthesis_repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {"runtime_learning_memory": synthesis_memory}
    )
    assert any(
        repair["trigger"] == "EXACT_SOURCE_SEMANTIC_DEFINITION_REPAIR_QUEUE"
        and repair["placeholder_symbol"] == "Exchangeable"
        and repair["source_theorem_kernel_evidence_eligible"] is False
        and repair["semantic_definition_risks"]
        for repair in synthesis_repairs
    )
    assert any(
        repair["trigger"] == "EXACT_SOURCE_SEMANTIC_DEFINITION_REPAIR_QUEUE"
        and repair["placeholder_symbol"] == "orderStat"
        and repair["source_theorem_kernel_evidence_eligible"] is False
        and repair["semantic_definition_risks"]
        for repair in synthesis_repairs
    )


def test_exact_semantic_definition_candidate_synthesis_can_opt_into_draft_semantic_repair(
    tmp_path: Path,
) -> None:
    review_results = tmp_path / "review_results.jsonl"
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n"
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fin.Basic\n"
        "import Mathlib.Data.Finset.Basic\n"
        "noncomputable section\n"
        "def Exchangeable {Ω : Type _} [MeasurableSpace Ω] {ι : Type _}\n"
        "    (P : MeasureTheory.Measure Ω) (s : ι → Ω → ℝ) : Prop :=\n"
        "  ∀ i j : ι, P.real {ω | s i ω ≤ s j ω} = P.real {ω | s j ω ≤ s i ω}\n"
        "def orderStat {Ω : Type _} {m : ℕ}\n"
        "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ :=\n"
        "  (Finset.univ.image (fun i : Fin (m + 1) => s i ω)).max' (by\n"
        "    classical\n"
        "    simp)\n"
        "theorem split_conformal_coverage : True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    rows = []
    for placeholder, risks in [
        (
            "Exchangeable",
            [
                "semantic_definition_risk: Exchangeable candidate uses pairwise score-order probability symmetry rather than finite permutation-invariant joint-law exchangeability",
                "semantic_definition_risk: Exchangeable candidate does not expose a finite permutation/invariance parameter",
            ],
        ),
        (
            "orderStat",
            [
                "semantic_definition_risk: orderStat candidate is a finite maximum, not a reviewed rank-k order statistic/conformal quantile",
                "semantic_definition_risk: orderStat candidate uses Finset.image, which collapses duplicate score values and is not faithful to finite-sample order statistics unless a reviewed no-tie or multiplicity-preserving tie policy is supplied",
                "semantic_definition_risk: orderStat candidate body does not use the requested rank parameter k",
            ],
        ),
    ]:
        rows.append(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewResult"
                ),
                "review_result_id": f"review:{placeholder}",
                "source_review_packet_id": f"packet:{placeholder}",
                "source_definition_closure_work_order_id": f"work_order:{placeholder}",
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": placeholder,
                "candidate_artifact_path": str(candidate),
                "candidate_artifact_present": True,
                "review_status": "CANDIDATE_DEFINITION_SEMANTIC_RISK_FOUND",
                "forbidden_placeholder_detected": False,
                "ready_for_definition_lean_check": False,
                "semantic_definition_risk_detected": True,
                "semantic_definition_risks": risks,
                "semantic_alignment_constraints": [
                    "preserve split conformal marginal coverage target"
                ],
                "semantic_alignment_blockers": risks,
                "source_semantic_alignment_review_required": True,
                "source_theorem_target_identity_status": (
                    "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
                ),
                "proof_evidence_status": (
                    "DEFINITION_CLOSURE_REVIEW_RESULT_NOT_PROOF_EVIDENCE"
                ),
            }
        )
    review_results.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    proof_body_queue_manifest = tmp_path / "proof_body_queue_manifest.json"
    proof_body_queue_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:semantic_repair",
                        "source_work_order_id": "proof_body_work_order:semantic_repair",
                        "target_theorem_name": "split_conformal_coverage",
                        "target_lean_declaration": "split_conformal_coverage",
                        "expected_target_lean_declaration": "split_conformal_coverage",
                        "source_theorem_target_known": True,
                        "source_candidate_artifact_path": str(candidate),
                        "signature_probe_artifact_path": str(candidate),
                        "candidate_artifact_path": str(tmp_path / "attempt.lean"),
                        "execution_transcript_path": str(tmp_path / "attempt.jsonl"),
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "target_identity_errors": [],
                        "live_goal_location_ready": True,
                        "semantic_alignment_constraints": [
                            "Coverage event must be marginal over the joint draw",
                            "unreviewed synthesized definition semantic risk: stale pairwise definition",
                        ],
                        "semantic_alignment_blockers": [
                            "Coverage event must be marginal over the joint draw",
                            "unreviewed synthesized definition semantic risk: stale finite maximum definition",
                        ],
                        "execution_status": (
                            "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    synthesis_manifest = run_source_theorem_exact_semantic_definition_candidate_synthesis(
        out_dir=tmp_path / "synthesis",
        review_results_jsonl=review_results,
        candidate_artifact_path=candidate,
        proof_body_queue_manifest=proof_body_queue_manifest,
        allow_draft_semantic_repair=True,
    )

    assert synthesis_manifest["n_replacements_applied"] == 2
    assert synthesis_manifest["n_semantic_definition_repair_queue_rows"] == 0
    assert synthesis_manifest["n_proof_body_recheck_queue_rows"] == 1
    assert synthesis_manifest["semantic_definition_typecheck_evidence_status"] == (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
    )
    assert synthesis_manifest["synthesis_status_counts"] == {
        "DEFINITION_SYNTHESIS_CANDIDATE_WRITTEN": 2
    }
    synthesized_text = Path(
        synthesis_manifest["synthesized_candidate_artifact_path"]
    ).read_text(encoding="utf-8")
    assert "P.real {ω | s i ω ≤ s j ω}" not in synthesized_text
    assert "Finset.univ.image" not in synthesized_text
    assert "Equiv.Perm" in synthesized_text
    assert "MeasureTheory.Measure.map" in synthesized_text
    assert "List.ofFn" in synthesized_text
    assert "mergeSort" in synthesized_text
    rows = [
        json.loads(line)
        for line in Path(
            synthesis_manifest["candidate_synthesis_results_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert all(
        row["definition_candidate_review_mode"]
        == "synthesize_draft_definition_from_semantic_risk_repair"
        for row in rows
    )
    assert all(row["semantic_definition_risk_detected"] is False for row in rows)
    assert all(row["semantic_alignment_blockers"] == [] for row in rows)
    assert all(
        row["proof_evidence_status"]
        == "DEFINITION_CANDIDATE_SYNTHESIS_NOT_PROOF_EVIDENCE"
        for row in rows
    )
    recheck_manifest = json.loads(
        Path(str(synthesis_manifest["proof_body_recheck_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    recheck_row = recheck_manifest["rows"][0]
    assert "Coverage event must be marginal over the joint draw" in recheck_row[
        "semantic_alignment_constraints"
    ]
    assert "Coverage event must be marginal over the joint draw" in recheck_row[
        "semantic_alignment_blockers"
    ]
    assert not any(
        "stale" in value
        for value in [
            *recheck_row["semantic_alignment_constraints"],
            *recheck_row["semantic_alignment_blockers"],
        ]
    )


def test_exact_semantic_definition_closure_review_accepts_permutation_exchangeable_for_lean_review(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Conformal.lean").write_text(
        "-- Exchangeability assumption used by the conformal coverage proof.\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="Exchangeable")
    lookup_manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n"
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fintype.Basic\n"
        "noncomputable section\n"
        "def Exchangeable {Ω : Type _} [MeasurableSpace Ω] {ι : Type _} [Fintype ι]\n"
        "    (P : MeasureTheory.Measure Ω) (s : ι → Ω → ℝ) : Prop :=\n"
        "  ∀ σ : Equiv.Perm ι,\n"
        "    MeasureTheory.Measure.map (fun ω : Ω => fun i : ι => s (σ i) ω) P =\n"
        "      MeasureTheory.Measure.map (fun ω : Ω => fun i : ι => s i ω) P\n",
        encoding="utf-8",
    )

    review_manifest = run_source_theorem_exact_semantic_definition_closure_review(
        out_dir=tmp_path / "review",
        lookup_manifest=Path(lookup_manifest["manifest_path"]),
        candidate_artifact_path=candidate,
    )

    rows = [
        json.loads(line)
        for line in Path(review_manifest["review_results_jsonl"]).read_text().splitlines()
    ]
    assert rows[0]["placeholder_symbol"] == "Exchangeable"
    assert rows[0]["review_status"] == "CANDIDATE_DEFINITION_REQUIRES_LEAN_REVIEW"
    assert rows[0]["ready_for_definition_lean_check"] is True
    assert rows[0]["semantic_definition_risk_detected"] is False
    assert rows[0]["semantic_definition_risks"] == []
    assert rows[0]["proof_evidence_status"] == (
        "DEFINITION_CLOSURE_REVIEW_RESULT_NOT_PROOF_EVIDENCE"
    )


def test_exact_semantic_definition_candidate_synthesis_replaces_forbidden_placeholders(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "work_orders.jsonl"
    source_root = tmp_path / "Lean"
    source_root.mkdir()
    (source_root / "Conformal.lean").write_text(
        "-- Exchangeability assumption used by the conformal coverage proof.\n"
        "-- quantile construction will be reviewed later.\n",
        encoding="utf-8",
    )
    _write_work_order(queue, placeholder_symbol="Exchangeable")
    with queue.open("a", encoding="utf-8") as handle:
        order_stat_row = json.loads(queue.read_text(encoding="utf-8").splitlines()[0])
        order_stat_row["work_order_id"] = (
            "source_theorem_exact_semantic_definition_work_order:orderStat"
        )
        order_stat_row["placeholder_symbol"] = "orderStat"
        order_stat_row["search_targets"] = ["quantile"]
        order_stat_row["candidate_registered_obligation_ids"] = [
            "split_conformal_good_rank_set_inclusion_bridge"
        ]
        order_stat_row[
            "kernel_verified_source_theorem_semantic_support_obligation_ids"
        ] = ["split_conformal_good_rank_set_inclusion_bridge"]
        handle.write(json.dumps(order_stat_row) + "\n")
    lookup_manifest = run_source_theorem_exact_semantic_definition_source_lookup(
        out_dir=tmp_path / "lookup",
        queue_jsonl=queue,
        source_roots=[source_root],
    )
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n"
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fin.Basic\n"
        "import Mathlib.Data.ENNReal.Basic\n"
        "noncomputable section\n"
        "def Exchangeable {Ω : Type _} [MeasurableSpace Ω] {ι : Type _} {PType : Sort _}\n"
        "    (P : PType) (s : ι → Ω → ℝ) : Prop := True\n"
        "def orderStat {Ω : Type _} {m : ℕ}\n"
        "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ := 0\n",
        encoding="utf-8",
    )
    review_manifest = run_source_theorem_exact_semantic_definition_closure_review(
        out_dir=tmp_path / "review",
        lookup_manifest=Path(lookup_manifest["manifest_path"]),
        candidate_artifact_path=candidate,
    )
    proof_body_queue_manifest = tmp_path / "proof_body_queue_manifest.json"
    proof_body_queue_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:original",
                        "source_work_order_id": "proof_body_work_order:original",
                        "target_theorem_name": "split_conformal_coverage",
                        "target_lean_declaration": "split_conformal_coverage",
                        "expected_target_lean_declaration": "split_conformal_coverage",
                        "source_theorem_target_known": True,
                        "source_theorem_target_provenance": {
                            "source_theorem_target_known": True,
                            "target_lean_declaration": "split_conformal_coverage",
                        },
                        "semantic_alignment_constraints": [
                            "preserve marginal coverage target"
                        ],
                        "source_candidate_artifact_path": str(candidate),
                        "signature_probe_artifact_path": str(candidate),
                        "candidate_artifact_path": str(tmp_path / "attempt.lean"),
                        "execution_transcript_path": str(tmp_path / "attempt.jsonl"),
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "target_identity_errors": [],
                        "live_goal_location_ready": True,
                        "live_proof_state_request": {
                            "expected_target_lean_declaration": (
                                "split_conformal_coverage"
                            )
                        },
                        "already_repaired_environment": {
                            "missing_formal_symbols": ["Exchangeable", "orderStat"],
                            "typeclass_blockers": [],
                            "signature_typecheck_reached_proof_body": True,
                        },
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    synthesis_manifest = run_source_theorem_exact_semantic_definition_candidate_synthesis(
        out_dir=tmp_path / "synthesis",
        review_manifest=Path(review_manifest["manifest_path"]),
        candidate_artifact_path=candidate,
        proof_body_queue_manifest=proof_body_queue_manifest,
        lean_project=tmp_path / "lean_project",
    )

    assert synthesis_manifest["n_synthesis_results"] == 2
    assert synthesis_manifest["n_replacements_applied"] == 2
    assert synthesis_manifest["n_forbidden_placeholder_definitions_after"] == 0
    assert synthesis_manifest["proof_evidence_status"] == (
        "DEFINITION_CANDIDATE_SYNTHESIS_NOT_PROOF_EVIDENCE"
    )
    synthesized_text = Path(
        synthesis_manifest["synthesized_candidate_artifact_path"]
    ).read_text(encoding="utf-8")
    assert "Prop := True" not in synthesized_text
    assert "(ω : Ω) : ℝ := 0" not in synthesized_text
    assert "Equiv.Perm" in synthesized_text
    assert "MeasureTheory.Measure.map" in synthesized_text
    assert "List.ofFn" in synthesized_text
    assert "mergeSort" in synthesized_text
    assert "Finset.univ.image" not in synthesized_text
    rows = [
        json.loads(line)
        for line in Path(
            synthesis_manifest["candidate_synthesis_results_jsonl"]
        ).read_text().splitlines()
    ]
    assert all(
        row["proof_evidence_status"]
        == "DEFINITION_CANDIDATE_SYNTHESIS_NOT_PROOF_EVIDENCE"
        for row in rows
    )
    assert all(row["source_theorem_kernel_evidence_eligible"] is False for row in rows)
    assert all(row["semantic_alignment_constraints"] for row in rows)
    assert all(row["semantic_alignment_blockers"] == [] for row in rows)
    assert all(row["semantic_definition_risk_detected"] is False for row in rows)
    assert all(row["semantic_definition_risks"] == [] for row in rows)
    assert all(row["semantic_review_note"] for row in rows)
    assert all(
        row["source_theorem_target_identity_status"]
        == "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
        for row in rows
    )
    assert all(row["source_semantic_alignment_review_required"] is True for row in rows)
    assert all(
        row["candidate_lean_project_hint"] == str(tmp_path / "lean_project")
        for row in rows
    )
    assert synthesis_manifest["n_semantic_definition_repair_queue_rows"] == 0
    repair_manifest = json.loads(
        Path(str(synthesis_manifest["semantic_definition_repair_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert repair_manifest["n_repair_queue_rows"] == 0
    assert repair_manifest["n_ready"] == 0
    assert repair_manifest["semantic_definition_risks"] == []
    assert synthesis_manifest["n_proof_body_recheck_queue_rows"] == 1
    recheck_manifest = json.loads(
        Path(str(synthesis_manifest["proof_body_recheck_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert recheck_manifest["proof_body_recheck_blocked"] is False
    assert recheck_manifest["proof_body_recheck_blocker"] == ""
    assert recheck_manifest["n_execution_queue_rows"] == 1
    assert recheck_manifest["n_semantic_definition_review_blocked_rows"] == 0
    assert recheck_manifest["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert recheck_manifest["rows"][0]["source_theorem_kernel_evidence_eligible"] is False
    assert recheck_manifest["rows"][0]["proof_body_attempt_source"] == (
        "synthesized_exact_semantic_definition_recheck_queue"
    )
    assert recheck_manifest["rows"][0]["semantic_alignment_blockers"] == []
    assert any(
        "unreviewed synthesized definition review note" in value
        for value in recheck_manifest["rows"][0]["semantic_alignment_constraints"]
    )
    memory = _load_runtime_learning_memory(
        [Path(synthesis_manifest["runtime_learning_rows_jsonl"])]
    )
    repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {"runtime_learning_memory": memory}
    )
    assert any(
        repair["trigger"] == "EXACT_SOURCE_SEMANTIC_DEFINITION_CANDIDATE_SYNTHESIS"
        and repair["candidate_artifact_path"]
        == synthesis_manifest["synthesized_candidate_artifact_path"]
        and repair["source_theorem_kernel_evidence_eligible"] is False
        and repair["semantic_alignment_constraints"]
        and repair["semantic_alignment_blockers"] == []
        and repair["source_theorem_target_identity_status"]
        == "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
        for repair in repairs
    )


def test_exact_semantic_definition_candidate_synthesis_reviews_ready_candidate_without_rewrite(
    tmp_path: Path,
) -> None:
    blocker = (
        "reviewed order-statistic definition must preserve the requested rank k"
    )
    review_results = tmp_path / "review_results.jsonl"
    candidate = tmp_path / "candidate.lean"
    candidate_text = (
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fin.Basic\n"
        "import Mathlib.Data.Finset.Basic\n"
        "noncomputable section\n"
        "def orderStat {Ω : Type _} {m : ℕ}\n"
        "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ :=\n"
        "  (Finset.univ.image (fun i : Fin (m + 1) => s i ω)).max' (by\n"
        "    classical\n"
        "    simp)\n"
        "theorem split_conformal_coverage : True := by\n"
        "  trivial\n"
    )
    candidate.write_text(candidate_text, encoding="utf-8")
    review_results.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewResult"
                ),
                "review_result_id": "review:orderStat",
                "source_review_packet_id": "packet:orderStat",
                "source_definition_closure_work_order_id": "work_order:orderStat",
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "orderStat",
                "definition_contract": {
                    "semantic_intent": "finite order statistic at rank k"
                },
                "candidate_artifact_path": str(candidate),
                "candidate_artifact_present": True,
                "review_status": "CANDIDATE_DEFINITION_REQUIRES_LEAN_REVIEW",
                "forbidden_placeholder_detected": False,
                "forbidden_placeholder_matches": [],
                "ready_for_definition_lean_check": True,
                "source_semantic_alignment_review_required": True,
                "source_theorem_target_identity_status": (
                    "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
                ),
                "source_theorem_target_provenance": {
                    "target_lean_declaration": "split_conformal_coverage"
                },
                "semantic_alignment_constraints": [
                    "preserve split conformal marginal coverage target"
                ],
                "semantic_alignment_blockers": [blocker],
                "recommended_repair_tasks": [
                    "run local Lean on the existing candidate definition"
                ],
                "proof_evidence_status": (
                    "DEFINITION_CLOSURE_REVIEW_RESULT_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    proof_body_queue_manifest = tmp_path / "proof_body_queue_manifest.json"
    proof_body_queue_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:original",
                        "source_work_order_id": "proof_body_work_order:original",
                        "target_theorem_name": "split_conformal_coverage",
                        "target_lean_declaration": "split_conformal_coverage",
                        "expected_target_lean_declaration": "split_conformal_coverage",
                        "source_theorem_target_known": True,
                        "source_theorem_target_provenance": {
                            "target_lean_declaration": "split_conformal_coverage"
                        },
                        "semantic_alignment_constraints": [
                            "preserve marginal coverage target"
                        ],
                        "source_candidate_artifact_path": str(candidate),
                        "signature_probe_artifact_path": str(candidate),
                        "candidate_artifact_path": str(tmp_path / "attempt.lean"),
                        "execution_transcript_path": str(tmp_path / "attempt.jsonl"),
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "target_identity_errors": [],
                        "live_goal_location_ready": True,
                        "live_proof_state_request": {
                            "expected_target_lean_declaration": (
                                "split_conformal_coverage"
                            )
                        },
                        "already_repaired_environment": {
                            "missing_formal_symbols": ["orderStat"],
                            "typeclass_blockers": [],
                            "signature_typecheck_reached_proof_body": True,
                        },
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    synthesis_manifest = run_source_theorem_exact_semantic_definition_candidate_synthesis(
        out_dir=tmp_path / "synthesis",
        review_results_jsonl=review_results,
        candidate_artifact_path=candidate,
        proof_body_queue_manifest=proof_body_queue_manifest,
        local_lean=True,
        lean_command=(
            "python3",
            "-c",
            "import sys; p=sys.argv[-1]; "
            "sys.exit(0) if p.endswith('_definitions_only.lean') "
            "else (print('error: unsolved goals'), sys.exit(1))",
        ),
    )

    assert synthesis_manifest["n_synthesis_results"] == 1
    assert synthesis_manifest["n_replacements_applied"] == 0
    assert synthesis_manifest["synthesis_status_counts"] == {
        "DEFINITION_REVIEW_LOCAL_LEAN_REACHED_PROOF_BODY": 1
    }
    assert synthesis_manifest["local_definition_lean_checked"] is True
    assert synthesis_manifest["local_definition_lean_compiled"] is True
    assert synthesis_manifest["local_lean_checked"] is True
    assert synthesis_manifest["local_lean_compiled"] is False
    synthesized_text = Path(
        synthesis_manifest["synthesized_candidate_artifact_path"]
    ).read_text(encoding="utf-8")
    assert synthesized_text == candidate_text
    definition_only_text = Path(
        synthesis_manifest["definition_only_candidate_artifact_path"]
    ).read_text(encoding="utf-8")
    assert "theorem split_conformal_coverage" not in definition_only_text
    assert "def orderStat" in definition_only_text
    rows = [
        json.loads(line)
        for line in Path(
            synthesis_manifest["candidate_synthesis_results_jsonl"]
        ).read_text().splitlines()
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["definition_candidate_review_mode"] == "lean_review_existing_candidate"
    assert row["replacement_applied"] is False
    assert row["replacement_definition"] == ""
    assert row["semantic_risk"] == ""
    assert row["semantic_alignment_blockers"] == [blocker]
    assert row["source_theorem_kernel_evidence_eligible"] is False
    assert row["source_semantic_alignment_review_required"] is True
    assert row["local_definition_lean_checked"] is True
    assert row["local_definition_lean_compiled"] is True
    assert row["semantic_definition_typecheck_evidence_status"] == (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    )
    assert "review existing candidate definitions" in row["recommended_next_action"]
    recheck_manifest = json.loads(
        Path(str(synthesis_manifest["proof_body_recheck_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert recheck_manifest["n_execution_queue_rows"] == 0
    assert recheck_manifest["proof_body_recheck_blocked"] is True
    assert recheck_manifest["n_semantic_definition_review_blocked_rows"] == 1
    assert synthesis_manifest["n_semantic_definition_repair_queue_rows"] == 1
    repair_manifest = json.loads(
        Path(str(synthesis_manifest["semantic_definition_repair_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    repair_rows = [
        json.loads(line)
        for line in Path(
            repair_manifest["semantic_definition_repair_queue_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert len(repair_rows) == 1
    repair_row = repair_rows[0]
    assert repair_row["definition_only_candidate_artifact_path"] == (
        synthesis_manifest["definition_only_candidate_artifact_path"]
    )
    assert repair_row["synthesized_candidate_artifact_path"] == (
        synthesis_manifest["synthesized_candidate_artifact_path"]
    )
    assert repair_row["local_definition_lean_checked"] is True
    assert repair_row["local_definition_lean_compiled"] is True
    assert repair_row["semantic_definition_typecheck_evidence_status"] == (
        "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
    )
    assert repair_row[
        "source_theorem_exact_semantic_definition_typechecked_candidate"
    ]["definition_only_candidate_artifact_path"] == (
        synthesis_manifest["definition_only_candidate_artifact_path"]
    )
    assert repair_row[
        "source_theorem_exact_semantic_definition_typechecked_candidate"
    ]["local_definition_lean_compiled"] is True
    memory = _load_runtime_learning_memory(
        [Path(synthesis_manifest["runtime_learning_rows_jsonl"])]
    )
    repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {"runtime_learning_memory": memory}
    )
    assert any(
        repair["trigger"] == "EXACT_SOURCE_SEMANTIC_DEFINITION_CANDIDATE_SYNTHESIS"
        and repair["definition_candidate_review_mode"]
        == "lean_review_existing_candidate"
        and repair["source_theorem_kernel_evidence_eligible"] is False
        and repair["local_definition_lean_compiled"] is True
        and repair["definition_only_candidate_artifact_path"]
        == synthesis_manifest["definition_only_candidate_artifact_path"]
        and repair["semantic_definition_typecheck_evidence_status"]
        == "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
        and repair["semantic_alignment_blockers"] == [blocker]
        for repair in repairs
    )


def test_exact_semantic_definition_candidate_synthesis_recheck_queue_uses_synthesized_artifact_when_unblocked(
    tmp_path: Path,
) -> None:
    review_results = tmp_path / "review_results.jsonl"
    candidate = tmp_path / "candidate.lean"
    candidate_text = (
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fin.Basic\n"
        "noncomputable section\n"
        "def orderStat {Ω : Type _} {m : ℕ}\n"
        "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ := 0\n"
        "theorem split_conformal_coverage : True := by\n"
        "  trivial\n"
    )
    candidate.write_text(candidate_text, encoding="utf-8")
    review_results.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewResult"
                ),
                "review_result_id": "review:orderStat",
                "source_review_packet_id": "packet:orderStat",
                "source_definition_closure_work_order_id": "work_order:orderStat",
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "orderStat",
                "definition_contract": {
                    "semantic_intent": "finite order statistic at rank k"
                },
                "candidate_artifact_path": str(candidate),
                "candidate_artifact_present": True,
                "review_status": "CANDIDATE_DEFINITION_REQUIRES_LEAN_REVIEW",
                "forbidden_placeholder_detected": False,
                "forbidden_placeholder_matches": [],
                "ready_for_definition_lean_check": True,
                "source_semantic_alignment_review_required": False,
                "source_theorem_target_identity_status": (
                    "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
                ),
                "source_theorem_target_provenance": {
                    "target_lean_declaration": "split_conformal_coverage"
                },
                "semantic_alignment_constraints": [
                    "preserve split conformal marginal coverage target"
                ],
                "semantic_alignment_blockers": [],
                "recommended_repair_tasks": [
                    "run local Lean on the existing candidate definition"
                ],
                "proof_evidence_status": (
                    "DEFINITION_CLOSURE_REVIEW_RESULT_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    stale_signature_probe = tmp_path / "stale_signature_probe.lean"
    stale_signature_probe.write_text(
        "theorem split_conformal_coverage : False := by\n"
        "  contradiction\n",
        encoding="utf-8",
    )
    proof_body_queue_manifest = tmp_path / "proof_body_queue_manifest.json"
    proof_body_queue_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:original",
                        "source_work_order_id": "proof_body_work_order:original",
                        "target_theorem_name": "split_conformal_coverage",
                        "target_lean_declaration": "split_conformal_coverage",
                        "expected_target_lean_declaration": "split_conformal_coverage",
                        "source_theorem_target_known": True,
                        "source_theorem_target_provenance": {
                            "target_lean_declaration": "split_conformal_coverage"
                        },
                        "semantic_alignment_constraints": [
                            "preserve marginal coverage target"
                        ],
                        "source_candidate_artifact_path": str(stale_signature_probe),
                        "signature_probe_artifact_path": str(stale_signature_probe),
                        "candidate_artifact_path": str(tmp_path / "attempt.lean"),
                        "execution_transcript_path": str(tmp_path / "attempt.jsonl"),
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "target_identity_errors": [],
                        "live_goal_location_ready": True,
                        "live_proof_state_request": {
                            "expected_target_lean_declaration": (
                                "split_conformal_coverage"
                            )
                        },
                        "already_repaired_environment": {
                            "missing_formal_symbols": ["orderStat"],
                            "typeclass_blockers": [],
                            "signature_typecheck_reached_proof_body": True,
                        },
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    synthesis_manifest = run_source_theorem_exact_semantic_definition_candidate_synthesis(
        out_dir=tmp_path / "synthesis",
        review_results_jsonl=review_results,
        candidate_artifact_path=candidate,
        proof_body_queue_manifest=proof_body_queue_manifest,
        local_lean=True,
        lean_command=(
            "python3",
            "-c",
            "import sys; p=sys.argv[-1]; "
            "sys.exit(0) if p.endswith('_definitions_only.lean') "
            "else (print('error: unsolved goals'), sys.exit(1))",
        ),
    )

    synthesized_path = synthesis_manifest["synthesized_candidate_artifact_path"]
    assert synthesis_manifest["n_semantic_definition_repair_queue_rows"] == 0
    assert synthesis_manifest["n_proof_body_recheck_queue_rows"] == 1
    recheck_manifest = json.loads(
        Path(str(synthesis_manifest["proof_body_recheck_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert recheck_manifest["proof_body_recheck_blocked"] is False
    assert recheck_manifest["n_execution_queue_rows"] == 1
    recheck_rows = [
        json.loads(line)
        for line in Path(
            recheck_manifest["proof_body_execution_queue_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert len(recheck_rows) == 1
    recheck_row = recheck_rows[0]
    assert recheck_row["source_candidate_artifact_path"] == synthesized_path
    assert recheck_row["signature_probe_artifact_path"] == synthesized_path
    assert recheck_row["source_theorem_signature_probe_artifact_path"] == (
        synthesized_path
    )
    assert recheck_row["proof_body_signature_probe_artifact_path"] == synthesized_path
    assert recheck_row["candidate_artifact_path"] == synthesized_path
    assert recheck_row["source_candidate_artifact_path"] != str(stale_signature_probe)
    assert recheck_row["source_theorem_kernel_evidence_eligible"] is False
    assert recheck_row["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
    )


def test_exact_semantic_definition_candidate_synthesis_normalizes_orderstat_fin_witness(
    tmp_path: Path,
) -> None:
    review_results = tmp_path / "review_results.jsonl"
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n"
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fin.Basic\n"
        "def orderStat {Ω : Type _} {m : ℕ}\n"
        "    (s : Fin (m + 1) → Ω → ℝ) (k : ℕ) (ω : Ω) : ℝ := 0\n"
        "theorem split_conformal_coverage {Ω : Type _} [MeasurableSpace Ω]\n"
        "    (n2 : ℕ) (alpha : ℝ) (s : Fin (n2 + 1) → Ω → ℝ)\n"
        "    (q_hat : Ω → ℝ)\n"
        "    (hq : q_hat = fun ω => "
        "orderStat s ⟨Nat.ceil ((↑(n2 + 1)) * (1 - alpha)) - 1, by omega⟩ ω) :\n"
        "    True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    review_results.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "RuntimeSourceTheoremExactSemanticDefinitionClosureReviewResult"
                ),
                "review_result_id": "review:orderStat",
                "source_review_packet_id": "packet:orderStat",
                "source_definition_closure_work_order_id": "work_order:orderStat",
                "question_id": "conformal_prediction_coverage",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "orderStat",
                "definition_contract": {
                    "semantic_intent": "finite order statistic at rank k"
                },
                "candidate_artifact_path": str(candidate),
                "candidate_artifact_present": True,
                "review_status": "FORBIDDEN_PLACEHOLDER_DEFINITION_FOUND",
                "forbidden_placeholder_detected": True,
                "ready_for_definition_lean_check": False,
                "semantic_definition_risk_detected": False,
                "semantic_definition_risks": [],
                "semantic_alignment_constraints": [],
                "semantic_alignment_blockers": [],
                "proof_evidence_status": (
                    "DEFINITION_CLOSURE_REVIEW_RESULT_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    synthesis_manifest = run_source_theorem_exact_semantic_definition_candidate_synthesis(
        out_dir=tmp_path / "synthesis",
        review_results_jsonl=review_results,
        candidate_artifact_path=candidate,
    )

    synthesized = Path(
        synthesis_manifest["synthesized_candidate_artifact_path"]
    ).read_text(encoding="utf-8")
    assert "orderStat s ⟨" not in synthesized
    assert (
        "orderStat s (Nat.ceil ((↑(n2 + 1)) * (1 - alpha)) - 1) ω"
        in synthesized
    )
    assert "(k : ℕ)" in synthesized
    assert ".getD k 0" in synthesized


def test_typechecked_review_recheck_queue_blocks_unreviewed_candidate(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text("theorem split_conformal_coverage : True := by\n  trivial\n")
    queue_manifest = tmp_path / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_exact_proof_body_queue_manifest(queue_manifest, candidate=candidate)
    review_packets = tmp_path / "review_packets.jsonl"
    review_packets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
                ),
                "review_packet_id": "review:covered",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "candidate_artifact_path": str(candidate),
                "local_definition_lean_compiled": True,
                "semantic_review_required_before_proof_body": True,
                "source_theorem_ready_for_exact_proof_body": False,
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
        proof_body_queue_manifest=queue_manifest,
    )

    assert manifest["n_review_packets"] == 1
    assert manifest["n_semantically_approved_review_packets"] == 0
    assert manifest["n_blocked_review_packets"] == 1
    assert manifest["n_blocked_review_learning_rows"] == 0
    assert manifest["n_semantic_review_work_orders"] == 1
    assert manifest["n_verifier_gate_work_orders"] == 0
    assert manifest["n_runtime_learning_rows"] == 1
    assert manifest["n_execution_queue_rows"] == 0
    assert manifest["proof_body_recheck_blocked"] is True
    assert manifest["proof_body_recheck_blocker"] == (
        "typechecked_candidate_semantic_review_required"
    )
    assert manifest["source_theorem_ready_for_exact_proof_body"] is False
    blocked = [
        json.loads(line)
        for line in Path(manifest["blocked_review_packets_jsonl"]).read_text().splitlines()
        if line.strip()
    ]
    assert blocked[0]["proof_body_recheck_blockers"] == [
        "source_theorem_ready_for_exact_proof_body_false",
        "semantic_review_required_before_proof_body",
    ]
    assert manifest["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_REVIEW_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
    )
    semantic_review_work_orders = [
        json.loads(line)
        for line in Path(manifest["semantic_review_work_orders_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert semantic_review_work_orders[0]["artifact_kind"] == (
        "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedSemanticReviewWorkOrder"
    )
    assert semantic_review_work_orders[0]["learning_task"] == (
        "source_theorem_exact_semantic_definition_typechecked_semantic_review_required"
    )
    assert semantic_review_work_orders[0]["action_type"] == (
        "review_typechecked_exact_semantic_definition_candidate"
    )
    assert semantic_review_work_orders[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_SEMANTIC_FAITHFULNESS_REVIEW"
    )
    assert semantic_review_work_orders[0]["failure_classification"] == (
        "typechecked_exact_semantic_definition_semantic_review_missing"
    )
    assert semantic_review_work_orders[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert (
        semantic_review_work_orders[0]["source_theorem_kernel_evidence_eligible"]
        is False
    )
    assert semantic_review_work_orders[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_SEMANTIC_REVIEW_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows == semantic_review_work_orders
    assert learning_rows[0]["learning_task"] == (
        "source_theorem_exact_semantic_definition_typechecked_semantic_review_required"
    )
    assert learning_rows[0]["input_summary"]["trigger"] == (
        "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_SEMANTIC_REVIEW_REQUIRED"
    )
    assert learning_rows[0]["proof_body_recheck_blockers"] == [
        "source_theorem_ready_for_exact_proof_body_false",
        "semantic_review_required_before_proof_body",
    ]
    assert learning_rows[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_SEMANTIC_FAITHFULNESS_REVIEW"
    )
    assert learning_rows[0]["failure_classification"] == (
        "typechecked_exact_semantic_definition_semantic_review_missing"
    )
    assert learning_rows[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_SEMANTIC_REVIEW_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    memory = _load_runtime_learning_memory(
        [Path(manifest["runtime_learning_rows_jsonl"])],
        max_rows=10,
    )
    repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {"runtime_learning_memory": memory}
    )
    assert len(repairs) == 1
    assert repairs[0]["trigger"] == (
        "EXACT_SOURCE_SEMANTIC_DEFINITION_TYPECHECKED_SEMANTIC_REVIEW_REQUIRED"
    )
    assert repairs[0]["failure_classification"] == (
        "typechecked_exact_semantic_definition_semantic_review_missing"
    )
    assert repairs[0]["proof_body_gate_status"] == (
        "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY"
    )


def test_typechecked_review_recheck_queue_normalizes_serialized_false_flags(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    queue_manifest = tmp_path / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_exact_proof_body_queue_manifest(queue_manifest, candidate=candidate)
    review_packets = tmp_path / "review_packets.jsonl"
    review_packets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
                ),
                "review_packet_id": "review:covered:string-false",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "candidate_artifact_path": str(candidate),
                "local_definition_lean_compiled": True,
                "semantic_review_required_before_proof_body": "false",
                "source_theorem_ready_for_exact_proof_body": "false",
                "source_theorem_kernel_verified": "false",
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
        proof_body_queue_manifest=queue_manifest,
    )

    assert manifest["n_review_packets"] == 1
    assert manifest["n_semantically_approved_review_packets"] == 0
    assert manifest["n_blocked_review_packets"] == 1
    assert manifest["n_blocked_review_learning_rows"] == 1
    assert manifest["n_semantic_review_work_orders"] == 0
    assert manifest["n_verifier_gate_work_orders"] == 0
    assert manifest["n_runtime_learning_rows"] == 1
    assert manifest["n_execution_queue_rows"] == 0
    blocked = [
        json.loads(line)
        for line in Path(manifest["blocked_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert blocked[0]["proof_body_recheck_blockers"] == [
        "source_theorem_ready_for_exact_proof_body_false"
    ]
    assert blocked[0]["runtime_queue_status"] == (
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows[0]["proof_body_recheck_blockers"] == [
        "source_theorem_ready_for_exact_proof_body_false"
    ]
    assert learning_rows[0]["source_theorem_kernel_verified"] is False
    assert learning_rows[0]["source_theorem_kernel_evidence_eligible"] is False


def test_typechecked_review_recheck_queue_blocks_llm_review_without_verifier_gate(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.lean"
    candidate.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    queue_manifest = tmp_path / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_exact_proof_body_queue_manifest(queue_manifest, candidate=candidate)
    review_packets = tmp_path / "review_packets.jsonl"
    review_packets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
                ),
                "review_packet_id": "review:covered:llm-approved",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "candidate_artifact_path": str(candidate),
                "local_definition_lean_compiled": True,
                "semantic_definition_typecheck_evidence_status": (
                    "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                ),
                "semantic_review_decision": "approved_definition_candidate",
                "semantic_review_status": (
                    "llm_semantic_review_approved_definition_candidate_not_proof"
                ),
                "semantic_review_evidence": [
                    "checked source theorem binders and adapter dependencies"
                ],
                "semantic_review_required_before_proof_body": True,
                "source_theorem_ready_for_exact_proof_body": False,
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
        proof_body_queue_manifest=queue_manifest,
    )

    assert manifest["n_review_packets"] == 1
    assert manifest["n_semantically_approved_review_packets"] == 0
    assert manifest["n_llm_semantic_review_approved_packets"] == 1
    assert (
        manifest["n_llm_semantic_review_packets_requiring_verifier_gate"] == 1
    )
    assert manifest["n_blocked_review_packets"] == 1
    assert manifest["n_blocked_review_learning_rows"] == 0
    assert manifest["n_verifier_gate_work_orders"] == 1
    assert manifest["n_verifier_gate_work_orders_with_source_anchor_context"] == 1
    assert manifest["n_verifier_gate_work_orders_missing_source_anchor_context"] == 0
    assert manifest["n_runtime_learning_rows"] == 1
    assert manifest["n_execution_queue_rows"] == 0
    assert manifest["proof_body_recheck_blocked"] is True
    assert manifest["proof_body_recheck_blocker"] == (
        "typechecked_candidate_llm_review_requires_verifier_gate"
    )
    assert manifest["source_theorem_ready_for_exact_proof_body"] is False
    blocked = [
        json.loads(line)
        for line in Path(manifest["blocked_review_packets_jsonl"]).read_text().splitlines()
        if line.strip()
    ]
    assert blocked[0]["semantic_review_decision"] == "approved_definition_candidate"
    assert blocked[0]["proof_body_recheck_blockers"] == [
        "source_theorem_ready_for_exact_proof_body_false",
        "semantic_review_required_before_proof_body",
        "llm_semantic_review_approved_requires_verifier_recheck_gate",
    ]
    assert blocked[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_REVIEW_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
    )
    verifier_gate_rows = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_work_orders_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert verifier_gate_rows[0]["learning_task"] == (
        "source_theorem_exact_semantic_definition_typechecked_review_verifier_gate"
    )
    assert verifier_gate_rows[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_RECHECK_GATE"
    )
    assert verifier_gate_rows[0]["failure_classification"] == (
        "typechecked_exact_semantic_definition_llm_review_requires_verifier_gate"
    )
    assert verifier_gate_rows[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert verifier_gate_rows[0]["source_theorem_kernel_evidence_eligible"] is False
    assert verifier_gate_rows[0]["source_anchors"][0]["kind"] == (
        "proof_body_goal_context"
    )
    assert verifier_gate_rows[0]["source_anchors"][0][
        "source"
    ] == "exact_source_theorem_proof_body_execution_queue"
    assert verifier_gate_rows[0]["source_anchors"][0][
        "proof_evidence_status"
    ] == "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_WORK_ORDER_NOT_PROOF_EVIDENCE"
    binders_by_name = {
        row["name"]: row for row in verifier_gate_rows[0]["exact_source_theorem_binders"]
    }
    assert binders_by_name["P"]["type"] == "MeasureTheory.Measure Ω"
    assert binders_by_name["score"]["type"] == "Fin (n + 1) → Ω → ℝ"
    assert binders_by_name["hq"]["role"] == "source_theorem_hypothesis"
    assert "hC" in verifier_gate_rows[0]["premise_semantic_anchor_binder_names"]
    assert verifier_gate_rows[0]["input_summary"]["source_anchors"][0][
        "kind"
    ] == "proof_body_goal_context"
    assert verifier_gate_rows[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert learning_rows == verifier_gate_rows


def test_typechecked_review_recheck_queue_uses_definition_only_candidate_for_verifier_gate(
    tmp_path: Path,
) -> None:
    definition_only_candidate = tmp_path / "covered_definition_only.lean"
    definition_only_candidate.write_text(
        "def covered : Prop := True\n",
        encoding="utf-8",
    )
    queue_manifest = tmp_path / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_exact_proof_body_queue_manifest(
        queue_manifest,
        candidate=definition_only_candidate,
    )
    review_packets = tmp_path / "review_packets.jsonl"
    review_packets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
                ),
                "review_packet_id": "review:covered:definition-only",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "definition_only_candidate_artifact_path": str(
                    definition_only_candidate
                ),
                "definition_only_candidate_file_resolved": True,
                "local_definition_lean_checked": True,
                "local_definition_lean_compiled": True,
                "semantic_definition_typecheck_evidence_status": (
                    "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                ),
                "semantic_review_decision": "approved_definition_candidate",
                "semantic_review_status": (
                    "llm_semantic_review_approved_definition_candidate_not_proof"
                ),
                "semantic_review_required_before_proof_body": True,
                "source_theorem_ready_for_exact_proof_body": False,
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
        proof_body_queue_manifest=queue_manifest,
    )

    assert manifest["n_review_packets"] == 1
    assert manifest["n_blocked_review_packets"] == 1
    assert manifest["n_verifier_gate_work_orders"] == 1
    blocked = [
        json.loads(line)
        for line in Path(manifest["blocked_review_packets_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert "candidate_artifact_path_missing" not in blocked[0][
        "proof_body_recheck_blockers"
    ]
    assert blocked[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    verifier_gate_rows = [
        json.loads(line)
        for line in Path(manifest["verifier_gate_work_orders_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert verifier_gate_rows[0]["candidate_artifact_path"] == str(
        definition_only_candidate
    )
    assert verifier_gate_rows[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    assert verifier_gate_rows[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )


def test_typechecked_review_verifier_gate_memory_remains_specific() -> None:
    repairs = _runtime_learning_memory_source_theorem_exact_candidate_repairs(
        {
            "runtime_learning_memory": {
                "artifact_kind": "RuntimeLearningMemoryContext",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": (
                            "RuntimeSourceTheoremExactSemanticDefinitionTypecheckedReviewVerifierGateWorkOrder"
                        ),
                        "learning_task": (
                            "source_theorem_exact_semantic_definition_typechecked_review_verifier_gate"
                        ),
                        "work_order_id": "verifier-gate:covered",
                        "target_theorem_name": "split_conformal_coverage",
                        "placeholder_symbol": "covered",
                        "candidate_artifact_path": "runs/candidates/covered.lean",
                        "local_definition_lean_compiled": True,
                        "semantic_definition_typecheck_evidence_status": (
                            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                        ),
                        "proof_body_gate_status": (
                            "SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY"
                        ),
                        "runtime_queue_status": (
                            "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_RECHECK_GATE"
                        ),
                        "failure_classification": (
                            "typechecked_exact_semantic_definition_llm_review_requires_verifier_gate"
                        ),
                        "definition_candidate_review_mode": (
                            "llm_semantic_review_requires_verifier_gate"
                        ),
                        "source_theorem_kernel_evidence_eligible": False,
                        "required_next_checks": [
                            "run a local Lean/AXLE semantic-faithfulness verifier"
                        ],
                        "proof_evidence_status": (
                            "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_WORK_ORDER_NOT_PROOF_EVIDENCE"
                        ),
                    }
                ],
            }
        }
    )

    assert len(repairs) == 1
    assert repairs[0]["failure_classification"] == (
        "typechecked_exact_semantic_definition_llm_review_requires_verifier_gate"
    )
    assert repairs[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_VERIFIER_RECHECK_GATE"
    )
    assert repairs[0]["definition_candidate_review_mode"] == (
        "llm_semantic_review_requires_verifier_gate"
    )
    assert repairs[0]["source_theorem_kernel_evidence_eligible"] is False
    assert repairs[0]["recommended_repair_tasks"] == [
        "run a local Lean/AXLE semantic-faithfulness verifier"
    ]


def test_typechecked_review_recheck_queue_exports_approved_candidate(
    tmp_path: Path,
) -> None:
    original_candidate = tmp_path / "original.lean"
    original_candidate.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    reviewed_candidate = tmp_path / "reviewed.lean"
    reviewed_candidate.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    queue_manifest = tmp_path / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_exact_proof_body_queue_manifest(queue_manifest, candidate=original_candidate)
    review_packets = tmp_path / "review_packets.jsonl"
    review_packets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
                ),
                "review_packet_id": "review:covered",
                "target_theorem_name": "split_conformal_coverage",
                "placeholder_symbol": "covered",
                "candidate_artifact_path": str(reviewed_candidate),
                "local_definition_lean_compiled": True,
                "semantic_definition_typecheck_evidence_status": (
                    "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
                ),
                "semantic_review_required_before_proof_body": False,
                "source_theorem_ready_for_exact_proof_body": True,
                "semantic_review_status": "approved",
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
        proof_body_queue_manifest=queue_manifest,
    )

    assert manifest["n_review_packets"] == 1
    assert manifest["n_semantically_approved_review_packets"] == 1
    assert manifest["n_blocked_review_packets"] == 0
    assert manifest["n_execution_queue_rows"] == 1
    assert manifest["n_ready"] == 1
    assert manifest["proof_body_recheck_blocked"] is False
    assert manifest["proof_body_recheck_blocker"] == ""
    rows = [
        json.loads(line)
        for line in Path(manifest["proof_body_execution_queue_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert rows[0]["source_execution_queue_id"] == "exact_source_queue:split"
    assert rows[0]["target_ids"] == ["split_conformal_coverage"]
    assert rows[0]["candidate_artifact_path"] == str(reviewed_candidate)
    assert rows[0]["source_candidate_artifact_path"] == str(reviewed_candidate)
    assert rows[0]["signature_probe_artifact_path"] == str(reviewed_candidate)
    assert rows[0]["source_theorem_signature_probe_artifact_path"] == str(
        reviewed_candidate
    )
    assert rows[0]["proof_body_signature_probe_artifact_path"] == str(
        reviewed_candidate
    )
    assert rows[0]["proof_body_attempt_source"] == (
        "reviewed_existing_semantic_definition_recheck_queue"
    )
    assert rows[0]["source_theorem_kernel_evidence_eligible"] is False
    assert rows[0]["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_RECHECK_QUEUE_NOT_PROOF_EVIDENCE"
    )


def test_typechecked_review_recheck_prefers_target_known_source_rows(
    tmp_path: Path,
) -> None:
    original_candidate = tmp_path / "original.lean"
    original_candidate.write_text(
        "theorem split_conformal_coverage_repair_v3 : True := by\n  trivial\n",
        encoding="utf-8",
    )
    reviewed_candidate = tmp_path / "reviewed.lean"
    reviewed_candidate.write_text(
        "def good_rank_event : True := True\n",
        encoding="utf-8",
    )
    queue_manifest = tmp_path / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    queue_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueManifest",
                "rows": [
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:mismatch",
                        "target_theorem_name": "split_conformal_coverage",
                        "target_ids": ["split_conformal_coverage"],
                        "target_lean_declaration": (
                            "split_conformal_coverage_helper_derivation"
                        ),
                        "expected_target_lean_declaration": (
                            "split_conformal_coverage"
                        ),
                        "source_theorem_target_identity_status": (
                            "TARGET_DECLARATION_MISMATCH"
                        ),
                        "target_identity_status": "TARGET_DECLARATION_MISMATCH",
                        "target_identity_errors": [
                            "helper declaration does not match source theorem"
                        ],
                        "signature_probe_artifact_path": str(original_candidate),
                        "candidate_artifact_path": str(original_candidate),
                        "semantic_alignment_constraints": [],
                        "semantic_alignment_blockers": [],
                        "proof_body_goal_excerpt": [],
                        "live_goal_location_ready": False,
                        "execution_status": (
                            "BLOCKED_EXACT_SOURCE_PROOF_BODY_TARGET_IDENTITY"
                        ),
                    },
                    {
                        "schema_version": 1,
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:target-known",
                        "target_theorem_name": (
                            "split_conformal_coverage_repair_v3"
                        ),
                        "target_ids": ["split_conformal_coverage"],
                        "target_lean_declaration": (
                            "split_conformal_coverage_repair_v3"
                        ),
                        "expected_target_lean_declaration": (
                            "split_conformal_coverage_repair_v3"
                        ),
                        "source_theorem_target_known": True,
                        "source_theorem_target_identity_status": (
                            "SOURCE_THEOREM_TARGET_KNOWN"
                        ),
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "target_identity_errors": [],
                        "signature_probe_artifact_path": str(original_candidate),
                        "candidate_artifact_path": str(original_candidate),
                        "semantic_alignment_constraints": [],
                        "semantic_alignment_blockers": [],
                        "proof_body_goal_excerpt": ["q : Real", "⊢ True"],
                        "live_goal_location_ready": True,
                        "live_proof_state_request": {"request_id": "live_goal"},
                        "already_repaired_environment": {
                            "missing_formal_symbols": [],
                            "typeclass_blockers": [],
                            "signature_typecheck_reached_proof_body": True,
                        },
                        "execution_status": (
                            "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
                        ),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    review_packets = tmp_path / "review_packets.jsonl"
    review_packets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionVerifierApprovedReviewPacket"
                ),
                "review_packet_id": "review:good-rank",
                "target_theorem_name": "split_conformal_coverage",
                "target_ids": ["split_conformal_coverage"],
                "placeholder_symbol": "good_rank_event",
                "candidate_artifact_path": str(reviewed_candidate),
                "definition_only_candidate_artifact_path": str(reviewed_candidate),
                "local_definition_lean_compiled": True,
                "semantic_definition_typecheck_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_APPROVED_LOCAL_LEAN_COMPILED_NOT_PROOF"
                ),
                "semantic_review_required_before_proof_body": False,
                "source_theorem_ready_for_exact_proof_body": True,
                "semantic_review_decision": "approved_definition_candidate",
                "semantic_review_status": (
                    "verifier_gate_approved_definition_candidate_not_proof"
                ),
                "semantic_review_evidence": ["verifier gate approved"],
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_APPROVED_NOT_SOURCE_THEOREM_PROOF"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
        proof_body_queue_manifest=queue_manifest,
    )

    assert manifest["n_execution_queue_rows"] == 1
    assert manifest["n_ready"] == 1
    rows = [
        json.loads(line)
        for line in Path(manifest["proof_body_execution_queue_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert rows[0]["source_execution_queue_id"] == "exact_source_queue:target-known"
    assert rows[0]["target_ids"] == ["split_conformal_coverage"]
    assert rows[0]["target_lean_declaration"] == (
        "split_conformal_coverage_repair_v3"
    )
    assert rows[0]["signature_probe_artifact_path"] == str(original_candidate)
    assert rows[0]["candidate_artifact_path"] != str(reviewed_candidate)
    assert rows[0]["reviewed_exact_semantic_definition_artifact_path"] == (
        str(reviewed_candidate)
    )
    assert rows[0]["reviewed_exact_semantic_definition_artifact_paths"] == [
        str(reviewed_candidate)
    ]
    assert rows[0]["execution_status"] == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
    assert rows[0]["source_theorem_target_identity_status"] == (
        "SOURCE_THEOREM_TARGET_KNOWN"
    )


def test_typechecked_review_recheck_queue_normalizes_source_row_string_false_flags(
    tmp_path: Path,
) -> None:
    original_candidate = tmp_path / "original.lean"
    original_candidate.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    reviewed_candidate = tmp_path / "reviewed.lean"
    reviewed_candidate.write_text(
        "theorem split_conformal_coverage : True := by\n  trivial\n",
        encoding="utf-8",
    )
    queue_manifest = tmp_path / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    _write_exact_proof_body_queue_manifest(queue_manifest, candidate=original_candidate)
    queue_payload = json.loads(queue_manifest.read_text(encoding="utf-8"))
    queue_payload["rows"][0]["source_theorem_target_known"] = "false"
    queue_payload["rows"][0]["source_theorem_target_provenance"][
        "source_theorem_target_known"
    ] = "false"
    queue_payload["rows"][0]["source_theorem_target_identity_status"] = ""
    queue_payload["rows"][0]["live_goal_location_ready"] = "false"
    queue_payload["rows"][0]["already_repaired_environment"][
        "signature_typecheck_reached_proof_body"
    ] = "false"
    queue_manifest.write_text(json.dumps(queue_payload), encoding="utf-8")
    review_packets = tmp_path / "review_packets.jsonl"
    review_packets.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": (
                    "SourceTheoremExactSemanticDefinitionVerifierApprovedReviewPacket"
                ),
                "review_packet_id": "review:covered:string-false-source-row",
                "target_theorem_name": "split_conformal_coverage",
                "target_ids": ["split_conformal_coverage"],
                "placeholder_symbol": "covered",
                "candidate_artifact_path": str(reviewed_candidate),
                "definition_only_candidate_artifact_path": str(reviewed_candidate),
                "local_definition_lean_compiled": True,
                "semantic_review_required_before_proof_body": False,
                "source_theorem_ready_for_exact_proof_body": True,
                "semantic_review_decision": "approved_definition_candidate",
                "semantic_review_status": (
                    "verifier_gate_approved_definition_candidate_not_proof"
                ),
                "semantic_review_evidence": ["verifier gate approved"],
                "source_theorem_kernel_verified": False,
                "proof_evidence_status": (
                    "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_VERIFIER_GATE_APPROVED_NOT_SOURCE_THEOREM_PROOF"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_typechecked_review_recheck_queue(
        out_dir=tmp_path / "recheck",
        review_packets_jsonl=review_packets,
        proof_body_queue_manifest=queue_manifest,
    )

    assert manifest["n_execution_queue_rows"] == 1
    assert manifest["n_live_goal_location_ready"] == 0
    rows = [
        json.loads(line)
        for line in Path(manifest["proof_body_execution_queue_jsonl"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert rows[0]["source_theorem_target_known"] is False
    assert rows[0]["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert rows[0]["live_goal_location_ready"] is False
    assert (
        rows[0]["already_repaired_environment"][
            "signature_typecheck_reached_proof_body"
        ]
        is False
    )
