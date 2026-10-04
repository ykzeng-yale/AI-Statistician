"""External outcome mechanisms, not mathematical qualification or live inference."""

from copy import deepcopy
from dataclasses import replace
import base64
import hashlib
import json
import os
from pathlib import Path

import pytest

from benchmarks.publication import evaluate_final_artifacts as outcomes
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
from ai_statistician.research_schema import OpenResearchQuestion, research_question_payload
from ai_statistician.scientific_project import scientific_project_hash
from ai_statistician.scientific_sandbox import ScientificEstimatorBinding, discover_scientific_sandbox_runtime
from ai_statistician.theory_workspace import theory_workspace_document_manifest
from ai_statistician.research_control import collect_native_research_submission, load_native_research_submission


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


def external_review_fixture(kwargs, *, verdict="accepted"):
    """Opaque record transport only: no expert or mathematical acceptance exists."""

    def reference(name, text):
        path = kwargs["project_root"] / name
        path.write_bytes(text.encode("utf-8"))
        return {"path": str(path), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "byte_size": len(text.encode("utf-8"))}

    kwargs["task"].pop("hidden_theory_semantic_evaluator")
    kwargs["task"]["external_theory_authority"] = {
        "authority_id": "opaque-mechanism-authority-not-an-expert",
        "protocol": reference("protocol.md", "# Unqualified opaque protocol\nNot mathematical gold.\n"),
    }
    kwargs["external_theory_review"] = {
        "authority_id": kwargs["task"]["external_theory_authority"]["authority_id"],
        "task_hash": stable_hash(kwargs["task"]),
        "submission_identity_hash": stable_hash(kwargs["submission_identity"]),
        "submitted_material_hash": outcomes.publication_submitted_material_hash(**{
            key: kwargs.get(key) for key in ("theory_documents", "estimator_bindings", "empirical_artifact",
                                           "source_replication_artifact", "formal_artifacts")}),
        "verdict": verdict,
        "report": reference("review.tex", "% Opaque transport fixture, not a proof.\r\nNo scientific verdict.\r\n"),
    }


def require_runtime(language):
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available or (language == "r" and not runtime.r_available):
        pytest.skip("scientific runtime is not prepared")


@pytest.mark.parametrize("dimension", ["empirical", "source_replication"])
@pytest.mark.parametrize("defect", ["none", "corrupt", "missing", "wrong_expectation"])
def test_common_r_artifact_evaluator_reads_exact_rds_without_python_conversion(tmp_path, monkeypatch, dimension, defect):
    config = os.environ.get("AI_STATISTICIAN_TEST_NATIVE_R_CONFIG", "")
    if not config:
        pytest.skip("explicit native R artifact environment is not configured")
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_R_CONFIG", config)
    profile = "scientific_native_r"
    intent = {name: "required" if name == dimension else "not_applicable" for name in (
        "theory", "scientific_code", "empirical", "source_replication", "formal")}
    kwargs = outcome_fixture(tmp_path, intent=intent)
    # Fresh opaque R 4.4.2/version-2 compressed serialization, not an author result.
    rds = (
        "H4sIAAAAAAAAA21RwU6EMBAtLCzuRg3ZvXjwYIw/sFy88hneTIUuaVJahC6uXtxv8Uv8JI+e"
        "xCntIBAnKTPDvJk3fX1YE0J8EgQ+8Rcm3MJnCSe2/8kKfKQq+nxgyTTdQXhpUOk96e1zQ5z5"
        "5n+QXtssvXH+1vk7xAErIZ4bu8h5Ce6iJx7OBHIGEElL1kC8dZjxokGtXpJRvJvXMyWSUWzq"
        "P8CMnN4/nEvBWiaa2STvDQM6w4eZoA3ChyF7mmlVW7pBY6OS9/5llIg+3NW9k5XG1r5RqTG2"
        "t9itu+rAwK//eqfroF5xT4raMCrwNbnUrGA1voKk0oXnlWq45i175HKPnZodNXYKVfAMBvW3"
        "IlemuyMnu0DYzThDQZ8Yki5bKg6wlstKqmt+HARU+VCKSt40XBaYVvRVKJobyl/g2P5XuwIA"
        "AA=="
    )
    raw = b"not an RDS object" if defect == "corrupt" else base64.b64decode(rds, validate=True)
    candidate = {"files": {"selected.rds": {"base64": base64.b64encode(raw).decode(),
        "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}},
        "missing_files": ["declared-but-absent.rds"], "report": "Unresolved opaque fixture.\r\n"}
    if defect == "missing":
        candidate["files"] = {}
    kwargs[dimension + "_artifact"] = candidate
    code = (
        "evaluate_artifact <- function(candidate, seed, replicates) {\n"
        "    if (is.null(candidate$files[['selected.rds']])) stop('opaque selected file absent')\n"
        "    p <- tempfile(fileext='.rds')\n"
        "    on.exit(unlink(p))\n"
        "    writeBin(jsonlite::base64_dec(candidate$files[['selected.rds']]$base64), p)\n"
        "    x <- readRDS(p)\n"
        "    list(echo=x$values[[1]], types=\n"
        "        identical(x$label, c('opaque2','opaque1')) &&\n"
        "        identical(x$matrix, matrix(c(7,8,9,10), nrow=2,\n"
        "            dimnames=list(c('row2','row1'), c('col2','col1')))) &&\n"
        "        identical(x$codes, factor(c('z','a'),levels=c('z','a'))) &&\n"
        "        identical(x$missing$real, NA_real_) &&\n"
        "        identical(x$missing$integer, NA_integer_) &&\n"
        "        is.nan(x$missing$nan) && identical(x$missing$positive_inf, Inf) &&\n"
        "        identical(x$missing$text, NA_character_) && identical(x$missing$logical, NA) &&\n"
        "        identical(x$payload, as.raw(c(255,0,128))),\n"
        "        context=identical(candidate$missing_files, list('declared-but-absent.rds')) &&\n"
        "            identical(candidate$report, 'Unresolved opaque fixture.\\r\\n') &&\n"
        "            seed==99173 && replicates==5)\n"
        "}\n"
    )
    harness = tmp_path / "external-authority" / "opaque-reader.R"
    harness.write_text(code)
    kwargs["task"]["hidden_" + dimension + "_evaluator"] = {
        "language": "r", "harness_path": str(harness),
        "harness_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "dependencies": ["jsonlite"], "execution_profile": profile,
        "seed": 99173, "replicates": 5, "timeout_seconds": 30,
        "acceptance_checks": [{"path": ["echo"], "operator": "eq", "expected": 24 if defect == "wrong_expectation" else 23},
            {"path": ["types"], "operator": "eq", "expected": True},
            {"path": ["context"], "operator": "eq", "expected": True}],
    }
    before = deepcopy(kwargs)
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    row = result["dimension_status"][dimension]
    assert row["status"] == ("passed" if defect == "none" else "failed")
    assert result["task_passed"] is (defect == "none") and not calls
    assert kwargs == before
    execution = row["execution"]
    assert execution["execution_profile"] == profile
    assert execution["backend"] == "native_r"
    request = json.loads(Path(execution["request_path"]).read_text())
    assert request["language"] == "r" and request["execution_profile"] == profile
    if defect in {"corrupt", "missing"}:
        assert execution["execution_passed"] is False
    elif defect == "wrong_expectation":
        assert execution["execution_passed"] is True and execution["checks_passed"] is False


def test_r_artifact_evaluator_without_jsonlite_does_not_fall_back_to_native(tmp_path, monkeypatch):
    kwargs = outcome_fixture(tmp_path, intent={"empirical": "required", "theory": "not_applicable",
        "scientific_code": "not_applicable", "formal": "not_applicable"})
    kwargs["task"]["hidden_empirical_evaluator"].update(language="r", dependencies=["jsonlite"])
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    execution = result["dimension_status"]["empirical"]["execution"]
    assert execution["execution_attempted"] is False
    assert execution["execution_profile"] == "scientific_wasm" and execution["backend"] == "webr"
    assert "generated code declares unsupported dependencies: jsonlite" in execution["errors"]
    assert result["task_passed"] is False and not calls


def test_r_artifact_evaluator_rejects_mismatched_profile_before_assessment(tmp_path, monkeypatch):
    kwargs = outcome_fixture(tmp_path, intent={"empirical": "required"})
    kwargs["task"]["hidden_empirical_evaluator"].update(language="r", execution_profile="scientific_native_python")
    calls = scripted_semantics(monkeypatch)
    with pytest.raises(ValueError, match="execution profile is invalid"):
        outcomes.evaluate_final_research_artifacts(**kwargs)
    assert not calls and not kwargs["out_dir"].exists()


@pytest.mark.parametrize("language", ["python", "r"])
@pytest.mark.parametrize("profile", ["scientific_wasm", "native"])
@pytest.mark.parametrize("defect", ["none", "source", "empirical"])
def test_collected_native_files_reach_common_final_outcome_without_author_receipts(tmp_path, monkeypatch, language, profile, defect):
    from test_native_research_submission import native_fixture

    if profile == "native":
        config = os.environ.get("AI_STATISTICIAN_TEST_NATIVE_" + language.upper() + "_CONFIG", "")
        python_config = os.environ.get("AI_STATISTICIAN_TEST_NATIVE_PYTHON_CONFIG", "")
        if not config or not python_config:
            pytest.skip("explicit native numerical and artifact environments are not configured")
        monkeypatch.setenv("AI_STATISTICIAN_NATIVE_" + language.upper() + "_CONFIG", config)
        monkeypatch.setenv("AI_STATISTICIAN_NATIVE_PYTHON_CONFIG", python_config)
    else:
        require_runtime(language)
    kwargs = outcome_fixture(tmp_path, language=language, intent={"scientific_code": "required", "empirical": "required",
        "theory": "not_applicable", "formal": "not_applicable"})
    author = tmp_path / "native"
    author.mkdir()
    root, store, _, paths, process, _ = native_fixture(author, language=language, offset=3 if defect == "source" else 0)
    measurement = root / "experiments" / "measurement.txt"
    measurement.write_bytes(str(99175 if defect == "empirical" else 99178).encode())
    paths["empirical"].append("experiments/measurement.txt")
    question = kwargs["question"]
    ref = collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
                                             host_result=process, snapshot_dir=store)
    native = load_native_research_submission(ref, question=question, artifact_paths=paths, snapshot_dir=store)
    material = outcomes.publication_material_from_submission(native, source_kind="native",
        native_estimator_projects={"opaque": {"root": "code", "language": language}})
    source = kwargs["task"]["hidden_empirical_evaluator"]["harness_path"]
    harness = ("import base64\n"
               "def evaluate_artifact(candidate, seed, replicates):\n"
               "    raw = base64.b64decode(candidate['files']['experiments/measurement.txt']['base64'], validate=True)\n"
               "    return {'echo': int(raw)}\n")
    Path(source).write_text(harness)
    kwargs["task"]["hidden_empirical_evaluator"]["harness_sha256"] = hashlib.sha256(harness.encode()).hexdigest()
    if profile == "native":
        kwargs["task"]["hidden_algorithm_evaluator"]["execution_profile"] = "scientific_native_" + language
        kwargs["task"]["hidden_empirical_evaluator"]["execution_profile"] = "scientific_native_python"
    kwargs.update(material)
    kwargs["submission_identity"] = {key: value for key, value in native.items() if key != "artifact_bytes"}
    before = deepcopy(native)
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["task_passed"] is (defect == "none") and not calls
    assert result["dimension_status"]["scientific_code"]["status"] == ("failed" if defect == "source" else "passed")
    assert result["dimension_status"]["empirical"]["status"] == ("failed" if defect == "empirical" else "passed")
    assert result["dimension_status"]["theory"]["status"] == "not_requested"
    assert native == before and result["internal_acceptance_required"] is False
    if profile == "native":
        for dimension, runtime_language in (("scientific_code", language), ("empirical", "python")):
            execution = result["dimension_status"][dimension]["execution"]
            assert execution["execution_profile"] == "scientific_native_" + runtime_language
            assert execution["backend"] == "native_" + runtime_language


@pytest.mark.parametrize("dimension", ["unresolved_gaps", "novelty", "opaque_unsupported"])
@pytest.mark.parametrize("requirement", ["required", "optional"])
def test_unsupported_active_dimensions_reject_before_evaluation(tmp_path, monkeypatch, dimension, requirement):
    kwargs = outcome_fixture(tmp_path, intent={"theory": "required", dimension: requirement})
    reviews = scripted_semantics(monkeypatch)
    with pytest.raises(ValueError, match="does not support active dimensions"):
        outcomes.evaluate_final_research_artifacts(**kwargs)
    assert not reviews and not kwargs["out_dir"].exists()


def test_not_applicable_extra_intent_does_not_request_unimplemented_authority():
    assert outcomes.publication_dimension_requirements({"theory": "required", "novelty": "not_applicable"}) == {
        "theory": "required", "scientific_code": "optional", "empirical": "optional",
        "formal": "optional", "novelty": "not_applicable"}


@pytest.mark.parametrize("language", ["python", "r"])
def test_frozen_native_estimator_profile_reaches_common_outcome_executor(tmp_path, monkeypatch, language):
    config = os.environ.get("AI_STATISTICIAN_TEST_NATIVE_" + language.upper() + "_CONFIG", "")
    if not config:
        pytest.skip("explicit native outcome fixture environment is not configured")
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_" + language.upper() + "_CONFIG", config)
    kwargs = outcome_fixture(tmp_path, language=language, intent={"scientific_code": "required"})
    profile = "scientific_native_" + language
    kwargs["task"]["hidden_algorithm_evaluator"]["execution_profile"] = profile
    original = deepcopy(kwargs)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    execution = result["dimension_status"]["scientific_code"]["execution"]
    assert result["task_passed"] is True
    assert execution["execution_profile"] == profile
    assert execution["backend"] == "native_" + language
    assert execution["estimator_invocation_count"] == 1
    request = json.loads(Path(execution["request_path"]).read_bytes())
    assert request["execution_profile"] == profile
    assert stable_hash(request) == execution["request_hash"]
    assert request["runtime"]["native_" + language]["configuration_path"] == str(Path(config).resolve())
    assert kwargs == original


@pytest.mark.parametrize("dimension", ["empirical", "source_replication"])
def test_frozen_native_artifact_profile_reaches_common_outcome_executor(tmp_path, monkeypatch, dimension):
    config = os.environ.get("AI_STATISTICIAN_TEST_NATIVE_PYTHON_CONFIG", "")
    if not config:
        pytest.skip("explicit native artifact fixture environment is not configured")
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_PYTHON_CONFIG", config)
    kwargs = outcome_fixture(tmp_path, intent={dimension: "required"})
    evaluator = kwargs["task"]["hidden_empirical_evaluator"]
    evaluator["execution_profile"] = "scientific_native_python"
    if dimension == "source_replication":
        kwargs["task"]["hidden_source_replication_evaluator"] = deepcopy(evaluator)
        kwargs["source_replication_artifact"] = kwargs["empirical_artifact"]
    original = deepcopy(kwargs)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    execution = result["dimension_status"][dimension]["execution"]
    assert result["task_passed"] is True
    assert execution["execution_profile"] == "scientific_native_python"
    assert execution["backend"] == "native_python"
    request = json.loads(Path(execution["request_path"]).read_bytes())
    assert request["execution_profile"] == "scientific_native_python"
    assert stable_hash(request) == execution["request_hash"]
    assert request["input_artifacts"][0]["artifact_id"] == "candidate-artifact.json"
    assert kwargs == original


def test_missing_frozen_native_environment_is_not_replaced_by_wasm(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_PYTHON_CONFIG", str(tmp_path / "missing.json"))
    kwargs = outcome_fixture(tmp_path, intent={"scientific_code": "required"})
    kwargs["task"]["hidden_algorithm_evaluator"]["execution_profile"] = "scientific_native_python"
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    execution = result["dimension_status"]["scientific_code"]["execution"]
    assert result["task_passed"] is False
    assert execution["execution_attempted"] is False
    assert execution["execution_profile"] == "scientific_native_python"
    assert execution["backend"] == "native_python"
    assert any("configuration rejected" in error for error in execution["errors"])


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
    assert rows["theory"]["assessment_authority"] == "local_model_review"
    assert rows["empirical"]["status"] == "passed"
    assert rows["formal"]["status"] == "not_requested"
    assert result["task_passed"] is (theory_passed and offset == 0)
    assert result["internal_acceptance_required"] is False and result["runtime_feedback_generated"] is False
    assert result["submission_identity_hash"] == stable_hash(kwargs["submission_identity"])
    assert len(calls) == 1 and calls[0]["candidate_documents"] == kwargs["theory_documents"]
    assert json.loads((kwargs["out_dir"] / "outcome.json").read_text()) == result
    saved = json.loads((kwargs["out_dir"] / "theory" / "semantic_judgment.json").read_text())
    assert saved["judgment_hash"] == rows["theory"]["semantic_judgment_hash"]
    assert kwargs == before
    with pytest.raises(FileExistsError):
        outcomes.evaluate_final_research_artifacts(**kwargs)
    assert len(calls) == 1


@pytest.mark.parametrize("verdict,status", [("accepted", "passed"), ("rejected", "failed"), ("unresolved", "unresolved")])
def test_external_review_is_recorded_without_model_agreement_or_inferred_scientific_truth(tmp_path, monkeypatch, verdict, status):
    kwargs = outcome_fixture(tmp_path, intent={"theory": "required"})
    external_review_fixture(kwargs, verdict=verdict)
    original = deepcopy(kwargs)
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    row = result["dimension_status"]["theory"]
    assert row["status"] == status and row["assessment_authority"] == "external_adjudication_record"
    assert row["external_review_verdict"] == verdict and row["external_review_hash"] == stable_hash(kwargs["external_theory_review"])
    assert result["task_passed"] is (verdict == "accepted") and not calls
    assert result["submitted_material_hash"] == kwargs["external_theory_review"]["submitted_material_hash"]
    directory = kwargs["out_dir"] / "theory"
    assert json.loads((directory / "external_review.json").read_text()) == kwargs["external_theory_review"]
    assert (directory / "assessment_report.txt").read_bytes() == Path(kwargs["external_theory_review"]["report"]["path"]).read_bytes()
    assert (directory / "assessment_protocol.txt").read_bytes() == Path(kwargs["task"]["external_theory_authority"]["protocol"]["path"]).read_bytes()
    assert kwargs == original
    with pytest.raises(FileExistsError):
        outcomes.evaluate_final_research_artifacts(**kwargs)
    assert not calls


@pytest.mark.parametrize("change", ["authority", "task", "submission", "material", "protocol", "report", "verdict",
                                   "changed_document", "changed_experiment", "model_fallback", "no_frozen_authority"])
def test_external_review_cannot_grade_another_submission_change_its_protocol_or_fall_back(tmp_path, monkeypatch, change):
    kwargs = outcome_fixture(tmp_path, intent={"theory": "required"})
    external_review_fixture(kwargs)
    review = kwargs["external_theory_review"]
    field = {"authority": "authority_id", "task": "task_hash", "submission": "submission_identity_hash",
             "material": "submitted_material_hash"}.get(change)
    if field:
        review[field] = "another"
    elif change in {"protocol", "report"}:
        reference = kwargs["task"]["external_theory_authority"]["protocol"] if change == "protocol" else review["report"]
        Path(reference["path"]).write_text("changed after assessment")
    elif change == "verdict":
        review["verdict"] = ["accepted"]
    elif change == "changed_document":
        text = "another final argument"
        kwargs["theory_documents"][0].update(content=text, sha256=hashlib.sha256(text.encode()).hexdigest())
    elif change == "changed_experiment":
        kwargs["empirical_artifact"]["measurement"] += 1
    elif change == "model_fallback":
        kwargs["task"]["hidden_theory_semantic_evaluator"] = {"provider": "local"}
    else:
        kwargs["task"].pop("external_theory_authority")
    calls = scripted_semantics(monkeypatch)
    with pytest.raises(ValueError):
        outcomes.evaluate_final_research_artifacts(**kwargs)
    assert not calls and not kwargs["out_dir"].exists()


def test_missing_external_assessment_stays_pending_and_does_not_use_a_model(tmp_path, monkeypatch):
    kwargs = outcome_fixture(tmp_path, intent={"theory": "required"})
    external_review_fixture(kwargs)
    kwargs.pop("external_theory_review")
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["dimension_status"]["theory"]["status"] == "pending_adjudication"
    assert result["task_passed"] is False and not calls


def test_external_theory_acceptance_cannot_override_incorrect_numerical_submission(tmp_path, monkeypatch):
    require_runtime("python")
    kwargs = outcome_fixture(tmp_path, offset=1)
    external_review_fixture(kwargs)
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["dimension_status"]["theory"]["status"] == "passed"
    assert result["dimension_status"]["scientific_code"]["status"] == "failed"
    assert result["task_passed"] is False and not calls


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


@pytest.mark.parametrize("intent", [{}, {"theory": "optional"}, {"formal": "required"}])
def test_no_required_success_or_boolean_formal_claim_cannot_pass(tmp_path, intent):
    kwargs = outcome_fixture(tmp_path, intent=intent)
    kwargs.update(theory_documents=(), estimator_bindings=(), empirical_artifact=None,
                  formal_artifacts={"all_ok": True, "kernel_verified": True})
    result = outcomes.evaluate_final_research_artifacts(**kwargs)
    assert result["task_passed"] is False
    if intent.get("formal") == "required":
        assert result["dimension_status"]["formal"]["status"] == "failed"


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


def projection_fixture(tmp_path):
    kwargs = outcome_fixture(tmp_path)
    binding = kwargs["estimator_bindings"][0]
    docs = {row["path"]: row["content"] for row in kwargs["theory_documents"]}
    root = tmp_path / "theory-snapshot"
    root.mkdir()
    for path, content in docs.items():
        (root / path).write_text(content)
    core = {"theory_workspace_manifest": theory_workspace_document_manifest(docs, workspace_dir=root)}
    row = {"estimator_id": binding.artifact_id, "language": binding.language, "source_code": binding.code,
           "script_hash": binding.code_hash, "project_hash": binding.project_hash,
           "project_files": list(binding.project_files), "dependencies": list(binding.dependencies),
           "smoke_passed": False, "execution_attempted": False}
    empirical = {"source_code": "opaque experiment", "metrics": {"measurement": 99178},
                 "execution_phase": "exploratory_diagnostic", "smoke_passed": False}
    runtime = {"internal_status": "BLOCKED", "selected_artifacts": {
        "theory": core, "scientific_code": {"prototypes": [row]}, "empirical": {"generated_simulation_sandbox_prototypes": [empirical]}},
        "earlier_accepted_artifacts": {"opaque": "not selected"}}
    control = {"checkpoint_payloads": {"theory": {"core_packet": core}, "algorithm": {
        "code_draft": {"language": binding.language, "code": binding.code,
                       "dependencies": list(binding.dependencies), "project_files": list(binding.project_files)},
        "check_result": {"prototype": row, "accepted": False}}, "simulation": {"check_result": {"prototype": empirical}}}}
    return kwargs, runtime, control


def test_projection_keeps_exact_unaccepted_material_and_its_exploratory_status(tmp_path):
    kwargs, runtime, control = projection_fixture(tmp_path)
    original = deepcopy((runtime, control))
    product = outcomes.publication_material_from_submission(runtime, source_kind="runtime")
    shared = outcomes.publication_material_from_submission(control, source_kind="control", control_estimator_scopes={"algorithm": "opaque"})
    assert product == shared
    assert product["theory_documents"] == kwargs["theory_documents"]
    assert product["estimator_bindings"] == kwargs["estimator_bindings"]
    assert product["empirical_artifact"]["generated_simulation_rows"][0]["execution_phase"] == "exploratory_diagnostic"
    assert (runtime, control) == original
    product["empirical_artifact"]["generated_simulation_rows"][0]["metrics"]["measurement"] = -1
    assert (runtime, control) == original


@pytest.mark.parametrize("phase,confirmed,eligible", [
    ("exploratory_diagnostic", False, False),
    ("confirmatory_evaluator_execution", True, True),
])
def test_projection_reads_selected_runtime_manifest_without_inventing_row_receipts(tmp_path, phase, confirmed, eligible):
    _, runtime, _ = projection_fixture(tmp_path)
    selected = runtime["selected_artifacts"]["empirical"]
    selected.update(empirical_evaluation_phase=phase, evaluator_source_confirmation=confirmed,
                    confirmatory_empirical_evidence_eligible=eligible)
    row = selected["generated_simulation_sandbox_prototypes"][0]
    row.pop("execution_phase")
    original = deepcopy(runtime)
    material = outcomes.publication_material_from_submission(runtime, source_kind="runtime")
    assert material["empirical_artifact"] == {
        "generated_simulation_rows": [row], "empirical_evaluation_phase": phase,
        "evaluator_source_confirmation": confirmed, "confirmatory_empirical_evidence_eligible": eligible}
    assert "execution_phase" not in material["empirical_artifact"]["generated_simulation_rows"][0]
    assert "evaluator_source_confirmation" not in material["empirical_artifact"]["generated_simulation_rows"][0]
    assert runtime == original


@pytest.mark.parametrize("dimension", ["theory", "scientific_code", "empirical"])
def test_projection_keeps_missing_final_selections_missing(tmp_path, dimension):
    _, runtime, control = projection_fixture(tmp_path)
    runtime["selected_artifacts"].pop(dimension)
    control["checkpoint_payloads"].pop({"scientific_code": "algorithm", "empirical": "simulation"}.get(dimension, dimension))
    product = outcomes.publication_material_from_submission(runtime, source_kind="runtime")
    shared = outcomes.publication_material_from_submission(control, source_kind="control", control_estimator_scopes={"algorithm": "opaque"})
    assert product == shared
    key = {"theory": "theory_documents", "scientific_code": "estimator_bindings", "empirical": "empirical_artifact"}[dimension]
    assert not product[key]


@pytest.mark.parametrize("change", ["document", "source_hash", "support", "draft", "dependencies", "estimator", "unknown_scope", "missing_contract", "runtime_contract", "native_kind"])
def test_invalid_projection_identity_or_contract_is_not_repaired(tmp_path, change):
    _, runtime, control = projection_fixture(tmp_path)
    source = runtime["selected_artifacts"]["scientific_code"]["prototypes"][0]
    kind, submission, scopes = "control", control, {"algorithm": "opaque"}
    if change == "document":
        (tmp_path / "theory-snapshot" / "claim.md").write_text("later mutation")
    elif change == "source_hash":
        source["script_hash"] = "different"
    elif change == "support":
        source["project_files"] = [{"path": "helper.py", "content": "different support"}]
    elif change == "draft":
        control["checkpoint_payloads"]["algorithm"]["code_draft"]["code"] = "different source"
    elif change == "dependencies":
        control["checkpoint_payloads"]["algorithm"]["code_draft"]["dependencies"] = ["numpy"]
    elif change == "estimator":
        scopes = {"algorithm": "different"}
    elif change == "unknown_scope":
        control["checkpoint_payloads"]["unknown"] = deepcopy(control["checkpoint_payloads"]["algorithm"])
    elif change == "missing_contract":
        scopes = None
    elif change == "runtime_contract":
        kind, submission = "runtime", runtime
    else:
        kind = "native"
    with pytest.raises(ValueError):
        outcomes.publication_material_from_submission(submission, source_kind=kind, control_estimator_scopes=scopes)


def source_file_projection_fixture(tmp_path, *, status="FAILED", selected_run=2):
    def reference(path):
        raw = path.read_bytes()
        return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}

    intent = {"source_replication": "required", "theory": "not_applicable"}
    manifests, refs, contents = [], [], []
    for run in (1, 2):
        directory = tmp_path / ("source-run-" + str(run))
        workspace = directory / "source_workspace"
        workspace.mkdir(parents=True)
        results = {"results/opaque.csv": b"label,value\r\nopaque," + str(run).encode() + b"\r\n",
                   "results/opaque.bin": bytes([255, 0, run, 128])}
        streams = {"runtime_streams/source_stdout.txt": b"opaque output\r\n" * 10001 + str(run).encode(),
                   "runtime_streams/source_stderr.txt": b"opaque raw failure\r\n"}
        descriptors, stream_rows = [], []
        for collection, files, root in ((descriptors, results, workspace), (stream_rows, streams, directory)):
            for relative, raw in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                collection.append({"relative_path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                                   "size_bytes": len(raw), "content_encoding": "binary_not_embedded"})
        path = directory / "source_replication_manifest.json"
        manifest = {"artifact_kind": "SourceReplicationManifest", "artifact_id": "opaque-source-" + str(run),
                    "question_id": "opaque", "manifest_path": str(path),
                    "execution_status": "EXECUTED" if run == 1 else status,
                    "raw_stdout": "truncated opaque preview", "raw_stdout_truncated": True,
                    "result_artifacts": descriptors, "execution_streams": stream_rows,
                    "declared_result_artifact_paths": list(results) + ["results/missing.rds",
                                                                          "runtime_streams/source_stdout.txt"]}
        manifest["manifest_hash"] = stable_hash(manifest)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        ref = {**reference(path), **{key: manifest[key] for key in
                                    ("artifact_id", "manifest_hash", "execution_status")}, "source_run": run}
        manifests.append(manifest)
        refs.append(ref)
        contents.append({**results, **streams})
    report = tmp_path / "selected-report.md"
    report.write_bytes(b"# Opaque source report\r\nUnresolved mechanism fixture, not a scientific claim.\r\n")
    body = {"artifact_kind": "SourceReplicationCheckpoint", "question_id": "opaque", "task_intent": intent,
            "source_replication_manifest_ref": refs[selected_run - 1], "source_execution_attempt_refs": refs,
            "selected_source_run": selected_run, "report_document": {**reference(report), "relative_path": "report.md"},
            "unresolved_gaps": ["Opaque source remains unresolved."]}
    checkpoint = {**body, "checkpoint_id": "source_replication_checkpoint:" + stable_hash(body)[:20]}
    runtime = {"question_id": "opaque", "task_intent": intent,
               "selected_artifacts": {"source_replication": checkpoint}}
    control = {"question_id": "opaque", "task_intent": intent,
               "checkpoint_payloads": {"theory": {"core_packet": checkpoint}}}
    return runtime, control, manifests, contents


@pytest.mark.parametrize("status", ["EXECUTED", "FAILED"])
@pytest.mark.parametrize("selected_run", [1, 2])
def test_selected_source_projection_keeps_full_result_and_stream_bytes_without_draft_salvage(tmp_path, status, selected_run):
    runtime, control, manifests, contents = source_file_projection_fixture(tmp_path, status=status, selected_run=selected_run)
    original = deepcopy((runtime, control))
    product = outcomes.publication_material_from_submission(runtime, source_kind="runtime")
    shared = outcomes.publication_material_from_submission(control, source_kind="control", control_estimator_scopes={})
    assert product == shared
    artifact = product["source_replication_artifact"]
    assert artifact["source_execution"] == manifests[selected_run - 1]
    assert artifact["source_execution_attempts"] == manifests
    assert artifact["missing_files"] == ["results/missing.rds", "runtime_streams/source_stdout.txt"]
    assert set(artifact["files"]) == set(contents[selected_run - 1])
    for path, raw in contents[selected_run - 1].items():
        assert artifact["files"][path] == {"base64": base64.b64encode(raw).decode("ascii"),
            "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}
    assert artifact["report_document"]["content"].endswith("\r\n")
    assert not product["theory_documents"] and not product["estimator_bindings"] and product["empirical_artifact"] is None
    assert "task_passed" not in artifact and "confirmatory_empirical_evidence_eligible" not in artifact
    assert (runtime, control) == original


@pytest.mark.parametrize("defect", ["changed_result", "missing_result", "changed_stream", "missing_stream", "size", "duplicate", "escape", "ambiguous", "missing_manifest"])
def test_selected_source_projection_rejects_unbound_files_without_a_previous_run_fallback(tmp_path, defect):
    runtime, _, manifests, _ = source_file_projection_fixture(tmp_path)
    manifest = manifests[1]
    root = Path(manifest["manifest_path"]).parent
    if defect in {"changed_result", "missing_result", "changed_stream", "missing_stream"}:
        path = root / ("source_workspace/results/opaque.bin" if defect.endswith("result") else "runtime_streams/source_stderr.txt")
        if defect.startswith("changed"):
            path.write_bytes(b"changed opaque bytes")
        else:
            path.unlink()
    elif defect == "missing_manifest":
        Path(manifest["manifest_path"]).unlink()
    else:
        if defect == "size":
            manifest["result_artifacts"][0]["size_bytes"] += 1
        elif defect == "duplicate":
            manifest["result_artifacts"].append(deepcopy(manifest["result_artifacts"][0]))
        elif defect == "escape":
            manifest["result_artifacts"][0]["relative_path"] = "../outside.csv"
        else:
            manifest["execution_streams"].append(deepcopy(manifest["result_artifacts"][0]))
        manifest.pop("manifest_hash")
        manifest["manifest_hash"] = stable_hash(manifest)
        path = Path(manifest["manifest_path"])
        path.write_text(json.dumps(manifest), encoding="utf-8")
        checkpoint = runtime["selected_artifacts"]["source_replication"]
        ref = checkpoint["source_replication_manifest_ref"]
        ref.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), byte_size=len(path.read_bytes()),
                   manifest_hash=manifest["manifest_hash"])
        body = {key: value for key, value in checkpoint.items() if key != "checkpoint_id"}
        checkpoint["checkpoint_id"] = "source_replication_checkpoint:" + stable_hash(body)[:20]
    with pytest.raises(ValueError):
        outcomes.publication_material_from_submission(runtime, source_kind="runtime")


@pytest.mark.parametrize("kind", ["runtime", "control"])
@pytest.mark.parametrize("profile", ["scientific_wasm", "scientific_native_python"])
@pytest.mark.parametrize("expected", [2, 3])
def test_selected_source_bytes_reach_the_real_common_artifact_harness(tmp_path, monkeypatch, kind, profile, expected):
    if profile == "scientific_wasm":
        require_runtime("python")
    elif not os.environ.get("AI_STATISTICIAN_NATIVE_PYTHON_CONFIG"):
        pytest.skip("pinned native Python config is not supplied")
    runtime, control, _, _ = source_file_projection_fixture(tmp_path)
    material = outcomes.publication_material_from_submission(
        runtime if kind == "runtime" else control, source_kind=kind,
        **({"control_estimator_scopes": {}} if kind == "control" else {}))
    question = OpenResearchQuestion("opaque", "Opaque file transport", "Not a scientific assessment.",
                                   task_intent=runtime["task_intent"])
    public = research_question_payload(question, include_task_intent=True)
    harness = tmp_path / "opaque-file-evaluator.py"
    harness.write_text("import base64, csv, io\n"
        "def evaluate_artifact(candidate, seed, replicates):\n"
        "    files = candidate['files']\n"
        "    text = base64.b64decode(files['results/opaque.csv']['base64']).decode('utf-8')\n"
        "    row = next(csv.DictReader(io.StringIO(text)))\n"
        "    return {'measurement': int(row['value']),\n"
        "        'binary': base64.b64decode(files['results/opaque.bin']['base64']) == bytes([255,0,2,128]),\n"
        "        'full_stream': len(base64.b64decode(files['runtime_streams/source_stdout.txt']['base64'])) > 100000,\n"
        "        'missing_kept': candidate['missing_files'] == ['results/missing.rds', 'runtime_streams/source_stdout.txt']}\n",
        encoding="utf-8")
    task = {"task_id": question.id, "task_intent": deepcopy(question.task_intent),
            "visible_question_hash": stable_hash(_visible_question_hash_payload(public)),
            "hidden_source_replication_evaluator": {"language": "python", "harness_path": str(harness),
                "harness_sha256": hashlib.sha256(harness.read_bytes()).hexdigest(), "dependencies": [],
                "seed": 17, "replicates": 1, "timeout_seconds": 30, "execution_profile": profile,
                "acceptance_checks": [{"check_id": "opaque-" + key, "path": [key], "operator": "eq", "expected": value}
                                      for key, value in (("measurement", expected), ("binary", True),
                                                         ("full_stream", True), ("missing_kept", True))]}}
    original = deepcopy(material)
    calls = scripted_semantics(monkeypatch)
    result = outcomes.evaluate_final_research_artifacts(
        question=question, task=task,
        submission_identity={"question_id": question.id, "question_hash": stable_hash(public),
                             "task_intent": deepcopy(question.task_intent)},
        project_root=tmp_path, out_dir=tmp_path / "common-outcome", **material)
    row = result["dimension_status"]["source_replication"]
    assert row["execution"]["execution_passed"] is True
    assert row["status"] == ("passed" if expected == 2 else "failed")
    assert result["task_passed"] is (expected == 2)
    assert material == original and not calls
    assert result["evaluation_role"] == "external_publication_outcome_not_product_acceptance_or_proof"
