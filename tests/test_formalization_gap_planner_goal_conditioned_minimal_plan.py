from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.goal_conditioned_minimal_formalization_plan import (
    export_goal_conditioned_minimal_formalization_plan,
)


def test_goal_conditioned_plan_preserves_route_target_prover_family() -> None:
    root = Path("runs/test_formalization_gap_planner_goal_conditioned_target")
    delta_dir = root / "delta"
    queue_dir = root / "queue"
    out_dir = root / "plan"
    shutil.rmtree(root, ignore_errors=True)
    delta_dir.mkdir(parents=True, exist_ok=True)
    queue_dir.mkdir(parents=True, exist_ok=True)
    (delta_dir / "formalization_delta_plan_manifest.json").write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "rows": [
                    {"primitive": "rocq_bridge"},
                    {"primitive": "not_selected"},
                ],
                "theorem_formalization_routes": [
                    {
                        "route_id": "route:rocq",
                        "task_id": "task:rocq",
                        "display_name": "Rocq bridge target",
                        "theorem_skeleton": (
                            "Theorem rocq_bridge : True. Proof. exact I. Qed."
                        ),
                        "theorem_statement": (
                            "Theorem rocq_bridge : True. Proof. exact I. Qed."
                        ),
                        "target_prover_family": "rocq",
                        "route_class": "bridge_or_wrapper",
                        "total_estimated_cost": 4,
                        "actions": [
                            {
                                "primitive": "rocq_bridge",
                                "action_id": "action:rocq_bridge",
                                "action_class": "design_bridge_lemma",
                                "total_cost": 4,
                                "candidate_declarations": ["Rocq.Init.Logic.I"],
                            }
                        ],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (queue_dir / "formal_verifier_queue_manifest.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "route_id": "route:rocq",
                        "target_prover_family": "rocq",
                        "import_cone_size": 0,
                        "dependency_graph_depth": 0,
                        "blocker_count": 0,
                        "source_trust_level": "local_candidate_declarations",
                        "recommended_action": "prove the Rocq bridge",
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = export_goal_conditioned_minimal_formalization_plan(
        delta_dir,
        queue_dir,
        out_dir,
    )

    assert payload["all_ok"]
    assert payload["target_prover_family"] == "rocq"
    assert payload["by_target_prover_family"] == {"rocq": 1}
    assert payload["n_formal_realization_dag_nodes"] > 0
    assert payload["n_formal_realization_dag_edges"] > 0
    assert payload["n_lean_realization_dag_nodes"] == 0
    assert payload["n_lean_realization_dag_edges"] == 0
    row = payload["rows"][0]
    assert row["target_prover_family"] == "rocq"
    assert row["formal_realization_dag_nodes"]
    assert row["formal_realization_dag_edges"]
    assert not row["lean_realization_dag_nodes"]
    assert not row["lean_realization_dag_edges"]
    assert row["lean_realization_dag"]["nodes"] == []
    assert row["lean_realization_dag"]["edges"] == []
    proof_hook = next(
        hook
        for hook in row["interactive_refinement_hooks"]
        if hook["hook_kind"] == "proof_state_feedback"
    )
    assert "Rocq/coq-lsp proof-state adapter" in proof_hook["recommended_tools"]
    assert "lean-lsp-mcp" not in proof_hook["recommended_tools"]
    assert row["next_work_packets"][0]["target_prover_family"] == "rocq"
    assert row["portable_work_packets"][0]["target_prover_family"] == "rocq"
    assert (
        "target_prover_family"
        in row["portable_work_packet_contract"]["required_fields"]
    )
