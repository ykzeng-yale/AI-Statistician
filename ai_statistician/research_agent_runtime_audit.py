from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model_backend import LIVE_EVALUATION_CLAUDE_MODEL


RESEARCH_AGENT_RUNTIME_AUDIT_SCHEMA_VERSION = 2
CANONICAL_RUNTIME_ENDPOINT = "typed_agent_runtime"
CANONICAL_FORMAL_EVIDENCE_SOURCE = "integrated_agent_runtime_only"
ALLOWED_LIVE_CLAUDE_TIERS = frozenset({"haiku", "sonnet"})
FORMALIZER_CLIENT_TOOL_EVIDENCE_TYPES = frozenset(
    {
        "formalizer_lean_candidate_client_tool_loop",
        "formalizer_packet_validation_failure",
    }
)


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _manifest_path(runtime_dir: Path) -> Path:
    if runtime_dir.is_file():
        return runtime_dir
    direct = runtime_dir / "research_agent_runtime_manifest.json"
    if direct.exists():
        return direct
    candidates = sorted(runtime_dir.glob("**/research_agent_runtime_manifest.json"))
    if len(candidates) == 1:
        return candidates[0]
    return direct


def _resolve_artifact_path(runtime_dir: Path, value: object) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    path = Path(raw)
    candidates = [path]
    if not path.is_absolute():
        candidates.extend((runtime_dir / path, runtime_dir / path.name))
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def _read_jsonl(path: Path | None, errors: list[str]) -> list[dict[str, Any]]:
    if path is None:
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, Mapping):
                    errors.append(f"{path.name}:{line_number} is not an object")
                    continue
                rows.append(dict(row))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {path}: {exc}")
    return rows


def _artifact_rows(
    manifest: Mapping[str, Any],
    runtime_dir: Path,
    key: str,
    errors: list[str],
) -> tuple[Path | None, list[dict[str, Any]]]:
    artifacts = manifest.get("artifacts", {})
    value = artifacts.get(key) if isinstance(artifacts, Mapping) else None
    path = _resolve_artifact_path(runtime_dir, value)
    if value and path is None:
        errors.append(f"missing runtime artifact: {value}")
    return path, _read_jsonl(path, errors)


def _question_ids(*row_groups: Iterable[Mapping[str, Any]]) -> list[str]:
    return sorted(
        {
            str(row.get("question_id", "") or "").strip()
            for rows in row_groups
            for row in rows
            if str(row.get("question_id", "") or "").strip()
        }
    )


def _rows_by_question(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        question_id = str(row.get("question_id", "") or "").strip()
        if question_id:
            grouped[question_id].append(row)
    return grouped


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("payload", {})
    return value if isinstance(value, Mapping) else {}


def _all_questions(
    question_ids: Iterable[str],
    rows_by_question: Mapping[str, list[Mapping[str, Any]]],
    predicate: Callable[[Mapping[str, Any]], bool],
) -> bool:
    ids = list(question_ids)
    return bool(ids) and all(
        any(predicate(row) for row in rows_by_question.get(question_id, []))
        for question_id in ids
    )


def _enabled_model_rows(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    topology = manifest.get("llm_runtime_topology", {})
    rows = topology.get("llm_agents", []) if isinstance(topology, Mapping) else []
    return [
        row
        for row in rows
        if isinstance(row, Mapping) and _bool(row.get("enabled", False))
    ]


def _model_policy_summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    config = manifest.get("config", {})
    config = config if isinstance(config, Mapping) else {}
    evaluation_mode = str(config.get("evaluation_mode", "") or "").strip()
    evaluation_run = bool(evaluation_mode and evaluation_mode != "production")
    enabled = _enabled_model_rows(manifest)
    tiers = sorted(
        {
            str(row.get("model_tier", "") or "").strip().lower()
            for row in enabled
            if str(row.get("model_tier", "") or "").strip()
        }
    )
    models = sorted(
        {
            str(value).strip()
            for row in enabled
            for value in (row.get("model"), row.get("serious_model"))
            if str(value or "").strip()
        }
    )
    prohibited = sorted(
        model
        for model in models
        if "opus" in model.lower()
    )
    invalid_tiers = sorted(set(tiers) - ALLOWED_LIVE_CLAUDE_TIERS)
    exact_haiku = not enabled or all(
        str(row.get("model", "") or "").strip() == LIVE_EVALUATION_CLAUDE_MODEL
        and (
            not str(row.get("serious_model", "") or "").strip()
            or str(row.get("serious_model", "") or "").strip()
            == LIVE_EVALUATION_CLAUDE_MODEL
        )
        for row in enabled
    )
    topology_ok = _bool(manifest.get("llm_topology_policy_ok", False))
    return {
        "evaluation_mode": evaluation_mode,
        "evaluation_run": evaluation_run,
        "required_evaluation_model": LIVE_EVALUATION_CLAUDE_MODEL,
        "enabled_models": models,
        "enabled_model_tiers": tiers,
        "n_enabled_agents": len(enabled),
        "prohibited_models": prohibited,
        "invalid_model_tiers": invalid_tiers,
        "exact_haiku_for_evaluation": exact_haiku,
        "passed": bool(
            topology_ok
            and not prohibited
            and not invalid_tiers
            and (not evaluation_run or exact_haiku)
        ),
    }


def _evidence_type(row: Mapping[str, Any]) -> str:
    return str(row.get("evidence_type", "") or "").strip()


def _model_owned_theory_workspace(
    payload: Mapping[str, Any],
    *,
    operation: str,
) -> bool:
    workspace = payload.get("llm_client_tool_loop", {})
    if not isinstance(workspace, Mapping):
        return False
    changed = set(workspace.get("changed_artifact_names", []) or [])
    return bool(
        workspace.get("artifact_kind")
        == "TheoryDeveloperWorkspaceEvidence"
        and workspace.get("workspace_operation") == operation
        and _bool(workspace.get("accepted", False))
        and _bool(workspace.get("model_owned_theory", False))
        and not _bool(workspace.get("runtime_edited_theory", True))
        and _int(workspace.get("reads")) > 0
        and _int(workspace.get("submissions")) > 0
        and bool(changed)
        and bool(str(workspace.get("provider", "") or "").strip())
        and bool(str(workspace.get("model", "") or "").strip())
    )


def _has_direct_revision(
    evidence_rows: list[Mapping[str, Any]],
    *,
    failure_type: str,
    proposal_type: str,
    failed: Callable[[Mapping[str, Any]], bool],
) -> tuple[bool, int, int]:
    grouped = _rows_by_question(evidence_rows)
    n_failures = 0
    n_resolved = 0

    def workspace_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        rows = payload.get("scientific_code_workspaces", [])
        return [row for row in rows or [] if isinstance(row, Mapping)]

    def workspace_identity(
        row: Mapping[str, Any],
        *,
        question_id: str,
    ) -> tuple[str, str] | None:
        artifact_id = str(row.get("artifact_id", "") or "").strip()
        child_hash = str(
            row.get("submitted_code_draft_hash", "") or ""
        ).strip()
        if not (
            artifact_id.startswith(question_id + ":")
            and child_hash
            and _bool(row.get("model_owned_source", False))
            and not _bool(row.get("runtime_edited_source", True))
            and _int(row.get("source_updates")) > 0
            and _int(row.get("sandbox_checks")) > 0
            and _int(row.get("runtime_executed_tool_calls")) > 0
            and bool(str(row.get("provider", "") or "").strip())
            and bool(str(row.get("model", "") or "").strip())
            and bool(
                str(row.get("initial_check_result_hash", "") or "").strip()
            )
            and bool(
                str(row.get("terminal_check_result_hash", "") or "").strip()
            )
            and bool(str(row.get("transcript_fingerprint", "") or "").strip())
        ):
            return None
        return artifact_id, child_hash

    for question_id, rows in grouped.items():
        for index, row in enumerate(rows):
            payload = _payload(row)
            if _evidence_type(row) != failure_type or not failed(payload):
                continue
            n_failures += 1
            failure_artifact_id = str(row.get("artifact_id", "") or "").strip()
            frontier = {
                identity
                for summary in workspace_rows(payload)
                if (
                    identity := workspace_identity(
                        summary,
                        question_id=question_id,
                    )
                )
                is not None
            }
            resolved = False
            for later in rows[index + 1 :]:
                for summary in workspace_rows(_payload(later)):
                    identity = workspace_identity(
                        summary,
                        question_id=question_id,
                    )
                    if identity is None:
                        continue
                    parent_hash = str(
                        summary.get("parent_code_draft_hash", "") or ""
                    ).strip()
                    valid_revision = bool(
                        summary.get("workspace_operation") == "targeted_revision"
                        and summary.get("initial_check_accepted") is False
                        and _bool(summary.get("source_changed", False))
                        and parent_hash
                        and parent_hash != identity[1]
                    )
                    if not valid_revision:
                        continue
                    linked_by_hash = bool(
                        (identity[0], parent_hash) in frontier
                    )
                    source_lineage = summary.get("source_revision_lineage", {})
                    source_lineage = (
                        source_lineage
                        if isinstance(source_lineage, Mapping)
                        else {}
                    )
                    linked_by_manifest = bool(
                        failure_artifact_id
                        and str(
                            source_lineage.get("parent_manifest_id", "") or ""
                        ).strip()
                        == failure_artifact_id
                        and _bool(
                            source_lineage.get(
                                "feedback_supplied_to_generator",
                                False,
                            )
                        )
                        and _bool(
                            source_lineage.get("lineage_contract_complete", False)
                        )
                    )
                    if not (linked_by_hash or linked_by_manifest):
                        continue
                    frontier.add(identity)
                    if _bool(summary.get("accepted", False)):
                        resolved = True
                        break
                if resolved:
                    break
            if not resolved and "scientific_code_workspaces" not in payload:
                resolved = any(
                    _evidence_type(later) == proposal_type
                    for later in rows[index + 1 :]
                )
            if resolved:
                n_resolved += 1
    return (n_failures == n_resolved, n_failures, n_resolved)


def _source_owner_revision_summary(
    evidence_rows: list[Mapping[str, Any]],
    observation_rows: list[Mapping[str, Any]],
) -> tuple[bool, int, int, int, set[str]]:
    """Audit explicit source-owner backedges, not arbitrary metric failures."""

    evidence_by_task: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        task_id = str(row.get("task_id", "") or "").strip()
        if task_id:
            evidence_by_task[task_id].append(row)

    requests = [
        row
        for row in observation_rows
        if str(row.get("observation_type", "") or "")
        == "algorithm_consumer_source_workspace_resumed"
    ]
    restores_by_question = Counter(
        str(row.get("question_id", "") or "").strip()
        for row in observation_rows
        if str(row.get("observation_type", "") or "")
        == "scientific_consumer_continuation_restored"
    )
    valid_revisions = 0
    request_counts_by_question: Counter[str] = Counter()
    valid_questions: set[str] = set()
    for request in requests:
        question_id = str(request.get("question_id", "") or "").strip()
        task_id = str(request.get("task_id", "") or "").strip()
        payload = _payload(request)
        requested_ids = {
            str(value or "").strip()
            for value in payload.get("source_revision_artifact_ids", []) or []
            if str(value or "").strip()
        }
        source_manifest_id = str(
            payload.get("source_manifest_id", "") or ""
        ).strip()
        if question_id:
            request_counts_by_question[question_id] += 1
        valid_ids: set[str] = set()
        for evidence in evidence_by_task.get(task_id, []):
            if _evidence_type(evidence) != "algorithm_sandbox":
                continue
            for summary in _payload(evidence).get(
                "scientific_code_workspaces", []
            ) or []:
                if not isinstance(summary, Mapping):
                    continue
                artifact_id = str(summary.get("artifact_id", "") or "").strip()
                short_id = artifact_id.removeprefix(question_id + ":")
                parent_hash = str(
                    summary.get("parent_code_draft_hash", "") or ""
                ).strip()
                child_hash = str(
                    summary.get("submitted_code_draft_hash", "") or ""
                ).strip()
                if not (
                    question_id
                    and artifact_id.startswith(question_id + ":")
                    and short_id in requested_ids
                    and summary.get("workspace_operation") == "targeted_revision"
                    and summary.get("initial_check_accepted") is False
                    and _bool(summary.get("source_changed", False))
                    and parent_hash
                    and child_hash
                    and parent_hash != child_hash
                    and _int(summary.get("source_updates")) > 0
                    and _int(summary.get("sandbox_checks")) > 0
                    and _int(summary.get("runtime_executed_tool_calls")) > 0
                    and _bool(summary.get("model_owned_source", False))
                    and not _bool(summary.get("runtime_edited_source", True))
                    and _bool(summary.get("accepted", False))
                    and bool(str(summary.get("provider", "") or "").strip())
                    and bool(str(summary.get("model", "") or "").strip())
                    and bool(
                        str(summary.get("transcript_fingerprint", "") or "").strip()
                    )
                ):
                    continue
                valid_ids.add(short_id)
        if (
            source_manifest_id
            and requested_ids
            and valid_ids == requested_ids
        ):
            valid_revisions += 1
            valid_questions.add(question_id)

    restored_requests = sum(
        min(count, restores_by_question.get(question_id, 0))
        for question_id, count in request_counts_by_question.items()
    )
    request_questions = set(request_counts_by_question)
    complete = bool(
        valid_revisions == len(requests)
        and restored_requests == len(requests)
        and valid_questions == request_questions
    )
    return (
        complete,
        len(requests),
        valid_revisions,
        restored_requests,
        valid_questions,
    )


def _failed_algorithm(payload: Mapping[str, Any]) -> bool:
    return bool(
        _int(payload.get("n_generated_code_execution_failed")) > 0
        or _int(payload.get("n_generated_code_metric_gate_failed")) > 0
        or (
            _int(payload.get("n_generated_code_executed")) > 0
            and _int(payload.get("n_generated_code_passed")) <= 0
        )
    )


def _failed_simulation(payload: Mapping[str, Any]) -> bool:
    return bool(
        _int(payload.get("n_generated_simulation_sandbox_execution_failed")) > 0
        or _int(payload.get("n_generated_simulation_sandbox_metric_gate_failed")) > 0
        or (
            _int(payload.get("n_generated_simulation_sandbox_executed")) > 0
            and _int(payload.get("n_generated_simulation_sandbox_passed")) <= 0
        )
    )


def _formalizer_revision_summary(
    evidence_rows: list[Mapping[str, Any]],
) -> tuple[bool, int, int]:
    loops = [
        _payload(row)
        for row in evidence_rows
        if _evidence_type(row) in FORMALIZER_CLIENT_TOOL_EVIDENCE_TYPES
        and _bool(_payload(row).get("model_owned_lean_code", False))
        and not _bool(_payload(row).get("runtime_selected_lean_code", True))
        and bool(str(_payload(row).get("candidate_source_hash", "") or ""))
    ]
    revised = [
        row
        for row in loops
        if _bool(row.get("source_changed", False))
        and _int(row.get("source_updates")) > 0
        and _int(row.get("local_lean_checks")) > 0
        and _bool(row.get("model_owned_lean_code", False))
        and not _bool(row.get("runtime_selected_lean_code", True))
        and bool(str(row.get("provider", "") or "").strip())
        and bool(str(row.get("model", "") or "").strip())
    ]
    return (bool(loops) and len(loops) == len(revised), len(loops), len(revised))


def _scorecard(
    manifest: Mapping[str, Any],
    traces: list[Mapping[str, Any]],
    observations: list[Mapping[str, Any]],
    evidence: list[Mapping[str, Any]],
    integrity: Mapping[str, bool],
) -> dict[str, Any]:
    question_ids = _question_ids(traces, observations, evidence)
    evidence_by_question = _rows_by_question(evidence)
    observation_by_question = _rows_by_question(observations)
    model_policy = _model_policy_summary(manifest)

    (
        source_revision_ok,
        source_revision_requests,
        source_revisions,
        consumer_replays,
        source_revision_questions,
    ) = _source_owner_revision_summary(
        evidence,
        observations,
    )
    lean_revision_ok, lean_loops, lean_revisions = _formalizer_revision_summary(
        evidence
    )

    def evidence_for(question_id: str, kind: str) -> list[Mapping[str, Any]]:
        return [
            row
            for row in evidence_by_question.get(question_id, [])
            if _evidence_type(row) == kind
        ]

    fresh_plan_questions = {
        question_id
        for question_id in question_ids
        if any(
            _bool(_payload(row).get("fresh_architect_plan_model_invocation", False))
            for row in evidence_for(question_id, "llm_architect_coordinator_proposal")
        )
    }
    theory_content_questions = {
        question_id
        for question_id in question_ids
        if any(
            _int(
                (_payload(row).get("theory_derivation_contract", {}) or {}).get(
                    "n_derivation_steps", 0
                )
            )
            > 0
            and _int(
                (_payload(row).get("theory_derivation_contract", {}) or {}).get(
                    "n_equation_chain_steps", 0
                )
            )
            > 0
            and _int(
                (_payload(row).get("theory_derivation_contract", {}) or {}).get(
                    "n_assumption_ledger_rows", 0
                )
            )
            > 0
            for row in evidence_for(question_id, "llm_theory_derivation")
        )
    }
    initial_theory_workspace_questions = {
        question_id
        for question_id in question_ids
        if any(
            _model_owned_theory_workspace(
                _payload(row),
                operation="initial_discovery",
            )
            for row in evidence_for(question_id, "llm_theory_derivation")
        )
    }
    theory_questions = (
        theory_content_questions & initial_theory_workspace_questions
    )
    targeted_theory_workspace_questions = {
        question_id
        for question_id in question_ids
        if any(
            _model_owned_theory_workspace(
                _payload(row),
                operation="targeted_revision",
            )
            for row in evidence_for(question_id, "llm_theory_derivation")
        )
    }
    theory_revision_questions = {
        question_id
        for question_id in question_ids
        if len(evidence_for(question_id, "llm_theory_derivation")) >= 2
        and bool(evidence_for(question_id, "llm_critic_evaluator_proposal"))
        and question_id in targeted_theory_workspace_questions
    }
    algorithm_questions = {
        question_id
        for question_id in question_ids
        if any(
            _int(_payload(row).get("n_generated_code_executed")) > 0
            and _int(_payload(row).get("n_generated_code_passed")) > 0
            for row in evidence_for(question_id, "algorithm_sandbox")
        )
    }
    simulation_questions = {
        question_id
        for question_id in question_ids
        if any(
            _int(_payload(row).get("n_generated_simulation_sandbox_executed")) > 0
            and _int(_payload(row).get("n_generated_simulation_sandbox_passed")) > 0
            for row in evidence_for(question_id, "simulation")
        )
    }
    code_review_questions = {
        question_id
        for question_id in question_ids
        if any(
            str(_payload(row).get("overall_verdict", "") or "").upper()
            == "ACCEPT"
            and bool(str(_payload(row).get("source_manifest_id", "") or ""))
            for row in evidence_for(question_id, "generated_code_semantic_review")
        )
    }
    retrieval_questions = {
        question_id
        for question_id in question_ids
        if any(
            _int(_payload(row).get("formal_source_hits")) > 0
            for row in evidence_for(question_id, "retrieval_memory")
        )
        and (
            any(
                row.get("observation_type")
                == "formalizer_environment_feedback_formal_source_grounding"
                and _int(_payload(row).get("n_formal_source_grounding_hits")) > 0
                for row in observation_by_question.get(question_id, [])
            )
            or any(
                _int(_payload(row).get("n_formal_rag_tool_calls")) > 0
                for evidence_type in FORMALIZER_CLIENT_TOOL_EVIDENCE_TYPES
                for row in evidence_for(question_id, evidence_type)
            )
        )
    }
    formal_review_questions = {
        question_id
        for question_id in question_ids
        if any(
            str(_payload(row).get("overall_verdict", "") or "").upper()
            == "ACCEPT"
            and bool(str(_payload(row).get("candidate_source_hash", "") or ""))
            for row in evidence_for(question_id, "formal_target_semantic_review")
        )
    }
    lean_source_questions = {
        question_id
        for question_id in question_ids
        if (
            any(
                _int(_payload(row).get("n_lean_candidate_sources")) > 0
                and _int(_payload(row).get("n_lean_candidate_artifacts_written"))
                > 0
                for row in evidence_for(
                    question_id, "llm_formalizer_proof_engineer_proposal"
                )
            )
            or any(
                _bool(_payload(row).get("model_owned_lean_code", False))
                and not _bool(
                    _payload(row).get("runtime_selected_lean_code", True)
                )
                and bool(
                    str(_payload(row).get("candidate_source_hash", "") or "")
                )
                for evidence_type in FORMALIZER_CLIENT_TOOL_EVIDENCE_TYPES
                for row in evidence_for(question_id, evidence_type)
            )
        )
    }
    target_identity_questions = {
        question_id
        for question_id in question_ids
        if any(
            bool(_payload(row).get("source_theorem_kernel_verified_target_ids"))
            for row in evidence_for(question_id, "formalization_proof_feedback")
        )
    }
    kernel_questions = {
        question_id
        for question_id in question_ids
        if any(
            _bool(_payload(row).get("source_theorem_kernel_verified", False))
            and bool(_payload(row).get("source_theorem_kernel_verified_target_ids"))
            and _int((_payload(row).get("counts", {}) or {}).get("formal_gap")) == 0
            for row in evidence_for(question_id, "formalization_proof_feedback")
        )
    }
    final_critic_questions = {
        question_id
        for question_id in question_ids
        if any(
            str(
                (_payload(row).get("evidence_contract_decision", {}) or {}).get(
                    "final_acceptance_status", ""
                )
                or ""
            )
            == "FORMAL_CONTRACT_SATISFIED"
            for row in evidence_for(question_id, "critic_evaluator")
        )
    }

    def all_have(values: set[str]) -> bool:
        return bool(question_ids) and set(question_ids).issubset(values)

    rows = [
        ("canonical_single_runtime", all(integrity.values()), str(dict(integrity))),
        (
            "approved_live_model_policy",
            bool(model_policy["passed"]),
            f"tiers={model_policy['enabled_model_tiers']} models={model_policy['enabled_models']}",
        ),
        (
            "fresh_cross_task_panel",
            len(question_ids) >= 2 and all_have(fresh_plan_questions),
            f"questions={question_ids} fresh_plans={sorted(fresh_plan_questions)}",
        ),
        (
            "architect_initial_plan_observed",
            all_have(fresh_plan_questions),
            f"questions={sorted(fresh_plan_questions)}",
        ),
        (
            "rigorous_theory_derivation_observed",
            all_have(theory_questions),
            f"content={sorted(theory_content_questions)} "
            "model_owned_initial_workspace="
            f"{sorted(initial_theory_workspace_questions)}",
        ),
        (
            "theory_critic_revision_observed",
            all_have(theory_revision_questions),
            f"questions={sorted(theory_revision_questions)} "
            "model_owned_targeted_workspace="
            f"{sorted(targeted_theory_workspace_questions)}",
        ),
        (
            "generated_algorithm_executed_and_passed",
            all_have(algorithm_questions),
            f"questions={sorted(algorithm_questions)}",
        ),
        (
            "generated_simulation_executed_and_passed",
            all_have(simulation_questions),
            f"questions={sorted(simulation_questions)}",
        ),
        (
            "source_producer_owns_code_revision",
            all_have(algorithm_questions)
            and source_revision_ok,
            f"algorithm_executed={sorted(algorithm_questions)}; "
            f"simulation_executed={sorted(simulation_questions)}; "
            f"source_revision_questions={sorted(source_revision_questions)}; "
            f"requests={source_revision_requests} "
            f"model_owned_revisions={source_revisions} "
            f"consumer_replays={consumer_replays}",
        ),
        (
            "independent_generated_code_review_accepted",
            all_have(code_review_questions),
            f"questions={sorted(code_review_questions)}",
        ),
        (
            "task_bound_formal_rag_observed",
            all_have(retrieval_questions),
            f"questions={sorted(retrieval_questions)}",
        ),
        (
            "formal_target_semantic_review_accepted",
            all_have(formal_review_questions),
            f"questions={sorted(formal_review_questions)}",
        ),
        (
            "llm_generated_lean_source_observed",
            all_have(lean_source_questions),
            f"questions={sorted(lean_source_questions)}",
        ),
        (
            "same_formalizer_revised_from_raw_lean_feedback",
            lean_revision_ok,
            f"direct_loops={lean_loops} model_owned_revisions={lean_revisions}",
        ),
        (
            "exact_target_identity_preserved",
            all_have(target_identity_questions),
            f"questions={sorted(target_identity_questions)}",
        ),
        (
            "target_bound_kernel_closure_and_final_critic_acceptance",
            all_have(kernel_questions) and all_have(final_critic_questions),
            f"kernel={sorted(kernel_questions)} final_critic={sorted(final_critic_questions)}",
        ),
    ]
    score_rows = [
        {
            "requirement_id": requirement_id,
            "passed": bool(passed),
            "evidence": evidence_text,
        }
        for requirement_id, passed, evidence_text in rows
    ]
    n_passed = sum(row["passed"] for row in score_rows)
    return {
        "schema_version": 2,
        "n_requirements": len(score_rows),
        "n_passed": n_passed,
        "n_failed": len(score_rows) - n_passed,
        "ready": n_passed == len(score_rows),
        "rows": score_rows,
        "boundary": (
            "The scorecard reports integrated runtime observations only. LLM "
            "proposals, RAG hits, semantic reviews, and compiler diagnostics are "
            "not proof; exact target-bound local Lean or AXLE kernel evidence is required."
        ),
    }


def _report(payload: Mapping[str, Any]) -> str:
    scorecard = payload.get("capability_scorecard", {})
    rows = scorecard.get("rows", []) if isinstance(scorecard, Mapping) else []
    lines = [
        "# Research Agent Runtime Audit",
        "",
        f"- audit_integrity_ok: {payload.get('all_ok', False)}",
        "- capability_ready_for_full_ai_statistician: "
        f"{payload.get('capability_ready_for_full_ai_statistician', False)}",
        f"- score: {scorecard.get('n_passed', 0)}/{scorecard.get('n_requirements', 0)}",
        "",
        "## Capability Evidence",
        "",
    ]
    for row in rows:
        mark = "PASS" if row.get("passed") else "FAIL"
        lines.append(
            f"- [{mark}] {row.get('requirement_id')}: {row.get('evidence', '')}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            str(scorecard.get("boundary", "")),
            "",
        ]
    )
    return "\n".join(lines)


def audit_research_agent_runtime(
    runtime_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    runtime_dir = Path(runtime_dir)
    manifest_path = _manifest_path(runtime_dir)
    audit_dir = Path(out_dir) if out_dir is not None else runtime_dir / "runtime_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    if not manifest_path.exists():
        errors.append(f"missing runtime manifest: {manifest_path}")
        manifest: dict[str, Any] = {}
    else:
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = dict(loaded) if isinstance(loaded, Mapping) else {}
            if not manifest:
                errors.append(f"runtime manifest is not an object: {manifest_path}")
        except (OSError, json.JSONDecodeError) as exc:
            manifest = {}
            errors.append(f"cannot read runtime manifest {manifest_path}: {exc}")

    source_dir = manifest_path.parent if manifest_path.exists() else runtime_dir
    trace_path, traces = _artifact_rows(
        manifest, source_dir, "runtime_traces_jsonl", errors
    )
    observation_path, observations = _artifact_rows(
        manifest, source_dir, "runtime_observations_jsonl", errors
    )
    evidence_path, evidence = _artifact_rows(
        manifest, source_dir, "runtime_evidence_ledger_jsonl", errors
    )
    tool_path, tool_calls = _artifact_rows(
        manifest, source_dir, "runtime_tool_calls_jsonl", errors
    )

    legacy_fallback = _bool(
        manifest.get("legacy_post_runtime_formal_fallback_used", False)
    ) or any(
        _bool(value)
        for key, value in manifest.items()
        if str(key).endswith("_legacy_post_runtime_fallback_used")
    )
    integrity = {
        "manifest_readable": bool(manifest) and not any(
            error.startswith("cannot read runtime manifest") for error in errors
        ),
        "canonical_runtime_endpoint": (
            manifest.get("runtime_endpoint") == CANONICAL_RUNTIME_ENDPOINT
        ),
        "integrated_evidence_only": (
            manifest.get("runtime_formal_capability_source")
            == CANONICAL_FORMAL_EVIDENCE_SOURCE
        ),
        "legacy_post_runtime_fallback_absent": not legacy_fallback,
        "runtime_streams_readable": bool(
            trace_path and observation_path and evidence_path and tool_path
        )
        and not errors,
    }
    scorecard = _scorecard(manifest, traces, observations, evidence, integrity)
    question_ids = _question_ids(traces, observations, evidence)
    status_counts = Counter(
        str(row.get("status", "") or "") for row in traces if row.get("status")
    )
    evidence_counts = Counter(_evidence_type(row) for row in evidence)
    model_policy = _model_policy_summary(manifest)
    manifest_hash = ""
    if manifest_path.exists():
        manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    payload: dict[str, Any] = {
        "schema_version": RESEARCH_AGENT_RUNTIME_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requested": True,
        "available": bool(manifest),
        "runtime_dir": str(source_dir),
        "runtime_manifest_path": str(manifest_path),
        "runtime_manifest_sha256": manifest_hash,
        "runtime_audit_source": "integrated_runtime_artifacts",
        "contract_smoke": False,
        "all_ok": all(integrity.values()) and model_policy["passed"] and not errors,
        "integrity_checks": integrity,
        "errors": errors,
        "capability_scorecard": scorecard,
        "capability_ready_for_full_ai_statistician": bool(scorecard["ready"]),
        "capability_status": (
            "READY" if scorecard["ready"] else "INCOMPLETE"
        ),
        "capability_gaps": [
            row["requirement_id"]
            for row in scorecard["rows"]
            if not row["passed"]
        ],
        "model_policy": model_policy,
        "question_ids": question_ids,
        "n_results": len(question_ids),
        "n_ok": _int(
            (manifest.get("status_counts", {}) or {}).get("ACCEPTED", 0)
        ),
        "n_runtime_traces": len(traces),
        "n_runtime_observations": len(observations),
        "n_runtime_tool_calls": len(tool_calls),
        "n_runtime_evidence_rows": len(evidence),
        "trace_status_counts": dict(sorted(status_counts.items())),
        "evidence_type_counts": dict(sorted(evidence_counts.items())),
        "n_kernel_verified_subclaims": _int(
            manifest.get("n_kernel_verified_subclaims", 0)
        ),
        "n_materialized_formal_gap_rows": _int(
            manifest.get(
                "n_materialized_formal_gap_rows",
                manifest.get("n_formal_gaps", 0),
            )
        ),
        "n_formal_gaps": _int(manifest.get("n_formal_gaps", 0)),
        "formal_closure_summary": dict(
            manifest.get("formal_closure_summary", {})
            if isinstance(manifest.get("formal_closure_summary", {}), Mapping)
            else {}
        ),
        "formalizer_client_tool_observation_summary": dict(
            manifest.get("formalizer_client_tool_observation_summary", {})
            if isinstance(
                manifest.get("formalizer_client_tool_observation_summary", {}),
                Mapping,
            )
            else {}
        ),
        "n_live_generated_code_sandbox_executed": _int(
            manifest.get("n_live_generated_code_sandbox_executed", 0)
        ),
        "n_live_generated_simulation_sandbox_executed": _int(
            manifest.get("n_live_generated_simulation_sandbox_executed", 0)
        ),
        "n_live_llm_formalizer_proof_engineer_proposals": _int(
            manifest.get("n_live_llm_formalizer_proof_engineer_proposals", 0)
        ),
        "n_formalizer_lean_candidate_local_lean_checked": _int(
            manifest.get("n_formalizer_lean_candidate_local_lean_checked", 0)
        ),
        "n_formalizer_lean_candidate_local_lean_compiled": _int(
            manifest.get("n_formalizer_lean_candidate_local_lean_compiled", 0)
        ),
        "n_full_frontier_theorem_proved": _int(
            manifest.get("n_full_frontier_theorem_proved", 0)
        ),
        "readiness_boundary": scorecard["boundary"],
        "limitations": [
            "The audit does not reconstruct tasks or propose repair routes.",
            "Historical manifests without the canonical endpoint markers fail integrity.",
            "Capability readiness requires a fresh multi-task run and exact target-bound kernel closure.",
        ],
        "artifacts": {
            "runtime_manifest": str(manifest_path),
            "runtime_traces": str(trace_path or ""),
            "runtime_observations": str(observation_path or ""),
            "runtime_evidence_ledger": str(evidence_path or ""),
            "runtime_tool_calls": str(tool_path or ""),
        },
    }
    audit_manifest_path = audit_dir / "research_agent_runtime_audit_manifest.json"
    audit_report_path = audit_dir / "research_agent_runtime_audit.md"
    payload["manifest_path"] = str(audit_manifest_path)
    payload["report_path"] = str(audit_report_path)
    audit_manifest_path.write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    audit_report_path.write_text(_report(payload), encoding="utf-8")
    return payload
