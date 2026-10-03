from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.scientific_sandbox import (
    SCIENTIFIC_NATIVE_R_PROFILE, ScientificEstimatorBinding,
    discover_scientific_sandbox_runtime, execute_scientific_sandbox,
    generated_code_draft_json_schema, load_native_r_runtime, scientific_sandbox_contract,
)
from ai_statistician.theory_workspace import TheoryScratchpadConfig, execute_theory_scratchpad_tool, read_theory_scratch_execution


@pytest.fixture
def native_runtime(monkeypatch):
    path = os.environ.get("AI_STATISTICIAN_TEST_NATIVE_R_CONFIG", "")
    if not path:
        pytest.skip("explicit test native R environment is not configured")
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_R_CONFIG", path)
    runtime = discover_scientific_sandbox_runtime()
    assert runtime.native_r_available, runtime.native_r_errors
    return runtime


def test_explicit_native_r_never_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_R_CONFIG", str(tmp_path / "missing.json"))
    runtime = discover_scientific_sandbox_runtime()
    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path, artifact_id="no-fallback", language="r",
        execution_profile=SCIENTIFIC_NATIVE_R_PROFILE, runtime=runtime,
        dependencies=[], code="run_sandbox <- function(seed, replicates) list(n=1)",
        seed=0, replicates=1, timeout_s=5,
    )
    assert result.status == "REJECTED_CONTRACT"
    assert result.backend == "native_r"
    assert not result.execution_attempted
    assert any("configuration rejected" in error for error in result.errors)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("change,match", [
    ({"interpreter_executable_sha256": "0" * 64}, "sha256 mismatch"),
    ({"interpreter_executable_relative_path": "../runtime"}, "inside environment_root"),
    ({"runtime_environment": {"PATH": "/tmp"}}, "controlled entry"),
    ({"package_versions": {"unsafe-name": "1", "jsonlite": "2"}}, "package names"),
    ({"package_versions": {"jsonlite": "2", "JSONLITE": "2"}}, "unique normalized"),
])
def test_native_r_resource_validation(tmp_path, change, match):
    executable = tmp_path / "Rscript"
    executable.write_bytes(b"fixture")
    executable.chmod(0o700)
    payload = dict(schema_version=1, environment_root=str(tmp_path),
        interpreter_executable_relative_path="Rscript",
        interpreter_executable_sha256=hashlib.sha256(b"fixture").hexdigest(),
        runtime_version="4.4.2", package_versions={"jsonlite": "2.0.0"})
    payload.update(change)
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match=match):
        load_native_r_runtime(path)


def test_native_r_packages_are_environment_owned_not_case_rules(native_runtime):
    contract = scientific_sandbox_contract(native_runtime)["profiles"][SCIENTIFIC_NATIVE_R_PROFILE]
    assert contract["runtime_available"]
    assert contract["package_versions"] == dict(native_runtime.native_r.package_versions)
    schema = generated_code_draft_json_schema(artifact_properties={}, artifact_required=())
    assert SCIENTIFIC_NATIVE_R_PROFILE in schema["properties"]["execution_profile"]["enum"]
    names = schema["properties"]["dependencies"]["items"]["enum"]
    assert all(name in names for name, _ in native_runtime.native_r.package_versions)


def execute(tmp_path, runtime, code, **kwargs):
    return execute_scientific_sandbox(
        sandbox_dir=tmp_path, artifact_id="native-fixture", language="r",
        execution_profile=SCIENTIFIC_NATIVE_R_PROFILE, runtime=runtime,
        code=code, dependencies=kwargs.pop("dependencies", []), seed=7, replicates=3,
        timeout_s=30, **kwargs,
    )


def test_native_r_executes_library_project_and_exact_bound_estimator(tmp_path, native_runtime):
    estimator = "source('helper.R')\nrun_estimator <- function(request) list(estimate=transform(request$x))"
    binding = ScientificEstimatorBinding(
        artifact_id="reviewed-source", language="r", code=estimator,
        code_hash=stable_hash(estimator), dependencies=("ranger",),
        project_files=({"path": "helper.R", "content": "transform <- function(x) x * 2"},),
    )
    code = '''run_sandbox <- function(seed, replicates, estimators) {
      fit <- ranger::ranger(Sepal.Length ~ ., data=iris, num.trees=2, seed=seed, num.threads=1)
      values <- vapply(seq_len(replicates), function(i) estimators[["reviewed-source"]](list(x=i))$estimate, numeric(1))
      list(total=sum(values), trees=fit$num.trees)
    }'''
    result = execute(tmp_path, native_runtime, code, dependencies=["ranger"], estimator_bindings=[binding])
    assert result.status == "EXECUTED", (result.errors, result.stderr_summary)
    assert result.metrics == {"total": 12, "trees": 2}
    assert result.estimator_invocation_counts == {"reviewed-source": 3}
    assert len(result.estimator_invocation_samples["reviewed-source"]) == 3
    assert result.code_hash == stable_hash(code)
    assert result.estimator_code_hashes == {"reviewed-source": stable_hash(estimator)}
    assert Path(result.code_path).read_bytes().decode() == code
    request = json.loads(Path(result.request_path).read_bytes())
    assert request["runtime"]["native_r"]["configuration_sha256"] == native_runtime.native_r.config_sha256
    assert request["network_access"] is False
    assert request["secret_environment_inherited"] is False
    assert "R_LIBS_USER" in result.subprocess_environment_keys
    assert result.isolation_provider == "macos_sandbox_exec+native_r"


def test_native_r_raw_error_and_author_revision_are_separate_exact_attempts(tmp_path, native_runtime):
    broken = "run_sandbox <- function(seed, replicates) { stop('original author error') }"
    first = execute(tmp_path, native_runtime, broken)
    assert first.status == "FAILED"
    assert "original author error" in ";".join(first.errors)
    fixed = "run_sandbox <- function(seed, replicates) list(n=replicates)"
    second = execute(tmp_path, native_runtime, fixed)
    assert second.status == "EXECUTED", second.errors
    assert first.code_path != second.code_path
    assert Path(first.code_path).read_bytes().decode() == broken
    assert Path(second.code_path).read_bytes().decode() == fixed
    assert second.metrics == {"n": 3}


def test_native_r_bound_error_returns_exact_owner(tmp_path, native_runtime):
    source = "run_estimator <- function(request) stop('estimator diagnostic')"
    result = execute(tmp_path, native_runtime,
        'run_sandbox <- function(seed, replicates, estimators) estimators[["owner"]](list(x=1))',
        estimator_bindings=[ScientificEstimatorBinding(artifact_id="owner", language="r",
            code=source, code_hash=stable_hash(source))])
    assert result.status == "FAILED"
    assert result.estimator_runtime_failure_ids == ("owner",)
    assert "estimator diagnostic" in result.estimator_runtime_errors[0]


def test_hidden_harness_uses_its_own_explicit_native_profile(tmp_path, native_runtime):
    from ai_statistician.research_gold_evaluation import _run_hidden_scientific_harness
    source = "run_estimator <- function(request) list(estimate=request$x * 2)"
    result = _run_hidden_scientific_harness(sandbox_dir=tmp_path, artifact_id="hidden-fixture",
        harness_language="r", harness_execution_profile=SCIENTIFIC_NATIVE_R_PROFILE,
        harness_code='run_sandbox <- function(seed, replicates, estimators) estimators[["candidate"]](list(x=7))',
        harness_dependencies=[], estimator_binding=ScientificEstimatorBinding(
            artifact_id="candidate", language="r", code=source, code_hash=stable_hash(source)),
        seed=0, replicates=1, timeout_s=30)
    assert result["status"] == "EXECUTED", result["errors"]
    assert result["metrics"] == {"estimate": 14}
    assert result["estimator_invocation_counts"] == {"candidate": 1}
    assert result["execution_profile"] == SCIENTIFIC_NATIVE_R_PROFILE


def test_research_runtime_dispatch_preserves_native_profile(tmp_path, native_runtime):
    from ai_statistician.research_agent_runtime import _run_generated_simulation_sandbox
    from ai_statistician.scientific_project import scientific_project_hash
    estimator = "run_estimator <- function(request) list(estimate=request$x * 2)"
    prototype, _ = _run_generated_simulation_sandbox(
        sandbox_dir=tmp_path, simulation_id="native-runtime-fixture",
        code_draft=dict(language="r", execution_profile=SCIENTIFIC_NATIVE_R_PROFILE,
            dependencies=[], entrypoint="run_sandbox", required_estimator_ids=["candidate"],
            code='run_sandbox <- function(seed, replicates, estimators) estimators[["candidate"]](list(x=7))'),
        upstream_algorithm_handoff={"exact_algorithm_artifacts": [dict(
            estimator_id="candidate", language="r", dependencies=[], exact_source_code=estimator,
            exact_source_hash=stable_hash(estimator),
            exact_project_hash=scientific_project_hash(language="r", code=estimator))]},
        n_runs=1, seed=0, timeout_s=30)
    assert prototype["backend"] == "native_r"
    assert prototype["executor_profile"] == SCIENTIFIC_NATIVE_R_PROFILE
    assert prototype["estimator_invocation_counts"] == {"candidate": 1}


def test_native_r_scratch_script_keeps_raw_output(tmp_path, native_runtime):
    source = "cat('local source feedback', seed, '\\n'); stop('scratch diagnostic')"
    result, ref = execute_theory_scratchpad_tool(
        tool_input=dict(language="r", execution_profile=SCIENTIFIC_NATIVE_R_PROFILE,
                        dependencies=[], code=source),
        scratchpad=TheoryScratchpadConfig(tmp_path, seed=19, replicates=1, timeout_s=30),
        sandbox_binding=("native-r-scratch",), artifact_id="scratch", run_index=1,
        owner_label="TheoryDeveloper",
    )
    assert result.content["status"] == "FAILED"
    assert "local source feedback 19" in result.content["stdout_summary"]
    assert "scratch diagnostic" in result.content["stderr_summary"]
    assert ref["runtime_edited_source"] is False
    assert ref["execution_profile"] == SCIENTIFIC_NATIVE_R_PROFILE
    stored = read_theory_scratch_execution(ref=ref, scratch_root=tmp_path)
    assert stored["result"]["stdout"] == result.content["stdout_summary"]
    assert stored["result"]["stderr"] == "scratch diagnostic\n"


def test_native_r_cannot_promote_changed_source(tmp_path, native_runtime):
    result = execute(tmp_path, native_runtime,
        "run_sandbox <- function(seed, replicates) { writeLines('changed', 'main.R'); list(n=1) }")
    assert result.status == "FAILED"
    assert any("changed immutable input" in error for error in result.errors)


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_process_observations_never_follow_links_or_nonregular_files(tmp_path, kind):
    from ai_statistician.research_source_library import _bounded_execution_text
    outside = tmp_path / "outside.txt"
    outside.write_text("private fixture data")
    output = tmp_path / "output.txt"
    if kind == "symlink":
        output.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, output)
    else:
        os.mkfifo(output)
    text, errors = _bounded_execution_text(output, 1024)
    assert text == ""
    assert errors
    assert outside.read_text() == "private fixture data"


def test_native_r_cannot_write_trusted_adapter_or_envelope(tmp_path, native_runtime):
    result = execute(tmp_path, native_runtime,
        "run_sandbox <- function(seed, replicates) { writeLines('changed', '../../native_execution.R'); list(n=1) }")
    assert result.status == "FAILED"
    assert "changed" not in Path(result.request_path).read_text()
    assert Path(result.request_path).parent.joinpath("native_execution.R").read_text() != "changed\n"


@pytest.mark.parametrize("value", ["NA_real_", "Inf", "as.environment(list(x=1))"])
def test_native_r_rejects_non_json_metrics(tmp_path, native_runtime, value):
    result = execute(tmp_path, native_runtime,
        f"run_sandbox <- function(seed, replicates) list(n={value})")
    assert result.status == "FAILED"
    assert any("non-finite or non-JSON" in error for error in result.errors)
