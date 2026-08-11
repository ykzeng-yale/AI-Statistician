from __future__ import annotations

from pathlib import Path

import ai_statistician.lean_kernel_promotion as promotion_module
from ai_statistician.fingerprint import stable_hash
from ai_statistician.lean_kernel_promotion import evaluate_lean_kernel_promotion


def _reviewed_artifacts(source_path: Path) -> tuple[dict, dict]:
    source_hash = stable_hash(source_path.read_text(encoding="utf-8"))
    materialization_id = "materialization:one"
    review_packet_id = "review:one"
    review_packet = {
        "artifact_kind": "FormalTargetSemanticReviewPacket",
        "packet_id": review_packet_id,
        "overall_verdict": "ACCEPT",
    }
    review_packet_hash = stable_hash(review_packet)
    execution_id = "review-execution:one"
    artifacts = {
        materialization_id: {
            "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
            "manifest_id": materialization_id,
            "question": {"id": "question:one"},
            "candidate_rows": [
                {
                    "candidate_id": "candidate:one",
                    "candidate_lean_declaration": "target",
                    "source_hash": source_hash,
                    "artifact_path": str(source_path),
                    "target_ids": ["theorem:one"],
                    "source_theorem_candidate_evidence_eligible": True,
                }
            ],
        },
        review_packet_id: review_packet,
        execution_id: {
            "artifact_kind": "RuntimeFormalTargetSemanticReviewExecutionManifest",
            "execution_id": execution_id,
            "candidate_materialization_id": materialization_id,
            "candidate_id": "candidate:one",
            "candidate_source_hash": source_hash,
            "review_packet_id": review_packet_id,
            "review_packet_hash": review_packet_hash,
            "semantic_review_accepted": True,
        },
    }
    feedback = {
        "overall_verdict": "ACCEPT",
        "candidate_materialization_id": materialization_id,
        "candidate_id": "candidate:one",
        "candidate_source_hash": source_hash,
        "semantic_review_execution_id": execution_id,
        "semantic_review_packet_id": review_packet_id,
        "semantic_review_packet_hash": review_packet_hash,
    }
    return artifacts, feedback


def test_kernel_promotion_requires_independent_acceptance(tmp_path: Path) -> None:
    assert (
        evaluate_lean_kernel_promotion(
            blackboard_artifacts={},
            environment_feedback={"overall_verdict": "REVISE"},
            lean_project=tmp_path,
            lean_timeout=5,
        )
        is None
    )


def test_kernel_promotion_reruns_unchanged_reviewed_source(
    tmp_path: Path, monkeypatch
) -> None:
    source_path = tmp_path / "Target.lean"
    source_path.write_text("theorem target : True := by exact True.intro\n")
    artifacts, feedback = _reviewed_artifacts(source_path)
    calls: list[dict] = []

    def probe(**kwargs):
        calls.append(kwargs)
        return {
            "local_lean_attempted": True,
            "local_lean_compiled": True,
            "local_lean_source_compiled": True,
            "candidate_identity_lean_verified": True,
            "candidate_axiom_audit_clean": True,
        }

    monkeypatch.setattr(promotion_module, "run_lean_candidate_identity_probe", probe)
    result = evaluate_lean_kernel_promotion(
        blackboard_artifacts=artifacts,
        environment_feedback=feedback,
        lean_project=tmp_path,
        lean_timeout=5,
    )

    assert result is not None
    assert result["source_theorem_kernel_verified"] is True
    assert result["runtime_edited_source"] is False
    assert result["runtime_selected_proof"] is False
    assert result["question_id"] == "question:one"
    assert result["local_lean_checked"] is True
    assert result["local_lean_compiled"] is True
    assert result["exact_source_hash_preserved"] is True
    assert result["independent_semantic_review_accepted"] is True
    assert calls == [
        {
            "artifact_path": source_path,
            "candidate_lean_declaration": "target",
            "lean_project": tmp_path,
            "lean_timeout": 5,
        }
    ]


def test_kernel_promotion_rejects_source_hash_drift_before_lean(
    tmp_path: Path, monkeypatch
) -> None:
    source_path = tmp_path / "Target.lean"
    source_path.write_text("theorem target : True := by exact True.intro\n")
    artifacts, feedback = _reviewed_artifacts(source_path)
    source_path.write_text("theorem target : False := by contradiction\n")
    monkeypatch.setattr(
        promotion_module,
        "run_lean_candidate_identity_probe",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("probe must not run")),
    )

    result = evaluate_lean_kernel_promotion(
        blackboard_artifacts=artifacts,
        environment_feedback=feedback,
        lean_project=tmp_path,
        lean_timeout=5,
    )

    assert result is not None
    assert result["source_theorem_kernel_verified"] is False
    assert "reviewed Lean source hash mismatch" in result["blockers"]


def test_kernel_promotion_rejects_review_lineage_mismatch(tmp_path: Path) -> None:
    source_path = tmp_path / "Target.lean"
    source_path.write_text("theorem target : True := by exact True.intro\n")
    artifacts, feedback = _reviewed_artifacts(source_path)
    artifacts["review-execution:one"]["candidate_id"] = "candidate:other"

    result = evaluate_lean_kernel_promotion(
        blackboard_artifacts=artifacts,
        environment_feedback=feedback,
        lean_project=tmp_path,
        lean_timeout=5,
    )

    assert result is not None
    assert result["source_theorem_kernel_verified"] is False
    assert "semantic review execution candidate_id mismatch" in result["blockers"]
