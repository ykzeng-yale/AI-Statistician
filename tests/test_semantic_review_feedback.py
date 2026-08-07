from __future__ import annotations

from ai_statistician.semantic_review_feedback import (
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
                "severity": "critical",
                "category": "metric_semantics",
                "summary": "The executed statistic has the wrong sign.",
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
            "severity": "critical",
            "category": "metric_semantics",
            "summary": "The executed statistic has the wrong sign.",
            "repair_scope": "source_code",
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
