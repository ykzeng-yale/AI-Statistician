from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_runtime_handoff_audit import (
    RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
    audit_formalization_gap_planner_runtime_handoffs,
)
from ai_statistician.research_agent_runtime import (
    _runtime_formalization_gap_planner_handoff_execution_plan,
)


def test_runtime_handoff_audit_accepts_mixed_seed_when_handoff_target_is_in_seed() -> None:
    root = Path("runs/test_formalization_gap_planner_runtime_handoff_audit_mixed_seed")
    seed_path = root / "standalone_seed.json"
    target_intake_path = root / "target_intake.json"
    handoffs_path = root / "handoffs.jsonl"
    out_dir = root / "audit"
    standalone_plan_dir = root / "standalone_plan"
    target_intake_dir = root / "target_intake_dir"
    registry_dir = root / "component_resource_registry"
    route_replan_handoff_dir = root / "route_replan_handoff"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    route_replan_handoff_dir.mkdir(parents=True, exist_ok=True)
    seed_payload = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_standalone_input",
        "library_snapshot_ref": "portable:runtime-mixed-targets",
        "routes": [
            {
                "route_id": "lean_rank_route",
                "display_name": "lean_rank_route",
                "target_prover_family": "lean4",
                "theorem_statement": "A Lean rank route.",
                "primitives": [
                    {
                        "primitive": "exchangeability",
                        "coverage_status": "exact_exists",
                        "candidate_declaration_rows": [
                            {
                                "declaration": "Probability.exchangeable",
                                "target_prover_family": "lean4",
                                "source_field": "runtime_test_fixture",
                            }
                        ],
                    }
                ],
            },
            {
                "route_id": "rocq_rank_route",
                "display_name": "rocq_rank_route",
                "target_prover_family": "rocq",
                "theorem_statement": "A Rocq rank route.",
                "primitives": [
                    {
                        "primitive": "exchangeability",
                        "coverage_status": "exact_exists",
                        "candidate_declaration_rows": [
                            {
                                "declaration": "Rocq.Probability.exchangeable",
                                "target_prover_family": "rocq",
                                "source_field": "runtime_test_fixture",
                            }
                        ],
                    }
                ],
            },
        ],
    }
    target_intake_payload = {
        "schema_version": 1,
        "component_name": "formalization_gap_planner_target_intake",
        "library_snapshot_ref": "portable:runtime-mixed-targets",
        "targets": [
            {
                "target_prover_family": "lean4",
                "target_id": "lean_rank_route",
                "theorem_statement": "A Lean rank route.",
                "known_proof_sources": ["runtime fixture"],
                "candidate_primitives": ["exchangeability"],
            },
            {
                "target_prover_family": "rocq",
                "target_id": "rocq_rank_route",
                "theorem_statement": "A Rocq rank route.",
                "known_proof_sources": ["runtime fixture"],
                "candidate_primitives": ["exchangeability"],
            },
        ],
    }
    seed_path.write_text(json.dumps(seed_payload, indent=2), encoding="utf-8")
    target_intake_path.write_text(
        json.dumps(target_intake_payload, indent=2),
        encoding="utf-8",
    )
    formal_attempt_context = {
        "attempt_id": "attempt:rocq_rank_uniformity_bridge",
        "formal_node_id": "formal:rocq_rank_uniformity",
        "formal_attempt_queue_index": 0,
        "formal_attempt_dependency_status": "initial_ready",
        "attempt_kind": "bridge_lemma",
        "primitive": "rank_uniformity",
        "target_primitives": ["rank_uniformity"],
        "target_prover_family": "rocq",
        "prerequisite_formal_node_ids": [],
        "prerequisite_attempt_ids": [],
        "missing_prerequisite_formal_node_ids": [],
        "expected_feedback": ["kernel_status", "residual_goals"],
    }
    (
        route_replan_handoff_dir
        / "formalization_gap_planner_route_replan_handoff_manifest.json"
    ).write_text(
        json.dumps(
            {
                "component_name": "formalization_gap_planner_route_replan_handoff",
                "rows": [
                    {
                        "route_replan_handoff_id": (
                            "handoff:rocq_rank_route_formal_attempt_feedback"
                        ),
                        "route_revision_overlay_id": (
                            "overlay:rocq_rank_route_formal_attempt_feedback"
                        ),
                        "goal_plan_id": "rocq_rank_route",
                        "route_id": "rocq_rank_route",
                        "display_name": "rocq_rank_route",
                        "applied_hook_kinds": ["resource_response_ledger"],
                        "applied_resource_response_traces": [
                            {
                                "resource_response_ledger_id": (
                                    "ledger:rocq_rank_uniformity_attempt"
                                ),
                                "resource_request_id": (
                                    "request:rocq_rank_uniformity_attempt"
                                ),
                                "resource_id": "rocq_lsp_mcp",
                                "target_primitives": ["rank_uniformity"],
                                "formal_attempt_context": formal_attempt_context,
                                "residual_goals": [
                                    (
                                        "rocq_rank_uniformity needs an explicit "
                                        "measurability side condition"
                                    )
                                ],
                                "prover_attempt_status": (
                                    "failed_with_residual_goals"
                                ),
                                "prover_diagnostic_signature": (
                                    "residual_goal:rocq_rank_uniformity_measurability"
                                ),
                                "route_revision_recommended": True,
                                "route_revision_reasons": [
                                    (
                                        "formal attempt exposed a source-backed "
                                        "measurability side condition"
                                    )
                                ],
                            }
                        ],
                        "applied_llm_route_planner_hook_traces": [
                            {
                                "llm_route_planner_row_id": (
                                    "llm_route:rocq_rank_uniformity_feedback"
                                ),
                                "llm_route_planner_request_id": (
                                    "llm_request:rocq_rank_uniformity_feedback"
                                ),
                                "llm_route_planner_hook_kind": (
                                    "formal_attempt_feedback"
                                ),
                                "formal_attempt_context": formal_attempt_context,
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    handoff_target = "rocq"
    handoff_row = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizationGapPlannerHandoff",
        "handoff_id": "runtime_formalization_gap_planner_handoff:mixed_seed",
        "bridge_id": "runtime_formalization_gap_planner_bridge:mixed_seed",
        "standalone_seed_path": str(seed_path),
        "standalone_plan_dir": str(standalone_plan_dir),
        "target_intake_path": str(target_intake_path),
        "target_intake_dir": str(target_intake_dir),
        "target_prover_family": handoff_target,
        "library_snapshot_ref": "portable:runtime-mixed-targets",
        "recommended_llm_provider": "anthropic",
        "recommended_model_tier": "auto",
        "formalization_gap_planner_route_replan_handoff_dir": str(
            route_replan_handoff_dir
        ),
        "component_resource_registry_dir": str(registry_dir),
        "component_resource_registry_cli": (
            "python3 -m ai_statistician.cli "
            "formalization-gap-planner-component-resource-registry "
            f"--out {registry_dir}"
        ),
        "standalone_plan_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-standalone-plan --input {seed_path} "
            f"--out {standalone_plan_dir}"
        ),
        "target_intake_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-target-intake --input {target_intake_path} "
            f"--out {target_intake_dir}"
        ),
        "llm_route_planner_prompt_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-llm-route-planner --input {seed_path} "
            "--provider anthropic --model-tier auto --max-repair-attempts 1 "
            "--max-estimated-prompt-input-tokens 0 "
            "--goal-conditioned-minimal-formalization-plan-dir "
            f"{standalone_plan_dir} "
            f"--formalization-gap-planner-target-intake-dir {target_intake_dir} "
            "--formalization-gap-planner-route-replan-handoff-dir "
            f"{route_replan_handoff_dir} "
            "--formalization-gap-planner-component-resource-registry-dir "
            f"{registry_dir} --out {root / 'llm_prompt'}"
        ),
        "llm_route_planner_live_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-llm-route-planner --input {seed_path} "
            "--provider anthropic --model-tier auto --max-repair-attempts 1 "
            "--max-estimated-prompt-input-tokens 0 "
            "--goal-conditioned-minimal-formalization-plan-dir "
            f"{standalone_plan_dir} "
            f"--formalization-gap-planner-target-intake-dir {target_intake_dir} "
            "--formalization-gap-planner-route-replan-handoff-dir "
            f"{route_replan_handoff_dir} "
            "--formalization-gap-planner-component-resource-registry-dir "
            f"{registry_dir} --invoke-provider --out {root / 'llm_live'}"
        ),
        "reuse_smoke_cli": (
            "python3 -m ai_statistician.cli formalization-gap-planner-reuse-smoke "
            f"--input {target_intake_path} "
            f"--target-prover-family {handoff_target} "
            "--target-library-snapshot-ref portable:runtime-mixed-targets "
            "--llm-route-planner-provider anthropic "
            "--llm-route-planner-model-tier auto "
            "--llm-route-planner-max-repair-attempts 1 "
            "--llm-route-planner-max-estimated-prompt-input-tokens 0 "
            "--feedback-llm-route-planner-provider anthropic "
            "--feedback-llm-route-planner-model-tier auto "
            "--feedback-llm-route-planner-max-repair-attempts 1 "
            "--feedback-llm-route-planner-max-estimated-prompt-input-tokens 0 "
            f"--out {root / 'reuse_smoke'}"
        ),
        "cost_control": (
            "Run prompt-only handoff first; live execution is explicit."
        ),
        "proof_evidence_status": RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "Runtime handoff rows are not theorem proof evidence."
        ),
    }
    execution_plan = _runtime_formalization_gap_planner_handoff_execution_plan(
        standalone_plan_cli=handoff_row["standalone_plan_cli"],
        target_intake_cli=handoff_row["target_intake_cli"],
        component_resource_registry_cli=handoff_row[
            "component_resource_registry_cli"
        ],
        llm_route_planner_prompt_cli=handoff_row[
            "llm_route_planner_prompt_cli"
        ],
        llm_route_planner_live_cli=handoff_row["llm_route_planner_live_cli"],
        reuse_smoke_cli=handoff_row["reuse_smoke_cli"],
        standalone_seed_path=str(seed_path),
        target_intake_path=str(target_intake_path),
        standalone_plan_dir=str(standalone_plan_dir),
        target_intake_dir=str(target_intake_dir),
        component_resource_registry_dir=str(registry_dir),
        llm_prompt_out=str(root / "llm_prompt"),
        llm_live_out=str(root / "llm_live"),
        reuse_smoke_out=str(root / "reuse_smoke"),
        target_prover_family=handoff_target,
        library_snapshot_ref="portable:runtime-mixed-targets",
    )
    handoff_row["execution_plan"] = execution_plan
    handoff_row["execution_plan_stage_count"] = execution_plan["stage_count"]
    handoffs_path.write_text(json.dumps(handoff_row) + "\n", encoding="utf-8")

    payload = audit_formalization_gap_planner_runtime_handoffs(
        handoffs_path,
        out_dir,
        run_smoke=True,
    )

    assert payload["all_ok"]
    assert payload["n_mixed_seed_target_prover_families"] == 1
    assert payload["n_seed_target_prover_family_compatible_with_handoff"] == 1
    assert payload["n_llm_prompt_packets"] == 2
    assert payload["n_execution_plans"] == 1
    assert payload["n_execution_plan_stage_rows"] == 6
    assert payload["n_execution_plan_schema_valid"] == 1
    assert payload["n_llm_prompt_report_only_prompt_budget_caps"] == 1
    assert payload["n_llm_prompt_prompt_budget_preflight_blocked"] == 0
    assert payload["n_llm_prompt_model_tier_mismatches"] == 0
    assert payload["n_llm_prompt_requests_with_current_goal_plan_rows"] == 2
    assert payload["n_llm_prompt_current_goal_plan_rows"] == 2
    assert payload["n_llm_prompt_model_tier_haiku"] == 0
    assert payload["n_llm_prompt_model_tier_sonnet"] == 2
    assert payload["n_llm_prompt_model_tier_opus"] == 0
    assert payload["n_llm_prompt_requests_with_model_tier_decision_evidence"] == 2
    assert payload["n_llm_prompt_model_tier_decision_auto_haiku_bounded"] == 0
    assert payload["n_llm_prompt_model_tier_decision_auto_sonnet_triggered"] == 2
    assert payload["n_llm_prompt_model_tier_decision_operator_override"] == 0
    assert payload["n_llm_prompt_model_tier_decision_sonnet_triggers"] > 0
    assert payload["n_llm_prompt_requests_with_formal_attempt_feedback_summary"] == 1
    assert payload["n_llm_prompt_formal_attempt_feedback_contexts"] == 1
    assert payload["n_llm_prompt_formal_attempt_feedback_residual_goals"] == 1
    assert payload["n_llm_prompt_formal_attempt_feedback_failed_statuses"] == 1
    assert (
        out_dir
        / "formalization_gap_planner_runtime_handoff_execution_plan.schema.json"
    ).exists()
    assert (
        payload[
            "n_llm_prompt_model_tier_decision_formal_attempt_feedback_contexts"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_prompt_model_tier_decision_formal_attempt_feedback_residual_goals"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_prompt_model_tier_decision_formal_attempt_feedback_failed_statuses"
        ]
        == 1
    )
    assert (
        payload[
            "n_llm_prompt_model_tier_decision_formal_attempt_feedback_sonnet_triggers"
        ]
        == 1
    )
    assert payload["n_llm_prompt_model_tier_decision_evidence_invalid"] == 0
    assert payload["llm_prompt_by_model_tier_decision_basis"] == {
        "auto_sonnet_triggers": 2
    }
    summary = payload["smoke_summaries"][0]
    assert summary["seed_declared_target_prover_family"] == ""
    assert summary["seed_target_prover_family"] == "mixed:lean4,rocq"
    assert summary["seed_n_target_prover_families"] == 2
    assert summary["seed_by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    assert summary["llm_prompt_model_tier_haiku"] == 0
    assert summary["llm_prompt_max_estimated_prompt_input_tokens"] == 0
    assert summary["llm_prompt_prompt_budget_preflight_blocked"] == 0
    assert summary["standalone_plan_dir"] == str(standalone_plan_dir)
    assert summary["llm_prompt_requests_with_current_goal_plan_rows"] == 2
    assert summary["llm_prompt_current_goal_plan_rows"] == 2
    assert summary["llm_prompt_model_tier_sonnet"] == 2
    assert summary["llm_prompt_model_tier_opus"] == 0
    assert summary["llm_prompt_requests_with_model_tier_decision_evidence"] == 2
    assert summary["llm_prompt_model_tier_decision_auto_haiku_bounded"] == 0
    assert summary["llm_prompt_model_tier_decision_auto_sonnet_triggered"] == 2
    assert summary["llm_prompt_model_tier_decision_operator_override"] == 0
    assert summary["llm_prompt_model_tier_decision_sonnet_triggers"] > 0
    assert summary["llm_prompt_requests_with_formal_attempt_feedback_summary"] == 1
    assert summary["llm_prompt_formal_attempt_feedback_contexts"] == 1
    assert summary["llm_prompt_formal_attempt_feedback_residual_goals"] == 1
    assert summary["llm_prompt_formal_attempt_feedback_failed_statuses"] == 1
    assert (
        summary[
            "llm_prompt_model_tier_decision_formal_attempt_feedback_contexts"
        ]
        == 1
    )
    assert (
        summary[
            "llm_prompt_model_tier_decision_formal_attempt_feedback_residual_goals"
        ]
        == 1
    )
    assert (
        summary[
            "llm_prompt_model_tier_decision_formal_attempt_feedback_failed_statuses"
        ]
        == 1
    )
    assert (
        summary[
            "llm_prompt_model_tier_decision_formal_attempt_feedback_sonnet_triggers"
        ]
        == 1
    )
    assert summary["llm_prompt_model_tier_decision_evidence_invalid"] == 0
    assert summary["llm_prompt_by_model_tier_decision_basis"] == {
        "auto_sonnet_triggers": 2
    }
    report = (
        out_dir / "formalization_gap_planner_runtime_handoff_audit.md"
    ).read_text(encoding="utf-8")
    assert "- LLM prompt model tiers: haiku=0 sonnet=2 opus=0" in report
    assert "- LLM prompt budget caps report-only/blocks: 1/0" in report
    assert "- Standalone goal-plan context in prompts: requests=2 rows=2" in report
    assert (
        "- LLM prompt model-tier decision basis: {'auto_sonnet_triggers': 2} "
        "evidence=2"
    ) in report
    assert (
        "- LLM prompt formal-attempt feedback: requests=1 contexts=1 "
        "residual_goals=1 failed_statuses=1 tier_contexts=1 "
        "tier_residual_goals=1 tier_failed_statuses=1 "
        "tier_sonnet_triggers=1"
    ) in report
    seed_target_checks = {
        str(check["check_name"]).split(":", 1)[0]: check
        for check in payload["checks"]
        if str(check["check_name"]).startswith("row_seed_target_prover_family")
    }
    assert seed_target_checks["row_seed_target_prover_family_present"]["ok"]
    assert seed_target_checks["row_seed_target_prover_family_matches_handoff"]["ok"]
