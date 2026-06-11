from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_local_proof_state_adapter import (
    export_formalization_gap_planner_local_proof_state_adapter_responses,
)
from ai_statistician.formalization_gap_planner_refinement_evidence import (
    export_formalization_gap_planner_refinement_evidence,
)


def test_local_proof_state_adapter_emits_prover_feedback(
    monkeypatch,
) -> None:
    root = Path("runs/test_formalization_gap_planner_local_proof_state_adapter")
    queue_dir = root / "queue"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    bin_dir = root / "bin"
    base_response_jsonl = root / "base_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    fake_lean = bin_dir / "lean"
    fake_lean.write_text(
        "#!/bin/sh\n"
        "echo \"$1:3:12: error: unsolved goals\" >&2\n"
        "echo \"case h\" >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake_lean.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    display_name = "causal_ate_aipw:aipw_double_robustness:skeleton"
    queue_rows = [
        {
            "refinement_item_id": "refinement:lean",
            "goal_plan_id": "goal:test",
            "route_id": "route:test",
            "display_name": display_name,
            "hook_kind": "lean_library_grounding",
            "refinement_stage": "lean",
            "owner_agent": "lean",
            "target_primitives": ["conditional_mean_residual_zero"],
            "queries": ["conditional mean residual zero Lean theorem"],
        },
        {
            "refinement_item_id": "refinement:proof",
            "goal_plan_id": "goal:test",
            "route_id": "route:test",
            "display_name": display_name,
            "hook_kind": "proof_state_feedback",
            "refinement_stage": "proof",
            "owner_agent": "proof",
            "target_primitives": ["conditional_mean_residual_zero"],
            "theorem_skeleton": "theorem probe_conditional_mean_residual_zero : True := by\n  exact False.elim (by exact False.elim (by contradiction))",
            "queries": ["probe conditional mean residual zero"],
        },
        {
            "refinement_item_id": "refinement:name_only",
            "goal_plan_id": "goal:test",
            "route_id": "route:test",
            "display_name": display_name,
            "hook_kind": "proof_state_feedback",
            "refinement_stage": "proof",
            "owner_agent": "proof",
            "target_primitives": ["nuisance_correctness_cases"],
            "theorem_skeleton": "skeleton",
            "queries": ["name-only theorem skeleton"],
        },
        {
            "refinement_item_id": "refinement:formal_gap",
            "goal_plan_id": "goal:test",
            "route_id": "route:test",
            "display_name": display_name,
            "hook_kind": "proof_state_feedback",
            "refinement_stage": "proof",
            "owner_agent": "proof",
            "target_primitives": ["nuisance_correctness_cases"],
            "theorem_skeleton": (
                "/- Status: FORMAL_GAP. -/\n"
                "theorem probe_frontier_gap "
                "(h_frontier_missing_nuisance_correctness_cases : True) : True := by\n"
                "  exact h_frontier_missing_nuisance_correctness_cases"
            ),
            "queries": ["formal gap theorem skeleton"],
        },
    ]
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps({"rows": queue_rows}, indent=2),
        encoding="utf-8",
    )
    base_response_jsonl.write_text(
        json.dumps(
            {
                "refinement_item_id": "refinement:lean",
                "route_id": "route:test",
                "display_name": display_name,
                "evidence_kind": "lean_library_grounding",
                "tool_name": "fixture_lean_grounding_adapter",
                "lean_declaration_hits": [
                    {
                        "primitive": "conditional_mean_residual_zero",
                        "declaration": "Demo.conditional_mean_residual_zero",
                    }
                ],
                "coverage_updates": {"conditional_mean_residual_zero": "exact_exists"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_local_proof_state_adapter_responses(
        queue_dir,
        adapter_dir,
        base_response_jsonl=base_response_jsonl,
        lean_timeout=5,
    )

    assert payload["all_ok"]
    assert payload["n_target_proof_state_feedback_rows"] == 3
    assert payload["n_skipped_non_target_proof_state_feedback_rows"] == 0
    assert payload["skipped_non_target_proof_state_feedback_rows"] == []
    assert payload["n_local_proof_state_responses"] == 3
    assert payload["n_merged_responses"] == 4
    assert payload["n_local_response_schema_valid"] == 3
    assert payload["n_local_response_schema_invalid"] == 0
    assert payload["n_merged_response_schema_valid"] == 4
    assert payload["n_merged_response_schema_invalid"] == 0
    assert (
        payload["refinement_tool_response_schema"]["$id"]
        == "urn:ai-statistician:schemas:formalization-gap-planner-refinement-tool-response:1"
    )
    assert payload["n_local_lean_failed"] == 1
    assert payload["n_target_prover_failed"] == 1
    assert payload["n_non_lean_skeleton"] == 1
    assert payload["n_non_target_prover_skeleton"] == 1
    assert payload["n_formal_gap_scaffold_blocked"] == 1
    assert payload["target_prover_family"] == "lean4"
    assert payload["by_prover_attempt_class"] == {
        "formal_gap_scaffold_blocked": 1,
        "non_target_prover_skeleton": 1,
        "target_prover_failed": 1,
    }
    by_item = {row["refinement_item_id"]: row for row in payload["responses"]}
    response = by_item["refinement:proof"]
    assert response["attempt_status"] == "local_lean_failed"
    assert response["prover_attempt_class"] == "target_prover_failed"
    assert response["target_prover_family"] == "lean4"
    assert response["route_revision_recommended"]
    assert response["residual_goals"]
    assert any("unsolved goals" in item for item in response["prover_diagnostics"])
    name_only = by_item["refinement:name_only"]
    assert name_only["attempt_status"] == "non_lean_skeleton"
    assert name_only["prover_attempt_class"] == "non_target_prover_skeleton"
    assert name_only["route_revision_recommended"]
    assert any("not a Lean command" in item for item in name_only["prover_diagnostics"])
    formal_gap = by_item["refinement:formal_gap"]
    assert formal_gap["attempt_status"] == "formal_gap_scaffold_blocked"
    assert formal_gap["prover_attempt_class"] == "formal_gap_scaffold_blocked"
    assert formal_gap["route_revision_recommended"]
    assert any("h_frontier_missing" in item for item in formal_gap["prover_diagnostics"])

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_contract_ok"] == 4
    assert evidence_payload["n_evidence_row_schema_valid"] == evidence_payload["n_evidence_rows"]
    assert evidence_payload["n_evidence_row_schema_invalid"] == 0
    assert evidence_payload["n_route_revision_proposals"] == 3
    assert evidence_payload["by_prover_attempt_status"] == {
        "formal_gap_scaffold_blocked": 1,
        "local_lean_failed": 1,
        "non_lean_skeleton": 1,
    }
    assert evidence_payload["by_prover_attempt_class"] == {
        "formal_gap_scaffold_blocked": 1,
        "non_target_prover_skeleton": 1,
        "target_prover_failed": 1,
    }
    evidence_schema = evidence_payload["refinement_evidence_row_schema"]
    assert "prover_attempt_class" in evidence_schema["required"]
    assert "target_prover_family" in evidence_schema["required"]
    evidence_by_item = {
        row["refinement_item_id"]: row for row in evidence_payload["rows"]
    }
    formal_gap_evidence = evidence_by_item["refinement:formal_gap"]
    assert (
        formal_gap_evidence["prover_attempt_status"]
        == "formal_gap_scaffold_blocked"
    )
    assert (
        formal_gap_evidence["prover_attempt_class"]
        == "formal_gap_scaffold_blocked"
    )
    assert formal_gap_evidence["target_prover_family"] == "lean4"
    assert formal_gap_evidence["prover_diagnostic_signature"]
    proposals_by_item = {
        row["refinement_item_id"]: row
        for row in evidence_payload["route_revision_proposals"]
    }
    assert (
        proposals_by_item["refinement:formal_gap"]["prover_attempt_status"]
        == "formal_gap_scaffold_blocked"
    )
    assert (
        proposals_by_item["refinement:formal_gap"]["prover_attempt_class"]
        == "formal_gap_scaffold_blocked"
    )
    assert (
        evidence_dir / "formalization_gap_planner_refinement_evidence_row.schema.json"
    ).exists()
    assert (
        adapter_dir / "formalization_gap_planner_refinement_tool_response.schema.json"
    ).exists()


def test_local_proof_state_adapter_skips_non_lean_targets() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_local_proof_state_adapter_non_lean"
    )
    queue_dir = root / "queue"
    adapter_dir = root / "adapter"
    evidence_dir = root / "evidence"
    base_response_jsonl = root / "base_responses.jsonl"
    shutil.rmtree(root, ignore_errors=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    display_name = "rocq rank route"
    queue_rows = [
        {
            "refinement_item_id": "refinement:rocq-proof",
            "goal_plan_id": "goal:rocq",
            "route_id": "route:rocq",
            "display_name": display_name,
            "hook_kind": "proof_state_feedback",
            "refinement_stage": "proof",
            "owner_agent": "proof",
            "target_prover_family": "rocq",
            "target_primitives": ["rank_uniformity"],
            "theorem_skeleton": "Theorem rank_uniformity : True.",
            "queries": ["probe rank uniformity in Rocq"],
        },
    ]
    (queue_dir / "formalization_gap_planner_refinement_queue_manifest.json").write_text(
        json.dumps({"rows": queue_rows}, indent=2),
        encoding="utf-8",
    )
    base_response_jsonl.write_text(
        json.dumps(
            {
                "refinement_item_id": "refinement:rocq-proof",
                "route_id": "route:rocq",
                "display_name": display_name,
                "evidence_kind": "prover_feedback",
                "tool_name": "target_prover_adapter_feedback_adapter",
                "target_prover_family": "rocq",
                "attempt_status": "needs_statement_translation",
                "prover_attempt_class": "target_prover_translation_gap",
                "prover_diagnostics": [
                    "Rocq adapter requires a translated statement before replay"
                ],
                "residual_goals": ["rank_uniformity: translate statement to Rocq"],
                "route_revision_recommended": True,
                "route_revision_reasons": ["translate statement to Rocq"],
                "proof_evidence_status": (
                    "FORMALIZATION_GAP_PLANNER_PROVER_ADAPTER_FEEDBACK_ADAPTER_NOT_PROOF_EVIDENCE"
                ),
                "proof_evidence_boundary": "not theorem proof evidence",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = export_formalization_gap_planner_local_proof_state_adapter_responses(
        queue_dir,
        adapter_dir,
        base_response_jsonl=base_response_jsonl,
    )

    assert payload["all_ok"]
    assert payload["n_proof_state_feedback_rows"] == 1
    assert payload["n_target_proof_state_feedback_rows"] == 0
    assert payload["n_skipped_non_target_proof_state_feedback_rows"] == 1
    assert payload["by_skipped_target_prover_family"] == {"rocq": 1}
    assert payload["n_local_proof_state_responses"] == 0
    assert payload["n_merged_responses"] == 1
    assert payload["n_local_response_schema_valid"] == 0
    assert payload["n_merged_response_schema_valid"] == 1
    assert payload["responses"] == []
    skipped = payload["skipped_non_target_proof_state_feedback_rows"][0]
    assert skipped["refinement_item_id"] == "refinement:rocq-proof"
    assert skipped["target_prover_family"] == "rocq"
    merged_response = json.loads(
        (
            adapter_dir
            / "formalization_gap_planner_refinement_evidence_responses.jsonl"
        ).read_text(encoding="utf-8")
    )
    assert merged_response["tool_name"] == "target_prover_adapter_feedback_adapter"
    assert merged_response["target_prover_family"] == "rocq"

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )

    assert evidence_payload["all_ok"]
    row = evidence_payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert row["prover_attempt_class"] == "target_prover_translation_gap"
    assert row["route_revision_recommended"]
