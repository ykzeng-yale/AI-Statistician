from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import (
    _dimension_status,
    _full_task_gold_configured,
    evaluate_research_gold_benchmark,
    validate_research_gold_benchmark_manifest,
)


def _formal_only_task() -> dict[str, object]:
    return {
        "scoring_scope": "full_task",
        "task_intent": {
            "source_replication": "not_applicable",
            "theory": "not_applicable",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "required",
            "novelty": "not_applicable",
            "unresolved_gaps": "not_applicable",
        },
    }


def _formal_dimensions(*, kernel_closed: bool) -> dict[str, dict[str, object]]:
    return _dimension_status(
        _formal_only_task(),
        runtime_requirements={
            "exact_formal_target_kernel_closed": kernel_closed,
        },
        runtime_research_eval_complete=kernel_closed,
        hidden_theory_passed=False,
        hidden_algorithm_passed=False,
        hidden_empirical_passed=False,
        runtime_result_observed=True,
    )


def test_exact_target_kernel_closure_is_formal_gold_authority() -> None:
    dimensions = _formal_dimensions(kernel_closed=True)

    assert dimensions["formal"] == {
        "requirement": "required",
        "status": "passed",
        "gold_validated": True,
        "evidence_authority": (
            "operator_frozen_exact_target_plus_runtime_lean_kernel"
        ),
    }
    assert dimensions["overall_runtime_research_loop"]["status"] == "passed"
    assert _full_task_gold_configured(_formal_only_task()) is True


def test_formal_gold_fails_closed_without_kernel_closure() -> None:
    dimensions = _formal_dimensions(kernel_closed=False)

    assert dimensions["formal"]["status"] == "failed"
    assert dimensions["formal"]["gold_validated"] is False
    assert dimensions["overall_runtime_research_loop"]["status"] == "failed"


def test_novelty_still_requires_external_gold_authority() -> None:
    task = _formal_only_task()
    task_intent = dict(task["task_intent"])
    task_intent["novelty"] = "required"
    task["task_intent"] = task_intent

    assert _full_task_gold_configured(task) is False


def _runtime_formal_authority() -> tuple[dict[str, object], dict[str, object]]:
    source_prefix = "import Statlib.QMD\n\ntheorem exact_target : True := by\n"
    question = {
        "id": "formal-test",
        "formal_target_contract": {
            "schema_version": 1,
            "target_id": "exact_target",
            "declaration_name": "ExactBench.exact_target",
            "lean_source_prefix": source_prefix,
            "lean_source_prefix_sha256": hashlib.sha256(
                source_prefix.encode("utf-8")
            ).hexdigest(),
            "proof_visibility": "hidden",
            "lean_environment": {
                "project_id": "fixture",
                "lean_toolchain": "leanprover/lean4:v4.30.0",
                "lake_manifest_sha256": "fixture-manifest-hash",
            },
            "required_primitives": ["True.intro"],
        },
    }
    promotion_id = "lean_kernel_promotion:fixture"
    artifacts = {
        promotion_id: {
            "artifact_kind": "LeanKernelPromotionResult",
            "promotion_id": promotion_id,
            "question_id": "formal-test",
            "target_ids": ["exact_target"],
            "target_lean_declaration": "ExactBench.exact_target",
            "candidate_source_hash": "candidate-source-hash",
            "source_theorem_kernel_verified": True,
            "local_lean_checked": True,
            "local_lean_compiled": True,
            "candidate_identity_lean_verified": True,
            "candidate_axiom_audit_clean": True,
            "exact_source_hash_preserved": True,
            "independent_semantic_review_accepted": True,
            "runtime_edited_source": False,
            "runtime_selected_proof": False,
            "proof_evidence_status": "EXACT_MODEL_SOURCE_KERNEL_VERIFIED",
            "blockers": [],
        },
        "formalization_manifest:fixture": {
            "artifact_kind": "RuntimeFormalizationManifest",
            "question": question,
            "lean_kernel_promotion_id": promotion_id,
            "source_theorem_kernel_verified": True,
            "source_theorem_kernel_verified_target_ids": ["exact_target"],
            "source_theorem_kernel_verified_target_names": [
                "ExactBench.exact_target"
            ],
            "counts": {"source_theorem_kernel_verified": 1},
            "proof_evidence_status": "EXACT_SOURCE_THEOREM_KERNEL_VERIFIED",
        },
    }
    return question, artifacts


def _formal_gold_manifest(tmp_path: Path, *, include_contract: bool) -> Path:
    question, _ = _runtime_formal_authority()
    question.update(
        {
            "title": "Exact formal target",
            "description": "Prove the frozen declaration.",
            "tags": ["formal_L0"],
            "task_intent": _formal_only_task()["task_intent"],
        }
    )
    if not include_contract:
        question.pop("formal_target_contract")
    visible_path = tmp_path / "questions.json"
    visible_path.write_text(
        json.dumps({"questions": [question]}), encoding="utf-8"
    )
    visible_hash = hashlib.sha256(visible_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 4,
        "artifact_kind": "ResearchCapabilityGoldBenchmark",
        "benchmark_id": "formal-gold-fixture",
        "runtime_visibility": "evaluator_only_after_runtime",
        "gold_is_accessible_to_runtime_rag": False,
        "gold_is_accessible_to_model_workspace": False,
        "gold_execution_may_generate_runtime_feedback": False,
        "model_visible_questions_path": str(visible_path),
        "model_visible_questions_sha256": visible_hash,
        "model_policy": {
            "provider": "anthropic",
            "model_tier": "haiku",
            "model": "claude-haiku-4-5-20251001",
            "automatic_tier_escalation_allowed": False,
        },
        "active_tasks": [
            {
                "task_id": "formal-test",
                "level": "L0",
                "status": "active_scored",
                "scoring_scope": "full_task",
                "visible_question_hash": stable_hash(question),
                "task_intent": _formal_only_task()["task_intent"],
            }
        ],
        "proof_evidence_status": "EXACT_TARGET_CONTRACT_REQUIRES_KERNEL",
        "boundary": "Fixture authority remains outside runtime.",
    }
    manifest_path = tmp_path / "gold.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_formal_full_task_manifest_uses_exact_target_as_gold_authority(
    tmp_path: Path,
) -> None:
    descriptor = validate_research_gold_benchmark_manifest(
        _formal_gold_manifest(tmp_path, include_contract=True)
    )

    assert descriptor["n_full_task_gold_configured"] == 1


def test_formal_required_manifest_rejects_missing_exact_target(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="formal_target_contract is required"):
        validate_research_gold_benchmark_manifest(
            _formal_gold_manifest(tmp_path, include_contract=False)
        )


def test_formal_full_task_scores_exact_kernel_promotion(
    tmp_path: Path,
) -> None:
    manifest_path = _formal_gold_manifest(tmp_path, include_contract=True)
    question, artifacts = _runtime_formal_authority()
    question.update(
        {
            "title": "Exact formal target",
            "description": "Prove the frozen declaration.",
            "tags": ["formal_L0"],
            "task_intent": _formal_only_task()["task_intent"],
        }
    )
    artifacts["runtime_question_metadata:formal-test"] = {
        "artifact_kind": "RuntimeQuestionMetadata",
        "question": question,
    }
    result = evaluate_research_gold_benchmark(
        [{"status": "ACCEPTED", "blackboard": {"artifacts": artifacts}}],
        research_evaluation_summary={
            "rows": [
                {
                    "question_id": "formal-test",
                    "research_eval_complete": True,
                    "requirements": {
                        "exact_formal_target_kernel_closed": True,
                    },
                }
            ]
        },
        benchmark_manifest_path=manifest_path,
        out_dir=tmp_path / "out",
    )

    assert result["n_tasks_evaluated"] == 1
    assert result["n_tasks_passed"] == 1
    assert result["all_active_tasks_passed"] is True
    task = result["tasks"][0]
    assert task["proof_evidence_status"] == "GOLD_EVALUATION_NOT_PROOF_EVIDENCE"
    assert task["dimension_status"]["formal"]["status"] == "passed"
