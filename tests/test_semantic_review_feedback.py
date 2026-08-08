from __future__ import annotations

from ai_statistician.semantic_review_feedback import (
    architect_observations_without_runtime_routing,
    coding_agent_observations_only,
    compact_semantic_review_feedback,
    model_observations_without_repair_recipes,
)


def test_author_feedback_keeps_evidence_but_drops_repair_recipe() -> None:
    feedback = {
        "feedback_type": "generated_code_semantic_review_feedback",
        "feedback_source": "GeneratedCodeSemanticReviewer",
        "candidate_id": "candidate:1",
        "candidate_source_hash": "sha256:source",
        "overall_verdict": "REVISE",
        "repair_owner_agent": "AlgorithmEngineer",
        "repair_target_subsystem": "AlgorithmEngineer",
        "findings": [
            {
                "finding_id": "finding:wrong-sign",
                "severity": "critical",
                "category": "metric_semantics",
                "summary": "The executed statistic has the wrong sign.",
                "observed_behavior": "The execution returned 2.0.",
                "expected_behavior": "The declared statistic returns -2.0.",
                "required_change": "Negate the statistic on line 12.",
                "repair_scope": "source_code",
                "evidence_refs": ["result#/observed_statistic"],
            }
        ],
        "repair_instructions": ["Replace x with -x on line 12."],
        "reviewed_source_artifacts": [
            {
                "artifact_id": "generated_source:1",
                "exact_source_hash": "sha256:source",
                "exact_source_code": "def estimate(x):\n    return x\n",
                "exact_source_code_complete": True,
                "exact_result": {"observed_statistic": 2.0},
                "exact_result_hash": "sha256:result",
            }
        ],
    }

    projected = compact_semantic_review_feedback(
        feedback,
        expected_feedback_type="generated_code_semantic_review_feedback",
    )

    assert projected["candidate_source_hash"] == "sha256:source"
    assert projected["findings"] == [
        {
            "finding_id": "finding:wrong-sign",
            "severity": "critical",
            "category": "metric_semantics",
            "summary": "The executed statistic has the wrong sign.",
            "observed_behavior": "The execution returned 2.0.",
            "expected_behavior": "The declared statistic returns -2.0.",
            "evidence_refs": ["result#/observed_statistic"],
        }
    ]
    assert projected["reviewed_source_artifacts"][0][
        "exact_source_code"
    ] == "def estimate(x):\n    return x\n"
    assert "required_change" not in str(projected)
    assert "repair_instructions" not in str(projected)


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
    assert "repair_target_subsystem" not in serialized
    assert "repair_plan" not in serialized
