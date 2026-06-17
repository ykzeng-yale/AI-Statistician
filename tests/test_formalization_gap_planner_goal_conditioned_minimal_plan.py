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


def test_goal_conditioned_plan_honors_explicit_selected_primitives() -> None:
    root = Path("runs/test_formalization_gap_planner_goal_conditioned_selected_subset")
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
                    {"primitive": "selected_bridge"},
                    {"primitive": "comparison_boundary"},
                ],
                "theorem_formalization_routes": [
                    {
                        "route_id": "route:selected_subset",
                        "task_id": "task:selected_subset",
                        "display_name": "Selected subset route",
                        "theorem_skeleton": "theorem selected_subset : True := by trivial",
                        "theorem_statement": "Selected subset route can reuse True.intro.",
                        "target_prover_family": "lean4",
                        "route_class": "bridge_or_wrapper",
                        "total_estimated_cost": 4,
                        "selected_primitives": ["selected_bridge"],
                        "minimal_delta_and_or_cost_graph": {
                            "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                            "selected_route_option_id": "route_option:selected",
                            "route_options": [
                                {
                                    "route_option_id": "route_option:selected",
                                    "selected": True,
                                    "selected_primitives": ["selected_bridge"],
                                    "route_cost": 4,
                                },
                                {
                                    "route_option_id": "route_option:comparison",
                                    "selected": False,
                                    "selected_primitives": [
                                        "selected_bridge",
                                        "comparison_boundary",
                                    ],
                                    "route_cost": 24,
                                },
                            ],
                            "and_edges": [
                                {
                                    "route_option_id": "route_option:selected",
                                    "requires": ["selected_bridge"],
                                },
                                {
                                    "route_option_id": "route_option:comparison",
                                    "requires": [
                                        "selected_bridge",
                                        "comparison_boundary",
                                    ],
                                },
                            ],
                            "or_nodes": [
                                {
                                    "node_id": "or:selected_subset",
                                    "choices": [
                                        "route_option:selected",
                                        "route_option:comparison",
                                    ],
                                }
                            ],
                        },
                        "actions": [
                            {
                                "primitive": "selected_bridge",
                                "action_id": "action:selected_bridge",
                                "action_class": "design_bridge_lemma",
                                "total_cost": 4,
                                "candidate_declarations": ["True.intro"],
                            },
                            {
                                "primitive": "comparison_boundary",
                                "action_id": "action:comparison_boundary",
                                "action_class": "design_from_first_principles",
                                "total_cost": 20,
                            },
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
                "target_prover_family": "lean4",
                "rows": [
                    {
                        "route_id": "route:selected_subset",
                        "target_prover_family": "lean4",
                        "import_cone_size": 0,
                        "dependency_graph_depth": 0,
                        "blocker_count": 0,
                        "source_trust_level": "local_candidate_declarations",
                        "recommended_action": "prove selected bridge",
                    }
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
    row = payload["rows"][0]
    assert row["selected_primitives"] == ("selected_bridge",)
    assert [node["primitive"] for node in row["minimal_additional_formalization_nodes"]] == [
        "selected_bridge"
    ]
    assert "comparison_boundary" in row["do_not_formalize_now"]
    assert row["route_option_cost_graph"]["selected_route_option_id"] == (
        "route_option:selected"
    )
    assert row["route_option_cost_graph_summary"]["n_route_options"] == 2
    assert row["route_option_cost_graph_summary"]["unselected_route_option_ids"] == [
        "route_option:comparison"
    ]
    assert row["route_option_cost_graph_summary"]["comparison_only_primitives"] == [
        "comparison_boundary"
    ]
    assert payload["n_route_option_cost_graph_route_options"] == 2
    assert payload["n_route_option_cost_graph_unselected_route_options"] == 1
    assert payload["n_route_option_cost_graph_comparison_only_primitives"] == 1


def test_goal_conditioned_plan_rejects_nonminimal_upstream_cost_graph() -> None:
    root = Path(
        "runs/test_formalization_gap_planner_goal_conditioned_nonminimal_graph"
    )
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
                "rows": [{"primitive": "selected_bridge"}],
                "theorem_formalization_routes": [
                    {
                        "route_id": "route:nonminimal_graph",
                        "task_id": "task:nonminimal_graph",
                        "display_name": "Nonminimal graph route",
                        "theorem_skeleton": (
                            "theorem selected_bridge : True := by trivial"
                        ),
                        "theorem_statement": "Selected bridge route.",
                        "target_prover_family": "lean4",
                        "route_class": "bridge_or_wrapper",
                        "total_estimated_cost": 10,
                        "selected_primitives": ["selected_bridge"],
                        "minimal_delta_and_or_cost_graph": {
                            "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                            "selected_route_option_id": "route_option:expensive",
                            "route_options": [
                                {
                                    "route_option_id": "route_option:expensive",
                                    "selected": True,
                                    "selected_primitives": ["selected_bridge"],
                                    "route_cost": 10,
                                    "cost_rationale": "incorrect expensive choice",
                                },
                                {
                                    "route_option_id": "route_option:cheap",
                                    "selected": False,
                                    "selected_primitives": ["selected_bridge"],
                                    "route_cost": 3,
                                    "cost_rationale": "cheaper listed route",
                                },
                            ],
                            "and_edges": [
                                {
                                    "route_option_id": "route_option:expensive",
                                    "requires": ["selected_bridge"],
                                },
                                {
                                    "route_option_id": "route_option:cheap",
                                    "requires": ["selected_bridge"],
                                },
                            ],
                            "or_nodes": [
                                {
                                    "node_id": "or:nonminimal_graph",
                                    "choices": [
                                        "route_option:expensive",
                                        "route_option:cheap",
                                    ],
                                }
                            ],
                        },
                        "actions": [
                            {
                                "primitive": "selected_bridge",
                                "action_id": "action:selected_bridge",
                                "action_class": "design_bridge_lemma",
                                "total_cost": 10,
                                "candidate_declarations": ["True.intro"],
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
                "target_prover_family": "lean4",
                "rows": [
                    {
                        "route_id": "route:nonminimal_graph",
                        "target_prover_family": "lean4",
                        "import_cone_size": 0,
                        "dependency_graph_depth": 0,
                        "blocker_count": 0,
                        "source_trust_level": "local_candidate_declarations",
                        "recommended_action": "prove selected bridge",
                    }
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

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["ok"] is False
    assert any(
        "selected route option is not minimal" in error
        for error in row["errors"]
    )
    summary = row["route_option_cost_graph_summary"]
    assert summary["cost_graph_ok"] is False
    assert any(
        "selected route option is not minimal" in error
        for error in summary["cost_graph_errors"]
    )


def test_goal_conditioned_plan_rejects_flat_upstream_cost_graph() -> None:
    root = Path("runs/test_formalization_gap_planner_goal_conditioned_flat_graph")
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
                "rows": [{"primitive": "selected_bridge"}],
                "theorem_formalization_routes": [
                    {
                        "route_id": "route:flat_graph",
                        "task_id": "task:flat_graph",
                        "display_name": "Flat graph route",
                        "theorem_skeleton": (
                            "theorem selected_bridge : True := by trivial"
                        ),
                        "theorem_statement": "Selected bridge route.",
                        "target_prover_family": "lean4",
                        "route_class": "bridge_or_wrapper",
                        "total_estimated_cost": 4,
                        "selected_primitives": ["selected_bridge"],
                        "minimal_delta_and_or_cost_graph": {
                            "graph_kind": "AND_OR_ROUTE_COST_GRAPH",
                            "selected_route_option_id": "route_option:selected",
                            "route_options": [
                                {
                                    "route_option_id": "route_option:selected",
                                    "selected": True,
                                    "selected_primitives": ["selected_bridge"],
                                    "route_cost": 4,
                                    "cost_rationale": "selected bridge route",
                                }
                            ],
                        },
                        "actions": [
                            {
                                "primitive": "selected_bridge",
                                "action_id": "action:selected_bridge",
                                "action_class": "design_bridge_lemma",
                                "total_cost": 4,
                                "candidate_declarations": ["True.intro"],
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
                "target_prover_family": "lean4",
                "rows": [
                    {
                        "route_id": "route:flat_graph",
                        "target_prover_family": "lean4",
                        "import_cone_size": 0,
                        "dependency_graph_depth": 0,
                        "blocker_count": 0,
                        "source_trust_level": "local_candidate_declarations",
                        "recommended_action": "prove selected bridge",
                    }
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

    assert not payload["all_ok"]
    row = payload["rows"][0]
    assert row["ok"] is False
    assert "route_option_cost_graph.or_nodes must be non-empty" in row["errors"]
    assert "route_option_cost_graph.and_edges must be non-empty" in row["errors"]
    summary = row["route_option_cost_graph_summary"]
    assert summary["cost_graph_ok"] is False
    assert "route_option_cost_graph.or_nodes must be non-empty" in summary[
        "cost_graph_errors"
    ]
    assert "route_option_cost_graph.and_edges must be non-empty" in summary[
        "cost_graph_errors"
    ]


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
