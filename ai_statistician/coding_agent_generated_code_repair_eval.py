from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .algorithm_engineer_generated_code_repair_eval import (
    ALGORITHM_REPAIR_EVAL_NOT_PROOF_EVIDENCE,
    run_algorithm_engineer_generated_code_repair_eval,
    write_algorithm_engineer_generated_code_repair_eval_failure_manifest,
)
from .model_backend import default_generator_model
from .simulation_engineer_generated_code_repair_eval import (
    SIMULATION_REPAIR_EVAL_NOT_PROOF_EVIDENCE,
    run_simulation_engineer_generated_code_repair_eval,
    write_simulation_engineer_generated_code_repair_eval_failure_manifest,
)


CODING_AGENT_REPAIR_EVAL_NOT_PROOF_EVIDENCE = (
    "CODING_AGENT_GENERATED_CODE_REPAIR_EVAL_NOT_PROOF_EVIDENCE"
)


def run_coding_agent_generated_code_repair_eval(
    *,
    question_file: Path,
    question_id: str,
    out_dir: Path,
    provider_name: str = "anthropic",
    model: str = "",
    algorithm_static_response_file: Path | None = None,
    simulation_static_response_file: Path | None = None,
    llm_timeout_seconds: float | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.1,
    n_runs: int = 24,
    seed: int = 20260623,
    target_coverage: float = 0.9,
    max_repair_attempts: int = 4,
) -> dict[str, Any]:
    """Run the narrow coding-agent generated-code repair capability gate.

    This aggregates the AlgorithmEngineer and SimulationEngineer component
    evals. It is intentionally strict: the combined capability is true only
    when both generator-backed workers show fail-then-pass generated Python
    repair evidence under local sandbox/metric gates. Static replay may exercise
    plumbing but never counts as capability evidence.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    provider_name = provider_name.strip().lower()
    resolved_model = default_generator_model(
        provider_name,
        model,
        model_tier="haiku",
    )
    algorithm_manifest: dict[str, Any]
    simulation_manifest: dict[str, Any]
    try:
        algorithm_manifest = run_algorithm_engineer_generated_code_repair_eval(
            question_file=question_file,
            question_id=question_id,
            out_dir=out_dir / "algorithm_engineer",
            provider_name=provider_name,
            model=model,
            static_response_file=algorithm_static_response_file,
            llm_timeout_seconds=llm_timeout_seconds,
            max_tokens=max_tokens,
            temperature=temperature,
            n_runs=n_runs,
            seed=seed,
            target_coverage=target_coverage,
            max_repair_attempts=max_repair_attempts,
        )
    except Exception as exc:
        algorithm_manifest = (
            write_algorithm_engineer_generated_code_repair_eval_failure_manifest(
                out_dir=out_dir / "algorithm_engineer",
                provider_name=provider_name,
                model=model,
                question_id=question_id,
                exc=exc,
            )
        )
    try:
        simulation_manifest = run_simulation_engineer_generated_code_repair_eval(
            question_file=question_file,
            question_id=question_id,
            out_dir=out_dir / "simulation_engineer",
            provider_name=provider_name,
            model=model,
            static_response_file=simulation_static_response_file,
            llm_timeout_seconds=llm_timeout_seconds,
            max_tokens=max_tokens,
            temperature=temperature,
            n_runs=n_runs,
            seed=seed,
            target_coverage=target_coverage,
            max_repair_attempts=max_repair_attempts,
        )
    except Exception as exc:
        simulation_manifest = (
            write_simulation_engineer_generated_code_repair_eval_failure_manifest(
                out_dir=out_dir / "simulation_engineer",
                provider_name=provider_name,
                model=model,
                question_id=question_id,
                exc=exc,
            )
        )

    algorithm_ok = bool(algorithm_manifest.get("capability_evidence_ok"))
    simulation_ok = bool(simulation_manifest.get("capability_evidence_ok"))
    live_generator = provider_name in {"anthropic", "openai"}
    algorithm_live_repair_sequences = int(
        algorithm_manifest.get(
            "n_live_generated_code_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    algorithm_metric_repair_sequences = int(
        algorithm_manifest.get(
            "n_generated_code_sandbox_metric_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    algorithm_unsafe_repair_sequences = int(
        algorithm_manifest.get(
            "n_generated_code_sandbox_unsafe_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    simulation_live_repair_sequences = int(
        simulation_manifest.get(
            "n_live_generated_simulation_sandbox_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    simulation_metric_repair_sequences = int(
        simulation_manifest.get(
            "n_generated_simulation_sandbox_metric_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    simulation_unsafe_repair_sequences = int(
        simulation_manifest.get(
            "n_generated_simulation_sandbox_unsafe_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    autonomous_live_failed_then_passed = bool(
        live_generator
        and algorithm_live_repair_sequences > 0
        and simulation_live_repair_sequences > 0
    )
    fixture_plumbing_ok = bool(
        not live_generator
        and algorithm_manifest.get("sandbox_clean_after_repair")
        and simulation_manifest.get("sandbox_clean_after_repair")
    )
    capability_evidence_ok = bool(live_generator and algorithm_ok and simulation_ok)
    capability_evidence_scope = (
        "static_fixture_plumbing_only"
        if not live_generator
        else (
            "live_attempt_failed_then_passed"
            if autonomous_live_failed_then_passed
            else (
                "injected_prior_failure_feedback_then_live_generated_pass"
                if capability_evidence_ok
                else "generated_repair_not_observed"
            )
        )
    )
    manifest_path = out_dir / "coding_agent_generated_code_repair_eval_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "CodingAgentGeneratedCodeRepairEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question_id,
        "provider_name": provider_name,
        "model": resolved_model,
        "live_generator": live_generator,
        "component_eval": "AlgorithmEngineer + SimulationEngineer generated-code repair",
        "algorithm_capability_evidence_ok": algorithm_ok,
        "simulation_capability_evidence_ok": simulation_ok,
        "capability_evidence_ok": capability_evidence_ok,
        "fixture_plumbing_ok": fixture_plumbing_ok,
        "static_or_fixture_only": not live_generator,
        "algorithm_result_status": algorithm_manifest.get("result_status", ""),
        "simulation_result_status": simulation_manifest.get("result_status", ""),
        "algorithm_repair_sequences": int(
            algorithm_manifest.get(
                "n_generated_code_sandbox_failed_then_passed_repair_sequences",
                0,
            )
            or 0
        ),
        "algorithm_metric_repair_sequences": algorithm_metric_repair_sequences,
        "algorithm_unsafe_repair_sequences": algorithm_unsafe_repair_sequences,
        "algorithm_live_repair_sequences": algorithm_live_repair_sequences,
        "simulation_repair_sequences": int(
            simulation_manifest.get(
                "n_generated_simulation_sandbox_failed_then_passed_repair_sequences",
                0,
            )
            or 0
        ),
        "simulation_metric_repair_sequences": simulation_metric_repair_sequences,
        "simulation_unsafe_repair_sequences": simulation_unsafe_repair_sequences,
        "simulation_live_repair_sequences": simulation_live_repair_sequences,
        "prior_failure_feedback_injected": True,
        "autonomous_live_failed_then_passed_repair_observed": (
            autonomous_live_failed_then_passed
        ),
        "capability_evidence_scope": capability_evidence_scope,
        "max_repair_attempts": max_repair_attempts,
        "algorithm_manifest": {
            "path": algorithm_manifest.get("artifacts", {}).get("manifest_json", ""),
            "proof_evidence_status": algorithm_manifest.get(
                "proof_evidence_status",
                ALGORITHM_REPAIR_EVAL_NOT_PROOF_EVIDENCE,
            ),
        },
        "simulation_manifest": {
            "path": simulation_manifest.get("artifacts", {}).get("manifest_json", ""),
            "proof_evidence_status": simulation_manifest.get(
                "proof_evidence_status",
                SIMULATION_REPAIR_EVAL_NOT_PROOF_EVIDENCE,
            ),
        },
        "proof_evidence_status": CODING_AGENT_REPAIR_EVAL_NOT_PROOF_EVIDENCE,
        "boundary": (
            "This combined eval is a coding-agent capability gate for local "
            "generated-code repair only. It is not theorem proof evidence, not a "
            "full AgentRuntime research success, and static fixture plumbing cannot "
            "satisfy capability_evidence_ok."
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
