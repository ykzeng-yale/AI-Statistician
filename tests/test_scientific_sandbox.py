from __future__ import annotations

import json
from pathlib import Path

import pytest

import ai_statistician.research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import ToolCallRecord
from ai_statistician.algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
    validate_algorithm_engineer_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.scientific_sandbox import (
    SCIENTIFIC_SANDBOX_BOUNDARY,
    ScientificEstimatorBinding,
    ScientificSandboxExecution,
    ScientificSandboxRuntime,
    discover_scientific_sandbox_runtime,
    execute_scientific_sandbox,
    generated_code_draft_json_schema,
    generated_code_execution_contract_errors,
    normalized_generated_code_profile,
    scientific_python_safety_errors,
)
from ai_statistician.simulation_engineer_llm import (
    SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
    _validate_simulation_estimator_selection,
    validate_simulation_engineer_packet,
)


def test_generated_code_contract_keeps_stdlib_default_and_requires_r_wasm() -> None:
    assert normalized_generated_code_profile(None, language="python") == "stdlib"
    assert normalized_generated_code_profile(None, language="r") == "scientific_wasm"
    assert generated_code_execution_contract_errors(
        {
            "language": "python",
            "execution_profile": "scientific_wasm",
            "dependencies": ["numpy"],
            "entrypoint": "run_sandbox",
            "code": "def run_sandbox(seed, replicates):\n    return {'n': replicates}",
        }
    ) == []
    assert "generated R code requires execution_profile scientific_wasm" in (
        generated_code_execution_contract_errors(
            {
                "language": "r",
                "execution_profile": "stdlib",
                "dependencies": [],
                "entrypoint": "run_sandbox",
                "code": "run_sandbox <- function(seed, replicates) list(n=replicates)",
            }
        )
    )


def test_generated_code_contract_rejects_string_dependencies_before_execution() -> None:
    errors = generated_code_execution_contract_errors(
        {
            "language": "python",
            "execution_profile": "scientific_wasm",
            "dependencies": "numpy, scipy",
            "entrypoint": "run_sandbox",
            "code": "def run_sandbox(seed, replicates):\n    return {'n': replicates}",
        }
    )

    assert "generated code dependencies must be an array" in errors


def test_generated_code_schema_uses_one_compact_runtime_validated_shape() -> None:
    schema = generated_code_draft_json_schema(
        artifact_properties={"artifact_id": {"type": "string"}},
        artifact_required=["artifact_id"],
    )

    assert "anyOf" not in schema
    assert schema["properties"]["execution_profile"]["enum"] == [
        "stdlib",
        "scientific_wasm",
    ]
    assert schema["properties"]["language"]["enum"] == ["python", "r"]
    assert "dependencies" in schema["required"]
    assert schema["properties"]["dependencies"]["items"]["enum"] == [
        "numpy",
        "scipy",
        "pandas",
        "scikit-learn",
        "statsmodels",
        "base",
        "stats",
        "utils",
        "methods",
    ]


def test_scientific_python_guard_requires_declared_packages_and_blocks_bridges() -> None:
    undeclared = scientific_python_safety_errors(
        "import numpy as np\n\ndef run_sandbox(seed, replicates):\n    return {'n': replicates}",
        dependencies=[],
    )
    bridged = scientific_python_safety_errors(
        "import js\n\ndef run_sandbox(seed, replicates):\n    return {'n': replicates}",
        dependencies=[],
    )
    stdlib = scientific_python_safety_errors(
        "import json\n"
        "from collections import defaultdict\n"
        "from typing import Any\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    values: Any = defaultdict(int)\n"
        "    values['n'] = replicates\n"
        "    return json.loads(json.dumps(dict(values)))",
        dependencies=[],
    )
    assert (
        "generated scientific Python third-party import is not declared: numpy"
        in undeclared
    )
    assert (
        "generated scientific Python import is forbidden in the isolated runtime: js"
        in bridged
    )
    assert stdlib == []


def test_scientific_runtime_unavailable_fails_closed_without_execution(
    tmp_path: Path,
) -> None:
    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="missing-runtime",
        language="r",
        code="run_sandbox <- function(seed, replicates) list(n=replicates)",
        dependencies=["base"],
        seed=7,
        replicates=4,
        timeout_s=2,
        runtime=ScientificSandboxRuntime(),
    )

    assert result.status == "RUNTIME_UNAVAILABLE"
    assert result.execution_attempted is False
    assert result.metrics == {}
    assert list(tmp_path.iterdir()) == []


def test_live_standalone_source_reports_missing_callable_export(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")

    source = (
        "def run_sandbox(seed, replicates):\n"
        "    def run_estimator(request):\n"
        "        return {'estimate': request['value']}\n"
        "    return run_estimator({'value': seed})\n"
    )
    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="nested-estimator-export",
        language="python",
        code=source,
        dependencies=[],
        seed=7,
        replicates=4,
        timeout_s=60,
        required_callable_exports=("run_estimator",),
    )

    assert result.status == "FAILED"
    assert result.execution_attempted is True
    assert result.required_callable_exports == ("run_estimator",)
    assert any(
        "generated source did not export callable run_estimator" in error
        for error in result.errors
    )
    request = json.loads(Path(result.request_path).read_text(encoding="utf-8"))
    assert request["required_callable_exports"] == ["run_estimator"]


def test_estimator_binding_rejects_tampered_source_hash_before_execution(
    tmp_path: Path,
) -> None:
    algorithm = (
        "def run_estimator(request):\n"
        "    return {'estimate': request['value']}\n"
    )
    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="tampered-estimator",
        language="python",
        code=(
            "def run_sandbox(seed, replicates, estimators):\n"
            "    return estimators['candidate']({'value': seed})\n"
        ),
        dependencies=[],
        seed=7,
        replicates=4,
        timeout_s=2,
        runtime=ScientificSandboxRuntime(),
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language="python",
                code=algorithm,
                code_hash=stable_hash(algorithm + "# changed"),
            ),
        ),
    )

    assert result.status == "REJECTED_CONTRACT"
    assert result.execution_attempted is False
    assert result.invocation_mode == "estimator_bound"
    assert any("source hash mismatch" in error for error in result.errors)
    assert any(
        "source hash mismatch" in error for error in result.estimator_binding_errors
    )
    assert list(tmp_path.iterdir()) == []


def test_algorithm_and_simulation_packets_accept_declared_r_drafts() -> None:
    r_draft = {
        "language": "r",
        "execution_profile": "scientific_wasm",
        "dependencies": ["base", "stats"],
        "entrypoint": "run_sandbox",
        "code": (
            "run_sandbox <- function(seed, replicates) "
            "list(mean=mean(seq_len(replicates)))"
        ),
    }
    algorithm_packet = {
        "implementation_targets": [
            {"estimator_id": "r-estimator", "registered_template_hint": "none"}
        ],
        "sandbox_code_drafts": [
            {"estimator_id": "r-estimator", **r_draft}
        ],
        "next_actions": [{"owner_agent": "AlgorithmEngineer"}],
        "execution_evidence_status": (
            ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE
        ),
        "sandbox_executed": False,
        "production_registered": False,
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }
    simulation_packet = {
        "simulation_targets": [{"procedure_id": "r-simulation"}],
        "simulation_code_drafts": [
            {
                "simulation_id": "r-simulation",
                "required_estimator_ids": [],
                **r_draft,
            }
        ],
        "runtime_execution_plan": {
            "registered_simulator": "ResearchSimulator.run"
        },
        "critic_findings": [{"finding": "inspect tails"}],
        "next_actions": [{"owner_agent": "SimulationEngineer"}],
        "simulation_evidence_status": (
            SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE
        ),
        "simulations_executed": False,
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }

    assert validate_algorithm_engineer_packet(algorithm_packet) == []
    assert validate_simulation_engineer_packet(simulation_packet) == []


def test_simulation_estimator_selection_requires_a_known_handoff_subset() -> None:
    packet = {
        "simulation_code_drafts": [
            {
                "simulation_id": "confirmatory-dgp",
                "required_estimator_ids": ["candidate-a"],
            }
        ]
    }

    assert _validate_simulation_estimator_selection(
        packet,
        upstream_estimator_ids=("candidate-a", "candidate-b"),
    ) == []

    packet["simulation_code_drafts"][0]["required_estimator_ids"] = []
    assert any(
        "must select at least one" in error
        for error in _validate_simulation_estimator_selection(
            packet,
            upstream_estimator_ids=("candidate-a", "candidate-b"),
        )
    )

    packet["simulation_code_drafts"][0]["required_estimator_ids"] = [
        "unknown-candidate"
    ]
    assert any(
        "selected unknown upstream estimator ids" in error
        for error in _validate_simulation_estimator_selection(
            packet,
            upstream_estimator_ids=("candidate-a", "candidate-b"),
        )
    )


def test_runtime_dispatch_preserves_existing_metric_and_evidence_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    code = "run_sandbox <- function(seed, replicates) list(n=replicates)"
    code_path = tmp_path / "draft.R"
    code_path.write_text(code, encoding="utf-8")
    metrics = {"mean": 0.25, "n": 8}
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(metrics), encoding="utf-8")
    envelope_path = tmp_path / "execution-envelope.json"
    envelope = {"ok": True, "metrics": metrics}
    envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
    execution = ScientificSandboxExecution(
        status="EXECUTED",
        language="r",
        execution_profile="scientific_wasm",
        backend="webr",
        isolation_provider="test-wasm-isolation",
        dependencies=("base", "stats"),
        execution_attempted=True,
        returncode=0,
        metrics=metrics,
        errors=(),
        stdout_summary="",
        stderr_summary="",
        result_parse_error="",
        code_path=str(code_path),
        request_path=str(tmp_path / "request.json"),
        result_path=str(result_path),
        code_hash="code-hash",
        request_hash="request-hash",
        result_hash=stable_hash(metrics),
        subprocess_environment_keys=("HOME", "PATH"),
        resource_limits={"cpu_seconds": 5},
        execution_envelope_path=str(envelope_path),
        execution_envelope_hash=stable_hash(envelope),
        boundary=SCIENTIFIC_SANDBOX_BOUNDARY,
    )
    monkeypatch.setattr(
        runtime_module,
        "execute_scientific_sandbox",
        lambda **_kwargs: execution,
    )

    prototype, tool_call = runtime_module._run_generated_code_sandbox(
        sandbox_dir=tmp_path,
        estimator_id="r-estimator",
        spec={"id": "r-estimator"},
        code_draft={
            "language": "r",
            "execution_profile": "scientific_wasm",
            "dependencies": ["base", "stats"],
            "entrypoint": "run_sandbox",
            "code": code,
        },
        validation_context={},
        n_runs=8,
        seed=11,
        timeout_s=5,
    )

    assert prototype["prototype_status"] == "EXECUTED"
    assert prototype["smoke_passed"] is True
    assert prototype["language"] == "r"
    assert prototype["backend"] == "webr"
    assert prototype["metrics"] == metrics
    assert prototype["execution_envelope_path"] == str(envelope_path)
    assert prototype["execution_envelope_hash"] == stable_hash(envelope)
    assert prototype["metric_gate_policy_mode"] == "execution_only_no_typed_contract"
    assert tool_call.tool_name == "r.generated_algorithm_sandbox"
    assert isinstance(tool_call, ToolCallRecord)

    simulation, simulation_call = runtime_module._run_generated_simulation_sandbox(
        sandbox_dir=tmp_path,
        simulation_id="r-simulation",
        code_draft={
            "language": "r",
            "execution_profile": "scientific_wasm",
            "dependencies": ["base", "stats"],
            "entrypoint": "run_sandbox",
            "code": code,
        },
        n_runs=8,
        seed=11,
        timeout_s=5,
    )
    assert simulation["executor"] == "generated_simulation_sandbox"
    assert simulation["smoke_passed"] is True
    assert simulation_call.tool_name == "r.generated_simulation_sandbox"

    source_row = runtime_module._runtime_generated_code_semantic_review_rows(
        {"generated_simulation_sandbox_prototypes": [simulation]},
        source_subsystem="SimulationEvaluator",
    )[0]
    material, errors = runtime_module._runtime_generated_code_semantic_review_material(
        work_order={
            "source_subsystem": "SimulationEvaluator",
            "reviewed_artifacts": [
                {
                    "artifact_id": source_row["semantic_review_artifact_id"],
                    "row_hash": stable_hash(source_row),
                }
            ],
        },
        source_task={},
        source_manifest={"generated_simulation_sandbox_prototypes": [simulation]},
        theory_packet={},
        proposal_packet={},
    )
    assert errors == []
    assert material["exact_executed_artifacts"][0]["exact_result"] == metrics

    rejected, rejected_call = runtime_module._run_generated_code_sandbox(
        sandbox_dir=tmp_path,
        estimator_id="invalid-profile",
        spec={"id": "invalid-profile"},
        code_draft={
            "language": "python",
            "execution_profile": "host_process",
            "dependencies": [],
            "entrypoint": "run_sandbox",
            "code": "def run_sandbox(seed, replicates):\n    return {'n': replicates}\n",
        },
        validation_context={},
        n_runs=8,
        seed=11,
        timeout_s=5,
    )
    assert rejected["prototype_status"] == "REJECTED_UNSAFE_GENERATED_CODE"
    assert rejected["executor_profile"] == "host_process"
    assert rejected_call.inputs["execution_profile"] == "host_process"
    assert rejected["execution_attempted"] is False


def test_runtime_does_not_normalize_invalid_dependency_shape_before_validation(
    tmp_path: Path,
) -> None:
    rejected, tool_call = runtime_module._run_generated_code_sandbox(
        sandbox_dir=tmp_path,
        estimator_id="invalid-dependency-shape",
        spec={"id": "invalid-dependency-shape"},
        code_draft={
            "language": "python",
            "execution_profile": "scientific_wasm",
            "dependencies": "numpy, scipy",
            "entrypoint": "run_sandbox",
            "code": "def run_sandbox(seed, replicates):\n    return {'n': replicates}\n",
        },
        n_runs=8,
        seed=11,
        timeout_s=5,
    )

    assert rejected["prototype_status"] == "REJECTED_UNSAFE_GENERATED_CODE"
    assert "generated code dependencies must be an array" in rejected[
        "safety_errors"
    ]
    assert rejected["execution_attempted"] is False
    assert tool_call.exit_status == "rejected"


def test_runtime_simulation_dispatch_records_mechanical_estimator_reuse(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    algorithm = "def run_estimator(request):\n    return {'estimate': request['x']}\n"
    simulation = (
        "def run_sandbox(seed, replicates, estimators):\n"
        "    return estimators['candidate']({'x': seed})\n"
    )
    simulation_path = tmp_path / "simulation.py"
    simulation_path.write_text(simulation, encoding="utf-8")
    metrics = {"estimate": 11}
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(metrics), encoding="utf-8")
    execution = ScientificSandboxExecution(
        status="EXECUTED",
        language="python",
        execution_profile="scientific_wasm",
        backend="pyodide",
        isolation_provider="test-wasm-isolation",
        dependencies=(),
        execution_attempted=True,
        returncode=0,
        metrics=metrics,
        errors=(),
        stdout_summary="",
        stderr_summary="",
        result_parse_error="",
        code_path=str(simulation_path),
        request_path=str(tmp_path / "request.json"),
        result_path=str(result_path),
        code_hash=stable_hash(simulation),
        request_hash="request-hash",
        result_hash=stable_hash(metrics),
        subprocess_environment_keys=("HOME", "PATH"),
        resource_limits={"cpu_seconds": 5},
        execution_envelope_hash="execution-envelope-hash",
        estimator_code_hashes={"candidate": stable_hash(algorithm)},
        estimator_invocation_counts={"candidate": 3},
        estimator_binding_hash=stable_hash(
            {"candidate": stable_hash(algorithm)}
        ),
    )
    seen: dict[str, object] = {}

    def execute(**kwargs):
        seen.update(kwargs)
        return execution

    monkeypatch.setattr(runtime_module, "execute_scientific_sandbox", execute)
    unused_algorithm = (
        "def run_estimator(request):\n    return {'estimate': request['x'] + 1}\n"
    )
    handoff = {
        "exact_algorithm_artifacts": [
            {
                "estimator_id": "candidate",
                "language": "python",
                "dependencies": [],
                "exact_source_code": algorithm,
                "exact_source_hash": stable_hash(algorithm),
            },
            {
                "estimator_id": "unused-candidate",
                "language": "python",
                "dependencies": [],
                "exact_source_code": unused_algorithm,
                "exact_source_hash": stable_hash(unused_algorithm),
            },
        ]
    }

    prototype, _ = runtime_module._run_generated_simulation_sandbox(
        sandbox_dir=tmp_path,
        simulation_id="confirmatory-dgp",
        code_draft={
            "required_estimator_ids": ["candidate"],
            "language": "python",
            "execution_profile": "stdlib",
            "dependencies": [],
            "entrypoint": "run_sandbox",
            "code": simulation,
        },
        upstream_algorithm_handoff=handoff,
        n_runs=8,
        seed=11,
        timeout_s=5,
    )

    bindings = seen["estimator_bindings"]
    assert isinstance(bindings, tuple)
    assert len(bindings) == 1
    assert bindings[0].artifact_id == "candidate"
    assert bindings[0].code == algorithm
    assert prototype["executor_profile"] == "scientific_wasm"
    assert prototype["mechanical_estimator_invocation_verified"] is True
    assert prototype["bound_estimator_code_hashes"] == {
        "candidate": stable_hash(algorithm)
    }
    receipt = runtime_module._runtime_algorithm_handoff_receipt(
        handoff,
        simulation_rows=[prototype],
    )
    assert receipt["mechanical_estimator_invocation_verified"] is True
    assert receipt["mechanically_invoked_estimator_ids"] == ["candidate"]
    assert receipt["all_handoff_estimators_invoked"] is False


def test_estimator_abi_failure_preserves_typed_observation() -> None:
    feedback = runtime_module._generated_simulation_revision_feedback(
        manifest={
            "manifest_id": "simulation:abi-failed",
            "generated_simulation_sandbox_prototypes": [
                {
                    "simulation_id": "abi-probe",
                    "estimator_binding_errors": [
                        "accepted algorithm did not define callable run_estimator: candidate"
                    ]
                }
            ],
        },
        boundary="simulation observations are not proof evidence",
        failure_classification="accepted_algorithm_estimator_abi_failed",
    )

    assert feedback["failure_classification"] == (
        "accepted_algorithm_estimator_abi_failed"
    )
    assert feedback["generated_simulation_prototypes"][0][
        "estimator_binding_errors"
    ] == [
        "accepted algorithm did not define callable run_estimator: candidate"
    ]
    assert "target_behavior" not in feedback
    assert "success_metric" not in feedback
    assert "required_repair" not in feedback


def test_estimator_runtime_failure_preserves_typed_observation() -> None:
    feedback = runtime_module._generated_simulation_revision_feedback(
        manifest={
            "manifest_id": "simulation:runtime-failed",
            "generated_simulation_sandbox_prototypes": [
                {
                    "simulation_id": "runtime-probe",
                    "estimator_runtime_failure_ids": ["candidate"],
                    "estimator_runtime_errors": [
                        "RuntimeError: run_estimator response was non-finite"
                    ],
                }
            ],
        },
        boundary="simulation observations are not proof evidence",
        failure_classification="accepted_algorithm_estimator_runtime_failed",
    )

    assert feedback["failure_classification"] == (
        "accepted_algorithm_estimator_runtime_failed"
    )
    row = feedback["generated_simulation_prototypes"][0]
    assert row["estimator_runtime_failure_ids"] == ["candidate"]
    assert row["estimator_runtime_errors"] == [
        "RuntimeError: run_estimator response was non-finite"
    ]
    assert "target_behavior" not in feedback
    assert "success_metric" not in feedback
    assert "required_repair" not in feedback


@pytest.mark.parametrize(
    ("language", "dependencies", "code", "expected_metric"),
    [
        (
            "python",
            ["numpy"],
            "import numpy as np\n\n"
            "def run_sandbox(seed, replicates):\n"
            "    rng = np.random.default_rng(seed)\n"
            "    values = rng.normal(size=replicates)\n"
            "    return {'mean': float(np.mean(values)), 'n': int(values.size)}\n",
            "mean",
        ),
        (
            "r",
            ["base", "stats"],
            "run_sandbox <- function(seed, replicates) {\n"
            "  set.seed(seed)\n"
            "  values <- rnorm(replicates)\n"
            "  list(mean=mean(values), n=length(values), "
            "secret_present=nzchar(Sys.getenv('AI_STATISTICIAN_TEST_SECRET')), "
            "host_file_readable=webr::eval_js(\"try { "
            "process.getBuiltinModule('fs').readFileSync('/etc/hosts', 'utf8'); "
            "true } catch (error) { false }\"), "
            "child_process_started=webr::eval_js(\"try { "
            "const cp = process.getBuiltinModule('child_process'); "
            "const attempt = cp.spawnSync(process.execPath, ['-e', '']); "
            "!attempt.error && attempt.status === 0 "
            "} catch (error) { false }\"))\n"
            "}\n",
            "mean",
        ),
    ],
)
def test_live_scientific_wasm_backends(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    language: str,
    dependencies: list[str],
    code: str,
    expected_metric: str,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    available = runtime.python_available if language == "python" else runtime.r_available
    if not available:
        pytest.skip("pinned scientific WASM runtime is not installed on this host")
    monkeypatch.setenv("AI_STATISTICIAN_TEST_SECRET", "must-not-be-inherited")

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id=f"live-{language}",
        language=language,
        code=code,
        dependencies=dependencies,
        seed=20260716,
        replicates=16,
        timeout_s=60,
    )

    assert result.status == "EXECUTED"
    assert result.execution_attempted is True
    assert expected_metric in result.metrics
    assert result.metrics["n"] == 16
    assert json.loads(Path(result.result_path).read_text(encoding="utf-8")) == (
        result.metrics
    )
    envelope = json.loads(
        Path(result.execution_envelope_path).read_text(encoding="utf-8")
    )
    assert envelope["metrics"] == result.metrics
    assert result.execution_envelope_hash
    assert "AI_STATISTICIAN_TEST_SECRET" not in result.subprocess_environment_keys
    if language == "r":
        assert result.metrics["secret_present"] is False
        assert result.metrics["host_file_readable"] is False
        assert result.metrics["child_process_started"] is False


def test_live_scientific_runtime_returns_exact_error_feedback(tmp_path: Path) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="live-error",
        language="python",
        code=(
            "def run_sandbox(seed, replicates):\n"
            "    raise ValueError('intentional scientific repair signal')\n"
        ),
        dependencies=[],
        seed=3,
        replicates=2,
        timeout_s=60,
    )

    assert result.status == "FAILED"
    assert result.execution_attempted is True
    assert any("intentional scientific repair signal" in error for error in result.errors)
    assert "ValueError" in result.stderr_summary


def test_live_unbound_python_normalizes_numpy_result_values(tmp_path: Path) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="unbound-python-numpy-values",
        language="python",
        code=(
            "import numpy as np\n\n"
            "def run_sandbox(seed, replicates):\n"
            "    return {\n"
            "        'accepted': np.bool_(True),\n"
            "        'count': np.int64(replicates),\n"
            "        'values': np.asarray([1.5, 2.5]),\n"
            "    }\n"
        ),
        dependencies=["numpy"],
        seed=7,
        replicates=5,
        timeout_s=60,
    )

    assert result.status == "EXECUTED"
    assert result.metrics == {
        "accepted": True,
        "count": 5,
        "values": [1.5, 2.5],
    }


def test_live_unbound_python_still_rejects_nonfinite_values(tmp_path: Path) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="unbound-python-nonfinite",
        language="python",
        code=(
            "import numpy as np\n\n"
            "def run_sandbox(seed, replicates):\n"
            "    return {'invalid_metric': np.float64(np.nan)}\n"
        ),
        dependencies=["numpy"],
        seed=7,
        replicates=5,
        timeout_s=60,
    )

    assert result.status == "FAILED"
    assert any("Out of range float values" in error for error in result.errors)


@pytest.mark.parametrize(
    ("language", "dependencies", "algorithm", "simulation"),
    [
        (
            "python",
            [],
            "def run_estimator(request):\n"
            "    values = request['values']\n"
            "    return {'estimate': sum(values) / len(values)}\n",
            "def run_sandbox(seed, replicates, estimators):\n"
            "    fitted = estimators['candidate']({'values': [seed, replicates]})\n"
            "    return {'estimate': fitted['estimate'], 'n': replicates}\n",
        ),
        (
            "r",
            ["base", "stats"],
            "run_estimator <- function(request) "
            "list(estimate=mean(request$values))\n",
            "run_sandbox <- function(seed, replicates, estimators) { "
            "fitted <- estimators[['candidate']](list(values=c(seed, replicates))); "
            "list(estimate=fitted$estimate, n=replicates) }\n",
        ),
    ],
)
def test_live_estimator_bound_simulation_invokes_exact_reviewed_source(
    tmp_path: Path,
    language: str,
    dependencies: list[str],
    algorithm: str,
    simulation: str,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    available = runtime.python_available if language == "python" else runtime.r_available
    if not available:
        pytest.skip("pinned scientific WASM runtime is not installed on this host")

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id=f"bound-{language}",
        language=language,
        code=simulation,
        dependencies=dependencies,
        seed=7,
        replicates=5,
        timeout_s=60,
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language=language,
                code=algorithm,
                code_hash=stable_hash(algorithm),
                dependencies=tuple(dependencies),
            ),
        ),
    )

    assert result.status == "EXECUTED"
    assert result.invocation_mode == "estimator_bound"
    assert result.metrics == {"estimate": 6, "n": 5}
    assert result.estimator_code_hashes == {"candidate": stable_hash(algorithm)}
    assert result.estimator_invocation_counts == {"candidate": 1}
    assert result.estimator_binding_hash == stable_hash(result.estimator_code_hashes)


def test_live_estimator_bound_reports_nested_export_as_binding_failure(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")
    algorithm = (
        "def run_sandbox(seed, replicates):\n"
        "    def run_estimator(request):\n"
        "        return {'estimate': request['value']}\n"
        "    return run_estimator({'value': seed})\n"
    )
    simulation = (
        "def run_sandbox(seed, replicates, estimators):\n"
        "    return estimators['candidate']({'value': seed})\n"
    )

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="bound-nested-export",
        language="python",
        code=simulation,
        dependencies=[],
        seed=7,
        replicates=5,
        timeout_s=60,
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language="python",
                code=algorithm,
                code_hash=stable_hash(algorithm),
            ),
        ),
    )

    assert result.status == "FAILED"
    assert result.estimator_runtime_failure_ids == ()
    assert len(result.estimator_binding_errors) == 1
    assert "ACCEPTED_ESTIMATOR_BINDING_ERROR: candidate" in (
        result.estimator_binding_errors[0]
    )


def test_live_estimator_bound_python_normalizes_numpy_callback_values(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")
    algorithm = (
        "import numpy as np\n\n"
        "def run_estimator(request):\n"
        "    values = request['values']\n"
        "    return {'estimate': np.float64(sum(values) / len(values))}\n"
    )
    simulation = (
        "import numpy as np\n\n"
        "def run_sandbox(seed, replicates, estimators):\n"
        "    values = np.asarray([seed, replicates], dtype=float)\n"
        "    fitted = estimators['candidate']({'values': values})\n"
        "    return {'estimate': fitted['estimate'], 'n': replicates}\n"
    )

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="bound-python-numpy-values",
        language="python",
        code=simulation,
        dependencies=["numpy"],
        seed=7,
        replicates=5,
        timeout_s=60,
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language="python",
                code=algorithm,
                code_hash=stable_hash(algorithm),
                dependencies=("numpy",),
            ),
        ),
    )

    assert result.status == "EXECUTED"
    assert result.metrics == {"estimate": 6, "n": 5}
    assert result.estimator_invocation_counts == {"candidate": 1}


def test_live_estimator_bound_simulation_fails_when_callback_is_not_used(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")
    algorithm = "def run_estimator(request):\n    return {'estimate': 1.0}\n"

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="bound-not-used",
        language="python",
        code=(
            "def run_sandbox(seed, replicates, estimators):\n"
            "    return {'estimate': 1.0, 'n': replicates}\n"
        ),
        dependencies=[],
        seed=7,
        replicates=5,
        timeout_s=60,
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language="python",
                code=algorithm,
                code_hash=stable_hash(algorithm),
            ),
        ),
    )

    assert result.status == "FAILED"
    assert result.metrics == {"estimate": 1, "n": 5}
    assert result.estimator_invocation_counts == {"candidate": 0}
    assert any("was not invoked" in error for error in result.errors)


def test_live_estimator_failure_is_tagged_as_algorithm_runtime_feedback(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")
    algorithm = (
        "def run_estimator(request):\n"
        "    return {'estimate': float('inf')}\n"
    )

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="bound-nonfinite-response",
        language="python",
        code=(
            "def run_sandbox(seed, replicates, estimators):\n"
            "    return estimators['candidate']({'seed': seed})\n"
        ),
        dependencies=[],
        seed=7,
        replicates=5,
        timeout_s=60,
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language="python",
                code=algorithm,
                code_hash=stable_hash(algorithm),
            ),
        ),
    )

    assert result.status == "FAILED"
    assert result.estimator_runtime_failure_ids == ("candidate",)
    assert len(result.estimator_runtime_errors) == 1
    assert "ACCEPTED_ESTIMATOR_RUNTIME_ERROR" in result.estimator_runtime_errors[0]


def test_live_estimator_failure_caught_by_simulation_keeps_algorithm_origin(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.python_available:
        pytest.skip("pinned Pyodide runtime is not installed on this host")
    algorithm = (
        "def run_estimator(request):\n"
        "    return {'estimate': 1.0, 'by_time': {1.5: 2}}\n"
    )
    simulation = (
        "def run_sandbox(seed, replicates, estimators):\n"
        "    try:\n"
        "        estimators['candidate']({'seed': seed})\n"
        "    except Exception as exc:\n"
        "        return {'caught': True, 'message': str(exc)}\n"
        "    return {'caught': False}\n"
    )

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="bound-caught-estimator-failure",
        language="python",
        code=simulation,
        dependencies=[],
        seed=7,
        replicates=5,
        timeout_s=60,
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language="python",
                code=algorithm,
                code_hash=stable_hash(algorithm),
            ),
        ),
    )

    assert result.status == "FAILED"
    assert result.metrics["caught"] is True
    assert result.estimator_invocation_counts == {"candidate": 0}
    assert result.estimator_runtime_failure_ids == ("candidate",)
    assert len(result.estimator_runtime_errors) == 1
    assert "object keys must be strings" in result.estimator_runtime_errors[0]
    assert "float" in result.estimator_runtime_errors[0]


def test_live_r_estimator_failure_caught_by_simulation_keeps_algorithm_origin(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.r_available:
        pytest.skip("pinned WebR runtime is not installed on this host")
    algorithm = (
        "run_estimator <- function(request) "
        "list(estimate=Inf)\n"
    )
    simulation = (
        "run_sandbox <- function(seed, replicates, estimators) {\n"
        "  tryCatch({\n"
        "    estimators[['candidate']](list(seed=seed))\n"
        "    list(caught=FALSE)\n"
        "  }, error=function(error) {\n"
        "    list(caught=TRUE, message=conditionMessage(error))\n"
        "  })\n"
        "}\n"
    )

    result = execute_scientific_sandbox(
        sandbox_dir=tmp_path,
        artifact_id="bound-r-caught-estimator-failure",
        language="r",
        code=simulation,
        dependencies=["base", "stats"],
        seed=7,
        replicates=5,
        timeout_s=60,
        estimator_bindings=(
            ScientificEstimatorBinding(
                artifact_id="candidate",
                language="r",
                code=algorithm,
                code_hash=stable_hash(algorithm),
                dependencies=("base", "stats"),
            ),
        ),
    )

    assert result.status == "FAILED"
    assert result.metrics["caught"] is True
    assert result.estimator_invocation_counts == {"candidate": 0}
    assert result.estimator_runtime_failure_ids == ("candidate",)
    assert len(result.estimator_runtime_errors) == 1
    assert "finite JSON-compatible values" in result.estimator_runtime_errors[0]
