"""Prospective final-artifact identity checks, without models or scientific credit."""

from copy import deepcopy
from dataclasses import replace

import pytest

from ai_statistician.agent_runtime import runtime_artifact_reference
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_evaluation import load_runtime_research_submission
from ai_statistician.research_gold_evaluation import _semantic_judgment_metrics
from ai_statistician.research_schema import OpenResearchQuestion, research_question_payload


def submission_fixture(status="ACCEPTED"):
    question = OpenResearchQuestion("opaque", "Opaque task", "Unresolved transport record.",
                                    task_intent={"theory": "required", "scientific_code": "required"})
    artifacts = {
        "theory": {"artifact_kind": "OpaqueTheory", "content": "unresolved"},
        "code": {"artifact_kind": "RuntimeAlgorithmSandboxManifest", "prototypes": []},
        "assessment": {"artifact_kind": "CriticEvaluatorProposalPacket", "packet_id": "assessment",
                       "canonical_evidence_view_hash": "opaque-view"},
    }
    refs = {scope: runtime_artifact_reference(artifact_id, artifacts[artifact_id])
            for scope, artifact_id in (("theory", "theory"), ("scientific_code", "code"), ("assessment", "assessment"))}
    artifacts["critic"] = {
        "artifact_kind": "RuntimeCriticEvaluatorManifest", "manifest_id": "critic",
        "question": research_question_payload(question, include_task_intent=True),
        "theory_packet_id": "theory", "algorithm_sandbox_manifest_id": "code",
        "llm_critic_evaluator_proposal_id": "assessment", "canonical_evidence_view_hash": "opaque-view",
        "submission_artifact_refs": refs,
    }
    result = {"status": status, "final_task_id": "final", "blackboard": {"artifacts": artifacts},
              "traces": [{"task": {"task_id": "final"}, "subsystem": "CriticEvaluator", "status": status,
                          "produced_artifact_ids": ["assessment", "critic"]}]}
    return question, result


@pytest.mark.parametrize("status", ["ACCEPTED", "BLOCKED", "FAILED"])
def test_final_artifacts_are_read_independently_of_internal_acceptance(status):
    question, result = submission_fixture(status)
    original = deepcopy(result)
    submission = load_runtime_research_submission(result, question=question)
    assert submission["internal_status"] == status
    assert submission["selected_artifacts"]["theory"]["content"] == "unresolved"
    assert submission["selected_artifacts"]["scientific_code"]["prototypes"] == []
    assert "empirical" not in submission["selected_artifacts"]
    assert "task_passed" not in submission and "report_markdown" not in submission
    submission["selected_artifacts"]["theory"]["content"] = "caller mutation"
    submission["selected_artifact_refs"]["theory"]["content_hash"] = "caller mutation"
    assert result == original


@pytest.mark.parametrize("change", ["source", "missing", "ref_id", "extra", "ref_missing", "assessment", "task", "foreign_question"])
def test_final_identity_mismatches_are_rejected_without_an_intermediate_fallback(change):
    question, result = submission_fixture()
    artifacts = result["blackboard"]["artifacts"]
    refs = artifacts["critic"]["submission_artifact_refs"]
    if change == "source":
        artifacts["theory"]["content"] = "different"
    elif change == "missing":
        artifacts.pop("theory")
    elif change == "ref_id":
        refs["theory"]["artifact_id"] = "code"
    elif change == "extra":
        refs["empirical"] = deepcopy(refs["scientific_code"])
    elif change == "ref_missing":
        refs.pop("theory")
    elif change == "assessment":
        artifacts["assessment"]["canonical_evidence_view_hash"] = "different"
        refs["assessment"] = runtime_artifact_reference("assessment", artifacts["assessment"])
    elif change == "foreign_question":
        artifacts["theory"]["question"] = {"id": "different"}
        refs["theory"] = runtime_artifact_reference("theory", artifacts["theory"])
    else:
        question = replace(question, task_intent={"theory": "optional"})
    with pytest.raises(ValueError):
        load_runtime_research_submission(result, question=question)


@pytest.mark.parametrize("ending", ["next_stage", "budget", "pending", "wrong_task", "missing_submission"])
def test_only_the_actual_terminal_submission_is_selected(ending):
    question, result = submission_fixture()
    if ending == "next_stage":
        result["traces"].append({"subsystem": "TheoryDeveloper", "status": "BLOCKED"})
    elif ending == "budget":
        result["status"] = "MAX_ITERATIONS_REACHED"
    elif ending == "pending":
        result["pending_task"] = {"task_id": "continue"}
    elif ending == "wrong_task":
        result["final_task_id"] = "different"
    else:
        result["traces"][-1]["produced_artifact_ids"] = []
    assert load_runtime_research_submission(result, question=question) == {}


def test_earlier_unselected_artifacts_and_verdicts_do_not_replace_a_partial_final_selection():
    question, result = submission_fixture("BLOCKED")
    artifacts = result["blackboard"]["artifacts"]
    artifacts["earlier-accepted-critic"] = deepcopy(artifacts["critic"])
    result["traces"].insert(0, {"subsystem": "CriticEvaluator", "status": "ACCEPTED",
                               "produced_artifact_ids": ["earlier-accepted-critic"]})
    artifacts["critic"]["algorithm_sandbox_manifest_id"] = ""
    artifacts["critic"]["submission_artifact_refs"].pop("scientific_code")
    submission = load_runtime_research_submission(result, question=question)
    assert set(submission["selected_artifacts"]) == {"theory", "assessment"}
    assert submission["internal_status"] == "BLOCKED"


def source_submission_fixture():
    question = OpenResearchQuestion("source-only", "Source-only", "Opaque replication observation.", task_intent={
        "source_replication": "required", "theory": "not_applicable", "scientific_code": "not_applicable",
        "empirical": "not_applicable", "formal": "not_applicable"})
    checkpoint = {"artifact_kind": "SourceReplicationCheckpoint", "checkpoint_id": "exact-source",
                  "question_id": question.id, "task_intent": question.task_intent, "opaque": "unresolved"}
    result = {"status": "BLOCKED", "final_task_id": "final", "blackboard": {"artifacts": {"exact-source": checkpoint}},
              "traces": [{"task": {"task_id": "final"}, "subsystem": "TheoryDeveloper", "status": "BLOCKED",
                          "produced_artifact_ids": ["exact-source"]}]}
    return question, result


def test_source_only_terminal_keeps_failed_selection_without_inventing_theory_or_review():
    question, result = source_submission_fixture()
    earlier = {**result["blackboard"]["artifacts"]["exact-source"], "checkpoint_id": "earlier-source", "opaque": "earlier"}
    result["blackboard"]["artifacts"]["earlier-source"] = earlier
    result["traces"].insert(0, {"subsystem": "TheoryDeveloper", "status": "ACCEPTED", "produced_artifact_ids": ["earlier-source"]})
    submission = load_runtime_research_submission(result, question=question)
    assert set(submission["selected_artifacts"]) == {"source_replication"}
    assert submission["selected_artifacts"]["source_replication"]["opaque"] == "unresolved"
    assert submission["internal_status"] == "BLOCKED"
    assert submission["selected_artifact_refs"]["source_replication"]["artifact_id"] == "exact-source"


@pytest.mark.parametrize("dimension", ["theory", "scientific_code", "empirical", "formal"])
def test_source_checkpoint_is_not_a_final_selection_for_required_research(dimension):
    question, result = source_submission_fixture()
    question = replace(question, task_intent={**question.task_intent, dimension: "required"})
    result["blackboard"]["artifacts"]["exact-source"]["task_intent"] = question.task_intent
    assert load_runtime_research_submission(result, question=question) == {}


@pytest.mark.parametrize("defect", ["pending", "next_task", "budget", "absent", "ambiguous", "wrong_id", "wrong_intent"])
def test_source_terminal_requires_the_exact_final_checkpoint(defect):
    question, result = source_submission_fixture()
    checkpoint = result["blackboard"]["artifacts"]["exact-source"]
    if defect == "pending":
        result["pending_task"] = {"task_id": "continue"}
    elif defect == "next_task":
        result["traces"][-1]["next_task_id"] = "continue"
    elif defect == "budget":
        result["status"] = "MAX_ITERATIONS_REACHED"
    elif defect == "absent":
        result["traces"][-1]["produced_artifact_ids"] = []
    elif defect == "ambiguous":
        result["blackboard"]["artifacts"]["second"] = {**checkpoint, "checkpoint_id": "second"}
        result["traces"][-1]["produced_artifact_ids"].append("second")
    elif defect == "wrong_id":
        checkpoint["checkpoint_id"] = "absent"
    else:
        checkpoint["task_intent"] = {"theory": "required"}
    if defect in {"ambiguous", "wrong_id", "wrong_intent"}:
        with pytest.raises(ValueError):
            load_runtime_research_submission(result, question=question)
    else:
        assert load_runtime_research_submission(result, question=question) == {}


def test_integrated_critic_selects_source_checkpoint_by_exact_reference():
    question, result = submission_fixture()
    artifacts = result["blackboard"]["artifacts"]
    checkpoint = {"artifact_kind": "SourceReplicationCheckpoint", "opaque": "exact source observation"}
    artifacts["source"] = checkpoint
    artifacts["critic"].update(source_replication_checkpoint_id="source")
    artifacts["critic"]["submission_artifact_refs"]["source_replication"] = runtime_artifact_reference("source", checkpoint)
    submission = load_runtime_research_submission(result, question=question)
    assert submission["selected_artifacts"]["source_replication"] == checkpoint
    artifacts["source"]["opaque"] = "changed"
    with pytest.raises(ValueError):
        load_runtime_research_submission(result, question=question)


def test_legacy_semantic_projection_preserves_field_types_and_copies_assessments():
    judgment = {"passed": True, "judgment_hash": "opaque", "semantic_judge_calibrated": 1,
                "n_claims": "2", "n_calibration_cases": None, "candidate_status": None,
                "candidate_claim_assessments": [{"opaque": "unchanged"}]}
    theory = _semantic_judgment_metrics(judgment, prefix="hidden_theory_semantic_")
    source = _semantic_judgment_metrics(judgment, prefix="hidden_source_report_semantic_")
    assert {key.removeprefix("hidden_theory_semantic_"): value for key, value in theory.items()} == {
        key.removeprefix("hidden_source_report_semantic_"): value for key, value in source.items()}
    assert theory["hidden_theory_semantic_passed"] is True
    assert theory["hidden_theory_semantic_judge_calibrated"] is False
    assert theory["hidden_theory_semantic_claim_count"] == 2
    assert theory["hidden_theory_semantic_calibration_case_count"] == 0
    assert theory["hidden_theory_semantic_candidate_status"] == ""
    theory["hidden_theory_semantic_claim_assessments"][0]["opaque"] = "changed"
    assert judgment["candidate_claim_assessments"] == [{"opaque": "unchanged"}]


def test_legacy_nonexecuted_semantic_defaults_do_not_invent_a_judgment_hash():
    evaluator = {"opaque": "frozen configuration"}
    default = _semantic_judgment_metrics({}, prefix="", executed=False, evaluator=evaluator)
    assert default == {
        "execution_attempted": False, "evaluation_configured": True, "evaluator_hash": stable_hash(evaluator),
        "judge_calibrated": False, "calibration_case_count": 0, "calibration_cases_correct": 0,
        "candidate_mode_negative_case_count": 0, "candidate_mode_negative_cases_correct": 0,
        "candidate_mode_negative_model_calls": 0, "candidate_mode_negative_controls_passed": False,
        "claim_count": 0, "candidate_status": "", "candidate_document_status": "",
        "candidate_integrated_context": False, "candidate_model_calls": 0, "claim_assessments": [], "passed": False,
    }
