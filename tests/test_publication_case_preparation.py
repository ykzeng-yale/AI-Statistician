"""Candidate configuration assembly, not model inference or scientific grading."""

import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from urllib.error import HTTPError

import pytest

from ai_statistician.cross_family_eval_protocol import (
    CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY, confirmatory_evaluation_seed,
    resolve_confirmatory_evaluation_cohort,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_source_library import load_research_source_snapshot
from ai_statistician.research_schema import load_open_research_questions, research_question_payload
from benchmarks.publication.prepare_configs import MODES, prepare
from benchmarks.publication.draw_cli import main as draw_main


def inputs(tmp_path, monkeypatch):
    def no_http(*args, **kwargs):
        raise AssertionError("configuration preparation must not call a model or source network")
    monkeypatch.setattr("urllib.request.build_opener", no_http)
    deployment = tmp_path / "deployment.json"
    deployment.write_text(json.dumps({"model": "Qwen3-4B-Instruct-2507", "authority": "test declaration"}))
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    content = "opaque public source bytes\n"
    (source_dir / "source.txt").write_text(content)
    environment_text = "opaque environment declaration\n"
    (source_dir / "environment.txt").write_text(environment_text)
    sources = tmp_path / "sources.json"
    sources.write_text(json.dumps({"schema_version": 1, "snapshot_id": "opaque-config-source",
        "source_horizon": "2026-10-03", "source_root": "sources", "documents": [{
            "document_id": "opaque", "title": "Opaque", "source_kind": "replication_provenance",
            "relative_path": "source.txt", "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "model_visible": True, "git_commit": "opaque-fixture-commit"}, {
            "document_id": "environment", "title": "Opaque environment", "source_kind": "replication_provenance",
            "relative_path": "environment.txt", "sha256": hashlib.sha256(environment_text.encode()).hexdigest(),
            "model_visible": True, "git_commit": "opaque-fixture-commit"}]}))
    snapshot = load_research_source_snapshot(sources)
    environment = tmp_path / "environment"
    environment.mkdir()
    (environment / "python").symlink_to(sys.executable)
    execution = tmp_path / "execution.json"
    execution.write_text(json.dumps({"schema_version": 3, "artifact_kind": "ResearchSourceExecutionSpec",
        "execution_id": "opaque-config-execution", "benchmark_id": "opaque-fixture",
        "source_snapshot_id": snapshot.snapshot_id, "source_snapshot_hash": snapshot.snapshot_hash,
        "source_manifest_sha256": snapshot.manifest_sha256, "source_commit": "opaque-fixture-commit",
        "entrypoint_document_id": "opaque", "environment_lock_document_id": "environment",
        "environment_root": str(environment), "runtime_language": "python",
        "interpreter_executable_relative_path": "python",
        "interpreter_executable_sha256": hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
        "runtime_read_roots": [], "working_directory_relative": ".", "arguments": [],
        "package_distributions": {"Opaque": "opaque"}, "timeout_seconds": 30, "max_output_bytes": 8192}))
    questions = tmp_path / "questions.json"
    field = {key: "opaque" for key in (
        "name", "meaning", "json_type", "shape", "units", "indexing", "edge_cases")}
    questions.write_text(json.dumps([{"id": "opaque-config-question", "title": "Opaque configuration",
        "description": "Mechanism fixture, not a statistical result.",
        "task_intent": {"theory": "required", "scientific_code": "required", "empirical": "required",
                        "formal": "not_applicable", "source_replication": "required"},
        "estimator_execution_contract": {"schema_version": 1, "estimator_id": "opaque-estimator",
            "entrypoint": "run_estimator", "request_fields": [{**field, "clause_id": "request",
                "binding": "per_replicate_data"}],
            "response_fields": [{**field, "clause_id": "response", "normalization": "opaque"}]}}]))
    return dict(out=tmp_path / "prepared",
        questions=questions, question_id="opaque-config-question",
        deployment=deployment, sources=sources, source_execution=execution,
        call_limit=19, output_tokens=1703, temperature=0.23, seed=17, confirmation_base=90211,
        replicates=23, execution_timeout=117, model_timeout=211.0, no_progress_turns=5)


def test_candidate_uses_existing_configs_with_explicit_data_and_output_settings(tmp_path, monkeypatch):
    args = inputs(tmp_path, monkeypatch)
    refs = prepare(**args)
    assert tuple(refs) == MODES
    configs = {}
    for mode, ref in refs.items():
        raw = Path(ref["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == ref["sha256"] and len(raw) == ref["byte_size"]
        configs[mode] = json.loads(raw)
    for mode, config in configs.items():
        assert config["question_id"] == "opaque-config-question"
        assert config["backend"] == {"base_url": "http://127.0.0.1:8081/v1", "timeout_s": 211.0}
        assert config["source_execution_ref"]["path"] == str(args["source_execution"].resolve())
        assert config["native_execution_refs"] == {}
        assert all(row["provider_name"] == row["model_tier"] == "local"
                   and row["max_tokens"] == 1703 and row["temperature"] == 0.23
                   for row in config["roles"].values())
        assert config["roles"]["theory"]["serious_max_tokens"] == 1703
        if mode in {"free_planning", "same_workflow"}:
            assert config["request"]["max_tokens"] == 1703
            assert config["request"]["tool_choice"] == "any"
            assert config["limits"]["local_model_call_limit"] == 19
            assert config["execution"]["timeout_s"] == 117
            assert config["execution"]["seed"] == 17 and config["execution"]["n_runs"] == 23
            assert bool(config["workflow_instructions"]) == (mode == "same_workflow")
        else:
            runtime = config["runtime"]
            assert runtime["local_model_call_limit"] == 19 and runtime["max_iterations"] == 19
            assert runtime["generated_simulation_timeout_seconds"] == runtime["theory_scratch_timeout_seconds"] == 117
            assert runtime["seed"] == 17 and runtime["n_runs"] == 23
            context = config["architect_context"]
            assert confirmatory_evaluation_seed(context, fallback_seed=17) == 90211
            cohort, errors = resolve_confirmatory_evaluation_cohort(context,
                question_id=config["question_id"], execution_seed=90211)
            assert not errors and cohort == context[CONFIRMATORY_EVALUATION_COHORT_CONTEXT_KEY]
            assert configs["free_planning"]["execution"]["confirmatory_seeds"] == [
                cohort["base_seed"] + index * 1_000_003 for index in range(19)]
    record = json.loads((args["out"] / "preparation.json").read_text())
    assert record["scope"] == "configuration_preparation_only"
    assert record["model_calls"] == 0 and record["study_activated"] is False
    assert record["scientific_evaluation_performed"] is False and record["remaining"]
    saved = {path: path.read_bytes() for path in args["out"].iterdir()}
    with pytest.raises(FileExistsError):
        prepare(**args)
    assert all(path.read_bytes() == raw for path, raw in saved.items())


@pytest.mark.parametrize("change", [
    {"confirmation_base": 17}, {"call_limit": 0}, {"execution_timeout": 0}, {"temperature": float("nan")},
])
def test_bad_candidate_settings_do_not_materialize_configs(tmp_path, monkeypatch, change):
    args = inputs(tmp_path, monkeypatch)
    args.update(change)
    with pytest.raises(ValueError):
        prepare(**args)
    assert not args["out"].exists()


def test_control_request_is_bound_in_candidate_protocol_identity(tmp_path, monkeypatch):
    args = inputs(tmp_path, monkeypatch)
    refs = prepare(**args)
    configs = {mode: json.loads(Path(ref["path"]).read_bytes()) for mode, ref in refs.items()}
    shared, production = configs["free_planning"], configs["full_collaboration"]
    material = {"question_ref": shared["question_ref"], "question_id": shared["question_id"],
        "native_execution_refs": {}, "deployment_ref": shared["deployment_ref"],
        "source_snapshot_ref": shared["source_snapshot_ref"], "source_execution_ref": shared["source_execution_ref"],
        "backend": shared["backend"], "roles": production["roles"], "control_request": shared["request"],
        "workflow": configs["same_workflow"]["workflow_instructions"], "modes": MODES,
        "call_limit": args["call_limit"], "seed": args["seed"], "replicates": args["replicates"],
        "execution_timeout": args["execution_timeout"], "no_progress_turns": args["no_progress_turns"],
        "confirmation_schedule": shared["execution"]["confirmatory_seeds"]}
    declared = production["architect_context"]["cross_family_evaluation_protocol"]["protocol_fingerprint"]
    assert stable_hash(material) == declared
    material["control_request"] = {**shared["request"], "tool_choice": "auto"}
    assert stable_hash(material) != declared


@pytest.mark.parametrize("language", ["python", "r"])
def test_native_execution_refs_are_explicit_and_change_protocol_identity(tmp_path, monkeypatch, language):
    args = inputs(tmp_path, monkeypatch)
    native_path = tmp_path / "native.json"
    native = {"schema_version": 1, "runtime_language": language,
        "runtime_version": "opaque-schema-fixture-not-executed",
        "environment_root": str(tmp_path / "environment"),
        "interpreter_executable_relative_path": "python",
        "interpreter_executable_sha256": hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
        "runtime_read_roots": [], "runtime_executables": {}, "runtime_environment": {},
        "package_versions": {"jsonlite": "opaque-version"} if language == "r" else {}}
    native_path.write_text(json.dumps(native))
    args["native_" + language] = native_path
    refs = prepare(**args)
    configs = {mode: json.loads(Path(ref["path"]).read_bytes()) for mode, ref in refs.items()}
    declared = {language: {"path": str(native_path.resolve()),
        "sha256": hashlib.sha256(native_path.read_bytes()).hexdigest(), "byte_size": native_path.stat().st_size}}
    assert all(config["native_execution_refs"] == declared for config in configs.values())
    before = configs["full_collaboration"]["architect_context"]["cross_family_evaluation_protocol"]["protocol_fingerprint"]
    native["runtime_version"] += "-changed"
    native_path.write_text(json.dumps(native))
    args["out"] = tmp_path / "prepared-after-declaration-change"
    changed = prepare(**args)
    after = json.loads(Path(changed["full_collaboration"]["path"]).read_bytes())
    assert after["native_execution_refs"][language]["sha256"] != declared[language]["sha256"]
    assert after["architect_context"]["cross_family_evaluation_protocol"]["protocol_fingerprint"] != before


def test_changed_source_is_not_declared_a_valid_input(tmp_path, monkeypatch):
    args = inputs(tmp_path, monkeypatch)
    (tmp_path / "sources" / "source.txt").write_text("changed public bytes")
    with pytest.raises(ValueError):
        prepare(**args)
    assert not args["out"].exists()


def test_missing_source_execution_is_rejected_before_all_arm_files(tmp_path, monkeypatch):
    args = inputs(tmp_path, monkeypatch)
    args["source_execution"] = tmp_path / "missing-execution.json"
    with pytest.raises(FileNotFoundError):
        prepare(**args)
    assert not args["out"].exists()


def test_question_selection_and_contract_are_explicit_not_a_case_default(tmp_path, monkeypatch):
    args = inputs(tmp_path, monkeypatch)
    original = json.loads(args["questions"].read_bytes())[0]
    selected = {**original, "id": "opaque-selected-question",
                "estimator_execution_contract": {**original["estimator_execution_contract"], "estimator_id": "opaque-selected"}}
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([original, selected]))
    args.update(questions=path, question_id=selected["id"])
    refs = prepare(**args)
    for ref in refs.values():
        config = json.loads(Path(ref["path"]).read_bytes())
        assert config["question_id"] == selected["id"]
        assert config["question_ref"]["path"] == str(path.resolve())
        if "estimator_ids" in config:
            assert config["estimator_ids"] == ["opaque-selected"]


@pytest.mark.parametrize("defect", ["absent", "duplicate", "missing_contract"])
def test_invalid_selected_question_does_not_write_arm_files(tmp_path, monkeypatch, defect):
    args = inputs(tmp_path, monkeypatch)
    rows = json.loads(args["questions"].read_bytes())
    if defect == "absent":
        args["question_id"] = "absent"
    elif defect == "duplicate":
        rows *= 2
    else:
        rows[0].pop("estimator_execution_contract")
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(rows))
    args["questions"] = path
    with pytest.raises(ValueError):
        prepare(**args)
    assert not args["out"].exists()


@pytest.mark.parametrize("requirement", ["required", "optional"])
def test_unsupported_active_intent_is_rejected_before_configuration_preparation(tmp_path, monkeypatch, requirement):
    args = inputs(tmp_path, monkeypatch)
    questions = json.loads(args["questions"].read_bytes())
    questions[0]["task_intent"]["opaque_unsupported"] = requirement
    path = tmp_path / "unsupported.json"
    path.write_text(json.dumps(questions))
    args["questions"] = path
    with pytest.raises(ValueError, match="does not support active dimensions"):
        prepare(**args)
    assert not args["out"].exists()


def test_preserved_tsci_draft_is_not_silently_declared_assessable(tmp_path, monkeypatch):
    args = inputs(tmp_path, monkeypatch)
    args.update(questions=Path("benchmarks/publication_case_candidates/tsci_b1_card/questions.json").resolve(),
                question_id="tsci_b1_card_integrated_candidate_v2")
    before = args["questions"].read_bytes()
    with pytest.raises(ValueError, match="unresolved_gaps"):
        prepare(**args)
    assert not args["out"].exists() and args["questions"].read_bytes() == before


@pytest.mark.parametrize("question_id,estimator_id", [
    ("stepmix_external_variables_source_assisted_candidate_v3", "stepmix_external_variables"),
    ("ebnm_prior_families_source_assisted_candidate_v3", "ebnm_prior_families"),
    ("bizicount_joint_count_source_assisted_candidate_v3", "bizicount_joint_count"),
])
def test_unactivated_execution_tasks_keep_integrated_intent_and_explicit_transport(
    tmp_path, monkeypatch, question_id, estimator_id,
):
    args = inputs(tmp_path, monkeypatch)
    args.update(questions=Path("benchmarks/publication_case_candidates/published_methods/execution_questions.json").resolve(),
                question_id=question_id)
    questions = load_open_research_questions(args["questions"])
    selected = next(row for row in questions if row.id == question_id)
    assert all(selected.task_intent[dimension] == "required" for dimension in (
        "theory", "scientific_code", "empirical", "source_replication"))
    assert "unresolved_gaps" not in selected.task_intent
    assert "unresolved" in selected.description.lower()
    assert selected.task_intent["formal"] == selected.task_intent["novelty"] == "not_applicable"
    assert research_question_payload(selected)["estimator_execution_contract"]["estimator_id"] == estimator_id
    refs = prepare(**args)
    assert len(refs) == 4
    for mode in ("free_planning", "same_workflow"):
        assert json.loads(Path(refs[mode]["path"]).read_bytes())["estimator_ids"] == [estimator_id]


@pytest.mark.parametrize("mode", MODES)
def test_generated_config_reaches_existing_draw_transport_without_inference(tmp_path, monkeypatch, capsys, mode):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    for language in ("PYTHON", "R"):
        monkeypatch.delenv("AI_STATISTICIAN_NATIVE_" + language + "_CONFIG", raising=False)
    args = inputs(tmp_path, monkeypatch)
    refs = prepare(**args)
    requests = []

    class Opener:
        def open(self, request, *, timeout):
            requests.append(json.loads(request.data))
            raise HTTPError(request.full_url, 400, "Fixture failure", {}, BytesIO(b"opaque transport failure"))

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    assert draw_main(["--config", refs[mode]["path"], "--out", str(tmp_path / "draw")]) == 1
    observed = json.loads(capsys.readouterr().out)
    assert observed["status"] == "FAILED" and observed["final_material_ref"] is None
    assert observed["scientific_evaluation_performed"] is False
    assert observed["local_model_usage"]["attempted_requests"] == 1
    assert len(requests) == 1 and requests[0]["model"] == "Qwen3-4B-Instruct-2507"
    assert requests[0]["max_tokens"] == 1703 and requests[0]["temperature"] == 0.23
    if mode in {"free_planning", "same_workflow"}:
        assert requests[0]["tool_choice"] == "required"
        assert requests[0]["parallel_tool_calls"] is True
    else:
        assert "tools" not in requests[0] and "tool_choice" not in requests[0]
        assert requests[0]["response_format"]["type"] == "json_schema"
    assert "90211" not in json.dumps(requests[0])
