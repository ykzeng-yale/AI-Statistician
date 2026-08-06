from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician import (
    source_theorem_exact_semantic_definition_lean_repair_executor as executor_module,
)
from ai_statistician.source_theorem_exact_semantic_definition_lean_repair_executor import (
    run_source_theorem_exact_semantic_definition_lean_repair_executor,
)


def test_local_lean_failure_classifier_preserves_candidate_diagnostics_for_model() -> None:
    classify = executor_module._classify_local_lean_failure

    assert classify(
        [
            "candidate.lean:31:25: error(lean.synthInstanceFailed): "
            "failed to synthesize instance of type class",
            "  FloorRing ℝ",
        ]
    ) == "local_lean_candidate_rejected"
    assert classify(
        [
            "candidate.lean:30:33: error(lean.invalidField): "
            "Invalid field `toNNReal`: The environment does not contain "
            "`Real.toNNReal`"
        ]
    ) == "local_lean_candidate_rejected"
    assert classify(
        [
            "candidate.lean:30:25: error(lean.unknownIdentifier): "
            "Unknown constant `Int.floor`"
        ]
    ) == "local_lean_candidate_rejected"


def test_lean_repair_request_uses_policy_roles_for_unannotated_source_binders() -> None:
    row = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:alpha-policy-binders",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "alpha",
        "exact_source_theorem_binders": [
            {"name": "P", "type": "MeasureTheory.Measure Ω"},
            {"name": "n2", "type": "Nat"},
            {"name": "alpha", "type": "Fin (n2 + 1) -> ℝ"},
            {"name": "s", "type": "Fin (n2 + 1) -> Ω -> ℝ"},
            {"name": "hexch", "type": "Exchangeable P s"},
        ],
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }

    request = executor_module._candidate_definition_request(
        row,
        placeholder_symbol="alpha",
    )
    binders_by_name = {
        binder["name"]: binder for binder in request["required_binders"]
    }

    assert request["missing_required_anchor_names"] == []
    assert binders_by_name["P"]["role"] == "probability_measure_anchor"
    assert binders_by_name["alpha"]["role"] == "miscoverage_level_anchor"


def _write_lean_repair_tasks(path: Path) -> None:
    rows = [
        {
            "schema_version": 1,
            "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
            "lean_repair_task_id": "lean-repair:orderStat",
            "source_repair_packet_id": "repair:orderStat",
            "source_review_packet_id": "review:orderStat",
            "source_definition_closure_work_order_id": "closure:orderStat",
            "question_id": "conformal_prediction_coverage",
            "question_title": "Split conformal prediction interval coverage",
            "target_theorem_name": "split_conformal_coverage",
            "placeholder_symbol": "orderStat",
            "lean_repair_action": "review_import_source_declaration",
            "repair_strategy": "review_import_candidate_source_declaration",
            "candidate_import_declarations": [
                {
                    "candidate_kind": "lean_declaration",
                    "path": "StatInference/Conformal/Quantile.lean",
                    "line": 12,
                    "snippet": "def reviewedOrderStat",
                }
            ],
            "source_reference_hints": [],
            "proof_evidence_status": (
                "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
            ),
        },
        {
            "schema_version": 1,
            "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
            "lean_repair_task_id": "lean-repair:Exchangeable",
            "source_repair_packet_id": "repair:Exchangeable",
            "source_review_packet_id": "review:Exchangeable",
            "source_definition_closure_work_order_id": "closure:Exchangeable",
            "question_id": "conformal_prediction_coverage",
            "target_theorem_name": "split_conformal_coverage",
            "placeholder_symbol": "Exchangeable",
            "lean_repair_action": "synthesize_exact_definition",
            "repair_strategy": "synthesize_reviewed_definition_from_source_references",
            "candidate_import_declarations": [],
            "source_reference_hints": [
                {
                    "candidate_kind": "lean_source_text_match",
                    "path": "StatInference/Conformal/Exchangeability.lean",
                    "line": 8,
                    "snippet": "finite exchangeability handoff",
                }
            ],
            "exact_source_theorem_binders": [
                {
                    "name": "hexch",
                    "role": "exchangeability_anchor",
                    "type": "Exchangeable P s",
                }
            ],
            "premise_semantic_anchor_binder_names": ["P", "s", "hexch"],
            "source_to_bridge_adapter_instantiation_group_id": (
                "adapter-instantiation:split-conformal"
            ),
            "proof_evidence_status": (
                "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
            ),
        },
    ]
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_exact_semantic_definition_lean_repair_executor_checks_import_candidate(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Quantile.lean"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("-- candidate source declaration\n", encoding="utf-8")
    _write_lean_repair_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    assert manifest["n_tasks"] == 2
    assert manifest["n_results"] == 2
    assert manifest["n_candidate_source_files_resolved"] == 1
    assert manifest["n_local_lean_checked"] == 1
    assert manifest["n_local_lean_compiled"] == 1
    assert manifest["n_import_candidate_ready_for_semantic_review"] == 1
    assert manifest["n_exact_definition_authoring_required"] == 1
    assert manifest["proofengineer_state"] == (
        "IMPORT_CANDIDATE_SEMANTIC_REVIEW_REQUIRED"
    )
    assert "source semantic review" in manifest["proofengineer_state_reason"]
    assert manifest["n_lean_environment_repair_tasks"] == 0
    assert manifest["n_exact_semantic_definition_authoring_tasks"] == 1
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["semantic_definition_kernel_verified"] is False
    assert manifest["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
    )
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in results}
    assert by_symbol["orderStat"]["execution_status"] == (
        "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LEAN_COMPILED_NOT_PROOF"
    )
    assert by_symbol["orderStat"]["candidate_source_file"] == str(source_file)
    assert by_symbol["orderStat"]["source_theorem_kernel_verified"] is False
    assert by_symbol["Exchangeable"]["execution_status"] == (
        "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN"
    )
    assert by_symbol["Exchangeable"]["candidate_source_file"] == ""
    assert by_symbol["Exchangeable"]["local_lean_checked"] is False
    assert by_symbol["Exchangeable"]["exact_source_theorem_binders"] == [
        {
            "name": "hexch",
            "role": "exchangeability_anchor",
            "type": "Exchangeable P s",
        }
    ]
    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert len(authoring_tasks) == 1
    assert authoring_tasks[0]["artifact_kind"] == (
        "SourceTheoremExactSemanticDefinitionAuthoringTask"
    )
    assert authoring_tasks[0]["placeholder_symbol"] == "Exchangeable"
    assert authoring_tasks[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING"
    )
    assert authoring_tasks[0]["premise_semantic_anchor_binder_names"] == [
        "P",
        "s",
        "hexch",
    ]
    assert authoring_tasks[0]["source_to_bridge_adapter_instantiation_group_id"] == (
        "adapter-instantiation:split-conformal"
    )
    request = authoring_tasks[0]["candidate_definition_request"]
    assert request["request_kind"] == (
        "source_theorem_exact_semantic_definition_candidate"
    )
    assert request["placeholder_symbol"] == "Exchangeable"
    assert request["required_anchor_names"] == ["P", "s"]
    assert request["available_anchor_names"] == ["P", "s", "hexch"]
    assert request["missing_required_anchor_names"] == []
    assert request["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
    )
    assert request["model_owns_candidate_and_repair_strategy"] is True
    assert request["runtime_supplies_observations_only"] is True
    assert "forbidden_shortcuts" not in request
    assert "do not add axiom/sorry/admit/unsafe" in request[
        "evidence_integrity_constraints"
    ]
    assert authoring_tasks[0]["source_theorem_kernel_verified"] is False
    assert authoring_tasks[0]["semantic_definition_kernel_verified"] is False
    assert authoring_tasks[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert {row["learning_task"] for row in learning_rows} == {
        "source_theorem_exact_semantic_definition_author_definition",
        "source_theorem_exact_semantic_definition_lean_repair_execution",
    }
    order_stat_learning = next(
        row for row in learning_rows if row["placeholder_symbol"] == "orderStat"
    )
    assert order_stat_learning["semantic_definition_import_candidate_ready"] is True
    assert order_stat_learning["runtime_queue_status"] == (
        "PENDING_REVIEWED_SEMANTIC_DEFINITION_IMPORT"
    )
    assert order_stat_learning["candidate_source_file"] == str(source_file)
    assert order_stat_learning["input_summary"]["trigger"] == (
        "EXACT_SOURCE_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION"
    )
    assert order_stat_learning["input_summary"][
        "semantic_definition_import_candidate_ready"
    ] is True
    exchangeable_learning = next(
        row
        for row in learning_rows
        if row["placeholder_symbol"] == "Exchangeable"
        and row["learning_task"]
        == "source_theorem_exact_semantic_definition_lean_repair_execution"
    )
    assert exchangeable_learning["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING"
    )
    assert exchangeable_learning["semantic_definition_authoring_required"] is True
    assert exchangeable_learning["exact_source_theorem_binders"][0]["name"] == "hexch"
    authoring_learning = next(
        row
        for row in learning_rows
        if row["learning_task"]
        == "source_theorem_exact_semantic_definition_author_definition"
    )
    assert authoring_learning["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING"
    )
    assert authoring_learning["input_summary"]["source_reference_hint_count"] == 1
    assert authoring_learning["input_summary"]["candidate_definition_request"][
        "placeholder_symbol"
    ] == "Exchangeable"
    assert authoring_learning["input_summary"]["premise_semantic_anchor_binder_names"] == [
        "P",
        "s",
        "hexch",
    ]
    assert all(
        row["proof_evidence_status"]
        == "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
        for row in learning_rows
        if row["learning_task"]
        == "source_theorem_exact_semantic_definition_lean_repair_execution"
    )


def test_lean_repair_executor_preserves_nested_required_anchor_bindings(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    nested_context = {
        "semantic_primitive": "good_rank_event",
        "source_anchor_context": [
            {
                "source": "candidate_definition_request.required_anchor_bindings",
                "kind": "required_anchor_binding",
                "required_anchor_name": "q_hat",
                "actual_anchor_name": "q",
                "semantic_anchor_name": "q_hat",
                "name": "q",
                "type": "Real",
                "role": "threshold_function_anchor",
                "binder": {
                    "name": "q",
                    "type": "Real",
                    "role": "threshold_function_anchor",
                },
            }
        ],
        "source_anchor_context_rows": 1,
        "candidate_definition_request": {
            "request_kind": "source_theorem_exact_semantic_definition_candidate",
            "placeholder_symbol": "good_rank_event",
            "required_anchor_names": ["q_hat"],
            "available_anchor_names": ["q", "q_hat"],
            "missing_required_anchor_names": [],
            "required_anchor_bindings": [
                {
                    "required_anchor_name": "q_hat",
                    "actual_anchor_name": "q",
                    "match_kind": "source_anchor_role",
                    "role": "threshold_function_anchor",
                    "binder": {
                        "name": "q",
                        "type": "Real",
                        "role": "threshold_function_anchor",
                    },
                }
            ],
            "required_binders": [
                {
                    "name": "q",
                    "type": "Real",
                    "role": "threshold_function_anchor",
                }
            ],
        },
    }
    row = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:good-rank",
        "source_repair_packet_id": "repair:good-rank",
        "source_review_packet_id": "review:good-rank",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_coverage"],
        "placeholder_symbol": "good_rank_event",
        "lean_repair_action": "author_exact_definition",
        "repair_strategy": "author_reviewed_definition_from_contract",
        "candidate_definition_request": {},
        "input_summary": {
            "exact_semantic_definition_context": nested_context,
        },
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=False,
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    result = results[0]
    assert result["execution_status"] == (
        "EXACT_DEFINITION_AUTHORING_REQUIRED_BEFORE_LOCAL_LEAN"
    )
    assert result["source_anchor_context"][0]["actual_anchor_name"] == "q"
    assert result["candidate_definition_request"]["required_anchor_bindings"][0][
        "actual_anchor_name"
    ] == "q"

    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert authoring_tasks[0]["source_anchor_context"][0]["name"] == "q"
    assert authoring_tasks[0]["candidate_definition_request"]["required_binders"][0][
        "name"
    ] == "q"

    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    repair_learning = next(
        row
        for row in learning_rows
        if row["learning_task"]
        == "source_theorem_exact_semantic_definition_lean_repair_execution"
    )
    assert repair_learning["candidate_definition_request"][
        "required_anchor_bindings"
    ][0]["actual_anchor_name"] == "q"
    authoring_learning = next(
        row
        for row in learning_rows
        if row["learning_task"]
        == "source_theorem_exact_semantic_definition_author_definition"
    )
    assert authoring_learning["candidate_definition_request"][
        "required_anchor_bindings"
    ][0]["actual_anchor_name"] == "q"
    assert authoring_learning["input_summary"]["candidate_definition_request"][
        "required_binders"
    ][0]["name"] == "q"


def test_lean_repair_executor_authoring_task_recovers_binders_from_signature_probe(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    rich_probe = tmp_path / "split_conformal_signature_probe.lean"
    rich_probe.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem split_conformal_coverage {Ω : Type _} [MeasurableSpace Ω]",
                "    (P : MeasureTheory.Measure Ω) [MeasureTheory.IsProbabilityMeasure P]",
                "    (n : ℕ) (hn : 0 < n)",
                "    (score : Fin (n + 1) → Ω → ℝ)",
                "    (q : ℝ)",
                "    (hq : ∀ᵐ ω ∂P, score (Fin.last n) ω ≤ q) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    helper_probe = tmp_path / "adapter_helper_signature_probe.lean"
    helper_probe.write_text(
        "\n".join(
            [
                "import Mathlib",
                "theorem adapter_helper (good_rank_event coverage_event : Prop)",
                "    (hC : good_rank_event -> coverage_event) :",
                "    True := by",
                "  trivial",
            ]
        ),
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:good_rank_event",
        "source_repair_packet_id": "repair:good_rank_event",
        "source_review_packet_id": "review:good_rank_event",
        "source_definition_closure_work_order_id": "closure:good_rank_event",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "good_rank_event",
        "lean_repair_action": "synthesize_exact_definition",
        "repair_strategy": "synthesize_reviewed_definition_from_source_signature",
        "signature_probe_artifact_path": str(rich_probe),
        "source_theorem_signature_probe_artifact_path": str(rich_probe),
        "candidate_definition_request": {
            "request_kind": "source_theorem_exact_semantic_definition_candidate",
            "target_theorem_name": "split_conformal_coverage",
            "placeholder_symbol": "good_rank_event",
            "signature_probe_artifact_path": str(helper_probe),
        },
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(),
        local_lean=False,
    )

    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(authoring_tasks) == 1
    request = authoring_tasks[0]["candidate_definition_request"]
    assert request["placeholder_symbol"] == "good_rank_event"
    assert request["required_anchor_names"] == ["n2", "s", "q_hat", "hq"]
    assert request["missing_required_anchor_names"] == []
    assert [binder["name"] for binder in request["required_binders"]] == [
        "n",
        "score",
        "q",
        "hq",
    ]
    assert [
        (binding["required_anchor_name"], binding["actual_anchor_name"])
        for binding in request["required_anchor_bindings"]
    ] == [
        ("hq", "hq"),
        ("n2", "n"),
        ("s", "score"),
        ("q_hat", "q"),
    ]
    assert request["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
    )
    assert authoring_tasks[0]["source_theorem_kernel_verified"] is False


def test_exact_semantic_definition_lean_repair_executor_preserves_pseudo_formal_environment_repair(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Block.lean"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("import StatInference.Missing\n", encoding="utf-8")
    pseudo_formal_origin = {
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
        "pseudo_formal_method_contract_id": (
            "pseudo_formalization_block_verification_calibration_v1"
        ),
        "pseudo_formal_pipeline_stage": "pseudo_formal_block_routing",
        "pseudo_formal_proof_evidence_status": (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        ),
    }
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:blk_exchangeable_setup",
        "source_repair_packet_id": "repair:blk_exchangeable_setup",
        "source_review_packet_id": "review:blk_exchangeable_setup",
        "source_definition_closure_work_order_id": "closure:blk_exchangeable_setup",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_coverage"],
        "placeholder_symbol": "blk_exchangeable_setup",
        "lean_repair_action": "review_import_source_declaration",
        "repair_strategy": "review_import_candidate_source_declaration",
        "candidate_import_declarations": [
            {
                "candidate_kind": "lean_declaration",
                "path": "StatInference/Conformal/Block.lean",
                "line": 1,
                "snippet": "def reviewedBlock",
            }
        ],
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
        **pseudo_formal_origin,
    }
    tasks_path.write_text(json.dumps(task) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            (
                "import sys; "
                "print(\"candidate.lean:1:0: error: unknown module prefix "
                "'StatInference'\", file=sys.stderr); "
                "sys.exit(1)"
            ),
        ),
    )

    assert manifest["n_tasks_from_pseudo_formal"] == 1
    assert manifest["n_results_from_pseudo_formal"] == 1
    assert manifest["n_local_lean_checked_from_pseudo_formal"] == 1
    assert manifest["n_lean_environment_repair_tasks_from_pseudo_formal"] == 1
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
    output_paths = [
        Path(manifest["execution_results_jsonl"]),
        Path(manifest["lean_environment_repair_tasks_jsonl"]),
        Path(manifest["runtime_learning_rows_jsonl"]),
    ]
    for output_path in output_paths:
        rows = [
            json.loads(line)
            for line in output_path.read_text(encoding="utf-8").splitlines()
        ]
        assert rows
        for row in rows:
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
            assert row["source_theorem_kernel_verified"] is False
            assert row["semantic_definition_kernel_verified"] is False
            assert row["source_theorem_ready_for_exact_proof_body"] is False
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


def test_exact_semantic_definition_lean_repair_executor_tracks_formalizer_pf_component_gate(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Coverage.lean"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("import StatInference.Missing\n", encoding="utf-8")
    exact_rows_jsonl = "runs/formalizer_pf/exact_semantic_definition_rows.jsonl"
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:coverage_event",
        "source_repair_packet_id": "repair:coverage_event",
        "source_review_packet_id": "review:coverage_event",
        "source_definition_closure_work_order_id": "closure:coverage_event",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_coverage"],
        "placeholder_symbol": "coverage_event",
        "semantic_primitive": "coverage_event",
        "semantic_primitive_requirements": ["coverage event must match source"],
        "source_component_gate": "formalizer_pseudo_formal_packet_component_gate",
        "source_component_gate_exact_rows_jsonl": exact_rows_jsonl,
        "component_eval_manifest_path": "runs/formalizer_pf/manifest.json",
        "provider_name": "anthropic",
        "backend_provider_name": "anthropic",
        "lean_repair_action": "review_import_source_declaration",
        "repair_strategy": "review_import_candidate_source_declaration",
        "candidate_import_declarations": [
            {
                "candidate_kind": "lean_declaration",
                "path": "StatInference/Conformal/Coverage.lean",
                "line": 1,
                "snippet": "def coverage_event",
            }
        ],
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            (
                "import sys; "
                "print(\"candidate.lean:1:0: error: unknown module prefix "
                "'StatInference'\", file=sys.stderr); "
                "sys.exit(1)"
            ),
        ),
    )

    assert manifest["n_tasks_from_pseudo_formal"] == 1
    assert manifest["n_tasks_from_formalizer_pf_component_gate"] == 1
    assert manifest["n_results_from_pseudo_formal"] == 1
    assert manifest["n_results_from_formalizer_pf_component_gate"] == 1
    assert manifest["n_local_lean_checked_from_pseudo_formal"] == 1
    assert manifest["n_local_lean_checked_from_formalizer_pf_component_gate"] == 1
    assert manifest["n_lean_environment_repair_tasks_from_pseudo_formal"] == 1
    assert (
        manifest[
            "n_lean_environment_repair_tasks_from_formalizer_pf_component_gate"
        ]
        == 1
    )
    assert manifest["formalizer_pf_component_gate_exact_rows_jsonl_paths"] == [
        exact_rows_jsonl
    ]

    for output_key in (
        "execution_results_jsonl",
        "lean_environment_repair_tasks_jsonl",
        "runtime_learning_rows_jsonl",
    ):
        output_path = Path(manifest[output_key])
        rows = [
            json.loads(line)
            for line in output_path.read_text(encoding="utf-8").splitlines()
        ]
        assert rows
        for row in rows:
            assert (
                row["source_component_gate"]
                == "formalizer_pseudo_formal_packet_component_gate"
            )
            assert row["source_component_gate_exact_rows_jsonl"] == exact_rows_jsonl
            assert row["semantic_primitive"] == "coverage_event"
            assert row["source_theorem_kernel_verified"] is False
            assert "KERNEL_VERIFIED" not in row["proof_evidence_status"]


def test_exact_semantic_definition_lean_repair_executor_preserves_typechecked_candidate(
    tmp_path: Path,
) -> None:
    typechecked_status = (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_LOCAL_LEAN_COMPILED_"
        "REVIEW_REQUIRED"
    )
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "def reviewedExchangeable : Prop := True\n",
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:Exchangeable:typechecked",
        "source_repair_packet_id": "repair:Exchangeable",
        "source_review_packet_id": "review:Exchangeable",
        "source_definition_closure_work_order_id": "closure:Exchangeable",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_coverage"],
        "placeholder_symbol": "Exchangeable",
        "materialization_order_index": 4,
        "lean_repair_action": "synthesize_exact_definition",
        "repair_strategy": "synthesize_reviewed_definition_from_source_references",
        "source_execution_status": (
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
        ),
        "authoring_trigger": (
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
        ),
        "authoring_mode": "repair_typechecked_semantic_definition_candidate",
        "source_lean_repair_action": "review_typechecked_exact_definition_candidate",
        "source_repair_strategy": "review_typechecked_exact_definition_candidate",
        "candidate_repair_feedback": {
            "failure_classification": "semantic_definition_review_blocked",
            "recommended_next_action": "repair semantic blockers",
        },
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "candidate_artifact_path": str(tmp_path / "candidate_full.lean"),
        "local_definition_lean_checked": True,
        "local_definition_lean_compiled": True,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
        ),
        "semantic_review_decision": "approved_definition_candidate",
        "semantic_review_status": (
            "llm_semantic_review_approved_definition_candidate_not_proof"
        ),
        "semantic_review_evidence": [
            "checked Exchangeable against source theorem binders"
        ],
        "semantic_review_required_before_proof_body": True,
        "llm_claimed_source_theorem_ready_for_exact_proof_body": True,
        "source_theorem_exact_semantic_definition_typechecked_candidate": {
            "definition_only_candidate_artifact_path": str(definition_only_candidate),
            "local_definition_lean_compiled": True,
            "semantic_definition_typecheck_evidence_status": (
                "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
            ),
        },
        "source_to_bridge_adapter_instantiation_group_id": (
            "source_to_bridge_adapter_instantiation_group:split-conformal"
        ),
        "required_adapter_object_names": ["rank"],
        "available_adapter_object_names": ["covered", "rank"],
        "missing_required_adapter_object_names": [],
        "candidate_definition_request": {
            "schema_version": 1,
            "request_kind": "source_theorem_exact_semantic_definition_candidate",
            "required_adapter_object_names": ["rank"],
            "available_adapter_object_names": ["covered", "rank"],
            "missing_required_adapter_object_names": [],
        },
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    assert manifest["n_tasks"] == 1
    assert manifest["n_local_lean_checked"] == 1
    assert manifest["n_local_lean_compiled"] == 1
    assert manifest["n_typechecked_candidate_review_ready"] == 1
    assert manifest["n_typechecked_candidate_review_packets"] == 1
    assert manifest["n_typechecked_candidate_semantic_review_blocked"] == 0
    assert manifest["n_exact_semantic_definition_authoring_tasks"] == 1
    assert manifest["n_exact_semantic_definition_authoring_repair_tasks"] == 0
    assert (
        manifest["n_exact_semantic_definition_candidate_review_authoring_tasks"] == 1
    )
    assert manifest["proofengineer_state"] == (
        "TYPECHECKED_CANDIDATE_SEMANTIC_REVIEW_REQUIRED"
    )
    assert "source semantic faithfulness" in manifest["proofengineer_state_reason"]
    assert manifest["source_theorem_kernel_verified"] is False
    assert manifest["semantic_definition_kernel_verified"] is False
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
    )
    assert results[0]["target_ids"] == ["split_conformal_coverage"]
    assert results[0]["runtime_queue_status"] == (
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
    )
    assert results[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert results[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert results[0]["source_repair_strategy"] == (
        "review_typechecked_exact_definition_candidate"
    )
    assert results[0]["candidate_repair_feedback"]["failure_classification"] == (
        "semantic_definition_review_blocked"
    )
    assert results[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    assert results[0]["definition_only_candidate_file_resolved"] is True
    assert results[0]["local_definition_lean_compiled"] is True
    assert results[0]["materialization_order_index"] == 4
    assert results[0]["required_adapter_object_names"] == ["rank"]
    assert results[0]["candidate_definition_request"][
        "available_adapter_object_names"
    ] == ["covered", "rank"]
    assert results[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "Exchangeable"
    )
    assert results[0]["candidate_definition_request"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    assert results[0]["semantic_definition_typecheck_evidence_status"] == (
        typechecked_status
    )
    assert results[0]["semantic_review_decision"] == "approved_definition_candidate"
    assert results[0]["semantic_review_status"] == (
        "llm_semantic_review_approved_definition_candidate_not_proof"
    )
    assert results[0]["semantic_review_evidence"] == [
        "checked Exchangeable against source theorem binders"
    ]
    assert results[0]["semantic_review_required_before_proof_body"] is True
    assert (
        results[0]["llm_claimed_source_theorem_ready_for_exact_proof_body"] is True
    )
    assert results[0]["source_theorem_kernel_verified"] is False
    assert results[0]["semantic_definition_kernel_verified"] is False
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["typechecked_candidate_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert len(review_packets) == 1
    assert review_packets[0]["artifact_kind"] == (
        "SourceTheoremExactSemanticDefinitionTypecheckedCandidateReviewPacket"
    )
    assert review_packets[0]["target_ids"] == ["split_conformal_coverage"]
    assert review_packets[0]["semantic_review_required_before_proof_body"] is True
    assert review_packets[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert review_packets[0]["semantic_definition_kernel_verified"] is False
    assert review_packets[0]["source_theorem_kernel_verified"] is False
    assert review_packets[0]["materialization_order_index"] == 4
    assert review_packets[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert review_packets[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert review_packets[0]["source_repair_strategy"] == (
        "review_typechecked_exact_definition_candidate"
    )
    assert review_packets[0]["candidate_repair_feedback"][
        "failure_classification"
    ] == "semantic_definition_review_blocked"
    assert review_packets[0]["required_adapter_object_names"] == ["rank"]
    assert review_packets[0]["available_adapter_object_names"] == ["covered", "rank"]
    assert review_packets[0]["missing_required_adapter_object_names"] == []
    assert review_packets[0]["candidate_definition_request"][
        "missing_required_adapter_object_names"
    ] == []
    assert review_packets[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "Exchangeable"
    )
    assert review_packets[0]["candidate_definition_request"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    assert review_packets[0]["semantic_definition_typecheck_evidence_status"] == (
        typechecked_status
    )
    assert review_packets[0]["semantic_review_decision"] == (
        "approved_definition_candidate"
    )
    assert review_packets[0]["semantic_review_status"] == (
        "llm_semantic_review_approved_definition_candidate_not_proof"
    )
    assert review_packets[0]["semantic_review_evidence"] == [
        "checked Exchangeable against source theorem binders"
    ]
    assert (
        review_packets[0]["llm_claimed_source_theorem_ready_for_exact_proof_body"]
        is True
    )
    assert review_packets[0]["runtime_queue_status"] == (
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
    )
    assert review_packets[0]["proof_evidence_status"] == (
        "TYPECHECKED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_NOT_PROOF_EVIDENCE"
    )
    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert len(authoring_tasks) == 1
    assert authoring_tasks[0]["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
    )
    assert authoring_tasks[0]["authoring_mode"] == (
        "review_typechecked_semantic_definition_candidate"
    )
    assert authoring_tasks[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
    )
    assert authoring_tasks[0]["prior_source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert authoring_tasks[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_AUTHORING"
    )
    assert (
        authoring_tasks[0]["semantic_review_required_before_proof_body"] is True
    )
    assert authoring_tasks[0]["source_theorem_ready_for_exact_proof_body"] is False
    assert authoring_tasks[0]["semantic_review_contract"][
        "review_decision_values"
    ] == [
        "approved_definition_candidate",
        "repair_required",
        "blocked_or_insufficient_context",
    ]
    assert authoring_tasks[0]["semantic_review_contract"][
        "source_theorem_ready_for_exact_proof_body"
    ] is False
    assert "LLM semantic review evidence is not source theorem proof" in (
        authoring_tasks[0]["semantic_review_contract"]["proof_body_promotion_gate"]
    )
    assert authoring_tasks[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    assert authoring_tasks[0]["candidate_artifact_path"] == str(
        tmp_path / "candidate_full.lean"
    )
    assert authoring_tasks[0]["local_definition_lean_compiled"] is True
    assert authoring_tasks[0]["semantic_definition_kernel_verified"] is False
    assert authoring_tasks[0]["source_theorem_kernel_verified"] is False
    assert authoring_tasks[0]["model_owns_candidate_and_repair_strategy"] is True
    assert authoring_tasks[0]["runtime_supplies_observations_only"] is True
    assert "authoring_policy" not in authoring_tasks[0]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert len(learning_rows) == 2
    assert learning_rows[0][
        "semantic_definition_typechecked_candidate_review_ready"
    ] is True
    assert learning_rows[0]["runtime_queue_status"] == (
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
    )
    assert learning_rows[0]["target_ids"] == ["split_conformal_coverage"]
    assert learning_rows[0]["input_summary"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    assert learning_rows[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "Exchangeable"
    )
    assert learning_rows[0]["input_summary"]["candidate_definition_request"][
        "placeholder_symbol"
    ] == "Exchangeable"
    assert learning_rows[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert learning_rows[0]["input_summary"]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert learning_rows[0]["candidate_repair_feedback"][
        "recommended_next_action"
    ] == "repair semantic blockers"
    assert learning_rows[0]["semantic_review_decision"] == (
        "approved_definition_candidate"
    )
    assert learning_rows[0]["input_summary"]["semantic_review_decision"] == (
        "approved_definition_candidate"
    )
    assert learning_rows[0]["input_summary"][
        "semantic_definition_typecheck_evidence_status"
    ] == typechecked_status
    assert learning_rows[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
    )
    assert learning_rows[1]["learning_task"] == (
        "source_theorem_exact_semantic_definition_author_definition"
    )
    assert learning_rows[1]["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
    )
    assert learning_rows[1]["authoring_mode"] == (
        "review_typechecked_semantic_definition_candidate"
    )
    assert learning_rows[1]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW_AUTHORING"
    )
    assert learning_rows[1]["input_summary"]["source_theorem_kernel_verified"] is False


def test_exact_semantic_definition_lean_repair_executor_string_false_review_flags_stay_false(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "def reviewedExchangeable : Prop := True\n",
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:Exchangeable:string-false",
        "source_repair_packet_id": "repair:Exchangeable",
        "source_review_packet_id": "review:Exchangeable",
        "source_definition_closure_work_order_id": "closure:Exchangeable",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_coverage"],
        "placeholder_symbol": "Exchangeable",
        "lean_repair_action": "review_typechecked_exact_definition_candidate",
        "repair_strategy": "review_typechecked_exact_definition_candidate",
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "candidate_artifact_path": str(tmp_path / "candidate_full.lean"),
        "local_definition_lean_checked": True,
        "local_definition_lean_compiled": True,
        "semantic_review_required_before_proof_body": "false",
        "llm_claimed_source_theorem_ready_for_exact_proof_body": "false",
        "source_theorem_exact_semantic_definition_typechecked_candidate": {
            "definition_only_candidate_artifact_path": str(definition_only_candidate),
            "local_definition_lean_checked": True,
            "local_definition_lean_compiled": True,
        },
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    assert manifest["n_typechecked_candidate_review_ready"] == 1
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
    )
    assert results[0]["semantic_review_required_before_proof_body"] is False
    assert (
        results[0]["llm_claimed_source_theorem_ready_for_exact_proof_body"] is False
    )
    review_packets = [
        json.loads(line)
        for line in Path(
            manifest["typechecked_candidate_review_packets_jsonl"]
        ).read_text().splitlines()
    ]
    assert (
        review_packets[0]["llm_claimed_source_theorem_ready_for_exact_proof_body"]
        is False
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["semantic_review_required_before_proof_body"] is False
    assert (
        learning_rows[0]["llm_claimed_source_theorem_ready_for_exact_proof_body"]
        is False
    )
    assert (
        learning_rows[0]["input_summary"][
            "semantic_review_required_before_proof_body"
        ]
        is False
    )
    assert (
        learning_rows[0]["input_summary"][
            "llm_claimed_source_theorem_ready_for_exact_proof_body"
        ]
        is False
    )


def test_authoring_task_exports_structured_candidate_definition_request(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:covered",
        "source_repair_packet_id": "repair:covered",
        "source_review_packet_id": "review:covered",
        "source_definition_closure_work_order_id": "closure:covered",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "covered",
        "lean_repair_action": "synthesize_exact_definition",
        "repair_strategy": "synthesize_reviewed_definition_from_source_references",
        "source_reference_hints": [],
        "exact_source_theorem_binders": [
            {"name": "s", "role": "score_process_anchor", "type": "Fin (n2 + 1) → Ω → ℝ"},
            {"name": "q_hat", "role": "threshold_function_anchor", "type": "Ω → ℝ"},
            {"name": "C", "role": "prediction_set_family_anchor", "type": "(Ω → ℝ) → Set ℝ"},
            {"name": "hC", "role": "coverage_event_anchor", "type": "∀ ω, C ..."},
        ],
        "premise_semantic_anchor_binder_names": ["s", "q_hat", "C", "hC"],
        "source_to_bridge_adapter_instantiation_group_id": (
            "source_to_bridge_adapter_instantiation_group:covered"
        ),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert manifest["n_exact_semantic_definition_authoring_tasks"] == 1
    assert manifest["n_tasks_with_placeholder_policy_lineage"] == 0
    assert manifest["n_results_with_placeholder_policy_lineage"] == 1
    assert (
        manifest[
            "n_exact_semantic_definition_authoring_tasks_with_placeholder_policy_lineage"
        ]
        == 1
    )
    assert manifest["n_runtime_learning_rows_with_placeholder_policy_lineage"] == 2
    assert manifest["placeholder_policy_lineage_complete"] is True
    request = authoring_tasks[0]["candidate_definition_request"]
    assert request["placeholder_symbol"] == "covered"
    assert request["placeholder_policy_id"] == "split_conformal_coverage.covered"
    assert request["placeholder_policy_scope"] == "split_conformal_coverage"
    assert request["required_anchor_names"] == ["s", "q_hat", "C", "hC"]
    assert request["missing_required_anchor_names"] == []
    assert [binder["name"] for binder in request["required_binders"]] == [
        "s",
        "q_hat",
        "C",
        "hC",
    ]
    assert "hC" in request["semantic_goal"]
    assert request["source_to_bridge_adapter_instantiation_group_id"] == (
        "source_to_bridge_adapter_instantiation_group:covered"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    authoring_learning = next(
        row
        for row in learning_rows
        if row["learning_task"]
        == "source_theorem_exact_semantic_definition_author_definition"
    )
    assert authoring_learning["candidate_definition_request"]["required_anchor_names"] == [
        "s",
        "q_hat",
        "C",
        "hC",
    ]
    assert authoring_learning["input_summary"]["candidate_definition_request"][
        "missing_required_anchor_names"
    ] == []
    assert request["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
    )


def test_authoring_task_request_uses_premise_semantic_binders(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:rank",
        "source_repair_packet_id": "repair:rank",
        "source_review_packet_id": "review:rank",
        "source_definition_closure_work_order_id": "closure:rank",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "rank",
        "lean_repair_action": "synthesize_exact_definition",
        "repair_strategy": "synthesize_reviewed_definition_from_source_references",
        "source_reference_hints": [],
        "exact_source_theorem_binders": [
            {"name": "n2", "role": "calibration_size_anchor", "type": "ℕ"},
            {
                "name": "s",
                "role": "score_process_anchor",
                "type": "Fin (n2 + 1) → Ω → ℝ",
            },
            {"name": "q_hat", "role": "threshold_function_anchor", "type": "Ω → ℝ"},
        ],
        "premise_semantic_anchor_binders": [
            {
                "name": "hq",
                "role": "quantile_definition_anchor",
                "type": "q_hat = fun ω => orderStat s k ω",
            }
        ],
        "premise_semantic_anchor_binder_names": ["n2", "s", "q_hat", "hq"],
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=False,
    )

    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    request = authoring_tasks[0]["candidate_definition_request"]
    assert request["required_anchor_names"] == ["n2", "s", "q_hat", "hq"]
    assert request["missing_required_anchor_names"] == []
    assert [binder["name"] for binder in request["required_binders"]] == [
        "n2",
        "s",
        "q_hat",
        "hq",
    ]


def test_authoring_task_exports_adapter_object_dependencies(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:alpha-total",
        "source_repair_packet_id": "repair:alpha-total",
        "source_review_packet_id": "review:alpha-total",
        "source_definition_closure_work_order_id": "closure:alpha-total",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "α_total",
        "lean_repair_action": "author_exact_definition",
        "repair_strategy": "author_reviewed_definition_from_contract",
        "source_reference_hints": [],
        "exact_source_theorem_binders": [
            {"name": "n2", "role": "calibration_size_anchor", "type": "ℕ"},
            {"name": "alpha", "role": "miscoverage_level_anchor", "type": "ℝ"},
            {
                "name": "halpha",
                "role": "miscoverage_level_anchor",
                "type": "0 < alpha ∧ alpha < 1",
            },
        ],
        "premise_semantic_anchor_binder_names": ["n2", "alpha", "halpha"],
        "source_to_bridge_adapter_object_names_requiring_source_instantiation": [
            "covered",
            "rank",
            "BadRanks",
            "α",
            "α_total",
        ],
        "source_to_bridge_adapter_instantiation_group_id": (
            "source_to_bridge_adapter_instantiation_group:split-conformal"
        ),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=False,
    )

    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    request = authoring_tasks[0]["candidate_definition_request"]
    assert request["placeholder_symbol"] == "α_total"
    assert request["placeholder_policy_id"] == "split_conformal_coverage.alpha_total"
    assert request["placeholder_policy_scope"] == "split_conformal_coverage"
    assert request["required_anchor_names"] == ["n2", "alpha", "halpha"]
    assert request["missing_required_anchor_names"] == []
    assert request["required_adapter_object_names"] == ["BadRanks"]
    assert request["available_adapter_object_names"] == [
        "covered",
        "rank",
        "BadRanks",
        "α",
        "α_total",
    ]
    assert request["missing_required_adapter_object_names"] == []
    assert "BadRanks" in request["semantic_goal"]
    assert request["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
    )


def test_typechecked_definition_candidate_with_semantic_blockers_is_not_review_ready(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "def reviewedOrderStat (k : Nat) : Nat := 0\n",
        encoding="utf-8",
    )
    blocker = "draft finite maximum ignores rank k"
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:orderStat:blockers",
        "source_repair_packet_id": "repair:orderStat",
        "source_review_packet_id": "review:orderStat",
        "source_definition_closure_work_order_id": "closure:orderStat",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "orderStat",
        "lean_repair_action": "review_typechecked_exact_definition_candidate",
        "repair_strategy": "review_typechecked_exact_definition_candidate",
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "semantic_alignment_blockers": [blocker],
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    assert manifest["n_tasks"] == 1
    assert manifest["n_local_lean_checked"] == 1
    assert manifest["n_local_lean_compiled"] == 1
    assert manifest["n_typechecked_candidate_review_ready"] == 0
    assert manifest["n_typechecked_candidate_semantic_review_blocked"] == 1
    assert manifest["n_exact_semantic_definition_authoring_tasks"] == 1
    assert manifest["n_exact_semantic_definition_authoring_repair_tasks"] == 1
    assert manifest["proofengineer_state"] == "SEMANTIC_REVIEW_BLOCKED"
    assert "semantic review blockers" in manifest["proofengineer_state_reason"]
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert results[0]["failure_classification"] == "semantic_definition_review_blocked"
    assert results[0]["semantic_alignment_blockers"] == [blocker]
    assert "semantic alignment blockers" in results[0]["recommended_next_action"]
    assert results[0]["source_theorem_kernel_verified"] is False
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0][
        "semantic_definition_typechecked_candidate_review_ready"
    ] is False
    assert learning_rows[0][
        "semantic_definition_typechecked_candidate_semantic_review_blocked"
    ] is True
    assert learning_rows[0]["runtime_queue_status"] == (
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_REPAIR"
    )
    assert learning_rows[0]["semantic_alignment_blockers"] == [blocker]
    assert learning_rows[0]["input_summary"]["semantic_alignment_blockers"] == [
        blocker
    ]
    assert learning_rows[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
    )
    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert len(authoring_tasks) == 1
    assert authoring_tasks[0]["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
    )
    assert authoring_tasks[0]["authoring_mode"] == (
        "repair_typechecked_semantic_definition_candidate"
    )
    assert authoring_tasks[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    )
    assert authoring_tasks[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    )
    assert authoring_tasks[0]["semantic_alignment_blockers"] == [blocker]
    assert authoring_tasks[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    assert authoring_tasks[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_TASK_NOT_PROOF_EVIDENCE"
    )
    assert len(learning_rows) == 2
    assert learning_rows[1]["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
    )
    assert learning_rows[1]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    )
    assert learning_rows[1]["input_summary"]["semantic_alignment_blockers"] == [
        blocker
    ]


def test_definition_candidate_without_local_lean_is_not_marked_typechecked(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "def reviewedExchangeable : Prop := True\n",
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:Exchangeable:unchecked",
        "source_repair_packet_id": "repair:Exchangeable",
        "source_review_packet_id": "review:Exchangeable",
        "source_definition_closure_work_order_id": "closure:Exchangeable",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "Exchangeable",
        "lean_repair_action": "author_exact_definition",
        "repair_strategy": "author_reviewed_definition_from_contract",
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "candidate_artifact_path": str(tmp_path / "candidate_full.lean"),
        "local_definition_lean_checked": False,
        "local_definition_lean_compiled": False,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECK_NOT_ESTABLISHED"
        ),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=False,
    )

    assert manifest["n_tasks"] == 1
    assert manifest["n_local_lean_checked"] == 0
    assert manifest["n_local_lean_compiled"] == 0
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_NOT_REQUESTED"
    )
    assert results[0]["definition_only_candidate_file_resolved"] is True
    assert results[0]["local_definition_lean_checked"] is False
    assert results[0]["local_definition_lean_compiled"] is False
    assert results[0]["failure_classification"] == ""
    assert "run the exact semantic-definition Lean repair executor with local Lean" in (
        results[0]["recommended_next_action"]
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0][
        "semantic_definition_typechecked_candidate_review_ready"
    ] is False
    assert learning_rows[0]["semantic_definition_local_lean_check_pending"] is True
    assert learning_rows[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_LOCAL_LEAN_CHECK"
    )
    assert learning_rows[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
    )


def test_definition_candidate_import_environment_failure_recommends_lake_project(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    lean_project = tmp_path / "LeanProject"
    lean_project.mkdir()
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "import Mathlib.Data.Real.Basic\n\n"
        "def reviewedExchangeable : Prop := True\n",
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:Exchangeable:import-env",
        "source_repair_packet_id": "repair:Exchangeable",
        "source_review_packet_id": "review:Exchangeable",
        "source_definition_closure_work_order_id": "closure:Exchangeable",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "Exchangeable",
        "lean_repair_action": "author_exact_definition",
        "repair_strategy": "author_reviewed_definition_from_contract",
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "candidate_artifact_path": str(tmp_path / "candidate_full.lean"),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
        lean_project=lean_project,
        lean_command=(
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stderr.write(\"error: unknown module prefix 'Mathlib'\\n"
                "No directory 'Mathlib' or file 'Mathlib.olean'\\n\"); "
                "sys.exit(1)"
            ),
        ),
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING"
    )
    assert results[0]["failure_classification"] == "lean_import_environment_missing"
    assert results[0]["candidate_lean_project_hint"] == str(lean_project)
    assert "Lake project" in results[0]["recommended_next_action"]
    assert "proof-body search" in results[0]["recommended_next_action"]
    assert results[0]["source_theorem_kernel_verified"] is False
    assert results[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_EXECUTION_NOT_SOURCE_THEOREM_PROOF"
    )
    assert manifest["n_lean_environment_repair_tasks"] == 1
    assert manifest["n_exact_semantic_definition_authoring_tasks"] == 1
    assert manifest["n_exact_semantic_definition_authoring_repair_tasks"] == 1
    environment_tasks = [
        json.loads(line)
        for line in Path(
            manifest["lean_environment_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert environment_tasks[0]["candidate_source_file"] == str(
        definition_only_candidate
    )
    assert environment_tasks[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert authoring_tasks[0]["authoring_trigger"] == (
        "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
    )
    assert authoring_tasks[0]["authoring_mode"] == (
        "repair_failed_exact_semantic_definition_candidate"
    )
    assert authoring_tasks[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING"
    )
    assert authoring_tasks[0]["failure_classification"] == (
        "lean_import_environment_missing"
    )
    assert authoring_tasks[0]["candidate_lean_project_hint"] == str(lean_project)
    assert authoring_tasks[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    assert "unknown module prefix" in "\n".join(
        authoring_tasks[0]["local_lean_diagnostics"]
    )
    assert authoring_tasks[0]["candidate_repair_feedback"][
        "definition_only_candidate_artifact_path"
    ] == str(definition_only_candidate)
    assert authoring_tasks[0]["candidate_repair_feedback"][
        "failure_classification"
    ] == "lean_import_environment_missing"
    assert authoring_tasks[0]["candidate_repair_feedback"][
        "candidate_lean_project_hint"
    ] == str(lean_project)
    assert "unknown module prefix" in "\n".join(
        authoring_tasks[0]["candidate_repair_feedback"]["local_lean_diagnostics"]
    )


def test_definition_candidate_local_lean_failure_creates_authoring_repair_task(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "def reviewedCovered : Prop := by exact True\n",
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:covered:local-failure",
        "source_repair_packet_id": "repair:covered",
        "source_review_packet_id": "review:covered",
        "source_definition_closure_work_order_id": "closure:covered",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "covered",
        "lean_repair_action": "author_exact_definition",
        "repair_strategy": "author_reviewed_definition_from_contract",
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "candidate_artifact_path": str(tmp_path / "candidate_full.lean"),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stderr.write('application type mismatch\\n'); "
                "sys.exit(1)"
            ),
        ),
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LOCAL_LEAN_FAILED"
    )
    assert results[0]["failure_classification"] == "local_lean_candidate_rejected"
    assert manifest["dominant_failure_classification"] == (
        "local_lean_candidate_rejected"
    )
    assert manifest["by_failure_classification"] == {
        "local_lean_candidate_rejected": 1
    }
    assert manifest["n_lean_environment_repair_tasks"] == 0
    assert manifest["n_exact_semantic_definition_authoring_tasks"] == 1
    assert manifest["n_exact_semantic_definition_authoring_repair_tasks"] == 1
    authoring_tasks = [
        json.loads(line)
        for line in Path(
            manifest["exact_semantic_definition_authoring_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert authoring_tasks[0]["authoring_mode"] == (
        "repair_failed_exact_semantic_definition_candidate"
    )
    assert authoring_tasks[0]["runtime_queue_status"] == (
        "PENDING_EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR"
    )
    assert (
        authoring_tasks[0]["semantic_review_required_before_proof_body"] is True
    )
    assert authoring_tasks[0]["semantic_review_contract"][
        "semantic_review_required_before_proof_body"
    ] is True
    assert "proof-body" in authoring_tasks[0]["semantic_review_contract"][
        "proof_body_promotion_gate"
    ]
    assert authoring_tasks[0]["definition_only_candidate_artifact_path"] == str(
        definition_only_candidate
    )
    assert "application type mismatch" in "\n".join(
        authoring_tasks[0]["local_lean_diagnostics"]
    )
    assert authoring_tasks[0]["candidate_repair_feedback"][
        "definition_only_candidate_artifact_path"
    ] == str(definition_only_candidate)
    assert authoring_tasks[0]["candidate_repair_feedback"][
        "failure_classification"
    ] == "local_lean_candidate_rejected"
    assert "application type mismatch" in "\n".join(
        authoring_tasks[0]["candidate_repair_feedback"]["local_lean_diagnostics"]
    )
    assert authoring_tasks[0]["source_theorem_kernel_verified"] is False
    assert authoring_tasks[0]["semantic_definition_kernel_verified"] is False


def test_typechecked_definition_candidate_without_project_does_not_create_false_env_blocker(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "import Mathlib.Data.Real.Basic\n\n"
        "def reviewedExchangeable : Prop := True\n",
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:Exchangeable:typechecked:no-project",
        "source_repair_packet_id": "repair:Exchangeable",
        "source_review_packet_id": "review:Exchangeable",
        "source_definition_closure_work_order_id": "closure:Exchangeable",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "Exchangeable",
        "lean_repair_action": "synthesize_exact_definition",
        "repair_strategy": "synthesize_reviewed_definition_from_source_references",
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "local_definition_lean_checked": True,
        "local_definition_lean_compiled": True,
        "semantic_definition_typecheck_evidence_status": (
            "SEMANTIC_DEFINITION_CANDIDATE_TYPECHECKED_NOT_PROOF"
        ),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
    )

    assert manifest["n_tasks"] == 1
    assert manifest["n_local_lean_checked"] == 0
    assert manifest["n_lean_environment_repair_tasks"] == 0
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
    )
    assert results[0]["local_lean_checked"] is False
    assert results[0]["local_definition_lean_checked"] is True
    assert results[0]["local_definition_lean_compiled"] is True
    assert results[0]["failure_classification"] == ""
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["local_definition_lean_checked"] is True
    assert learning_rows[0]["runtime_queue_status"] == (
        "PENDING_REVIEWED_EXACT_SEMANTIC_DEFINITION_CANDIDATE_REVIEW"
    )


def test_exact_semantic_definition_lean_repair_executor_blocks_semantic_mismatch_import(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "AsymptoticStatistics" / "LStatistics.lean"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("-- compiles, but not exact orderStat semantics\n", encoding="utf-8")
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:sample-mean",
        "source_repair_packet_id": "repair:sample-mean",
        "source_review_packet_id": "review:sample-mean",
        "source_definition_closure_work_order_id": "closure:orderStat",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "orderStat",
        "lean_repair_action": "review_import_source_declaration",
        "repair_strategy": "review_import_candidate_source_declaration",
        "candidate_import_declarations": [
            {
                "candidate_kind": "lean_declaration",
                "path": "StatInference/AsymptoticStatistics/LStatistics.lean",
                "line": 35,
                "snippet": "def vaart1998_orderStatisticSampleMean",
            }
        ],
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == "IMPORT_CANDIDATE_SEMANTIC_REVIEW_BLOCKED"
    assert results[0]["local_lean_checked"] is False
    assert results[0]["local_lean_compiled"] is False
    assert "aggregate/range/CDF display" in results[0]["semantic_import_blocker"]
    assert "placeholder policy" in results[0]["semantic_import_blocker"]
    assert "SEMANTIC_MISMATCH_NOT_EXACT_ORDER_STATISTIC" in results[0][
        "semantic_import_blocker"
    ]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["semantic_definition_import_candidate_ready"] is False
    assert learning_rows[0]["runtime_queue_status"] == ""


def test_exact_semantic_definition_lean_repair_executor_classifies_import_environment(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Quantile.lean"
    source_file.parent.mkdir(parents=True)
    (source_root / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    source_file.write_text("import StatInference.Missing\n", encoding="utf-8")
    _write_lean_repair_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print(\"error: unknown module prefix 'StatInference'\", "
            "file=sys.stderr); sys.exit(1)",
        ),
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in results}
    assert by_symbol["orderStat"]["execution_status"] == (
        "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_IMPORT_ENVIRONMENT_MISSING"
    )
    assert by_symbol["orderStat"]["failure_classification"] == (
        "lean_import_environment_missing"
    )
    assert by_symbol["orderStat"]["candidate_lean_project_hint"] == str(source_root)
    assert "Lake project" in by_symbol["orderStat"]["recommended_next_action"]
    assert by_symbol["orderStat"]["source_theorem_kernel_verified"] is False
    assert manifest["n_lean_environment_repair_tasks"] == 1
    repair_tasks = [
        json.loads(line)
        for line in Path(
            manifest["lean_environment_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert repair_tasks[0]["artifact_kind"] == (
        "SourceTheoremExactSemanticDefinitionLeanEnvironmentRepairTask"
    )
    assert repair_tasks[0]["candidate_lean_project_hint"] == str(source_root)
    assert repair_tasks[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "orderStat"
    )
    assert repair_tasks[0]["candidate_definition_request"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    assert repair_tasks[0]["runtime_queue_status"] == (
        "PENDING_LEAN_IMPORT_ENVIRONMENT_REPAIR"
    )
    assert repair_tasks[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_TASK_NOT_PROOF_EVIDENCE"
    )
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert any(
        row["learning_task"]
        == "source_theorem_exact_semantic_definition_lean_environment_repair"
        for row in learning_rows
    )
    environment_learning = [
        row
        for row in learning_rows
        if row["learning_task"]
        == "source_theorem_exact_semantic_definition_lean_environment_repair"
    ][0]
    assert environment_learning["candidate_definition_request"][
        "placeholder_symbol"
    ] == "orderStat"
    assert environment_learning["input_summary"]["candidate_definition_request"][
        "target_ids"
    ] == ["split_conformal_coverage"]


def test_exact_semantic_definition_environment_task_uses_explicit_lean_project(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "external_src"
    source_file = source_root / "StatInference" / "Conformal" / "Quantile.lean"
    lean_project = tmp_path / "exact_project"
    source_file.parent.mkdir(parents=True)
    lean_project.mkdir()
    (lean_project / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    source_file.write_text("import StatInference.Missing\n", encoding="utf-8")
    _write_lean_repair_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_project=lean_project,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print(\"error: unknown module prefix 'StatInference'\", "
            "file=sys.stderr); sys.exit(1)",
        ),
    )

    repair_tasks = [
        json.loads(line)
        for line in Path(
            manifest["lean_environment_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]

    assert repair_tasks[0]["candidate_source_file"] == str(source_file)
    assert repair_tasks[0]["candidate_lean_project_hint"] == str(lean_project)
    assert repair_tasks[0]["recommended_command"] == f"lake env lean {source_file}"
    assert repair_tasks[0]["candidate_definition_request"]["target_ids"] == [
        "split_conformal_coverage"
    ]


def test_exact_semantic_definition_lean_repair_executor_classifies_local_library_build(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Quantile.lean"
    missing_object = (
        source_root
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / "StatInference"
        / "AsymptoticStatistics"
        / "LStatistics.olean"
    )
    source_file.parent.mkdir(parents=True)
    (source_root / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    source_file.write_text("import StatInference.AsymptoticStatistics.LStatistics\n", encoding="utf-8")
    _write_lean_repair_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print(\"error: object file '"
            + str(missing_object)
            + "' of module StatInference.AsymptoticStatistics.LStatistics does not "
            "exist\", file=sys.stderr); sys.exit(1)",
        ),
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in results}
    assert by_symbol["orderStat"]["execution_status"] == (
        "IMPORT_CANDIDATE_SOURCE_FILE_LOCAL_LIBRARY_BUILD_UNRESOLVED"
    )
    assert by_symbol["orderStat"]["failure_classification"] == (
        "lean_local_library_build_unresolved"
    )
    assert "not a dependency fetch problem" in by_symbol["orderStat"][
        "recommended_next_action"
    ]
    repair_tasks = [
        json.loads(line)
        for line in Path(
            manifest["lean_environment_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert repair_tasks[0]["runtime_queue_status"] == (
        "PENDING_LEAN_LOCAL_LIBRARY_BUILD_REPAIR"
    )
    assert repair_tasks[0]["failure_classification"] == (
        "lean_local_library_build_unresolved"
    )


def test_exact_semantic_definition_lean_repair_executor_classifies_dependency_fetch(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Quantile.lean"
    source_file.parent.mkdir(parents=True)
    (source_root / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    source_file.write_text("-- candidate source declaration\n", encoding="utf-8")
    _write_lean_repair_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('info: mathlib: cloning https://github.com/x/y.git'); "
            "print('fatal: unable to access https://github.com/x/y.git: Could not "
            "resolve host: github.com', file=sys.stderr); sys.exit(1)",
        ),
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in results}
    assert by_symbol["orderStat"]["execution_status"] == (
        "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_DEPENDENCY_ENVIRONMENT_MISSING"
    )
    assert by_symbol["orderStat"]["failure_classification"] == (
        "lean_dependency_fetch_failed"
    )
    assert "dependencies/cache" in by_symbol["orderStat"]["recommended_next_action"]
    assert manifest["n_lean_environment_repair_tasks"] == 1
    repair_tasks = [
        json.loads(line)
        for line in Path(
            manifest["lean_environment_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert repair_tasks[0]["runtime_queue_status"] == (
        "PENDING_LEAN_DEPENDENCY_ENVIRONMENT_REPAIR"
    )
    assert repair_tasks[0]["failure_classification"] == "lean_dependency_fetch_failed"


def test_exact_semantic_definition_lean_repair_executor_routes_timeout_to_environment_repair(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Quantile.lean"
    source_file.parent.mkdir(parents=True)
    (source_root / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    source_file.write_text("-- candidate source declaration\n", encoding="utf-8")
    _write_lean_repair_tasks(tasks_path)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_timeout=1,
        lean_command=(
            sys.executable,
            "-c",
            "import time; time.sleep(5)",
        ),
    )

    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in results}
    assert by_symbol["orderStat"]["execution_status"] == (
        "IMPORT_CANDIDATE_SOURCE_FILE_LEAN_ENVIRONMENT_TIMEOUT"
    )
    assert by_symbol["orderStat"]["failure_classification"] == "local_lean_timeout"
    assert "preflight" in by_symbol["orderStat"]["recommended_next_action"]
    assert manifest["n_lean_environment_repair_tasks"] == 1
    repair_tasks = [
        json.loads(line)
        for line in Path(
            manifest["lean_environment_repair_tasks_jsonl"]
        ).read_text().splitlines()
    ]
    assert repair_tasks[0]["runtime_queue_status"] == (
        "PENDING_LEAN_DEPENDENCY_ENVIRONMENT_REPAIR"
    )
    assert repair_tasks[0]["failure_classification"] == "local_lean_timeout"


def test_exact_semantic_definition_lean_repair_executor_infers_lake_project(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    source_root = tmp_path / "src"
    source_file = source_root / "StatInference" / "Conformal" / "Quantile.lean"
    source_file.parent.mkdir(parents=True)
    (source_root / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    source_file.write_text("-- candidate source declaration\n", encoding="utf-8")
    _write_lean_repair_tasks(tasks_path)
    calls: list[dict[str, object]] = []

    def fake_lean_command(lean_project: Path | None) -> tuple[str, ...]:
        return ("fake-lake-env-lean",) if lean_project is not None else ("lean",)

    def fake_run_local_lean(
        lean_file: Path,
        *,
        lean_command: tuple[str, ...],
        lean_project: Path | None,
        timeout_s: int,
    ) -> tuple[bool, int, tuple[str, ...]]:
        calls.append(
            {
                "lean_file": str(lean_file),
                "lean_command": lean_command,
                "lean_project": str(lean_project or ""),
                "timeout_s": timeout_s,
            }
        )
        return True, 0, ()

    monkeypatch.setattr(executor_module, "_lean_command", fake_lean_command)
    monkeypatch.setattr(executor_module, "_run_local_lean", fake_run_local_lean)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        source_roots=(source_root,),
        local_lean=True,
        lean_timeout=13,
    )

    assert calls == [
        {
            "lean_file": str(source_file),
            "lean_command": ("fake-lake-env-lean",),
            "lean_project": str(source_root),
            "timeout_s": 13,
        }
    ]
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    by_symbol = {row["placeholder_symbol"]: row for row in results}
    assert by_symbol["orderStat"]["lean_project_inferred"] is True
    assert by_symbol["orderStat"]["lean_project"] == str(source_root)
    assert by_symbol["orderStat"]["local_lean_compiled"] is True


def test_definition_candidate_uses_task_lake_project_hint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    lake_project = tmp_path / "lake_project"
    lake_project.mkdir()
    definition_only_candidate = tmp_path / "candidate_defs_only.lean"
    definition_only_candidate.write_text(
        "import Mathlib.Data.Real.Basic\n\n"
        "def reviewedExchangeable : Prop := True\n",
        encoding="utf-8",
    )
    task = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanRepairTask",
        "lean_repair_task_id": "lean-repair:Exchangeable:project-hint",
        "source_repair_packet_id": "repair:Exchangeable",
        "source_review_packet_id": "review:Exchangeable",
        "source_definition_closure_work_order_id": "closure:Exchangeable",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "placeholder_symbol": "Exchangeable",
        "lean_repair_action": "author_exact_definition",
        "repair_strategy": "author_reviewed_definition_from_contract",
        "definition_only_candidate_artifact_path": str(definition_only_candidate),
        "candidate_lean_project_hint": str(lake_project),
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    tasks_path.write_text(json.dumps(task, sort_keys=True) + "\n", encoding="utf-8")
    calls: list[dict[str, object]] = []

    def fake_lean_command(lean_project: Path | None) -> tuple[str, ...]:
        return ("fake-lake-env-lean",) if lean_project is not None else ("lean",)

    def fake_run_local_lean(
        lean_file: Path,
        *,
        lean_command: tuple[str, ...],
        lean_project: Path | None,
        timeout_s: int,
    ) -> tuple[bool, int, tuple[str, ...]]:
        calls.append(
            {
                "lean_file": str(lean_file),
                "lean_command": lean_command,
                "lean_project": str(lean_project or ""),
                "timeout_s": timeout_s,
            }
        )
        return True, 0, ()

    monkeypatch.setattr(executor_module, "_lean_command", fake_lean_command)
    monkeypatch.setattr(executor_module, "_run_local_lean", fake_run_local_lean)

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        tasks_jsonl=tasks_path,
        local_lean=True,
        lean_timeout=17,
    )

    assert calls == [
        {
            "lean_file": str(definition_only_candidate),
            "lean_command": ("fake-lake-env-lean",),
            "lean_project": str(lake_project),
            "timeout_s": 17,
        }
    ]
    results = [
        json.loads(line)
        for line in Path(manifest["execution_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_REVIEW_REQUIRED"
    )
    assert results[0]["lean_project_inferred"] is True
    assert results[0]["candidate_lean_project_hint"] == str(lake_project)
    assert results[0]["lean_project"] == str(lake_project)
    assert results[0]["source_theorem_kernel_verified"] is False


def test_exact_semantic_definition_lean_repair_executor_resolves_bridge_manifest(
    tmp_path: Path,
) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    bridge_manifest = tmp_path / "bridge_manifest.json"
    _write_lean_repair_tasks(tasks_path)
    bridge_manifest.write_text(
        json.dumps({"lean_repair_tasks_jsonl": str(tasks_path)}),
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_lean_repair_executor(
        out_dir=tmp_path / "executor",
        bridge_manifest=bridge_manifest,
    )

    assert manifest["source_lean_repair_tasks_jsonl"] == str(tasks_path)
    assert manifest["n_results"] == 2
    assert manifest["n_local_lean_checked"] == 0


def test_exact_semantic_definition_lean_repair_executor_cli(tmp_path: Path) -> None:
    tasks_path = tmp_path / "lean_repair_tasks.jsonl"
    out_dir = tmp_path / "executor"
    _write_lean_repair_tasks(tasks_path)

    rc = main(
        [
            "source-theorem-exact-semantic-definition-lean-repair-executor",
            "--tasks-jsonl",
            str(tasks_path),
            "--out",
            str(out_dir),
        ]
    )

    assert rc == 0
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_lean_repair_executor_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["n_results"] == 2
    assert Path(manifest["execution_results_jsonl"]).exists()
    assert Path(manifest["runtime_learning_rows_jsonl"]).exists()
