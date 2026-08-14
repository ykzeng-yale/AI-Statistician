from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .fingerprint import stable_hash
from .scientific_sandbox import (
    ScientificEstimatorBinding,
    execute_scientific_sandbox,
)


GOLD_EVALUATION_BOUNDARY = (
    "Evaluator-only gold runs after the AgentRuntime has terminated. Hidden "
    "harness source, expected values, and acceptance checks are never added to "
    "the blackboard, retrieval context, model prompt, or source-revision loop."
)
GoldHarnessRunner = Callable[..., Mapping[str, Any]]


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
        "runtime_visibility": "evaluator_only_after_runtime",
        "boundary": GOLD_EVALUATION_BOUNDARY,
    }


def evaluate_research_gold_benchmark(
    results: Sequence[Mapping[str, Any]],
    *,
    research_evaluation_summary: Mapping[str, Any],
    benchmark_manifest_path: Path,
    out_dir: Path,
    run_harness: GoldHarnessRunner | None = None,
) -> dict[str, Any]:
    """Evaluate accepted model source against hidden post-runtime gold cases."""

    benchmark_manifest_path = benchmark_manifest_path.resolve()
    benchmark = _load_benchmark_manifest(benchmark_manifest_path)
    project_root = Path(__file__).resolve().parents[1]
    _validate_benchmark_manifest(
        benchmark,
        manifest_path=benchmark_manifest_path,
        project_root=project_root,
    )
    result_by_question = {
        question_id: result
        for result in results
        if (question_id := _runtime_result_question_id(result))
    }
    summary_rows = {
        str(row.get("question_id", "") or ""): row
        for row in research_evaluation_summary.get("rows", []) or []
        if isinstance(row, Mapping)
        and str(row.get("question_id", "") or "").strip()
    }
    harness_runner = run_harness or _run_hidden_scientific_harness
    task_rows: list[dict[str, Any]] = []
    for task in benchmark["active_tasks"]:
        task_rows.append(
            _evaluate_gold_task(
                task,
                runtime_result=result_by_question.get(str(task["task_id"])),
                research_summary_row=summary_rows.get(str(task["task_id"]), {}),
                project_root=project_root,
                out_dir=out_dir,
                run_harness=harness_runner,
            )
        )
    payload = {
        "schema_version": 1,
        "artifact_kind": "ResearchCapabilityGoldEvaluation",
        "configured": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": benchmark["benchmark_id"],
        "benchmark_manifest_path": str(benchmark_manifest_path),
        "benchmark_manifest_hash": stable_hash(benchmark),
        "gold_visibility": "evaluator_only_after_runtime_termination",
        "n_active_tasks": len(task_rows),
        "n_tasks_evaluated": sum(
            row["hidden_harness_execution_attempted"] is True for row in task_rows
        ),
        "n_tasks_passed": sum(row["task_passed"] is True for row in task_rows),
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
    out_dir: Path,
    run_harness: GoldHarnessRunner,
) -> dict[str, Any]:
    task_id = str(task["task_id"])
    runtime_requirements = (
        research_summary_row.get("requirements", {})
        if isinstance(research_summary_row.get("requirements", {}), Mapping)
        else {}
    )
    base = {
        "task_id": task_id,
        "level": str(task["level"]),
        "runtime_result_observed": runtime_result is not None,
        "runtime_research_eval_complete": (
            research_summary_row.get("research_eval_complete") is True
        ),
        "runtime_visible_question_hash": "",
        "accepted_algorithm_handoff_id": "",
        "accepted_algorithm_handoff_hash": "",
        "required_estimator_id": str(
            task["hidden_algorithm_evaluator"]["required_estimator_id"]
        ),
        "evaluated_source_hash": "",
        "hidden_evaluator_source_hash": str(
            task["hidden_algorithm_evaluator"]["harness_sha256"]
        ),
        "hidden_harness_execution_attempted": False,
        "hidden_harness_execution_passed": False,
        "hidden_checks_passed": False,
        "hidden_check_results": [],
        "dimension_status": {},
        "task_passed": False,
        "failure_reasons": [],
        "proof_evidence_status": "GOLD_EVALUATION_NOT_PROOF_EVIDENCE",
        "boundary": GOLD_EVALUATION_BOUNDARY,
    }
    if runtime_result is None:
        base["failure_reasons"] = ["runtime result is missing"]
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=False,
            hidden_algorithm_passed=False,
            runtime_result_observed=False,
        )
        return base

    runtime_question = _runtime_result_question(runtime_result)
    runtime_visible_question_hash = stable_hash(
        {
            key: runtime_question.get(key)
            for key in ("id", "title", "description", "tags")
        }
    )
    base["runtime_visible_question_hash"] = runtime_visible_question_hash
    if runtime_visible_question_hash != str(task["visible_question_hash"]):
        base["failure_reasons"] = [
            "runtime-visible question hash does not match the frozen gold task"
        ]
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=False,
            hidden_algorithm_passed=False,
            runtime_result_observed=True,
        )
        return base

    artifacts = _runtime_artifacts(runtime_result)
    accepted_id, accepted_handoff, errors = _latest_accepted_algorithm_handoff(
        runtime_result,
        artifacts,
    )
    if errors:
        base["failure_reasons"] = errors
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=(
                research_summary_row.get("research_eval_complete") is True
            ),
            hidden_algorithm_passed=False,
            runtime_result_observed=True,
        )
        return base
    base["accepted_algorithm_handoff_id"] = accepted_id
    base["accepted_algorithm_handoff_hash"] = stable_hash(accepted_handoff)

    evaluator = task["hidden_algorithm_evaluator"]
    estimator_id = str(evaluator["required_estimator_id"])
    source_rows = [
        row
        for row in accepted_handoff.get("exact_algorithm_artifacts", []) or []
        if isinstance(row, Mapping)
        and str(row.get("estimator_id", "") or "") == estimator_id
    ]
    if len(source_rows) != 1:
        base["failure_reasons"] = [
            "accepted algorithm handoff does not contain exactly one required "
            f"estimator source: {estimator_id}"
        ]
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=(
                research_summary_row.get("research_eval_complete") is True
            ),
            hidden_algorithm_passed=False,
            runtime_result_observed=True,
        )
        return base
    source = source_rows[0]
    source_code = str(source.get("exact_source_code", "") or "")
    source_hash = str(source.get("exact_source_hash", "") or "")
    if not source_code or source_hash != stable_hash(source_code):
        base["failure_reasons"] = [
            "accepted estimator source is missing or its immutable hash is invalid"
        ]
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=(
                research_summary_row.get("research_eval_complete") is True
            ),
            hidden_algorithm_passed=False,
            runtime_result_observed=True,
        )
        return base
    base["evaluated_source_hash"] = source_hash

    harness_path = _project_path(
        str(evaluator["harness_path"]),
        project_root=project_root,
    )
    harness_code = harness_path.read_text(encoding="utf-8")
    execution = dict(
        run_harness(
            sandbox_dir=out_dir / "gold_sandbox" / task_id,
            artifact_id=f"gold-{task_id}",
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
            ),
            seed=int(evaluator.get("seed", 0) or 0),
            replicates=int(evaluator.get("replicates", 1) or 1),
            timeout_s=int(evaluator.get("timeout_seconds", 60) or 60),
        )
    )
    execution_attempted = execution.get("execution_attempted") is True
    execution_passed = bool(
        execution_attempted
        and _safe_int(execution.get("returncode"), default=-1) == 0
        and not execution.get("errors")
        and not execution.get("estimator_binding_errors")
        and not execution.get("estimator_runtime_errors")
        and not execution.get("result_parse_error")
    )
    metrics = execution.get("metrics", {})
    metrics = metrics if isinstance(metrics, Mapping) else {}
    check_results = [
        _evaluate_hidden_check(metrics, check)
        for check in evaluator.get("acceptance_checks", []) or []
    ]
    hidden_checks_passed = bool(
        check_results and all(row["passed"] for row in check_results)
    )
    invocation_counts = (
        execution.get("estimator_invocation_counts", {})
        if isinstance(execution.get("estimator_invocation_counts", {}), Mapping)
        else {}
    )
    estimator_invocation_count = _safe_int(
        invocation_counts.get(estimator_id),
        default=0,
    )
    hidden_algorithm_passed = bool(
        execution_passed
        and hidden_checks_passed
        and estimator_invocation_count > 0
    )
    base.update(
        {
            "hidden_harness_execution_attempted": execution_attempted,
            "hidden_harness_execution_passed": execution_passed,
            "hidden_harness_result_hash": str(
                execution.get("result_hash", "") or ""
            ),
            "hidden_harness_estimator_invocation_count": (
                estimator_invocation_count
            ),
            "hidden_checks_passed": hidden_checks_passed,
            "hidden_check_results": check_results,
            "failure_reasons": [
                str(value)
                for value in (
                    execution.get("errors", [])
                    or execution.get("estimator_binding_errors", [])
                    or execution.get("estimator_runtime_errors", [])
                    or (
                        [str(execution.get("result_parse_error"))]
                        if execution.get("result_parse_error")
                        else []
                    )
                )
                if str(value).strip()
            ],
        }
    )
    dimensions = _dimension_status(
        task,
        runtime_requirements=runtime_requirements,
        runtime_research_eval_complete=(
            research_summary_row.get("research_eval_complete") is True
        ),
        hidden_algorithm_passed=hidden_algorithm_passed,
        runtime_result_observed=True,
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
    base["failure_reasons"].extend(
        f"required evidence dimension did not pass: {dimension}"
        for dimension in dimension_failures
    )
    base["failure_reasons"] = list(dict.fromkeys(base["failure_reasons"]))
    base["task_passed"] = bool(
        required_dimensions_passed
        and hidden_algorithm_passed
        and research_summary_row.get("research_eval_complete") is True
    )
    return base


def _dimension_status(
    task: Mapping[str, Any],
    *,
    runtime_requirements: Mapping[str, Any],
    runtime_research_eval_complete: bool,
    hidden_algorithm_passed: bool,
    runtime_result_observed: bool,
) -> dict[str, dict[str, Any]]:
    intent = task.get("task_intent", {})
    intent = intent if isinstance(intent, Mapping) else {}
    observed = {
        "source_replication": False,
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
        "formal": False,
        "novelty": False,
        "unresolved_gaps": bool(
            runtime_result_observed
            and runtime_requirements.get(
                "critic_unresolved_gap_disclosure_present"
            )
            is True
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
            status = "runtime_reviewed_not_gold_validated"
        elif dimension == "empirical" and observed[dimension]:
            status = "runtime_accepted_not_gold_validated"
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
                dimension == "scientific_code" and status == "passed"
            ),
            "evidence_authority": {
                "theory": "runtime_independent_review",
                "scientific_code": "evaluator_only_hidden_harness",
                "empirical": "runtime_confirmatory_protocol",
                "unresolved_gaps": "runtime_critic_disclosure",
            }.get(dimension, "not_configured"),
        }
    rows["overall_runtime_research_loop"] = {
        "requirement": "required",
        "status": "passed" if runtime_research_eval_complete else "failed",
        "gold_validated": False,
        "evidence_authority": "runtime_completion_contract",
    }
    return rows


def _evaluate_hidden_check(
    metrics: Mapping[str, Any],
    check: Mapping[str, Any],
) -> dict[str, Any]:
    check_id = str(check.get("check_id", "") or "")
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
    return {
        "check_id": check_id,
        "path": [str(part) for part in path] if isinstance(path, list) else [],
        "operator": operator,
        "observed": value if found else None,
        "observed_hash": stable_hash(value) if found else "",
        "passed": passed,
        "expected_value_disclosed": False,
    }


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
            implementation_handoff = artifacts.get(str(artifact_id), {})
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
    for artifact in _runtime_artifacts(result).values():
        if not isinstance(artifact, Mapping):
            continue
        if artifact.get("artifact_kind") != "RuntimeQuestionMetadata":
            continue
        question = artifact.get("question", {})
        if isinstance(question, Mapping):
            return question
    return {}


def _runtime_result_question_id(result: Mapping[str, Any]) -> str:
    return str(_runtime_result_question(result).get("id", "") or "")


def _run_hidden_scientific_harness(
    *,
    sandbox_dir: Path,
    artifact_id: str,
    harness_code: str,
    harness_dependencies: Sequence[str],
    estimator_binding: ScientificEstimatorBinding,
    seed: int,
    replicates: int,
    timeout_s: int,
) -> Mapping[str, Any]:
    execution = execute_scientific_sandbox(
        sandbox_dir=sandbox_dir,
        artifact_id=artifact_id,
        language="python",
        code=harness_code,
        dependencies=harness_dependencies,
        seed=seed,
        replicates=replicates,
        timeout_s=timeout_s,
        estimator_bindings=(estimator_binding,),
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
    if not (
        isinstance(model_policy, Mapping)
        and model_policy.get("model_tier") == "haiku"
        and model_policy.get("model") == "claude-haiku-4-5-20251001"
        and model_policy.get("automatic_tier_escalation_allowed") is False
    ):
        errors.append("gold benchmark model policy must be exact Haiku without escalation")
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
        visible_question = visible_questions.get(task_id, {})
        visible_runtime_payload = {
            key: visible_question.get(key)
            for key in ("id", "title", "description", "tags")
        }
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
        evaluator = task.get("hidden_algorithm_evaluator", {})
        if not isinstance(evaluator, Mapping):
            errors.append(f"active task {index} hidden evaluator must be an object")
            continue
        harness_path = _project_path(
            str(evaluator.get("harness_path", "") or ""),
            project_root=project_root,
        )
        if not harness_path.is_file():
            errors.append(f"active task {index} hidden harness is missing")
        elif _file_sha256(harness_path) != str(
            evaluator.get("harness_sha256", "") or ""
        ):
            errors.append(f"active task {index} hidden harness hash mismatch")
        if not str(evaluator.get("required_estimator_id", "") or "").strip():
            errors.append(f"active task {index} required_estimator_id is missing")
        checks = evaluator.get("acceptance_checks", [])
        if not isinstance(checks, list) or not checks:
            errors.append(f"active task {index} acceptance_checks are missing")
        for check_index, check in enumerate(checks or []):
            if not isinstance(check, Mapping):
                errors.append(
                    f"active task {index} check {check_index} must be an object"
                )
                continue
            if str(check.get("operator", "") or "") not in {
                "eq",
                "le",
                "ge",
                "approx",
            }:
                errors.append(
                    f"active task {index} check {check_index} has unsupported operator"
                )
            if not isinstance(check.get("path"), list) or not check.get("path"):
                errors.append(
                    f"active task {index} check {check_index} path is invalid"
                )
    if errors:
        raise ValueError(
            f"invalid gold benchmark manifest {manifest_path}: "
            + "; ".join(errors)
        )


def _project_path(value: str, *, project_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
