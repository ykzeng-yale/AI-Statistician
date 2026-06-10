from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai_statistician.formalization_gap_planner_contract import (
    LEGACY_FORMAL_REALIZATION_FIELD_ALIASES,
    validate_portable_gap_plan_payload,
)
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
    assert (
        payload["legacy_formal_realization_field_aliases"]
        == LEGACY_FORMAL_REALIZATION_FIELD_ALIASES
    )
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


def test_goal_conditioned_plan_reports_mixed_route_targets() -> None:
    root = Path("runs/test_formalization_gap_planner_goal_conditioned_mixed_targets")
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
                    {"primitive": "lean_reuse"},
                    {"primitive": "rocq_bridge"},
                ],
                "theorem_formalization_routes": [
                    {
                        "route_id": "route:lean",
                        "task_id": "task:lean",
                        "display_name": "Lean reuse target",
                        "theorem_skeleton": (
                            "theorem lean_reuse : True := by trivial"
                        ),
                        "theorem_statement": "Lean route can reuse True.intro.",
                        "target_prover_family": "lean4",
                        "route_class": "reuse_or_composition",
                        "total_estimated_cost": 1,
                        "actions": [
                            {
                                "primitive": "lean_reuse",
                                "action_id": "action:lean_reuse",
                                "action_class": "reuse_exact_proof_bank_obligation",
                                "total_cost": 1,
                                "candidate_declarations": ["True.intro"],
                            }
                        ],
                    },
                    {
                        "route_id": "route:rocq",
                        "task_id": "task:rocq",
                        "display_name": "Rocq bridge target",
                        "theorem_skeleton": (
                            "Theorem rocq_bridge : True. Proof. exact I. Qed."
                        ),
                        "theorem_statement": "Rocq route needs a bridge.",
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
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (queue_dir / "formal_verifier_queue_manifest.json").write_text(
        json.dumps(
            {
                "target_prover_family": "lean4",
                "rows": [
                    {
                        "route_id": "route:lean",
                        "target_prover_family": "lean4",
                        "import_cone_size": 0,
                        "dependency_graph_depth": 0,
                        "blocker_count": 0,
                        "source_trust_level": "local_candidate_declarations",
                        "recommended_action": "reuse Lean declaration",
                    },
                    {
                        "route_id": "route:rocq",
                        "target_prover_family": "rocq",
                        "import_cone_size": 0,
                        "dependency_graph_depth": 0,
                        "blocker_count": 0,
                        "source_trust_level": "local_candidate_declarations",
                        "recommended_action": "prove Rocq bridge",
                    },
                ],
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
    assert payload["target_prover_family"] == "mixed:lean4,rocq"
    assert payload["n_target_prover_families"] == 2
    assert payload["by_target_prover_family"] == {"lean4": 1, "rocq": 1}
    assert validate_portable_gap_plan_payload(payload) == []
    by_route = {row["route_id"]: row for row in payload["rows"]}
    assert by_route["route:lean"]["target_prover_family"] == "lean4"
    assert by_route["route:rocq"]["target_prover_family"] == "rocq"
