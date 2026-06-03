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
    assert payload["n_local_proof_state_responses"] == 1
    assert payload["n_merged_responses"] == 2
    assert payload["n_local_lean_failed"] == 1
    response = payload["responses"][0]
    assert response["attempt_status"] == "local_lean_failed"
    assert response["route_revision_recommended"]
    assert response["residual_goals"]
    assert any("unsolved goals" in item for item in response["prover_diagnostics"])

    evidence_payload = export_formalization_gap_planner_refinement_evidence(
        queue_dir,
        evidence_dir,
        response_jsonl=adapter_dir / "formalization_gap_planner_refinement_evidence_responses.jsonl",
    )
    assert evidence_payload["all_ok"]
    assert evidence_payload["n_contract_ok"] == 2
    assert evidence_payload["n_route_revision_proposals"] == 1
