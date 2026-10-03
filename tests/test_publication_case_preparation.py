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
from ai_statistician.research_source_library import load_research_source_snapshot
from benchmarks.publication_case_candidates.tsci_b1_card.prepare_configs import MODES, prepare
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
    return dict(out=tmp_path / "prepared", deployment=deployment, sources=sources, source_execution=execution,
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
        assert config["question_id"] == "tsci_b1_card_integrated_candidate_v2"
        assert config["backend"] == {"base_url": "http://127.0.0.1:8081/v1", "timeout_s": 211.0}
        assert config["source_execution_ref"]["path"] == str(args["source_execution"].resolve())
        assert all(row["provider_name"] == row["model_tier"] == "local"
                   and row["max_tokens"] == 1703 and row["temperature"] == 0.23
                   for row in config["roles"].values())
        assert config["roles"]["theory"]["serious_max_tokens"] == 1703
        if mode in {"free_planning", "same_workflow"}:
            assert config["request"]["max_tokens"] == 1703
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


@pytest.mark.parametrize("mode", MODES)
def test_generated_config_reaches_existing_draw_transport_without_inference(tmp_path, monkeypatch, capsys, mode):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
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
    assert "90211" not in json.dumps(requests[0])
