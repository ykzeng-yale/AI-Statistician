from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED,
)
from .model_backend import LIVE_EVALUATION_CLAUDE_MODEL_TIER
from .research_lab import build_research_provenance, run_research_benchmark
from .research_schema import (
    RESEARCH_EVIDENCE_DIMENSIONS,
    OpenResearchQuestion,
    research_dimension_requirements,
    research_task_intent_requirement,
)
from .research_trace_audit import audit_research_traces
from .verifier import AxleProofVerifier, MockProofVerifier, ProofVerifier


@dataclass(frozen=True)
class ResearchEvalConfig:
    seeds: tuple[int, ...]
    n_runs: int
    use_axle: bool = False


async def run_research_seed_eval(
    questions: list[OpenResearchQuestion],
    config: ResearchEvalConfig,
    out_dir: Path,
    *,
    proof_verifier: ProofVerifier | None = None,
) -> dict[str, object]:
    """Run the open-question research benchmark across multiple simulation seeds."""

    out_dir.mkdir(parents=True, exist_ok=True)
    verifier = proof_verifier or (AxleProofVerifier() if config.use_axle else MockProofVerifier())
    trials: list[dict[str, Any]] = []
    artifacts: list[dict[str, str]] = []
    for seed in config.seeds:
        seed_dir = out_dir / f"seed_{seed}"
        manifest = await run_research_benchmark(
            questions,
            seed_dir,
            proof_verifier=verifier,
            formal_source_index_path=seed_dir / "formal_source_index.sqlite",
            n_runs=config.n_runs,
            seed=seed,
        )
        trace_audit = audit_research_traces(seed_dir, seed_dir / "research_trace_audit")
        artifacts.append(
            {
                "seed": str(seed),
                "benchmark_manifest": str(seed_dir / "research_benchmark_manifest.json"),
                "trace_audit_manifest": str(seed_dir / "research_trace_audit" / "research_trace_audit_manifest.json"),
            }
        )
        for row in manifest["questions"]:
            trial = {
                "seed": seed,
                "trace_audit_ok": bool(trace_audit["all_ok"]),
                **row,
            }
            trials.append(trial)

    summary = _aggregate_trials(questions, trials)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "seeds": list(config.seeds),
            "n_runs": config.n_runs,
            "use_axle": config.use_axle,
            "verifier": verifier.name,
        },
        "provenance": build_research_provenance(),
        "n_questions": len(questions),
        "n_seeds": len(config.seeds),
        "all_ready_with_gaps": all(row["ready_rate"] == 1.0 for row in summary.values()),
        "all_trace_audits_ok": all(row["trace_audit_ok_rate"] == 1.0 for row in summary.values()),
        "summary": summary,
        "trials": trials,
        "artifacts": artifacts,
    }
    (out_dir / "research_evaluation_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def _aggregate_trials(questions: list[OpenResearchQuestion], trials: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for question in questions:
        rows = [row for row in trials if row["question"] == question.id]
        ready = sum(1 for row in rows if row["status"] == "RESEARCH_TRACE_READY_WITH_FORMAL_GAPS")
        sim_flagged = sum(1 for row in rows if row["status"] == "SIMULATION_FLAGGED_WITH_FORMAL_GAPS")
        formal_blocked = sum(1 for row in rows if row["status"] == "FORMAL_BLOCKED")
        trace_ok = sum(1 for row in rows if row["trace_audit_ok"])
        procedure_metrics: dict[str, dict[str, list[float]]] = {}
        for row in rows:
            for sim in row.get("simulations", []):
                procedure_id = str(sim.get("procedure_id"))
                metrics = sim.get("metrics", {})
                if not isinstance(metrics, dict):
                    continue
                procedure_metrics.setdefault(procedure_id, {})
                for key, value in metrics.items():
                    if isinstance(value, (int, float)) and math.isfinite(float(value)):
                        procedure_metrics[procedure_id].setdefault(key, []).append(float(value))
        procedures = {
            procedure_id: {
                metric: {
                    "mean": _mean(values),
                    "sd": _sample_sd(values),
                    "min": min(values),
                    "max": max(values),
                }
                for metric, values in metrics.items()
                if values
            }
            for procedure_id, metrics in procedure_metrics.items()
        }
        out[question.id] = {
            "trials": len(rows),
            "ready_with_gaps": ready,
            "simulation_flagged": sim_flagged,
            "formal_blocked": formal_blocked,
            "ready_rate": ready / len(rows) if rows else 0.0,
            "trace_audit_ok": trace_ok,
            "trace_audit_ok_rate": trace_ok / len(rows) if rows else 0.0,
            "procedures": procedures,
        }
    return out


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sample_sd(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


STRICT_FORMAL_SUBSYSTEMS = frozenset(
    {
        "FormalTargetSemanticReviewer",
        "FormalizationEvaluator",
        "TheoremReductionClosureProofEngineer",
        "ExactSourceTheoremProofBodyExecutor",
        "SourceSemanticProofEngineer",
        "PseudoFormalBlockVerifier",
        "SourceTheoremPromotionProofEngineer",
        "FormalizationEvaluator",
        "ExactSourceTheoremProver",
        "FormalizationGapPlanner",
    }
)


def _runtime_artifacts(result: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    blackboard = result.get("blackboard", {})
    artifacts = (
        blackboard.get("artifacts", {})
        if isinstance(blackboard, Mapping)
        and isinstance(blackboard.get("artifacts", {}), Mapping)
        else {}
    )
    return {
        str(artifact_id): artifact
        for artifact_id, artifact in artifacts.items()
        if isinstance(artifact, Mapping)
    }


def _final_accepted_critic_manifest(
    result: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    traces = result.get("traces", [])
    if not isinstance(traces, Sequence) or isinstance(
        traces, (str, bytes, bytearray)
    ):
        return {}
    for trace in reversed(traces):
        if not isinstance(trace, Mapping):
            continue
        if (
            trace.get("subsystem") != "CriticEvaluator"
            or trace.get("status") != "ACCEPTED"
        ):
            continue
        artifact_ids = trace.get("produced_artifact_ids", [])
        if not isinstance(artifact_ids, Sequence) or isinstance(
            artifact_ids, (str, bytes, bytearray)
        ):
            continue
        for artifact_id in reversed(artifact_ids):
            artifact = artifacts.get(str(artifact_id), {})
            decision = artifact.get("evidence_contract_decision", {})
            if (
                artifact.get("artifact_kind") == "RuntimeCriticEvaluatorManifest"
                and isinstance(decision, Mapping)
                and decision.get("runtime_status") == "ACCEPTED"
            ):
                return artifact
    return {}


def _critic_gap_disclosure_present(
    critic_manifest: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
) -> bool:
    proposal_id = str(
        critic_manifest.get("llm_critic_evaluator_proposal_id", "") or ""
    )
    proposal = artifacts.get(proposal_id, {})
    disclosure = proposal.get("gap_disclosure", {})
    return bool(
        proposal.get("artifact_kind") == "CriticEvaluatorProposalPacket"
        and isinstance(disclosure, Mapping)
        and disclosure.get("status") == "COMPLETE"
        and isinstance(disclosure.get("disclosed_gaps"), list)
        and isinstance(disclosure.get("evidence_refs"), list)
        and str(disclosure.get("rationale", "") or "").strip()
    )


def _critic_research_disposition_accepted(
    critic_manifest: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
) -> bool:
    proposal_id = str(
        critic_manifest.get("llm_critic_evaluator_proposal_id", "") or ""
    )
    proposal = artifacts.get(proposal_id, {})
    disposition = proposal.get("research_disposition", {})
    dimensions = proposal.get("dimension_assessments", [])
    decision = critic_manifest.get("evidence_contract_decision", {})
    if not (
        proposal.get("artifact_kind") == "CriticEvaluatorProposalPacket"
        and isinstance(disposition, Mapping)
        and disposition.get("status") == "ACCEPT"
        and not disposition.get("blocking_dimensions")
        and isinstance(dimensions, list)
        and isinstance(decision, Mapping)
        and decision.get("scientific_disposition") == "ACCEPT"
        and decision.get("runtime_status") == "ACCEPTED"
    ):
        return False
    status_by_dimension = {
        str(row.get("dimension", "") or ""): str(row.get("status", "") or "")
        for row in dimensions
        if isinstance(row, Mapping)
    }
    raw_requirements = proposal.get("dimension_requirements", {})
    requirements = research_dimension_requirements(
        raw_requirements if isinstance(raw_requirements, Mapping) else {}
    )
    if not requirements:
        requirements = {
            "theory": "required",
            "scientific_code": "required",
            "empirical": "required",
            "formal": "optional",
        }
    for dimension in RESEARCH_EVIDENCE_DIMENSIONS:
        status = status_by_dimension.get(dimension, "")
        requirement = requirements[dimension]
        if status == "CONTRADICTED":
            return False
        if requirement == "required" and status != "SUPPORTED":
            return False
        if requirement == "not_applicable" and status != "NOT_REQUESTED":
            return False
    return True


def _question_task_intent(
    artifacts: Mapping[str, Mapping[str, Any]],
) -> dict[str, str]:
    for artifact in artifacts.values():
        if artifact.get("artifact_kind") != "RuntimeQuestionMetadata":
            continue
        question = artifact.get("question", {})
        task_intent = (
            question.get("task_intent", {})
            if isinstance(question, Mapping)
            else {}
        )
        if isinstance(task_intent, Mapping):
            return {
                str(dimension): str(requirement)
                for dimension, requirement in task_intent.items()
            }
    return {}


def _semantic_review_accepted(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    source_subsystem: str,
    source_manifest_id: str,
    source_manifest: Mapping[str, Any],
    require_confirmatory_empirical_evidence: bool,
) -> bool:
    if not source_manifest_id or not source_manifest:
        return False
    source_manifest_hash = stable_hash(dict(source_manifest))
    return any(
        row.get("artifact_kind")
        == "RuntimeGeneratedCodeSemanticReviewExecutionManifest"
        and row.get("source_subsystem") == source_subsystem
        and row.get("source_manifest_id") == source_manifest_id
        and row.get("source_manifest_hash") == source_manifest_hash
        and row.get("semantic_review_accepted") is True
        and row.get("independent_agent") is True
        and row.get("independent_invocation") is True
        and str(row.get("reviewer_model_tier", "") or "").lower()
        == LIVE_EVALUATION_CLAUDE_MODEL_TIER
        and (
            not require_confirmatory_empirical_evidence
            or row.get("confirmatory_empirical_evidence_eligible") is True
        )
        for row in artifacts.values()
    )


def _latest_independently_reviewed_manifest(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    artifact_kind: str,
    source_subsystem: str,
    require_confirmatory_empirical_evidence: bool,
) -> tuple[str, Mapping[str, Any]]:
    for artifact_id, artifact in reversed(list(artifacts.items())):
        if artifact.get("artifact_kind") != artifact_kind:
            continue
        if _semantic_review_accepted(
            artifacts,
            source_subsystem=source_subsystem,
            source_manifest_id=str(artifact_id),
            source_manifest=artifact,
            require_confirmatory_empirical_evidence=(
                require_confirmatory_empirical_evidence
            ),
        ):
            return str(artifact_id), artifact
    return "", {}


def _latest_serious_theory_packet(
    artifacts: Mapping[str, Mapping[str, Any]],
) -> tuple[str, Mapping[str, Any]]:
    for artifact_id, artifact in reversed(list(artifacts.items())):
        if (
            artifact.get("artifact_kind") == "TheoryDerivationPacket"
            and artifact.get("serious_theory_mode") is True
            and str(artifact.get("provider", "") or "") in {"anthropic", "openai"}
            and artifact.get("packet_id") == artifact_id
        ):
            return str(artifact_id), artifact
    return "", {}


def _theory_preexecution_review_accepted(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    theory_packet_id: str,
    theory_packet: Mapping[str, Any],
) -> bool:
    if not theory_packet_id or not theory_packet:
        return False
    theory_packet_hash = stable_hash(dict(theory_packet))
    for acceptance in artifacts.values():
        if not (
            acceptance.get("artifact_kind")
            == "RuntimeArchitectTheoryExecutionPreflightAcceptance"
            and acceptance.get("source_theory_packet_id") == theory_packet_id
            and acceptance.get("source_theory_packet_hash") == theory_packet_hash
        ):
            continue
        preflight_id = str(acceptance.get("preflight_packet_id", "") or "")
        preflight = artifacts.get(preflight_id, {})
        if (
            preflight.get("artifact_kind")
            == "ArchitectTheoryExecutionPreflightReviewPacket"
            and stable_hash(dict(preflight))
            == str(acceptance.get("preflight_packet_hash", "") or "")
            and preflight.get("source_theory_packet_id") == theory_packet_id
            and preflight.get("source_theory_packet_hash") == theory_packet_hash
            and preflight.get("overall_verdict") == "ACCEPT"
            and not preflight.get("active_unresolved_finding_ids")
        ):
            return True
    return False


def _metric_protocol_accepted(packet: Mapping[str, Any]) -> bool:
    contract = packet.get("evidence_contract", {})
    if not isinstance(contract, Mapping):
        return False
    review = contract.get("empirical_metric_requirements_preexecution_review", {})
    return bool(
        isinstance(review, Mapping)
        and contract.get("empirical_metric_protocol_phase")
        == METRIC_PROTOCOL_PHASE_PREEXECUTION_REVIEW_ACCEPTED
        and contract.get("metric_protocol_execution_authorized") is True
        and contract.get("empirical_metric_requirements")
        and review.get("overall_verdict") == "ACCEPT"
        and all(
            review.get(field) is True
            for field in (
                "independent_agent",
                "independent_invocation",
            )
        )
    )


def _latest_metric_protocol_packet(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    theory_packet_id: str,
    theory_packet: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any]]:
    if not theory_packet_id or not theory_packet:
        return "", {}
    theory_packet_hash = stable_hash(dict(theory_packet))
    for artifact_id, artifact in reversed(list(artifacts.items())):
        if (
            artifact.get("artifact_kind") != "ArchitectCoordinatorProposalPacket"
            or not _metric_protocol_accepted(artifact)
        ):
            continue
        authoring = artifact.get("metric_requirement_authoring", {})
        if not isinstance(authoring, Mapping):
            continue
        if (
            authoring.get("source_theory_packet_id") == theory_packet_id
            and authoring.get("source_theory_packet_hash") == theory_packet_hash
        ):
            return str(artifact_id), artifact
    return "", {}


def _simulation_has_bound_nonvacuous_metric_evidence(
    simulation_manifest: Mapping[str, Any],
    *,
    requirement_set_id: str,
) -> bool:
    if not requirement_set_id:
        return False
    if int(
        simulation_manifest.get(
            "n_generated_simulation_typed_metric_contracts_declared", 0
        )
        or 0
    ) <= 0:
        return False
    if int(
        simulation_manifest.get(
            "n_generated_simulation_typed_metric_contracts_evaluated", 0
        )
        or 0
    ) <= 0:
        return False
    if int(
        simulation_manifest.get(
            "n_generated_simulation_typed_metric_contracts_passed", 0
        )
        or 0
    ) <= 0:
        return False
    prototypes = simulation_manifest.get(
        "generated_simulation_sandbox_prototypes", []
    )
    if not isinstance(prototypes, Sequence) or isinstance(
        prototypes, (str, bytes, bytearray)
    ):
        return False
    for prototype in prototypes:
        if not isinstance(prototype, Mapping):
            continue
        evaluation = prototype.get("metric_contract_evaluation", {})
        if not isinstance(evaluation, Mapping):
            continue
        if (
            prototype.get("smoke_passed") is True
            and prototype.get("metric_requirement_authority_validated") is True
            and str(prototype.get("metric_requirement_set_id", "") or "")
            == requirement_set_id
            and str(evaluation.get("metric_requirement_set_id", "") or "")
            == requirement_set_id
            and evaluation.get("metric_requirement_authority_validated") is True
            and int(evaluation.get("n_contracts", 0) or 0) > 0
            and int(evaluation.get("n_passed", 0) or 0) > 0
            and evaluation.get("all_required_passed") is True
        ):
            return True
    return False


def _question_id(
    result: Mapping[str, Any],
    critic_manifest: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
) -> str:
    question = critic_manifest.get("question", {})
    if isinstance(question, Mapping) and question.get("id"):
        return str(question["id"])
    for artifact in artifacts.values():
        if artifact.get("artifact_kind") != "RuntimeQuestionMetadata":
            continue
        question = artifact.get("question", {})
        if isinstance(question, Mapping) and question.get("id"):
            return str(question["id"])
    traces = result.get("traces", [])
    first = (
        traces[0]
        if isinstance(traces, Sequence)
        and not isinstance(traces, (str, bytes, bytearray))
        and traces
        else {}
    )
    task = first.get("task", {}) if isinstance(first, Mapping) else {}
    inputs = task.get("inputs", {}) if isinstance(task, Mapping) else {}
    question = inputs.get("question", {}) if isinstance(inputs, Mapping) else {}
    return str(question.get("id", "") or "") if isinstance(question, Mapping) else ""


def _latest_source_replication_checkpoint(
    artifacts: Mapping[str, Mapping[str, Any]],
    *,
    question_id: str,
) -> Mapping[str, Any]:
    """Find a runtime-validated source checkpoint; hidden gold remains separate."""

    for artifact_id, artifact in reversed(list(artifacts.items())):
        report = artifact.get("report_document", {})
        unresolved_gaps = artifact.get("unresolved_gaps")
        if (
            artifact.get("artifact_kind") == "SourceReplicationCheckpoint"
            and artifact.get("checkpoint_id") == artifact_id
            and artifact.get("question_id") == question_id
            and artifact.get("runtime_completion_status")
            == "SOURCE_EXECUTION_RECORDED_REQUIRES_HIDDEN_EVALUATION"
            and artifact.get("model_authored_report") is True
            and artifact.get("runtime_edited_report") is False
            and artifact.get("runtime_edited_source") is False
            and isinstance(report, Mapping)
            and str(report.get("relative_path", "") or "").strip()
            and isinstance(unresolved_gaps, list)
            and all(
                isinstance(value, str) and value.strip()
                for value in unresolved_gaps
            )
        ):
            return artifact
    return {}


def build_research_evaluation_summary(
    results: Sequence[Mapping[str, Any]],
    *,
    evaluation_mode: str,
    schema_version: str,
) -> dict[str, Any]:
    applies = str(evaluation_mode or "").strip() == "research_eval"
    rows: list[dict[str, Any]] = []
    for result in results:
        artifacts = _runtime_artifacts(result)
        task_intent = _question_task_intent(artifacts)
        dimension_requirements = research_dimension_requirements(task_intent)
        explicit_task_intent = bool(dimension_requirements)
        source_replication_requirement = research_task_intent_requirement(
            task_intent,
            "source_replication",
        )
        if not dimension_requirements:
            dimension_requirements = {
                "theory": "required",
                "scientific_code": "required",
                "empirical": "required",
                "formal": "optional",
            }
        critic_manifest = _final_accepted_critic_manifest(result, artifacts)
        question_id = _question_id(result, critic_manifest, artifacts)
        source_replication_checkpoint = _latest_source_replication_checkpoint(
            artifacts,
            question_id=question_id,
        )
        if critic_manifest:
            theory_packet_id = str(
                critic_manifest.get("theory_packet_id", "") or ""
            )
            algorithm_manifest_id = str(
                critic_manifest.get("algorithm_sandbox_manifest_id", "") or ""
            )
            simulation_manifest_id = str(
                critic_manifest.get("simulation_manifest_id", "") or ""
            )
        else:
            algorithm_manifest_id, algorithm_manifest = (
                _latest_independently_reviewed_manifest(
                    artifacts,
                    artifact_kind="RuntimeAlgorithmSandboxManifest",
                    source_subsystem="AlgorithmEngineer",
                    require_confirmatory_empirical_evidence=False,
                )
            )
            simulation_manifest_id, simulation_manifest = (
                _latest_independently_reviewed_manifest(
                    artifacts,
                    artifact_kind="RuntimeSimulationManifest",
                    source_subsystem="SimulationEvaluator",
                    require_confirmatory_empirical_evidence=True,
                )
            )
            theory_packet_id = str(
                algorithm_manifest.get("theory_packet_id", "")
                or simulation_manifest.get("theory_packet_id", "")
                or ""
            )
            if not theory_packet_id:
                theory_packet_id, _ = _latest_serious_theory_packet(artifacts)
        theory_packet = artifacts.get(theory_packet_id, {})
        algorithm_manifest = artifacts.get(algorithm_manifest_id, {})
        simulation_manifest = artifacts.get(simulation_manifest_id, {})
        simulation_control = simulation_manifest.get("runtime_architect_control", {})
        architect_packet_id = (
            str(
                simulation_control.get("architect_coordinator_proposal_id", "")
                or ""
            )
            if isinstance(simulation_control, Mapping)
            else ""
        )
        architect_packet = artifacts.get(architect_packet_id, {})
        if not _metric_protocol_accepted(architect_packet):
            architect_packet_id, architect_packet = _latest_metric_protocol_packet(
                artifacts,
                theory_packet_id=theory_packet_id,
                theory_packet=theory_packet,
            )
        architect_contract = architect_packet.get("evidence_contract", {})
        final_requirement_set_id = (
            str(
                architect_contract.get(
                    "empirical_metric_requirement_set_id", ""
                )
                or ""
            )
            if isinstance(architect_contract, Mapping)
            else ""
        )
        traces = result.get("traces", [])
        executed = {
            str(trace.get("subsystem", "") or "")
            for trace in traces
            if isinstance(trace, Mapping)
        } if isinstance(traces, Sequence) and not isinstance(
            traces, (str, bytes, bytearray)
        ) else set()
        formal_manifests = [
            artifact
            for artifact in artifacts.values()
            if artifact.get("artifact_kind") == "RuntimeFormalizationManifest"
        ]
        capability_checks = {
            "source_replication_checkpoint_recorded": bool(
                source_replication_checkpoint
            ),
            "source_replication_unresolved_gap_disclosure_present": bool(
                source_replication_checkpoint
                and isinstance(
                    source_replication_checkpoint.get("unresolved_gaps"), list
                )
            ),
            "serious_theory_completed": bool(
                theory_packet.get("artifact_kind") == "TheoryDerivationPacket"
                and theory_packet.get("packet_id") == theory_packet_id
                and theory_packet.get("serious_theory_mode") is True
                and str(theory_packet.get("provider", "") or "")
                in {"anthropic", "openai"}
            ),
            "theory_preexecution_review_accepted": bool(
                _theory_preexecution_review_accepted(
                    artifacts,
                    theory_packet_id=theory_packet_id,
                    theory_packet=theory_packet,
                )
            ),
            "generated_algorithm_executed_and_passed": bool(
                algorithm_manifest.get("artifact_kind")
                == "RuntimeAlgorithmSandboxManifest"
                and algorithm_manifest.get("manifest_id") == algorithm_manifest_id
                and algorithm_manifest.get("theory_packet_id") == theory_packet_id
                and int(
                    algorithm_manifest.get("n_live_generated_code_executed", 0)
                    or 0
                )
                > 0
                and int(algorithm_manifest.get("n_passed", 0) or 0) > 0
                and int(
                    algorithm_manifest.get(
                        "n_live_generated_code_execution_failed", 0
                    )
                    or 0
                )
                == 0,
            ),
            "metric_protocol_independently_accepted": bool(
                architect_packet.get("artifact_kind")
                == "ArchitectCoordinatorProposalPacket"
                and architect_packet.get("packet_id") == architect_packet_id
                and _metric_protocol_accepted(architect_packet)
            ),
            "algorithm_semantic_review_accepted": _semantic_review_accepted(
                artifacts,
                source_subsystem="AlgorithmEngineer",
                source_manifest_id=algorithm_manifest_id,
                source_manifest=algorithm_manifest,
                require_confirmatory_empirical_evidence=False,
            ),
            "generated_simulation_executed_and_passed": bool(
                simulation_manifest.get("artifact_kind")
                == "RuntimeSimulationManifest"
                and simulation_manifest.get("manifest_id") == simulation_manifest_id
                and simulation_manifest.get("theory_packet_id") == theory_packet_id
                and int(
                    simulation_manifest.get(
                        "n_live_generated_simulation_sandbox_executed", 0
                    )
                    or 0
                )
                > 0
                and simulation_manifest.get("generated_simulation_passed") is True
                and simulation_manifest.get("simulation_passed") is True
            ),
            "simulation_metric_evidence_nonvacuous_and_bound": (
                _simulation_has_bound_nonvacuous_metric_evidence(
                    simulation_manifest,
                    requirement_set_id=final_requirement_set_id,
                )
            ),
            "simulation_semantic_review_accepted": _semantic_review_accepted(
                artifacts,
                source_subsystem="SimulationEvaluator",
                source_manifest_id=simulation_manifest_id,
                source_manifest=simulation_manifest,
                require_confirmatory_empirical_evidence=True,
            ),
            "exact_formal_target_kernel_closed": any(
                manifest.get("source_theorem_kernel_verified") is True
                and bool(
                    manifest.get(
                        "source_theorem_kernel_verified_target_ids", []
                    )
                )
                for manifest in formal_manifests
            ),
            "critic_research_acceptance": bool(
                critic_manifest
                and result.get("status") == "ACCEPTED"
                and _critic_research_disposition_accepted(
                    critic_manifest,
                    artifacts,
                )
            ),
            "critic_unresolved_gap_disclosure_present": (
                _critic_gap_disclosure_present(critic_manifest, artifacts)
            ),
        }
        theory_required = bool(
            not explicit_task_intent
            or dimension_requirements["theory"] == "required"
        )
        scientific_code_required = bool(
            dimension_requirements["scientific_code"] == "required"
        )
        empirical_required = bool(
            dimension_requirements["empirical"] == "required"
        )
        source_replication_required = bool(
            source_replication_requirement == "required"
        )
        required_capability_checks: list[str] = []
        if source_replication_required:
            required_capability_checks.extend(
                (
                    "source_replication_checkpoint_recorded",
                    "source_replication_unresolved_gap_disclosure_present",
                )
            )
        if theory_required:
            required_capability_checks.append("serious_theory_completed")
        if empirical_required:
            required_capability_checks.append(
                "theory_preexecution_review_accepted"
            )
        if scientific_code_required:
            required_capability_checks.extend(
                (
                    "generated_algorithm_executed_and_passed",
                    "algorithm_semantic_review_accepted",
                )
            )
        if empirical_required:
            required_capability_checks.extend(
                (
                    "metric_protocol_independently_accepted",
                    "generated_simulation_executed_and_passed",
                    "simulation_metric_evidence_nonvacuous_and_bound",
                    "simulation_semantic_review_accepted",
                )
            )
        substantive_review_required = bool(
            theory_required or scientific_code_required or empirical_required
        )
        if substantive_review_required:
            required_capability_checks.extend(
                (
                    "critic_research_acceptance",
                    "critic_unresolved_gap_disclosure_present",
                )
            )
        formal_executed = bool(executed & STRICT_FORMAL_SUBSYSTEMS)
        formal_requirement = dimension_requirements["formal"]
        if formal_requirement == "required":
            required_capability_checks.append(
                "exact_formal_target_kernel_closed"
            )
        if formal_requirement == "required":
            formal_intent_conformant = formal_executed
        elif formal_requirement == "not_applicable":
            formal_intent_conformant = not formal_executed
        else:
            formal_intent_conformant = True
        conformance_checks = {
            "strict_formal_lane_not_executed": not formal_executed,
            "formal_lane_task_intent_conformant": formal_intent_conformant,
        }
        research_loop_complete = bool(
            applies
            and all(
                capability_checks[name] for name in required_capability_checks
            )
        )
        mode_conformant = bool(
            applies
            and conformance_checks["formal_lane_task_intent_conformant"]
            and (
                conformance_checks["strict_formal_lane_not_executed"]
                if not explicit_task_intent
                else True
            )
        )
        rows.append(
            {
                "question_id": question_id,
                "research_loop_complete": research_loop_complete,
                "mode_conformant": mode_conformant,
                "research_eval_complete": bool(
                    research_loop_complete
                ),
                "requirements": capability_checks,
                "dimension_requirements": {
                    **(
                        {"source_replication": source_replication_requirement}
                        if "source_replication" in task_intent
                        else {}
                    ),
                    **dimension_requirements,
                },
                "required_capability_checks": required_capability_checks,
                "mode_conformance": conformance_checks,
                "formalization_status": {
                    "required_for_research_eval": (
                        formal_requirement == "required"
                    ),
                    "strict_formal_lane_executed": bool(
                        executed & STRICT_FORMAL_SUBSYSTEMS
                    ),
                    "n_formalization_manifests": len(formal_manifests),
                    "n_kernel_verified_subclaims": sum(
                        int(
                            (row.get("counts", {}) or {}).get("kernel_verified", 0)
                            or 0
                        )
                        for row in formal_manifests
                        if isinstance(row.get("counts", {}), Mapping)
                    ),
                },
            }
        )
    return {
        "schema_version": schema_version,
        "artifact_kind": "RuntimeResearchEvaluationSummary",
        "evaluation_mode": str(evaluation_mode or "debug"),
        "applies": applies,
        "n_questions": len(rows),
        "n_questions_research_loop_complete": sum(
            row["research_loop_complete"] is True for row in rows
        ),
        "all_questions_research_loop_complete": bool(
            applies and rows and all(row["research_loop_complete"] for row in rows)
        ),
        "n_questions_mode_conformant": sum(
            row["mode_conformant"] is True for row in rows
        ),
        "all_questions_mode_conformant": bool(
            applies and rows and all(row["mode_conformant"] for row in rows)
        ),
        "n_questions_research_eval_complete": sum(
            row["research_eval_complete"] is True for row in rows
        ),
        "all_questions_research_eval_complete": bool(
            applies and rows and all(row["research_eval_complete"] for row in rows)
        ),
        "rows": rows,
        "evidence_boundary": (
            "This is research-loop evidence only. Theory, generated code, simulation, "
            "and semantic review are not theorem proof; formalization and kernel "
            "closure remain separately reported and are required only when selected "
            "task intent marks formal evidence required. "
            "Mode conformance is diagnostic and cannot erase completed research evidence."
        ),
    }
