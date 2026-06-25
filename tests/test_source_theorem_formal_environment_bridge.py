from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.exact_source_theorem_proof_body_executor import (
    export_exact_source_theorem_proof_body_execution_results,
)
from ai_statistician.formal_verifier_agentic_proof_execution_materializer import (
    _normalize_lean_statement_syntax,
)
from ai_statistician.source_theorem_formal_environment_proofengineer_bridge import (
    export_exact_source_theorem_proof_body_repair_execution_queue,
    _proof_body_repair_attempts,
    resolve_source_theorem_formal_environment_queue_path,
    run_source_theorem_formal_environment_proofengineer_bridge,
)


def test_formal_environment_bridge_resolves_queue_from_promotion_bridge_manifest(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runs" / "live_runtime"
    bridge_dir = runtime_dir / "runtime_source_theorem_promotion_proofengineer_bridge"
    queue_dir = bridge_dir / "formal_verifier_agentic_proof_source_theorem_formal_environment_work_orders"
    queue_dir.mkdir(parents=True)
    queue_jsonl = (
        queue_dir
        / "formal_verifier_agentic_proof_source_theorem_formal_environment_work_orders.jsonl"
    )
    queue_jsonl.write_text("", encoding="utf-8")
    bridge_manifest = (
        bridge_dir / "runtime_source_theorem_promotion_proofengineer_bridge_manifest.json"
    )
    bridge_manifest.write_text(
        json.dumps(
            {
                "source_theorem_formal_environment_work_orders_jsonl": str(
                    queue_jsonl.relative_to(tmp_path)
                )
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "research_agent_runtime_manifest.json").write_text(
        json.dumps(
            {
                "artifacts": {
                    "runtime_source_theorem_promotion_proofengineer_bridge_manifest": str(
                        bridge_manifest.relative_to(tmp_path)
                    )
                }
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_source_theorem_formal_environment_queue_path(
        runtime_dir=runtime_dir
    )

    assert resolved == queue_jsonl


def test_proof_body_repair_attempts_use_actual_closure_declaration() -> None:
    attempts = _proof_body_repair_attempts(
        row={
            "kernel_verified_theorem_reduction_closure_declarations": [
                "splitConformalFiniteSampleCoverage_reductionClosure"
            ],
        },
        primary_diagnostic={},
    )

    assert attempts[:2] == [
        "simpa using splitConformalFiniteSampleCoverage_reductionClosure",
        "exact splitConformalFiniteSampleCoverage_reductionClosure",
    ]
    assert all(
        "split_conformal_finite_sample_coverage_reduction_closure" not in attempt
        for attempt in attempts
    )


def test_proof_body_repair_work_order_exports_direct_execution_queue(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "split_conformal_coverage_candidate.lean"
    candidate.write_text(
        "theorem split_conformal_coverage : True := by\n"
        "  -- AI_STAT_EVOLVE_BLOCK_START\n"
        "  trivial\n",
        encoding="utf-8",
    )
    work_orders_jsonl = tmp_path / "runtime_source_theorem_promotion_work_orders.jsonl"
    work_orders_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremPromotionWorkOrder",
                "work_order_id": "source_theorem_promotion_work_order:proof_body",
                "proof_mode": "source_theorem_exact_proof_body_repair",
                "action_type": "repair_exact_source_theorem_candidate_proof_body",
                "source_formal_target_id": "target:split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "conformal_prediction_coverage",
                    "target_lean_declaration": "split_conformal_coverage",
                    "source_theorem_target_known": True,
                },
                "proof_body_candidate_artifact_path": str(candidate),
                "proof_body_goal_excerpt": ["claim : Prop", "⊢ claim"],
                "proof_body_attempt_summaries": [
                    "1:simp:returncode=1:compiled=False"
                ],
                "proof_body_failure_classification": "proof_body_incomplete",
                "proof_body_gate_status": "PROOF_BODY_REACHED_PROOF_INCOMPLETE",
                "source_theorem_exact_proof_body_reached": True,
                "kernel_verified_theorem_reduction_closure_declarations": [
                    "splitConformalFiniteSampleCoverage_reductionClosure"
                ],
                "verified_theorem_reduction_closure_artifact_paths": [
                    "runs/theorem_reduction_closure/closure.lean"
                ],
                "kernel_verified_theorem_reduction_closure_target_ids": [
                    "split_conformal_finite_sample_coverage_reduction_closure"
                ],
                "source_theorem_proof_body_adapter_feedback_available": True,
                "source_theorem_proof_body_adapter_kernel_verified": True,
                "kernel_verified_source_theorem_proof_body_adapter_ids": [
                    "source_theorem_proof_body_adapter_check:verified"
                ],
                "verified_source_theorem_proof_body_adapter_artifact_paths": [
                    "runs/adapter_candidates/split_conformal_coverage_adapter.lean"
                ],
                "verified_source_theorem_proof_body_adapter_declarations": [
                    "split_conformal_coverage_source_to_bridge_adapter"
                ],
                "kernel_verified_source_to_bridge_premise_derivation_ids": [
                    "source_to_bridge_premise_derivation_check:hGoodCovered"
                ],
                "verified_source_to_bridge_premise_derivation_artifact_paths": [
                    "runs/premise_derivations/hGoodCovered.lean"
                ],
                "verified_source_to_bridge_premise_derivation_declarations": [
                    "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
                ],
                "source_theorem_proof_body_adapter_context_boundary": (
                    "adapter guides proof-body retry but is not source theorem proof"
                ),
                "source_theorem_exact_proof_body_repair_diagnostics": [
                    {
                        "target_theorem_name": "split_conformal_coverage",
                        "candidate_artifact_path": str(candidate),
                        "proof_body_gate_status": (
                            "PROOF_BODY_REACHED_PROOF_INCOMPLETE"
                        ),
                        "proof_body_goal_reached": True,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    queue_result = export_exact_source_theorem_proof_body_repair_execution_queue(
        proof_body_repair_work_orders_jsonl=work_orders_jsonl,
        out_dir=tmp_path / "direct_execution_queue",
    )

    assert queue_result["queue_source_mode"] == (
        "source_theorem_exact_proof_body_repair"
    )
    assert queue_result["n_execution_queue_rows"] == 1
    assert queue_result["n_ready"] == 1
    execution_row = queue_result["rows"][0]
    assert execution_row["execution_status"] == (
        "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
    )
    assert execution_row["target_theorem_name"] == "split_conformal_coverage"
    assert execution_row["target_lean_declaration"] == "split_conformal_coverage"
    assert execution_row["source_theorem_target_known"] is True
    assert execution_row["signature_probe_artifact_path"] == str(candidate)
    assert execution_row["already_repaired_environment"][
        "signature_typecheck_reached_proof_body"
    ] is True
    assert execution_row["proof_body_goal_excerpt"] == ["claim : Prop", "⊢ claim"]
    assert execution_row["source_theorem_proof_body_adapter_kernel_verified"] is True
    assert execution_row["kernel_verified_source_theorem_proof_body_adapter_ids"] == [
        "source_theorem_proof_body_adapter_check:verified"
    ]
    assert execution_row["verified_source_theorem_proof_body_adapter_artifact_paths"] == [
        "runs/adapter_candidates/split_conformal_coverage_adapter.lean"
    ]
    assert execution_row["verified_source_theorem_proof_body_adapter_declarations"] == [
        "split_conformal_coverage_source_to_bridge_adapter"
    ]
    assert execution_row["kernel_verified_source_to_bridge_premise_derivation_ids"] == [
        "source_to_bridge_premise_derivation_check:hGoodCovered"
    ]
    assert execution_row["verified_source_to_bridge_premise_derivation_artifact_paths"] == [
        "runs/premise_derivations/hGoodCovered.lean"
    ]
    assert execution_row["verified_source_to_bridge_premise_derivation_declarations"] == [
        "split_conformal_coverage_hGoodCovered_source_to_bridge_derivation"
    ]
    assert execution_row["kernel_verified_theorem_reduction_closure_declarations"] == [
        "splitConformalFiniteSampleCoverage_reductionClosure"
    ]
    assert execution_row["verified_theorem_reduction_closure_artifact_paths"] == [
        "runs/theorem_reduction_closure/closure.lean"
    ]
    assert execution_row["kernel_verified_theorem_reduction_closure_target_ids"] == [
        "split_conformal_finite_sample_coverage_reduction_closure"
    ]
    assert execution_row["proof_body_attempts"][:2] == [
        "simpa using splitConformalFiniteSampleCoverage_reductionClosure",
        "exact splitConformalFiniteSampleCoverage_reductionClosure",
    ]
    assert (
        execution_row["live_proof_state_request"][
        "source_theorem_proof_body_adapter_kernel_verified"
        ]
        is True
    )
    assert execution_row["live_proof_state_request"][
        "kernel_verified_source_to_bridge_premise_derivation_ids"
    ] == ["source_to_bridge_premise_derivation_check:hGoodCovered"]
    assert "lean_multi_attempt" in execution_row["required_dynamic_checks"]

    executor_manifest = export_exact_source_theorem_proof_body_execution_results(
        Path(str(queue_result["proof_body_execution_queue_manifest"])).parent,
        tmp_path / "direct_executor",
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('error: unsolved goals'); sys.exit(1)",
        ),
    )
    assert executor_manifest["n_execution_result_rows"] == 1
    assert executor_manifest["n_source_theorem_proof_body_adapter_context_rows"] == 1
    assert (
        executor_manifest[
            "n_source_theorem_proof_body_adapter_kernel_verified_context_rows"
        ]
        == 1
    )
    assert executor_manifest["n_proof_body_goal_reached"] == 1
    assert executor_manifest["n_source_theorem_kernel_verified"] == 0
    assert executor_manifest["by_proof_body_gate_status"] == {
        "PROOF_BODY_REACHED_PROOF_INCOMPLETE": 1
    }
    executor_row = executor_manifest["rows"][0]
    assert executor_row["source_theorem_proof_body_adapter_kernel_verified"] is True
    assert list(executor_row["kernel_verified_theorem_reduction_closure_declarations"]) == [
        "splitConformalFiniteSampleCoverage_reductionClosure"
    ]
    assert list(executor_row["verified_theorem_reduction_closure_artifact_paths"]) == [
        "runs/theorem_reduction_closure/closure.lean"
    ]
    assert executor_row["source_theorem_kernel_verified"] is False
    assert executor_row["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
    )
    learning_export = executor_manifest["runtime_learning_export"]
    assert learning_export["n_source_theorem_proof_body_adapter_context_rows"] == 1
    learning_rows_path = Path(str(learning_export["runtime_learning_rows_jsonl"]))
    learning_rows = [
        json.loads(line)
        for line in learning_rows_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert learning_rows[0]["source_theorem_proof_body_adapter_kernel_verified"] is True
    assert learning_rows[0][
        "kernel_verified_theorem_reduction_closure_declarations"
    ] == ["splitConformalFiniteSampleCoverage_reductionClosure"]
    assert learning_rows[0]["kernel_verified_source_theorem_proof_body_adapter_ids"] == [
        "source_theorem_proof_body_adapter_check:verified"
    ]
    assert learning_rows[0][
        "kernel_verified_source_to_bridge_premise_derivation_ids"
    ] == ["source_to_bridge_premise_derivation_check:hGoodCovered"]
    assert learning_rows[0]["source_theorem_kernel_verified"] is False

    cli_out = tmp_path / "cli_direct_executor"
    exit_code = main(
        [
            "exact-source-theorem-proof-body-executor",
            "--proof-body-repair-work-orders-jsonl",
            str(work_orders_jsonl),
            "--out",
            str(cli_out),
            "--overwrite",
        ]
    )
    assert exit_code == 0
    assert (
        cli_out
        / "exact_source_theorem_proof_body_repair_execution_queue"
        / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    ).exists()
    cli_manifest = json.loads(
        (
            cli_out
            / "exact_source_theorem_proof_body_execution_result_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert cli_manifest["n_execution_result_rows"] == 1
    assert cli_manifest["n_source_theorem_kernel_verified"] == 0
    assert cli_manifest["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTOR_NOT_PROOF_EVIDENCE"
    )


def test_materializer_normalizes_order_stat_nat_placeholder_application() -> None:
    statement = (
        "theorem split_conformal_coverage\n"
        "    {Ω : Type*} [MeasurableSpace Ω]\n"
        "    (s : Fin (n2 + 1) → Ω → ℝ)\n"
        "    (q_hat : Ω → ℝ)\n"
        "    (hq : q_hat = fun ω => "
        "orderStat s ⟨Nat.ceil ((↑(n2 + 1)) * (1 - alpha)) - 1, by omega⟩ ω) :\n"
        "    True := by\n"
        "  trivial"
    )

    normalized = _normalize_lean_statement_syntax(statement)

    assert "Type*" not in normalized
    assert "orderStat s ⟨" not in normalized
    assert (
        "orderStat s (Nat.ceil ((↑(n2 + 1)) * (1 - alpha)) - 1) ω"
        in normalized
    )


def test_source_theorem_formal_environment_bridge_exports_repair_packets(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "split_conformal_coverage.lean"
    candidate_artifact.write_text(
        "import Mathlib.Probability.ProbabilityMeasure\n"
        "import Mathlib.Order.LocallyFiniteOrder\n\n"
        "theorem split_conformal_coverage {Ω : Type _} [MeasurableSpace Ω] "
        "(P : MeasureTheory.Measure Ω) [MeasureTheory.IsProbabilityMeasure P] "
        "(m : ℕ) (hm : 0 < m) (alpha : ℝ) "
        "(halpha : 0 < alpha ∧ alpha < 1) "
        "(s : Fin (m + 1) → Ω → ℝ) (hexch : Exchangeable P s) "
        "(k : ℕ) (hk : k = Nat.ceil ((m + 1 : ℝ) * (1 - alpha))) "
        "(q_hat : Ω → ℝ) (hq : ∀ ω, q_hat ω = orderStat s k ω) : "
        "P {ω | s (Fin.last m) ω ≤ q_hat ω} ≥ 1 - alpha := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:env",
                "question_id": "split_conformal",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "source_theorem_route_id": "route:split_conformal_source",
                "source_theorem_goal_id": "split_conformal_finite_sample_coverage",
                "source_theorem_statement": (
                    "split conformal finite-sample marginal coverage under exchangeability"
                ),
                "source_theorem_skeleton": (
                    "exchangeability -> uniform rank -> conformal coverage"
                ),
                "source_theorem_lean_file": "StatInference/Conformal/SplitCoverage.lean",
                "semantic_alignment_constraints": [
                    "preserve marginal coverage target",
                    "do not strengthen exchangeability assumptions",
                ],
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": [
                    "failed to synthesize instance of type class",
                    "  HSub ℕ ℝ ENNReal",
                    "Function expected at",
                    "  Exchangeable",
                    "Hint: The identifier `Exchangeable` is unknown.",
                    "Function expected at",
                    "  orderStat",
                    "Hint: The identifier `orderStat` is unknown.",
                ],
                "missing_formal_symbols": ["Exchangeable", "orderStat"],
                "typeclass_blockers": ["HSub ℕ ℝ ENNReal"],
                "recommended_repair_tasks": [
                    "resolve Lean declaration/import or explicitly formalize source-theorem primitive `Exchangeable`",
                    "resolve Lean declaration/import or explicitly formalize source-theorem primitive `orderStat`",
                    "repair exact source-theorem statement so Lean can synthesize typeclass instance `HSub ℕ ℝ ENNReal` without coercion ambiguity",
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue_jsonl,
        question_id="split_conformal",
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    assert manifest["n_work_orders"] == 1
    assert manifest["n_repair_packets"] == 1
    assert manifest["n_missing_formal_symbols"] == 2
    assert manifest["n_typeclass_blockers"] == 1
    assert manifest["signature_probes_requested"] is True
    assert manifest["n_signature_probe_rows"] == 1
    assert manifest["n_signature_probes_reached_proof_body"] == 1
    assert manifest["signature_probe_proof_evidence_status"] == (
        "SIGNATURE_PROBE_NOT_PROOF_EVIDENCE"
    )
    assert manifest["n_proof_body_work_orders"] == 1
    assert manifest["proof_body_work_order_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert manifest["n_proof_body_execution_queue_rows"] == 1
    assert manifest["n_proof_body_execution_live_goal_requests"] == 1
    assert manifest["proof_body_execution_queue_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert manifest["proof_evidence_status"] == (
        "FORMAL_ENVIRONMENT_REPAIR_PACKETS_NOT_PROOF_EVIDENCE"
    )
    repair_packets_path = Path(str(manifest["repair_packets_jsonl"]))
    repair_packet = json.loads(repair_packets_path.read_text(encoding="utf-8"))
    assert repair_packet["artifact_kind"] == "SourceTheoremFormalEnvironmentRepairPacket"
    assert repair_packet["question_id"] == "split_conformal"
    assert repair_packet["missing_formal_symbols"] == ["Exchangeable", "orderStat"]
    assert repair_packet["typeclass_blockers"] == ["HSub ℕ ℝ ENNReal"]
    assert repair_packet["source_theorem_target_known"] is True
    assert repair_packet["target_lean_declaration"] == "split_conformal_coverage"
    assert repair_packet["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert repair_packet["source_theorem_target_provenance"][
        "source_theorem_statement"
    ] == "split conformal finite-sample marginal coverage under exchangeability"
    assert repair_packet["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert repair_packet["repair_status"] == "FORMAL_ENVIRONMENT_REPAIR_REQUIRED"
    assert any("search Mathlib/StatInference" in row for row in repair_packet["proofengineer_action_plan"])
    declaration_hints = repair_packet["formal_environment_declaration_hints"]
    assert {hint["symbol"] for hint in declaration_hints} == {"Exchangeable", "orderStat"}
    assert any(
        "semantic primitive" in hint["signature_probe_fallback"]
        for hint in declaration_hints
    )
    statement_hints = repair_packet["statement_repair_hints"]
    assert statement_hints[0]["blocker"] == "HSub ℕ ℝ ENNReal"
    assert "ENNReal.ofReal (1 - alpha)" in statement_hints[0]["repair_hint"]
    signature_probe_plan = repair_packet["lean_signature_probe_plan"]
    assert signature_probe_plan["probe_kind"] == "statement_typecheck_not_proof"
    assert signature_probe_plan["proof_evidence_status"] == (
        "SIGNATURE_PROBE_PLAN_NOT_PROOF_EVIDENCE"
    )
    assert repair_packet["proof_evidence_status"] == "REPAIR_PACKET_NOT_PROOF_EVIDENCE"
    probe_manifest = json.loads(
        Path(str(manifest["signature_probe_manifest"])).read_text(encoding="utf-8")
    )
    probe_row = probe_manifest["rows"][0]
    assert probe_row["signature_typecheck_reached_proof_body"] is True
    assert probe_row["signature_probe_status"] == (
        "SIGNATURE_PROBE_REACHED_PROOF_BODY_NOT_PROOF"
    )
    probe_source = Path(probe_row["signature_probe_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "def Exchangeable" in probe_source
    assert "def orderStat" in probe_source
    assert "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n" in probe_source
    assert "import Mathlib.Data.Real.Basic\n" in probe_source
    assert "import Mathlib.Data.Fin.Basic\n" in probe_source
    assert "import Mathlib.Data.ENNReal.Basic\n" in probe_source
    assert "import Mathlib\n" not in probe_source
    assert "import Mathlib.Probability.ProbabilityMeasure" not in probe_source
    assert "import Mathlib.Order.LocallyFiniteOrder" not in probe_source
    assert "ENNReal.ofReal (1 - alpha)" in probe_source
    assert probe_manifest["proof_evidence_status"] == "SIGNATURE_PROBE_NOT_PROOF_EVIDENCE"
    proof_body_rows_path = Path(str(manifest["proof_body_work_orders_jsonl"]))
    proof_body_work_order = json.loads(proof_body_rows_path.read_text(encoding="utf-8"))
    assert proof_body_work_order["artifact_kind"] == "ExactSourceTheoremProofBodyWorkOrder"
    assert proof_body_work_order["question_id"] == "split_conformal"
    assert proof_body_work_order["target_theorem_name"] == "split_conformal_coverage"
    assert proof_body_work_order["target_lean_declaration"] == "split_conformal_coverage"
    assert proof_body_work_order["source_theorem_target_known"] is True
    assert proof_body_work_order["source_theorem_target_provenance"][
        "source_theorem_goal_id"
    ] == "split_conformal_finite_sample_coverage"
    assert proof_body_work_order["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert proof_body_work_order["proof_body_failure_classification"] == (
        "proof_body_incomplete"
    )
    assert proof_body_work_order["proof_body_goal_excerpt"] == ["unsolved goals"]
    assert proof_body_work_order["proof_body_attempts"] == []
    assert proof_body_work_order["proof_body_attempt_source"] == (
        "formal_environment_open_skip_tactic_attempts"
    )
    assert "not proof evidence" in proof_body_work_order[
        "proof_body_attempt_boundary"
    ].lower()
    assert "semantic primitives" in proof_body_work_order[
        "proof_body_attempt_boundary"
    ].lower()
    assert proof_body_work_order["already_repaired_environment"][
        "signature_typecheck_reached_proof_body"
    ] is True
    assert any(
        "do not change the theorem statement" in row
        for row in proof_body_work_order["forbidden_actions"]
    )
    assert proof_body_work_order["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    execution_queue_manifest = json.loads(
        Path(str(manifest["proof_body_execution_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    execution_row = execution_queue_manifest["rows"][0]
    assert execution_row["artifact_kind"] == "ExactSourceTheoremProofBodyExecutionQueueRow"
    assert execution_row["question_id"] == "split_conformal"
    assert execution_row["execution_status"] == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
    assert execution_row["owner_agent"] == "FormalizerProofEngineer"
    assert execution_row["target_theorem_name"] == "split_conformal_coverage"
    assert execution_row["expected_target_lean_declaration"] == (
        "split_conformal_coverage"
    )
    assert execution_row["source_theorem_target_known"] is True
    assert execution_row["source_theorem_target_identity_status"] == (
        "SOURCE_THEOREM_TARGET_KNOWN"
    )
    assert execution_row["source_theorem_target_provenance"][
        "source_theorem_lean_file"
    ] == "StatInference/Conformal/SplitCoverage.lean"
    assert execution_row["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert execution_row["live_goal_location_ready"] is True
    assert execution_row["target_lean_declaration"] == "split_conformal_coverage"
    assert execution_row["proof_body_goal_excerpt"] == ["unsolved goals"]
    assert execution_row["proof_body_attempts"] == []
    assert execution_row["proof_body_attempt_source"] == (
        "formal_environment_open_skip_tactic_attempts"
    )
    assert "local lean/axle" in execution_row["proof_body_attempt_boundary"].lower()
    assert execution_row["already_repaired_environment"]["missing_formal_symbols"] == [
        "Exchangeable",
        "orderStat",
    ]
    assert execution_row["target_identity_status"] == "TARGET_DECLARATION_MATCHED"
    assert execution_row["live_proof_state_request"]["provider_preferences"][0] == (
        "lean_lsp_mcp"
    )
    assert execution_row["live_proof_state_request"][
        "expected_target_lean_declaration"
    ] == "split_conformal_coverage"
    assert execution_row["live_proof_state_request"]["question_id"] == (
        "split_conformal"
    )
    assert execution_row["live_proof_state_request"][
        "source_theorem_target_provenance"
    ]["source_theorem_route_id"] == "route:split_conformal_source"
    assert execution_row["live_proof_state_request"][
        "source_theorem_target_identity_status"
    ] == "SOURCE_THEOREM_TARGET_KNOWN"
    assert {
        call["tool"] for call in execution_row["live_proof_state_request"]["mcp_tool_calls"]
    } >= {"lean_goal", "lean_diagnostic_messages", "lean_local_search"}
    assert "lean_multi_attempt" not in {
        call["tool"] for call in execution_row["live_proof_state_request"]["mcp_tool_calls"]
    }
    assert execution_row["live_proof_state_request"]["proof_body_attempts"] == []
    assert "copy signature_probe_artifact_path" in " ".join(execution_row["command_plan"])
    assert "no sorry/admit/axiom/unsafe tokens" in execution_row["required_static_checks"]
    assert execution_row["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
    )

    learning_rows_path = Path(str(manifest["runtime_learning_rows_jsonl"]))
    learning_row = json.loads(learning_rows_path.read_text(encoding="utf-8"))
    assert learning_row["learning_task"] == (
        "source_theorem_formal_environment_repair_feedback"
    )
    assert learning_row["question_id"] == "split_conformal"
    assert learning_row["input_summary"]["trigger"] == (
        "SOURCE_THEOREM_FORMAL_ENVIRONMENT_REPAIR_REQUIRED"
    )
    assert learning_row["input_summary"]["missing_formal_symbols"] == [
        "Exchangeable",
        "orderStat",
    ]
    assert learning_row["input_summary"]["lean_signature_probe_plan"]["probe_kind"] == (
        "statement_typecheck_not_proof"
    )
    assert learning_row["input_summary"]["signature_probe_rows"][0][
        "signature_typecheck_reached_proof_body"
    ] is True
    assert learning_row["input_summary"]["proof_body_work_orders"][0][
        "target_theorem_name"
    ] == "split_conformal_coverage"
    assert learning_row["input_summary"]["proof_body_execution_queue_rows"][0][
        "execution_status"
    ] == "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER"
    assert learning_row["input_summary"]["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert learning_row["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    export_manifest = json.loads(
        Path(str(manifest["runtime_learning_export_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    assert export_manifest["n_proof_body_work_orders"] == 1
    assert export_manifest["proof_body_work_order_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_WORK_ORDER_NOT_PROOF_EVIDENCE"
    )
    assert export_manifest["n_proof_body_execution_queue_rows"] == 1
    assert export_manifest["proof_body_execution_queue_proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
    )
    assert "statement_repair_hints" in learning_row["input_summary"]
    assert learning_row["proof_evidence_status"] == (
        "FORMAL_ENVIRONMENT_REPAIR_LEARNING_NOT_PROOF_EVIDENCE"
    )

    execution_payload = export_exact_source_theorem_proof_body_execution_results(
        Path(str(manifest["proof_body_execution_queue_manifest"])).parent,
        tmp_path / "proof_body_executor",
        overwrite=True,
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )
    assert execution_payload["n_execution_result_rows"] == 1
    assert execution_payload["n_materialized_candidate_artifacts"] == 1
    assert execution_payload["n_local_lean_checked"] == 1
    assert execution_payload["n_local_lean_compiled"] == 0
    assert execution_payload["n_proof_body_attempted"] == 0
    assert execution_payload["n_proof_body_attempt_success"] == 0
    assert execution_payload["n_artifact_kernel_verified"] == 0
    assert execution_payload["n_source_theorem_kernel_verified"] == 0
    assert execution_payload["n_placeholder_environment_blockers"] == 1
    assert execution_payload["n_source_theorem_target_known"] == 1
    assert execution_payload["n_semantic_alignment_constraint_rows"] == 1
    assert execution_payload["source_theorem_route_ids"] == [
        "route:split_conformal_source"
    ]
    execution_result = execution_payload["rows"][0]
    assert execution_result["execution_status"] == (
        "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    )
    assert execution_result["question_id"] == "split_conformal"
    assert execution_result["failure_classification"] == (
        "formal_environment_placeholder_primitives"
    )
    assert execution_result["proof_body_attempted"] is False
    assert execution_result["proof_body_attempt_count"] == 0
    assert list(execution_result["proof_body_attempt_summaries"]) == []
    assert execution_result["source_theorem_kernel_verified"] is False
    assert execution_result["source_theorem_target_known"] is True
    assert execution_result["expected_target_lean_declaration"] == (
        "split_conformal_coverage"
    )
    assert execution_result["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert list(execution_result["semantic_alignment_constraints"]) == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert execution_result["target_identity_status"] == "TARGET_DECLARATION_MATCHED"
    assert execution_result["candidate_live_proof_state_request"][
        "target_lean_file"
    ] == execution_result["candidate_artifact_path"]
    assert execution_result["candidate_live_proof_state_request"]["mcp_tool_calls"][0][
        "arguments"
    ]["file"] == execution_result["candidate_artifact_path"]
    candidate_source = Path(execution_result["candidate_artifact_path"]).read_text(
        encoding="utf-8"
    )
    assert "def Exchangeable" in candidate_source
    transcript_event = json.loads(
        Path(execution_result["execution_transcript_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert transcript_event["event"] == (
        "exact_source_theorem_proof_body_execution_result"
    )
    assert transcript_event["source_theorem_kernel_verified"] is False
    assert transcript_event["source_theorem_target_provenance"][
        "source_theorem_goal_id"
    ] == "split_conformal_finite_sample_coverage"
    assert transcript_event["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    learning_export = execution_payload["runtime_learning_export"]
    assert learning_export["n_source_theorem_target_known"] == 1
    assert learning_export["n_semantic_alignment_constraint_rows"] == 1
    assert learning_export["source_theorem_route_ids"] == [
        "route:split_conformal_source"
    ]
    executor_learning_row = json.loads(
        Path(str(learning_export["runtime_learning_rows_jsonl"])).read_text(
            encoding="utf-8"
        )
    )
    assert executor_learning_row["learning_task"] == (
        "exact_source_theorem_proof_body_execution_feedback"
    )
    assert executor_learning_row["question_id"] == "split_conformal"
    assert executor_learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_LOCAL_LEAN_FAILED"
    )
    assert executor_learning_row["source_theorem_target_provenance"][
        "source_theorem_route_id"
    ] == "route:split_conformal_source"
    assert executor_learning_row["semantic_alignment_constraints"] == [
        "preserve marginal coverage target",
        "do not strengthen exchangeability assumptions",
    ]
    assert executor_learning_row["kernel_verified_source_theorem_ids"] == []

    cli_out = tmp_path / "bridge_cli"
    code = main(
        [
            "source-theorem-formal-environment-proofengineer-bridge",
            "--queue-jsonl",
            str(queue_jsonl),
            "--question-id",
            "split_conformal",
            "--out",
            str(cli_out),
        ]
    )
    assert code == 0
    cli_manifest = json.loads(
        (
            cli_out
            / "source_theorem_formal_environment_proofengineer_bridge_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert cli_manifest["n_repair_packets"] == 1
    assert cli_manifest["runtime_learning_ready"] is True


def test_exact_source_theorem_proof_body_executor_attempts_bounded_tactics(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "proof_body_queue"
    queue_dir.mkdir()
    signature_probe_artifact = tmp_path / "signature_probe.lean"
    candidate_artifact = tmp_path / "candidate.lean"
    transcript_path = tmp_path / "candidate.jsonl"
    signature_probe_artifact.write_text(
        "theorem exact_source_claim {claim : Prop} (h_claim : claim) : claim := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    (
        queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:bounded_tactic",
                        "source_work_order_id": "source_work_order:bounded_tactic",
                        "target_theorem_name": "exact_source_claim",
                        "target_lean_declaration": "exact_source_claim",
                        "expected_target_lean_declaration": "exact_source_claim",
                        "source_theorem_target_known": True,
                        "source_theorem_target_provenance": {
                            "source_theorem_route_id": "route:bounded_tactic"
                        },
                        "semantic_alignment_constraints": [
                            "do not change theorem statement"
                        ],
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "source_candidate_artifact_path": str(signature_probe_artifact),
                        "signature_probe_artifact_path": str(signature_probe_artifact),
                        "candidate_artifact_path": str(candidate_artifact),
                        "execution_transcript_path": str(transcript_path),
                        "live_goal_location_ready": True,
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "proof_body_executor",
        overwrite=True,
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            (
                "import pathlib, sys; "
                "text = pathlib.Path(sys.argv[-1]).read_text(); "
                "sys.exit(0 if 'assumption' in text else "
                "(print('unsolved goals') or 1))"
            ),
        ),
    )

    assert payload["n_execution_result_rows"] == 1
    assert payload["n_local_lean_checked"] == 1
    assert payload["n_proof_body_attempted"] == 1
    assert payload["n_proof_body_attempt_success"] == 1
    assert payload["n_artifact_kernel_verified"] == 1
    assert payload["n_source_theorem_kernel_verified"] == 1
    assert payload["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_SOURCE_KERNEL_VERIFIED"
    )
    row = payload["rows"][0]
    assert row["execution_status"] == "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
    assert row["proof_body_attempted"] is True
    assert row["proof_body_attempt_success"] is True
    assert row["proof_body_attempt_strategy"] == "assumption"
    assert row["source_theorem_kernel_verified"] is True
    assert "assumption" in candidate_artifact.read_text(encoding="utf-8")
    transcript_event = json.loads(transcript_path.read_text(encoding="utf-8"))
    assert transcript_event["proof_body_attempt_success"] is True
    learning_export = payload["runtime_learning_export"]
    learning_row = json.loads(
        Path(str(learning_export["runtime_learning_rows_jsonl"])).read_text(
            encoding="utf-8"
        )
    )
    assert learning_row["trigger"] == "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED"
    assert learning_row["kernel_verified_source_theorem_ids"] == [
        "exact_source_claim"
    ]


def test_exact_source_theorem_proof_body_executor_blocks_unreviewed_semantic_risk(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "proof_body_queue"
    queue_dir.mkdir()
    signature_probe_artifact = tmp_path / "signature_probe.lean"
    candidate_artifact = tmp_path / "candidate.lean"
    transcript_path = tmp_path / "candidate.jsonl"
    signature_probe_artifact.write_text(
        "theorem exact_source_claim {claim : Prop} (h_claim : claim) : claim := by\n"
        "  exact h_claim\n",
        encoding="utf-8",
    )
    (
        queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:semantic_risk",
                        "source_work_order_id": "source_work_order:semantic_risk",
                        "target_theorem_name": "exact_source_claim",
                        "target_lean_declaration": "exact_source_claim",
                        "expected_target_lean_declaration": "exact_source_claim",
                        "source_theorem_target_known": True,
                        "source_theorem_target_provenance": {
                            "source_theorem_route_id": "route:semantic_risk"
                        },
                        "semantic_alignment_constraints": [
                            "unreviewed synthesized definition semantic risk: "
                            "draft finite maximum ignores rank",
                            "semantic_definition_risk: orderStat candidate is a finite maximum",
                        ],
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "source_candidate_artifact_path": str(signature_probe_artifact),
                        "signature_probe_artifact_path": str(signature_probe_artifact),
                        "candidate_artifact_path": str(candidate_artifact),
                        "execution_transcript_path": str(transcript_path),
                        "live_goal_location_ready": True,
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "proof_body_executor",
        overwrite=True,
        local_lean=True,
        lean_command=(sys.executable, "-c", "import sys; sys.exit(0)"),
    )

    assert payload["n_artifact_kernel_verified"] == 1
    assert payload["n_source_theorem_kernel_verified"] == 0
    assert payload["n_semantic_alignment_blocker_rows"] == 1
    assert payload["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_ARTIFACT_KERNEL_VERIFIED_NOT_SOURCE_THEOREM"
    )
    row = payload["rows"][0]
    assert row["artifact_kernel_verified"] is True
    assert row["source_theorem_kernel_verified"] is False
    assert row["formal_environment_semantically_closed"] is False
    assert row["failure_classification"] == (
        "source_theorem_semantic_alignment_unreviewed"
    )
    assert list(row["semantic_alignment_blockers"]) == [
        "unreviewed synthesized definition semantic risk: "
        "draft finite maximum ignores rank",
        "semantic_definition_risk: orderStat candidate is a finite maximum",
    ]


def test_exact_source_theorem_proof_body_executor_skips_attempts_for_semantic_blockers(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "proof_body_queue"
    queue_dir.mkdir()
    signature_probe_artifact = tmp_path / "signature_probe.lean"
    candidate_artifact = tmp_path / "candidate.lean"
    transcript_path = tmp_path / "candidate.jsonl"
    signature_probe_artifact.write_text(
        "theorem exact_source_claim : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    (
        queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:semantic_open",
                        "source_work_order_id": "source_work_order:semantic_open",
                        "target_theorem_name": "exact_source_claim",
                        "target_lean_declaration": "exact_source_claim",
                        "expected_target_lean_declaration": "exact_source_claim",
                        "source_theorem_target_known": True,
                        "semantic_alignment_constraints": [
                            "unreviewed synthesized definition semantic risk: "
                            "draft finite maximum ignores rank",
                            "semantic_definition_risk: orderStat candidate is a finite maximum",
                        ],
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "source_candidate_artifact_path": str(signature_probe_artifact),
                        "signature_probe_artifact_path": str(signature_probe_artifact),
                        "candidate_artifact_path": str(candidate_artifact),
                        "execution_transcript_path": str(transcript_path),
                        "live_goal_location_ready": True,
                        "live_proof_state_request": {
                            "mcp_tool_calls": [
                                {"tool": "lean_goal", "arguments": {}},
                                {"tool": "lean_multi_attempt", "arguments": {}},
                            ],
                            "proof_body_attempts": ["assumption"],
                        },
                        "already_repaired_environment": {
                            "missing_formal_symbols": [],
                            "typeclass_blockers": [],
                            "signature_typecheck_reached_proof_body": True,
                        },
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "proof_body_executor",
        overwrite=True,
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    assert payload["n_proof_body_attempted"] == 0
    assert payload["n_semantic_alignment_blocker_rows"] == 1
    row = payload["rows"][0]
    assert row["failure_classification"] == (
        "proof_body_reached_semantic_alignment_unreviewed"
    )
    assert row["proof_body_attempted"] is False
    request = row["candidate_live_proof_state_request"]
    assert request["proof_body_attempts"] == []
    assert request["proof_body_attempt_source"] == (
        "semantic_alignment_open_skip_tactic_attempts"
    )
    assert "lean_multi_attempt" not in {
        call["tool"] for call in request["mcp_tool_calls"]
    }
    learning_row = json.loads(
        Path(
            str(payload["runtime_learning_export"]["runtime_learning_rows_jsonl"])
        ).read_text(encoding="utf-8")
    )
    assert learning_row["trigger"] == (
        "EXACT_SOURCE_PROOF_BODY_REACHED_SEMANTIC_REVIEW_REQUIRED"
    )
    assert "exact semantic-definition source review/promotion" in learning_row[
        "target_behavior"
    ]
    assert "Reviewed or Lean-verified exact semantic definitions" in learning_row[
        "acceptance_gate"
    ]
    assert learning_row["semantic_alignment_blockers"] == [
        "unreviewed synthesized definition semantic risk: "
        "draft finite maximum ignores rank",
        "semantic_definition_risk: orderStat candidate is a finite maximum",
    ]
    assert learning_row["source_theorem_kernel_evidence_eligible"] is False
    assert learning_row["proof_body_attempt_source"] == (
        "semantic_alignment_open_skip_tactic_attempts"
    )


def test_exact_source_theorem_proof_body_executor_strips_attempts_for_open_environment(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "proof_body_queue"
    queue_dir.mkdir()
    signature_probe_artifact = tmp_path / "signature_probe.lean"
    candidate_artifact = tmp_path / "candidate.lean"
    transcript_path = tmp_path / "candidate.jsonl"
    signature_probe_artifact.write_text(
        "def Exchangeable : Prop := True\n"
        "theorem exact_source_claim (h : Exchangeable) : Exchangeable := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    (
        queue_dir / "exact_source_theorem_proof_body_execution_queue_manifest.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rows": [
                    {
                        "artifact_kind": "ExactSourceTheoremProofBodyExecutionQueueRow",
                        "execution_queue_id": "exact_source_queue:open_environment",
                        "source_work_order_id": "source_work_order:open_environment",
                        "target_theorem_name": "exact_source_claim",
                        "target_lean_declaration": "exact_source_claim",
                        "expected_target_lean_declaration": "exact_source_claim",
                        "source_theorem_target_known": True,
                        "target_identity_status": "TARGET_DECLARATION_MATCHED",
                        "source_candidate_artifact_path": str(signature_probe_artifact),
                        "signature_probe_artifact_path": str(signature_probe_artifact),
                        "candidate_artifact_path": str(candidate_artifact),
                        "execution_transcript_path": str(transcript_path),
                        "live_goal_location_ready": True,
                        "execution_status": "READY_FOR_EXACT_SOURCE_PROOF_BODY_WORKER",
                        "already_repaired_environment": {
                            "missing_formal_symbols": ["Exchangeable"],
                            "typeclass_blockers": [],
                        },
                        "proof_body_attempts": ["assumption", "simp"],
                        "live_proof_state_request": {
                            "mcp_tool_calls": [
                                {
                                    "tool": "lean_goal",
                                    "arguments": {"file": str(signature_probe_artifact)},
                                },
                                {
                                    "tool": "lean_multi_attempt",
                                    "arguments": {
                                        "file": str(signature_probe_artifact),
                                        "snippets": ["assumption", "simp"],
                                    },
                                },
                            ],
                            "proof_body_attempts": ["assumption", "simp"],
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_exact_source_theorem_proof_body_execution_results(
        queue_dir,
        tmp_path / "proof_body_executor",
        overwrite=True,
        local_lean=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    assert payload["n_proof_body_attempted"] == 0
    row = payload["rows"][0]
    assert row["failure_classification"] == "formal_environment_placeholder_primitives"
    assert row["proof_body_attempted"] is False
    request = row["candidate_live_proof_state_request"]
    assert request["proof_body_attempts"] == []
    assert request["proof_body_attempt_source"] == (
        "formal_environment_open_skip_tactic_attempts"
    )
    assert "lean_multi_attempt" not in {
        call["tool"] for call in request["mcp_tool_calls"]
    }


def test_signature_probe_repairs_greek_alpha_ennreal_lower_bound(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "split_conformal_coverage_greek.lean"
    candidate_artifact.write_text(
        "import Mathlib.MeasureTheory.Measure.ProbabilityMeasure\n"
        "import Mathlib.Data.Real.Basic\n"
        "import Mathlib.Data.Fin.Basic\n\n"
        "theorem split_conformal_coverage {Ω : Type _} [MeasurableSpace Ω] "
        "(P : MeasureTheory.Measure Ω) [MeasureTheory.IsProbabilityMeasure P] "
        "(n₂ : ℕ) (hn₂ : 0 < n₂) (α : ℝ) (hα : 0 < α) (hα1 : α < 1) "
        "(s : Fin (n₂ + 1) → Ω → ℝ) (hexch : Exchangeable P s) "
        "(q_hat : Ω → ℝ) "
        "(hq : ∀ ω, q_hat ω = orderStat s (⌈(↑(n₂ + 1) * (1 - α))⌉₊) ω) : "
        "P {ω | s (Fin.last n₂) ω ≤ q_hat ω} ≥ 1 - α := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:greek",
                "target_theorem_name": "split_conformal_coverage",
                "target_lean_declaration": "split_conformal_coverage",
                "source_theorem_target_known": True,
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": ["HSub ℕ ℝ ENNReal"],
                "missing_formal_symbols": ["Exchangeable", "orderStat"],
                "typeclass_blockers": ["HSub ℕ ℝ ENNReal"],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge_greek",
        queue_jsonl=queue_jsonl,
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    probe_manifest = json.loads(
        Path(str(manifest["signature_probe_manifest"])).read_text(encoding="utf-8")
    )
    probe_source = Path(
        str(probe_manifest["rows"][0]["signature_probe_artifact_path"])
    ).read_text(encoding="utf-8")
    assert "ENNReal.ofReal (1 - α)" in probe_source
    assert manifest["n_signature_probes_reached_proof_body"] == 1
    assert manifest["n_proof_body_execution_queue_rows"] == 1


def test_signature_probe_does_not_queue_proof_body_with_environment_errors(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "bad_environment_source_claim.lean"
    candidate_artifact.write_text(
        "import Mathlib.Probability.ProbabilityMeasure\n\n"
        "theorem bad_environment_source_claim {Ω : Type _} "
        "(P : MeasureProbability Ω) : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:bad_env",
                "question_id": "split_conformal",
                "target_theorem_name": "bad_environment_source_claim",
                "target_lean_declaration": "bad_environment_source_claim",
                "source_theorem_target_known": True,
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": [
                    "Function expected at",
                    "  MeasureProbability",
                    "error: unsolved goals",
                ],
                "missing_formal_symbols": [],
                "typeclass_blockers": [],
                "recommended_repair_tasks": [
                    "replace nonexistent MeasureProbability with a real Mathlib probability measure type"
                ],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue_jsonl,
        question_id="split_conformal",
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('Function expected at\\n  MeasureProbability\\nerror: unsolved goals'); sys.exit(1)",
        ),
    )

    assert manifest["n_signature_probe_rows"] == 1
    assert manifest["n_signature_probes_reached_proof_body"] == 0
    assert manifest["n_proof_body_work_orders"] == 0
    assert manifest["n_proof_body_execution_queue_rows"] == 0
    probe_manifest = json.loads(
        Path(str(manifest["signature_probe_manifest"])).read_text(encoding="utf-8")
    )
    probe_row = probe_manifest["rows"][0]
    assert probe_row["failure_classification"] == "formal_environment_symbol_missing"
    assert probe_row["signature_probe_status"] == "SIGNATURE_PROBE_LOCAL_LEAN_FAILED"
    assert probe_row["signature_typecheck_reached_proof_body"] is False


def test_signature_probe_tracks_generated_source_primitives_as_open_environment(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "split_conformal_coverage_lower.lean"
    candidate_artifact.write_text(
        "import Mathlib.Probability.ProbabilityMeasure\n"
        "import Mathlib.Order.LocallyFiniteOrder\n\n"
        "variable {Ω : Type _} [MeasurableSpace Ω] (P : MeasureProbability Ω)\n"
        "  (n : ℕ) (α : ℝ) (s : Fin (n+2) → Ω → ℝ)\n"
        "  (hexch : Exchangeable P s)\n\n"
        "def qHat (ω : Ω) : ℝ :=\n"
        "  orderStatistic (fun i : Fin (n+1) => s i ω) 1\n\n"
        "def covered (ω : Ω) : Prop := s (Fin.last (n+1)) ω ≤ qHat n α s ω\n\n"
        "theorem split_conformal_coverage_lower :\n"
        "    1 - α ≤ P.toMeasure {ω | covered n α s ω} := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:generated",
                "question_id": "split_conformal",
                "target_theorem_name": "split_conformal_coverage_lower",
                "target_lean_declaration": "split_conformal_coverage_lower",
                "source_theorem_target_known": True,
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "lean_import_environment_missing",
                "diagnostics": [
                    "object file 'Mathlib/Probability/ProbabilityMeasure.olean' does not exist"
                ],
                "missing_formal_symbols": [],
                "typeclass_blockers": [],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue_jsonl,
        question_id="split_conformal",
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    assert manifest["n_missing_formal_symbols"] == 3
    assert manifest["n_signature_probe_rows"] == 1
    assert manifest["n_signature_probes_reached_proof_body"] == 1
    assert manifest["n_proof_body_execution_queue_rows"] == 1
    repair_packet = json.loads(
        Path(str(manifest["repair_packets_jsonl"])).read_text(encoding="utf-8")
    )
    assert repair_packet["missing_formal_symbols"] == [
        "MeasureProbability",
        "Exchangeable",
        "orderStatistic",
    ]
    probe_manifest = json.loads(
        Path(str(manifest["signature_probe_manifest"])).read_text(encoding="utf-8")
    )
    probe_source = Path(
        str(probe_manifest["rows"][0]["signature_probe_artifact_path"])
    ).read_text(encoding="utf-8")
    assert "structure MeasureProbability" in probe_source
    assert "def Exchangeable" in probe_source
    assert "noncomputable def orderStatistic" in probe_source
    assert "import Mathlib\n" not in probe_source
    assert "s i.castSucc ω" in probe_source
    assert "qHat n α s ω" in probe_source
    assert "ENNReal.ofReal (1 - α) ≤ P.toMeasure" in probe_source
    execution_queue_manifest = json.loads(
        Path(str(manifest["proof_body_execution_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    execution_row = execution_queue_manifest["rows"][0]
    assert execution_row["already_repaired_environment"][
        "missing_formal_symbols"
    ] == [
        "MeasureProbability",
        "Exchangeable",
        "orderStatistic",
    ]
    assert execution_row["proof_evidence_status"] == (
        "EXACT_SOURCE_THEOREM_PROOF_BODY_EXECUTION_QUEUE_NOT_PROOF_EVIDENCE"
    )


def test_proof_body_execution_queue_blocks_target_declaration_mismatch(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "nearby_claim.lean"
    candidate_artifact.write_text(
        "import Mathlib\n\n"
        "theorem nearby_claim : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:mismatch",
                "target_theorem_name": "exact_source_claim",
                "target_lean_declaration": "exact_source_claim",
                "source_theorem_target_known": True,
                "source_theorem_route_id": "route:exact_source_claim",
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "formal_environment_symbol_missing",
                "diagnostics": ["Hint: The identifier `MissingPrimitive` is unknown."],
                "missing_formal_symbols": ["MissingPrimitive"],
                "typeclass_blockers": [],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge",
        queue_jsonl=queue_jsonl,
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    execution_queue_manifest = json.loads(
        Path(str(manifest["proof_body_execution_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    execution_row = execution_queue_manifest["rows"][0]
    assert execution_row["execution_status"] == (
        "BLOCKED_EXACT_SOURCE_PROOF_BODY_TARGET_IDENTITY"
    )
    assert execution_row["live_goal_location_ready"] is False
    assert execution_row["target_lean_declaration"] == "nearby_claim"
    assert execution_row["expected_target_lean_declaration"] == "exact_source_claim"
    assert execution_row["target_identity_status"] == "TARGET_DECLARATION_MISMATCH"
    assert execution_row["source_theorem_target_identity_status"] == (
        "TARGET_DECLARATION_MISMATCH"
    )
    assert "nearby_claim" in execution_row["target_identity_errors"][0]
    assert execution_row["live_proof_state_request"] == {}


def test_proof_body_queue_marks_matched_declaration_as_unpromoted_without_source_target(
    tmp_path: Path,
) -> None:
    candidate_artifact = tmp_path / "unpromoted_exact_claim.lean"
    candidate_artifact.write_text(
        "theorem exact_source_claim : True := by\n"
        "  fail_if_success trivial\n",
        encoding="utf-8",
    )
    queue_jsonl = tmp_path / "runtime_source_theorem_formal_environment_work_orders.jsonl"
    queue_jsonl.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "SourceTheoremFormalEnvironmentWorkOrder",
                "work_order_id": "source_theorem_formal_environment_work_order:unpromoted",
                "question_id": "question_from_formalizer_only",
                "target_theorem_name": "exact_source_claim",
                "target_lean_declaration": "exact_source_claim",
                "source_theorem_target_known": False,
                "source_theorem_target_provenance": {
                    "source_theorem_question_id": "question_from_formalizer_only"
                },
                "candidate_artifact_path": str(candidate_artifact),
                "failure_classification": "lean_import_environment_missing",
                "diagnostics": ["unsolved goals"],
                "missing_formal_symbols": [],
                "typeclass_blockers": [],
                "proof_evidence_status": "WORK_ORDER_NOT_PROOF_EVIDENCE",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = run_source_theorem_formal_environment_proofengineer_bridge(
        out_dir=tmp_path / "bridge_unpromoted",
        queue_jsonl=queue_jsonl,
        run_signature_probes=True,
        lean_command=(
            sys.executable,
            "-c",
            "import sys; print('unsolved goals'); sys.exit(1)",
        ),
    )

    execution_queue_manifest = json.loads(
        Path(str(manifest["proof_body_execution_queue_manifest"])).read_text(
            encoding="utf-8"
        )
    )
    execution_row = execution_queue_manifest["rows"][0]
    assert execution_row["target_identity_status"] == "TARGET_DECLARATION_MATCHED"
    assert execution_row["source_theorem_target_known"] is False
    assert execution_row["source_theorem_target_identity_status"] == (
        "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
    )
    assert execution_row["live_proof_state_request"][
        "source_theorem_target_identity_status"
    ] == "DECLARATION_MATCHED_SOURCE_THEOREM_TARGET_UNPROMOTED"
