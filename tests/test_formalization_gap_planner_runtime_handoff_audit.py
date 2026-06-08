from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_runtime_handoff_audit import (
    RUNTIME_BRIDGE_PROOF_EVIDENCE_STATUS,
    audit_formalization_gap_planner_runtime_handoffs,
)


def test_runtime_handoff_audit_accepts_mixed_seed_when_handoff_target_is_in_seed() -> None:
    root = Path("runs/test_formalization_gap_planner_runtime_handoff_audit_mixed_seed")
    seed_path = root / "standalone_seed.json"
    target_intake_path = root / "target_intake.json"
    handoffs_path = root / "handoffs.jsonl"
    out_dir = root / "audit"
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
        "target_prover_family": handoff_target,
        "library_snapshot_ref": "portable:runtime-mixed-targets",
        "recommended_llm_provider": "anthropic",
        "recommended_model_tier": "auto",
        "component_resource_registry_dir": str(registry_dir),
        "component_resource_registry_cli": (
            "python3 -m ai_statistician.cli "
            "formalization-gap-planner-component-resource-registry "
            f"--out {registry_dir}"
        ),
        "standalone_plan_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-standalone-plan --input {seed_path} "
            f"--out {root / 'standalone_plan'}"
        ),
        "llm_route_planner_prompt_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-llm-route-planner --input {seed_path} "
            "--provider anthropic --model-tier auto --max-repair-attempts 1 "
            "--formalization-gap-planner-component-resource-registry-dir "
            f"{registry_dir} --out {root / 'llm_prompt'}"
        ),
        "llm_route_planner_live_cli": (
            "python3 -m ai_statistician.cli "
            f"formalization-gap-planner-llm-route-planner --input {seed_path} "
            "--provider anthropic --model-tier auto --max-repair-attempts 1 "
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
            "--feedback-llm-route-planner-provider anthropic "
            "--feedback-llm-route-planner-model-tier auto "
            "--feedback-llm-route-planner-max-repair-attempts 1 "
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
    handoffs_path.write_text(json.dumps(handoff_row) + "\n", encoding="utf-8")

    payload = audit_formalization_gap_planner_runtime_handoffs(
        handoffs_path,
        out_dir,
        run_smoke=False,
    )

    assert payload["all_ok"]
    assert payload["n_mixed_seed_target_prover_families"] == 1
    assert payload["n_seed_target_prover_family_compatible_with_handoff"] == 1
    summary = payload["smoke_summaries"][0]
    assert summary["seed_declared_target_prover_family"] == ""
    assert summary["seed_target_prover_family"] == "mixed:lean4,rocq"
    assert summary["seed_n_target_prover_families"] == 2
    assert summary["seed_by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    seed_target_checks = {
        str(check["check_name"]).split(":", 1)[0]: check
        for check in payload["checks"]
        if str(check["check_name"]).startswith("row_seed_target_prover_family")
    }
    assert seed_target_checks["row_seed_target_prover_family_present"]["ok"]
    assert seed_target_checks["row_seed_target_prover_family_matches_handoff"]["ok"]
