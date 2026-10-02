"""External outcome mechanisms, not mathematical qualification or live inference."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from benchmarks.publication import evaluate_final_artifacts as outcomes
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
from ai_statistician.research_schema import OpenResearchQuestion, research_question_payload
from ai_statistician.scientific_project import scientific_project_hash
from ai_statistician.scientific_sandbox import ScientificEstimatorBinding, discover_scientific_sandbox_runtime


def outcome_fixture(tmp_path, *, language="python", offset=0, intent=None):
    question = OpenResearchQuestion("opaque", "Opaque outcome", "Unresolved mechanism fixture, not scientific gold.",
        task_intent=intent if intent is not None else {
            "theory": "required", "scientific_code": "required", "empirical": "required", "formal": "optional"})
    public = research_question_payload(question, include_task_intent=True)
    identity = {"question_id": question.id, "question_hash": stable_hash(public), "task_intent": deepcopy(question.task_intent)}
    private = tmp_path / "external-authority"
    private.mkdir()

    def evaluator(label, code, *, language="python", path="echo", expected=99178):
        source = private / (label + (".R" if language == "r" else ".py"))
        source.write_text(code, encoding="utf-8")
        return {"language": language, "harness_path": str(source),
                "harness_sha256": hashlib.sha256(code.encode()).hexdigest(), "dependencies": [],
                "seed": 99173, "replicates": 5, "timeout_seconds": 30,
                "acceptance_checks": [{"check_id": "opaque-held-" + label, "path": [path], "operator": "eq", "expected": expected}]}

    harness = ("def run_sandbox(seed, replicates, estimators):\n"
               "    return estimators['opaque']({'value': seed + replicates})\n" if language == "python" else
               "run_sandbox <- function(seed, replicates, estimators) estimators[['opaque']](list(value=seed+replicates))\n")
    algorithm = evaluator("source", harness, language=language)
    algorithm["required_estimator_id"] = "opaque"
    empirical = evaluator("submitted-experiment", "def evaluate_artifact(candidate, seed, replicates):\n"
                          "    return {'echo': candidate['measurement']}\n")
    task = {"task_id": question.id, "task_intent": deepcopy(question.task_intent),
            "visible_question_hash": stable_hash(_visible_question_hash_payload(public)),
            "hidden_algorithm_evaluator": algorithm, "hidden_empirical_evaluator": empirical,
            "hidden_theory_semantic_evaluator": {"provider": "local"}}
    code = (f"def run_estimator(request):\n    return {{'echo': request['value'] + {offset}}}\n" if language == "python" else
            f"run_estimator <- function(request) list(echo=request$value+{offset})\n")
    binding = ScientificEstimatorBinding("opaque", language, code, stable_hash(code), project_hash=scientific_project_hash(
        language=language, code=code))
    text = "# Opaque claim\n\nUnresolved: the semantic outcome below is scripted, not mathematical truth.\n"
    docs = [{"path": "claim.md", "content": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}]
    return dict(question=question, task=task, submission_identity=identity, project_root=tmp_path,
                out_dir=tmp_path / "outcome", theory_documents=docs, estimator_bindings=(binding,),
                empirical_artifact={"measurement": 99178})


def scripted_semantics(monkeypatch, *, passed=True, mutate=None):
    calls = []

    def review(**kwargs):
        calls.append(deepcopy(kwargs))
        if mutate is not None:
            mutate(kwargs)
        judgment = {"passed": passed, "mechanism_fixture_not_scientific_authority": True}
        return {**judgment, "judgment_hash": stable_hash(judgment)}, ""

    monkeypatch.setattr(outcomes, "_run_hidden_document_semantic_evaluation", review)
    return calls


def require_runtime(language):
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available or (language == "r" and not runtime.r_available):
        pytest.skip("scientific runtime is not prepared")


@pytest.mark.parametrize("language", ["python", "r"])
@pytest.mark.parametrize("offset", [0, 1])
@pytest.mark.parametrize("theory_passed", [False, True])
def test_same_external_criteria_ignore_internal_disposition_but_keep_theory_separate(tmp_path, monkeypatch, language, offset, theory_passed):
    require_runtime(language)
    kwargs = outcome_fixture(tmp_path, language=language, offset=offset)
    kwargs["submission_identity"]["internal_status"] = "BLOCKED" if offset == 0 else "ACCEPTED"
    before = deepcopy(kwargs)
    calls = scripted_semantics(monkeypatch, passed=theory_passed)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    rows = result["dimension_status"]
    assert rows["scientific_code"]["status"] == ("passed" if offset == 0 else "failed")
    assert rows["scientific_code"]["execution"]["estimator_invocation_count"] == 1
    assert rows["theory"]["status"] == ("passed" if theory_passed else "failed")
    assert rows["empirical"]["status"] == "passed"
    assert rows["formal"]["status"] == "not_requested"
    assert result["task_passed"] is (theory_passed and offset == 0)
    assert result["internal_acceptance_required"] is False and result["runtime_feedback_generated"] is False
    assert len(calls) == 1 and calls[0]["candidate_documents"] == kwargs["theory_documents"]
    assert json.loads((kwargs["out_dir"] / "outcome.json").read_text()) == result
    saved = json.loads((kwargs["out_dir"] / "theory" / "semantic_judgment.json").read_text())
    assert saved["judgment_hash"] == rows["theory"]["semantic_judgment_hash"]
    assert kwargs == before
    with pytest.raises(FileExistsError):
        outcomes.evaluate_final_research_artifacts(**kwargs)
    assert len(calls) == 1


@pytest.mark.parametrize("missing", ["theory_documents", "estimator_bindings", "empirical_artifact", "source_replication_artifact"])
def test_missing_final_material_cannot_be_replaced_by_reference_or_another_lane(tmp_path, monkeypatch, missing):
    require_runtime("python")
    intent = {"theory": "required", "scientific_code": "required", "empirical": "required", "formal": "optional",
              "source_replication": "required"}
    kwargs = outcome_fixture(tmp_path, intent=intent)
    kwargs["task"]["hidden_source_replication_evaluator"] = deepcopy(kwargs["task"]["hidden_empirical_evaluator"])
    kwargs["source_replication_artifact"] = {"measurement": 99178}
    kwargs[missing] = () if missing in {"theory_documents", "estimator_bindings"} else None
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    dimension = {"theory_documents": "theory", "estimator_bindings": "scientific_code",
                 "empirical_artifact": "empirical", "source_replication_artifact": "source_replication"}[missing]
    assert result["dimension_status"][dimension]["status"] == "missing" and result["task_passed"] is False
    assert len(calls) == (0 if missing == "theory_documents" else 1)
    assert all(call["candidate_documents"] is not None for call in calls)


@pytest.mark.parametrize("change", ["question", "task", "intent", "code", "project", "duplicate_source", "document", "duplicate_document", "harness", "provider", "binary", "nonfinite"])
def test_invalid_identity_authority_or_artifact_view_fails_before_evaluation(tmp_path, monkeypatch, change):
    kwargs = outcome_fixture(tmp_path)
    if change == "question":
        kwargs["submission_identity"]["question_hash"] = "different"
    elif change == "task":
        kwargs["task"]["task_id"] = "different"
    elif change == "intent":
        kwargs["task"]["task_intent"]["formal"] = "required"
    elif change in {"code", "project"}:
        kwargs["estimator_bindings"] = (replace(kwargs["estimator_bindings"][0], **{change + "_hash": "different"}),)
    elif change == "duplicate_source":
        kwargs["estimator_bindings"] *= 2
    elif change == "document":
        kwargs["theory_documents"][0]["content"] = "different"
    elif change == "duplicate_document":
        kwargs["theory_documents"] *= 2
    elif change == "harness":
        kwargs["task"]["hidden_algorithm_evaluator"]["harness_sha256"] = "different"
    elif change == "provider":
        kwargs["task"]["hidden_theory_semantic_evaluator"]["provider"] = "anthropic"
    else:
        kwargs["empirical_artifact"] = {"measurement": b"\x00\xff" if change == "binary" else float("nan")}
    calls = scripted_semantics(monkeypatch)
    with pytest.raises(ValueError):
        outcomes.evaluate_final_research_artifacts(**kwargs)
    assert not calls and not kwargs["out_dir"].exists()


def test_structural_theory_check_alone_cannot_grant_mathematical_acceptance(tmp_path, monkeypatch):
    require_runtime("python")
    kwargs = outcome_fixture(tmp_path, intent={"theory": "required", "scientific_code": "not_applicable", "empirical": "not_applicable"})
    kwargs["task"].pop("hidden_theory_semantic_evaluator")
    kwargs["task"]["hidden_theory_evaluator"] = deepcopy(kwargs["task"]["hidden_empirical_evaluator"])
    source = kwargs["project_root"] / "structural.py"
    code = "def evaluate_artifact(candidate, seed, replicates):\n    return {'echo': len(candidate['documents'])}\n"
    source.write_text(code)
    kwargs["task"]["hidden_theory_evaluator"].update(harness_path=str(source),
        harness_sha256=hashlib.sha256(code.encode()).hexdigest(),
        acceptance_checks=[{"path": ["echo"], "operator": "eq", "expected": 1}])
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["dimension_status"]["theory"]["execution"]["passed"] is True
    assert result["dimension_status"]["theory"]["status"] == "unconfigured"
    assert result["task_passed"] is False and not calls


def test_invalid_semantic_authority_fails_without_calling_a_model(tmp_path):
    kwargs = outcome_fixture(tmp_path, intent={"theory": "required", "scientific_code": "not_applicable", "empirical": "not_applicable"})
    calls = []
    def forbidden(**kwargs):
        calls.append(kwargs)
        raise AssertionError("invalid authority must fail before invoking a judge")
    kwargs["run_theory_semantic_judge"] = forbidden
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["dimension_status"]["theory"]["status"] == "failed"
    assert result["dimension_status"]["theory"]["errors"]
    assert result["task_passed"] is False and not calls


@pytest.mark.parametrize("intent", [{}, {"theory": "optional"}, {"formal": "required"}, {"novelty": "required"}])
def test_no_required_success_or_boolean_formal_claim_cannot_pass(tmp_path, intent):
    kwargs = outcome_fixture(tmp_path, intent=intent)
    kwargs.update(theory_documents=(), estimator_bindings=(), empirical_artifact=None,
                  formal_artifacts={"all_ok": True, "kernel_verified": True})
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["task_passed"] is False
    if intent.get("formal") == "required":
        assert result["dimension_status"]["formal"]["status"] == "failed"
    if intent.get("novelty") == "required":
        assert result["dimension_status"]["novelty"]["status"] == "missing"


def test_frozen_inputs_survive_callback_mutation_and_later_harness_file_change(tmp_path, monkeypatch):
    require_runtime("python")
    kwargs = outcome_fixture(tmp_path)
    task_hash = stable_hash(kwargs["task"])
    question_hash = stable_hash(research_question_payload(kwargs["question"], include_task_intent=True))
    def mutate(review):
        kwargs["question"].task_intent["formal"] = "required"
        kwargs["task"]["hidden_algorithm_evaluator"]["acceptance_checks"][0]["expected"] = -1
        kwargs["theory_documents"][0]["content"] = "changed outside call"
        review["candidate_documents"][0]["content"] = "changed callback copy"
        review["visible_question"]["id"] = "different"
        Path(kwargs["task"]["hidden_algorithm_evaluator"]["harness_path"]).write_text("invalid later source")
    scripted_semantics(monkeypatch, mutate=mutate)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["task_passed"] is True and result["task_hash"] == task_hash and result["question_hash"] == question_hash
    assert result["dimension_status"]["formal"]["requirement"] == "optional"
    assert result["dimension_status"]["scientific_code"]["execution"]["checks_passed"] is True


@pytest.mark.parametrize("value", [99179, {}])
def test_passing_source_cannot_manufacture_or_correct_a_submitted_experiment(tmp_path, monkeypatch, value):
    require_runtime("python")
    kwargs = outcome_fixture(tmp_path)
    kwargs["empirical_artifact"] = {"measurement": value}
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["dimension_status"]["scientific_code"]["status"] == "passed"
    assert result["dimension_status"]["empirical"]["status"] == "failed"
    assert result["task_passed"] is False and len(calls) == 1
    assert kwargs["empirical_artifact"] == {"measurement": value}


def test_missing_required_method_does_not_substitute_an_available_estimator(tmp_path, monkeypatch):
    kwargs = outcome_fixture(tmp_path, intent={"scientific_code": "required"})
    kwargs.update(theory_documents=(), empirical_artifact=None)
    kwargs["estimator_bindings"] = (replace(kwargs["estimator_bindings"][0], artifact_id="other"),)
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["dimension_status"]["scientific_code"]["status"] == "missing"
    assert result["task_passed"] is False and not calls
