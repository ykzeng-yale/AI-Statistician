from __future__ import annotations

import hashlib
import json
import math
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .fingerprint import stable_hash
from .lean_kernel_promotion import lean_kernel_promotion_evidence_errors
from .estimator_interface_contract import (
    frozen_estimator_execution_contract_clause_ids,
    frozen_estimator_execution_contract_empirical_claim_ids,
    frozen_estimator_execution_contract_errors,
    frozen_estimator_execution_contract_id,
)
from .model_backend import (
    GeneratorBackend, LIVE_EVALUATION_MODEL, LIVE_EVALUATION_MODEL_TIER,
    LIVE_EVALUATION_PROVIDER, resolve_live_evaluation_model,
)
from .local_model_backend import LocalChatGeneratorBackend
from .research_schema import frozen_formal_target_contract_errors
from .research_evaluation import research_evaluation_evidence_hash
from .research_source_library import source_replication_execution_integrity_ok
from .scientific_sandbox import (
    SCIENTIFIC_SANDBOX_LANGUAGES,
    SCIENTIFIC_SANDBOX_PROFILES,
    SCIENTIFIC_NATIVE_PROFILES,
    ScientificEstimatorBinding,
    ScientificInputArtifactBinding,
    execute_scientific_sandbox,
)
from .scientific_project import (
    normalized_scientific_project_files,
    scientific_project_hash,
)
from .theory_derivation_trace import document_authoritative_theory_context
from .theory_semantic_gold_judge import (
    THEORY_SEMANTIC_CANDIDATE_STRATEGIES,
    run_theory_semantic_gold_judge,
    theory_semantic_activation_judgment_errors,
)
from .theory_workspace import load_theory_workspace_document_rows


GOLD_EVALUATION_BOUNDARY = (
    "Evaluator-only gold runs after the AgentRuntime has terminated. Hidden "
    "harness source, expected values, and acceptance checks are never added to "
    "the blackboard, retrieval context, model prompt, or source-revision loop."
)
GoldHarnessRunner = Callable[..., Mapping[str, Any]]
GoldArtifactHarnessRunner = Callable[..., Mapping[str, Any]]
GoldTheorySemanticJudgeRunner = Callable[..., Mapping[str, Any]]


def _semantic_judgment_metrics(
    judgment: Mapping[str, Any], *, prefix: str, executed: bool = True,
    evaluator: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize the same frozen semantic-judge fields for theory and source reports."""

    values = {
        "execution_attempted": executed,
        "claim_assessments": deepcopy(judgment.get("candidate_claim_assessments", [])),
    }
    if executed:
        values["result_hash"] = str(judgment.get("judgment_hash", "") or "")
    else:
        values["evaluation_configured"] = bool(evaluator)
        values["evaluator_hash"] = stable_hash(evaluator) if evaluator else ""
    for target, source in {
        "judge_calibrated": "semantic_judge_calibrated",
        "candidate_mode_negative_controls_passed": "candidate_mode_negative_controls_passed",
        "candidate_integrated_context": "candidate_integrated_context",
        "passed": "passed",
    }.items():
        values[target] = judgment.get(source) is True
    for target, source in {
        "calibration_case_count": "n_calibration_cases",
        "calibration_cases_correct": "n_calibration_cases_correct",
        "candidate_mode_negative_case_count": "n_candidate_mode_negative_cases",
        "candidate_mode_negative_cases_correct": "n_candidate_mode_negative_cases_correct",
        "candidate_mode_negative_model_calls": "candidate_mode_negative_model_calls",
        "claim_count": "n_claims",
        "candidate_model_calls": "candidate_integrated_model_calls",
    }.items():
        values[target] = int(judgment.get(source, 0) or 0)
    for field in ("candidate_status", "candidate_document_status"):
        values[field] = str(judgment.get(field, "") or "")
    return {prefix + key: value for key, value in values.items()}


def _visible_question_hash_payload(question: Mapping[str, Any]) -> dict[str, Any]:
    base = ("id", "title", "description", "tags")
    optional = ("task_intent", "estimator_execution_contract", "formal_target_contract")
    return {
        key: question.get(key)
        for key in (*base, *optional)
        if key in base or key in question
    }


def validate_research_gold_benchmark_manifest(path: Path) -> dict[str, Any]:
    """Validate evaluator authority without exposing its payload to agents."""

    manifest_path = path.resolve()
    benchmark = _load_benchmark_manifest(manifest_path)
    _validate_benchmark_manifest(
        benchmark,
        manifest_path=manifest_path,
        project_root=Path(__file__).resolve().parents[1],
    )
    return {
        "artifact_kind": "ResearchCapabilityGoldBenchmarkDescriptor",
        "benchmark_id": str(benchmark["benchmark_id"]),
        "benchmark_manifest_hash": stable_hash(benchmark),
        "active_task_ids": [
            str(task["task_id"]) for task in benchmark["active_tasks"]
        ],
        "estimator_execution_contract_ids": {
            str(task["task_id"]): str(
                task.get("estimator_execution_contract_id", "") or ""
            )
            for task in benchmark["active_tasks"]
            if str(task.get("estimator_execution_contract_id", "") or "")
        },
        "n_full_task_gold_configured": sum(
            str(task.get("scoring_scope", "component") or "component")
            == "full_task"
            for task in benchmark["active_tasks"]
        ),
        "runtime_visibility": "evaluator_only_after_runtime",
        "boundary": GOLD_EVALUATION_BOUNDARY,
    }


def validate_research_gold_benchmark_activation(
    path: Path,
    *,
    visible_questions: Mapping[str, Mapping[str, Any]] | None = None,
    run_theory_semantic_judge: GoldTheorySemanticJudgeRunner | None = None,
    theory_semantic_judge_provider: GeneratorBackend | None = None,
    require_prequalified_activation: bool = False,
    evaluation_model_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute or verify future-task calibration through frozen validators."""

    descriptor = validate_research_gold_benchmark_manifest(path)
    if visible_questions is not None:
        visible_task_ids = {str(task_id) for task_id in visible_questions}
        missing_task_ids = sorted(set(descriptor["active_task_ids"]) - visible_task_ids)
        if missing_task_ids:
            raise ValueError(
                "research gold tasks are absent from the selected question set: "
                + ", ".join(missing_task_ids)
            )
    benchmark = _load_benchmark_manifest(path.resolve())
    if evaluation_model_policy is not None:
        model_policy = benchmark.get("model_policy", {})
        if any(model_policy.get(key) != value for key, value in evaluation_model_policy.items()):
            raise ValueError("gold benchmark model policy differs from the current runtime; historical qualifications cannot be reused")
    schema_version = int(benchmark.get("schema_version", 0) or 0)
    if schema_version not in {3, 4, 5}:
        raise ValueError("live gold activation requires schema_version 3, 4, or 5")
    semantic_rows: list[dict[str, Any]] = []
    if schema_version >= 4:
        visible_by_id = dict(visible_questions or {})
        for task in benchmark["active_tasks"]:
            task_id = str(task["task_id"])
            visible_question = visible_by_id.get(task_id)
            for field, artifact_role in (
                ("hidden_theory_semantic_evaluator", "theory"),
                ("hidden_source_report_semantic_evaluator", "source_replication_report"),
            ):
                evaluator = task.get(field)
                if not isinstance(evaluator, Mapping) or not evaluator:
                    continue
                activation_record = str(
                    evaluator.get("activation_record_path") or ""
                ).strip()
                if require_prequalified_activation and not activation_record:
                    raise ValueError("semantic activation is not frozen")
                if not isinstance(visible_question, Mapping):
                    raise ValueError(
                        "schema_version 4 semantic activation requires the exact "
                        f"visible question for task {task_id}"
                    )
                if stable_hash(
                    _visible_question_hash_payload(visible_question)
                ) != str(task["visible_question_hash"]):
                    raise ValueError(
                        "schema_version 4 semantic activation visible question "
                        f"hash mismatch for task {task_id}"
                    )
                semantic_rows.append(
                    _run_semantic_candidate_mode_activation(
                        evaluator=evaluator,
                        task_id=task_id,
                        visible_question=visible_question,
                        project_root=Path(__file__).resolve().parents[1],
                        run_semantic_judge=run_theory_semantic_judge,
                        semantic_judge_provider=theory_semantic_judge_provider,
                        semantic_artifact_role=artifact_role,
                    )
                )
    rows = []
    for task in benchmark["active_tasks"]:
        if not task.get("activation_candidate_suite"):
            continue
        project_root = Path(__file__).resolve().parents[1]
        if require_prequalified_activation or "mechanical_activation_record" in task:
            rows.append(_load_mechanical_activation_record(task, project_root=project_root))
        else:
            with tempfile.TemporaryDirectory(prefix="ai-stat-gold-activation-") as value:
                rows.append(_run_activation_candidate_suite(
                    task, project_root=project_root, sandbox_root=Path(value),
                ))
    return {
        **descriptor,
        "activation_schema_version": schema_version,
        "activation_candidate_validator_path": "same_hidden_evaluator_path",
        "activation_reference_tasks_passed": len(rows),
        "activation_negative_controls_rejected": sum(
            row["negative_controls_rejected"] for row in rows
        ),
        "activation_semantic_reference_documents_passed": len(semantic_rows),
        "activation_semantic_candidate_mode_negative_controls_rejected": sum(
            row["candidate_mode_negative_controls_rejected"]
            for row in semantic_rows
        ),
        "activation_semantic_model_calls": sum(
            row["model_calls"] for row in semantic_rows
        ),
        "activation_semantic_qualification_model_calls": sum(
            row["qualification_model_calls"] for row in semantic_rows
        ),
        "activation_semantic_qualification_reused": bool(
            semantic_rows and all(row["qualification_reused"] for row in semantic_rows)
        ),
    }


def _load_mechanical_activation_record(
    task: Mapping[str, Any], *, project_root: Path,
) -> dict[str, Any]:
    """Verify immutable calibration against its original inputs, without execution."""

    reference = task.get("mechanical_activation_record")
    if not isinstance(reference, Mapping):
        raise ValueError("mechanical activation is not frozen")
    documents = {}
    for name in ("record", "input_manifest"):
        path = _project_path(str(reference.get(name + "_path", "")), project_root=project_root)
        if not path.is_file() or _file_sha256(path) != reference.get(name + "_sha256"):
            raise ValueError(f"mechanical activation {name} hash mismatch")
        documents[name] = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(documents[name], dict):
            raise ValueError(f"mechanical activation {name} must be an object")
    original_tasks = documents["input_manifest"].get("active_tasks", [])
    if not isinstance(original_tasks, list):
        raise ValueError("mechanical activation input_manifest tasks must be an array")
    matching = [row for row in original_tasks if isinstance(row, Mapping)
                and row.get("task_id") == task.get("task_id")]
    fields = ("task_id", "visible_question_hash", "task_intent", "estimator_execution_contract_id",
              "hidden_algorithm_evaluator", "hidden_empirical_evaluator", "activation_candidate_suite")
    if len(matching) != 1 or any(matching[0].get(key) != task.get(key) for key in fields):
        raise ValueError("mechanical activation inputs changed")
    record = documents["record"]
    evaluators = {name: task[field] for name, field in (
        ("algorithm", "hidden_algorithm_evaluator"), ("empirical", "hidden_empirical_evaluator"),
    ) if task.get(field)}
    expected_rejections = sum(len(row["must_fail_evaluators"])
                              for row in task["activation_candidate_suite"]["negative_candidates"])
    if (record.get("status") != "PASSED_BEFORE_FIRST_PRODUCT_MODEL_CALL"
            or record.get("task_id_hash") != stable_hash(str(task["task_id"]))
            or record.get("reference_validator_hashes") != {
                name: stable_hash(value) for name, value in evaluators.items()}
            or type(record.get("negative_controls_rejected")) is not int
            or record.get("negative_controls_rejected") != expected_rejections):
        raise ValueError("mechanical activation qualification mismatch")
    results = record.get("reference_result_hashes")
    if not isinstance(results, Mapping) or set(results) != set(evaluators) or any(
        not isinstance(value, str) or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
        for value in results.values()
    ):
        raise ValueError("mechanical activation reference results missing")
    return record


def evaluate_research_gold_benchmark(
    results: Sequence[Mapping[str, Any]],
    *,
    research_evaluation_summary: Mapping[str, Any],
    benchmark_manifest_path: Path,
    out_dir: Path,
    run_harness: GoldHarnessRunner | None = None,
    run_artifact_harness: GoldArtifactHarnessRunner | None = None,
    run_theory_semantic_judge: GoldTheorySemanticJudgeRunner | None = None,
    theory_semantic_judge_provider: GeneratorBackend | None = None,
) -> dict[str, Any]:
    """Evaluate immutable accepted artifacts against hidden post-runtime gold."""

    benchmark_manifest_path = benchmark_manifest_path.resolve()
    benchmark = _load_benchmark_manifest(benchmark_manifest_path)
    project_root = Path(__file__).resolve().parents[1]
    _validate_benchmark_manifest(
        benchmark,
        manifest_path=benchmark_manifest_path,
        project_root=project_root,
    )
    result_pairs = [
        (question_id, result)
        for result in results
        if (question_id := _runtime_result_question_id(result))
    ]
    result_ids = [question_id for question_id, _ in result_pairs]
    duplicate_result_ids = sorted(
        question_id
        for question_id in set(result_ids)
        if result_ids.count(question_id) > 1
    )
    if duplicate_result_ids:
        raise ValueError(
            "duplicate runtime results for gold task ids: "
            + ", ".join(duplicate_result_ids)
        )
    result_by_question = dict(result_pairs)
    summary_pairs = [
        (str(row.get("question_id", "") or ""), row)
        for row in research_evaluation_summary.get("rows", []) or []
        if isinstance(row, Mapping)
        and str(row.get("question_id", "") or "").strip()
    ]
    summary_ids = [question_id for question_id, _ in summary_pairs]
    duplicate_summary_ids = sorted(
        question_id
        for question_id in set(summary_ids)
        if summary_ids.count(question_id) > 1
    )
    if duplicate_summary_ids:
        raise ValueError(
            "duplicate research summary rows for gold task ids: "
            + ", ".join(duplicate_summary_ids)
        )
    summary_rows = dict(summary_pairs)
    harness_runner = run_harness or _run_hidden_scientific_harness
    artifact_harness_runner = (
        run_artifact_harness or _run_hidden_artifact_harness
    )
    task_rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ai-stat-gold-") as sandbox_value:
        sandbox_root = Path(sandbox_value)
        for task in benchmark["active_tasks"]:
            task_rows.append(
                _evaluate_gold_task(
                    task,
                    runtime_result=result_by_question.get(str(task["task_id"])),
                    research_summary_row=summary_rows.get(str(task["task_id"]), {}),
                    project_root=project_root,
                    sandbox_root=sandbox_root,
                    run_harness=harness_runner,
                    run_artifact_harness=artifact_harness_runner,
                    run_theory_semantic_judge=run_theory_semantic_judge,
                    theory_semantic_judge_provider=theory_semantic_judge_provider,
                )
            )
    payload = {
        "schema_version": 4,
        "artifact_kind": "ResearchCapabilityGoldEvaluation",
        "configured": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": benchmark["benchmark_id"],
        "benchmark_manifest_hash": stable_hash(benchmark),
        "benchmark_authority_location_disclosed": False,
        "gold_visibility": "evaluator_only_after_runtime_termination",
        "n_active_tasks": len(task_rows),
            "n_tasks_evaluated": sum(
                (
                    any(
                        row.get(field) is True
                        for field in (
                            "hidden_harness_execution_attempted",
                            "hidden_theory_execution_attempted",
                            "hidden_theory_semantic_execution_attempted",
                            "hidden_empirical_execution_attempted",
                            "hidden_source_replication_execution_attempted",
                            "hidden_source_report_semantic_execution_attempted",
                        )
                    )
                    or (row.get("runtime_result_observed") is True
                        and row.get("dimension_status", {}).get("formal", {}).get("requirement") == "required")
                )
                for row in task_rows
        ),
        "n_tasks_passed": sum(row["task_passed"] is True for row in task_rows),
        "n_full_task_gold_configured": sum(
            row["full_task_gold_configured"] is True for row in task_rows
        ),
        "all_active_tasks_passed": bool(
            task_rows and all(row["task_passed"] for row in task_rows)
        ),
        "tasks": task_rows,
        "hidden_expected_values_disclosed": False,
        "runtime_feedback_generated": False,
        "proof_evidence_status": "GOLD_EVALUATION_NOT_PROOF_EVIDENCE",
        "boundary": GOLD_EVALUATION_BOUNDARY,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "research_capability_gold_evaluation.json"
    output_path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    payload["artifact_path"] = str(output_path)
    return payload


def _evaluate_gold_task(
    task: Mapping[str, Any],
    *,
    runtime_result: Mapping[str, Any] | None,
    research_summary_row: Mapping[str, Any],
    project_root: Path,
    sandbox_root: Path,
    run_harness: GoldHarnessRunner,
    run_artifact_harness: GoldArtifactHarnessRunner,
    run_theory_semantic_judge: GoldTheorySemanticJudgeRunner | None,
    theory_semantic_judge_provider: GeneratorBackend | None,
) -> dict[str, Any]:
    task_id = str(task["task_id"])
    runtime_requirements = (
        research_summary_row.get("requirements", {})
        if isinstance(research_summary_row.get("requirements", {}), Mapping)
        else {}
    )
    theory_evaluator = task.get("hidden_theory_evaluator", {})
    theory_evaluator = (
        theory_evaluator if isinstance(theory_evaluator, Mapping) else {}
    )
    theory_semantic_evaluator = task.get(
        "hidden_theory_semantic_evaluator", {}
    )
    theory_semantic_evaluator = (
        theory_semantic_evaluator
        if isinstance(theory_semantic_evaluator, Mapping)
        else {}
    )
    empirical_evaluator = task.get("hidden_empirical_evaluator", {})
    empirical_evaluator = (
        empirical_evaluator if isinstance(empirical_evaluator, Mapping) else {}
    )
    algorithm_evaluator = task.get("hidden_algorithm_evaluator", {})
    algorithm_evaluator = (
        algorithm_evaluator if isinstance(algorithm_evaluator, Mapping) else {}
    )
    source_replication_evaluator = task.get(
        "hidden_source_replication_evaluator", {}
    )
    source_replication_evaluator = (
        source_replication_evaluator
        if isinstance(source_replication_evaluator, Mapping)
        else {}
    )
    source_report_semantic_evaluator = task.get(
        "hidden_source_report_semantic_evaluator", {}
    )
    source_report_semantic_evaluator = (
        source_report_semantic_evaluator
        if isinstance(source_report_semantic_evaluator, Mapping)
        else {}
    )
    runtime_terminal_status = (
        str(runtime_result.get("status", "") or "")
        if runtime_result is not None
        else ""
    )
    runtime_terminal_accepted = runtime_terminal_status == "ACCEPTED"
    runtime_research_eval_complete = bool(
        research_summary_row.get("research_eval_complete") is True
        and runtime_terminal_accepted
    )
    base = {
        "task_id": task_id,
        "level": str(task["level"]),
        "scoring_scope": str(
            task.get("scoring_scope", "component") or "component"
        ),
        "full_task_gold_configured": _full_task_gold_configured(task),
        "runtime_result_observed": runtime_result is not None,
        "runtime_terminal_status": runtime_terminal_status,
        "runtime_terminal_accepted": runtime_terminal_accepted,
        "runtime_research_eval_complete": runtime_research_eval_complete,
        "runtime_summary_evidence_hash": str(
            research_summary_row.get("runtime_evidence_hash", "") or ""
        ),
        "runtime_summary_evidence_hash_valid": False,
        "runtime_summary_row_hash_valid": False,
        "runtime_visible_question_hash": "",
        "accepted_algorithm_handoff_id": "",
        "accepted_algorithm_handoff_hash": "",
        "required_estimator_id": str(
            algorithm_evaluator.get("required_estimator_id", "") or ""
        ),
        "estimator_execution_contract_id": str(
            task.get("estimator_execution_contract_id", "") or ""
        ),
        "evaluated_source_hash": "",
        "hidden_evaluator_source_hash": str(
            algorithm_evaluator.get("harness_sha256", "")
            or source_replication_evaluator.get("harness_sha256", "")
            or ""
        ),
        "hidden_harness_execution_attempted": False,
        "hidden_harness_execution_passed": False,
        "hidden_checks_passed": False,
        "hidden_check_results": [],
        "accepted_theory_packet_id": "",
        "accepted_theory_packet_hash": "",
        "accepted_theory_document_count": 0,
        "accepted_theory_document_set_hash": "",
        "hidden_theory_evaluation_configured": bool(
            theory_evaluator or theory_semantic_evaluator
        ),
        "hidden_theory_evaluator_source_hash": str(
            theory_evaluator.get("harness_sha256", "") or ""
        ),
        **_semantic_judgment_metrics({}, prefix="hidden_theory_semantic_", executed=False,
                                   evaluator=theory_semantic_evaluator),
        "hidden_theory_combined_passed": False,
        "hidden_empirical_evaluation_configured": bool(empirical_evaluator),
        "hidden_empirical_evaluator_source_hash": str(
            empirical_evaluator.get("harness_sha256", "") or ""
        ),
        "source_replication_manifest_id": "",
        "source_replication_manifest_hash": "",
        "hidden_source_replication_evaluation_configured": bool(
            source_replication_evaluator
        ),
        "hidden_source_replication_evaluator_source_hash": str(
            source_replication_evaluator.get("harness_sha256", "") or ""
        ),
        **{f"hidden_{scope}_{field}": deepcopy(value)
           for scope in ("theory", "empirical", "source_replication")
           for field, value in (("execution_attempted", False), ("execution_passed", False),
                                ("checks_passed", False), ("check_results", []))},
        "hidden_source_replication_identity_passed": False,
        **_semantic_judgment_metrics({}, prefix="hidden_source_report_semantic_", executed=False,
                                   evaluator=source_report_semantic_evaluator),
        "hidden_source_replication_combined_passed": False,
        "source_replication_report_document_hash": "",
        "source_replication_checkpoint_valid": False,
        "unresolved_gap_disclosure_present": False,
        "formal_kernel_authority_passed": False,
        "formal_kernel_authority_errors": [],
        "dimension_status": {},
        "task_passed": False,
        "failure_reasons": [],
        "proof_evidence_status": "GOLD_EVALUATION_NOT_PROOF_EVIDENCE",
        "boundary": GOLD_EVALUATION_BOUNDARY,
    }
    def reject_runtime_identity(reason: str, *, requirements=runtime_requirements) -> dict[str, Any]:
        base["failure_reasons"] = [reason]
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=requirements,
            runtime_research_eval_complete=False,
            hidden_theory_passed=False,
            hidden_algorithm_passed=False,
            hidden_empirical_passed=False,
            formal_gold_passed=False,
            runtime_result_observed=runtime_result is not None,
        )
        return base

    if runtime_result is None:
        return reject_runtime_identity("runtime result is missing")

    runtime_question = _runtime_result_question(runtime_result)
    runtime_visible_question_hash = stable_hash(
        _visible_question_hash_payload(runtime_question)
    )
    base["runtime_visible_question_hash"] = runtime_visible_question_hash
    if runtime_visible_question_hash != str(task["visible_question_hash"]):
        return reject_runtime_identity(
            "runtime-visible question hash does not match the frozen gold task"
        )

    if research_summary_row:
        observed_evidence_hash = research_evaluation_evidence_hash(runtime_result)
        base["runtime_summary_evidence_hash_valid"] = bool(
            base["runtime_summary_evidence_hash"] == observed_evidence_hash
        )
        reported_row_hash = str(
            research_summary_row.get("summary_row_hash", "") or ""
        )
        summary_row_payload = {
            key: value
            for key, value in research_summary_row.items()
            if key != "summary_row_hash"
        }
        base["runtime_summary_row_hash_valid"] = bool(
            reported_row_hash and reported_row_hash == stable_hash(summary_row_payload)
        )
        if not (
            base["runtime_summary_evidence_hash_valid"]
            and base["runtime_summary_row_hash_valid"]
        ):
            base["runtime_research_eval_complete"] = False
            return reject_runtime_identity(
                "research summary is not bound to this runtime evidence graph", requirements={},
            )

    artifacts = _runtime_artifacts(runtime_result)
    formal_requirement = str(
        (task.get("task_intent", {}) or {}).get("formal", "not_applicable")
        if isinstance(task.get("task_intent", {}), Mapping)
        else "not_applicable"
    )
    formal_gold_passed = False
    formal_authority_errors: list[str] = []
    if formal_requirement == "required" or runtime_requirements.get(
        "exact_formal_target_kernel_closed"
    ) is True:
        formal_gold_passed, formal_authority_errors = (
            _exact_formal_kernel_authority(
                artifacts,
                runtime_question=runtime_question,
            )
        )
    base["formal_kernel_authority_passed"] = formal_gold_passed
    base["formal_kernel_authority_errors"] = formal_authority_errors
    if formal_requirement == "required" and formal_authority_errors:
        base["failure_reasons"].append(
            "required formal evidence is not backed by an exact kernel promotion"
        )
    hidden_source_replication_identity_passed = False
    hidden_source_report_semantic_passed = not source_report_semantic_evaluator
    hidden_source_replication_passed = False
    source_replication_gap_disclosure_present = False
    if source_replication_evaluator:
        source_manifest_id, source_manifest, source_errors = (
            _latest_source_replication_manifest(artifacts, question_id=task_id)
        )
        if source_errors:
            base["failure_reasons"].extend(source_errors)
        else:
            base["source_replication_manifest_id"] = source_manifest_id
            base["source_replication_manifest_hash"] = str(
                source_manifest.get("manifest_hash", "") or ""
            )
            source_report_document, source_replication_gap_disclosure_present = (
                _source_replication_checkpoint_report_document(
                    artifacts,
                    question_id=task_id,
                    source_manifest=source_manifest,
                    task_intent=task.get("task_intent", {}),
                )
            )
            base["source_replication_checkpoint_valid"] = (
                source_replication_gap_disclosure_present
            )
            base["unresolved_gap_disclosure_present"] = (
                source_replication_gap_disclosure_present
            )
            source_harness_path = _project_path(
                str(source_replication_evaluator["harness_path"]),
                project_root=project_root,
            )
            source_execution = dict(
                run_artifact_harness(
                    sandbox_dir=sandbox_root / task_id / "source-replication",
                    artifact_id=f"gold-source-replication-{task_id}",
                    harness_code=source_harness_path.read_text(encoding="utf-8"),
                    harness_dependencies=tuple(
                        str(value)
                        for value in source_replication_evaluator.get(
                            "dependencies", []
                        )
                        or []
                    ),
                    candidate_artifact=source_manifest,
                    seed=int(source_replication_evaluator.get("seed", 0) or 0),
                    replicates=int(
                        source_replication_evaluator.get("replicates", 1) or 1
                    ),
                    timeout_s=int(
                        source_replication_evaluator.get("timeout_seconds", 60) or 60
                    ),
                )
            )
            source_summary = _hidden_execution_summary(
                source_execution,
                evaluator=source_replication_evaluator,
            )
            hidden_source_replication_identity_passed = source_summary["passed"]
            base.update(
                {
                    "hidden_harness_execution_attempted": source_summary[
                        "execution_attempted"
                    ],
                    "hidden_harness_execution_passed": source_summary[
                        "execution_passed"
                    ],
                    "hidden_checks_passed": source_summary["checks_passed"],
                    "hidden_check_results": source_summary["check_results"],
                    "hidden_source_replication_execution_attempted": source_summary[
                        "execution_attempted"
                    ],
                    "hidden_source_replication_execution_passed": source_summary[
                        "execution_passed"
                    ],
                    "hidden_source_replication_checks_passed": source_summary[
                        "checks_passed"
                    ],
                    "hidden_source_replication_check_results": source_summary[
                        "check_results"
                    ],
                    "hidden_source_replication_identity_passed": (
                        hidden_source_replication_identity_passed
                    ),
                }
            )
            base["failure_reasons"].extend(source_summary["errors"])
            if source_report_document is not None:
                base["source_replication_report_document_hash"] = stable_hash(
                    {
                        "path": source_report_document.get("path", ""),
                        "sha256": source_report_document.get("sha256", ""),
                    }
                )
            if source_report_document is not None and source_report_semantic_evaluator:
                semantic_evidence_document = (
                    _source_replication_semantic_evidence_document(
                        source_manifest=source_manifest,
                        source_execution=source_execution,
                    )
                )
                semantic_judgment, semantic_error = (
                    _run_hidden_document_semantic_evaluation(
                        evaluator=source_report_semantic_evaluator,
                        task_id=task_id,
                        visible_question=runtime_question,
                        candidate_documents=[
                            source_report_document,
                            semantic_evidence_document,
                        ],
                        project_root=project_root,
                        run_semantic_judge=run_theory_semantic_judge,
                        semantic_judge_provider=theory_semantic_judge_provider,
                        semantic_artifact_role="source_replication_report",
                    )
                )
                if semantic_error:
                    base["failure_reasons"].append(semantic_error)
                elif semantic_judgment is not None:
                    hidden_source_report_semantic_passed = (
                        semantic_judgment.get("passed") is True
                    )
                    base.update(_semantic_judgment_metrics(
                        semantic_judgment, prefix="hidden_source_report_semantic_",
                    ))
            hidden_source_replication_passed = bool(
                hidden_source_replication_identity_passed
                and hidden_source_report_semantic_passed
            )
            base["hidden_source_replication_combined_passed"] = (
                hidden_source_replication_passed
            )
    hidden_theory_passed = False
    if theory_evaluator or theory_semantic_evaluator:
        theory_id, theory_packet, theory_errors = _latest_accepted_theory_packet(
            artifacts
        )
        if theory_errors:
            base["failure_reasons"].extend(theory_errors)
        else:
            base["accepted_theory_packet_id"] = theory_id
            base["accepted_theory_packet_hash"] = stable_hash(theory_packet)
            try:
                theory_candidate = _hidden_theory_candidate_artifact(
                    theory_packet
                )
            except (OSError, UnicodeError, ValueError) as exc:
                base["failure_reasons"].append(str(exc))
                theory_candidate = None
            authoritative_documents = (
                theory_candidate.get("authoritative_theory_documents", [])
                if isinstance(theory_candidate, Mapping)
                else []
            )
            base["accepted_theory_document_count"] = len(
                authoritative_documents
            )
            base["accepted_theory_document_set_hash"] = stable_hash(
                [
                    (row.get("path", ""), row.get("sha256", ""))
                    for row in authoritative_documents
                    if isinstance(row, Mapping)
                ]
            )
            mechanical_theory_passed = not theory_evaluator
            if theory_candidate is not None and theory_evaluator:
                theory_harness_path = _project_path(
                    str(theory_evaluator["harness_path"]),
                    project_root=project_root,
                )
                theory_execution = dict(
                    run_artifact_harness(
                        sandbox_dir=sandbox_root / task_id / "theory",
                        artifact_id=f"gold-theory-{task_id}",
                        harness_code=theory_harness_path.read_text(encoding="utf-8"),
                        harness_dependencies=tuple(
                            str(value)
                            for value in theory_evaluator.get("dependencies", []) or []
                        ),
                        candidate_artifact=theory_candidate,
                        seed=int(theory_evaluator.get("seed", 0) or 0),
                        replicates=int(theory_evaluator.get("replicates", 1) or 1),
                        timeout_s=int(
                            theory_evaluator.get("timeout_seconds", 60) or 60
                        ),
                    )
                )
                theory_summary = _hidden_execution_summary(
                    theory_execution,
                    evaluator=theory_evaluator,
                )
                mechanical_theory_passed = theory_summary["passed"]
                base.update(
                    {
                        "hidden_theory_execution_attempted": theory_summary[
                            "execution_attempted"
                        ],
                        "hidden_theory_execution_passed": theory_summary[
                            "execution_passed"
                        ],
                        "hidden_theory_result_hash": theory_summary["result_hash"],
                        "hidden_theory_checks_passed": theory_summary[
                            "checks_passed"
                        ],
                        "hidden_theory_check_results": theory_summary[
                            "check_results"
                        ],
                    }
                )
                base["failure_reasons"].extend(theory_summary["errors"])
            semantic_theory_passed = not theory_semantic_evaluator
            if theory_candidate is not None and theory_semantic_evaluator:
                semantic_judgment, semantic_error = (
                    _run_hidden_document_semantic_evaluation(
                        evaluator=theory_semantic_evaluator,
                        task_id=task_id,
                        visible_question=runtime_question,
                        candidate_documents=_hidden_theory_semantic_candidate_documents(
                            theory_candidate
                        ),
                        project_root=project_root,
                        run_semantic_judge=run_theory_semantic_judge,
                        semantic_judge_provider=theory_semantic_judge_provider,
                        semantic_artifact_role="theory",
                    )
                )
                if semantic_error:
                    base["failure_reasons"].append(semantic_error)
                elif semantic_judgment is not None:
                    semantic_theory_passed = (
                        semantic_judgment.get("passed") is True
                    )
                    base.update(_semantic_judgment_metrics(
                        semantic_judgment, prefix="hidden_theory_semantic_",
                    ))
            hidden_theory_passed = bool(
                theory_candidate is not None
                and mechanical_theory_passed
                and semantic_theory_passed
            )
            base["hidden_theory_combined_passed"] = hidden_theory_passed

    if not algorithm_evaluator:
        dimensions = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=base["runtime_research_eval_complete"],
            hidden_theory_passed=hidden_theory_passed,
            hidden_algorithm_passed=True,
            hidden_empirical_passed=not empirical_evaluator,
            formal_gold_passed=formal_gold_passed,
            runtime_result_observed=True,
            hidden_source_replication_passed=hidden_source_replication_passed,
            source_replication_gap_disclosure_present=(
                source_replication_gap_disclosure_present
            ),
        )
        required_dimensions_passed = all(
            row["status"] == "passed"
            for row in dimensions.values()
            if row["requirement"] == "required"
        )
        base["dimension_status"] = dimensions
        if (
            source_replication_evaluator
            and not hidden_source_replication_identity_passed
        ):
            base["failure_reasons"].append(
                "hidden source-replication identity checks did not all pass"
            )
        if (
            source_report_semantic_evaluator
            and not hidden_source_report_semantic_passed
        ):
            base["failure_reasons"].append(
                "hidden source-report semantic checks did not all pass"
            )
        dimension_failures = [
            dimension
            for dimension, row in dimensions.items()
            if row["requirement"] == "required" and row["status"] != "passed"
        ]
        base["failure_reasons"].extend(
            f"required evidence dimension did not pass: {dimension}"
            for dimension in dimension_failures
        )
        base["failure_reasons"] = list(dict.fromkeys(base["failure_reasons"]))
        full_task = base["scoring_scope"] == "full_task"
        base["task_passed"] = bool(
            required_dimensions_passed
            and (not source_replication_evaluator or hidden_source_replication_passed)
            and (
                not full_task
                or base["runtime_research_eval_complete"] is True
            )
        )
        return base

    def reject_algorithm_source(errors: Sequence[str]) -> dict[str, Any]:
        base["failure_reasons"].extend(errors)
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=base["runtime_research_eval_complete"],
            hidden_theory_passed=hidden_theory_passed,
            hidden_algorithm_passed=False,
            hidden_empirical_passed=False,
            formal_gold_passed=formal_gold_passed,
            runtime_result_observed=True,
            source_replication_gap_disclosure_present=(
                source_replication_gap_disclosure_present
            ),
        )
        return base

    accepted_id, accepted_handoff, errors = _latest_accepted_algorithm_handoff(
        runtime_result,
        artifacts,
    )
    if errors:
        return reject_algorithm_source(errors)
    base["accepted_algorithm_handoff_id"] = accepted_id
    base["accepted_algorithm_handoff_hash"] = stable_hash(accepted_handoff)

    evaluator = algorithm_evaluator
    estimator_id = str(evaluator["required_estimator_id"])
    source_rows = [
        row
        for row in accepted_handoff.get("exact_algorithm_artifacts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "") == estimator_id
    ]
    if len(source_rows) != 1:
        return reject_algorithm_source([
            "accepted algorithm handoff does not contain exactly one required "
            f"estimator source: {estimator_id}"
        ])
    source = source_rows[0]
    source_code = str(source.get("exact_source_code", "") or "")
    source_hash = str(source.get("exact_source_hash", "") or "")
    if not source_code or source_hash != stable_hash(source_code):
        return reject_algorithm_source([
            "accepted estimator source is missing or its immutable hash is invalid"
        ])
    try:
        source_project_files = normalized_scientific_project_files(
            source.get("exact_project_files", []),
            language=str(source.get("language", "") or "python"),
        )
        source_project_hash = scientific_project_hash(
            language=str(source.get("language", "") or "python"),
            code=source_code,
            project_files=source_project_files,
        )
    except ValueError as exc:
        return reject_algorithm_source([
            "accepted estimator project is invalid: " + str(exc)
        ])
    persisted_project_hash = str(source.get("exact_project_hash", "") or "")
    if persisted_project_hash != source_project_hash:
        return reject_algorithm_source([
            "accepted estimator project hash is invalid"
        ])
    base["evaluated_source_hash"] = source_hash
    base["evaluated_project_hash"] = source_project_hash

    harness_path = _project_path(
        str(evaluator["harness_path"]),
        project_root=project_root,
    )
    harness_code = harness_path.read_text(encoding="utf-8")
    execution = dict(
        run_harness(
            sandbox_dir=sandbox_root / task_id / "algorithm",
            artifact_id=f"gold-{task_id}",
            harness_language=str(evaluator.get("language", "") or "python"),
            **({"harness_execution_profile": evaluator["execution_profile"]} if "execution_profile" in evaluator else {}),
            harness_code=harness_code,
            harness_dependencies=tuple(
                str(value) for value in evaluator.get("dependencies", []) or []
            ),
            estimator_binding=ScientificEstimatorBinding(
                artifact_id=estimator_id,
                language=str(source.get("language", "") or "python"),
                code=source_code,
                code_hash=source_hash,
                dependencies=tuple(
                    str(value) for value in source.get("dependencies", []) or []
                ),
                project_files=source_project_files,
                project_hash=source_project_hash,
            ),
            seed=int(evaluator.get("seed", 0) or 0),
            replicates=int(evaluator.get("replicates", 1) or 1),
            timeout_s=int(evaluator.get("timeout_seconds", 60) or 60),
        )
    )
    algorithm_summary = _hidden_execution_summary(
        execution,
        evaluator=evaluator,
        required_estimator_id=estimator_id,
    )
    hidden_algorithm_passed = algorithm_summary["passed"]
    base.update(
        {
            "hidden_harness_execution_attempted": algorithm_summary[
                "execution_attempted"
            ],
            "hidden_harness_execution_passed": algorithm_summary[
                "execution_passed"
            ],
            "hidden_harness_result_hash": algorithm_summary["result_hash"],
            "hidden_harness_estimator_invocation_count": (
                algorithm_summary["estimator_invocation_count"]
            ),
            "hidden_checks_passed": algorithm_summary["checks_passed"],
            "hidden_check_results": algorithm_summary["check_results"],
        }
    )
    base["failure_reasons"].extend(algorithm_summary["errors"])

    hidden_empirical_passed = False
    if empirical_evaluator:
        empirical_harness_path = _project_path(
            str(empirical_evaluator["harness_path"]),
            project_root=project_root,
        )
        empirical_execution = dict(
            run_harness(
                sandbox_dir=sandbox_root / task_id / "empirical",
                artifact_id=f"gold-empirical-{task_id}",
                harness_language=str(
                    empirical_evaluator.get("language", "") or "python"
                ),
                **({"harness_execution_profile": empirical_evaluator["execution_profile"]} if "execution_profile" in empirical_evaluator else {}),
                harness_code=empirical_harness_path.read_text(encoding="utf-8"),
                harness_dependencies=tuple(
                    str(value)
                    for value in empirical_evaluator.get("dependencies", []) or []
                ),
                estimator_binding=ScientificEstimatorBinding(
                    artifact_id=estimator_id,
                    language=str(source.get("language", "") or "python"),
                    code=source_code,
                    code_hash=source_hash,
                    dependencies=tuple(
                        str(value)
                        for value in source.get("dependencies", []) or []
                    ),
                    project_files=source_project_files,
                    project_hash=source_project_hash,
                ),
                seed=int(empirical_evaluator.get("seed", 0) or 0),
                replicates=int(empirical_evaluator.get("replicates", 1) or 1),
                timeout_s=int(
                    empirical_evaluator.get("timeout_seconds", 60) or 60
                ),
            )
        )
        empirical_summary = _hidden_execution_summary(
            empirical_execution,
            evaluator=empirical_evaluator,
            required_estimator_id=estimator_id,
        )
        hidden_empirical_passed = empirical_summary["passed"]
        base.update(
            {
                "hidden_empirical_execution_attempted": empirical_summary[
                    "execution_attempted"
                ],
                "hidden_empirical_execution_passed": empirical_summary[
                    "execution_passed"
                ],
                "hidden_empirical_result_hash": empirical_summary["result_hash"],
                "hidden_empirical_estimator_invocation_count": (
                    empirical_summary["estimator_invocation_count"]
                ),
                "hidden_empirical_checks_passed": empirical_summary[
                    "checks_passed"
                ],
                "hidden_empirical_check_results": empirical_summary[
                    "check_results"
                ],
            }
        )
        base["failure_reasons"].extend(empirical_summary["errors"])

    dimensions = _dimension_status(
        task,
        runtime_requirements=runtime_requirements,
        runtime_research_eval_complete=base["runtime_research_eval_complete"],
        hidden_theory_passed=hidden_theory_passed,
        hidden_algorithm_passed=hidden_algorithm_passed,
        hidden_empirical_passed=hidden_empirical_passed,
        formal_gold_passed=formal_gold_passed,
        runtime_result_observed=True,
        hidden_source_replication_passed=hidden_source_replication_passed,
        source_replication_gap_disclosure_present=(
            source_replication_gap_disclosure_present
        ),
    )
    required_dimensions_passed = all(
        row["status"] == "passed"
        for row in dimensions.values()
        if row["requirement"] == "required"
    )
    base["dimension_status"] = dimensions
    dimension_failures = [
        dimension
        for dimension, row in dimensions.items()
        if row["requirement"] == "required" and row["status"] != "passed"
    ]
    if not hidden_algorithm_passed:
        base["failure_reasons"].append(
            "hidden algorithm acceptance checks did not all pass"
        )
    if (theory_evaluator or theory_semantic_evaluator) and not hidden_theory_passed:
        base["failure_reasons"].append(
            "hidden theory acceptance checks did not all pass"
        )
    if empirical_evaluator and not hidden_empirical_passed:
        base["failure_reasons"].append(
            "hidden empirical acceptance checks did not all pass"
        )
    base["failure_reasons"].extend(
        f"required evidence dimension did not pass: {dimension}"
        for dimension in dimension_failures
    )
    base["failure_reasons"] = list(dict.fromkeys(base["failure_reasons"]))
    base["task_passed"] = bool(
        required_dimensions_passed
        and hidden_algorithm_passed
        and base["runtime_research_eval_complete"] is True
    )
    return base


def _exact_formal_kernel_authority(
    artifacts: Mapping[str, Any],
    *,
    runtime_question: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    contract = runtime_question.get("formal_target_contract", {})
    if not isinstance(contract, Mapping) or not contract:
        return False, ["runtime question has no frozen formal target contract"]
    question_id = str(runtime_question.get("id", "") or "")
    manifests = [
        artifact
        for artifact in artifacts.values()
        if isinstance(artifact, Mapping)
        and isinstance(artifact.get("question", {}), Mapping)
        and artifact.get("artifact_kind") == "RuntimeFormalizationManifest"
        and str(artifact.get("question", {}).get("id", "") or "") == question_id
    ]
    if not manifests:
        return False, ["no formalization manifest exists for the frozen target"]
    candidate_errors: list[str] = []
    for manifest in manifests:
        errors = lean_kernel_promotion_evidence_errors(
            manifest,
            blackboard_artifacts=artifacts,
            expected_question_id=question_id,
            expected_formal_target_contract=contract,
        )
        if not errors:
            return True, []
        manifest_id = str(manifest.get("manifest_id", "") or "<missing>")
        candidate_errors.extend(f"{manifest_id}: {error}" for error in errors)
    return False, list(dict.fromkeys(candidate_errors))


def _dimension_status(
    task: Mapping[str, Any],
    *,
    runtime_requirements: Mapping[str, Any],
    runtime_research_eval_complete: bool,
    hidden_theory_passed: bool,
    hidden_algorithm_passed: bool,
    hidden_empirical_passed: bool,
    formal_gold_passed: bool,
    runtime_result_observed: bool,
    hidden_source_replication_passed: bool = False,
    source_replication_gap_disclosure_present: bool = False,
) -> dict[str, dict[str, Any]]:
    intent = task.get("task_intent", {})
    intent = intent if isinstance(intent, Mapping) else {}
    observed = {
        "source_replication": hidden_source_replication_passed,
        "theory": bool(
            runtime_requirements.get("serious_theory_completed") is True
            and runtime_requirements.get(
                "theory_preexecution_review_accepted"
            )
            is True
        ),
        "scientific_code": bool(
            runtime_requirements.get("generated_algorithm_executed_and_passed")
            is True
            and runtime_requirements.get("algorithm_semantic_review_accepted")
            is True
            and hidden_algorithm_passed
        ),
        "empirical": bool(
            runtime_requirements.get("generated_simulation_executed_and_passed")
            is True
            and runtime_requirements.get(
                "simulation_metric_evidence_nonvacuous_and_bound"
            )
            is True
            and runtime_requirements.get("simulation_semantic_review_accepted")
            is True
        ),
        "formal": bool(runtime_result_observed and formal_gold_passed),
        "novelty": False,
        "unresolved_gaps": bool(
            source_replication_gap_disclosure_present
            or (
                runtime_result_observed
                and runtime_requirements.get(
                    "critic_unresolved_gap_disclosure_present"
                )
                is True
            )
        ),
    }
    rows: dict[str, dict[str, Any]] = {}
    for dimension in (
        "source_replication",
        "theory",
        "scientific_code",
        "empirical",
        "formal",
        "novelty",
        "unresolved_gaps",
    ):
        requirement = str(intent.get(dimension, "not_applicable") or "")
        if requirement == "not_applicable":
            status = "not_applicable"
        elif dimension == "theory" and observed[dimension]:
            status = (
                "passed"
                if hidden_theory_passed
                else "runtime_reviewed_not_gold_validated"
            )
        elif dimension == "empirical" and observed[dimension]:
            status = (
                "passed"
                if hidden_empirical_passed
                else "runtime_accepted_not_gold_validated"
            )
        elif dimension == "empirical" and hidden_empirical_passed:
            status = "hidden_gold_passed_runtime_not_accepted"
        elif observed[dimension]:
            status = "passed"
        elif requirement == "optional":
            status = "missing_optional"
        else:
            status = "failed"
        rows[dimension] = {
            "requirement": requirement,
            "status": status,
            "gold_validated": bool(
                requirement != "not_applicable"
                and (
                    (dimension == "theory" and hidden_theory_passed)
                    or (
                        dimension == "source_replication"
                        and hidden_source_replication_passed
                    )
                    or (
                        dimension == "scientific_code"
                        and hidden_algorithm_passed
                    )
                    or (dimension == "empirical" and hidden_empirical_passed)
                    or (dimension == "formal" and observed[dimension])
                )
            ),
            "evidence_authority": (
                "not_configured"
                if requirement == "not_applicable"
                else {
                    "theory": (
                        "evaluator_only_hidden_artifact_harness"
                        if hidden_theory_passed
                        else "runtime_independent_review"
                    ),
                    "scientific_code": "evaluator_only_hidden_harness",
                    "empirical": (
                        "evaluator_only_hidden_empirical_harness"
                        if hidden_empirical_passed
                        else "runtime_confirmatory_protocol"
                    ),
                    "source_replication": (
                        "evaluator_only_hidden_source_replication_harness"
                    ),
                    "formal": "operator_frozen_exact_target_plus_runtime_lean_kernel",
                    "unresolved_gaps": (
                        "source_replication_checkpoint"
                        if source_replication_gap_disclosure_present
                        else "runtime_critic_disclosure"
                    ),
                }.get(dimension, "not_configured")
            ),
        }
    overall_requirement = (
        "required"
        if str(task.get("scoring_scope", "component") or "component")
        == "full_task"
        else "not_applicable"
    )
    rows["overall_runtime_research_loop"] = {
        "requirement": overall_requirement,
        "status": (
            "not_applicable"
            if overall_requirement == "not_applicable"
            else ("passed" if runtime_research_eval_complete else "failed")
        ),
        "gold_validated": False,
        "evidence_authority": "runtime_completion_contract",
    }
    return rows


def _hidden_theory_candidate_artifact(
    theory_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Hydrate accepted theory documents only inside evaluator authority."""

    candidate = deepcopy(dict(theory_packet))
    authority_context = document_authoritative_theory_context(theory_packet)
    candidate.update({key: authority_context[key] for key in ("document_authoritative", "authoritative_theory_documents")})
    rows = candidate["authoritative_theory_documents"]
    candidate["evaluator_document_hydration"] = {
        "document_count": len(rows),
        "document_set_hash": stable_hash(
            [(row["path"], row["sha256"]) for row in rows]
        ),
        "runtime_feedback_generated": False,
        "visibility": "evaluator_only_after_runtime_termination",
        "boundary": GOLD_EVALUATION_BOUNDARY,
    }
    return candidate


def _hidden_theory_semantic_candidate_documents(
    theory_candidate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    authoritative_rows = theory_candidate.get("authoritative_theory_documents", []) or []
    documents = [
        deepcopy(dict(row)) for row in authoritative_rows if isinstance(row, Mapping)
    ]
    interface_keys = (
        "id", "name", "inputs", "outputs", "estimator_interface_contract_id",
        "estimator_interface_contract", "termination_guarantee",
    )
    estimator_specs = [
        {key: deepcopy(row[key]) for key in interface_keys if key in row}
        for row in theory_candidate.get("estimator_specs", []) or []
        if isinstance(row, Mapping)
    ]
    if estimator_specs:
        payload = {"artifact_kind": "ModelAuthoredTheorySemanticInterfaceProjection",
                   "estimator_specs": estimator_specs,
                   "content_authority": "model_authored_structured_executable_abi"}
        content = json.dumps(payload, indent=2, sort_keys=True)
        documents.append({"path": "model_authored_estimator_interfaces.json",
                          "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                          "content": content})
    return documents


def _load_hidden_theory_semantic_authority(
    evaluator: Mapping[str, Any],
    *,
    project_root: Path,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    reference_documents: list[dict[str, Any]] = []
    for row in evaluator.get("reference_documents", []) or []:
        if not isinstance(row, Mapping):
            raise ValueError("hidden theory semantic reference row is invalid")
        path = _project_path(
            str(row.get("path", "") or ""),
            project_root=project_root,
        )
        if _file_sha256(path) != str(row.get("sha256", "") or ""):
            raise ValueError("hidden theory semantic reference hash mismatch")
        reference_documents.append(
            {
                "document_id": str(row.get("document_id", "") or path.name),
                "sha256": str(row["sha256"]),
                "content": path.read_text(encoding="utf-8"),
            }
        )
    rubric = _load_hidden_json_authority(
        evaluator,
        path_field="rubric_path",
        hash_field="rubric_sha256",
        project_root=project_root,
    )
    calibration_payload = _load_hidden_json_authority(
        evaluator,
        path_field="calibration_cases_path",
        hash_field="calibration_cases_sha256",
        project_root=project_root,
    )
    candidate_mode_negative_payload: Mapping[str, Any] = {"cases": []}
    if evaluator.get("candidate_mode_negative_cases_path"):
        candidate_mode_negative_payload = _load_hidden_json_authority(
            evaluator,
            path_field="candidate_mode_negative_cases_path",
            hash_field="candidate_mode_negative_cases_sha256",
            project_root=project_root,
        )
    return (
        reference_documents,
        rubric,
        _hydrate_hidden_semantic_cases(
            calibration_payload,
            project_root=project_root,
            label="calibration",
        ),
        _hydrate_hidden_semantic_cases(
            candidate_mode_negative_payload,
            project_root=project_root,
            label="candidate-mode negative",
        ),
    )


def _hydrate_hidden_semantic_cases(
    payload: Mapping[str, Any],
    *,
    project_root: Path,
    label: str,
) -> list[dict[str, Any]]:
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError(f"hidden theory semantic {label} cases are invalid")
    hydrated_cases: list[dict[str, Any]] = []
    for row in cases:
        if not isinstance(row, Mapping):
            continue
        hydrated = dict(row)
        hydrated_documents: list[dict[str, Any]] = []
        for document in row.get("documents", []) or []:
            if not isinstance(document, Mapping):
                continue
            source_path_value = str(document.get("source_path", "") or "")
            if not source_path_value:
                hydrated_documents.append(dict(document))
                continue
            source_path = _project_path(
                source_path_value,
                project_root=project_root,
            )
            expected_hash = str(document.get("sha256", "") or "")
            if _file_sha256(source_path) != expected_hash:
                raise ValueError(
                    f"hidden theory semantic {label} document hash mismatch"
                )
            hydrated_documents.append(
                {
                    "path": str(
                        document.get("document_id", "") or source_path.name
                    ),
                    "sha256": expected_hash,
                    "content": source_path.read_text(encoding="utf-8"),
                }
            )
        hydrated["documents"] = hydrated_documents
        hydrated_cases.append(hydrated)
    return hydrated_cases


def _load_hidden_semantic_activation_judgment(
    evaluator: Mapping[str, Any],
    *,
    task_id: str,
    visible_question: Mapping[str, Any],
    reference_documents: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    calibration_cases: Sequence[Mapping[str, Any]],
    candidate_mode_negative_cases: Sequence[Mapping[str, Any]],
    project_root: Path,
    semantic_artifact_role: str,
) -> dict[str, Any] | None:
    record_path_value = str(
        evaluator.get("activation_record_path", "") or ""
    ).strip()
    if not record_path_value:
        return None
    record_path = _project_path(record_path_value, project_root=project_root)
    expected_hash = str(
        evaluator.get("activation_record_sha256", "") or ""
    )
    if not expected_hash or _file_sha256(record_path) != expected_hash:
        raise ValueError("hidden semantic activation record hash mismatch")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("hidden semantic activation record is invalid") from exc
    if not isinstance(record, Mapping):
        raise ValueError("hidden semantic activation record must be an object")
    record_checks = {
        "artifact_kind": "HiddenSemanticActivationAttempt",
        "status": "COMPLETED",
        "task_id": task_id,
        "model": str(evaluator.get("model", "") or ""),
        "model_tier": str(evaluator.get("model_tier", "") or ""),
        "product_runtime_started": False,
    }
    for field, expected in record_checks.items():
        if record.get(field) != expected:
            raise ValueError(
                f"hidden semantic activation record {field} mismatch"
            )
    judgment = record.get("judgment")
    if not isinstance(judgment, Mapping):
        raise ValueError("hidden semantic activation judgment is missing")
    errors = theory_semantic_activation_judgment_errors(
        judgment,
        task_id=task_id,
        visible_question=visible_question,
        reference_documents=reference_documents,
        rubric=rubric,
        calibration_cases=calibration_cases,
        candidate_mode_negative_cases=candidate_mode_negative_cases,
        provider_name=str(evaluator.get("provider", "") or ""),
        model=str(evaluator.get("model", "") or ""),
        model_tier=str(evaluator.get("model_tier", "") or ""),
        semantic_artifact_role=semantic_artifact_role,
        max_tokens=int(evaluator.get("max_tokens", 6000) or 6000),
        candidate_adjudication_strategy=str(
            evaluator.get(
                "candidate_adjudication_strategy",
                "integrated_single",
            )
            or "integrated_single"
        ),
    )
    if errors:
        raise ValueError(
            "invalid hidden semantic activation record: " + "; ".join(errors)
        )
    return deepcopy(dict(judgment))


def _run_hidden_document_semantic_evaluation(
    *,
    evaluator: Mapping[str, Any],
    task_id: str,
    visible_question: Mapping[str, Any],
    candidate_documents: Sequence[Mapping[str, Any]] | None,
    project_root: Path,
    run_semantic_judge: GoldTheorySemanticJudgeRunner | None,
    semantic_judge_provider: GeneratorBackend | None,
    semantic_artifact_role: str,
) -> tuple[dict[str, Any] | None, str]:
    try:
        (
            reference_documents,
            rubric,
            calibration_cases,
            candidate_mode_negative_cases,
        ) = (
            _load_hidden_theory_semantic_authority(
                evaluator,
                project_root=project_root,
            )
        )
        activation_judgment = _load_hidden_semantic_activation_judgment(
            evaluator,
            task_id=task_id,
            visible_question=visible_question,
            reference_documents=reference_documents,
            rubric=rubric,
            calibration_cases=calibration_cases,
            candidate_mode_negative_cases=candidate_mode_negative_cases,
            project_root=project_root,
            semantic_artifact_role=semantic_artifact_role,
        )
        kwargs = {
            "task_id": task_id,
            "visible_question": visible_question,
            "candidate_documents": (
                candidate_documents
                if candidate_documents is not None
                else reference_documents
            ),
            "reference_documents": reference_documents,
            "rubric": rubric,
            "calibration_cases": calibration_cases,
            "candidate_mode_negative_cases": candidate_mode_negative_cases,
            "model": str(evaluator["model"]),
            "model_tier": str(evaluator["model_tier"]),
            "max_tokens": int(evaluator.get("max_tokens", 6000) or 6000),
            "semantic_artifact_role": semantic_artifact_role,
            "activation_judgment": activation_judgment,
            "candidate_adjudication_strategy": str(
                evaluator.get(
                    "candidate_adjudication_strategy",
                    "integrated_single",
                )
                or "integrated_single"
            ),
        }
        if run_semantic_judge is not None:
            return dict(run_semantic_judge(**kwargs)), ""
        resolve_live_evaluation_model(str(evaluator["provider"]))
        provider = semantic_judge_provider or LocalChatGeneratorBackend(
            timeout_s=float(evaluator.get("timeout_seconds", 120) or 120)
        )
        return dict(
            run_theory_semantic_gold_judge(
                provider=provider,
                workspace_root=_project_path(str(evaluator["rubric_path"]), project_root=project_root).parent / "semantic_review_workspaces",
                **kwargs,
            )
        ), ""
    except Exception as exc:
        message = str(exc)
        if "invalid hidden calibration semantic judgment" in message:
            failure_code = "INVALID_CALIBRATION_JUDGMENT"
        elif "invalid hidden candidate" in message:
            failure_code = "INVALID_CANDIDATE_JUDGMENT"
        elif "semantic judge provider" in message:
            failure_code = "PROVIDER_FAILURE"
        else:
            failure_code = "EVALUATOR_FAILURE"
        return None, (
            f"hidden {semantic_artifact_role} semantic evaluation failed closed: "
            f"{type(exc).__name__}:{failure_code}"
        )


def _run_semantic_candidate_mode_activation(
    *,
    evaluator: Mapping[str, Any],
    task_id: str,
    visible_question: Mapping[str, Any],
    project_root: Path,
    run_semantic_judge: GoldTheorySemanticJudgeRunner | None,
    semantic_judge_provider: GeneratorBackend | None,
    semantic_artifact_role: str,
) -> dict[str, Any]:
    reused_activation = False
    judgment: dict[str, Any] | None = None
    error = ""
    if evaluator.get("activation_record_path"):
        (
            reference_documents,
            rubric,
            calibration_cases,
            candidate_mode_negative_cases,
        ) = _load_hidden_theory_semantic_authority(
            evaluator,
            project_root=project_root,
        )
        judgment = _load_hidden_semantic_activation_judgment(
            evaluator,
            task_id=task_id,
            visible_question=visible_question,
            reference_documents=reference_documents,
            rubric=rubric,
            calibration_cases=calibration_cases,
            candidate_mode_negative_cases=candidate_mode_negative_cases,
            project_root=project_root,
            semantic_artifact_role=semantic_artifact_role,
        )
        reused_activation = judgment is not None
    else:
        judgment, error = _run_hidden_document_semantic_evaluation(
            evaluator=evaluator,
            task_id=task_id,
            visible_question=visible_question,
            candidate_documents=None,
            project_root=project_root,
            run_semantic_judge=run_semantic_judge,
            semantic_judge_provider=semantic_judge_provider,
            semantic_artifact_role=semantic_artifact_role,
        )
    if error or judgment is None:
        raise ValueError(
            "schema_version 4 semantic reference or candidate-mode negative "
            "control failed exact candidate adjudication: "
            f"{error or 'missing evaluator judgment'}"
        )
    negative_count = int(
        judgment.get("n_candidate_mode_negative_cases", 0) or 0
    )
    activation_passed = bool(
        negative_count > 0
        and judgment.get("passed") is True
        and judgment.get("semantic_judge_calibrated") is True
        and judgment.get("candidate_status") == "PASS"
        and judgment.get("candidate_document_status") == "PASS"
        and int(
            judgment.get("n_candidate_mode_negative_cases_correct", 0) or 0
        )
        == negative_count
        and judgment.get("candidate_mode_negative_controls_passed") is True
    )
    if not activation_passed:
        raise ValueError(
            "schema_version 4 semantic reference or candidate-mode negative "
            "control failed exact candidate adjudication: "
            f"calibration={int(judgment.get('n_calibration_cases_correct', 0) or 0)}/"
            f"{int(judgment.get('n_calibration_cases', 0) or 0)}; "
            "candidate_mode_negative="
            f"{int(judgment.get('n_candidate_mode_negative_cases_correct', 0) or 0)}/"
            f"{negative_count}; "
            f"reference_status={str(judgment.get('candidate_status', '') or '')}; "
            "reference_document_status="
            f"{str(judgment.get('candidate_document_status', '') or '')}; "
            f"calibrated={judgment.get('semantic_judge_calibrated') is True}"
        )
    return {
        "task_id_hash": stable_hash(task_id),
        "semantic_artifact_role": semantic_artifact_role,
        "candidate_mode_negative_controls_rejected": negative_count,
        "model_calls": (
            0
            if reused_activation
            else int(judgment.get("n_model_calls", 0) or 0)
        ),
        "qualification_model_calls": (
            int(judgment.get("n_model_calls", 0) or 0)
            if reused_activation
            else 0
        ),
        "qualification_reused": reused_activation,
        "judgment_hash": str(judgment.get("judgment_hash", "") or ""),
    }


def _load_hidden_json_authority(
    evaluator: Mapping[str, Any],
    *,
    path_field: str,
    hash_field: str,
    project_root: Path,
) -> dict[str, Any]:
    path = _project_path(
        str(evaluator.get(path_field, "") or ""),
        project_root=project_root,
    )
    if _file_sha256(path) != str(evaluator.get(hash_field, "") or ""):
        raise ValueError(f"hidden theory semantic {path_field} hash mismatch")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"hidden theory semantic {path_field} must be an object")
    return dict(payload)


def _full_task_gold_configured(task: Mapping[str, Any]) -> bool:
    if str(task.get("scoring_scope", "component") or "component") != "full_task":
        return False
    intent = task.get("task_intent", {})
    if not isinstance(intent, Mapping):
        return False
    if str(intent.get("scientific_code", "not_applicable")) == "required" and not (
        isinstance(task.get("hidden_algorithm_evaluator"), Mapping)
        and task.get("hidden_algorithm_evaluator")
    ):
        return False
    if str(intent.get("theory", "not_applicable")) == "required" and not any(
        isinstance(task.get(field), Mapping) and task.get(field)
        for field in (
            "hidden_theory_evaluator",
            "hidden_theory_semantic_evaluator",
        )
    ):
        return False
    if str(intent.get("empirical", "not_applicable")) == "required" and not (
        isinstance(task.get("hidden_empirical_evaluator"), Mapping)
        and task.get("hidden_empirical_evaluator")
    ):
        return False
    if str(intent.get("source_replication", "not_applicable")) == "required" and not (
        isinstance(task.get("hidden_source_replication_evaluator"), Mapping)
        and task.get("hidden_source_replication_evaluator")
    ):
        return False
    return str(intent.get("novelty", "not_applicable")) != "required"


def _hidden_execution_summary(
    execution: Mapping[str, Any],
    *,
    evaluator: Mapping[str, Any],
    required_estimator_id: str = "",
) -> dict[str, Any]:
    execution_attempted = execution.get("execution_attempted") is True
    errors = [
        str(value)
        for field in (
            "errors",
            "estimator_binding_errors",
            "estimator_runtime_errors",
        )
        for value in (execution.get(field, []) or [])
        if str(value).strip()
    ]
    if execution.get("result_parse_error"):
        errors.append(str(execution["result_parse_error"]))
    execution_passed = bool(
        execution_attempted
        and _safe_int(execution.get("returncode"), default=-1) == 0
        and not errors
    )
    metrics = execution.get("metrics", {})
    metrics = metrics if isinstance(metrics, Mapping) else {}
    check_results = [
        _evaluate_hidden_check(metrics, check)
        for check in evaluator.get("acceptance_checks", []) or []
    ]
    checks_passed = bool(
        check_results and all(row["passed"] for row in check_results)
    )
    invocation_counts = execution.get("estimator_invocation_counts", {})
    invocation_counts = (
        invocation_counts if isinstance(invocation_counts, Mapping) else {}
    )
    invocation_count = (
        _safe_int(invocation_counts.get(required_estimator_id), default=0)
        if required_estimator_id
        else 0
    )
    return {
        "execution_attempted": execution_attempted,
        "execution_passed": execution_passed,
        "result_hash": str(execution.get("result_hash", "") or ""),
        "estimator_invocation_count": invocation_count,
        "checks_passed": checks_passed,
        "check_results": check_results,
        "errors": errors,
        "passed": bool(
            execution_passed
            and checks_passed
            and (not required_estimator_id or invocation_count > 0)
        ),
    }


def _evaluate_hidden_check(
    metrics: Mapping[str, Any],
    check: Mapping[str, Any],
) -> dict[str, Any]:
    path = check.get("path", [])
    value, found = _nested_value(metrics, path)
    operator = str(check.get("operator", "") or "")
    expected = check.get("expected")
    passed = False
    if found and operator == "eq":
        passed = value == expected
    elif found and operator in {"le", "ge"}:
        if _finite_number(value) and _finite_number(expected):
            passed = (
                float(value) <= float(expected)
                if operator == "le"
                else float(value) >= float(expected)
            )
    elif found and operator == "approx":
        tolerance = check.get("tolerance")
        if (
            _finite_number(value)
            and _finite_number(expected)
            and _finite_number(tolerance)
        ):
            passed = abs(float(value) - float(expected)) <= float(tolerance)
    check_id = str(check.get("check_id", "") or "")
    return {"check_id_hash": stable_hash(check_id) if check_id else "", "passed": passed}


def _nested_value(
    value: Mapping[str, Any],
    path: Any,
) -> tuple[Any, bool]:
    if not isinstance(path, list) or not path:
        return None, False
    current: Any = value
    for part in path:
        if not isinstance(current, Mapping) or str(part) not in current:
            return None, False
        current = current[str(part)]
    return current, True


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _safe_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _latest_accepted_theory_packet(
    artifacts: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any], list[str]]:
    for acceptance in reversed(list(artifacts.values())):
        if not (
            isinstance(acceptance, Mapping)
            and acceptance.get("artifact_kind")
            == "RuntimeArchitectTheoryExecutionPreflightAcceptance"
        ):
            continue
        theory_id = str(acceptance.get("source_theory_packet_id", "") or "")
        theory = artifacts.get(theory_id, {})
        if not isinstance(theory, Mapping) or not theory:
            return "", {}, ["accepted theory packet payload is missing"]
        theory_hash = stable_hash(theory)
        if theory_hash != str(
            acceptance.get("source_theory_packet_hash", "") or ""
        ):
            return "", {}, ["accepted theory packet hash mismatch"]
        if not (
            theory.get("artifact_kind") == "TheoryDerivationPacket"
            and theory.get("serious_theory_mode") is True
            and theory.get("packet_id") == theory_id
        ):
            return "", {}, ["accepted theory packet identity is invalid"]
        preflight_id = str(acceptance.get("preflight_packet_id", "") or "")
        preflight = artifacts.get(preflight_id, {})
        if not (
            isinstance(preflight, Mapping)
            and preflight.get("artifact_kind")
            == "ArchitectTheoryExecutionPreflightReviewPacket"
            and stable_hash(preflight)
            == str(acceptance.get("preflight_packet_hash", "") or "")
            and preflight.get("source_theory_packet_id") == theory_id
            and preflight.get("source_theory_packet_hash") == theory_hash
            and preflight.get("overall_verdict") == "ACCEPT"
            and not preflight.get("active_unresolved_finding_ids")
        ):
            return "", {}, ["accepted theory preflight lineage is invalid"]
        return theory_id, theory, []
    return "", {}, ["no independently accepted serious theory packet was observed"]


def _latest_source_replication_manifest(
    artifacts: Mapping[str, Any],
    *,
    question_id: str,
) -> tuple[str, Mapping[str, Any], list[str]]:
    for artifact_id, artifact in reversed(list(artifacts.items())):
        if not (
            isinstance(artifact, Mapping)
            and artifact.get("artifact_kind") == "SourceReplicationManifest"
            and artifact.get("question_id") == question_id
        ):
            continue
        manifest = dict(artifact)
        declared_hash = str(manifest.pop("manifest_hash", "") or "")
        if not (
            str(artifact.get("artifact_id", "") or "") == str(artifact_id)
            and artifact.get("runtime_generated") is True
            and artifact.get("model_authored") is False
            and artifact.get("command_owned_by_model") is False
            and artifact.get("runtime_edited_source") is False
            and stable_hash(manifest) == declared_hash
        ):
            return "", {}, ["source replication manifest lineage is invalid"]
        if not source_replication_execution_integrity_ok(artifact):
            return "", {}, ["source replication execution is not clean"]
        return str(artifact_id), artifact, []
    return "", {}, ["no runtime-generated source replication manifest was observed"]


def _source_replication_checkpoint_report_document(
    artifacts: Mapping[str, Any],
    *,
    question_id: str,
    source_manifest: Mapping[str, Any],
    task_intent: Any,
) -> tuple[dict[str, Any] | None, bool]:
    """Load one exact model-authored report bound to a valid source checkpoint."""

    source_artifact_id = str(source_manifest.get("artifact_id", "") or "")
    source_manifest_hash = str(source_manifest.get("manifest_hash", "") or "")
    for artifact_id, artifact in reversed(list(artifacts.items())):
        if not (
            isinstance(artifact, Mapping)
            and artifact.get("artifact_kind") == "SourceReplicationCheckpoint"
            and artifact.get("question_id") == question_id
            and artifact.get("checkpoint_id") == artifact_id
        ):
            continue
        checkpoint = deepcopy(dict(artifact))
        workspace_evidence_id = str(
            checkpoint.pop("workspace_evidence_id", "") or ""
        )
        workspace_evidence_hash = str(
            checkpoint.pop("workspace_evidence_hash", "") or ""
        )
        for runtime_field in (
            "runtime_completion_status",
            "boundary",
        ):
            checkpoint.pop(runtime_field, None)
        submitted_checkpoint_hash = stable_hash(checkpoint)
        checkpoint_body = deepcopy(checkpoint)
        checkpoint_id = str(checkpoint_body.pop("checkpoint_id", "") or "")
        source_ref = checkpoint_body.get("source_replication_manifest_ref", {})
        unresolved_gaps = checkpoint_body.get("unresolved_gaps")
        report = checkpoint_body.get("report_document", {})
        workspace_evidence = artifacts.get(workspace_evidence_id, {})
        if not (
            checkpoint_id
            == "source_replication_checkpoint:"
            + stable_hash(checkpoint_body)[:20]
            and checkpoint_body.get("task_intent")
            == (dict(task_intent) if isinstance(task_intent, Mapping) else {})
            and isinstance(source_ref, Mapping)
            and source_ref.get("artifact_id") == source_artifact_id
            and source_ref.get("manifest_hash") == source_manifest_hash
            and source_ref.get("execution_status")
            == source_manifest.get("execution_status")
            and source_ref.get("stdout_sha256")
            == source_manifest.get("stdout_sha256")
            and isinstance(unresolved_gaps, list)
            and all(
                isinstance(value, str) and value.strip()
                for value in unresolved_gaps
            )
            and isinstance(report, Mapping)
            and str(report.get("relative_path", "") or "")
            and checkpoint_body.get("model_authored_report") is True
            and checkpoint_body.get("runtime_edited_report") is False
            and checkpoint_body.get("runtime_edited_source") is False
            and isinstance(workspace_evidence, Mapping)
            and stable_hash(workspace_evidence) == workspace_evidence_hash
            and workspace_evidence.get("artifact_kind")
            == "TheoryDeveloperWorkspaceEvidence"
            and workspace_evidence.get("artifact_id") == workspace_evidence_id
            and workspace_evidence.get("question_id") == question_id
            and workspace_evidence.get("disposition")
            == "SOURCE_REPLICATION_CHECKPOINT_COMMITTED"
            and workspace_evidence.get("checkpoint_committed") is True
            and workspace_evidence.get("submitted_core_packet_hash")
            == submitted_checkpoint_hash
            and workspace_evidence.get("model_owned_source_report") is True
            and workspace_evidence.get("model_owned_theory") is False
            and workspace_evidence.get("runtime_edited_source") is False
            and workspace_evidence.get("runtime_edited_theory") is False
            and report.get("relative_path")
            in (workspace_evidence.get("changed_document_paths", []) or [])
        ):
            return None, False
        try:
            document_rows = load_theory_workspace_document_rows(workspace_evidence)
        except (OSError, UnicodeError, ValueError):
            return None, False
        matching_rows = [
            dict(row)
            for row in document_rows
            if (
            row.get("path") == report.get("relative_path")
            and row.get("sha256") == report.get("sha256")
            and str(row.get("content", "") or "").strip()
            )
        ]
        if len(matching_rows) != 1:
            return None, False
        return matching_rows[0], True
    return None, False


def _source_replication_semantic_evidence_document(
    *,
    source_manifest: Mapping[str, Any],
    source_execution: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind report adjudication to this run without exposing hidden thresholds."""

    manifest_projection = deepcopy(dict(source_manifest))
    manifest_projection.pop("raw_stdout", None)
    manifest_projection.pop("raw_stderr", None)
    manifest_projection.pop("manifest_path", None)
    projected_artifacts: list[dict[str, Any]] = []
    for raw_artifact in manifest_projection.get("result_artifacts", []) or []:
        if not isinstance(raw_artifact, Mapping):
            continue
        artifact = dict(raw_artifact)
        artifact.pop("raw_text", None)
        artifact.pop("text_preview", None)
        projected_artifacts.append(artifact)
    manifest_projection["result_artifacts"] = projected_artifacts
    metrics = source_execution.get("metrics", {})
    body = {
        "artifact_kind": "EvaluatorSourceReplicationObservation",
        "source_replication_manifest": manifest_projection,
        "hidden_source_replication_metrics": (
            deepcopy(dict(metrics)) if isinstance(metrics, Mapping) else {}
        ),
        "proof_evidence_status": "SOURCE_REPLICATION_OBSERVATION_NOT_PROOF_EVIDENCE",
        "boundary": (
            "This post-runtime evaluator observation contains exact run identity and "
            "observed hidden-harness metrics. It contains no acceptance thresholds, "
            "cannot enter AgentRuntime, and is not theorem proof evidence."
        ),
    }
    content = json.dumps(body, ensure_ascii=True, sort_keys=True)
    return {
        "path": "evaluator_source_replication_observation.json",
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "content": content,
    }


def _latest_accepted_algorithm_handoff(
    runtime_result: Mapping[str, Any],
    artifacts: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any], list[str]]:
    traces = runtime_result.get("traces", [])
    if not isinstance(traces, Sequence) or isinstance(traces, (str, bytes)):
        return "", {}, ["runtime traces are unavailable"]
    for trace in reversed(traces):
        if not isinstance(trace, Mapping):
            continue
        artifact_ids = trace.get("produced_artifact_ids", [])
        if not isinstance(artifact_ids, Sequence) or isinstance(
            artifact_ids,
            (str, bytes),
        ):
            continue
        for artifact_id in reversed(artifact_ids):
            artifact_id = str(artifact_id)
            implementation_handoff = artifacts.get(artifact_id, {})
            if (
                isinstance(implementation_handoff, Mapping)
                and implementation_handoff.get("artifact_kind")
                == "RuntimeAcceptedAlgorithmHandoff"
            ):
                if implementation_handoff.get("handoff_id") != artifact_id:
                    return "", {}, ["accepted algorithm handoff identity mismatch"]
                if not implementation_handoff.get("exact_algorithm_artifacts"):
                    return "", {}, ["accepted algorithm handoff has no exact source"]
                return artifact_id, implementation_handoff, []
            if not (
                isinstance(implementation_handoff, Mapping)
                and implementation_handoff.get("artifact_kind")
                == "RuntimeAcceptedImplementationInterfaceHandoff"
            ):
                continue
            accepted_id = str(
                implementation_handoff.get(
                    "source_accepted_algorithm_handoff_id",
                    "",
                )
                or ""
            )
            accepted = artifacts.get(accepted_id, {})
            if not isinstance(accepted, Mapping) or not accepted:
                return "", {}, ["accepted algorithm handoff payload is missing"]
            if stable_hash(accepted) != str(
                implementation_handoff.get(
                    "source_accepted_algorithm_handoff_hash",
                    "",
                )
                or ""
            ):
                return "", {}, ["accepted algorithm handoff hash mismatch"]
            if not accepted.get("exact_algorithm_artifacts"):
                return "", {}, ["accepted algorithm handoff has no exact source"]
            return accepted_id, accepted, []
    return "", {}, ["no independently accepted algorithm handoff was observed"]


def _runtime_artifacts(result: Mapping[str, Any]) -> dict[str, Any]:
    blackboard = result.get("blackboard", {})
    artifacts = blackboard.get("artifacts", {}) if isinstance(blackboard, Mapping) else {}
    return dict(artifacts) if isinstance(artifacts, Mapping) else {}


def _runtime_result_question(result: Mapping[str, Any]) -> Mapping[str, Any]:
    questions: list[Mapping[str, Any]] = []
    for artifact in _runtime_artifacts(result).values():
        if not isinstance(artifact, Mapping):
            continue
        if artifact.get("artifact_kind") != "RuntimeQuestionMetadata":
            continue
        question = artifact.get("question", {})
        if isinstance(question, Mapping):
            questions.append(question)
    if len(questions) > 1:
        raise ValueError(
            "runtime result contains multiple question metadata artifacts"
        )
    return questions[0] if questions else {}


def _runtime_result_question_id(result: Mapping[str, Any]) -> str:
    return str(_runtime_result_question(result).get("id", "") or "")


def _run_hidden_scientific_harness(
    *,
    sandbox_dir: Path,
    artifact_id: str,
    harness_language: str,
    harness_code: str,
    harness_dependencies: Sequence[str],
    estimator_binding: ScientificEstimatorBinding,
    seed: int,
    replicates: int,
    timeout_s: int,
    harness_execution_profile: str = "scientific_wasm",
) -> Mapping[str, Any]:
    execution = execute_scientific_sandbox(
        sandbox_dir=sandbox_dir,
        artifact_id=artifact_id,
        language=harness_language,
        execution_profile=harness_execution_profile,
        code=harness_code,
        dependencies=harness_dependencies,
        seed=seed,
        replicates=replicates,
        timeout_s=timeout_s,
        estimator_bindings=(estimator_binding,),
    )
    return execution.to_json()


def _run_hidden_artifact_harness(
    *,
    sandbox_dir: Path,
    artifact_id: str,
    harness_code: str,
    harness_dependencies: Sequence[str],
    candidate_artifact: Mapping[str, Any],
    seed: int,
    replicates: int,
    timeout_s: int,
    harness_execution_profile: str = "scientific_wasm",
    harness_language: str = "python",
) -> Mapping[str, Any]:
    """Use the selected executor; R JSON parsing requires its jsonlite dependency."""
    if harness_language not in SCIENTIFIC_SANDBOX_LANGUAGES:
        raise ValueError("artifact harness language must be python or r")
    candidate_json = json.dumps(candidate_artifact, ensure_ascii=True, separators=(",", ":"))
    executable_code = f"""import json as _gold_json
{harness_code.rstrip()}

def run_sandbox(seed, replicates, artifacts):
    return evaluate_artifact(
        _gold_json.loads(artifacts['candidate-artifact.json']['content']),
        seed=seed, replicates=replicates,
    )
""" if harness_language == "python" else f"""{harness_code.rstrip()}

run_sandbox <- function(seed, replicates, artifacts) {{
    .gold_candidate <- jsonlite::fromJSON(
        artifacts[['candidate-artifact.json']]$content, simplifyVector=FALSE
    )
    evaluate_artifact(.gold_candidate, seed=seed, replicates=replicates)
}}
"""
    execution = execute_scientific_sandbox(
        sandbox_dir=sandbox_dir,
        artifact_id=artifact_id,
        language=harness_language,
        execution_profile=harness_execution_profile,
        code=executable_code,
        dependencies=harness_dependencies,
        seed=seed,
        replicates=replicates,
        timeout_s=timeout_s,
        input_artifacts=(
            ScientificInputArtifactBinding(
                artifact_id="candidate-artifact.json",
                content=candidate_json,
                content_sha256=hashlib.sha256(candidate_json.encode("utf-8")).hexdigest(),
                media_type="application/json",
            ),
        ),
    )
    return execution.to_json()


def _load_benchmark_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"gold benchmark manifest is unreadable: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("gold benchmark manifest must be an object")
    return dict(payload)


def _validate_benchmark_manifest(
    benchmark: Mapping[str, Any],
    *,
    manifest_path: Path,
    project_root: Path,
) -> None:
    errors: list[str] = []
    schema_version = benchmark.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version not in {1, 2, 3, 4, 5}
    ):
        errors.append("schema_version must be 1, 2, 3, 4, or 5")
        schema_version = 0
    if benchmark.get("artifact_kind") != "ResearchCapabilityGoldBenchmark":
        errors.append("artifact_kind must be ResearchCapabilityGoldBenchmark")
    if not str(benchmark.get("benchmark_id", "") or "").strip():
        errors.append("benchmark_id is required")
    if benchmark.get("runtime_visibility") != "evaluator_only_after_runtime":
        errors.append("gold benchmark must be evaluator-only after runtime")
    for field in (
        "gold_is_accessible_to_runtime_rag",
        "gold_is_accessible_to_model_workspace",
        "gold_execution_may_generate_runtime_feedback",
    ):
        if benchmark.get(field) is not False:
            errors.append(f"{field} must be false")
    model_policy = benchmark.get("model_policy", {})
    expected_policy = {
        "model_tier": LIVE_EVALUATION_MODEL_TIER if schema_version >= 5 else "haiku",
        "model": LIVE_EVALUATION_MODEL if schema_version >= 5 else "claude-haiku-4-5-20251001",
        "automatic_tier_escalation_allowed": False,
    }
    if schema_version >= 5:
        expected_policy["provider"] = LIVE_EVALUATION_PROVIDER
    if not isinstance(model_policy, Mapping) or any(
        model_policy.get(key) != value for key, value in expected_policy.items()
    ):
        errors.append("gold benchmark model policy must match its exact recorded model without escalation")
    visible_path = _project_path(
        str(benchmark.get("model_visible_questions_path", "") or ""),
        project_root=project_root,
    )
    visible_questions: dict[str, Mapping[str, Any]] = {}
    if not visible_path.is_file():
        errors.append("model-visible question file is missing")
    elif _file_sha256(visible_path) != str(
        benchmark.get("model_visible_questions_sha256", "") or ""
    ):
        errors.append("model-visible question file hash mismatch")
    else:
        try:
            visible_payload = json.loads(visible_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("model-visible question file is invalid JSON")
        else:
            visible_rows = (
                visible_payload.get("questions", [])
                if isinstance(visible_payload, Mapping)
                else []
            )
            visible_questions = {
                str(row.get("id", "") or ""): row
                for row in visible_rows
                if isinstance(row, Mapping)
                and str(row.get("id", "") or "").strip()
            }
    tasks = benchmark.get("active_tasks", [])
    if not isinstance(tasks, list) or not tasks:
        errors.append("active_tasks must be a nonempty array")
        tasks = []
    observed_ids: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, Mapping):
            errors.append(f"active task {index} must be an object")
            continue
        task_id = str(task.get("task_id", "") or "")
        if not task_id or task_id in observed_ids:
            errors.append(f"active task {index} has missing or duplicate task_id")
        observed_ids.add(task_id)
        if task.get("status") != "active_scored":
            errors.append(f"active task {index} status must be active_scored")
        scoring_scope = str(
            task.get("scoring_scope", "component") or "component"
        )
        if scoring_scope not in {"component", "full_task"}:
            errors.append(
                f"active task {index} scoring_scope must be component or full_task"
            )
        visible_question = visible_questions.get(task_id, {})
        visible_runtime_payload = _visible_question_hash_payload(visible_question)
        if not visible_question:
            errors.append(f"active task {index} has no model-visible question")
        elif stable_hash(visible_runtime_payload) != str(
            task.get("visible_question_hash", "") or ""
        ):
            errors.append(f"active task {index} visible question hash mismatch")
        intent = task.get("task_intent", {})
        if not isinstance(intent, Mapping):
            errors.append(f"active task {index} task_intent must be an object")
        elif any(
            str(value) not in {"required", "optional", "not_applicable"}
            for value in intent.values()
        ):
            errors.append(f"active task {index} task_intent has an invalid requirement")
        visible_intent = visible_question.get("task_intent")
        if visible_intent is not None and not isinstance(visible_intent, Mapping):
            errors.append(
                f"active task {index} model-visible task_intent must be an object"
            )
        elif isinstance(visible_intent, Mapping) and dict(visible_intent) != dict(
            intent if isinstance(intent, Mapping) else {}
        ):
            errors.append(
                f"active task {index} task_intent does not match the "
                "model-visible question"
            )
        scientific_code_required = str(
            intent.get("scientific_code", "not_applicable")
            if isinstance(intent, Mapping)
            else "not_applicable"
        ) == "required"
        algorithm_evaluator = task.get("hidden_algorithm_evaluator", {})
        empirical_evaluator = task.get("hidden_empirical_evaluator")
        estimator_execution_contract = visible_question.get(
            "estimator_execution_contract", {}
        )
        contract_required = bool(
            schema_version >= 2
            and (
                scientific_code_required
                or (
                    isinstance(algorithm_evaluator, Mapping)
                    and bool(algorithm_evaluator)
                )
                or (
                    isinstance(empirical_evaluator, Mapping)
                    and bool(empirical_evaluator)
                )
            )
        )
        contract_errors = frozen_estimator_execution_contract_errors(
            estimator_execution_contract,
            label=(
                f"active task {index} model-visible "
                "estimator_execution_contract"
            ),
            required=(
                contract_required
                or "estimator_execution_contract" in visible_question
            ),
        )
        errors.extend(contract_errors)
        errors.extend(
            frozen_formal_target_contract_errors(
                visible_question.get("formal_target_contract", {}),
                label=f"active task {index} model-visible formal_target_contract",
                required=(isinstance(intent, Mapping) and str(intent.get("formal", "not_applicable")) == "required"
                    or "formal_target_contract" in visible_question),
            )
        )
        contract_clause_ids = (
            frozen_estimator_execution_contract_clause_ids(
                estimator_execution_contract
            )
            if isinstance(estimator_execution_contract, Mapping)
            and estimator_execution_contract
            and not contract_errors
            else set()
        )
        empirical_claim_clause_ids = (
            frozen_estimator_execution_contract_empirical_claim_ids(
                estimator_execution_contract
            )
            if contract_clause_ids
            else set()
        )
        if (
            schema_version >= 2
            and isinstance(empirical_evaluator, Mapping)
            and empirical_evaluator
            and not empirical_claim_clause_ids
        ):
            errors.append(
                f"active task {index} model-visible estimator_execution_contract "
                "requires an empirical claim for the hidden empirical evaluator"
            )
        contract_id = (
            frozen_estimator_execution_contract_id(
                estimator_execution_contract
            )
            if contract_clause_ids
            else ""
        )
        if contract_id and str(
            task.get("estimator_execution_contract_id", "") or ""
        ) != contract_id:
            errors.append(
                f"active task {index} estimator_execution_contract_id "
                "does not match the model-visible contract"
            )
        algorithm_required = scientific_code_required
        if algorithm_evaluator is None:
            algorithm_evaluator = {}
        if not isinstance(algorithm_evaluator, Mapping):
            errors.append(
                f"active task {index} hidden_algorithm_evaluator must be an object"
            )
            algorithm_evaluator = {}
        elif algorithm_evaluator:
            errors.extend(
                _hidden_evaluator_validation_errors(
                    algorithm_evaluator,
                    task_index=index,
                    label="algorithm",
                    project_root=project_root,
                    require_estimator=True,
                    allowed_contract_clause_ids=(
                        contract_clause_ids if schema_version >= 2 else None
                    ),
                )
            )
        elif algorithm_required:
            errors.append(
                f"active task {index} hidden_algorithm_evaluator must be an object"
            )
        algorithm_estimator_id = str(
            algorithm_evaluator.get("required_estimator_id", "") or ""
        )
        contract_estimator_id = (
            str(estimator_execution_contract.get("estimator_id", "") or "")
            if isinstance(estimator_execution_contract, Mapping)
            else ""
        )
        if (
            schema_version >= 2
            and bool(algorithm_evaluator)
            and algorithm_estimator_id != contract_estimator_id
        ):
            errors.append(
                f"active task {index} algorithm evaluator estimator identity "
                "must match the model-visible contract"
            )
        source_replication_evaluator = task.get(
            "hidden_source_replication_evaluator"
        )
        source_replication_required = str(
            intent.get("source_replication", "not_applicable")
            if isinstance(intent, Mapping)
            else "not_applicable"
        ) == "required"
        if source_replication_evaluator is not None:
            if not (
                isinstance(source_replication_evaluator, Mapping)
                and source_replication_evaluator
            ):
                errors.append(
                    f"active task {index} hidden_source_replication_evaluator "
                    "must be a nonempty object"
                )
            else:
                errors.extend(
                    _hidden_evaluator_validation_errors(
                        source_replication_evaluator,
                        task_index=index,
                        label="source replication",
                        project_root=project_root,
                        require_estimator=False,
                        allowed_contract_clause_ids=None,
                    )
                )
        elif source_replication_required:
            errors.append(
                f"active task {index} hidden_source_replication_evaluator is missing"
            )
        for field, label, require_estimator in (
            ("hidden_theory_evaluator", "theory", False),
            ("hidden_empirical_evaluator", "empirical", True),
        ):
            evaluator = task.get(field)
            if evaluator is None:
                continue
            if not isinstance(evaluator, Mapping) or not evaluator:
                errors.append(
                    f"active task {index} {field} must be a nonempty object"
                )
                continue
            errors.extend(
                _hidden_evaluator_validation_errors(
                    evaluator,
                    task_index=index,
                    label=label,
                    project_root=project_root,
                    require_estimator=require_estimator,
                    allowed_contract_clause_ids=(
                        contract_clause_ids
                        if schema_version >= 2 and label == "empirical"
                        else None
                    ),
                    required_contract_clause_ids=(
                        empirical_claim_clause_ids
                        if schema_version >= 2 and label == "empirical"
                        else None
                    ),
                )
            )
            if require_estimator and str(
                evaluator.get("required_estimator_id", "") or ""
            ) != algorithm_estimator_id:
                errors.append(
                    f"active task {index} empirical evaluator estimator identity "
                    "must match the algorithm evaluator"
                )
        for semantic_field, semantic_label in (
            ("hidden_theory_semantic_evaluator", "theory"),
            (
                "hidden_source_report_semantic_evaluator",
                "source report",
            ),
        ):
            semantic_evaluator = task.get(semantic_field)
            if semantic_evaluator is None:
                continue
            if not isinstance(semantic_evaluator, Mapping) or not semantic_evaluator:
                errors.append(
                    f"active task {index} {semantic_field} "
                    "must be a nonempty object"
                )
            else:
                errors.extend(
                    _hidden_theory_semantic_evaluator_validation_errors(
                        semantic_evaluator,
                        task_index=index,
                        project_root=project_root,
                        artifact_label=semantic_label,
                        model_policy=expected_policy if schema_version >= 5 else None,
                        require_candidate_mode_negative_cases=(
                            schema_version >= 4
                        ),
                    )
                )
                if (
                    semantic_field == "hidden_source_report_semantic_evaluator"
                    and not source_replication_evaluator
                ):
                    errors.append(
                        f"active task {index} source-report semantic evaluation "
                        "requires hidden_source_replication_evaluator"
                    )
        if schema_version >= 3:
            errors.extend(
                _activation_candidate_suite_validation_errors(
                    task,
                    task_index=index,
                    project_root=project_root,
                    algorithm_evaluator=algorithm_evaluator,
                    empirical_evaluator=(
                        empirical_evaluator
                        if isinstance(empirical_evaluator, Mapping)
                        else {}
                    ),
                    contract_clause_ids=contract_clause_ids,
                    empirical_claim_clause_ids=empirical_claim_clause_ids,
                )
            )
        if scoring_scope == "full_task":
            if not _full_task_gold_configured(task):
                errors.append(
                    f"active task {index} full_task scoring lacks hidden gold "
                    "for a required substantive dimension"
                )
    if errors:
        raise ValueError(
            f"invalid gold benchmark manifest {manifest_path}: "
            + "; ".join(errors)
        )


def _hidden_theory_semantic_evaluator_validation_errors(
    evaluator: Mapping[str, Any],
    *,
    task_index: int,
    project_root: Path,
    artifact_label: str = "theory",
    require_candidate_mode_negative_cases: bool = False,
    model_policy: Mapping[str, Any] | None = None,
) -> list[str]:
    label = (
        f"active task {task_index} hidden {artifact_label} semantic evaluator"
    )
    errors: list[str] = []
    expected_policy = model_policy if model_policy is not None else {
        "provider": "anthropic", "model_tier": "haiku",
        "model": "claude-haiku-4-5-20251001", "automatic_tier_escalation_allowed": False,
    }
    if any(evaluator.get(key) != value for key, value in expected_policy.items()):
        errors.append(f"{label} must use the benchmark's exact model without escalation")
    candidate_strategy = str(
        evaluator.get(
            "candidate_adjudication_strategy",
            "integrated_single",
        )
        or "integrated_single"
    )
    if candidate_strategy not in THEORY_SEMANTIC_CANDIDATE_STRATEGIES:
        errors.append(f"{label} candidate adjudication strategy is invalid")
    references = evaluator.get("reference_documents", [])
    if not isinstance(references, list) or not references:
        errors.append(f"{label} reference_documents are missing")
        references = []
    for index, row in enumerate(references):
        if not isinstance(row, Mapping):
            errors.append(f"{label} reference {index} must be an object")
            continue
        path = _project_path(
            str(row.get("path", "") or ""),
            project_root=project_root,
        )
        if not path.is_file():
            errors.append(f"{label} reference {index} is missing")
        elif _file_sha256(path) != str(row.get("sha256", "") or ""):
            errors.append(f"{label} reference {index} hash mismatch")
    authorities: dict[str, dict[str, Any]] = {}
    authority_specs = [
        ("rubric", "rubric_path", "rubric_sha256"),
        (
            "calibration cases",
            "calibration_cases_path",
            "calibration_cases_sha256",
        ),
    ]
    if require_candidate_mode_negative_cases or evaluator.get(
        "candidate_mode_negative_cases_path"
    ):
        authority_specs.append(
            (
                "candidate-mode negative cases",
                "candidate_mode_negative_cases_path",
                "candidate_mode_negative_cases_sha256",
            )
        )
    for name, path_field, hash_field in authority_specs:
        path = _project_path(
            str(evaluator.get(path_field, "") or ""),
            project_root=project_root,
        )
        if not path.is_file():
            errors.append(f"{label} {name} file is missing")
            continue
        if _file_sha256(path) != str(evaluator.get(hash_field, "") or ""):
            errors.append(f"{label} {name} hash mismatch")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append(f"{label} {name} file is invalid JSON")
            continue
        if not isinstance(payload, Mapping):
            errors.append(f"{label} {name} must be an object")
            continue
        authorities[name] = dict(payload)
    activation_record_path = str(
        evaluator.get("activation_record_path", "") or ""
    ).strip()
    activation_record_hash = str(
        evaluator.get("activation_record_sha256", "") or ""
    ).strip()
    if bool(activation_record_path) != bool(activation_record_hash):
        errors.append(
            f"{label} activation record path and hash must be configured together"
        )
    elif activation_record_path:
        record_path = _project_path(
            activation_record_path,
            project_root=project_root,
        )
        if not record_path.is_file():
            errors.append(f"{label} activation record is missing")
        elif _file_sha256(record_path) != activation_record_hash:
            errors.append(f"{label} activation record hash mismatch")
        else:
            try:
                record = json.loads(record_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                errors.append(f"{label} activation record is invalid JSON")
            else:
                if not isinstance(record, Mapping) or record.get(
                    "artifact_kind"
                ) != "HiddenSemanticActivationAttempt":
                    errors.append(f"{label} activation record is invalid")
    rubric = authorities.get("rubric", {})
    claims = rubric.get("claims", [])
    claim_ids = [
        str(row.get("claim_id", "") or "")
        for row in claims
        if isinstance(row, Mapping)
    ] if isinstance(claims, list) else []
    if (
        not claim_ids
        or len(claim_ids) != len(claims)
        or len(set(claim_ids)) != len(claim_ids)
    ):
        errors.append(f"{label} rubric claims are missing or have invalid identities")
    calibration_errors, calibration_statuses = (
        _semantic_case_authority_validation_errors(
            authorities.get("calibration cases", {}),
            label=f"{label} calibration",
            project_root=project_root,
        )
    )
    errors.extend(calibration_errors)
    if not {"PASS", "FAIL"} <= calibration_statuses:
        errors.append(f"{label} calibration must contain both PASS and FAIL cases")
    if require_candidate_mode_negative_cases or (
        "candidate-mode negative cases" in authorities
    ):
        negative_errors, negative_statuses = (
            _semantic_case_authority_validation_errors(
                authorities.get("candidate-mode negative cases", {}),
                label=f"{label} candidate-mode negative",
                project_root=project_root,
            )
        )
        errors.extend(negative_errors)
        if negative_statuses != {"FAIL"}:
            errors.append(
                f"{label} candidate-mode negative cases must all expect FAIL"
            )
    return errors


def _semantic_case_authority_validation_errors(
    authority: Mapping[str, Any],
    *,
    label: str,
    project_root: Path,
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    cases = authority.get("cases", [])
    if not isinstance(cases, list) or not cases:
        return [f"{label} cases are missing"], set()
    case_ids: list[str] = []
    expected_statuses: set[str] = set()
    for case_index, row in enumerate(cases):
        if not isinstance(row, Mapping):
            errors.append(f"{label} case {case_index} is invalid")
            continue
        case_id = str(row.get("case_id", "") or "")
        expected = str(row.get("expected_status", "") or "")
        case_ids.append(case_id)
        expected_statuses.add(expected)
        if not case_id or expected not in {"PASS", "FAIL", "INCONCLUSIVE"}:
            errors.append(
                f"{label} case {case_index} identity or expectation is invalid"
            )
        if not isinstance(row.get("documents"), list) or not row.get("documents"):
            errors.append(f"{label} case {case_index} has no documents")
            continue
        for document_index, document in enumerate(row.get("documents", []) or []):
            if not isinstance(document, Mapping):
                errors.append(
                    f"{label} case {case_index} document "
                    f"{document_index} is invalid"
                )
                continue
            source_path_value = str(document.get("source_path", "") or "")
            if not source_path_value:
                if not str(document.get("content", "") or "").strip():
                    errors.append(
                        f"{label} case {case_index} document "
                        f"{document_index} has no content"
                    )
                continue
            source_path = _project_path(
                source_path_value,
                project_root=project_root,
            )
            if not source_path.is_file():
                errors.append(
                    f"{label} case {case_index} document "
                    f"{document_index} is missing"
                )
            elif _file_sha256(source_path) != str(
                document.get("sha256", "") or ""
            ):
                errors.append(
                    f"{label} case {case_index} document "
                    f"{document_index} hash mismatch"
                )
    if len(set(case_ids)) != len(case_ids):
        errors.append(f"{label} case identities repeat")
    return errors, expected_statuses


def _hidden_evaluator_validation_errors(
    evaluator: Mapping[str, Any],
    *,
    task_index: int,
    label: str,
    project_root: Path,
    require_estimator: bool,
    allowed_contract_clause_ids: set[str] | None,
    required_contract_clause_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    profile = evaluator.get("execution_profile", "scientific_wasm")
    if profile not in SCIENTIFIC_SANDBOX_PROFILES or (
        profile in SCIENTIFIC_NATIVE_PROFILES and evaluator.get("language") != SCIENTIFIC_NATIVE_PROFILES[profile]
    ):
        errors.append(f"active task {task_index} hidden {label} execution profile is invalid")
    if (
        str(evaluator.get("language", "") or "")
        not in SCIENTIFIC_SANDBOX_LANGUAGES
    ):
        errors.append(f"active task {task_index} hidden {label} language is invalid")
    harness_path = _project_path(
        str(evaluator.get("harness_path", "") or ""),
        project_root=project_root,
    )
    if not harness_path.is_file():
        errors.append(f"active task {task_index} hidden {label} harness is missing")
    elif _file_sha256(harness_path) != str(
        evaluator.get("harness_sha256", "") or ""
    ):
        errors.append(
            f"active task {task_index} hidden {label} harness hash mismatch"
        )
    if require_estimator and not str(
        evaluator.get("required_estimator_id", "") or ""
    ).strip():
        errors.append(
            f"active task {task_index} {label} required_estimator_id is missing"
        )
    checks = evaluator.get("acceptance_checks", [])
    if not isinstance(checks, list) or not checks:
        errors.append(
            f"active task {task_index} {label} acceptance_checks are missing"
        )
        checks = []
    check_ids: list[str] = []
    for check_index, check in enumerate(checks):
        if not isinstance(check, Mapping):
            errors.append(
                f"active task {task_index} {label} check {check_index} "
                "must be an object"
            )
            continue
        check_id = str(check.get("check_id", "") or "").strip()
        if check_id:
            check_ids.append(check_id)
        elif allowed_contract_clause_ids is not None:
            errors.append(
                f"active task {task_index} {label} check {check_index} "
                "check_id is required by schema v2"
            )
        if str(check.get("operator", "") or "") not in {
            "eq",
            "le",
            "ge",
            "approx",
        }:
            errors.append(
                f"active task {task_index} {label} check {check_index} "
                "has unsupported operator"
            )
        if not isinstance(check.get("path"), list) or not check.get("path"):
            errors.append(
                f"active task {task_index} {label} check {check_index} path is invalid"
            )
        if allowed_contract_clause_ids is not None:
            raw_refs = check.get("contract_clause_refs")
            refs = (
                [str(value).strip() for value in raw_refs]
                if isinstance(raw_refs, list)
                else []
            )
            if not refs or any(not value for value in refs):
                errors.append(
                    f"active task {task_index} {label} check {check_index} "
                    "contract_clause_refs must be a nonempty string array"
                )
            unknown_refs = sorted(
                {value for value in refs if value}
                - allowed_contract_clause_ids
            )
            if unknown_refs:
                errors.append(
                    f"active task {task_index} {label} check {check_index} "
                    "references unknown model-visible contract clauses: "
                    + ", ".join(unknown_refs)
                )
            if len(refs) != len(set(refs)):
                errors.append(
                    f"active task {task_index} {label} check {check_index} "
                    "contract_clause_refs repeat"
                )
            if required_contract_clause_ids is not None and not (
                set(refs) & required_contract_clause_ids
            ):
                errors.append(
                    f"active task {task_index} {label} check {check_index} "
                    "must cite a model-visible empirical claim"
                )
    if allowed_contract_clause_ids is not None and len(check_ids) != len(
        set(check_ids)
    ):
        errors.append(
            f"active task {task_index} {label} check_id values must be unique"
        )
    return errors


def _activation_candidate_suite_validation_errors(
    task: Mapping[str, Any],
    *,
    task_index: int,
    project_root: Path,
    algorithm_evaluator: Mapping[str, Any],
    empirical_evaluator: Mapping[str, Any],
    contract_clause_ids: set[str],
    empirical_claim_clause_ids: set[str],
) -> list[str]:
    evaluators = {
        name: value
        for name, value in (
            ("algorithm", algorithm_evaluator),
            ("empirical", empirical_evaluator),
        )
        if value
    }
    if not evaluators:
        return []
    label = f"active task {task_index} activation_candidate_suite"
    suite = task.get("activation_candidate_suite")
    if not isinstance(suite, Mapping):
        return [f"{label} is required by schema v3"]
    estimator_ids = {
        str(value.get("required_estimator_id", "") or "")
        for value in evaluators.values()
    }
    errors = _activation_candidate_validation_errors(
        suite.get("reference_candidate"),
        label=f"{label} reference_candidate",
        project_root=project_root,
        estimator_ids=estimator_ids,
    )
    negatives = suite.get("negative_candidates")
    if not isinstance(negatives, list) or not negatives:
        errors.append(f"{label} negative_candidates must be nonempty")
        negatives = []
    covered_evaluators: set[str] = set()
    for candidate_index, candidate in enumerate(negatives):
        candidate_label = f"{label} negative candidate {candidate_index}"
        errors.extend(
            _activation_candidate_validation_errors(
                candidate,
                label=candidate_label,
                project_root=project_root,
                estimator_ids=estimator_ids,
            )
        )
        targets = (
            {str(value) for value in candidate.get("must_fail_evaluators", [])}
            if isinstance(candidate, Mapping)
            and isinstance(candidate.get("must_fail_evaluators"), list)
            else set()
        )
        if not targets or not targets <= set(evaluators):
            errors.append(f"{candidate_label} must target configured evaluators")
        covered_evaluators.update(targets)
    missing_negative_controls = set(evaluators) - covered_evaluators
    if missing_negative_controls:
        errors.append(
            f"{label} lacks negative controls for: "
            + ", ".join(sorted(missing_negative_controls))
        )
    cited_clauses = {
        str(clause_id)
        for evaluator in evaluators.values()
        for check in evaluator.get("acceptance_checks", []) or []
        if isinstance(check, Mapping)
        for clause_id in check.get("contract_clause_refs", []) or []
    }
    required_clause_ids = contract_clause_ids - (
        set() if empirical_evaluator else empirical_claim_clause_ids
    )
    if missing_clauses := required_clause_ids - cited_clauses:
        errors.append(
            f"{label} does not exercise public contract clauses: "
            + ", ".join(sorted(missing_clauses))
        )
    return errors


def _activation_candidate_validation_errors(
    candidate: Any,
    *,
    label: str,
    project_root: Path,
    estimator_ids: set[str],
) -> list[str]:
    if not isinstance(candidate, Mapping):
        return [f"{label} must be an object"]
    errors: list[str] = []
    if str(candidate.get("estimator_id", "") or "") not in estimator_ids:
        errors.append(f"{label} estimator identity is invalid")
    if (
        str(candidate.get("language", "") or "")
        not in SCIENTIFIC_SANDBOX_LANGUAGES
    ):
        errors.append(f"{label} language is invalid")
    dependencies = candidate.get("dependencies")
    if not isinstance(dependencies, list) or any(
        not isinstance(value, str) or not value.strip() for value in dependencies
    ):
        errors.append(f"{label} dependencies must be a string array")
    source_path = _project_path(
        str(candidate.get("source_path", "") or ""), project_root=project_root
    )
    if not source_path.is_file():
        errors.append(f"{label} source is missing")
    elif _file_sha256(source_path) != str(candidate.get("source_sha256", "") or ""):
        errors.append(f"{label} source hash mismatch")
    return errors


def _run_activation_candidate_suite(
    task: Mapping[str, Any], *, project_root: Path, sandbox_root: Path
) -> dict[str, Any]:
    suite = task["activation_candidate_suite"]
    evaluators = {
        name: task[field]
        for name, field in (
            ("algorithm", "hidden_algorithm_evaluator"),
            ("empirical", "hidden_empirical_evaluator"),
        )
        if isinstance(task.get(field), Mapping) and task.get(field)
    }
    reference = suite["reference_candidate"]
    reference_results = {
        name: _run_activation_candidate(
            reference,
            evaluator=evaluator,
            project_root=project_root,
            sandbox_dir=sandbox_root / str(task["task_id"]) / name / "reference",
        )
        for name, evaluator in evaluators.items()
    }
    failed_reference = [
        name for name, row in reference_results.items() if not row["passed"]
    ]
    if failed_reference:
        raise ValueError(
            f"gold activation reference failed exact candidate validators for "
            f"task {task['task_id']}: " + ", ".join(failed_reference)
        )
    rejected = 0
    for index, candidate in enumerate(suite["negative_candidates"]):
        for name in candidate["must_fail_evaluators"]:
            row = _run_activation_candidate(
                candidate,
                evaluator=evaluators[name],
                project_root=project_root,
                sandbox_dir=(
                    sandbox_root / str(task["task_id"]) / name / f"negative-{index}"
                ),
            )
            if row["passed"] or not row["execution_attempted"] or not row[
                "estimator_invocation_count"
            ]:
                raise ValueError(
                    f"gold activation negative control {index} was not rejected "
                    f"by the exact {name} candidate validator for task {task['task_id']}"
                )
            rejected += 1
    return {
        "task_id_hash": stable_hash(str(task["task_id"])),
        "reference_validator_hashes": {
            name: stable_hash(evaluator) for name, evaluator in evaluators.items()
        },
        "reference_result_hashes": {
            name: row["result_hash"] for name, row in reference_results.items()
        },
        "negative_controls_rejected": rejected,
    }


def _run_activation_candidate(
    candidate: Mapping[str, Any],
    *,
    evaluator: Mapping[str, Any],
    project_root: Path,
    sandbox_dir: Path,
) -> dict[str, Any]:
    source = _project_path(
        str(candidate["source_path"]), project_root=project_root
    ).read_text(encoding="utf-8")
    harness = _project_path(str(evaluator["harness_path"]), project_root=project_root)
    execution = _run_hidden_scientific_harness(
        sandbox_dir=sandbox_dir,
        artifact_id="gold-activation-candidate",
        harness_language=str(evaluator["language"]),
        harness_execution_profile=str(evaluator.get("execution_profile", "scientific_wasm")),
        harness_code=harness.read_text(encoding="utf-8"),
        harness_dependencies=tuple(evaluator.get("dependencies", []) or []),
        estimator_binding=ScientificEstimatorBinding(
            artifact_id=str(candidate["estimator_id"]),
            language=str(candidate["language"]),
            code=source,
            code_hash=stable_hash(source),
            dependencies=tuple(candidate.get("dependencies", []) or []),
        ),
        seed=int(evaluator.get("seed", 0) or 0),
        replicates=int(evaluator.get("replicates", 1) or 1),
        timeout_s=int(evaluator.get("timeout_seconds", 60) or 60),
    )
    return _hidden_execution_summary(
        execution,
        evaluator=evaluator,
        required_estimator_id=str(evaluator["required_estimator_id"]),
    )


def _project_path(value: str, *, project_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
