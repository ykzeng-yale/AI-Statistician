from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .fingerprint import stable_hash
from .model_backend import is_live_generator_backend
from .research_agent_runtime import _generated_sandbox_repair_sequence_counts
from .task_family import is_explicit_task_family, task_family_value


SCHEMA_VERSION = 1
ARTIFACT_KIND = "FreshStartCrossTaskE2EEvidenceAudit"
MIN_COMPLETE_TASKS = 2
REQUIRED_THEORY_CONSUMERS = frozenset(
    {"AlgorithmEngineer", "SimulationEngineer", "FormalizerProofEngineer"}
)
NON_LIVE_PROVIDER_MARKERS = ("fixture", "mock", "static", "replay")


def audit_fresh_start_cross_task_e2e(
    *,
    runtime_manifest: Mapping[str, Any],
    result_payloads: Sequence[Mapping[str, Any]],
    row_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind end-to-end capability evidence per task before aggregating families.

    This audit deliberately refuses aggregate counter substitution. Each task
    must carry its own Architect, theory, executable code, simulation, retrieval,
    Lean feedback, and exact source-theorem proof lineage.
    """

    input_context = _mapping(runtime_manifest.get("runtime_input_context"))
    resume_context = _mapping(runtime_manifest.get("runtime_resume_context"))
    fresh_start = bool(
        str(runtime_manifest.get("runtime_resume_policy", "") or "")
        == "fresh_start"
        and runtime_manifest.get("runtime_resumed_from_pending_task") is not True
        and resume_context.get("resumed_from_pending_task") is not True
        and input_context.get("runtime_learning_memory_supplied") is not True
        and _safe_int(input_context.get("runtime_learning_memory_rows_loaded")) == 0
    )
    live_only_topology = bool(
        _safe_int(runtime_manifest.get("n_live_generator_agents_enabled")) > 0
        and _safe_int(runtime_manifest.get("n_static_generator_agents_enabled")) == 0
        and _safe_int(runtime_manifest.get("unsupported_generator_backends_enabled"))
        == 0
    )

    task_rows: list[dict[str, Any]] = []
    for index, result in enumerate(result_payloads):
        summary = row_summaries[index] if index < len(row_summaries) else {}
        task_rows.append(
            _audit_task_e2e(
                result=result,
                summary=summary,
                fresh_start=fresh_start,
                live_only_topology=live_only_topology,
            )
        )

    complete_rows = [row for row in task_rows if row["complete"] is True]
    question_ids = _unique_nonempty(row["question_id"] for row in task_rows)
    project_ids = _unique_nonempty(row["project_id"] for row in task_rows)
    complete_families = _unique_nonempty(
        row["task_family"] for row in complete_rows
    )
    complete_question_ids = _unique_nonempty(
        row["question_id"] for row in complete_rows
    )
    complete_source_lineage_ids = _unique_nonempty(
        row["source_proof_lineage_id"] for row in complete_rows
    )
    complete_theory_packet_ids = _unique_nonempty(
        row["theory_packet_id"] for row in complete_rows
    )
    complete_formalization_manifest_ids = _unique_nonempty(
        row["formalization_manifest_id"] for row in complete_rows
    )
    complete_source_proof_manifest_ids = _unique_nonempty(
        row["source_proof_manifest_id"] for row in complete_rows
    )
    identities_independent = bool(
        len(question_ids) == len(task_rows)
        and len(project_ids) == len(task_rows)
        and len(complete_source_lineage_ids) == len(complete_rows)
        and len(complete_theory_packet_ids) == len(complete_rows)
        and len(complete_formalization_manifest_ids) == len(complete_rows)
        and len(complete_source_proof_manifest_ids) == len(complete_rows)
    )
    cross_task_ready = bool(
        fresh_start
        and live_only_topology
        and len(task_rows) >= MIN_COMPLETE_TASKS
        and len(complete_rows) == len(task_rows)
        and len(complete_question_ids) >= MIN_COMPLETE_TASKS
        and len(complete_families) >= MIN_COMPLETE_TASKS
        and identities_independent
    )
    run_gates = {
        "fresh_start_without_task_learning_memory": fresh_start,
        "live_generator_topology_without_static_backends": live_only_topology,
        "at_least_two_tasks": len(task_rows) >= MIN_COMPLETE_TASKS,
        "all_tasks_complete": bool(task_rows) and len(complete_rows) == len(task_rows),
        "at_least_two_explicit_task_families": (
            len(complete_families) >= MIN_COMPLETE_TASKS
        ),
        "independent_task_and_proof_lineages": identities_independent,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "evaluation_contract": "fresh_start_per_task_evidence_graph_v1",
        "n_tasks": len(task_rows),
        "n_complete_tasks": len(complete_rows),
        "n_complete_task_families": len(complete_families),
        "question_ids": question_ids,
        "project_ids": project_ids,
        "complete_question_ids": complete_question_ids,
        "complete_task_families": complete_families,
        "complete_source_proof_lineage_ids": complete_source_lineage_ids,
        "complete_theory_packet_ids": complete_theory_packet_ids,
        "complete_formalization_manifest_ids": complete_formalization_manifest_ids,
        "complete_source_proof_manifest_ids": complete_source_proof_manifest_ids,
        "run_gates": run_gates,
        "task_rows": task_rows,
        "cross_task_full_e2e_generalization_demonstrated": cross_task_ready,
        "proof_evidence_status": "CROSS_TASK_CAPABILITY_AUDIT_NOT_PROOF_EVIDENCE",
        "boundary": (
            "This audit binds already-recorded runtime and kernel evidence into a "
            "cross-task capability claim. It does not itself prove either theorem. "
            "Aggregate family, repair, or kernel counters cannot satisfy this gate "
            "without complete per-task artifact lineages."
        ),
        "audit_fingerprint": stable_hash(
            {
                "run_gates": run_gates,
                "task_rows": task_rows,
                "complete_task_families": complete_families,
            }
        ),
    }


def _audit_task_e2e(
    *,
    result: Mapping[str, Any],
    summary: Mapping[str, Any],
    fresh_start: bool,
    live_only_topology: bool,
) -> dict[str, Any]:
    blackboard = _mapping(result.get("blackboard"))
    artifacts = _mapping(blackboard.get("artifacts"))
    artifact_rows = [row for row in artifacts.values() if isinstance(row, Mapping)]
    traces = result.get("traces", [])
    if not isinstance(traces, list):
        traces = []

    question_id = str(summary.get("question_id", "") or "").strip()
    task_family = task_family_value(summary.get("task_family", ""))
    project_id = str(blackboard.get("project_id", "") or "").strip()

    architect_packets = _artifacts_of_kind(
        artifact_rows, "ArchitectCoordinatorProposalPacket"
    )
    architect_packet = _latest_live_packet(architect_packets)
    architect_controlled = bool(
        summary.get("architect_coordinator_enabled") is True
        and traces
        and _mapping(traces[0]).get("subsystem") == "ArchitectCoordinator"
        and architect_packet
        and architect_packet.get("ok") is True
        and architect_packet.get("subsystem_execution_plan")
        and _artifact_question_id(architect_packet) == question_id
    )

    theory_packets = _artifacts_of_kind(
        artifact_rows, "TheoryDerivationPacket", "RuntimeTheoryDerivationPacket"
    )
    theory_packet = _latest_live_packet(theory_packets)
    theory_packet_id = str(
        (theory_packet or {}).get("packet_id", "")
        or (theory_packet or {}).get("manifest_id", "")
        or ""
    )
    structured_theory = _structured_theory_packet(theory_packet)
    structured_theory = bool(
        structured_theory and _artifact_question_id(theory_packet) == question_id
    )
    theory_consumers = _theory_consumers(
        artifact_rows,
        theory_packet_id,
        question_id=question_id,
    )
    theory_handoff_complete = bool(
        structured_theory and REQUIRED_THEORY_CONSUMERS.issubset(theory_consumers)
    )

    retrieval_rows = _artifacts_of_kind(
        artifact_rows, "RuntimeRetrievalMemoryManifest"
    )
    formal_source_rag = any(
        _retrieval_has_formal_source_hits(row)
        and _artifact_question_id(row) == question_id
        for row in retrieval_rows
    )

    algorithm_rows = _artifacts_of_kind(
        artifact_rows, "RuntimeAlgorithmSandboxManifest"
    )
    simulation_rows = _artifacts_of_kind(
        artifact_rows, "RuntimeSimulationManifest"
    )
    accepted_algorithm_manifest_ids = {
        str(row.get("manifest_id", "") or "")
        for row in algorithm_rows
        if str(row.get("theory_packet_id", "") or "") == theory_packet_id
        and _artifact_question_id(row) == question_id
        and _safe_int(row.get("n_live_generated_code_executed")) > 0
        and _safe_int(row.get("n_passed")) > 0
    }
    accepted_simulation_manifest_ids = {
        str(row.get("manifest_id", "") or "")
        for row in simulation_rows
        if str(row.get("theory_packet_id", "") or "") == theory_packet_id
        and _artifact_question_id(row) == question_id
        and row.get("confirmatory_empirical_evidence_eligible") is True
        and _safe_int(row.get("n_live_generated_simulation_sandbox_executed")) > 0
        and _safe_int(row.get("n_live_generated_simulation_sandbox_passed")) > 0
    }
    algorithm_execution = bool(
        _safe_int(summary.get("n_live_generated_code_sandbox_executed")) > 0
        and accepted_algorithm_manifest_ids
    )
    simulation_execution = bool(
        _safe_int(summary.get("n_live_generated_simulation_sandbox_executed")) > 0
        and accepted_simulation_manifest_ids
    )
    semantic_review_rows = _artifacts_of_kind(
        artifact_rows,
        "RuntimeGeneratedCodeSemanticReviewExecutionManifest",
    )
    algorithm_semantic_review = _has_independent_accepted_semantic_review(
        semantic_review_rows,
        question_id=question_id,
        source_subsystem="AlgorithmEngineer",
        source_manifest_ids=accepted_algorithm_manifest_ids,
    )
    simulation_semantic_review = _has_independent_accepted_semantic_review(
        semantic_review_rows,
        question_id=question_id,
        source_subsystem="SimulationEvaluator",
        source_manifest_ids=accepted_simulation_manifest_ids,
        require_confirmatory=True,
    )
    repair_counts = _generated_sandbox_repair_sequence_counts(artifacts)
    algorithm_failure_observed = any(
        str(row.get("theory_packet_id", "") or "") == theory_packet_id
        and _artifact_question_id(row) == question_id
        and (
            _safe_int(row.get("n_generated_code_execution_failed")) > 0
            or _safe_int(row.get("n_unsafe_generated_code_rejected")) > 0
        )
        for row in algorithm_rows
    )
    simulation_failure_observed = any(
        str(row.get("theory_packet_id", "") or "") == theory_packet_id
        and _artifact_question_id(row) == question_id
        and (
            _safe_int(row.get("n_generated_simulation_sandbox_execution_failed"))
            > 0
            or _safe_int(row.get("n_unsafe_generated_simulation_code_rejected"))
            > 0
            or _safe_int(row.get("n_generated_simulation_sandbox_metric_gate_failed"))
            > 0
        )
        for row in simulation_rows
    )
    algorithm_feedback_closed = bool(
        not algorithm_failure_observed
        or _safe_int(
            repair_counts.get(
                "n_live_generated_code_sandbox_failed_then_passed_repair_sequences"
            )
        )
        > 0
    )
    simulation_feedback_closed = bool(
        not simulation_failure_observed
        or _safe_int(
            repair_counts.get(
                "n_live_generated_simulation_sandbox_failed_then_passed_repair_sequences"
            )
        )
        > 0
    )

    formalization_rows = _artifacts_of_kind(
        artifact_rows, "RuntimeFormalizationManifest"
    )
    linked_formalization = _linked_formalization(
        formalization_rows,
        theory_packet_id=theory_packet_id,
        question_id=question_id,
        algorithm_rows=algorithm_rows,
        simulation_rows=simulation_rows,
    )
    current_target_ids = _formalization_target_ids(linked_formalization)
    linked_proof_state_feedback_id = str(
        (linked_formalization or {}).get("proof_state_feedback_manifest_id", "")
        or ""
    )
    lean_feedback = bool(
        _safe_int(summary.get("n_lean_lsp_mcp_live_calls")) > 0
        and linked_proof_state_feedback_id
        and any(
            row.get("lean_lsp_mcp_live_called") is True
            and _artifact_question_id(row) == question_id
            and str(row.get("manifest_id", "") or "")
            == linked_proof_state_feedback_id
            for row in artifact_rows
            if str(row.get("artifact_kind", "") or "")
            in {
                "RuntimeProofStateFeedbackManifest",
                "RuntimeFormalizerLeanCandidateProofStateFeedbackManifest",
            }
        )
    )
    proof_manifest, verified_target_ids = _exact_source_proof(
        artifact_rows,
        question_id=question_id,
        current_target_ids=current_target_ids,
    )
    source_proof_lineage_id = str(
        (proof_manifest or {}).get("source_lineage_id", "") or ""
    ).strip()
    exact_source_proof = bool(proof_manifest and verified_target_ids)
    no_formal_gaps = _safe_int(summary.get("n_formal_gaps")) == 0
    accepted = bool(
        result.get("status") == "ACCEPTED"
        and summary.get("ok") is True
        and not summary.get("errors")
    )

    gates = {
        "fresh_start": fresh_start,
        "live_only_topology": live_only_topology,
        "accepted_runtime_result": accepted,
        "explicit_question_and_task_family": bool(
            question_id and is_explicit_task_family(task_family)
        ),
        "architect_controlled": architect_controlled,
        "live_structured_theory_derivation": structured_theory,
        "theory_trace_consumed_by_required_subsystems": theory_handoff_complete,
        "formal_source_rag_observed": formal_source_rag,
        "live_generated_algorithm_executed": algorithm_execution,
        "independent_algorithm_semantic_review_accepted": (
            algorithm_semantic_review
        ),
        "live_generated_simulation_executed": simulation_execution,
        "independent_simulation_semantic_review_accepted": (
            simulation_semantic_review
        ),
        "algorithm_feedback_closed_if_failure_observed": (
            algorithm_feedback_closed
        ),
        "simulation_feedback_closed_if_failure_observed": (
            simulation_feedback_closed
        ),
        "linked_formalization_manifest": bool(linked_formalization),
        "live_lean_verifier_feedback": lean_feedback,
        "exact_source_theorem_kernel_verified": exact_source_proof,
        "no_formal_gaps_remaining": no_formal_gaps,
    }
    missing = [name for name, passed in gates.items() if passed is not True]
    return {
        "question_id": question_id,
        "task_family": task_family,
        "project_id": project_id,
        "result_status": str(result.get("status", "") or ""),
        "theory_packet_id": theory_packet_id,
        "theory_consumers": sorted(theory_consumers),
        "accepted_algorithm_manifest_ids": sorted(
            accepted_algorithm_manifest_ids
        ),
        "accepted_simulation_manifest_ids": sorted(
            accepted_simulation_manifest_ids
        ),
        "algorithm_failure_observed": algorithm_failure_observed,
        "simulation_failure_observed": simulation_failure_observed,
        "formalization_manifest_id": str(
            (linked_formalization or {}).get("manifest_id", "") or ""
        ),
        "current_target_ids": current_target_ids,
        "verified_target_ids": verified_target_ids,
        "source_proof_manifest_id": str(
            (proof_manifest or {}).get("manifest_id", "") or ""
        ),
        "source_proof_lineage_id": source_proof_lineage_id,
        "artifact_bound_repair_counts": dict(repair_counts),
        "gates": gates,
        "missing_requirements": missing,
        "complete": not missing,
        "proof_evidence_status": "PER_TASK_E2E_BINDING_NOT_PROOF_EVIDENCE",
    }


def _latest_live_packet(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for row in reversed(list(rows)):
        provider = str(row.get("provider", "") or row.get("provider_name", "") or "")
        backend = str(
            row.get("backend_provider", "")
            or row.get("backend_provider_name", "")
            or provider
        )
        if is_live_generator_backend(provider, backend):
            return row
    return None


def _structured_theory_packet(packet: Mapping[str, Any] | None) -> bool:
    if not packet or packet.get("ok") is not True:
        return False
    derivation = _mapping(packet.get("theory_derivation_packet")) or packet
    steps = derivation.get("derivation_steps", [])
    equations = derivation.get("equation_chain", [])
    assumptions = derivation.get("assumption_ledger", [])
    handoff = _mapping(derivation.get("formalization_handoff"))
    return bool(
        isinstance(steps, list)
        and steps
        and isinstance(equations, list)
        and equations
        and isinstance(assumptions, list)
        and assumptions
        and handoff
    )


def _theory_consumers(
    artifacts: Sequence[Mapping[str, Any]],
    theory_packet_id: str,
    *,
    question_id: str,
) -> set[str]:
    consumers: set[str] = set()
    if not theory_packet_id:
        return consumers
    contract_keys = (
        "theory_trace_consumption_contract",
        "llm_algorithm_engineer_theory_trace_consumption_contract",
        "llm_simulation_engineer_theory_trace_consumption_contract",
        "llm_formalizer_theory_trace_consumption_contract",
    )
    for artifact in artifacts:
        if _artifact_question_id(artifact) != question_id:
            continue
        for key in contract_keys:
            contract = _mapping(artifact.get(key))
            if (
                str(contract.get("source_theory_packet_id", "") or "")
                != theory_packet_id
                or contract.get("theory_derivation_trace_supplied") is not True
                or _safe_int(contract.get("n_equation_chain_steps_supplied")) <= 0
                or _safe_int(contract.get("n_assumption_ledger_rows_supplied")) <= 0
            ):
                continue
            consumer = str(contract.get("consumer_subsystem", "") or "").strip()
            if consumer:
                consumers.add(consumer)
    return consumers


def _retrieval_has_formal_source_hits(row: Mapping[str, Any]) -> bool:
    counts = _mapping(row.get("counts"))
    hits = row.get("formal_source_hits", [])
    return bool(
        _safe_int(counts.get("formal_source_hits")) > 0
        and isinstance(hits, list)
        and any(_mapping(group).get("hits") for group in hits)
    )


def _linked_formalization(
    rows: Sequence[Mapping[str, Any]],
    *,
    theory_packet_id: str,
    question_id: str,
    algorithm_rows: Sequence[Mapping[str, Any]],
    simulation_rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    algorithm_ids = {
        str(row.get("manifest_id", "") or "")
        for row in algorithm_rows
        if _safe_int(row.get("n_live_generated_code_executed")) > 0
        and str(row.get("theory_packet_id", "") or "") == theory_packet_id
        and _artifact_question_id(row) == question_id
    }
    simulation_ids = {
        str(row.get("manifest_id", "") or "")
        for row in simulation_rows
        if _safe_int(row.get("n_live_generated_simulation_sandbox_executed")) > 0
        and str(row.get("theory_packet_id", "") or "") == theory_packet_id
        and _artifact_question_id(row) == question_id
    }
    for row in reversed(list(rows)):
        if (
            str(row.get("theory_packet_id", "") or "") == theory_packet_id
            and _artifact_question_id(row) == question_id
            and str(row.get("algorithm_sandbox_manifest_id", "") or "")
            in algorithm_ids
            and str(row.get("simulation_manifest_id", "") or "")
            in simulation_ids
        ):
            return row
    return None


def _formalization_target_ids(row: Mapping[str, Any] | None) -> list[str]:
    if not row:
        return []
    values: list[str] = []
    for key in (
        "full_frontier_current_target_ids",
        "source_theorem_current_target_ids",
        "target_ids",
    ):
        values.extend(_strings(row.get(key, [])))
    for goal in row.get("deterministic_theorem_goals", []) or []:
        if isinstance(goal, Mapping):
            values.extend(_strings(goal.get("id", "")))
    for target in row.get("formal_targets", []) or []:
        if isinstance(target, Mapping):
            values.extend(
                _strings(
                    target.get("id", "")
                    or target.get("target_lean_declaration", "")
                    or target.get("name", "")
                )
            )
    return _unique_nonempty(values)


def _exact_source_proof(
    artifacts: Sequence[Mapping[str, Any]],
    *,
    question_id: str,
    current_target_ids: Sequence[str],
) -> tuple[Mapping[str, Any] | None, list[str]]:
    current_targets = set(current_target_ids)
    for manifest in reversed(
        _artifacts_of_kind(
            artifacts, "RuntimeExternalExactProofCandidateRerunManifest"
        )
    ):
        provider = str(manifest.get("provider", "") or "").lower()
        source_lineage_id = str(
            manifest.get("source_lineage_id", "") or ""
        ).strip()
        contract = _mapping(manifest.get("proof_body_generation_contract"))
        target_ids = set(
            _strings(manifest.get("source_theorem_kernel_verified_target_ids", []))
        )
        matching_targets = sorted(current_targets & target_ids)
        rows = manifest.get("rows", [])
        if not isinstance(rows, list):
            rows = []
        verified_rows = [
            row
            for row in rows
            if isinstance(row, Mapping)
            and row.get("source_theorem_kernel_verified") is True
            and row.get("local_lean_checked") is True
            and row.get("local_lean_compiled") is True
            and row.get("exact_signature_preserved") is True
            and row.get("runtime_generated_proof_body") is False
            and str(row.get("candidate_origin", "") or "")
            == "external_llm_or_prover_provider"
            and str(row.get("question_id", "") or "") == question_id
            and str(row.get("source_lineage_id", "") or "")
            == source_lineage_id
            and bool(set(_strings(row.get("target_ids", []))) & set(matching_targets))
        ]
        if (
            not question_id
            or str(manifest.get("question_id", "") or "") != question_id
            or not source_lineage_id
            or not str(manifest.get("input_fingerprint", "") or "").strip()
            or not str(manifest.get("execution_id", "") or "").strip()
            or not str(manifest.get("source_task_id", "") or "").strip()
            or not str(manifest.get("source_work_order_id", "") or "").strip()
            or not str(manifest.get("execution_queue_id", "") or "").strip()
            or not provider
            or any(marker in provider for marker in NON_LIVE_PROVIDER_MARKERS)
            or not str(manifest.get("provider_result_id", "") or "").strip()
            or _safe_int(manifest.get("n_runtime_generated_proof_bodies")) != 0
            or contract.get("mode") != "llm_zero_shot_with_lean_compile_feedback"
            or contract.get("compiler_feedback_retry") is not True
            or contract.get("static_tactic_fallback") is not False
            or manifest.get("source_theorem_kernel_verified") is not True
            or _safe_int(manifest.get("n_source_theorem_kernel_verified"))
            != len(verified_rows)
            or _safe_int(manifest.get("n_local_lean_checked")) < len(verified_rows)
            or _safe_int(manifest.get("n_local_lean_compiled")) < len(verified_rows)
            or not matching_targets
            or not verified_rows
        ):
            continue
        return manifest, matching_targets
    return None, []


def _has_independent_accepted_semantic_review(
    rows: Sequence[Mapping[str, Any]],
    *,
    question_id: str,
    source_subsystem: str,
    source_manifest_ids: set[str],
    require_confirmatory: bool = False,
) -> bool:
    if not source_manifest_ids:
        return False
    return any(
        str(row.get("question_id", "") or "") == question_id
        and str(row.get("source_subsystem", "") or "") == source_subsystem
        and str(row.get("source_manifest_id", "") or "") in source_manifest_ids
        and row.get("semantic_review_accepted") is True
        and row.get("independent_agent") is True
        and row.get("independent_invocation") is True
        and str(row.get("reviewer_model_tier", "") or "").lower() == "sonnet"
        and (
            not require_confirmatory
            or row.get("confirmatory_empirical_evidence_eligible") is True
        )
        for row in rows
    )


def _artifacts_of_kind(
    rows: Sequence[Mapping[str, Any]], *kinds: str
) -> list[Mapping[str, Any]]:
    allowed = set(kinds)
    return [
        row
        for row in rows
        if str(row.get("artifact_kind", "") or "") in allowed
    ]


def _artifact_question_id(row: Mapping[str, Any] | None) -> str:
    if not row:
        return ""
    question = _mapping(row.get("question"))
    problem = _mapping(row.get("problem"))
    return str(
        row.get("question_id", "")
        or question.get("id", "")
        or problem.get("question_id", "")
        or ""
    ).strip()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _strings(value: Any) -> list[str]:
    if isinstance(value, (str, int, float, bool)):
        values = [value]
    elif isinstance(value, Sequence):
        values = list(value)
    else:
        values = []
    return [str(item).strip() for item in values if str(item).strip()]


def _unique_nonempty(values: Sequence[Any] | Any) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
