from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .agent_runtime import AgentTask, BlackboardState
from .formalizer_llm import FormalizerConfig, LLMFormalizerProofEngineerAgent
from .model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    OpenAIResponsesGeneratorBackend,
    generator_backend_provider_name,
    is_live_generator_backend,
    resolve_live_evaluation_model,
)
from .proof_state_feedback import (
    LeanLspMcpProofStateFeedbackProvider,
    LocalLeanProofStateFeedbackProvider,
    proof_state_feedback_row_to_json,
)
from .research_agent_runtime import (
    FormalizationEvaluatorRuntimeSubsystem,
    _formalizer_lean_candidate_proof_state_subclaims,
    _formalizer_lean_candidate_repair_feedback,
    _materialize_formalizer_lean_candidate_artifacts,
)
from .research_architect import AnthropicArchitectLLMProvider, StaticArchitectLLMProvider
from .research_lab import load_open_research_questions
from .research_schema import OpenResearchQuestion


FORMALIZER_LEAN_REPAIR_EVAL_NOT_SOURCE_THEOREM_PROOF_EVIDENCE = (
    "FORMALIZER_LEAN_CANDIDATE_REPAIR_EVAL_NOT_SOURCE_THEOREM_PROOF_EVIDENCE"
)


def run_formalizer_lean_candidate_repair_eval(
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
    lean_project: Path | None = None,
    lean_timeout: int = 15,
    lean_lsp_mcp_proof_state_feedback: bool = False,
    max_repair_attempts: int = 3,
) -> dict[str, Any]:
    """Run a narrow Formalizer/ProofEngineer Lean-candidate repair eval.

    This component capability eval injects a prior local-Lean failure, asks the
    configured generator-backed Formalizer to repair it, materializes the Lean
    candidate, runs local Lean, and records whether the failure was followed by
    a compiling candidate. The checked candidate is evidence only for that exact
    generated helper artifact; it is not source theorem proof evidence.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    questions = load_open_research_questions(question_file)
    question = next((row for row in questions if row.id == question_id), None)
    if question is None:
        raise ValueError(f"unknown question_id: {question_id}")
    source_question = question
    question = OpenResearchQuestion(
        id="formalizer_lean_candidate_repair_probe",
        title="Formalizer Lean-candidate repair probe",
        description=(
            "Component capability eval for a Formalizer/ProofEngineer worker: "
            "repair a prior local-Lean failure into a compact no-import Lean "
            "helper theorem. This is not a statistical source theorem."
        ),
        tags=("formalizer", "lean", "capability-eval"),
    )

    provider_name = provider_name.strip().lower()
    provider = _formalizer_repair_eval_provider(
        provider_name=provider_name,
        static_response_file=static_response_file,
        llm_timeout_seconds=llm_timeout_seconds,
    )
    backend_provider_name = generator_backend_provider_name(provider, provider_name)
    resolved_model = resolve_live_evaluation_model(
        provider_name,
        model,
    )
    formalizer = LLMFormalizerProofEngineerAgent(
        provider=provider,
        config=FormalizerConfig(
            provider_name=provider_name,
            model=resolved_model,
            model_tier=LIVE_EVALUATION_CLAUDE_MODEL_TIER,
            max_tokens=max_tokens,
            temperature=temperature,
            max_repair_attempts=1,
        ),
    )

    prior_failure_manifest = _prior_local_lean_failure_manifest(
        question=question,
        out_dir=out_dir,
        lean_project=lean_project,
        lean_timeout=lean_timeout,
    )
    prior_feedback = _formalizer_lean_candidate_repair_feedback(
        prior_failure_manifest
    )
    if prior_feedback is None:
        raise RuntimeError("failed to create prior Formalizer local-Lean feedback")
    prior_feedback = dict(prior_feedback)
    proof_state_provider_cls = (
        LeanLspMcpProofStateFeedbackProvider
        if lean_lsp_mcp_proof_state_feedback
        else LocalLeanProofStateFeedbackProvider
    )
    proof_state_provider = proof_state_provider_cls(
        project_root=lean_project,
        timeout_s=lean_timeout,
    )
    prior_feedback = _attach_candidate_proof_state_feedback(
        manifest=prior_failure_manifest,
        feedback=prior_feedback,
        proof_state_provider=proof_state_provider,
    )
    theory_packet_id = "theory:formalizer_lean_repair_eval"
    simulation_manifest_id = "simulation:formalizer_lean_repair_eval"
    algorithm_manifest_id = "algorithm:formalizer_lean_repair_eval"
    blackboard = BlackboardState(
        project_id=f"formalizer-lean-repair-eval:{question.id}",
        artifacts={
            prior_failure_manifest["manifest_id"]: prior_failure_manifest,
            theory_packet_id: _formalizer_repair_theory_packet(theory_packet_id),
            simulation_manifest_id: {
                "schema_version": 1,
                "artifact_kind": "RuntimeSimulationManifest",
                "manifest_id": simulation_manifest_id,
                "simulation_passed": True,
                "proof_evidence_status": "SIMULATION_NOT_PROOF_EVIDENCE",
            },
            algorithm_manifest_id: {
                "schema_version": 1,
                "artifact_kind": "RuntimeAlgorithmSandboxManifest",
                "manifest_id": algorithm_manifest_id,
                "n_executed": 1,
                "promotion_ready": False,
            },
        },
    )
    registered_problem_override = {
        "question_id": question.id,
        "problem_class": "formalizer_lean_candidate_repair_eval",
        "dgp": "Synthetic no-data component eval for a Lean helper candidate.",
        "estimand": "No statistical estimand; this eval targets Lean helper generation.",
        "assumptions": ["Synthetic Lean canary has no statistical assumptions"],
        "asymptotic_regime": "not applicable",
        "diagnostics": ["local Lean compile result"],
        "stress_tests": [],
        "extraction_evidence": {},
    }
    theorem_goals_override = [
        {
            "id": "ai_statistician_formalizer_repair_candidate",
            "title": "Minimal Formalizer Lean repair helper",
            "informal_statement": (
                "Formalize the unchanged declaration `theorem "
                "ai_statistician_formalizer_repair_candidate (n : Nat) : n = n`."
            ),
            "proof_strategy": (
                "Use the rejected candidate and local Lean observations to author "
                "a complete proof candidate."
            ),
            "status": "PROVABLE_NOW",
            "required_primitives": [],
            "proof_obligations": [],
        }
    ]
    subsystem = FormalizationEvaluatorRuntimeSubsystem(
        proposal_agent=formalizer,
        proof_state_provider=proof_state_provider,
        max_proof_obligations=0,
        lean_candidate_root=out_dir / "formalizer_lean_candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=lean_project,
        lean_candidate_lean_timeout=lean_timeout,
    )
    task = AgentTask(
        task_id=f"formalize-lean-repair:{question.id}:component_eval",
        owner_subsystem="ProofEngineer",
        objective=(
            "Regenerate the unchanged Lean target from the rejected candidate and "
            "exact local Lean observations."
        ),
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": list(question.tags),
            },
            "theory_packet_id": theory_packet_id,
            "simulation_manifest_id": simulation_manifest_id,
            "algorithm_sandbox_manifest_id": algorithm_manifest_id,
            "registered_problem_override": registered_problem_override,
            "theorem_goals_override": theorem_goals_override,
            "environment_feedback": prior_feedback,
            "architect_context": {
                "runtime_requested_evidence_contract": {
                    "capability_eval_requires_formalizer_lean_candidate_repair": True,
                    "formal_required_for_final": False,
                    "must_disclose_formal_gaps": True,
                    "formalizer_repair_eval_helper_channel": "formal_targets",
                },
                "FormalizationEvaluator": {
                    "acceptance_gate": (
                        "generated Lean candidate compiles locally after prior "
                        "local-Lean failure feedback"
                    )
                },
            },
        },
        expected_artifacts=("formalizer_lean_candidate_materialization",),
        acceptance_gate=(
            "a later Claude/OpenAI-generated Lean candidate compiles locally "
            "after the injected local-Lean failure"
        ),
        stop_condition="formalizer Lean-candidate repair evidence recorded",
    )

    attempt_results: list[dict[str, Any]] = []
    accumulated_produced_artifacts: dict[str, Any] = {}
    current_task = task
    result = None
    for attempt_index in range(max(0, max_repair_attempts) + 1):
        result = subsystem.run(current_task, blackboard)
        attempt_results.append(
            {
                "attempt_index": attempt_index,
                "task_id": current_task.task_id,
                "owner_subsystem": current_task.owner_subsystem,
                "status": result.status,
                "failure_classification": result.failure_classification,
                "next_task_id": result.next_task.task_id if result.next_task else "",
                "produced_artifact_ids": tuple(result.produced_artifacts),
            }
        )
        for artifact_id, artifact in result.produced_artifacts.items():
            blackboard.artifacts[artifact_id] = artifact
            accumulated_produced_artifacts[artifact_id] = artifact
        sequence_counts = _formalizer_lean_candidate_repair_sequence_counts(
            blackboard.artifacts
        )
        latest_materialization = _latest_formalizer_materialization_manifest(
            blackboard.artifacts
        )
        if _formalizer_materialization_has_compiled_candidate(
            latest_materialization
        ) and int(
            sequence_counts.get(
                "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
                0,
            )
            or 0
        ) > 0:
            break
        if result.next_task is None:
            break
        if result.next_task.owner_subsystem not in {
            "FormalizationEvaluator",
            "ProofEngineer",
        }:
            break
        current_task = result.next_task
    if result is None:
        raise RuntimeError("Formalizer Lean-candidate repair eval produced no attempts")

    latest_materialization = _latest_formalizer_materialization_manifest(
        blackboard.artifacts
    )
    sequence_counts = _formalizer_lean_candidate_repair_sequence_counts(
        blackboard.artifacts
    )
    n_repair_sequences = int(
        sequence_counts.get(
            "n_formalizer_lean_candidate_failed_then_passed_repair_sequences",
            0,
        )
        or 0
    )
    n_candidate_sources = int(
        latest_materialization.get("n_candidate_sources", 0) or 0
    )
    n_artifacts_written = int(
        latest_materialization.get("n_candidate_artifacts_written", 0) or 0
    )
    n_local_checked = int(
        latest_materialization.get("n_local_lean_checked", 0) or 0
    )
    n_local_compiled = int(
        latest_materialization.get("n_local_lean_compiled", 0) or 0
    )
    n_precheck_rejected = int(
        latest_materialization.get("n_precheck_rejected", 0) or 0
    )
    live_generator = is_live_generator_backend(provider_name, backend_provider_name)
    repair_loop_observed = bool(n_repair_sequences > 0)
    proofengineer_repair_task_observed = any(
        str(row.get("task_id", "") or "").startswith("formalize-lean-repair:")
        for row in attempt_results
    )
    proofengineer_context = (
        prior_feedback.get("proofengineer_repair_context", {})
        if isinstance(
            prior_feedback.get("proofengineer_repair_context", {}),
            Mapping,
        )
        else {}
    )
    prior_feedback_proof_state_provider = str(
        proofengineer_context.get("candidate_proof_state_provider", "") or ""
    )
    proof_state_counts = (
        proofengineer_context.get("candidate_proof_state_feedback_counts", {})
        if isinstance(
            proofengineer_context.get("candidate_proof_state_feedback_counts", {}),
            Mapping,
        )
        else {}
    )
    prior_feedback_proof_state_rows = int(proof_state_counts.get("rows", 0) or 0)
    candidate_kernel_verified = bool(
        n_candidate_sources > 0
        and n_artifacts_written > 0
        and n_local_checked > 0
        and n_local_compiled > 0
        and n_precheck_rejected == 0
    )
    capability_requirements = {
        "live_generator": live_generator,
        "proofengineer_repair_task_observed": proofengineer_repair_task_observed,
        "prior_feedback_proof_state_rows": prior_feedback_proof_state_rows > 0,
        "repair_loop_observed": repair_loop_observed,
        "candidate_kernel_verified": candidate_kernel_verified,
    }
    manifest = {
        "schema_version": 1,
        "artifact_kind": "FormalizerLeanCandidateRepairEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question.id,
        "source_question_id": source_question.id,
        "question_title": question.title,
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": resolved_model,
        "live_generator": live_generator,
        "component_eval": "Formalizer/ProofEngineer Lean-candidate repair",
        "result_status": result.status,
        "failure_classification": result.failure_classification,
        "n_repair_attempts_run": len(attempt_results),
        "repair_attempts": attempt_results,
        "proofengineer_repair_task_observed": proofengineer_repair_task_observed,
        "n_formalizer_lean_candidate_sources": n_candidate_sources,
        "n_formalizer_lean_candidate_artifacts_written": n_artifacts_written,
        "n_formalizer_lean_candidate_local_lean_checked": n_local_checked,
        "n_formalizer_lean_candidate_local_lean_compiled": n_local_compiled,
        "n_formalizer_lean_candidate_precheck_rejected": n_precheck_rejected,
        "n_formalizer_lean_candidate_failed_then_passed_repair_sequences": (
            n_repair_sequences
        ),
        "repair_loop_observed": repair_loop_observed,
        "candidate_kernel_verified": candidate_kernel_verified,
        "source_theorem_kernel_verified": False,
        "full_frontier_theorem_proved": False,
        "capability_evidence_ok": bool(
            all(capability_requirements.values())
        ),
        "capability_evidence_requirements": capability_requirements,
        "static_or_fixture_only": not live_generator,
        "prior_failure_manifest": prior_failure_manifest,
        "prior_feedback_proof_state_provider": prior_feedback_proof_state_provider,
        "prior_feedback_proof_state_rows": prior_feedback_proof_state_rows,
        "prior_feedback_proof_state_counts": dict(proof_state_counts),
        "formalizer_lean_candidate_materialization": dict(latest_materialization),
        "proof_evidence_status": (
            FORMALIZER_LEAN_REPAIR_EVAL_NOT_SOURCE_THEOREM_PROOF_EVIDENCE
        ),
        "boundary": (
            "This component eval checks whether Formalizer/ProofEngineer can "
            "consume local-Lean failure feedback and produce a later generated "
            "Lean candidate that compiles locally. A compiled candidate is "
            "kernel evidence only for that exact helper artifact; it is not "
            "source theorem proof, not full frontier theorem closure, and not "
            "semantic faithfulness evidence for a paper theorem."
        ),
    }
    manifest_path = out_dir / "formalizer_lean_candidate_repair_eval_manifest.json"
    result_path = out_dir / "formalizer_lean_candidate_repair_eval_result.json"
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


def write_formalizer_lean_candidate_repair_eval_failure_manifest(
    *,
    out_dir: Path,
    provider_name: str,
    model: str,
    question_id: str,
    exc: Exception,
    backend_provider_name: str = "",
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    provider_name = provider_name.strip().lower()
    backend_provider_name = (
        backend_provider_name.strip().lower() if backend_provider_name else provider_name
    )
    resolved_model = resolve_live_evaluation_model(
        provider_name,
        model,
    )
    live_generator = is_live_generator_backend(provider_name, backend_provider_name)
    manifest_path = out_dir / "formalizer_lean_candidate_repair_eval_manifest.json"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "FormalizerLeanCandidateRepairEvalManifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": question_id,
        "provider_name": provider_name,
        "backend_provider_name": backend_provider_name,
        "model": resolved_model,
        "live_generator": live_generator,
        "component_eval": "Formalizer/ProofEngineer Lean-candidate repair",
        "result_status": "PROVIDER_OR_RUNTIME_FAILURE",
        "failure_classification": "provider_or_runtime_exception",
        "failure_exception_type": type(exc).__name__,
        "failure_message": str(exc)[:1000],
        "n_formalizer_lean_candidate_sources": 0,
        "n_formalizer_lean_candidate_artifacts_written": 0,
        "n_formalizer_lean_candidate_local_lean_checked": 0,
        "n_formalizer_lean_candidate_local_lean_compiled": 0,
        "n_formalizer_lean_candidate_precheck_rejected": 0,
        "n_formalizer_lean_candidate_failed_then_passed_repair_sequences": 0,
        "repair_loop_observed": False,
        "candidate_kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "full_frontier_theorem_proved": False,
        "capability_evidence_ok": False,
        "static_or_fixture_only": not live_generator,
        "proof_evidence_status": (
            FORMALIZER_LEAN_REPAIR_EVAL_NOT_SOURCE_THEOREM_PROOF_EVIDENCE
        ),
        "boundary": (
            "The component eval did not complete. This failure manifest is "
            "inspectable status only: it is not Formalizer/ProofEngineer "
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


def _attach_candidate_proof_state_feedback(
    *,
    manifest: Mapping[str, Any],
    feedback: Mapping[str, Any],
    proof_state_provider: LocalLeanProofStateFeedbackProvider,
) -> dict[str, Any]:
    """Attach the same candidate proof-state rows used by runtime repair.

    This keeps the component eval aligned with the product path: the LLM repair
    worker receives structured ProofEngineer diagnostics, not only raw
    stdout/stderr excerpts.
    """

    output = dict(feedback)
    subclaims = _formalizer_lean_candidate_proof_state_subclaims(manifest, output)
    proof_state_rows = (
        proof_state_provider.inspect(subclaims)
        if subclaims
        else []
    )
    row_dicts = [proof_state_feedback_row_to_json(row) for row in proof_state_rows]
    if not row_dicts:
        return output
    proofengineer_context = output.setdefault("proofengineer_repair_context", {})
    if not isinstance(proofengineer_context, dict):
        proofengineer_context = {}
        output["proofengineer_repair_context"] = proofengineer_context
    proofengineer_context["candidate_proof_state_feedback_rows"] = row_dicts[:3]
    proofengineer_context["candidate_proof_state_feedback_counts"] = {
        "rows": len(row_dicts),
        "residual_goals": sum(len(row.residual_goals) for row in proof_state_rows),
        "executed_tool_calls": sum(
            len(row.executed_tools) for row in proof_state_rows
        ),
        "local_lean_tool_calls": sum(
            1
            for row in proof_state_rows
            for tool in row.executed_tools
            if tool == "local.lake_env_lean"
        ),
        "lean_lsp_mcp_tool_calls": sum(
            1
            for row in proof_state_rows
            for tool in row.executed_tools
            if str(tool).startswith("lean_lsp_mcp.")
        ),
        "route_revision_recommended": sum(
            1 for row in proof_state_rows if row.route_revision_recommended
        ),
    }
    proofengineer_context["candidate_proof_state_provider"] = (
        proof_state_provider.name
    )
    return output


def _formalizer_repair_eval_provider(
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
        "unsupported Formalizer Lean repair eval provider: "
        f"{provider_name!r}; expected anthropic, openai, or static"
    )


def _prior_local_lean_failure_manifest(
    *,
    question: Any,
    out_dir: Path,
    lean_project: Path | None,
    lean_timeout: int,
) -> dict[str, Any]:
    task = AgentTask(
        task_id=f"formalizer-lean-repair-eval-prior-failure:{question.id}",
        owner_subsystem="FormalizationEvaluator",
        objective="create prior local-Lean failure feedback for component eval",
    )
    return _materialize_formalizer_lean_candidate_artifacts(
        root=out_dir / "prior_formalizer_lean_failure",
        question=question,
        task=task,
        proposal_packet={
            "packet_id": "formalizer_proposal:injected_prior_local_lean_failure",
            "formal_targets": [
                {
                    "id": "ai_statistician_formalizer_repair_candidate",
                    "informal_source": (
                        "injected prior failure for Formalizer Lean repair eval"
                    ),
                    "lean_statement_sketch": (
                        "theorem ai_statistician_formalizer_repair_candidate "
                        "(n : Nat) : n = n := by\n"
                        "  exact definitelyUnknownLeanProof n\n"
                    ),
                    "expected_status": "NEEDS_KERNEL_CHECK",
                }
            ],
        },
        local_lean=True,
        lean_project=lean_project,
        lean_timeout=lean_timeout,
    )


def _formalizer_repair_theory_packet(packet_id: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": "TheoryPacketForFormalizerLeanRepairEval",
        "packet_id": packet_id,
        "theorem_cards": [
            {
                "id": "formalizer_lean_candidate_repair_probe",
                "title": "Formalizer Lean-candidate repair probe",
                "claim": (
                    "A generated helper candidate should repair a local Lean "
                    "unknown-identifier failure while preserving the theorem target."
                ),
                "proof_obligations": ["local Lean compile for generated candidate"],
            }
        ],
        "formalization_requests": [
            {
                "id": "formalizer_lean_candidate_repair_probe",
                "target": (
                    "theorem ai_statistician_formalizer_repair_candidate "
                    "(n : Nat) : n = n"
                ),
                "reason": (
                    "Component eval for Formalizer/ProofEngineer generated "
                    "Lean-candidate repair; not a source theorem proof."
                ),
                "proof_obligations": ["local_lean_candidate_compile"],
            }
        ],
        "proof_plan": {
            "strategy": (
                "Use the rejected candidate and local Lean observations in "
                "runtime_environment_feedback to author a complete candidate."
            )
        },
    }


def _latest_formalizer_materialization_manifest(
    artifacts: Mapping[str, Any],
) -> Mapping[str, Any]:
    manifests = [
        artifact
        for artifact in artifacts.values()
        if isinstance(artifact, Mapping)
        and artifact.get("artifact_kind")
        == "RuntimeFormalizerLeanCandidateMaterialization"
    ]
    if not manifests:
        return {}
    return max(manifests, key=lambda row: str(row.get("created_at", "")))


def _formalizer_materialization_has_compiled_candidate(
    manifest: Mapping[str, Any],
) -> bool:
    return bool(
        int(manifest.get("n_candidate_sources", 0) or 0) > 0
        and int(manifest.get("n_candidate_artifacts_written", 0) or 0) > 0
        and int(manifest.get("n_local_lean_checked", 0) or 0) > 0
        and int(manifest.get("n_local_lean_compiled", 0) or 0) > 0
        and int(manifest.get("n_precheck_rejected", 0) or 0) == 0
    )


def _formalizer_lean_candidate_repair_sequence_counts(
    artifacts: Mapping[str, Any],
) -> dict[str, int]:
    manifests = [
        artifact
        for artifact in artifacts.values()
        if isinstance(artifact, Mapping)
        and artifact.get("artifact_kind")
        == "RuntimeFormalizerLeanCandidateMaterialization"
    ]
    manifests = sorted(manifests, key=lambda row: str(row.get("created_at", "")))
    saw_failure = False
    repair_sequences = 0
    for manifest in manifests:
        manifest_task_id = str(manifest.get("task_id", "") or "")
        manifest_is_proofengineer_repair = manifest_task_id.startswith(
            "formalize-lean-repair:"
        )
        rows = [
            row
            for row in manifest.get("candidate_rows", []) or []
            if isinstance(row, Mapping)
        ]
        manifest_failed = any(
            str(row.get("precheck_status", "") or "")
            == "REJECTED_BY_RUNTIME_PRECHECK"
            or (
                bool(row.get("local_lean_attempted", False))
                and not bool(row.get("local_lean_compiled", False))
            )
            for row in rows
        )
        manifest_passed = any(
            bool(row.get("local_lean_attempted", False))
            and bool(row.get("local_lean_compiled", False))
            for row in rows
        )
        if manifest_passed and manifest_is_proofengineer_repair and saw_failure:
            repair_sequences += 1
            saw_failure = False
        if manifest_failed:
            saw_failure = True
    return {
        "n_formalizer_lean_candidate_failed_then_passed_repair_sequences": (
            repair_sequences
        )
    }
