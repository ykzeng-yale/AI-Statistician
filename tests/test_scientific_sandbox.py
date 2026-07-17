from __future__ import annotations

from pathlib import Path

import pytest

import ai_statistician.research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import ToolCallRecord
from ai_statistician.algorithm_engineer_llm import (
    ALGORITHM_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
    validate_algorithm_engineer_packet,
)
from ai_statistician.scientific_sandbox import (
    SCIENTIFIC_SANDBOX_BOUNDARY,
    ScientificSandboxExecution,
    ScientificSandboxRuntime,
    discover_scientific_sandbox_runtime,
    execute_scientific_sandbox,
    generated_code_execution_contract_errors,
    normalized_generated_code_profile,
    scientific_python_safety_errors,
)
from ai_statistician.simulation_engineer_llm import (
    SIMULATION_ENGINEER_PROPOSAL_NOT_EXECUTION_EVIDENCE,
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


def test_scientific_python_guard_requires_declared_packages_and_blocks_bridges() -> None:
    undeclared = scientific_python_safety_errors(
        "import numpy as np\n\ndef run_sandbox(seed, replicates):\n    return {'n': replicates}",
        dependencies=[],
    )
    bridged = scientific_python_safety_errors(
        "import js\n\ndef run_sandbox(seed, replicates):\n    return {'n': replicates}",
        dependencies=[],
    )
    assert "generated scientific Python import is not declared: numpy" in undeclared
    assert "generated scientific Python import is not declared: js" in bridged


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
            {"simulation_id": "r-simulation", **r_draft}
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


def test_runtime_dispatch_preserves_existing_metric_and_evidence_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    execution = ScientificSandboxExecution(
        status="EXECUTED",
        language="r",
        execution_profile="scientific_wasm",
        backend="webr",
        isolation_provider="test-wasm-isolation",
        dependencies=("base", "stats"),
        execution_attempted=True,
        returncode=0,
        metrics={"mean": 0.25, "n": 8},
        errors=(),
        stdout_summary="",
        stderr_summary="",
        result_parse_error="",
        code_path=str(tmp_path / "draft.R"),
        request_path=str(tmp_path / "request.json"),
        result_path=str(tmp_path / "result.json"),
        code_hash="code-hash",
        request_hash="request-hash",
        result_hash="result-hash",
        subprocess_environment_keys=("HOME", "PATH"),
        resource_limits={"cpu_seconds": 5},
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
            "code": "run_sandbox <- function(seed, replicates) list(n=replicates)",
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
    assert prototype["metrics"] == {"mean": 0.25, "n": 8}
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
            "code": "run_sandbox <- function(seed, replicates) list(n=replicates)",
        },
        n_runs=8,
        seed=11,
        timeout_s=5,
    )
    assert simulation["executor"] == "generated_simulation_sandbox"
    assert simulation["smoke_passed"] is True
    assert simulation_call.tool_name == "r.generated_simulation_sandbox"

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
