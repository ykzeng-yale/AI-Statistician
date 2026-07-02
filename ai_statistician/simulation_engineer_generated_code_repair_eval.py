from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .agent_runtime import AgentTask, BlackboardState
from .generated_metric_repair_policy import (
    generated_coverage_metric_component_feedback,
    generated_python_sandbox_guard_repair_instruction,
)
from .model_backend import (
    OpenAIResponsesGeneratorBackend,
    default_generator_model,
)
from .research_agent_runtime import (
    SimulationEvaluatorRuntimeSubsystem,
    _generated_sandbox_repair_sequence_counts,
)
from .research_architect import AnthropicArchitectLLMProvider, StaticArchitectLLMProvider
from .research_lab import load_open_research_questions
from .simulation_engineer_llm import (
    LLMSimulationEngineerAgent,
    SimulationEngineerConfig,
)


SIMULATION_REPAIR_EVAL_NOT_PROOF_EVIDENCE = (
    "SIMULATION_ENGINEER_GENERATED_CODE_REPAIR_EVAL_NOT_PROOF_EVIDENCE"
)


def run_simulation_engineer_generated_code_repair_eval(
    *,
    question_file: Path,
    question_id: str,
    out_dir: Path,
    provider_name: str = "anthropic",
    model: str = "",
    static_response_file: Path | None = None,
    llm_timeout_seconds: float | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.1,
    n_runs: int = 24,
    seed: int = 20260623,
    target_coverage: float = 0.9,
    max_repair_attempts: int = 4,
) -> dict[str, Any]:
    """Run a narrow generated-code repair eval for SimulationEngineer.

    This component eval injects a prior generated simulation metric-gate
    failure, asks the configured generator-backed SimulationEngineer to repair
    it with a new generated Python stress-test draft, executes that draft
    locally through the existing AgentRuntime simulation sandbox, and records
    whether the failure was followed by a passing generated draft. It is not
    theorem proof evidence and is not a full AgentRuntime research success.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    questions = load_open_research_questions(question_file)
    question = next((row for row in questions if row.id == question_id), None)
    if question is None:
        raise ValueError(f"unknown question_id: {question_id}")

    provider_name = provider_name.strip().lower()
    provider = _repair_eval_provider(
        provider_name=provider_name,
        static_response_file=static_response_file,
        llm_timeout_seconds=llm_timeout_seconds,
    )
    resolved_model = default_generator_model(
        provider_name,
        model,
        model_tier="haiku",
    )
    simulation_engineer = LLMSimulationEngineerAgent(
        provider=provider,
        config=SimulationEngineerConfig(
            provider_name=provider_name,
            model=resolved_model,
            model_tier="haiku",
            max_tokens=max_tokens,
            temperature=temperature,
        ),
    )

    simulation_id = "generated_split_conformal_stress_repair_probe"
    theory_packet_id = "theory:generated_simulation_repair_eval"
    prior_failure_manifest = _prior_metric_gate_failure_manifest(
        simulation_id=simulation_id,
        target_coverage=target_coverage,
        question={
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "tags": list(question.tags),
        },
    )
    blackboard = BlackboardState(
        project_id=f"simulation-repair-eval:{question.id}",
        artifacts={
            theory_packet_id: {
                "schema_version": 1,
                "artifact_kind": "TheoryPacketForSimulationRepairEval",
                "packet_id": theory_packet_id,
                "problem_card": {
                    "estimand": "finite-sample predictive coverage",
                    "assumptions": ["exchangeable calibration and test scores"],
                    "desired_theorem_type": "split conformal coverage diagnostic",
                },
                "simulation_ademp_spec": {
                    "aim": (
                        "Stress a generated split-conformal-style simulation "
                        "draft and require nondegenerate empirical coverage."
                    ),
                    "target_coverage": target_coverage,
                    "metrics": ["empirical_coverage", "target_coverage", "mean_width"],
                },
            },
            prior_failure_manifest["manifest_id"]: prior_failure_manifest,
        },
    )
    feedback = _prior_metric_gate_feedback(
        manifest=prior_failure_manifest,
        target_coverage=target_coverage,
    )
    subsystem = SimulationEvaluatorRuntimeSubsystem(
        proposal_agent=simulation_engineer,
        sandbox_root=out_dir / "simulation_sandbox",
    )
    task = AgentTask(
        task_id=f"simulation-repair-eval:{question.id}",
        owner_subsystem="SimulationEvaluator",
        objective=(
            "Repair a metric-gate-failing generated simulation stress-test draft. "
            "Use generated simulation code; do not rely only on the registered simulator."
        ),
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "theory_packet_id": theory_packet_id,
            "environment_feedback": feedback,
            "architect_context": {
                "runtime_requested_evidence_contract": {
                    "capability_eval_requires_generated_simulation_code": True,
                    "formal_required_for_final": False,
                    "must_disclose_formal_gaps": True,
                }
            },
            "n_runs": n_runs,
            "seed": seed,
        },
        expected_artifacts=("simulation_manifest",),
        acceptance_gate=(
            "a later Claude/OpenAI-generated simulation draft passes local "
            "execution and statistical metric gates after the injected failure"
        ),
        stop_condition="generated simulation-code repair evidence recorded",
    )
    attempt_results = []
    accumulated_produced_artifacts: dict[str, Any] = {}
    current_task = task
    result = None
    for attempt_index in range(max(0, max_repair_attempts) + 1):
        result = subsystem.run(current_task, blackboard)
        attempt_results.append(
            {
                "attempt_index": attempt_index,
                "task_id": current_task.task_id,
                "status": result.status,
                "failure_classification": result.failure_classification,
                "next_task_id": result.next_task.task_id if result.next_task else "",
                "produced_artifact_ids": tuple(result.produced_artifacts),
            }
        )
        for artifact_id, artifact in result.produced_artifacts.items():
            blackboard.artifacts[artifact_id] = artifact
            accumulated_produced_artifacts[artifact_id] = artifact
        sequence_counts = _generated_sandbox_repair_sequence_counts(
            blackboard.artifacts
        )
        latest_simulation_manifest = _latest_simulation_manifest(
            result.produced_artifacts
        )
        if _simulation_manifest_passes_generated_metric_gate(
            latest_simulation_manifest
        ) and int(
            sequence_counts.get(
                "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
                0,
            )
            or 0
        ) > 0:
            break
        if result.next_task is None:
            break
        if result.next_task.owner_subsystem != "SimulationEvaluator":
            break
        current_task = result.next_task
    if result is None:
        raise RuntimeError("SimulationEngineer repair eval produced no attempts")
    sequence_counts = _generated_sandbox_repair_sequence_counts(blackboard.artifacts)
    live_sequence_counts = _generated_sandbox_repair_sequence_counts(
        accumulated_produced_artifacts
    )
    simulation_manifest = _latest_simulation_manifest(blackboard.artifacts)
    n_generated_executed = int(
        simulation_manifest.get("n_generated_simulation_sandbox_executed", 0) or 0
    )
    n_passed = int(
        simulation_manifest.get("n_generated_simulation_sandbox_passed", 0) or 0
    )
    n_metric_gate_failed = int(
        simulation_manifest.get("n_generated_simulation_sandbox_metric_gate_failed", 0)
        or 0
    )
    n_unsafe_rejected = int(
        simulation_manifest.get("n_unsafe_generated_simulation_code_rejected", 0) or 0
    )
    n_repair_sequences = int(
        sequence_counts.get(
            "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_metric_repair_sequences = int(
        sequence_counts.get(
            "n_generated_simulation_sandbox_metric_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_unsafe_repair_sequences = int(
        sequence_counts.get(
            "n_generated_simulation_sandbox_unsafe_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_live_repair_sequences = int(
        live_sequence_counts.get(
            "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_live_metric_repair_sequences = int(
        live_sequence_counts.get(
            "n_generated_simulation_sandbox_metric_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_live_unsafe_repair_sequences = int(
        live_sequence_counts.get(
            "n_generated_simulation_sandbox_unsafe_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    live_generator = provider_name in {"anthropic", "openai"}
    repair_loop_observed = bool(n_repair_sequences > 0)
    live_attempt_failed_then_passed = bool(n_live_repair_sequences > 0)
    sandbox_clean = bool(
        n_generated_executed > 0
        and n_passed > 0
        and n_metric_gate_failed == 0
        and n_unsafe_rejected == 0
    )
    manifest = {
        "schema_version": 1,
        "artifact_kind": "SimulationEngineerGeneratedCodeRepairEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "question_title": question.title,
        "provider_name": provider_name,
        "model": resolved_model,
        "live_generator": live_generator,
        "component_eval": "SimulationEngineer generated-code repair",
        "result_status": result.status,
        "failure_classification": result.failure_classification,
        "n_repair_attempts_run": len(attempt_results),
        "repair_attempts": attempt_results,
        "n_generated_simulation_sandbox_executed": n_generated_executed,
        "n_generated_simulation_sandbox_passed": n_passed,
        "n_generated_simulation_sandbox_metric_gate_failed": n_metric_gate_failed,
        "n_unsafe_generated_simulation_code_rejected": n_unsafe_rejected,
        "n_generated_simulation_sandbox_failed_then_passed_repair_sequences": (
            n_repair_sequences
        ),
        "n_generated_simulation_sandbox_metric_failed_then_passed_repair_sequences": (
            n_metric_repair_sequences
        ),
        "n_generated_simulation_sandbox_unsafe_failed_then_passed_repair_sequences": (
            n_unsafe_repair_sequences
        ),
        "n_live_generated_simulation_sandbox_failed_then_passed_repair_sequences": (
            n_live_repair_sequences
        ),
        "n_live_generated_simulation_sandbox_metric_failed_then_passed_repair_sequences": (
            n_live_metric_repair_sequences
        ),
        "n_live_generated_simulation_sandbox_unsafe_failed_then_passed_repair_sequences": (
            n_live_unsafe_repair_sequences
        ),
        "prior_failure_feedback_injected": True,
        "repair_loop_observed": repair_loop_observed,
        "live_attempt_failed_then_passed_observed": live_attempt_failed_then_passed,
        "repair_evidence_scope": (
            "static_fixture_plumbing_only"
            if not live_generator
            else (
                "live_attempt_failed_then_passed"
                if live_attempt_failed_then_passed
                else (
                    "injected_prior_failure_feedback_then_live_generated_pass"
                    if repair_loop_observed and sandbox_clean
                    else "generated_repair_not_observed"
                )
            )
        ),
        "sandbox_clean_after_repair": sandbox_clean,
        "capability_evidence_ok": bool(
            live_generator and repair_loop_observed and sandbox_clean
        ),
        "static_or_fixture_only": not live_generator,
        "prior_failure_manifest": prior_failure_manifest,
        "simulation_manifest": dict(simulation_manifest),
        "proof_evidence_status": SIMULATION_REPAIR_EVAL_NOT_PROOF_EVIDENCE,
        "boundary": (
            "This component eval checks whether SimulationEngineer can consume "
            "local generated-simulation failure feedback and produce a later "
            "generated Python stress-test draft that passes sandbox and metric "
            "gates. It is not theorem proof evidence and not a full AgentRuntime "
            "research success."
        ),
    }
    manifest_path = out_dir / "simulation_engineer_generated_code_repair_eval_manifest.json"
    result_path = out_dir / "simulation_engineer_generated_code_repair_eval_result.json"
    manifest["artifacts"] = {
        "manifest_json": str(manifest_path),
        "result_json": str(result_path),
    }
    result_path.write_text(
        json.dumps(
            {
                "status": result.status,
                "failure_classification": result.failure_classification,
                "attempts": attempt_results,
                "observations": [row.__dict__ for row in result.observations],
                "produced_artifacts": accumulated_produced_artifacts,
                "next_task": result.next_task.__dict__ if result.next_task else None,
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


def _latest_simulation_manifest(
    artifacts: Mapping[str, Any],
) -> Mapping[str, Any]:
    manifests = [
        artifact
        for key, artifact in artifacts.items()
        if key.startswith("simulation_manifest:") and isinstance(artifact, Mapping)
    ]
    if not manifests:
        return {}
    return max(
        manifests,
        key=lambda row: str(row.get("created_at", "")),
    )


def _simulation_manifest_passes_generated_metric_gate(
    manifest: Mapping[str, Any],
) -> bool:
    return bool(
        int(manifest.get("n_generated_simulation_sandbox_executed", 0) or 0) > 0
        and int(manifest.get("n_generated_simulation_sandbox_passed", 0) or 0) > 0
        and int(manifest.get("n_generated_simulation_sandbox_metric_gate_failed", 0) or 0)
        == 0
        and int(manifest.get("n_unsafe_generated_simulation_code_rejected", 0) or 0)
        == 0
    )


def write_simulation_engineer_generated_code_repair_eval_failure_manifest(
    *,
    out_dir: Path,
    provider_name: str,
    model: str,
    question_id: str,
    exc: Exception,
) -> dict[str, Any]:
    """Write an inspectable failure manifest for provider/runtime exceptions."""

    out_dir.mkdir(parents=True, exist_ok=True)
    provider_name = provider_name.strip().lower()
    resolved_model = default_generator_model(
        provider_name,
        model,
        model_tier="haiku",
    )
    live_generator = provider_name in {"anthropic", "openai"}
    manifest_path = out_dir / "simulation_engineer_generated_code_repair_eval_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "SimulationEngineerGeneratedCodeRepairEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question_id,
        "provider_name": provider_name,
        "model": resolved_model,
        "live_generator": live_generator,
        "component_eval": "SimulationEngineer generated-code repair",
        "result_status": "PROVIDER_OR_RUNTIME_FAILURE",
        "failure_classification": "provider_or_runtime_exception",
        "failure_exception_type": type(exc).__name__,
        "failure_message": str(exc)[:1000],
        "n_generated_simulation_sandbox_executed": 0,
        "n_generated_simulation_sandbox_passed": 0,
        "n_generated_simulation_sandbox_metric_gate_failed": 0,
        "n_unsafe_generated_simulation_code_rejected": 0,
        "n_generated_simulation_sandbox_failed_then_passed_repair_sequences": 0,
        "repair_loop_observed": False,
        "sandbox_clean_after_repair": False,
        "capability_evidence_ok": False,
        "static_or_fixture_only": not live_generator,
        "proof_evidence_status": SIMULATION_REPAIR_EVAL_NOT_PROOF_EVIDENCE,
        "boundary": (
            "The component eval did not complete. This failure manifest is "
            "inspectable status only: it is not simulation coding-agent "
            "capability evidence and not theorem proof evidence."
        ),
        "artifacts": {
            "manifest_json": str(manifest_path),
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


def _repair_eval_provider(
    *,
    provider_name: str,
    static_response_file: Path | None,
    llm_timeout_seconds: float | None,
):
    if provider_name == "anthropic":
        return AnthropicArchitectLLMProvider(timeout_s=llm_timeout_seconds)
    if provider_name == "openai":
        return OpenAIResponsesGeneratorBackend(timeout_s=llm_timeout_seconds)
    if provider_name == "static":
        if static_response_file is None:
            raise ValueError("static provider requires static_response_file")
        return StaticArchitectLLMProvider(
            static_response_file.read_text(encoding="utf-8")
        )
    raise ValueError(
        "unsupported SimulationEngineer repair eval provider: "
        f"{provider_name!r}; expected anthropic, openai, or static"
    )


def _prior_metric_gate_failure_manifest(
    *,
    simulation_id: str,
    target_coverage: float,
    question: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": "simulation_manifest:injected_metric_gate_failure",
        "created_at": "2026-01-01T00:00:00+00:00",
        "generated_simulation_sandbox_prototypes": [
            {
                "simulation_id": simulation_id,
                "prototype_status": "FAILED_METRIC_GATE",
                "executor": "generated_simulation_sandbox",
                "smoke_passed": False,
                "execution_smoke_passed": True,
                "metric_gate_errors": [
                    "empirical_coverage is degenerate zero coverage",
                    "empirical_coverage below target_coverage",
                ],
                "metrics": {
                    "empirical_coverage": 0.0,
                    "target_coverage": target_coverage,
                    "mean_width": 1.0,
                    "sandbox_failed": False,
                },
            }
        ],
        "n_generated_simulation_sandbox_prototypes": 1,
        "n_generated_simulation_sandbox_executed": 1,
        "n_generated_simulation_sandbox_passed": 0,
        "n_generated_simulation_sandbox_metric_gate_failed": 1,
        "n_unsafe_generated_simulation_code_rejected": 0,
        "simulation_passed": False,
        "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
        "boundary": (
            "Injected prior generated simulation failure for component eval; "
            "not proof evidence and not a completed simulation study."
        ),
    }
    if isinstance(question, Mapping) and str(question.get("id", "") or "").strip():
        payload["question"] = dict(question)
        payload["question_id"] = str(question.get("id", "") or "")
    return payload


def _prior_metric_gate_feedback(
    *,
    manifest: Mapping[str, Any],
    target_coverage: float,
) -> dict[str, Any]:
    return {
        "feedback_type": "generated_simulation_sandbox_execution_feedback",
        "simulation_manifest_id": str(manifest.get("manifest_id", "")),
        "failure_classification": "generated_simulation_sandbox_metric_gate_failed",
        "n_generated_simulation_sandbox_prototypes": 1,
        "n_generated_simulation_sandbox_executed": 1,
        "n_generated_simulation_sandbox_passed": 0,
        "n_generated_simulation_sandbox_metric_gate_failed": 1,
        "n_unsafe_generated_simulation_code_rejected": 0,
        "generated_simulation_prototypes": list(
            manifest.get("generated_simulation_sandbox_prototypes", []) or []
        ),
        "required_repair": generated_coverage_metric_component_feedback(
            artifact_label="generated simulation sandbox",
            target_coverage=target_coverage,
            return_fields=(
                "target_coverage",
                "mean_width",
                "sandbox_failed=False",
            ),
        )
        + " "
        + generated_python_sandbox_guard_repair_instruction(
            artifact_label="generated simulation sandbox"
        ),
        "runtime_requested_evidence_contract": {
            "capability_eval_requires_generated_simulation_code": True
        },
        "boundary": (
            "Injected metric-gate failure feedback for component eval; not proof "
            "evidence."
        ),
    }
