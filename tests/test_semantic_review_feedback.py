from __future__ import annotations

from ai_statistician.semantic_review_feedback import (
    architect_observations_without_runtime_routing,
    coding_agent_observations_only,
    model_observations_without_repair_recipes,
)


def test_recursive_projection_preserves_rejected_candidate_exactly() -> None:
    rejected_candidate = {
        "source": "def estimate(x):\n    return x\n",
        "required_change": "This is candidate data, not runtime guidance.",
    }
    projected = model_observations_without_repair_recipes(
        {
            "rejected_candidate": rejected_candidate,
            "findings": [
                {
                    "summary": "The result disagrees with the reference run.",
                    "required_change": "Replace the implementation.",
                    "evidence_refs": ["result#/estimate"],
                }
            ],
            "nested": {
                "repair_instructions": ["Edit line 2."],
                "compiler_feedback": "unknown identifier 'estimate'",
            },
        }
    )

    assert projected["rejected_candidate"] == rejected_candidate
    assert projected["findings"] == [
        {
            "summary": "The result disagrees with the reference run.",
            "evidence_refs": ["result#/estimate"],
        }
    ]
    assert projected["nested"] == {
        "compiler_feedback": "unknown identifier 'estimate'"
    }


def test_metric_author_receives_executable_semantic_control_observation() -> None:
    projected = model_observations_without_repair_recipes(
        {
            "requirement_reviews": [
                {
                    "requirement_id": "metric:realized_fraction",
                    "semantic_positive_control": {
                        "raw_comparison_value": 0.3,
                        "rationale": "The scientific target is an absolute fraction.",
                        "runtime_evaluation": {
                            "runtime_passed": False,
                            "aggregate_value": 0.3,
                            "errors": ["0.3 did not satisfy the frozen gate"],
                        },
                    },
                    "semantic_control_status": "CONTRADICTION",
                    "repair_instructions": ["Shift the gate by 0.3."],
                }
            ]
        }
    )

    review = projected["requirement_reviews"][0]
    assert review["semantic_positive_control"]["raw_comparison_value"] == 0.3
    assert review["semantic_positive_control"]["runtime_evaluation"] == {
        "runtime_passed": False,
        "aggregate_value": 0.3,
        "errors": ["0.3 did not satisfy the frozen gate"],
    }
    assert review["semantic_control_status"] == "CONTRADICTION"
    assert "repair_instructions" not in review


def test_recursive_projection_drops_runtime_repair_memory_and_recommendations() -> None:
    projected = model_observations_without_repair_recipes(
        {
            "candidate_source": "theorem target : True := by\n  trivial",
            "compiler_feedback": "Main.lean:2:3: error: unknown tactic",
            "candidate_source_hash": "sha256:candidate",
            "recommended_formalizer_target_mode": "replace_proof_body",
            "required_next_checks": ["prepend Mathlib import"],
            "source_theorem_exact_candidate_requires_repair": True,
            "source_theorem_exact_candidate_repair_diagnostics": [
                {"suggested_fix": "use exact runtime_selected_term"}
            ],
            "formalizer_lean_candidate_repair_memory": [
                {"preferred_tool_order": ["add_import", "splice_proof"]}
            ],
        }
    )

    assert projected == {
        "candidate_source": "theorem target : True := by\n  trivial",
        "compiler_feedback": "Main.lean:2:3: error: unknown tactic",
        "candidate_source_hash": "sha256:candidate",
    }


def test_projection_drops_runtime_authored_cli_recipes() -> None:
    projected = model_observations_without_repair_recipes(
        {
            "local_lean_stderr": "type mismatch at the exact target",
            "llm_route_planner_prompt_cli": "python -m hidden.route --fix target",
            "nested": {
                "reuse_smoke_cli": "python -m hidden.replay --repair target",
                "target_theorem_statement": "theorem target : True",
            },
        }
    )

    assert projected["local_lean_stderr"] == (
        "type mismatch at the exact target"
    )
    assert projected["nested"]["target_theorem_statement"] == (
        "theorem target : True"
    )
    assert "llm_route_planner_prompt_cli" not in projected
    assert "reuse_smoke_cli" not in projected["nested"]


def test_coding_agent_projection_keeps_observations_without_repair_routing() -> None:
    rejected_candidate = {
        "source": "def estimate(x):\n    return x\n",
    }
    projected = coding_agent_observations_only(
        {
            "rejected_candidate": rejected_candidate,
            "runtime_errors": ["TypeError: expected a string key"],
            "reviewed_source_artifacts": [
                {
                    "exact_source_code": "def estimate(x):\n    return x\n",
                    "exact_result": {"estimate": 2.0},
                }
            ],
            "findings": [
                {
                    "summary": "The result disagrees with the cited contract.",
                    "repair_scope": "source_code",
                    "required_change": "Negate the return value.",
                    "evidence_refs": ["result#/estimate"],
                }
            ],
            "repair_plan": [{"repair_owner": "AlgorithmEngineer"}],
            "source_repair_contract": {"repair_target_subsystem": "AlgorithmEngineer"},
            "recommended_repair_scope": "source_code",
            "semantic_reviewer_recommended_repair_scope": "source_code",
            "runtime_queue_status": "PENDING_SOURCE_REPAIR",
            "next_action": "Apply a canned patch.",
        }
    )

    assert projected["rejected_candidate"] == rejected_candidate
    assert projected["runtime_errors"] == ["TypeError: expected a string key"]
    assert projected["reviewed_source_artifacts"][0]["exact_source_code"].startswith(
        "def estimate"
    )
    assert projected["findings"] == [
        {
            "summary": "The result disagrees with the cited contract.",
            "evidence_refs": ["result#/estimate"],
        }
    ]
    serialized = str(projected)
    assert "Negate the return value" not in serialized
    assert "Apply a canned patch" not in serialized
    assert "repair_target_subsystem" not in serialized
    assert "repair_scope" not in serialized
    assert "repair_plan" not in serialized
    assert "runtime_queue_status" not in serialized
    assert "recommended_repair_scope" not in serialized
    assert "semantic_reviewer_recommended_repair_scope" not in serialized


def test_architect_projection_keeps_observations_without_runtime_route() -> None:
    projected = architect_observations_without_runtime_routing(
        {
            "runtime_errors": ["ValueError: metric payload is incomplete"],
            "findings": [
                {
                    "summary": "The generated statistic is not the requested one.",
                    "repair_scope": "source_code",
                    "required_change": "Replace the implementation.",
                }
            ],
            "repair_scope": "source_code",
            "recommended_repair_scope": "source_code",
            "semantic_reviewer_recommended_repair_scope": "source_code",
            "repair_owner_agent": "AlgorithmEngineer",
            "repair_target_subsystem": "AlgorithmEngineer",
            "repair_plan": [
                {
                    "repair_scope": "source_code",
                    "repair_owner": "AlgorithmEngineer",
                }
            ],
        }
    )

    assert projected["runtime_errors"] == [
        "ValueError: metric payload is incomplete"
    ]
    assert projected["findings"] == [
        {
            "summary": "The generated statistic is not the requested one.",
        }
    ]
    serialized = str(projected)
    assert "Replace the implementation" not in serialized
    assert "repair_owner" not in serialized
    assert "repair_scope" not in serialized
    assert "recommended_repair_scope" not in serialized
    assert "semantic_reviewer_recommended_repair_scope" not in serialized
    assert "repair_target_subsystem" not in serialized
    assert "repair_plan" not in serialized
