from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.scientific_sandbox import (
    SCIENTIFIC_NATIVE_PYTHON_PROFILE, ScientificEstimatorBinding,
    ScientificInputArtifactBinding, discover_scientific_sandbox_runtime,
    execute_scientific_sandbox, generated_code_draft_json_schema,
    load_native_scientific_runtime, scientific_sandbox_contract,
)


@pytest.fixture
def native_runtime(monkeypatch):
    path = os.environ.get("AI_STATISTICIAN_TEST_NATIVE_PYTHON_CONFIG", "")
    if not path:
        pytest.skip("explicit test native Python environment is not configured")
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_PYTHON_CONFIG", path)
    runtime = discover_scientific_sandbox_runtime()
    assert runtime.native_available("python"), runtime.native_python_errors
    return runtime


def execute(tmp_path, runtime, code, **kwargs):
    return execute_scientific_sandbox(
        sandbox_dir=tmp_path, artifact_id="native-python-fixture", language="python",
        execution_profile=SCIENTIFIC_NATIVE_PYTHON_PROFILE, runtime=runtime,
        code=code, dependencies=kwargs.pop("dependencies", []), seed=7, replicates=3,
        timeout_s=30, **kwargs,
    )


def test_explicit_native_python_never_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_STATISTICIAN_NATIVE_PYTHON_CONFIG", str(tmp_path / "missing.json"))
    runtime = discover_scientific_sandbox_runtime()
    result = execute(tmp_path, runtime, "def run_sandbox(seed, replicates): return {'n': 1}")
    assert result.status == "REJECTED_CONTRACT"
    assert result.backend == "native_python"
    assert not result.execution_attempted
    assert any("configuration rejected" in error for error in result.errors)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("change,match", [
    ({"interpreter_executable_sha256": "0" * 64}, "sha256 mismatch"),
    ({"runtime_language": "r"}, "language mismatch"),
    ({"runtime_environment": {"PATH": "/tmp"}}, "controlled entry"),
    ({"package_versions": {"../unsafe": "1"}}, "package names"),
    ({"package_versions": {"scikit_learn": "1", "Scikit.Learn": "1"}}, "unique normalized"),
])
def test_native_python_resource_validation(tmp_path, change, match):
    executable = tmp_path / "python"
    executable.write_bytes(b"fixture")
    executable.chmod(0o700)
    payload = dict(schema_version=1, runtime_language="python", environment_root=str(tmp_path),
        interpreter_executable_relative_path="python",
        interpreter_executable_sha256=hashlib.sha256(b"fixture").hexdigest(),
        runtime_version="3.11.15", package_versions={"scikit-learn": "1.5.0"})
    payload.update(change)
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match=match):
        load_native_scientific_runtime(path, language="python")


def test_native_python_packages_are_operator_owned(native_runtime):
    contract = scientific_sandbox_contract(native_runtime)["profiles"][SCIENTIFIC_NATIVE_PYTHON_PROFILE]
    assert contract["runtime_available"]
    assert "stepmix" in contract["python_dependencies"]
    assert contract["package_versions"] == dict(native_runtime.native_python.package_versions)
    schema = generated_code_draft_json_schema(artifact_properties={}, artifact_required=())
    assert SCIENTIFIC_NATIVE_PYTHON_PROFILE in schema["properties"]["execution_profile"]["enum"]
    assert "stepmix" in schema["properties"]["dependencies"]["items"]["enum"]


def test_native_python_executes_library_project_bound_estimator_and_input(tmp_path, native_runtime):
    estimator = "from helper import transform\ndef run_estimator(request): return {'estimate': transform(request['x'])}"
    binding = ScientificEstimatorBinding(
        artifact_id="reviewed-source", language="python", code=estimator,
        code_hash=stable_hash(estimator), dependencies=("numpy",),
        project_files=({"path": "helper.py", "content": "import numpy as np\ndef transform(x): return np.array(x) * 2"},),
    )
    data = '{"x": [1, 2, 3]}'
    result = execute(tmp_path, native_runtime, '''import json
from helper import count
from stepmix.stepmix import StepMix
def run_sandbox(seed, replicates, estimators, artifacts):
    values = json.loads(artifacts['data']['content'])
    result = estimators['reviewed-source'](values)
    return {'values': result['estimate'], 'count': count(), 'components': StepMix(n_components=2).n_components}
''', dependencies=["stepmix"], estimator_bindings=[binding],
        project_files=[{"path": "helper.py", "content": "def count(): return 3"}],
        input_artifacts=[ScientificInputArtifactBinding("data", data, hashlib.sha256(data.encode()).hexdigest(), "application/json")])
    assert result.status == "EXECUTED", (result.errors, result.stderr_summary)
    assert result.metrics == {"values": [2, 4, 6], "count": 3, "components": 2}
    assert result.estimator_invocation_counts == {"reviewed-source": 1}
    assert result.estimator_code_hashes == {"reviewed-source": stable_hash(estimator)}
    assert result.input_artifact_hashes == {"data": hashlib.sha256(data.encode()).hexdigest()}
    request = json.loads(Path(result.request_path).read_bytes())
    assert request["runtime"]["native_python"]["configuration_sha256"] == native_runtime.native_python.config_sha256
    assert request["network_access"] is False
    assert request["secret_environment_inherited"] is False
    assert "__PYVENV_LAUNCHER__" in result.subprocess_environment_keys
    assert result.isolation_provider == "macos_sandbox_exec+native_python"


def test_native_python_raw_error_and_new_source_remain_separate(tmp_path, native_runtime):
    broken = "def run_sandbox(seed, replicates): raise ValueError('original author diagnostic')"
    first = execute(tmp_path, native_runtime, broken)
    assert first.status == "FAILED"
    assert "ValueError: original author diagnostic" in first.stderr_summary
    fixed = "def run_sandbox(seed, replicates): return {'n': replicates}"
    second = execute(tmp_path, native_runtime, fixed)
    assert second.status == "EXECUTED", second.errors
    assert first.code_path != second.code_path
    assert Path(first.code_path).read_bytes().decode() == broken
    assert Path(second.code_path).read_bytes().decode() == fixed


def test_native_python_bound_error_returns_exact_owner(tmp_path, native_runtime):
    source = "def run_estimator(request): raise ValueError('estimator diagnostic')"
    result = execute(tmp_path, native_runtime,
        "def run_sandbox(seed, replicates, estimators): return estimators['owner']({'x': 1})",
        estimator_bindings=[ScientificEstimatorBinding(artifact_id="owner", language="python",
            code=source, code_hash=stable_hash(source))])
    assert result.status == "FAILED"
    assert result.estimator_runtime_failure_ids == ("owner",)
    assert "estimator diagnostic" in result.estimator_runtime_errors[0]


@pytest.mark.parametrize("kind", ["runtime", "package"])
def test_native_python_versions_are_checked_before_source(tmp_path, native_runtime, kind):
    payload = json.loads(Path(native_runtime.native_python.config_path).read_bytes())
    if kind == "runtime":
        payload["runtime_version"] = "0.0.0"
    else:
        payload["package_versions"]["numpy"] = "0.0.0"
    config = tmp_path / "runtime.json"
    config.write_text(json.dumps(payload))
    runtime = replace(native_runtime, native_python=load_native_scientific_runtime(config, language="python"))
    result = execute(tmp_path, runtime, "raise ValueError('must not run source')", entrypoint=None)
    assert result.status == "FAILED"
    assert "version mismatch" in result.stderr_summary
    assert "must not run source" not in result.stderr_summary


def test_native_python_configuration_drift_is_rejected(tmp_path, native_runtime, monkeypatch):
    from ai_statistician import scientific_sandbox
    config = tmp_path / "runtime.json"
    config.write_bytes(Path(native_runtime.native_python.config_path).read_bytes())
    runtime = replace(native_runtime, native_python=load_native_scientific_runtime(config, language="python"))
    original_run = scientific_sandbox.subprocess.run
    def run(*args, **kwargs):
        completed = original_run(*args, **kwargs)
        payload = json.loads(config.read_bytes())
        payload["runtime_version"] = "0.0.0"
        config.write_text(json.dumps(payload))
        return completed
    monkeypatch.setattr(scientific_sandbox.subprocess, "run", run)
    result = execute(tmp_path, runtime, "raise ValueError('must not run source')", entrypoint=None)
    assert result.status == "FAILED"
    assert any("configuration changed before execution" in error for error in result.errors)
    assert "must not run source" not in result.stderr_summary


def test_native_python_never_inherits_host_secret_environment(tmp_path, native_runtime, monkeypatch):
    monkeypatch.setenv("HOST_FIXTURE_SECRET", "synthetic-test-only")
    result = execute(tmp_path, native_runtime,
        "import os\ndef run_sandbox(seed, replicates): return {'present': 'HOST_FIXTURE_SECRET' in os.environ}")
    assert result.status == "EXECUTED", result.errors
    assert result.metrics == {"present": False}
    assert "HOST_FIXTURE_SECRET" not in result.subprocess_environment_keys


@pytest.mark.parametrize("value", ["float('nan')", "set([1])"])
def test_native_python_rejects_non_json_metrics(tmp_path, native_runtime, value):
    result = execute(tmp_path, native_runtime, f"def run_sandbox(seed, replicates): return {{'x': {value}}}")
    assert result.status == "FAILED"
    assert result.errors


def test_native_python_cannot_write_trusted_adapter(tmp_path, native_runtime):
    result = execute(tmp_path, native_runtime,
        "def run_sandbox(seed, replicates):\n    open('../../native_execution.py', 'w').write('changed')\n    return {'n': 1}")
    assert result.status == "FAILED"
    assert Path(result.request_path).parent.joinpath("native_execution.py").read_text() != "changed"


@pytest.mark.parametrize("target", ["main.py", "helper.py"])
def test_native_python_cannot_promote_changed_project(tmp_path, native_runtime, target):
    result = execute(tmp_path, native_runtime,
        f"def run_sandbox(seed, replicates):\n    open('{target}', 'w').write('changed')\n    return {{'n': 1}}",
        project_files=[{"path": "helper.py", "content": "x = 1"}])
    assert result.status == "FAILED"
    assert any("changed immutable input" in error for error in result.errors)


def test_native_python_script_keeps_raw_feedback_and_support_path(tmp_path, native_runtime):
    result = execute(tmp_path, native_runtime, "x = 1", entrypoint=None, script_path="probe.py",
        project_files=[{"path": "probe.py", "content": "print('source feedback', seed)\nraise ValueError('scratch diagnostic')"}])
    assert result.status == "FAILED"
    assert "source feedback 7" in result.stdout_summary
    assert "scratch diagnostic" in result.stderr_summary


def test_native_python_hidden_harness_keeps_profile(tmp_path, native_runtime):
    from ai_statistician.research_gold_evaluation import _run_hidden_scientific_harness
    source = "def run_estimator(request): return {'estimate': request['x'] * 2}"
    result = _run_hidden_scientific_harness(sandbox_dir=tmp_path, artifact_id="hidden-fixture",
        harness_language="python", harness_execution_profile=SCIENTIFIC_NATIVE_PYTHON_PROFILE,
        harness_code="def run_sandbox(seed, replicates, estimators): return estimators['candidate']({'x': 7})",
        harness_dependencies=[], estimator_binding=ScientificEstimatorBinding(
            artifact_id="candidate", language="python", code=source, code_hash=stable_hash(source)),
        seed=0, replicates=1, timeout_s=30)
    assert result["status"] == "EXECUTED", result["errors"]
    assert result["metrics"] == {"estimate": 14}
    assert result["execution_profile"] == SCIENTIFIC_NATIVE_PYTHON_PROFILE


def test_native_python_outer_runtime_keeps_profile(tmp_path, native_runtime):
    from ai_statistician.research_agent_runtime import _run_generated_simulation_sandbox
    from ai_statistician.scientific_project import scientific_project_hash
    source = "def run_estimator(request): return {'estimate': request['x'] * 2}"
    prototype, _ = _run_generated_simulation_sandbox(
        sandbox_dir=tmp_path, simulation_id="native-runtime-fixture",
        code_draft=dict(language="python", execution_profile=SCIENTIFIC_NATIVE_PYTHON_PROFILE,
            dependencies=[], entrypoint="run_sandbox", required_estimator_ids=["candidate"],
            code="def run_sandbox(seed, replicates, estimators): return estimators['candidate']({'x': 7})"),
        upstream_algorithm_handoff={"exact_algorithm_artifacts": [dict(
            estimator_id="candidate", language="python", dependencies=[], exact_source_code=source,
            exact_source_hash=stable_hash(source),
            exact_project_hash=scientific_project_hash(language="python", code=source))]},
        n_runs=1, seed=0, timeout_s=30)
    assert prototype["backend"] == "native_python"
    assert prototype["executor_profile"] == SCIENTIFIC_NATIVE_PYTHON_PROFILE
    assert prototype["estimator_invocation_counts"] == {"candidate": 1}


def test_native_python_theory_scratch_uses_selected_runtime(tmp_path, native_runtime):
    from ai_statistician.theory_workspace import (
        TheoryScratchpadConfig, execute_theory_scratchpad_tool, read_theory_scratch_execution,
    )
    result, ref = execute_theory_scratchpad_tool(
        tool_input=dict(language="python", execution_profile=SCIENTIFIC_NATIVE_PYTHON_PROFILE,
            dependencies=["stepmix"], code="from stepmix.stepmix import StepMix\nprint(StepMix(n_components=2).n_components)"),
        scratchpad=TheoryScratchpadConfig(tmp_path, seed=19, replicates=1, timeout_s=30),
        sandbox_binding=("native-python-scratch",), artifact_id="scratch", run_index=1,
        owner_label="TheoryDeveloper")
    assert result.content["status"] == "EXECUTED", result.content
    assert result.content["stdout_summary"] == "2\n"
    assert ref["runtime_edited_source"] is False
    assert ref["execution_profile"] == SCIENTIFIC_NATIVE_PYTHON_PROFILE
    stored = read_theory_scratch_execution(ref=ref, scratch_root=tmp_path)
    assert stored["result"]["stdout"] == result.content["stdout_summary"]
