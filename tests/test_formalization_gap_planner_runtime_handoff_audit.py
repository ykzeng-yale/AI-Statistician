from __future__ import annotations

import json
import shutil
import shlex
from pathlib import Path

from ai_statistician.formalization_gap_planner_runtime_handoff_audit import (
    RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
    _run_llm_prompt_smoke,
    audit_formalization_gap_planner_runtime_handoffs,
    validate_runtime_handoff_execution_plan,
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
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
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
    handoff_target = "rocq"
    handoff_row = {
        "schema_version": 1,
        "artifact_kind": "RuntimeFormalizationGapPlannerHandoff",
        "handoff_id": "runtime_formalization_gap_planner_handoff:mixed_seed",
        "bridge_id": "runtime_formalization_gap_planner_bridge:mixed_seed",
        "standalone_seed_path": str(seed_path),
        "target_intake_path": str(target_intake_path),
        "target_intake_dir": str(target_intake_dir),
        "target_prover_family": handoff_target,
        "library_snapshot_ref": "portable:runtime-mixed-targets",
        "recommended_llm_provider": "anthropic",
        "recommended_model_tier": "haiku",
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
        "standalone_plan_dir": str(standalone_plan_dir),
        "target_intake_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-target-intake --input {target_intake_path} "
            f"--out {target_intake_dir}"
        ),
        "llm_route_planner_prompt_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-llm-route-planner --input {seed_path} "
            "--provider anthropic --model-tier haiku --max-repair-attempts 1 "
            "--max-estimated-prompt-input-tokens 0 "
            "--goal-conditioned-minimal-formalization-plan-dir "
            f"{standalone_plan_dir} "
            f"--formalization-gap-planner-target-intake-dir {target_intake_dir} "
            "--formalization-gap-planner-component-resource-registry-dir "
            f"{registry_dir} --out {root / 'llm_prompt'}"
        ),
        "llm_route_planner_live_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-llm-route-planner --input {seed_path} "
            "--provider anthropic --model-tier haiku --max-repair-attempts 1 "
            "--max-estimated-prompt-input-tokens 0 "
            "--goal-conditioned-minimal-formalization-plan-dir "
            f"{standalone_plan_dir} "
            f"--formalization-gap-planner-target-intake-dir {target_intake_dir} "
            "--formalization-gap-planner-component-resource-registry-dir "
            f"{registry_dir} --invoke-provider --out {root / 'llm_live'}"
        ),
        "reuse_smoke_cli": (
            "python3 -m ai_statistician.cli formalization-gap-planner-reuse-smoke "
            f"--input {target_intake_path} "
            f"--target-prover-family {handoff_target} "
            "--target-library-snapshot-ref portable:runtime-mixed-targets "
            "--llm-route-planner-provider anthropic "
            "--llm-route-planner-model-tier haiku "
            "--llm-route-planner-max-repair-attempts 1 "
            "--llm-route-planner-max-estimated-prompt-input-tokens 0 "
            "--feedback-llm-route-planner-provider anthropic "
            "--feedback-llm-route-planner-model-tier haiku "
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
    stage_specs = [
        (
            "standalone_plan",
            "formalization-gap-planner-standalone-plan",
            handoff_row["standalone_plan_cli"],
            False,
            [str(seed_path)],
            [str(root / "standalone_plan")],
        ),
        (
            "target_intake",
            "formalization-gap-planner-target-intake",
            handoff_row["target_intake_cli"],
            False,
            [str(target_intake_path)],
            [str(target_intake_dir)],
        ),
        (
            "component_resource_registry",
            "formalization-gap-planner-component-resource-registry",
            handoff_row["component_resource_registry_cli"],
            False,
            [],
            [str(registry_dir)],
        ),
        (
            "llm_route_planner_prompt",
            "formalization-gap-planner-llm-route-planner",
            handoff_row["llm_route_planner_prompt_cli"],
            False,
            [str(seed_path), str(root / "standalone_plan"), str(target_intake_dir), str(registry_dir)],
            [str(root / "llm_prompt")],
        ),
        (
            "llm_route_planner_live_optional",
            "formalization-gap-planner-llm-route-planner",
            handoff_row["llm_route_planner_live_cli"],
            True,
            [str(seed_path), str(root / "standalone_plan"), str(target_intake_dir), str(registry_dir)],
            [str(root / "llm_live")],
        ),
        (
            "reuse_smoke",
            "formalization-gap-planner-reuse-smoke",
            handoff_row["reuse_smoke_cli"],
            False,
            [str(target_intake_path)],
            [str(root / "reuse_smoke")],
        ),
    ]
    handoff_row["execution_plan"] = {
        "plan_kind": "runtime_formalization_gap_planner_handoff_execution_plan",
        "schema_version": 1,
        "recommended_llm_provider": "anthropic",
        "recommended_model_tier": "haiku",
        "target_prover_family": handoff_target,
        "library_snapshot_ref": "portable:runtime-mixed-targets",
        "stage_count": len(stage_specs),
        "stages": [
            {
                "stage_id": stage_id,
                "command": command,
                "cli": cli,
                "argv": shlex.split(cli),
                "requires_live_llm": requires_live_llm,
                "requires_operator_review_before_live": requires_live_llm,
                "required_inputs": required_inputs,
                "expected_outputs": expected_outputs,
                "purpose": f"run {stage_id}",
                "proof_evidence_status": RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
                "proof_evidence_boundary": (
                    "Runtime handoff execution stages are not theorem proof evidence."
                ),
            }
            for (
                stage_id,
                command,
                cli,
                requires_live_llm,
                required_inputs,
                expected_outputs,
            ) in stage_specs
        ],
        "cost_control_boundary": (
            "Prompt stages are offline; the only live Claude API stage is explicit."
        ),
        "proof_evidence_status": RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": (
            "Runtime handoff execution plans are not theorem proof evidence."
        ),
    }
    handoff_row["execution_plan_stage_count"] = len(stage_specs)
    handoffs_path.write_text(json.dumps(handoff_row) + "\n", encoding="utf-8")

    payload = audit_formalization_gap_planner_runtime_handoffs(
        handoffs_path,
        out_dir,
        run_smoke=True,
    )

    assert payload["all_ok"]
    assert payload["n_mixed_seed_target_prover_families"] == 1
    assert payload["n_seed_target_prover_family_compatible_with_handoff"] == 1
    assert payload["n_execution_plans"] == 1
    assert payload["n_execution_plan_stage_rows"] == 6
    assert payload["n_execution_plan_schema_valid"] == 1
    assert payload["n_execution_plan_rows"] == 1
    assert payload["n_execution_plan_row_schema_valid"] == 1
    assert payload["n_execution_plan_row_schema_invalid"] == 0
    assert payload["n_execution_plan_prompt_stage_cost_control_ok"] == 1
    assert payload["n_execution_plan_live_stage_explicit_ok"] == 1
    assert payload["n_execution_plan_reuse_smoke_stage_cost_control_ok"] == 1
    assert payload["n_llm_prompt_packets"] == 2
    assert payload["n_llm_prompt_report_only_prompt_budget_caps"] == 1
    assert payload["n_llm_prompt_prompt_budget_preflight_blocked"] == 0
    assert payload["n_llm_prompt_model_tier_mismatches"] == 0
    assert payload["n_llm_prompt_model_tier_haiku"] == 2
    assert payload["n_llm_prompt_model_tier_sonnet"] == 0
    assert payload["n_llm_prompt_model_tier_opus"] == 0
    summary = payload["smoke_summaries"][0]
    assert summary["seed_declared_target_prover_family"] == ""
    assert summary["seed_target_prover_family"] == "mixed:lean4,rocq"
    assert summary["seed_n_target_prover_families"] == 2
    assert summary["seed_by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    assert summary["llm_prompt_model_tier_haiku"] == 2
    assert summary["llm_prompt_max_estimated_prompt_input_tokens"] == 0
    assert summary["llm_prompt_prompt_budget_preflight_blocked"] == 0
    assert summary["standalone_plan_dir"] == str(standalone_plan_dir)
    assert summary["llm_prompt_model_tier_sonnet"] == 0
    assert summary["llm_prompt_model_tier_opus"] == 0
    report = (
        out_dir / "formalization_gap_planner_runtime_handoff_audit.md"
    ).read_text(encoding="utf-8")
    execution_plan_rows_path = (
        out_dir / "formalization_gap_planner_runtime_handoff_execution_plans.jsonl"
    )
    assert execution_plan_rows_path.exists()
    execution_plan_rows = [
        json.loads(line)
        for line in execution_plan_rows_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert execution_plan_rows[0]["handoff_id"] == handoff_row["handoff_id"]
    assert execution_plan_rows[0]["stage_count"] == 6
    assert "- LLM prompt model tiers: haiku=2 sonnet=0 opus=0" in report
    assert "- LLM prompt budget caps report-only/blocks: 1/0" in report
    assert (
        out_dir
        / "formalization_gap_planner_runtime_handoff_execution_plan.schema.json"
    ).exists()
    assert "- Execution plan JSONL schema valid: 1/1" in report
    assert "- LLM prompt model tiers: haiku=2 sonnet=0 opus=0" in report
    request_rows = [
        json.loads(line)
        for line in (
            Path(str(payload["smoke_root"]))
            / "runtime_formalization_gap_planner_handoff_mixed_seed"
            / "llm_route_planner_prompt"
            / "formalization_gap_planner_llm_route_planner_requests.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert {row["model_tier"] for row in request_rows} == {"haiku"}
    assert {row["model"] for row in request_rows} == {
        "claude-haiku-4-5-20251001"
    }
    seed_target_checks = {
        str(check["check_name"]).split(":", 1)[0]: check
        for check in payload["checks"]
        if str(check["check_name"]).startswith("row_seed_target_prover_family")
    }
    assert seed_target_checks["row_seed_target_prover_family_present"]["ok"]
    assert seed_target_checks["row_seed_target_prover_family_matches_handoff"]["ok"]

    audit_smoke_dir = (
        Path(str(payload["smoke_root"]))
        / "runtime_formalization_gap_planner_handoff_mixed_seed"
    )
    budget_ok, budget_observed, budget_counts = _run_llm_prompt_smoke(
        seed_path,
        handoff_id="budget_staged_route",
        smoke_root=root / "budget_staged_smoke",
        target_intake_dir=audit_smoke_dir / "target_intake",
        component_resource_registry_dir=(
            audit_smoke_dir / "component_resource_registry"
        ),
        model_tier="haiku",
        max_estimated_prompt_input_tokens=1,
    )
    assert budget_ok, budget_observed
    assert budget_counts["llm_prompt_prompt_budget_preflight_blocked"] == 2
    assert budget_counts["llm_prompt_staged_budget_route_ready"] == 1
    assert budget_counts["llm_prompt_staged_followups_required"] == 2
    assert budget_counts[
        "llm_prompt_staged_followups_due_to_prompt_budget"
    ] == 2

    prompt_budget_rows_path = (
        audit_smoke_dir
        / "llm_route_planner_prompt"
        / "formalization_gap_planner_llm_route_planner_prompt_token_budget.jsonl"
    )
    prompt_estimates = [
        int(json.loads(line)["estimated_input_tokens"])
        for line in prompt_budget_rows_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert min(prompt_estimates) < max(prompt_estimates)
    mixed_ok, mixed_observed, mixed_counts = _run_llm_prompt_smoke(
        seed_path,
        handoff_id="mixed_direct_and_staged_route",
        smoke_root=root / "mixed_direct_and_staged_smoke",
        target_intake_dir=audit_smoke_dir / "target_intake",
        component_resource_registry_dir=(
            audit_smoke_dir / "component_resource_registry"
        ),
        model_tier="haiku",
        max_estimated_prompt_input_tokens=min(prompt_estimates),
    )
    assert mixed_ok, mixed_observed
    assert mixed_counts["llm_prompt_awaiting_response"] == 1
    assert mixed_counts["llm_prompt_prompt_budget_preflight_blocked"] == 1
    assert mixed_counts["llm_prompt_staged_budget_route_ready"] == 1
    assert mixed_counts["llm_prompt_staged_followups_required"] == 1

    drifted_execution_plan = json.loads(
        json.dumps(handoff_row["execution_plan"])
    )
    drifted_execution_plan["recommended_model_tier"] = "auto"
    drift_errors = validate_runtime_handoff_execution_plan(
        drifted_execution_plan
    )
    assert (
        "llm_route_planner_prompt.argv --model-tier must equal "
        "recommended_model_tier auto"
    ) in drift_errors
    assert (
        "reuse_smoke.argv --feedback-llm-route-planner-model-tier must equal "
        "recommended_model_tier auto"
    ) in drift_errors

    unsupported_execution_plan = json.loads(
        json.dumps(handoff_row["execution_plan"])
    )
    unsupported_execution_plan["recommended_model_tier"] = "opus"
    assert (
        "recommended_model_tier must be one of ['auto', 'haiku', 'sonnet']"
        in validate_runtime_handoff_execution_plan(unsupported_execution_plan)
    )
